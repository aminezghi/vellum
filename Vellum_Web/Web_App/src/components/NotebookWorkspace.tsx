"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Notebook, Source, EvidenceExtraction, db } from "@/lib/db";
import { initializeAppearance, setTheme, useTheme } from "@/lib/theme";
import { Modal } from "@/components/Modal";
import { fetchAndStorePaperPdf } from "@/lib/pdfDownloader";
import { AcademicPaperResult } from "@/app/api/search/route";
import {
  ArrowLeft,
  Plus,
  FileText,
  Search,
  Download,
  BookOpen,
  ZoomIn,
  ZoomOut,
  Quote,
  CheckCircle2,
  Sparkles,
  Layers,
  ExternalLink,
  Zap,
  AlertCircle,
  Trash2,
  Sun,
  Moon,
  BookmarkPlus,
  Upload,
  Share2,
} from "lucide-react";

interface NotebookWorkspaceProps {
  notebook: Notebook;
  onBack: () => void;
  onUpdate: () => void;
  onOpenConnectedGraph?: (seed: string) => void;
}

/**
 * Store a paper as a source of a notebook and keep the notebook's counters in
 * step, in one transaction-ish sequence.
 *
 * This lives outside the component because it mints an id and reads the clock:
 * work that is not idempotent must not run during a render, and a module-level
 * function makes that impossible to accidentally reintroduce.
 */
async function addPaperToNotebook(
  paper: AcademicPaperResult,
  notebookId: string
): Promise<Source> {
  const now = Date.now();
  const source: Source = {
    id: `src-${now}-${Math.random().toString(36).substring(2, 6)}`,
    notebookId,
    title: paper.title,
    authors: paper.authors,
    year: paper.year,
    journal: paper.venue,
    doi: paper.doi,
    abstract: paper.abstract,
    status: "ready",
    addedAt: now,
  };

  await db.sources.put(source);
  const count = await db.sources.where("notebookId").equals(notebookId).count();
  await db.notebooks.update(notebookId, { sourcesCount: count, updatedAt: now });
  return source;
}

