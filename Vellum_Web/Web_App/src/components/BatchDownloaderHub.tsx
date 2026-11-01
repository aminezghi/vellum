"use client";

import React, { useState, useRef, useEffect } from "react";
import { Notebook } from "@/lib/db";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload, type ResolverSettings } from "@/lib/pdfDownloader";
import {
  parseInputFilesToCandidates,
  normalizeDoi,
  type ImportSummary,
  type ParsedPublication,
} from "@/lib/bibliographicParser";
import {
  DownloadCloud,
  Zap,
  ExternalLink,
  FolderDown,
  Trash2,
  CheckCircle2,
  Play,
  Pause,
  RotateCw,
  FileText,
  Download,
  X,
  SlidersHorizontal,
  Mail,
  Key,
  Globe,
  Building2,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
} from "lucide-react";

interface BatchDownloaderHubProps {
  notebooks: Notebook[];
}

export interface QueueItem extends ParsedPublication {
  status: "idle" | "resolving" | "success" | "paywalled" | "failed";
  message: string;
  source?: string;
  sizeKb?: number;
  pdfBlob?: Blob;
  landingUrl?: string;
  workerId?: number;
}

const SAMPLE_DOIS = [
  "10.1057/s41270-026-00470-6",
  "10.1016/S2214-109X(23)00000-0",
  "10.1038/s41586-023-00000-0",
  "10.48550/arXiv.2303.08774",
  "10.1101/2023.01.01.522432",
  "10.1371/journal.pone.0280000",
];

const SCIHUB_MIRROR_OPTIONS = [
  "https://sci-hub.se/",
  "https://sci-hub.st/",
  "https://sci-hub.ru/",
  "https://sci-hub.ee/",
];

