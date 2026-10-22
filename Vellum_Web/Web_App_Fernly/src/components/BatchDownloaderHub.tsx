"use client";

import React, { useState } from "react";
import { Notebook } from "@/lib/db";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload } from "@/lib/pdfDownloader";
import {
  DownloadCloud,
  Zap,
  ExternalLink,
  ArrowUpRight,
  FolderDown,
  Trash2,
} from "lucide-react";

interface BatchDownloaderHubProps {
  notebooks: Notebook[];
}

interface QueueItem {
  id: string;
  raw: string;
  doi: string;
  title?: string;
  status: "idle" | "resolving" | "success" | "paywalled" | "failed";
  message: string;
  source?: string;
  sizeKb?: number;
  pdfBlob?: Blob;
  landingUrl?: string;
}

const SAMPLE_DOIS = [
  "10.1016/S2214-109X(23)00000-0",
  "10.1038/s41586-023-00000-0",
  "10.48550/arXiv.2303.08774",
  "10.1101/2023.01.01.522432",
  "10.1371/journal.pone.0280000",
];

export function BatchDownloaderHub({ notebooks }: BatchDownloaderHubProps) {
  const [inputText, setInputText] = useState("");
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>("");
  const [queue, setQueue] = useState<QueueItem[]>([]);
  const [isProcessing, setIsProcessing] = useState(false);
  const [activeTab, setActiveTab] = useState<"text" | "file">("text");

  // Parse DOIs or URLs from text
  const extractItems = (text: string): string[] => {
    const rawTokens = text.split(/[\n,;]+/);
    const results: string[] = [];
    for (const t of rawTokens) {
      const trimmed = t.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      // Match DOI or URL
      const doiMatch = trimmed.match(/10\.\d{4,9}\/[-._;()/:A-Za-z0-9]+/);
      if (doiMatch) {
        results.push(doiMatch[0]);
      } else if (trimmed.startsWith("http://") || trimmed.startsWith("https://")) {
        results.push(trimmed);
      } else if (trimmed.length > 5) {
        results.push(trimmed);
      }
    }
    return Array.from(new Set(results));
  };

  const handleQueueItems = () => {
    const items = extractItems(inputText);
    if (items.length === 0) return;

    const newQueue: QueueItem[] = items.map((item, idx) => ({
      id: `queue-${Date.now()}-${idx}`,
      raw: item,
      doi: item.startsWith("10.") ? item : item.replace(/^https?:\/\/doi\.org\//, ""),
      title: `Academic Publication (${item.substring(0, 24)}...)`,
      status: "idle",
      message: "Ready to resolve",
    }));

    setQueue(newQueue);
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const content = event.target?.result as string;
      if (content) {
        setInputText(content);
        const items = extractItems(content);
        const newQueue: QueueItem[] = items.map((item, idx) => ({
          id: `queue-${Date.now()}-${idx}`,
          raw: item,
          doi: item.startsWith("10.") ? item : item.replace(/^https?:\/\/doi\.org\//, ""),
          title: `Academic Item (${item.substring(0, 24)}...)`,
          status: "idle",
          message: "Imported from file",
        }));
        setQueue(newQueue);
      }
    };
    reader.readAsText(file);
  };

  const handleStartDownload = async () => {
    if (queue.length === 0 || isProcessing) return;
    setIsProcessing(true);

    for (let i = 0; i < queue.length; i++) {
      const item = queue[i];
      if (item.status === "success") continue;

      setQueue((prev) =>
        prev.map((q, idx) =>
          idx === i ? { ...q, status: "resolving", message: "Searching multi-tier sources..." } : q
        )
      );

      try {
        const res = await fetchAndStorePaperPdf(
          {
            doi: item.doi,
            title: item.title || item.doi,
            notebookId: selectedNotebookId || undefined,
          },
          (status, details) => {
            setQueue((prev) =>
              prev.map((q, idx) => (idx === i ? { ...q, message: details || status } : q))
            );
          }
        );

        if (res.success && res.blob) {
          const sizeKb = Math.round(res.blob.size / 1024);
          setQueue((prev) =>
            prev.map((q, idx) =>
              idx === i
                ? {
                    ...q,
                    status: "success",
                    message: `Downloaded (${sizeKb} KB)`,
                    pdfBlob: res.blob,
                    sizeKb,
                    source: res.sourceName || "Multi-Tier",
                  }
                : q
            )
          );
        } else if (res.landingUrl) {
          setQueue((prev) =>
            prev.map((q, idx) =>
              idx === i
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
              idx === i
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
            idx === i
              ? {
                  ...q,
                  status: "failed",
                  message: err instanceof Error ? err.message : "Network error",
                }
              : q
          )
        );
      }
    }

    setIsProcessing(false);
  };

  const successCount = queue.filter((q) => q.status === "success").length;
  const paywalledCount = queue.filter((q) => q.status === "paywalled").length;
  const failedCount = queue.filter((q) => q.status === "failed").length;

  const handleExportReport = () => {
    if (queue.length === 0) return;
    const now = new Date().toISOString();
    const lines = [
      "=======================================================================",
      "  VELLUM ACADEMIC PDF BATCH DOWNLOAD REPORT",
      "=======================================================================",
      `  Generated on : ${now}`,
      `  Total items  : ${queue.length}`,
      `  Downloaded   : ${successCount}`,
      `  Paywalled    : ${paywalledCount}`,
      `  Failed       : ${failedCount}`,
      "=======================================================================",
      "",
      "RESOLVED PAPERS:",
      "-----------------------------------------------------------------------",
    ];

    queue.forEach((item, idx) => {
      lines.push(`[${idx + 1}] ${item.doi}`);
      lines.push(`    Status: ${item.status.toUpperCase()} (${item.message})`);
      if (item.sizeKb) lines.push(`    Size: ${item.sizeKb} KB | Source: ${item.source || "Mirror"}`);
      if (item.landingUrl) lines.push(`    Gateway: ${item.landingUrl}`);
      lines.push("");
    });

    const blob = new Blob([lines.join("\n")], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `Vellum_Batch_Download_Report_${Date.now()}.txt`;
    a.click();
  };

  return (
    <div className="w-full space-y-6 animate-fade-in-up">
      {/* Top Banner Card */}
      <div className="fernly-card p-6 sm:p-8 rounded-[2rem] flex flex-col md:flex-row md:items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-[var(--g-950)] text-[var(--g-300)] border border-[var(--g-800)] shadow-xs flex-shrink-0">
            <DownloadCloud className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-lg sm:text-xl font-bold tracking-tight text-[var(--ink)]">
                Academic Batch PDF Downloader
              </h2>
              <span className="fernly-badge fernly-badge-leaf text-[10px] font-semibold">
                Multi-Tier Mirror Protocol
              </span>
            </div>
            <p className="text-xs text-[var(--ink-muted)] mt-1 font-medium leading-relaxed max-w-2xl">
              Incorporate high-velocity paper downloads from the desktop engine. Resolve and download batches of DOIs across Unpaywall, arXiv, Europe PMC, Semantic Scholar, and Sci-Hub mirrors.
            </p>
          </div>
        </div>

        {/* Quick Stats Pill */}
        <div className="flex items-center gap-3 bg-[var(--panel)] p-2 rounded-2xl border border-[var(--card-bdr)]">
          <div className="text-center px-3">
            <span className="text-[10px] font-semibold text-[var(--ink-muted)] block">In Queue</span>
            <span className="text-sm font-bold text-[var(--ink)]">{queue.length}</span>
          </div>
          <div className="h-6 w-px bg-[var(--card-bdr)]" />
          <div className="text-center px-3">
            <span className="text-[10px] font-semibold text-[var(--g-600)] block">Downloaded</span>
            <span className="text-sm font-bold text-[var(--g-700)] dark:text-[var(--g-300)]">{successCount}</span>
          </div>
        </div>
      </div>

      {/* Main Grid: Input Form (Left) & Live Resolution Queue (Right) */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* LEFT COLUMN: Input Form */}
        <div className="lg:col-span-5 space-y-4">
          <div className="fernly-card p-5 sm:p-6 rounded-[1.75rem] space-y-4">
            {/* Input Mode Selector */}
            <div className="flex items-center justify-between pb-3 border-b border-[var(--card-bdr)]">
              <div className="flex items-center gap-1 bg-[var(--panel)] p-1 rounded-full border border-[var(--card-bdr)] text-xs">
                <button
                  onClick={() => setActiveTab("text")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                    activeTab === "text"
                      ? "bg-[var(--g-800)] text-white shadow-xs"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  Paste DOIs
                </button>
                <button
                  onClick={() => setActiveTab("file")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                    activeTab === "file"
                      ? "bg-[var(--g-800)] text-white shadow-xs"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  Upload File
                </button>
              </div>

              {activeTab === "text" && (
                <button
                  onClick={() => setInputText(SAMPLE_DOIS.join("\n"))}
                  className="text-[11px] text-[var(--g-600)] dark:text-[var(--g-400)] hover:underline font-semibold cursor-pointer"
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
                  placeholder="10.1016/S2214-109X(23)00000-0&#10;10.1038/s41586-023-00000-0&#10;https://doi.org/10.48550/arXiv.2303.08774"
                  rows={8}
                  className="fernly-input w-full font-mono text-xs leading-relaxed resize-none rounded-xl"
                />
              </div>
            ) : (
              <div className="space-y-2">
                <label className="block text-xs font-bold text-[var(--ink)]">
                  Upload CSV, TXT, or BibTeX containing DOIs:
                </label>
                <div className="border-2 border-dashed border-[var(--card-bdr)] hover:border-[var(--g-500)] rounded-2xl p-6 text-center cursor-pointer bg-[var(--panel)] transition-colors">
                  <input
                    type="file"
                    accept=".txt,.csv,.bib,.ris"
                    onChange={handleFileUpload}
                    className="block w-full text-xs text-[var(--ink-muted)] file:mr-2 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-[var(--g-800)] file:text-white cursor-pointer"
                  />
                  <p className="text-[11px] text-[var(--ink-muted)] mt-2 font-medium">
                    Automatically extracts all identifiers matching 10.xxxx/...
                  </p>
                </div>
              </div>
            )}

            {/* Optional Target Notebook Attachment */}
            <div className="space-y-1.5 pt-2">
              <label className="block text-xs font-semibold text-[var(--ink)] flex items-center justify-between">
                <span>Attach to Notebook (Optional):</span>
                <span className="text-[10px] text-[var(--ink-muted)]">IndexedDB</span>
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
              <button
                onClick={handleQueueItems}
                disabled={!inputText.trim()}
                className="btn-fernly-ghost flex-1 py-2.5 rounded-full text-xs font-semibold disabled:opacity-50 cursor-pointer"
              >
                Import to Queue
              </button>
              <button
                onClick={() => {
                  setInputText("");
                  setQueue([]);
                }}
                className="p-2.5 rounded-full border border-[var(--card-bdr)] hover:bg-red-50 dark:hover:bg-red-950/30 text-red-600 dark:text-red-400 cursor-pointer"
                title="Clear input and queue"
              >
                <Trash2 className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* RIGHT COLUMN: Resolution Queue & Execution */}
        <div className="lg:col-span-7 space-y-4">
          <div className="fernly-card p-5 sm:p-6 rounded-[1.75rem] flex flex-col min-h-[420px]">
            {/* Queue Header & Actions */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-4 border-b border-[var(--card-bdr)]">
              <div>
                <h3 className="text-sm font-bold text-[var(--ink)] tracking-tight">
                  Download Queue ({queue.length})
                </h3>
                <p className="text-[11px] text-[var(--ink-muted)] font-medium">
                  Multi-tier resolution across open mirrors and academic gateways
                </p>
              </div>

              <div className="flex items-center gap-2">
                {queue.length > 0 && (
                  <button
                    onClick={handleExportReport}
                    className="btn-fernly-ghost px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer"
                  >
                    Export Report
                  </button>
                )}
                <button
                  onClick={handleStartDownload}
                  disabled={queue.length === 0 || isProcessing}
                  className="btn-fernly-primary px-5 py-2 rounded-full text-xs font-semibold shadow-xs disabled:opacity-50 cursor-pointer flex items-center gap-2"
                >
                  {isProcessing ? (
                    <span className="animate-pulse">Resolving Papers...</span>
                  ) : (
                    <>
                      <span>Start Download</span>
                      <span className="fernly-arrow bg-white/20 text-white w-4 h-4 rounded-full flex items-center justify-center">
                        <ArrowUpRight className="h-3 w-3" />
                      </span>
                    </>
                  )}
                </button>
              </div>
            </div>

            {/* Queue List */}
            <div className="flex-1 overflow-y-auto mt-4 space-y-2.5 max-h-[480px]">
              {queue.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-64 text-center text-xs text-[var(--ink-muted)]">
                  <FolderDown className="h-10 w-10 opacity-30 mb-2 text-[var(--ink-muted)]" />
                  <p className="font-semibold text-[var(--ink)]">Queue is empty</p>
                  <p className="text-[11px] mt-1 max-w-xs">
                    Paste DOIs on the left or click &quot;Load sample DOIs&quot; to test the multi-tier downloader.
                  </p>
                </div>
              ) : (
                queue.map((item, idx) => (
                  <div
                    key={item.id}
                    className="p-3.5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] flex items-center justify-between gap-3 transition-all"
                  >
                    <div className="flex items-start gap-3 min-w-0">
                      <div className="h-7 w-7 rounded-full bg-[var(--card)] border border-[var(--card-bdr)] flex items-center justify-center flex-shrink-0 text-[11px] font-bold text-[var(--ink)]">
                        {idx + 1}
                      </div>
                      <div className="min-w-0">
                        <span className="text-xs font-bold text-[var(--ink)] truncate block font-mono">
                          {item.doi}
                        </span>
                        <div className="flex items-center gap-2 mt-0.5 flex-wrap">
                          <span
                            className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                              item.status === "success"
                                ? "bg-[var(--g-100)] text-[var(--g-800)] border-[var(--g-300)] dark:bg-[var(--g-900)] dark:text-[var(--g-200)]"
                                : item.status === "resolving"
                                ? "bg-amber-100 text-amber-800 border-amber-300 dark:bg-amber-950 dark:text-amber-200 animate-pulse"
                                : item.status === "paywalled"
                                ? "bg-rose-100 text-rose-800 border-rose-300 dark:bg-rose-950 dark:text-rose-200"
                                : "bg-[var(--card)] text-[var(--ink-muted)] border-[var(--card-bdr)]"
                            }`}
                          >
                            {item.status.toUpperCase()}
                          </span>
                          <span className="text-[11px] text-[var(--ink-muted)] truncate">
                            {item.message}
                          </span>
                        </div>
                      </div>
                    </div>

                    {/* Action on Item */}
                    <div className="flex items-center gap-2 flex-shrink-0">
                      {item.pdfBlob && (
                        <button
                          onClick={() => triggerBrowserFileDownload(item.pdfBlob!, item.doi)}
                          className="btn-fernly-primary px-3 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1 cursor-pointer shadow-xs"
                          title="Save PDF to device"
                        >
                          <Zap className="h-3 w-3 text-white" />
                          <span>Save PDF</span>
                        </button>
                      )}

                      {item.landingUrl && (
                        <a
                          href={item.landingUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="btn-fernly-ghost px-2.5 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1 text-[var(--ink)]"
                          title="Open publisher landing page"
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