export function NotebookWorkspace({
  notebook,
  onBack,
  onUpdate,
  onOpenConnectedGraph,
}: NotebookWorkspaceProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [activeTab, setActiveTab] = useState<"evidence" | "notes" | "export">("evidence");
  const [notesContent, setNotesContent] = useState("");
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isAddSourceOpen, setIsAddSourceOpen] = useState(false);
  const [sourceSearch, setSourceSearch] = useState("");
  const [viewMode, setViewMode] = useState<"reader" | "pdf">("reader");
  const [uploadProgress, setUploadProgress] = useState<{ current: number; total: number; name: string } | null>(null);
  const [copiedCitation, setCopiedCitation] = useState<string | null>(null);
  const [pdfFetchStatus, setPdfFetchStatus] = useState<{
    status: string;
    message: string;
    landingUrl?: string;
  } | null>(null);

  // In-Workspace Dynamic Evidence State
  const [evidenceItems, setEvidenceItems] = useState<EvidenceExtraction[]>([]);
  const [evidenceFilter, setEvidenceFilter] = useState<"current" | "all">("current");
  const [isAddClaimOpen, setIsAddClaimOpen] = useState(false);
  const [newClaimText, setNewClaimText] = useState("");
  const [newClaimQuote, setNewClaimQuote] = useState("");
  const [newClaimCategory, setNewClaimCategory] = useState<"method" | "sampling" | "statistics" | "rigour">("method");
  const [newClaimPage, setNewClaimPage] = useState<number | "">("");

  // In-Workspace Academic Search & Add Modal
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);
  const [searchModalQuery, setSearchModalQuery] = useState("");
  const [searchModalResults, setSearchModalResults] = useState<AcademicPaperResult[]>([]);
  const [searchModalLoading, setSearchModalLoading] = useState(false);
  const [searchModalOA, setSearchModalOA] = useState(true);
  const [addedIds, setAddedIds] = useState<Record<string, boolean>>({});

  const theme = useTheme();
  const isDarkMode = theme === "dark";

  useEffect(() => {
    // The workspace can be the first thing rendered after a reload, so make
    // sure the saved theme is applied before anything paints.
    initializeAppearance();
  }, []);

  const toggleTheme = () => {
    setTheme(isDarkMode ? "light" : "dark");
  };

  // Paper Management & Action Handlers (Delete, Replace PDF, Connected Papers)
  const replaceFileInputRef = React.useRef<HTMLInputElement>(null);
  const [sourceToReplaceId, setSourceToReplaceId] = useState<string | null>(null);

  const handleDeleteSource = async (e: React.MouseEvent, sourceId: string) => {
    e.stopPropagation();
    const sourceToDelete = sources.find((s) => s.id === sourceId);
    if (!sourceToDelete) return;

    if (!confirm(`Are you sure you want to remove "${sourceToDelete.title.slice(0, 50)}..." from this notebook?`)) {
      return;
    }

    await db.sources.delete(sourceId);
    await db.evidence.where("sourceId").equals(sourceId).delete();

    const remaining = sources.filter((s) => s.id !== sourceId);
    setSources(remaining);
    if (selectedSource?.id === sourceId) {
      setSelectedSource(remaining[0] || null);
    }
    const count = await db.sources.where("notebookId").equals(notebook.id).count();
    await db.notebooks.update(notebook.id, { sourcesCount: count, updatedAt: Date.now() });
    onUpdate();
  };

  const handleOpenReplaceDialog = (e: React.MouseEvent, sourceId: string) => {
    e.stopPropagation();
    setSourceToReplaceId(sourceId);
    replaceFileInputRef.current?.click();
  };

  const handleExecuteReplacePdf = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !sourceToReplaceId) return;

    const arrayBuffer = await file.arrayBuffer();
    const blob = new Blob([arrayBuffer], { type: "application/pdf" });

    await db.sources.update(sourceToReplaceId, {
      pdfBlob: blob,
      sizeBytes: file.size,
      status: "ready",
    });

    const refreshed = await db.sources.where("notebookId").equals(notebook.id).toArray();
    setSources(refreshed);

    const updatedSource = refreshed.find((s) => s.id === sourceToReplaceId);
    if (updatedSource && selectedSource?.id === sourceToReplaceId) {
      setSelectedSource(updatedSource);
      setViewMode("pdf");
    }

    setSourceToReplaceId(null);
    e.target.value = "";
    onUpdate();
  };

  const handleOpenConnectedPapers = (e: React.MouseEvent, source: Source) => {
    e.stopPropagation();
    const seed = source.doi ? `https://doi.org/${source.doi}` : source.title;
    onOpenConnectedGraph?.(seed);
  };

  const handleFetchPdfForSource = async () => {
    if (!selectedSource) return;
    setPdfFetchStatus({ status: "resolving", message: "Searching multi-tier sources..." });

    const res = await fetchAndStorePaperPdf(
      {
        doi: selectedSource.doi,
        title: selectedSource.title,
        sourceId: selectedSource.id,
        notebookId: notebook.id,
      },
      (status, details) => {
        setPdfFetchStatus({ status, message: details || "" });
      }
    );

    if (res.success && res.blob) {
      const updatedSource = {
        ...selectedSource,
        pdfBlob: res.blob,
        sizeBytes: res.blob.size,
      };
      setSelectedSource(updatedSource);
      setSources((prev) => prev.map((s) => (s.id === selectedSource.id ? updatedSource : s)));
      setViewMode("pdf");
      setPdfFetchStatus(null);
    } else if (res.landingUrl) {
      setPdfFetchStatus({
        status: "paywalled",
        message: "Protected by publisher paywall",
        landingUrl: res.landingUrl,
      });
    }
  };

  // Object URL for PDF blob if available
  const pdfBlobUrl = React.useMemo(() => {
    if (selectedSource?.pdfBlob) {
      try {
        return URL.createObjectURL(selectedSource.pdfBlob);
      } catch (err) {
        console.error("Error creating blob URL:", err);
        return null;
      }
    }
    return null;
  }, [selectedSource]);

  // Clean up object URL when source changes
  useEffect(() => {
    return () => {
      if (pdfBlobUrl) {
        URL.revokeObjectURL(pdfBlobUrl);
      }
    };
  }, [pdfBlobUrl]);

  // Load sources and notes from IndexedDB
  const reloadSources = async () => {
    const loadedSources = await db.sources.where("notebookId").equals(notebook.id).toArray();
    setSources(loadedSources);
    if (!selectedSource && loadedSources.length > 0) {
      setSelectedSource(loadedSources[0]);
    }
  };

  const reloadEvidence = useCallback(async () => {
    if (!notebook.id) return;
    const items = await db.evidence.where("notebookId").equals(notebook.id).toArray();
    setEvidenceItems(items);
  }, [notebook.id]);

  useEffect(() => {
    let isMounted = true;
    async function loadData() {
      const loadedSources = await db.sources.where("notebookId").equals(notebook.id).toArray();
      if (!isMounted) return;
      setSources(loadedSources);
      setSelectedSource(loadedSources.length > 0 ? loadedSources[0] : null);

      const items = await db.evidence.where("notebookId").equals(notebook.id).toArray();
      if (!isMounted) return;
      setEvidenceItems(items);

      const note = await db.notes.where("notebookId").equals(notebook.id).first();
      if (!isMounted) return;
      if (note) {
        setNotesContent(note.content);
      } else {
        const initialNote = `# Systematic Review Synthesis: ${notebook.title}\n\n## Research Objective\nSynthesizing comparative outcomes and methodological rigour across loaded evidence sources.\n\n## Grounded Evidence Claims\n`;
        setNotesContent(initialNote);
        await db.notes.put({
          id: `note-${notebook.id}`,
          notebookId: notebook.id,
          content: initialNote,
          updatedAt: Date.now(),
        });
      }
    }
    loadData();
    return () => {
      isMounted = false;
    };
  }, [notebook.id, notebook.title]);

  const handleSaveNotes = async (newContent: string) => {
    setNotesContent(newContent);
    await db.notes.put({
      id: `note-${notebook.id}`,
      notebookId: notebook.id,
      content: newContent,
      updatedAt: Date.now(),
    });
  };

  const handleInsertQuote = (quoteText: string, pageNum: number) => {
    const citation = `\n> "${quoteText}"\n> — *${selectedSource?.title || "Source"}*, Page ${pageNum}\n\n`;
    const updated = notesContent + citation;
    handleSaveNotes(updated);
    setActiveTab("notes");
  };

  const handleAddEvidenceClaim = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!newClaimText.trim() || !notebook.id || !selectedSource) return;

    const newClaim: EvidenceExtraction = {
      id: `evi-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      notebookId: notebook.id,
      sourceId: selectedSource.id,
      category: newClaimCategory,
      claim: newClaimText.trim(),
      quote: newClaimQuote.trim() || undefined,
      pageNumber: typeof newClaimPage === "number" ? newClaimPage : 1,
      confidence: 95,
      createdAt: Date.now(),
    };

    await db.evidence.put(newClaim);
    await reloadEvidence();
    setNewClaimText("");
    setNewClaimQuote("");
    setNewClaimPage("");
    setIsAddClaimOpen(false);
  };

  const handleDeleteEvidenceClaim = async (claimId: string) => {
    await db.evidence.delete(claimId);
    await reloadEvidence();
  };

  const handleExtractClaimFromText = async (text: string, sourceId: string) => {
    const summary = text.length > 200 ? text.substring(0, 197) + "..." : text;
    const newClaim: EvidenceExtraction = {
      id: `evi-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      notebookId: notebook.id,
      sourceId,
      category: "method",
      claim: summary,
      quote: text.length > 500 ? text.substring(0, 497) + "..." : text,
      pageNumber: 1,
      confidence: 95,
      createdAt: Date.now(),
    };
    await db.evidence.put(newClaim);
    await reloadEvidence();
    setActiveTab("evidence");
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const newFiles = Array.from(e.target.files);
    const total = newFiles.length;
    const now = Date.now();

    setUploadProgress({ current: 0, total, name: `Preparing ${total} file(s)...` });

    const newSources: Source[] = newFiles.map((f, i) => {
      // Clean title from filename
      const cleanTitle = f.name
        .replace(/\.pdf$/i, "")
        .replace(/^[a-zA-Z0-9_\-]+ - \d{4} - /, "") // remove Zotero prefix if present
        .replace(/_/g, " ");

      return {
        id: `src-${now}-${i}-${Math.random().toString(36).substring(2, 6)}`,
        notebookId: notebook.id,
        title: cleanTitle,
        authors: [f.name.includes(" - ") ? f.name.split(" - ")[0] : "Author"],
        year: parseInt((f.name.match(/\b(19|20)\d{2}\b/) || ["2024"])[0], 10),
        pdfBlob: f,
        sizeBytes: f.size,
        status: "ready",
        addedAt: now + i,
      };
    });

    setUploadProgress({ current: total, total, name: `Saving ${total} file(s) to vault...` });
    await db.sources.bulkPut(newSources);

    setUploadProgress(null);
    const count = await db.sources.where("notebookId").equals(notebook.id).count();
    await db.notebooks.update(notebook.id, { sourcesCount: count, updatedAt: Date.now() });
    const reloaded = await db.sources.where("notebookId").equals(notebook.id).toArray();
    setSources(reloaded);
    if (reloaded.length > 0) {
      setSelectedSource(reloaded[reloaded.length - 1]);
    }
    setIsAddSourceOpen(false);
    onUpdate();
  };

  // Search papers inside workspace modal
  const handleWorkspaceSearch = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!searchModalQuery.trim()) return;

    setSearchModalLoading(true);
    try {
      const params = new URLSearchParams({
        q: searchModalQuery.trim(),
        openAccessOnly: searchModalOA ? "true" : "false",
        sources: "openalex,arxiv,semanticscholar",
      });
      const res = await fetch(`/api/search?${params.toString()}`);
      if (!res.ok) throw new Error("Search failed");
      const data = await res.json();
      setSearchModalResults(data.results || []);
    } catch (err) {
      console.error("Workspace search error:", err);
      setSearchModalResults([]);
    } finally {
      setSearchModalLoading(false);
    }
  };

  const handleAddPaperFromSearch = async (paper: AcademicPaperResult, fetchPdfNow = false) => {
    const newSource = await addPaperToNotebook(paper, notebook.id);

    setAddedIds((prev) => ({ ...prev, [paper.id]: true }));
    await reloadSources();
    setSelectedSource(newSource);
    onUpdate();

    if (fetchPdfNow && paper.doi) {
      setIsSearchModalOpen(false);
      handleFetchPdfForSource();
    }
  };

  const handleCopyCitation = (format: "APA" | "BibTeX") => {
    if (!selectedSource) return;
    let text = "";
    if (format === "APA") {
      const authors = selectedSource.authors?.join(", ") || "Anonymous";
      text = `${authors} (${selectedSource.year || 2024}). ${selectedSource.title}. ${selectedSource.journal || ""}. https://doi.org/${selectedSource.doi || ""}`;
    } else {
      text = `@article{ref_${selectedSource.id},\n  title={${selectedSource.title}},\n  author={${selectedSource.authors?.join(" and ") || "Author"}},\n  year={${selectedSource.year || 2024}},\n  doi={${selectedSource.doi || ""}}\n}`;
    }
    navigator.clipboard.writeText(text);
    setCopiedCitation(format);
    setTimeout(() => setCopiedCitation(null), 2000);
  };

  const filteredSources = sources.filter((s) =>
    s.title.toLowerCase().includes(sourceSearch.toLowerCase())
  );

  return (
    <div className="flex flex-col h-screen w-full bg-[var(--bg)] text-[var(--ink)] overflow-hidden transition-colors duration-200">
      {/* Top Workspace Header */}
      <header className="flex items-center justify-between px-4 sm:px-6 lg:px-8 xl:px-10 py-3 border-b border-[var(--card-bdr)] bg-[var(--card)]/90 backdrop-blur-xl flex-shrink-0 z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="btn-fernly-ghost px-3.5 py-1.5 rounded-full text-[var(--ink)] flex items-center gap-1.5 text-xs font-semibold cursor-pointer"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">My notebooks</span>
          </button>
          <div className="h-4 w-px bg-[var(--card-bdr)]" />
          <div className="flex items-center gap-2.5">
            <span className="text-xl p-1.5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)]">
              {notebook.emoji}
            </span>
            <div>
              <h1 className="text-sm font-bold text-[var(--ink)] truncate max-w-xs sm:max-w-md tracking-tight">
                {notebook.title}
              </h1>
              <p className="text-[11px] text-[var(--ink-muted)] font-medium">
                {sources.length} {sources.length === 1 ? "source" : "sources"} loaded · 100% Local-First
              </p>
            </div>
          </div>
        </div>

        {/* Right Action Tools */}
        <div className="flex items-center gap-2">
          {/* Quick Search Button in Workspace Header */}
          <button
            onClick={() => setIsSearchModalOpen(true)}
            className="btn-fernly-ghost flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold text-[var(--ink)] cursor-pointer"
          >
            <Search className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
            <span className="hidden sm:inline">Search &amp; Add</span>
          </button>

          {/* Reading Mode / Dark Mode Toggle Button */}
          <button
            onClick={toggleTheme}
            className="p-2 rounded-full border border-[var(--card-bdr)] bg-[var(--panel)] text-[var(--ink)] hover:border-[var(--g-500)] transition-colors cursor-pointer shadow-xs flex items-center justify-center"
            title={isDarkMode ? "Switch to Linen Day Canvas" : "Switch to Deep Forest Dark Mode"}
          >
            {isDarkMode ? (
              <Sun className="h-4 w-4 text-[var(--g-300)]" />
            ) : (
              <Moon className="h-4 w-4 text-[var(--g-800)]" />
            )}
          </button>

          <button
            onClick={async () => {
              if (confirm(`Delete notebook "${notebook.title}" and its saved sources from storage?`)) {
                await db.notebooks.delete(notebook.id);
                await db.sources.where("notebookId").equals(notebook.id).delete();
                await db.notes.where("notebookId").equals(notebook.id).delete();
                await db.evidence.where("notebookId").equals(notebook.id).delete();
                onBack();
              }
            }}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-red-200 dark:border-red-900/40 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs font-medium transition-colors cursor-pointer shadow-xs"
            title="Delete this notebook"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Delete</span>
          </button>

          <button
            onClick={() => setActiveTab("export")}
            className="btn-fernly-primary flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold shadow-xs cursor-pointer"
          >
            <Download className="h-3.5 w-3.5" />
            <span>Export Citations</span>
          </button>
        </div>
      </header>

      {/* Tri-Pane Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* PANE 1: Sources Corpus (Left) */}
        <aside className="w-72 lg:w-80 flex flex-col border-r border-[var(--card-bdr)] bg-[var(--panel)] flex-shrink-0">
          <div className="p-3.5 border-b border-[var(--card-bdr)] flex items-center justify-between">
            <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" /> Sources ({sources.length})
            </span>
            <div className="flex items-center gap-1">
              <button
                onClick={() => setIsSearchModalOpen(true)}
                className="btn-fernly-ghost flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold cursor-pointer"
                title="Search academic literature directly to add"
              >
                <Search className="h-3 w-3" /> Search
              </button>
              <button
                onClick={() => setIsAddSourceOpen(!isAddSourceOpen)}
                className="btn-fernly-primary flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer shadow-xs"
              >
                <Plus className="h-3.5 w-3.5" /> Upload
              </button>
            </div>
          </div>

          {/* Add Source Drawer (Upload) */}
          {isAddSourceOpen && (
            <div className="p-3.5 bg-[var(--card)] border-b border-[var(--card-bdr)] space-y-2.5 animate-in fade-in duration-200">
              <label className="block text-xs font-semibold text-[var(--ink)]">Upload PDF(s)</label>
              <input
                type="file"
                multiple
                accept="application/pdf"
                onChange={handleFileUpload}
                className="block w-full text-xs text-[var(--ink-muted)] file:mr-2 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-[var(--g-800)] file:text-white hover:file:bg-[var(--g-950)] cursor-pointer"
              />
            </div>
          )}

          {/* Upload Progress Bar */}
          {uploadProgress && (
            <div className="p-3 bg-[var(--g-50)] dark:bg-[var(--g-950)] border-b border-[var(--g-200)] dark:border-[var(--g-800)]">
              <div className="flex items-center justify-between text-xs text-[var(--g-800)] dark:text-[var(--g-200)] font-medium mb-1">
                <span>Importing {uploadProgress.current} of {uploadProgress.total}...</span>
                <span>{Math.round((uploadProgress.current / uploadProgress.total) * 100)}%</span>
              </div>
              <div className="w-full bg-[var(--card-bdr)] h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-[var(--g-600)] dark:bg-[var(--g-400)] h-full transition-all duration-300"
                  style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                />
              </div>
              <p className="text-[10px] text-[var(--ink-muted)] truncate mt-1">{uploadProgress.name}</p>
            </div>
          )}

          {/* Source Search Filter */}
          <div className="p-2.5 border-b border-[var(--card-bdr)]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--ink-muted)]" />
              <input
                type="text"
                value={sourceSearch}
                onChange={(e) => setSourceSearch(e.target.value)}
                placeholder="Filter loaded sources..."
                className="fernly-input w-full pl-8.5 pr-3 py-1.5 rounded-full text-xs"
              />
            </div>
          </div>

          {/* Hidden File Input for PDF Replacement / Direct Upload */}
          <input
            type="file"
            accept="application/pdf"
            ref={replaceFileInputRef}
            onChange={handleExecuteReplacePdf}
            className="hidden"
          />

          {/* Sources List */}
          <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
            {filteredSources.length === 0 ? (
              <div className="p-6 text-center text-xs text-[var(--ink-muted)] flex flex-col items-center justify-center h-52">
                <FileText className="h-8 w-8 text-[var(--ink-muted)] opacity-30 mb-2" />
                <p className="font-semibold text-[var(--ink)]">No sources added yet</p>
                <p className="text-[11px] mt-1 text-[var(--ink-muted)] max-w-xs">
                  Search across 250M+ papers or upload a PDF to begin systematic synthesis.
                </p>
                <div className="flex items-center gap-2 mt-3">
                  <button
                    onClick={() => setIsSearchModalOpen(true)}
                    className="btn-fernly-primary px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer"
                  >
                    🔍 Search Papers
                  </button>
                  <button
                    onClick={() => setIsAddSourceOpen(true)}
                    className="btn-fernly-ghost px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer"
                  >
                    + Upload
                  </button>
                </div>
              </div>
            ) : (
              filteredSources.map((s) => {
                const isSelected = selectedSource?.id === s.id;
                return (
                  <div
                    key={s.id}
                    onClick={() => {
                      setSelectedSource(s);
                      if (s.pdfBlob) setViewMode("pdf");
                    }}
                    className={`group relative p-3 rounded-2xl border transition-all cursor-pointer flex flex-col gap-1.5 ${
                      isSelected
                        ? "bg-[var(--g-50)] dark:bg-[var(--g-950)] border-[var(--g-600)] dark:border-[var(--g-400)] text-[var(--ink)] shadow-xs"
                        : "bg-[var(--card)] border-[var(--card-bdr)] hover:border-[var(--g-400)] text-[var(--ink)]"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-1.5">
                      <div className="flex items-start gap-2 flex-1 min-w-0">
                        <FileText className={`h-4 w-4 mt-0.5 flex-shrink-0 ${isSelected ? "text-[var(--g-600)] dark:text-[var(--g-400)]" : "text-[var(--ink-muted)]"}`} />
                        <span className="text-xs font-bold line-clamp-2 leading-tight">{s.title}</span>
                      </div>
                      {/* Action buttons on card */}
                      <div className="flex items-center gap-0.5 opacity-80 group-hover:opacity-100 flex-shrink-0">
                        <button
                          type="button"
                          onClick={(e) => handleOpenConnectedPapers(e, s)}
                          className="p-1 rounded-md text-[var(--ink-muted)] hover:text-[var(--g-600)] dark:hover:text-[var(--g-400)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
                          title="Explore Connected Papers Graph"
                        >
                          <Share2 className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleOpenReplaceDialog(e, s.id)}
                          className="p-1 rounded-md text-[var(--ink-muted)] hover:text-[var(--g-600)] dark:hover:text-[var(--g-400)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
                          title="Replace or upload PDF document"
                        >
                          <Upload className="h-3.5 w-3.5" />
                        </button>
                        <button
                          type="button"
                          onClick={(e) => handleDeleteSource(e, s.id)}
                          className="p-1 rounded-md text-[var(--ink-muted)] hover:text-rose-600 hover:bg-rose-50 dark:hover:bg-rose-950/40 transition-colors cursor-pointer"
                          title="Remove paper from notebook"
                        >
                          <Trash2 className="h-3.5 w-3.5" />
                        </button>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[var(--ink-muted)] pl-6">
                      <span>{s.authors?.[0] || "Author"} · {s.year || "2023"}</span>
                      {s.pdfBlob ? (
                        <span className="fernly-badge fernly-badge-mint text-[9px] font-semibold">PDF Ready</span>
                      ) : (
                        s.doi && <span className="text-[var(--g-600)] dark:text-[var(--g-400)] font-mono font-medium">DOI</span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* PANE 2: Interactive Document Reader (Center) */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[var(--bg)]">
          {/* Reader Sub-Toolbar */}
          <div className="flex items-center justify-between px-6 py-2.5 border-b border-[var(--card-bdr)] bg-[var(--card)]/90 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-xs text-[var(--ink)] truncate">
              <BookOpen className="h-4 w-4 text-[var(--g-600)] dark:text-[var(--g-400)] flex-shrink-0" />
              <span className="font-semibold truncate max-w-xs md:max-w-sm">{selectedSource?.title || "No document selected"}</span>
            </div>

            <div className="flex items-center gap-3">
              {/* Paper Quick Actions */}
              {selectedSource && (
                <div className="flex items-center gap-1.5 mr-2 border-r border-[var(--card-bdr)] pr-3">
                  <button
                    onClick={(e) => handleOpenConnectedPapers(e, selectedSource)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--panel)] hover:bg-[var(--card-bdr)] text-[var(--ink)] border border-[var(--card-bdr)] transition-all cursor-pointer shadow-xs"
                    title="Open Connected Papers Graph for this paper"
                  >
                    <Share2 className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                    <span className="hidden lg:inline">Connected Graph</span>
                  </button>
                  <button
                    onClick={(e) => handleOpenReplaceDialog(e, selectedSource.id)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-[var(--panel)] hover:bg-[var(--card-bdr)] text-[var(--ink)] border border-[var(--card-bdr)] transition-all cursor-pointer shadow-xs"
                    title="Replace or attach PDF file"
                  >
                    <Upload className="h-3.5 w-3.5 text-[var(--ink-muted)]" />
                    <span className="hidden lg:inline">Replace PDF</span>
                  </button>
                  <button
                    onClick={(e) => handleDeleteSource(e, selectedSource.id)}
                    className="flex items-center gap-1 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 dark:bg-rose-950/40 hover:bg-rose-100 text-rose-600 dark:text-rose-400 border border-rose-200 dark:border-rose-900 transition-all cursor-pointer shadow-xs"
                    title="Delete paper from this notebook"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                    <span className="hidden lg:inline">Remove</span>
                  </button>
                </div>
              )}
              {/* Dual View Toggle with Fernly Pill */}
              <div className="flex items-center bg-[var(--panel)] border border-[var(--card-bdr)] rounded-full p-1 text-xs">
                <button
                  onClick={() => setViewMode("reader")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                    viewMode === "reader"
                      ? "bg-[var(--g-800)] text-white shadow-xs"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  🔬 Grounded Reader
                </button>
                <button
                  onClick={() => setViewMode("pdf")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer ${
                    viewMode === "pdf"
                      ? "bg-[var(--g-800)] text-white shadow-xs"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  📄 Interactive PDF
                </button>
              </div>

              {viewMode === "reader" && (
                <div className="flex items-center gap-1.5 bg-[var(--panel)] border border-[var(--card-bdr)] rounded-full px-2 py-1">
                  <button
                    onClick={() => setZoomLevel(Math.max(70, zoomLevel - 15))}
                    className="p-1 rounded-full hover:bg-[var(--card-bdr)] text-[var(--ink-muted)] hover:text-[var(--ink)] cursor-pointer"
                    title="Zoom Out"
                  >
                    <ZoomOut className="h-3.5 w-3.5" />
                  </button>
                  <span className="text-[11px] text-[var(--ink-muted)] font-mono w-9 text-center font-medium">{zoomLevel}%</span>
                  <button
                    onClick={() => setZoomLevel(Math.min(160, zoomLevel + 15))}
                    className="p-1 rounded-full hover:bg-[var(--card-bdr)] text-[var(--ink-muted)] hover:text-[var(--ink)] cursor-pointer"
                    title="Zoom In"
                  >
                    <ZoomIn className="h-3.5 w-3.5" />
                  </button>
                </div>
              )}
            </div>
          </div>

          {/* Center Pane Viewport: Native PDF or Grounded Reader Canvas */}
          {viewMode === "pdf" ? (
            <div className="flex-1 w-full h-full bg-[var(--bg)] flex flex-col">
              {pdfBlobUrl ? (
                <iframe
                  src={pdfBlobUrl}
                  className="w-full h-full border-0"
                  title={selectedSource?.title || "PDF Viewer"}
                />
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4 max-w-lg mx-auto">
                  <div className="p-4 rounded-2xl bg-[var(--card)] text-[var(--g-600)] dark:text-[var(--g-400)] border border-[var(--card-bdr)] shadow-md">
                    <FileText className="h-10 w-10" />
                  </div>
                  <div>
                    <h3 className="text-sm font-bold text-[var(--ink)]">{selectedSource?.title}</h3>
                    <p className="text-xs text-[var(--ink-muted)] mt-1 font-medium">
                      {selectedSource?.authors?.join(", ")} · {selectedSource?.year}
                    </p>
                  </div>

                  {pdfFetchStatus ? (
                    <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--card-bdr)] text-xs w-full space-y-2 shadow-xs">
                      <div className="flex items-center justify-center gap-2">
                        {pdfFetchStatus.status === "resolving" || pdfFetchStatus.status === "saving" ? (
                          <>
                            <div className="h-3.5 w-3.5 rounded-full border-2 border-[var(--g-600)] dark:border-[var(--g-400)] border-t-transparent animate-spin" />
                            <span className="text-[var(--g-600)] dark:text-[var(--g-400)] font-semibold animate-pulse">{pdfFetchStatus.message}</span>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                            <span className="text-[var(--ink)] font-semibold">{pdfFetchStatus.message}</span>
                          </>
                        )}
                      </div>
                      {pdfFetchStatus.landingUrl && (
                        <a
                          href={pdfFetchStatus.landingUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-[var(--g-600)] dark:text-[var(--g-400)] hover:underline font-mono font-medium"
                        >
                          <span>Open Publisher Gateway</span>
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      )}
                    </div>
                  ) : (
                    <div className="space-y-2.5 w-full">
                      <button
                        onClick={handleFetchPdfForSource}
                        className="btn-fernly-primary w-full flex items-center justify-center gap-2 py-3 px-5 rounded-full text-xs font-semibold shadow-xs transition-all cursor-pointer"
                      >
                        <Zap className="h-4 w-4" />
                        <span>Fetch PDF via Multi-Source Protocol</span>
                      </button>

                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => selectedSource && handleOpenReplaceDialog(e, selectedSource.id)}
                          className="btn-fernly-ghost flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-full text-xs font-semibold cursor-pointer"
                        >
                          <Upload className="h-3.5 w-3.5" />
                          <span>Attach Local PDF</span>
                        </button>
                        <button
                          onClick={(e) => selectedSource && handleOpenConnectedPapers(e, selectedSource)}
                          className="btn-fernly-ghost flex-1 flex items-center justify-center gap-1.5 py-2 px-3 rounded-full text-xs font-semibold cursor-pointer"
                        >
                          <Share2 className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                          <span>Connected Graph</span>
                        </button>
                      </div>

                      <p className="text-[11px] text-[var(--ink-muted)]">
                        Queries Springer, Nature, Unpaywall, Semantic Scholar, Europe PMC &amp; Academic Mirrors
                      </p>
                    </div>
                  )}

                  <div className="pt-2">
                    <button
                      onClick={() => setViewMode("reader")}
                      className="text-xs font-medium text-[var(--ink-muted)] hover:text-[var(--ink)] transition-colors cursor-pointer"
                    >
                      ← Switch to Grounded Evidence Canvas
                    </button>
                  </div>
                </div>
              )}
            </div>
          ) : !selectedSource ? (
            <div className="flex-1 flex flex-col items-center justify-center p-8 text-center max-w-lg mx-auto">
              <div className="relative mb-6">
                <div className="h-20 w-20 rounded-[2rem] bg-[var(--card)] border border-[var(--card-bdr)] flex items-center justify-center shadow-md">
                  <BookOpen className="h-9 w-9 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                </div>
                <div className="absolute -top-1 -right-1 h-7 w-7 rounded-full bg-[var(--g-100)] text-[var(--g-950)] border border-[var(--g-300)] flex items-center justify-center shadow-xs">
                  <Sparkles className="h-3.5 w-3.5" />
                </div>
              </div>
              <h3 className="text-xl font-bold text-[var(--ink)] mb-2 tracking-tight">
                Systematic Evidence Canvas
              </h3>
              <p className="text-xs text-[var(--ink-muted)] leading-relaxed mb-6 max-w-sm">
                No paper selected. Search academic literature or upload local PDFs to begin extracting verbatim claims and synthesis notes.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  onClick={() => setIsSearchModalOpen(true)}
                  className="btn-fernly-primary flex items-center gap-2 px-5 py-2.5 rounded-full text-xs font-semibold shadow-xs cursor-pointer"
                >
                  <Search className="h-4 w-4" />
                  <span>Search Literature</span>
                </button>
                <label className="btn-fernly-ghost flex items-center gap-2 px-5 py-2.5 rounded-full text-[var(--ink)] text-xs font-semibold cursor-pointer shadow-xs">
                  <Download className="h-4 w-4 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                  <span>Upload Local PDF</span>
                  <input
                    type="file"
                    accept="application/pdf"
                    multiple
                    className="hidden"
                    onChange={handleFileUpload}
                  />
                </label>
              </div>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto p-6 flex flex-col items-center gap-6">
              {/* Paper Canvas (Grounded Reader) */}
              <div
                className="fernly-card rounded-[2rem] p-8 sm:p-12 w-full max-w-2xl transition-all"
                style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: "top center" }}
              >
                <div className="border-b border-[var(--card-bdr)] pb-5 mb-6">
                  <div className="flex flex-wrap items-center gap-2 mb-2">
                    <span className="fernly-badge fernly-badge-leaf text-[10px] font-bold tracking-wider uppercase">
                      {[selectedSource?.journal, selectedSource?.year ? String(selectedSource.year) : null]
                        .filter(Boolean)
                        .join(" · ") || "Scholarly Publication"}
                    </span>
                    {selectedSource?.pdfBlob && (
                      <span className="fernly-badge fernly-badge-mint text-[9px] font-semibold">
                        PDF Attached ({Math.round((selectedSource.sizeBytes || 0) / 1024)} KB)
                      </span>
                    )}
                  </div>
                  <h1 className="text-xl font-bold text-[var(--ink)] leading-snug">
                    {selectedSource?.title}
                  </h1>
                  <p className="text-xs text-[var(--ink-muted)] mt-2 font-medium">
                    {selectedSource?.authors?.length ? selectedSource.authors.join(", ") : "Unknown Author(s)"}
                  </p>
                  {selectedSource?.doi && (
                    <a
                      href={`https://doi.org/${selectedSource.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-[10px] text-[var(--g-600)] dark:text-[var(--g-400)] hover:underline mt-1.5 font-mono"
                    >
                      <span>https://doi.org/{selectedSource.doi}</span>
                      <ExternalLink className="h-2.5 w-2.5" />
                    </a>
                  )}
                </div>

                {/* Real Abstract & Synthesized Overview Section */}
                <div className="p-6 rounded-2xl bg-[var(--panel)] border-l-4 border-[var(--g-600)] mb-6 text-xs text-[var(--ink)] space-y-3 font-sans">
                  <div className="flex items-center justify-between">
                    <h3 className="font-bold text-[var(--g-700)] dark:text-[var(--g-300)] text-xs flex items-center gap-1.5">
                      <BookOpen className="h-3.5 w-3.5 text-[var(--g-600)]" />
                      Abstract &amp; Grounded Evidence
                    </h3>
                    {selectedSource?.abstract && (
                      <span className="text-[10px] text-[var(--ink-muted)] font-mono">
                        {selectedSource.abstract.split(/\s+/).filter(Boolean).length} words
                      </span>
                    )}
                  </div>

                  {selectedSource?.abstract ? (
                    <>
                      <p className="leading-relaxed text-[var(--ink-muted)] text-xs whitespace-pre-line selection:bg-[var(--g-200)] selection:text-[var(--g-950)]">
                        {selectedSource.abstract}
                      </p>
                      <div className="flex flex-wrap items-center gap-2 pt-2 border-t border-[var(--card-bdr)]">
                        <button
                          onClick={() => handleInsertQuote(selectedSource.abstract!, 1)}
                          className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[var(--g-800)] dark:text-[var(--g-200)] hover:text-[var(--g-950)] bg-[var(--g-100)] dark:bg-[var(--g-900)] px-3 py-1 rounded-full cursor-pointer transition-colors"
                        >
                          <Quote className="h-3 w-3" /> Quote Abstract to Review Notes
                        </button>
                        <button
                          onClick={() => {
                            if (!selectedSource) return;
                            handleExtractClaimFromText(selectedSource.abstract!, selectedSource.id);
                          }}
                          className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[var(--ink)] hover:text-[var(--g-800)] bg-[var(--card)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] px-3 py-1 rounded-full cursor-pointer transition-colors"
                        >
                          <Plus className="h-3 w-3 text-[var(--g-600)]" /> Extract as Evidence Claim
                        </button>
                      </div>
                    </>
                  ) : (
                    <div className="py-4 text-center space-y-2">
                      <p className="text-xs text-[var(--ink-muted)] italic">
                        No abstract available in bibliographic metadata for this source.
                      </p>
                      <div className="flex items-center justify-center gap-2 pt-1">
                        {selectedSource?.pdfBlob ? (
                          <button
                            onClick={() => setViewMode("pdf")}
                            className="btn-fernly-primary px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer"
                          >
                            Open Local PDF Reader
                          </button>
                        ) : selectedSource?.doi ? (
                          <button
                            onClick={handleFetchPdfForSource}
                            className="btn-fernly-primary px-3 py-1.5 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-1.5"
                          >
                            <Zap className="h-3.5 w-3.5" />
                            Fetch PDF Full Text
                          </button>
                        ) : (
                          <span className="text-[11px] text-[var(--ink-muted)]">
                            Upload a PDF or query academic databases to attach full text.
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                </div>

                {/* Bibliographic Context & Citation Quick Actions */}
                <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--card-bdr)] space-y-2.5 text-xs text-[var(--ink-muted)]">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-[var(--ink)]">Bibliographic Record</span>
                    <span className="text-[10px] font-mono text-[var(--ink-muted)]">ID: {selectedSource?.id}</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px]">
                    <div>
                      <span className="text-[var(--ink-muted)]">Status: </span>
                      <span className="font-semibold text-[var(--ink)] capitalize">{selectedSource?.status || "ready"}</span>
                    </div>
                    <div>
                      <span className="text-[var(--ink-muted)]">Format: </span>
                      <span className="font-semibold text-[var(--ink)]">{selectedSource?.pdfBlob ? "Full-text PDF" : "Metadata record"}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-2 pt-2 border-t border-[var(--card-bdr)] flex-wrap">
                    <button
                      onClick={(e) => selectedSource && handleOpenConnectedPapers(e, selectedSource)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--g-700)] dark:text-[var(--g-300)] hover:underline cursor-pointer"
                    >
                      <Share2 className="h-3 w-3" /> Explore Connected Papers Graph
                    </button>
                    <span className="text-[var(--card-bdr)]">•</span>
                    <button
                      onClick={(e) => selectedSource && handleOpenReplaceDialog(e, selectedSource.id)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-[var(--ink-muted)] hover:text-[var(--ink)] cursor-pointer"
                    >
                      <Upload className="h-3 w-3" /> Replace PDF
                    </button>
                    <span className="text-[var(--card-bdr)]">•</span>
                    <button
                      onClick={(e) => selectedSource && handleDeleteSource(e, selectedSource.id)}
                      className="inline-flex items-center gap-1 text-[11px] font-semibold text-rose-600 dark:text-rose-400 hover:underline cursor-pointer"
                    >
                      <Trash2 className="h-3 w-3" /> Delete from Notebook
                    </button>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>

        {/* PANE 3: Evidence & Synthesis Studio (Right) */}
        <aside className="w-80 lg:w-96 flex flex-col border-l border-[var(--card-bdr)] bg-[var(--panel)] flex-shrink-0">
          {/* Studio Tab Switcher with Fernly Pill */}
          <div className="flex border-b border-[var(--card-bdr)] p-2.5 bg-[var(--card)] gap-1.5">
            <button
              onClick={() => setActiveTab("evidence")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all cursor-pointer ${
                activeTab === "evidence"
                  ? "bg-[var(--g-800)] text-white shadow-xs"
                  : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
              }`}
            >
              🔬 Evidence
            </button>
            <button
              onClick={() => setActiveTab("notes")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all cursor-pointer ${
                activeTab === "notes"
                  ? "bg-[var(--g-800)] text-white shadow-xs"
                  : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
              }`}
            >
              📝 Notes
            </button>
            <button
              onClick={() => setActiveTab("export")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all cursor-pointer ${
                activeTab === "export"
                  ? "bg-[var(--g-800)] text-white shadow-xs"
                  : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
              }`}
            >
              📤 Export
            </button>
          </div>

          {/* TAB 1: Verbatim Evidence Claims */}
          {activeTab === "evidence" && (
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-xs font-bold text-[var(--ink)]">Grounded Extraction</span>
                  <p className="text-[10px] text-[var(--ink-muted)]">
                    {evidenceItems.length} claim(s) across {sources.length} source(s)
                  </p>
                </div>
                <button
                  onClick={() => setIsAddClaimOpen(!isAddClaimOpen)}
                  disabled={!selectedSource}
                  className="btn-fernly-primary text-[11px] font-semibold px-2.5 py-1 rounded-full flex items-center gap-1 cursor-pointer disabled:opacity-40"
                  title={!selectedSource ? "Select a source to add claims" : "Add new grounded claim"}
                >
                  <Plus className="h-3 w-3" /> Add Claim
                </button>
              </div>

              {/* Source Filter Pill: Current Paper vs All Notebook Papers */}
              {sources.length > 1 && (
                <div className="flex items-center bg-[var(--card)] border border-[var(--card-bdr)] rounded-full p-0.5 text-[10px]">
                  <button
                    onClick={() => setEvidenceFilter("current")}
                    className={`flex-1 py-1 px-2 rounded-full font-semibold transition-all cursor-pointer truncate ${
                      evidenceFilter === "current"
                        ? "bg-[var(--g-800)] text-white shadow-xs"
                        : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                    }`}
                  >
                    Current Paper ({selectedSource ? evidenceItems.filter((e) => e.sourceId === selectedSource.id).length : 0})
                  </button>
                  <button
                    onClick={() => setEvidenceFilter("all")}
                    className={`flex-1 py-1 px-2 rounded-full font-semibold transition-all cursor-pointer ${
                      evidenceFilter === "all"
                        ? "bg-[var(--g-800)] text-white shadow-xs"
                        : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                    }`}
                  >
                    All Papers ({evidenceItems.length})
                  </button>
                </div>
              )}

              {/* Inline Add Claim Form */}
              {isAddClaimOpen && selectedSource && (
                <form
                  onSubmit={handleAddEvidenceClaim}
                  className="p-3.5 bg-[var(--card)] border border-[var(--g-500)] rounded-2xl space-y-2.5 animate-in fade-in duration-150"
                >
                  <div className="flex items-center justify-between text-xs">
                    <span className="font-bold text-[var(--ink)]">New Grounded Claim</span>
                    <button
                      type="button"
                      onClick={() => setIsAddClaimOpen(false)}
                      className="text-[var(--ink-muted)] hover:text-[var(--ink)] text-xs cursor-pointer"
                    >
                      Cancel
                    </button>
                  </div>
                  <div className="grid grid-cols-2 gap-2">
                    <select
                      value={newClaimCategory}
                      onChange={(e) =>
                        setNewClaimCategory(e.target.value as "method" | "sampling" | "statistics" | "rigour")
                      }
                      className="fernly-input py-1 px-2 text-xs rounded-lg"
                    >
                      <option value="method">📐 Methodology</option>
                      <option value="sampling">👥 Sample Size (N)</option>
                      <option value="statistics">📊 Statistics &amp; Rigour</option>
                      <option value="rigour">🛡️ Findings &amp; Outcomes</option>
                    </select>
                    <input
                      type="number"
                      placeholder="Page #"
                      value={newClaimPage}
                      onChange={(e) => setNewClaimPage(e.target.value ? parseInt(e.target.value, 10) : "")}
                      className="fernly-input py-1 px-2 text-xs rounded-lg"
                    />
                  </div>
                  <textarea
                    placeholder="Enter synthesized claim statement..."
                    value={newClaimText}
                    onChange={(e) => setNewClaimText(e.target.value)}
                    rows={2}
                    className="fernly-input w-full p-2 text-xs rounded-lg resize-none"
                    required
                  />
                  <textarea
                    placeholder="Optional: verbatim quote excerpt..."
                    value={newClaimQuote}
                    onChange={(e) => setNewClaimQuote(e.target.value)}
                    rows={2}
                    className="fernly-input w-full p-2 text-xs rounded-lg resize-none font-mono"
                  />
                  <button
                    type="submit"
                    className="btn-fernly-primary w-full py-1.5 rounded-full text-xs font-semibold cursor-pointer"
                  >
                    Save Evidence Claim
                  </button>
                </form>
              )}

              {/* Dynamic Claim List */}
              {(() => {
                const displayed = evidenceFilter === "current" && selectedSource
                  ? evidenceItems.filter((e) => e.sourceId === selectedSource.id)
                  : evidenceItems;

                if (displayed.length === 0) {
                  return (
                    <div className="p-6 text-center text-xs text-[var(--ink-muted)] bg-[var(--card)] border border-[var(--card-bdr)] rounded-2xl space-y-2">
                      <Sparkles className="h-6 w-6 text-[var(--g-600)] dark:text-[var(--g-400)] mx-auto opacity-40" />
                      <p className="font-semibold text-[var(--ink)]">No evidence claims extracted yet</p>
                      <p className="text-[11px] leading-relaxed max-w-xs mx-auto">
                        {selectedSource
                          ? "Extract claims from the abstract or click '+ Add Claim' to record methodology, sample size, or outcomes."
                          : "Select a source to view or extract grounded evidence."}
                      </p>
                    </div>
                  );
                }

                const categoryLabels: Record<string, { label: string; icon: string }> = {
                  method: { label: "Methodology", icon: "📐" },
                  sampling: { label: "Sample Size (N)", icon: "👥" },
                  statistics: { label: "Statistics & Rigour", icon: "📊" },
                  rigour: { label: "Findings & Outcomes", icon: "🛡️" },
                };

                return displayed.map((item) => {
                  const cat = categoryLabels[item.category] || { label: item.category, icon: "📌" };
                  const source = sources.find((s) => s.id === item.sourceId);

                  return (
                    <div key={item.id} className="fernly-card p-4 rounded-2xl space-y-2 relative group transition-all">
                      <div className="flex items-center justify-between text-xs">
                        <span className="font-bold text-[var(--g-700)] dark:text-[var(--g-300)] flex items-center gap-1.5">
                          <span>{cat.icon}</span>
                          <span>{cat.label}</span>
                        </span>
                        <div className="flex items-center gap-1.5">
                          {item.pageNumber ? (
                            <span className="text-[10px] text-[var(--ink-muted)] font-medium">
                              Page {item.pageNumber}
                            </span>
                          ) : null}
                          <button
                            onClick={() => handleDeleteEvidenceClaim(item.id)}
                            title="Delete this claim"
                            className="text-[var(--ink-muted)] hover:text-red-500 opacity-60 hover:opacity-100 p-0.5 transition-colors cursor-pointer"
                          >
                            <Trash2 className="h-3 w-3" />
                          </button>
                        </div>
                      </div>

                      {evidenceFilter === "all" && source && (
                        <p className="text-[10px] font-semibold text-[var(--ink-muted)] truncate">
                          📄 {source.title}
                        </p>
                      )}

                      <p className="text-xs text-[var(--ink)] leading-relaxed">
                        {item.claim}
                      </p>

                      {item.quote && (
                        <p className="text-xs text-[var(--ink-muted)] leading-relaxed italic border-l-2 border-[var(--g-500)] pl-2.5 py-0.5">
                          &quot;{item.quote}&quot;
                        </p>
                      )}

                      <button
                        onClick={() =>
                          handleInsertQuote(item.quote || item.claim, item.pageNumber || 1)
                        }
                        className="text-[11px] text-[var(--g-600)] dark:text-[var(--g-400)] hover:underline flex items-center gap-1 font-semibold cursor-pointer pt-0.5"
                      >
                        <Plus className="h-3 w-3" /> Insert into Review Notes
                      </button>
                    </div>
                  );
                });
              })()}
            </div>
          )}

          {/* TAB 2: Synthesis Review Notes */}
          {activeTab === "notes" && (
            <div className="flex-1 flex flex-col p-4 overflow-hidden">
              <span className="text-xs font-bold text-[var(--ink)] mb-2">Project Synthesis Review Notes</span>
              <textarea
                value={notesContent}
                onChange={(e) => handleSaveNotes(e.target.value)}
                placeholder="Write critical reflections, draft synthesis paragraphs, or quote evidence..."
                className="fernly-input flex-1 w-full rounded-2xl p-4 text-xs font-mono leading-relaxed resize-none"
              />
              <span className="text-[10px] text-[var(--ink-muted)] mt-2 font-medium">Saved automatically to local IndexedDB</span>
            </div>
          )}

          {/* TAB 3: Export & Citations */}
          {activeTab === "export" && (
            <div className="flex-1 p-4 space-y-4 overflow-y-auto">
              <div>
                <span className="text-xs font-bold text-[var(--ink)]">Selected Source Citation</span>
                <p className="text-[11px] text-[var(--ink-muted)] mt-0.5">
                  Copy formatted citation for: <span className="text-[var(--ink)] font-semibold">{selectedSource?.title}</span>
                </p>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <button
                    onClick={() => handleCopyCitation("APA")}
                    className="btn-fernly-ghost flex items-center justify-center gap-1.5 py-2 px-3 rounded-full text-xs font-semibold text-[var(--ink)] cursor-pointer"
                  >
                    {copiedCitation === "APA" ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-[var(--g-600)]" />
                        <span className="text-[var(--g-600)]">Copied APA!</span>
                      </>
                    ) : (
                      <>
                        <Quote className="h-3.5 w-3.5 text-[var(--g-600)]" />
                        <span>Copy APA</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => handleCopyCitation("BibTeX")}
                    className="btn-fernly-ghost flex items-center justify-center gap-1.5 py-2 px-3 rounded-full text-xs font-semibold text-[var(--ink)] cursor-pointer"
                  >
                    {copiedCitation === "BibTeX" ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-[var(--g-600)]" />
                        <span className="text-[var(--g-600)]">Copied BibTeX!</span>
                      </>
                    ) : (
                      <>
                        <Quote className="h-3.5 w-3.5 text-[var(--g-600)]" />
                        <span>Copy BibTeX</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="h-px bg-[var(--card-bdr)] my-2" />

              <div>
                <span className="text-xs font-bold text-[var(--ink)]">Corpus Batch Export</span>
                <p className="text-xs text-[var(--ink-muted)] mt-0.5">
                  Export all ({filteredSources.length}) loaded sources into your reference manager or PRISMA report:
                </p>

                <div className="space-y-2.5 mt-3">
                  <button
                    onClick={() => {
                      const bibtex = filteredSources
                        .map(
                          (s, i) =>
                            `@article{ref${i + 1},\n  title={${s.title}},\n  author={${s.authors.join(" and ")}},\n  year={${s.year || 2023}},\n  doi={${s.doi || ""}}\n}`
                        )
                        .join("\n\n");
                      const blob = new Blob([bibtex], { type: "text/plain" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${notebook.title.replace(/\s+/g, "_")}.bib`;
                      a.click();
                    }}
                    className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-[var(--card)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-xs font-semibold text-[var(--ink)] transition-all cursor-pointer shadow-xs group"
                  >
                    <span>Export All BibTeX (.bib)</span>
                    <span className="fernly-arrow w-6 h-6 rounded-full bg-[var(--panel)] flex items-center justify-center text-[var(--ink)] group-hover:bg-[var(--g-800)] group-hover:text-white transition-all">
                      <Download className="h-3.5 w-3.5" />
                    </span>
                  </button>

                  <button
                    onClick={() => {
                      const ris = filteredSources
                        .map(
                          (s) =>
                            `TY  - JOUR\nTI  - ${s.title}\nAU  - ${s.authors.join("\nAU  - ")}\nPY  - ${s.year || 2023}\nDO  - ${s.doi || ""}\nER  -`
                        )
                        .join("\n\n");
                      const blob = new Blob([ris], { type: "text/plain" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = `${notebook.title.replace(/\s+/g, "_")}.ris`;
                      a.click();
                    }}
                    className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-[var(--card)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-xs font-semibold text-[var(--ink)] transition-all cursor-pointer shadow-xs group"
                  >
                    <span>Export All EndNote / Zotero (RIS)</span>
                    <span className="fernly-arrow w-6 h-6 rounded-full bg-[var(--panel)] flex items-center justify-center text-[var(--ink)] group-hover:bg-[var(--g-800)] group-hover:text-white transition-all">
                      <Download className="h-3.5 w-3.5" />
                    </span>
                  </button>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>

      {/* MODAL: Search & Add Literature Directly to Active Notebook */}
      {isSearchModalOpen && (
        <Modal
          isOpen={isSearchModalOpen}
          onClose={() => setIsSearchModalOpen(false)}
          title={`Search & Add Papers to "${notebook.title}"`}
          subtitle="Search across 250M+ global literature records and attach them with 1 click"
          icon={<Search className="h-4 w-4" />}
          panelClassName="max-w-3xl max-h-[85vh] flex flex-col space-y-4"
        >
            {/* Search Input Bar with OA Toggle */}
            <form onSubmit={handleWorkspaceSearch} className="space-y-3">
              <div className="flex items-center gap-2">
                <div className="relative flex-1">
                  <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--ink-muted)] pointer-events-none" aria-hidden="true" />
                  <input
                    type="text"
                    value={searchModalQuery}
                    onChange={(e) => setSearchModalQuery(e.target.value)}
                    placeholder="Search keywords, topics, authors, or paste a DOI..."
                    aria-label="Search the academic literature"
                    className="fernly-input fernly-input-search w-full !pl-10 !pr-4 py-2.5 text-xs sm:text-sm rounded-full"
                    autoFocus
                  />
                </div>
                <button
                  type="submit"
                  disabled={searchModalLoading || !searchModalQuery.trim()}
                  className="btn-fernly-primary px-5 py-2.5 rounded-full text-xs font-semibold shadow-xs disabled:opacity-50 cursor-pointer flex-shrink-0"
                >
                  {searchModalLoading ? "Searching..." : "Search"}
                </button>
              </div>

              <div className="flex items-center justify-between text-xs text-[var(--ink-muted)] px-1">
                <label className="flex items-center gap-2 cursor-pointer select-none">
                  <input
                    type="checkbox"
                    checked={searchModalOA}
                    onChange={(e) => setSearchModalOA(e.target.checked)}
                    className="rounded border-[var(--card-bdr)] text-[var(--g-600)]"
                  />
                  <span className="font-semibold text-[var(--ink)]">🌿 Open Access Only (Free PDF)</span>
                </label>
                <span>Sources: OpenAlex · arXiv · Semantic Scholar</span>
              </div>
            </form>

            {/* Search Results List */}
            <div className="flex-1 overflow-y-auto space-y-3 min-h-[220px] max-h-[380px] pr-1">
              {searchModalLoading ? (
                <div className="flex flex-col items-center justify-center py-12 space-y-2">
                  <div className="h-7 w-7 border-2 border-[var(--g-600)] border-t-transparent rounded-full animate-spin" />
                  <span className="text-xs text-[var(--ink-muted)] animate-pulse">
                    Querying academic databases...
                  </span>
                </div>
              ) : searchModalResults.length > 0 ? (
                searchModalResults.map((p) => {
                  const isAlreadyAdded =
                    addedIds[p.id] || sources.some((s) => s.doi && p.doi && s.doi.toLowerCase() === p.doi.toLowerCase());
                  return (
                    <div
                      key={p.id}
                      className="p-4 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                    >
                      <div className="space-y-1 min-w-0 flex-1">
                        <div className="flex items-center gap-1.5 flex-wrap">
                          <span className="fernly-badge fernly-badge-leaf text-[9px] font-bold uppercase">
                            {p.source}
                          </span>
                          {p.isOpenAccess && (
                            <span className="fernly-badge fernly-badge-mint text-[9px] font-semibold">
                              OA
                            </span>
                          )}
                          <span className="text-[10px] text-[var(--ink-muted)] font-mono">
                            {p.citationCount || 0} cites · {p.year || "2023"}
                          </span>
                        </div>
                        <h4 className="text-xs sm:text-sm font-bold text-[var(--ink)] line-clamp-2">
                          {p.title}
                        </h4>
                        <p className="text-[11px] text-[var(--ink-muted)] truncate">
                          {p.authors?.slice(0, 3).join(", ")}
                          {p.authors && p.authors.length > 3 ? " et al." : ""} · {p.venue}
                        </p>
                      </div>

                      <div className="flex items-center gap-2 flex-shrink-0 self-end sm:self-center">
                        {isAlreadyAdded ? (
                          <span className="inline-flex items-center gap-1 px-3 py-1.5 rounded-full bg-[var(--g-100)] text-[var(--g-800)] dark:bg-[var(--g-900)] dark:text-[var(--g-200)] text-xs font-semibold">
                            <CheckCircle2 className="h-3.5 w-3.5 text-[var(--g-600)]" />
                            <span>Added</span>
                          </span>
                        ) : (
                          <>
                            <button
                              onClick={() => handleAddPaperFromSearch(p, false)}
                              className="btn-fernly-primary px-3.5 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1 cursor-pointer shadow-xs"
                            >
                              <BookmarkPlus className="h-3.5 w-3.5" />
                              <span>Add</span>
                            </button>
                            {p.isOpenAccess && (
                              <button
                                onClick={() => handleAddPaperFromSearch(p, true)}
                                className="btn-fernly-ghost px-3 py-1.5 rounded-full text-xs font-semibold flex items-center gap-1 text-[var(--ink)] cursor-pointer"
                                title="Add and immediately fetch full-text PDF"
                              >
                                <Zap className="h-3.5 w-3.5 text-[var(--g-600)]" />
                                <span>Add &amp; PDF</span>
                              </button>
                            )}
                          </>
                        )}
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="flex flex-col items-center justify-center py-10 text-center text-xs text-[var(--ink-muted)]">
                  <Search className="h-8 w-8 opacity-30 mb-2" />
                  <p className="font-semibold text-[var(--ink)]">Search for articles to add</p>
                  <p className="text-[11px] mt-1">
                    Try &quot;CRISPR gene editing&quot;, &quot;transformer reasoning&quot;, or paste a paper DOI.
                  </p>
                </div>
              )}
            </div>

            {/* Modal Footer */}
            <div className="pt-2 border-t border-[var(--card-bdr)] flex items-center justify-between text-xs text-[var(--ink-muted)]">
              <span>{sources.length} sources currently loaded in review</span>
              <button
                onClick={() => setIsSearchModalOpen(false)}
                className="btn-fernly-ghost px-4 py-1.5 rounded-full font-semibold text-xs cursor-pointer"
              >
                Close
              </button>
            </div>
        </Modal>
      )}
    </div>
  );
}