export function BatchDownloaderHub({ notebooks }: BatchDownloaderHubProps) {
  const [inputText, setInputText] = useState("");
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>("");
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<"text" | "file">("text");
  const [importSummary, setImportSummary] = useState<ImportSummary | null>(null);

  // Paywall Bypass & Resolver Settings (persistent in localStorage like Desktop App)
  const [showSettings, setShowSettings] = useState(false);
  const [unpaywallEmail, setUnpaywallEmail] = useState("scholar.vellum@gmail.com");
  const [elsevierApiKey, setElsevierApiKey] = useState("");
  const [scihubMirror, setScihubMirror] = useState("https://sci-hub.se/");
  const [ezproxyUrl, setEzproxyUrl] = useState("");

  const stopRequestedRef = useRef(false);

  // Load saved bypass settings from localStorage on client mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedEmail = localStorage.getItem("vellum_unpaywall_email");
      if (savedEmail) setUnpaywallEmail(savedEmail);

      const savedElsevier = localStorage.getItem("vellum_elsevier_key");
      if (savedElsevier) setElsevierApiKey(savedElsevier);

      const savedMirror = localStorage.getItem("vellum_scihub_mirror");
      if (savedMirror) setScihubMirror(savedMirror);

      const savedProxy = localStorage.getItem("vellum_ezproxy_url");
      if (savedProxy) setEzproxyUrl(savedProxy);
    }
  }, []);

  const handleEmailChange = (val: string) => {
    setUnpaywallEmail(val);
    if (typeof window !== "undefined") localStorage.setItem("vellum_unpaywall_email", val);
  };

  const handleElsevierChange = (val: string) => {
    setElsevierApiKey(val);
    if (typeof window !== "undefined") localStorage.setItem("vellum_elsevier_key", val);
  };

  const handleMirrorChange = (val: string) => {
    setScihubMirror(val);
    if (typeof window !== "undefined") localStorage.setItem("vellum_scihub_mirror", val);
  };

  const handleEzproxyChange = (val: string) => {
    setEzproxyUrl(val);
    if (typeof window !== "undefined") localStorage.setItem("vellum_ezproxy_url", val);
  };

  const getActiveResolverSettings = (): ResolverSettings => ({
    email: unpaywallEmail.trim() || undefined,
    elsevierApiKey: elsevierApiKey.trim() || undefined,
    customMirror: scihubMirror.trim() || undefined,
    ezproxyUrl: ezproxyUrl.trim() || undefined,
  });

  // Convert parsed publication candidates to queue items
  const toQueueItems = (pubs: ParsedPublication[]): QueueItem[] =>
    pubs.map((p) => ({
      ...p,
      status: "idle",
      message: "Ready to resolve",
    }));

  // Intelligent Deduplication and Merge Protocol across multiple files / inputs
  const mergeCandidatesIntoQueue = (
    newCandidates: ParsedPublication[],
    sourceName: string,
    batchDuplicates = 0,
    batchSkipped = 0
  ) => {
    // Map existing records to identify duplicates
    const existingDois = new Set<string>();
    const existingTitles = new Set<string>();

    queue.forEach((q) => {
      const normDoi = normalizeDoi(q.doi);
      if (normDoi) existingDois.add(normDoi);
      const cleanTitle = q.title?.trim().toLowerCase();
      if (cleanTitle && cleanTitle.length > 5) existingTitles.add(cleanTitle);
    });

    let queueDuplicatesCount = 0;
    const uniqueCandidates: ParsedPublication[] = [];

    newCandidates.forEach((cand) => {
      const normDoi = normalizeDoi(cand.doi);
      const cleanTitle = cand.title?.trim().toLowerCase();

      const isDoiDupe = !!(normDoi && existingDois.has(normDoi));
      const isTitleDupe = !!(cleanTitle && cleanTitle.length > 5 && existingTitles.has(cleanTitle));

      if (isDoiDupe || isTitleDupe) {
        queueDuplicatesCount++;
      } else {
        uniqueCandidates.push(cand);
        if (normDoi) existingDois.add(normDoi);
        if (cleanTitle && cleanTitle.length > 5) existingTitles.add(cleanTitle);
      }
    });

    const newQueueItems = toQueueItems(uniqueCandidates);
    const updatedQueue = [...queue, ...newQueueItems];
    setQueue(updatedQueue);

    const totalDupes = batchDuplicates + queueDuplicatesCount;
    setImportSummary({
      fileName: sourceName,
      totalParsed: newCandidates.length + batchDuplicates,
      validWithDoi: uniqueCandidates.length,
      duplicatesRemoved: totalDupes,
      skippedWithoutDoi: batchSkipped,
    });
  };

  // Parse Text Input
  const handleQueueText = () => {
    if (!inputText.trim()) return;
    const { candidates, summary } = parseInputFilesToCandidates(inputText, "Pasted DOIs");
    if (candidates.length === 0) {
      alert("No valid DOIs or academic paper URLs found. Please ensure input contains identifiers like 10.xxxx/...");
      return;
    }
    mergeCandidatesIntoQueue(candidates, "Pasted Text", summary.duplicatesRemoved, summary.skippedWithoutDoi);
  };

  // Parse Multi-File Upload with Strict Extraction, Deduplication & Merging
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const fileList = Array.from(files);
    const aggregatedCandidates: ParsedPublication[] = [];
    let totalDuplicatesInFiles = 0;
    let totalSkippedInFiles = 0;
    const processedNames: string[] = [];

    for (const file of fileList) {
      try {
        const text = await file.text();
        if (text && text.trim()) {
          const { candidates, summary } = parseInputFilesToCandidates(text, file.name);
          aggregatedCandidates.push(...candidates);
          totalDuplicatesInFiles += summary.duplicatesRemoved;
          totalSkippedInFiles += summary.skippedWithoutDoi;
          processedNames.push(file.name);
        }
      } catch (err) {
        console.error(`Error reading ${file.name}:`, err);
      }
    }

    if (aggregatedCandidates.length === 0) {
      alert("No valid DOIs or academic paper entries found in the uploaded file(s).");
      e.target.value = "";
      return;
    }

    const sourceLabel =
      processedNames.length === 1
        ? processedNames[0]
        : `${processedNames.length} files (${processedNames.slice(0, 2).join(", ")}${processedNames.length > 2 ? "..." : ""})`;

    mergeCandidatesIntoQueue(
      aggregatedCandidates,
      sourceLabel,
      totalDuplicatesInFiles,
      totalSkippedInFiles
    );
    e.target.value = "";
  };

  /**
   * Multi-Worker Concurrency Download Protocol (3 Workers in Parallel)
   * Inspired by Vellum Desktop Engine
   */
  const handleStartDownload = async () => {
    if (queue.length === 0 || isProcessing) return;

    setIsProcessing(true);
    stopRequestedRef.current = false;

    const WORKER_COUNT = 3;
    const settings = getActiveResolverSettings();

    // Build list of indices that need processing
    const pendingIndices: number[] = [];
    queue.forEach((item, idx) => {
      if (item.status === "idle" || item.status === "resolving") {
        pendingIndices.push(idx);
      }
    });

    if (pendingIndices.length === 0) {
      setIsProcessing(false);
      return;
    }

    let currentIndex = 0;

    const workerTask = async (workerId: number) => {
      while (currentIndex < pendingIndices.length && !stopRequestedRef.current) {
        const itemIdx = pendingIndices[currentIndex++];
        if (itemIdx === undefined) break;

        const item = queue[itemIdx];
        if (!item || item.status === "success") continue;

        setQueue((prev) =>
          prev.map((q, idx) =>
            idx === itemIdx
              ? {
                  ...q,
                  status: "resolving",
                  workerId,
                  message: `Worker ${workerId}: Resolving multi-tier mirrors...`,
                }
              : q
          )
        );

        try {
          const res = await fetchAndStorePaperPdf(
            {
              doi: item.doi,
              title: item.title || item.doi,
              notebookId: selectedNotebookId || undefined,
              settings,
            },
            (status, details) => {
              setQueue((prev) =>
                prev.map((q, idx) =>
                  idx === itemIdx ? { ...q, message: `Worker ${workerId}: ${details || status}` } : q
                )
              );
            }
          );

          if (res.success && res.blob) {
            const sizeKb = Math.round(res.blob.size / 1024);
            setQueue((prev) =>
              prev.map((q, idx) =>
                idx === itemIdx
                  ? {
                      ...q,
                      status: "success",
                      message: `Downloaded (${sizeKb} KB)`,
                      pdfBlob: res.blob,
                      sizeKb,
                      source: res.sourceName || "Multi-Tier Mirror",
                    }
                  : q
              )
            );
          } else if (res.landingUrl) {
            setQueue((prev) =>
              prev.map((q, idx) =>
                idx === itemIdx
                  ? {
                      ...q,
                      status: "paywalled",
                      message: "Publisher paywalled",
                      landingUrl: res.landingUrl,
                    }
                  : q
              )
            );
          } else {
            setQueue((prev) =>
              prev.map((q, idx) =>
                idx === itemIdx
                  ? {
                      ...q,
                      status: "failed",
                      message: "No open mirror found",
                    }
                  : q
              )
            );
          }
        } catch (err) {
          setQueue((prev) =>
            prev.map((q, idx) =>
              idx === itemIdx
                ? {
                    ...q,
                    status: "failed",
                    message: err instanceof Error ? err.message : "Resolution timeout",
                  }
                : q
            )
          );
        }
      }
    };

    const workers = Array.from({ length: Math.min(WORKER_COUNT, pendingIndices.length) }, (_, i) =>
      workerTask(i + 1)
    );

    await Promise.all(workers);
    setIsProcessing(false);
  };

  // Single Item Retry
  const handleRetryItem = async (itemIdx: number) => {
    const item = queue[itemIdx];
    if (!item || isProcessing) return;

    setQueue((prev) =>
      prev.map((q, idx) =>
        idx === itemIdx
          ? { ...q, status: "resolving", message: "Retrying with active bypass settings..." }
          : q
      )
    );

    try {
      const res = await fetchAndStorePaperPdf(
        {
          doi: item.doi,
          title: item.title || item.doi,
          notebookId: selectedNotebookId || undefined,
          settings: getActiveResolverSettings(),
        },
        (status, details) => {
          setQueue((prev) =>
            prev.map((q, idx) => (idx === itemIdx ? { ...q, message: details || status } : q))
          );
        }
      );

      if (res.success && res.blob) {
        const sizeKb = Math.round(res.blob.size / 1024);
        setQueue((prev) =>
          prev.map((q, idx) =>
            idx === itemIdx
              ? {
                  ...q,
                  status: "success",
                  message: `Downloaded (${sizeKb} KB)`,
                  pdfBlob: res.blob,
                  sizeKb,
                  source: res.sourceName || "Multi-Tier Mirror",
                }
              : q
          )
        );
      } else if (res.landingUrl) {
        setQueue((prev) =>
          prev.map((q, idx) =>
            idx === itemIdx
              ? {
                  ...q,
                  status: "paywalled",
                  message: "Publisher paywalled",
                  landingUrl: res.landingUrl,
                }
              : q
          )
        );
      } else {
        setQueue((prev) =>
          prev.map((q, idx) =>
            idx === itemIdx ? { ...q, status: "failed", message: "No open mirror found" } : q
          )
        );
      }
    } catch {
      setQueue((prev) =>
        prev.map((q, idx) =>
          idx === itemIdx ? { ...q, status: "failed", message: "Timeout" } : q
        )
      );
    }
  };

  const handlePauseDownload = () => {
    stopRequestedRef.current = true;
    setIsProcessing(false);
  };

  const handleRetryFailed = () => {
    setQueue((prev) =>
      prev.map((q) =>
        q.status === "failed" || q.status === "paywalled"
          ? { ...q, status: "idle", message: "Queued for retry" }
          : q
      )
    );
  };

  const handleDownloadAllRetrieved = async () => {
    const successItems = queue.filter((q) => q.status === "success" && q.pdfBlob);
    for (let i = 0; i < successItems.length; i++) {
      const item = successItems[i];
      const safeName = (item.title || item.doi).replace(/[^a-zA-Z0-9_\-]/g, "_").substring(0, 60);
      triggerBrowserFileDownload(item.pdfBlob!, `${safeName}.pdf`);
      await new Promise((r) => setTimeout(r, 250));
    }
  };

  const successCount = queue.filter((q) => q.status === "success").length;
  const paywalledCount = queue.filter((q) => q.status === "paywalled").length;
  const failedCount = queue.filter((q) => q.status === "failed").length;
  const completedCount = successCount + paywalledCount + failedCount;
  const progressPercent = queue.length > 0 ? Math.round((completedCount / queue.length) * 100) : 0;

  const handleExportReport = () => {
    if (queue.length === 0) return;
    const now = new Date().toISOString();
    const lines = [
      "=======================================================================",
      "  VELLUM ACADEMIC PDF BATCH DOWNLOAD AUDIT REPORT",
      "=======================================================================",
      `  Generated on       : ${now}`,
      `  Total items        : ${queue.length}`,
      `  Successfully Saved : ${successCount}`,
      `  Paywalled Gateway  : ${paywalledCount}`,
      `  Failed Mirrors     : ${failedCount}`,
      "=======================================================================",
      "",
      "RESOLVED PAPERS:",
      "-----------------------------------------------------------------------",
    ];

    queue.forEach((item, idx) => {
      lines.push(`[${idx + 1}] ${item.doi}`);
      lines.push(`    Title   : ${item.title}`);
      if (item.authors) lines.push(`    Authors : ${item.authors}${item.year ? ` (${item.year})` : ""}`);
      lines.push(`    Status  : ${item.status.toUpperCase()} (${item.message})`);
      if (item.sizeKb) lines.push(`    Size    : ${item.sizeKb} KB | Source: ${item.source || "Mirror"}`);
      if (item.landingUrl) lines.push(`    Gateway : ${item.landingUrl}`);
      lines.push("");
    });

    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Vellum_Batch_Report_${Date.now()}.txt`;
    a.click();
  };

  return (
    <div className="w-full space-y-6 animate-fade-in-up">
      {/* Top Banner Card */}
      <div className="fernly-card p-6 sm:p-8 rounded-[2rem] flex flex-col md:flex-row md:items-center justify-between gap-6 shadow-sm">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--panel)] text-[var(--g-500)] border border-[var(--hair)] shadow-xs flex-shrink-0">
            <DownloadCloud className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-[var(--ink)]">
                Academic Batch PDF Downloader
              </h2>
              <span className="fernly-badge fernly-badge-leaf text-[10px] font-semibold">
                Multi-Worker Mirror Protocol
              </span>
              <button
                onClick={() => setShowSettings(!showSettings)}
                className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-medium bg-[var(--panel)] border border-[var(--hair)] text-[var(--ink)] hover:border-[var(--g-500)] transition-all cursor-pointer"
              >
                <SlidersHorizontal className="h-3 w-3 text-[var(--g-500)]" />
                <span>Bypass & Settings</span>
                {showSettings ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
              </button>
            </div>
            <p className="text-xs text-[var(--muted)] mt-1 font-medium leading-relaxed max-w-2xl">
              High-velocity PDF resolution based on the Vellum Desktop protocol. Parses BibTeX, CSV, RIS, and text callsets to extract valid DOIs and downloads them across Unpaywall, arXiv, Europe PMC, Semantic Scholar, and Open Mirrors.
            </p>
          </div>
        </div>

        {/* Quick Stats Pill */}
        <div className="flex items-center gap-3 bg-[var(--panel)] p-2.5 rounded-2xl border border-[var(--hair)]">
          <div className="text-center px-3">
            <span className="text-[10px] font-semibold text-[var(--muted)] block">Queue</span>
            <span className="text-base font-bold text-[var(--ink)]">{queue.length}</span>
          </div>
          <div className="h-6 w-px bg-[var(--hair)]" />
          <div className="text-center px-3">
            <span className="text-[10px] font-semibold text-[var(--g-500)] block">Downloaded</span>
            <span className="text-base font-bold text-[var(--g-500)]">{successCount}</span>
          </div>
          {paywalledCount > 0 && (
            <>
              <div className="h-6 w-px bg-[var(--hair)]" />
              <div className="text-center px-3">
                <span className="text-[10px] font-semibold text-amber-500 block">Paywalled</span>
                <span className="text-base font-bold text-amber-500">{paywalledCount}</span>
              </div>
            </>
          )}
          {failedCount > 0 && (
            <>
              <div className="h-6 w-px bg-[var(--hair)]" />
              <div className="text-center px-3">
                <span className="text-[10px] font-semibold text-rose-500 block">Failed</span>
                <span className="text-base font-bold text-rose-500">{failedCount}</span>
              </div>
            </>
          )}
        </div>
      </div>

      {/* Paywall Bypass & Resolver Settings Panel (Collapsible like Desktop App) */}
      {showSettings && (
        <div className="fernly-card p-5 sm:p-6 rounded-[1.75rem] border border-[var(--hair)] space-y-4 animate-fade-in-up bg-[var(--panel)]">
          <div className="flex items-center justify-between pb-3 border-b border-[var(--hair)]">
            <div className="flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-[var(--g-500)]" />
              <h3 className="text-xs font-bold uppercase tracking-wider text-[var(--ink)]">
                Paywall Bypass & Resolver Settings (Desktop Protocol)
              </h3>
            </div>
            <span className="text-[10px] text-[var(--muted)]">Settings auto-save to local session</span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Researcher / Unpaywall Email */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-[var(--ink)] flex items-center gap-1.5">
                <Mail className="h-3.5 w-3.5 text-[var(--g-500)]" />
                <span>Email (Unpaywall & OpenAlex)</span>
              </label>
              <input
                type="email"
                value={unpaywallEmail}
                onChange={(e) => handleEmailChange(e.target.value)}
                placeholder="researcher@university.edu"
                className="fernly-input w-full rounded-xl text-xs"
              />
              <p className="text-[10px] text-[var(--muted)] leading-tight">
                Used to query Unpaywall & OpenAlex polite pools for institutional preprints and author green OA copies.
              </p>
            </div>

            {/* 2. Elsevier / Scopus API Key */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-[var(--ink)] flex items-center gap-1.5">
                <Key className="h-3.5 w-3.5 text-amber-500" />
                <span>Elsevier Key (dev.elsevier.com)</span>
              </label>
              <input
                type="password"
                value={elsevierApiKey}
                onChange={(e) => handleElsevierChange(e.target.value)}
                placeholder="Paste free Elsevier API key..."
                className="fernly-input w-full rounded-xl text-xs font-mono"
              />
              <p className="text-[10px] text-[var(--muted)] leading-tight">
                Unlocks direct automated PDF download for ScienceDirect (10.1016) papers without bot challenges.
              </p>
            </div>

            {/* 3. Primary Academic Mirror (Sci-Hub) */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-[var(--ink)] flex items-center gap-1.5">
                <Globe className="h-3.5 w-3.5 text-[var(--sky)]" />
                <span>Academic Mirror (Sci-Hub)</span>
              </label>
              <select
                value={scihubMirror}
                onChange={(e) => handleMirrorChange(e.target.value)}
                className="fernly-input w-full rounded-xl text-xs"
              >
                {SCIHUB_MIRROR_OPTIONS.map((m) => (
                  <option key={m} value={m}>
                    {m}
                  </option>
                ))}
              </select>
              <p className="text-[10px] text-[var(--muted)] leading-tight">
                Primary open mirror checked when publishers restrict direct open access.
              </p>
            </div>

            {/* 4. University EZProxy Gateway Prefix */}
            <div className="space-y-1.5">
              <label className="text-[11px] font-bold text-[var(--ink)] flex items-center gap-1.5">
                <Building2 className="h-3.5 w-3.5 text-purple-400" />
                <span>University Library EZProxy</span>
              </label>
              <input
                type="text"
                value={ezproxyUrl}
                onChange={(e) => handleEzproxyChange(e.target.value)}
                placeholder="https://login.ezproxy.univ.edu/login?url="
                className="fernly-input w-full rounded-xl text-xs font-mono"
              />
              <p className="text-[10px] text-[var(--muted)] leading-tight">
                Prepended to publisher gateway links so you can log in through your university library.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Import Feedback Banner */}
      {importSummary && (
        <div className="p-4 rounded-2xl bg-[var(--panel)] border border-[var(--hair)] flex items-center justify-between gap-4 text-xs animate-fade-in-up">
          <div className="flex items-center gap-3">
            <div className="h-8 w-8 rounded-full bg-[var(--g-100)] text-[var(--g-500)] flex items-center justify-center flex-shrink-0">
              <CheckCircle2 className="h-4 w-4" />
            </div>
            <div>
              <p className="font-bold text-[var(--ink)]">
                {importSummary.fileName ? `Import: ${importSummary.fileName}` : "DOIs Processed"}
              </p>
              <p className="text-[11px] text-[var(--muted)] mt-0.5">
                Added <strong className="text-[var(--g-500)]">{importSummary.validWithDoi} new papers</strong> to queue.
                {importSummary.duplicatesRemoved > 0 && ` Detected and merged ${importSummary.duplicatesRemoved} duplicate entries.`}
                {importSummary.skippedWithoutDoi > 0 && ` Filtered out ${importSummary.skippedWithoutDoi} non-paper rows.`}
                {" "}Total queue: <strong className="text-[var(--ink)]">{queue.length} items</strong>.
              </p>
            </div>
          </div>
          <button
            onClick={() => setImportSummary(null)}
            className="p-1 rounded-full text-[var(--muted)] hover:text-[var(--ink)] cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}

      {/* Progress Bar */}
      {queue.length > 0 && (isProcessing || completedCount > 0) && (
        <div className="fernly-card p-4 rounded-2xl space-y-2">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2">
              {isProcessing ? (
                <span className="flex items-center gap-1.5 font-bold text-[var(--g-500)]">
                  <span className="h-2 w-2 rounded-full bg-[var(--g-500)] animate-ping" />
                  3-Worker Concurrency Engine Running...
                </span>
              ) : (
                <span className="font-semibold text-[var(--muted)]">Batch Resolution Progress</span>
              )}
            </div>
            <span className="font-bold text-[var(--ink)]">
              {completedCount} / {queue.length} ({progressPercent}%)
            </span>
          </div>
          <div className="w-full h-2.5 rounded-full bg-[var(--panel)] border border-[var(--hair)] overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-[var(--g-600)] to-[var(--g-400)] transition-all duration-300"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
      )}

      {/* Main Grid: Input Form (Left) & Resolution Queue (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Input Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="fernly-card p-5 sm:p-6 rounded-[1.75rem] space-y-4">
            {/* Input Mode Selector */}
            <div className="flex items-center justify-between pb-3 border-b border-[var(--hair)]">
              <div className="flex items-center gap-1 bg-[var(--panel)] p-1 rounded-full border border-[var(--hair)] text-xs">
                <button
                  onClick={() => setActiveTab("text")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                    activeTab === "text"
                      ? "bg-[var(--g-700)] text-white shadow-xs"
                      : "text-[var(--muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  Paste DOIs
                </button>
                <button
                  onClick={() => setActiveTab("file")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                    activeTab === "file"
                      ? "bg-[var(--g-700)] text-white shadow-xs"
                      : "text-[var(--muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  Upload File
                </button>
              </div>

              {activeTab === "text" && (
                <button
                  onClick={() => {
                    setInputText(SAMPLE_DOIS.join("\n"));
                    const { candidates, summary } = parseInputFilesToCandidates(SAMPLE_DOIS.join("\n"), "Sample DOIs");
                    setQueue(toQueueItems(candidates));
                    setImportSummary(summary);
                  }}
                  className="text-[11px] text-[var(--g-500)] hover:underline font-semibold cursor-pointer"
                >
                  Load sample DOIs
                </button>
              )}
            </div>

            {/* Input Area */}
            {activeTab === "text" ? (
              <div className="space-y-2">
                <label className="block text-xs font-bold text-[var(--ink)]">
                  Enter List of DOIs or Article URLs (one per line):
                </label>
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="10.1057/s41270-026-00470-6&#10;10.1016/S2214-109X(23)00000-0&#10;10.1038/s41586-023-00000-0&#10;https://doi.org/10.48550/arXiv.2303.08774"
                  rows={8}
                  className="fernly-input w-full font-mono text-xs leading-relaxed resize-none rounded-xl"
                />
              </div>
            ) : (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="block text-xs font-bold text-[var(--ink)]">
                    Upload BibTeX (.bib), CSV, TSV, or RIS files:
                  </label>
                  <span className="text-[10px] text-[var(--g-500)] font-semibold">Multi-file auto-merge</span>
                </div>
                <div className="border-2 border-dashed border-[var(--hair)] hover:border-[var(--g-500)] rounded-2xl p-6 text-center cursor-pointer bg-[var(--panel)] transition-colors">
                  <input
                    type="file"
                    multiple
                    accept=".bib,.ris,.csv,.tsv,.txt"
                    onChange={handleFileUpload}
                    className="block w-full text-xs text-[var(--muted)] file:mr-2 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-[var(--g-700)] file:text-white cursor-pointer"
                  />
                  <p className="text-[11px] text-[var(--muted)] mt-2 font-medium">
                    Select one or multiple files. The engine automatically filters spurious fields, detects duplicates, and merges new papers into your active queue.
                  </p>
                </div>
              </div>
            )}

            {/* Target Notebook Attachment */}
            <div className="space-y-1.5 pt-2">
              <label className="block text-xs font-semibold text-[var(--ink)] flex items-center justify-between">
                <span>Attach to Project Notebook (Optional):</span>
                <span className="text-[10px] text-[var(--muted)]">Local Vault</span>
              </label>
              <select
                value={selectedNotebookId}
                onChange={(e) => setSelectedNotebookId(e.target.value)}
                className="fernly-input w-full rounded-xl text-xs font-medium"
              >
                <option value="">Do not attach (standalone download)</option>
                {notebooks.map((nb) => (
                  <option key={nb.id} value={nb.id}>
                    {nb.emoji} {nb.title} ({nb.sourcesCount || 0} papers)
                  </option>
                ))}
              </select>
            </div>

            {/* Actions Button */}
            <div className="flex items-center gap-2 pt-2">
              {activeTab === "text" && (
                <button
                  onClick={handleQueueText}
                  disabled={!inputText.trim()}
                  className="btn-fernly-ghost flex-1 py-2.5 rounded-full text-xs font-semibold disabled:opacity-50 cursor-pointer"
                >
                  Import to Queue
                </button>
              )}
              <button
                onClick={() => {
                  setInputText("");
                  setQueue([]);
                  setImportSummary(null);
                }}
                className="p-2.5 rounded-full border border-[var(--hair)] hover:bg-rose-500/10 text-rose-500 cursor-pointer"
                title="Clear input and queue"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Resolution Queue & Execution */}
        <div className="lg:col-span-7 space-y-4">
          <div className="fernly-card p-5 sm:p-6 rounded-[1.75rem] flex flex-col min-h-[440px]">
            {/* Queue Header & Action Controls */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[var(--hair)]">
              <div>
                <h3 className="text-sm font-bold text-[var(--ink)] tracking-tight">
                  Download Queue ({queue.length})
                </h3>
                <p className="text-[11px] text-[var(--muted)] font-medium">
                  Multi-tier resolution across open mirrors and academic gateways
                </p>
              </div>

              <div className="flex items-center gap-2 flex-wrap">
                {/* Retry Failed */}
                {(failedCount > 0 || paywalledCount > 0) && !isProcessing && (
                  <button
                    onClick={handleRetryFailed}
                    className="btn-fernly-ghost px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-1.5"
                    title="Retry failed or paywalled items with active bypass settings"
                  >
                    <RotateCw className="h-3.5 w-3.5" />
                    <span>Retry ({failedCount + paywalledCount})</span>
                  </button>
                )}

                {/* Save All Downloaded */}
                {successCount > 0 && (
                  <button
                    onClick={handleDownloadAllRetrieved}
                    className="btn-fernly-ghost px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-1.5 text-[var(--g-500)]"
                    title="Download all successfully retrieved PDFs to your computer"
                  >
                    <Download className="h-3.5 w-3.5" />
                    <span>Save All ({successCount})</span>
                  </button>
                )}

                {/* Export Report */}
                {queue.length > 0 && (
                  <button
                    onClick={handleExportReport}
                    className="btn-fernly-ghost px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-1.5"
                    title="Export download audit report"
                  >
                    <FileText className="h-3.5 w-3.5" />
                    <span>Report</span>
                  </button>
                )}

                {/* Clear Queue */}
                {queue.length > 0 && !isProcessing && (
                  <button
                    onClick={() => {
                      if (confirm("Clear all items from the download queue?")) {
                        setQueue([]);
                        setImportSummary(null);
                      }
                    }}
                    className="btn-fernly-ghost px-2.5 py-1.5 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-1 text-[var(--muted)] hover:text-rose-500"
                    title="Clear current queue"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span>Clear</span>
                  </button>
                )}

                {/* Start / Pause Button */}
                {isProcessing ? (
                  <button
                    onClick={handlePauseDownload}
                    className="btn-fernly-ghost px-4 py-2 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-1.5 text-amber-500 border-amber-500/30"
                  >
                    <Pause className="h-3.5 w-3.5" />
                    <span>Pause</span>
                  </button>
                ) : (
                  <button
                    onClick={handleStartDownload}
                    disabled={queue.length === 0 || completedCount === queue.length}
                    className="btn-fernly-primary px-5 py-2 rounded-full text-xs font-semibold shadow-xs disabled:opacity-50 cursor-pointer flex items-center gap-2"
                  >
                    <Play className="h-3.5 w-3.5 fill-current" />
                    <span>Start Download</span>
                  </button>
                )}
              </div>
            </div>

            {/* Queue Items List */}
            <div className="flex-1 overflow-y-auto mt-4 space-y-2.5 max-h-[500px]">
              {queue.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-center text-xs text-[var(--muted)]">
                  <FolderDown className="h-10 w-10 opacity-30 mb-2 text-[var(--muted)]" />
                  <p className="font-semibold text-[var(--ink)]">Queue is empty</p>
                  <p className="text-[11px] mt-1 max-w-xs text-[var(--muted)]">
                    Upload a BibTeX, CSV, or RIS file, or paste DOIs to launch parallel batch downloads.
                  </p>
                </div>
              ) : (
                queue.map((item, idx) => (
                  <div
                    key={item.id}
                    className="p-3.5 rounded-2xl bg-[var(--panel)] border border-[var(--hair)] flex items-center justify-between gap-3 transition-all"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="h-7 w-7 rounded-full bg-[var(--card)] border border-[var(--hair)] flex items-center justify-center flex-shrink-0 text-[11px] font-bold text-[var(--ink)]">
                        {idx + 1}
                      </div>
                      <div className="min-w-0">
                        {/* Title */}
                        <p className="text-xs font-semibold text-[var(--ink)] truncate max-w-lg">
                          {item.title}
                        </p>
                        {/* Author & Journal line */}
                        {(item.authors || item.year || item.journal) && (
                          <p className="text-[11px] text-[var(--muted)] truncate max-w-lg mt-0.5">
                            {item.authors}
                            {item.year ? ` (${item.year})` : ""}
                            {item.journal ? ` · ${item.journal}` : ""}
                          </p>
                        )}
                        {/* DOI badge & Status message */}
                        <div className="flex items-center gap-2 mt-1 flex-wrap">
                          <span className="text-[10px] font-mono font-medium text-[var(--muted)] bg-[var(--card)] px-1.5 py-0.5 rounded border border-[var(--hair)]">
                            {item.doi}
                          </span>
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                              item.status === "success"
                                ? "bg-emerald-500/10 text-emerald-400 border-emerald-500/30"
                                : item.status === "resolving"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/30 animate-pulse"
                                : item.status === "paywalled"
                                ? "bg-amber-500/10 text-amber-400 border-amber-500/30"
                                : item.status === "failed"
                                ? "bg-rose-500/10 text-rose-400 border-rose-500/30"
                                : "bg-[var(--card)] text-[var(--muted)] border-[var(--hair)]"
                            }`}
                          >
                            {item.status.toUpperCase()}
                          </span>
                          <span className="text-[11px] text-[var(--muted)] truncate">
                            {item.message}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Action on Item */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {item.pdfBlob && (
                        <button
                          onClick={() => {
                            const safeName = (item.title || item.doi).replace(/[^a-zA-Z0-9_\-]/g, "_").substring(0, 60);
                            triggerBrowserFileDownload(item.pdfBlob!, `${safeName}.pdf`);
                          }}
                          className="btn-fernly-primary px-3 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1 cursor-pointer shadow-xs"
                          title="Save PDF to device"
                        >
                          <Zap className="h-3 w-3 text-white" />
                          <span>Save PDF</span>
                        </button>
                      )}

                      {(item.status === "paywalled" || item.status === "failed") && (
                        <button
                          onClick={() => handleRetryItem(idx)}
                          disabled={isProcessing}
                          className="btn-fernly-ghost p-1.5 rounded-full text-xs font-semibold cursor-pointer text-[var(--ink)] hover:text-[var(--g-500)]"
                          title="Retry resolving this paper with active bypass settings"
                        >
                          <RotateCw className="h-3 w-3" />
                        </button>
                      )}

                      {item.landingUrl && (
                        <a
                          href={ezproxyUrl ? (ezproxyUrl.includes("url=") ? `${ezproxyUrl}${item.landingUrl}` : `${ezproxyUrl.replace(/\/$/, "")}/${item.landingUrl}`) : item.landingUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-fernly-ghost px-2.5 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1 text-[var(--ink)]"
                          title={ezproxyUrl ? "Open via university EZProxy library" : "Open publisher landing page"}
                        >
                          <span>Gateway</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
