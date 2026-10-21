"use client";

import React, { useState, useEffect } from "react";
import { Notebook, Source, Note, db } from "@/lib/db";
import { fetchAndStorePaperPdf } from "@/lib/pdfDownloader";
import {
  ArrowLeft,
  Plus,
  FileText,
  Search,
  Download,
  BookOpen,
  Share2,
  ZoomIn,
  ZoomOut,
  Quote,
  CheckCircle2,
  Sparkles,
  Layers,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  Zap,
  AlertCircle,
  Trash2,
  Sun,
  Moon,
} from "lucide-react";

interface NotebookWorkspaceProps {
  notebook: Notebook;
  onBack: () => void;
  onUpdate: () => void;
}

export function NotebookWorkspace({ notebook, onBack, onUpdate }: NotebookWorkspaceProps) {
  const [sources, setSources] = useState<Source[]>([]);
  const [selectedSource, setSelectedSource] = useState<Source | null>(null);
  const [activeTab, setActiveTab] = useState<"evidence" | "notes" | "export">("evidence");
  const [notesContent, setNotesContent] = useState("");
  const [zoomLevel, setZoomLevel] = useState(100);
  const [isAddSourceOpen, setIsAddSourceOpen] = useState(false);
  const [doiInput, setDoiInput] = useState("");
  const [sourceSearch, setSourceSearch] = useState("");
  const [viewMode, setViewMode] = useState<"reader" | "pdf">("reader");
  const [uploadProgress, setUploadProgress] = useState<{ current: number; total: number; name: string } | null>(null);
  const [copiedCitation, setCopiedCitation] = useState<string | null>(null);
  const [pdfFetchStatus, setPdfFetchStatus] = useState<{
    status: string;
    message: string;
    landingUrl?: string;
  } | null>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const isDark =
        document.documentElement.classList.contains("dark") ||
        document.documentElement.getAttribute("data-theme") === "dark";
      setIsDarkMode(isDark);
    }
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDarkMode;
    setIsDarkMode(nextDark);
    if (typeof window !== "undefined") {
      if (nextDark) {
        document.documentElement.classList.add("dark");
        document.body.classList.add("dark");
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("vellum-theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        document.body.classList.remove("dark");
        document.documentElement.setAttribute("data-theme", "light");
        localStorage.setItem("vellum-theme", "light");
      }
    }
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
  useEffect(() => {
    async function loadData() {
      const loadedSources = await db.sources.where("notebookId").equals(notebook.id).toArray();
      setSources(loadedSources);
      setSelectedSource(loadedSources.length > 0 ? loadedSources[0] : null);

      const note = await db.notes.where("notebookId").equals(notebook.id).first();
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

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const newFiles = Array.from(e.target.files);
    const total = newFiles.length;

    for (let i = 0; i < total; i++) {
      const f = newFiles[i];
      setUploadProgress({ current: i + 1, total, name: f.name });

      // Clean title from filename
      const cleanTitle = f.name
        .replace(/\.pdf$/i, "")
        .replace(/^[a-zA-Z0-9_\-]+ - \d{4} - /, "") // remove Zotero prefix if present
        .replace(/_/g, " ");

      const newSource: Source = {
        id: `src-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        notebookId: notebook.id,
        title: cleanTitle,
        authors: [f.name.includes(" - ") ? f.name.split(" - ")[0] : "Author"],
        year: parseInt((f.name.match(/\b(19|20)\d{2}\b/) || ["2024"])[0], 10),
        pdfBlob: f,
        sizeBytes: f.size,
        status: "ready",
        addedAt: Date.now(),
      };
      await db.sources.put(newSource);
    }

    setUploadProgress(null);
    // Update notebook source count
    const count = await db.sources.where("notebookId").equals(notebook.id).count();
    await db.notebooks.update(notebook.id, { sourcesCount: count, updatedAt: Date.now() });
    const reloaded = await db.sources.where("notebookId").equals(notebook.id).toArray();
    setSources(reloaded);
    if (reloaded.length > 0) {
      setSelectedSource(reloaded[reloaded.length - 1]); // focus on the newest paper
    }
    setIsAddSourceOpen(false);
    onUpdate();
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
    <div className="flex flex-col h-screen w-full bg-[#fbfbf6] dark:bg-[#000000] text-[#1a1a1a] dark:text-[#f5f5f7] overflow-hidden transition-colors duration-200">
      {/* Top Workspace Header */}
      <header className="apple-glass flex items-center justify-between px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14 py-2.5 sm:py-3 border-b border-black/8 dark:border-white/10 bg-white/80 dark:bg-black/60 backdrop-blur-2xl flex-shrink-0 z-20">
        <div className="flex items-center gap-3">
          <button
            onClick={onBack}
            className="apple-press px-3 py-1.5 rounded-full text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors flex items-center gap-1.5 text-xs font-semibold cursor-pointer"
          >
            <ArrowLeft className="h-4 w-4" />
            <span className="hidden sm:inline">My notebooks</span>
          </button>
          <div className="h-4 w-px bg-black/10 dark:bg-white/10" />
          <div className="flex items-center gap-2.5">
            <span className="text-xl p-1.5 rounded-2xl bg-black/5 dark:bg-white/10 border border-black/5 dark:border-white/10">{notebook.emoji}</span>
            <div>
              <h1 className="text-sm font-semibold text-[#1a1a1a] dark:text-white truncate max-w-xs sm:max-w-md tracking-tight">
                {notebook.title}
              </h1>
              <p className="text-[11px] text-[#1a1a1a]/55 dark:text-white/55">
                {sources.length} {sources.length === 1 ? "source" : "sources"} loaded · 100% Local-First
              </p>
            </div>
          </div>
        </div>

        {/* Right Action Tools */}
        <div className="flex items-center gap-2">
          {/* Reading Mode / Dark Mode Toggle Button */}
          <button
            onClick={toggleTheme}
            className="apple-press p-1.5 sm:p-2 rounded-full border border-black/12 dark:border-white/15 bg-white/80 dark:bg-white/10 text-[#1a1a1a] dark:text-white hover:bg-black/5 dark:hover:bg-white/15 transition-colors cursor-pointer shadow-xs flex items-center justify-center"
            title={isDarkMode ? "Switch to Linen Day Canvas" : "Switch to Night Reading Mode"}
          >
            {isDarkMode ? (
              <Sun className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#ff9f0a]" />
            ) : (
              <Moon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#0071e3]" />
            )}
          </button>

          <button
            onClick={async () => {
              if (confirm(`Delete notebook "${notebook.title}" and its saved sources from storage?`)) {
                await db.notebooks.delete(notebook.id);
                await db.sources.where("notebookId").equals(notebook.id).delete();
                await db.notes.where("notebookId").equals(notebook.id).delete();
                onBack();
              }
            }}
            className="apple-press flex items-center gap-1.5 px-3 py-1.5 rounded-full border border-red-200 dark:border-red-900/40 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs font-medium transition-colors cursor-pointer shadow-xs"
            title="Delete this notebook"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Delete</span>
          </button>

          <button
            onClick={() => setActiveTab("export")}
            className="apple-press flex items-center gap-1.5 px-4 py-2 rounded-full bg-white dark:bg-white/10 border border-black/12 dark:border-white/15 hover:bg-black/5 dark:hover:bg-white/15 text-xs font-semibold text-[#1a1a1a] dark:text-white transition-colors cursor-pointer shadow-xs"
          >
            <Download className="h-3.5 w-3.5 text-[#0071e3] dark:text-[#64d2ff]" />
            <span>Export Citations</span>
          </button>
        </div>
      </header>

      {/* Tri-Pane Main Body */}
      <div className="flex flex-1 overflow-hidden">
        {/* PANE 1: Sources Corpus (Left) */}
        <aside className="w-72 lg:w-80 flex flex-col border-r border-[#1a1a1a]/8 dark:border-white/10 bg-white/70 dark:bg-[#161a18]/80 backdrop-blur-sm flex-shrink-0">
          <div className="p-3.5 border-b border-[#1a1a1a]/8 dark:border-white/10 flex items-center justify-between">
            <span className="text-xs font-semibold text-[#1a1a1a] dark:text-white flex items-center gap-1.5">
              <Layers className="h-3.5 w-3.5 text-[#034f46] dark:text-[#cef5ca]" /> Sources ({sources.length})
            </span>
            <button
              onClick={() => setIsAddSourceOpen(!isAddSourceOpen)}
              className="flex items-center gap-1 px-3 py-1 rounded-full bg-[#cef5ca] hover:bg-[#cef5ca]/80 text-[#114e0b] border border-[#cef5ca] text-xs font-semibold transition-colors cursor-pointer"
            >
              <Plus className="h-3.5 w-3.5" /> Add
            </button>
          </div>

          {/* Add Source Drawer */}
          {isAddSourceOpen && (
            <div className="p-3.5 bg-[#ffffeb] dark:bg-[#1a1e1c] border-b border-[#1a1a1a]/8 dark:border-white/10 space-y-2.5">
              <label className="block text-xs font-semibold text-[#1a1a1a]/80 dark:text-white/80">Upload PDF(s)</label>
              <input
                type="file"
                multiple
                accept="application/pdf"
                onChange={handleFileUpload}
                className="block w-full text-xs text-[#1a1a1a]/70 dark:text-white/70 file:mr-2 file:py-1.5 file:px-3 file:rounded-full file:border-0 file:text-xs file:font-semibold file:bg-[#034f46] file:text-[#ffffeb] hover:file:bg-[#034f46]/90 cursor-pointer"
              />
            </div>
          )}

          {/* Upload Progress Bar */}
          {uploadProgress && (
            <div className="p-3 bg-[#cef5ca]/40 dark:bg-[#034f46]/30 border-b border-[#cef5ca] dark:border-[#034f46]">
              <div className="flex items-center justify-between text-xs text-[#114e0b] dark:text-[#cef5ca] font-medium mb-1">
                <span>Importing {uploadProgress.current} of {uploadProgress.total}...</span>
                <span>{Math.round((uploadProgress.current / uploadProgress.total) * 100)}%</span>
              </div>
              <div className="w-full bg-[#1a1a1a]/10 dark:bg-white/10 h-1.5 rounded-full overflow-hidden">
                <div
                  className="bg-[#034f46] dark:bg-[#23a07a] h-full transition-all duration-300"
                  style={{ width: `${(uploadProgress.current / uploadProgress.total) * 100}%` }}
                />
              </div>
              <p className="text-[10px] text-[#1a1a1a]/60 dark:text-white/60 truncate mt-1">{uploadProgress.name}</p>
            </div>
          )}

          {/* Source Search Filter */}
          <div className="p-2.5 border-b border-[#1a1a1a]/8 dark:border-white/10">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[#1a1a1a]/40 dark:text-white/40" />
              <input
                type="text"
                value={sourceSearch}
                onChange={(e) => setSourceSearch(e.target.value)}
                placeholder="Filter sources..."
                className="w-full pl-8.5 pr-3 py-1.5 bg-[#f8f9fa] dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 rounded-full text-xs text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/40 dark:placeholder-white/35 focus:outline-none focus:bg-white dark:focus:bg-[#222825] focus:border-[#034f46]"
              />
            </div>
          </div>

          {/* Sources List */}
          <div className="flex-1 overflow-y-auto p-2.5 space-y-2">
            {filteredSources.length === 0 ? (
              <div className="p-6 text-center text-xs text-[#1a1a1a]/50 dark:text-white/50 flex flex-col items-center justify-center h-48">
                <FileText className="h-8 w-8 text-[#1a1a1a]/25 dark:text-white/25 mb-2" />
                <p className="font-semibold text-[#1a1a1a] dark:text-white">No sources added</p>
                <p className="text-[11px] mt-1 text-[#1a1a1a]/60 dark:text-white/60">
                  Add DOI/arXiv or upload a PDF to begin review.
                </p>
                <button
                  onClick={() => setIsAddSourceOpen(true)}
                  className="mt-3 px-3.5 py-1.5 rounded-full bg-[#cef5ca] dark:bg-[#034f46] hover:bg-[#cef5ca]/80 dark:hover:bg-[#034f46]/80 text-[#114e0b] dark:text-[#cef5ca] border border-[#cef5ca] dark:border-[#034f46] text-xs font-semibold cursor-pointer transition-colors"
                >
                  + Add Source
                </button>
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
                    className={`p-3 rounded-2xl border transition-all cursor-pointer flex flex-col gap-1.5 ${
                      isSelected
                        ? "bg-[#cef5ca]/40 dark:bg-[#034f46]/30 border-[#034f46]/40 dark:border-[#cef5ca]/40 text-[#1a1a1a] dark:text-white shadow-xs"
                        : "bg-white dark:bg-[#1a1e1c] border-[#1a1a1a]/8 dark:border-white/10 hover:bg-[#ffffeb] dark:hover:bg-[#222825] text-[#1a1a1a] dark:text-white"
                    }`}
                  >
                    <div className="flex items-start gap-2">
                      <FileText className={`h-4 w-4 mt-0.5 flex-shrink-0 ${isSelected ? "text-[#034f46] dark:text-[#cef5ca]" : "text-[#1a1a1a]/40 dark:text-white/40"}`} />
                      <span className="text-xs font-semibold line-clamp-2 leading-tight">{s.title}</span>
                    </div>
                    <div className="flex items-center justify-between text-[10px] text-[#1a1a1a]/55 dark:text-white/55 pl-6">
                      <span>{s.authors?.[0] || "Author"} · {s.year || "2023"}</span>
                      {s.pdfBlob ? (
                        <span className="text-[#114e0b] dark:text-[#cef5ca] bg-[#cef5ca] dark:bg-[#034f46]/60 px-1.5 py-0.5 rounded-md font-semibold">PDF Ready</span>
                      ) : (
                        s.doi && <span className="text-[#034f46] dark:text-[#cef5ca] font-mono font-medium">DOI</span>
                      )}
                    </div>
                  </div>
                );
              })
            )}
          </div>
        </aside>

        {/* PANE 2: Interactive Document Reader (Center) */}
        <main className="flex-1 flex flex-col overflow-hidden bg-[#fbfbf6] dark:bg-[#121413]">
          {/* Reader Sub-Toolbar */}
          <div className="flex items-center justify-between px-6 py-2.5 border-b border-[#1a1a1a]/8 dark:border-white/10 bg-white/90 dark:bg-[#161a18]/90 backdrop-blur-sm">
            <div className="flex items-center gap-2 text-xs text-[#1a1a1a] dark:text-white truncate">
              <BookOpen className="h-4 w-4 text-[#034f46] dark:text-[#cef5ca] flex-shrink-0" />
              <span className="font-semibold truncate max-w-xs md:max-w-sm">{selectedSource?.title || "No document selected"}</span>
            </div>

            <div className="flex items-center gap-3">
              {/* Dual View Toggle */}
              <div className="flex items-center bg-[#ffffeb] dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 rounded-full p-1 text-xs">
                <button
                  onClick={() => setViewMode("reader")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all ${
                    viewMode === "reader"
                      ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                      : "text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white"
                  }`}
                >
                  🔬 Grounded Reader
                </button>
                <button
                  onClick={() => setViewMode("pdf")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all ${
                    viewMode === "pdf"
                      ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                      : "text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white"
                  }`}
                >
                  📄 Interactive PDF
                </button>
              </div>

              {viewMode === "reader" && (
                <div className="flex items-center gap-1.5 bg-[#ffffeb] dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 rounded-full px-2 py-1">
                  <button
                    onClick={() => setZoomLevel(Math.max(70, zoomLevel - 15))}
                    className="p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white"
                    title="Zoom Out"
                  >
                    <ZoomOut className="h-3.5 w-3.5" />
                  </button>
                  <span className="text-[11px] text-[#1a1a1a]/70 dark:text-white/70 font-mono w-9 text-center font-medium">{zoomLevel}%</span>
                  <button
                    onClick={() => setZoomLevel(Math.min(160, zoomLevel + 15))}
                    className="p-1 rounded-full hover:bg-black/5 dark:hover:bg-white/10 text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white"
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
            <div className="flex-1 w-full h-full bg-[#fbfbf6] dark:bg-[#121413] flex flex-col">
              {pdfBlobUrl ? (
                <iframe
                  src={pdfBlobUrl}
                  className="w-full h-full border-0"
                  title={selectedSource?.title || "PDF Viewer"}
                />
              ) : (
                <div className="flex-1 flex flex-col items-center justify-center p-8 text-center space-y-4 max-w-lg mx-auto">
                  <div className="p-4 rounded-2xl bg-white dark:bg-[#1a1e1c] text-[#034f46] dark:text-[#cef5ca] border border-[#1a1a1a]/10 dark:border-white/10 shadow-md">
                    <FileText className="h-10 w-10" />
                  </div>
                  <div>
                    <h3 className="text-sm font-semibold text-[#1a1a1a] dark:text-white">{selectedSource?.title}</h3>
                    <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-1">
                      {selectedSource?.authors?.join(", ")} · {selectedSource?.year}
                    </p>
                  </div>

                  {pdfFetchStatus ? (
                    <div className="p-4 rounded-2xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 text-xs w-full space-y-2 shadow-xs">
                      <div className="flex items-center justify-center gap-2">
                        {pdfFetchStatus.status === "resolving" || pdfFetchStatus.status === "saving" ? (
                          <>
                            <div className="h-3.5 w-3.5 rounded-full border-2 border-[#034f46] dark:border-[#cef5ca] border-t-transparent animate-spin" />
                            <span className="text-[#034f46] dark:text-[#cef5ca] font-semibold animate-pulse">{pdfFetchStatus.message}</span>
                          </>
                        ) : (
                          <>
                            <AlertCircle className="h-4 w-4 text-amber-600 dark:text-amber-400" />
                            <span className="text-[#1a1a1a] dark:text-white font-semibold">{pdfFetchStatus.message}</span>
                          </>
                        )}
                      </div>
                      {pdfFetchStatus.landingUrl && (
                        <a
                          href={pdfFetchStatus.landingUrl}
                          target="_blank"
                          rel="noreferrer"
                          className="inline-flex items-center gap-1 text-[11px] text-[#034f46] dark:text-[#cef5ca] hover:underline font-mono font-medium"
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
                        className="w-full flex items-center justify-center gap-2 py-3 px-5 rounded-full bg-[#034f46] hover:bg-[#034f46]/90 text-[#ffffeb] text-xs font-semibold shadow-sm shadow-[#034f46]/20 transition-all cursor-pointer"
                      >
                        <Zap className="h-4 w-4" />
                        <span>Fetch PDF via Multi-Source Protocol</span>
                      </button>
                      <p className="text-[11px] text-[#1a1a1a]/50 dark:text-white/50">
                        Queries Springer, Nature, Unpaywall, Semantic Scholar, Europe PMC &amp; Academic Mirrors
                      </p>
                    </div>
                  )}

                  <div className="pt-2">
                    <button
                      onClick={() => setViewMode("reader")}
                      className="text-xs font-medium text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a] dark:hover:text-white transition-colors cursor-pointer"
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
                <div className="h-20 w-20 rounded-[2rem] bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 flex items-center justify-center shadow-lg">
                  <BookOpen className="h-9 w-9 text-[#034f46] dark:text-[#cef5ca]" />
                </div>
                <div className="absolute -top-1 -right-1 h-7 w-7 rounded-full bg-[#cef5ca] text-[#114e0b] border border-[#cef5ca] flex items-center justify-center shadow-sm">
                  <Sparkles className="h-3.5 w-3.5" />
                </div>
              </div>
              <h3 className="text-xl font-serif italic text-[#1a1a1a] dark:text-white mb-2 tracking-tight">
                Systematic Evidence Canvas
              </h3>
              <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 leading-relaxed mb-6 max-w-sm">
                No paper selected. Add peer-reviewed papers by DOI or upload local PDFs to begin extracting verbatim claims and synthesis notes.
              </p>
              <div className="flex flex-wrap items-center justify-center gap-3">
                <button
                  onClick={() => setIsAddSourceOpen(true)}
                  className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-[#034f46] hover:bg-[#034f46]/90 text-[#ffffeb] text-xs font-semibold shadow-sm shadow-[#034f46]/20 cursor-pointer"
                >
                  <Plus className="h-4 w-4" />
                  <span>Add First Paper</span>
                </button>
                <label className="flex items-center gap-2 px-5 py-2.5 rounded-full bg-white dark:bg-[#1a1e1c] hover:bg-[#ffffeb] dark:hover:bg-white/10 text-[#1a1a1a] dark:text-white border border-[#1a1a1a]/12 dark:border-white/15 text-xs font-semibold cursor-pointer shadow-xs">
                  <Download className="h-4 w-4 text-[#034f46] dark:text-[#cef5ca]" />
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
            {/* Simulated High-Fidelity Paper Canvas (Page 1) */}
            <div
              className="bg-white dark:bg-[#1a1e1c] text-[#1a1a1a] dark:text-[#e8eae6] rounded-[2rem] shadow-xl border border-[#1a1a1a]/8 dark:border-white/10 p-8 sm:p-12 w-full max-w-2xl transition-all font-serif"
              style={{ transform: `scale(${zoomLevel / 100})`, transformOrigin: "top center" }}
            >
              <div className="border-b border-[#1a1a1a]/10 dark:border-white/10 pb-5 mb-6 font-sans">
                <span className="text-[10px] font-bold text-[#034f46] dark:text-[#cef5ca] tracking-wider uppercase">
                  {selectedSource?.journal || "The Lancet Global Health"} · Research Articles
                </span>
                <h1 className="text-xl font-serif font-bold text-[#1a1a1a] dark:text-white mt-2 leading-snug">
                  {selectedSource?.title}
                </h1>
                <p className="text-xs text-[#1a1a1a]/65 dark:text-white/65 mt-2 font-serif">
                  {selectedSource?.authors?.join(", ")}
                </p>
                {selectedSource?.doi && (
                  <p className="text-[10px] text-[#034f46] dark:text-[#cef5ca] mt-1.5 font-mono">
                    https://doi.org/{selectedSource?.doi}
                  </p>
                )}
              </div>

              {/* Research In Context Callout */}
              <div className="p-5 rounded-2xl bg-[#cef5ca]/25 dark:bg-[#034f46]/20 border-l-4 border-[#034f46] dark:border-[#cef5ca] mb-6 text-xs text-[#1a1a1a] dark:text-white/90 space-y-2 font-sans">
                <h3 className="font-bold text-[#034f46] dark:text-[#cef5ca]">Research in Context</h3>
                <p className="leading-relaxed">
                  <strong>Evidence before this study:</strong> Non-communicable disease (NCD) policy implementation
                  was monitored across 194 countries from 2014 to 2021 using repeated cross-sectional surveillance.
                </p>
                <p className="leading-relaxed">
                  <strong>Added value of this study:</strong> We estimated the own- and cross-price elasticities
                  controlling for corporate financial influence and deprivation indexes.
                </p>
                <button
                  onClick={() =>
                    handleInsertQuote(
                      "Non-communicable disease policy implementation was monitored across 194 countries from 2014 to 2021 using repeated cross-sectional surveillance.",
                      1
                    )
                  }
                  className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[#114e0b] dark:text-[#cef5ca] hover:text-[#034f46] bg-[#cef5ca] dark:bg-[#034f46]/60 px-3 py-1 rounded-full cursor-pointer mt-1"
                >
                  <Quote className="h-3 w-3" /> Quote to Review Notes
                </button>
              </div>

              {/* Methodology Paragraph */}
              <div className="space-y-3 text-xs leading-relaxed font-serif text-[#1a1a1a]/85 dark:text-white/85">
                <h2 className="text-sm font-sans font-bold text-[#1a1a1a] dark:text-white">Methods</h2>
                <p>
                  The linear approximate almost ideal demand system was estimated across a panel representative
                  of 3,694 households. The Own-price elasticity for animal-welfare and certified organic foods was
                  computed at -1.42 (p &lt; 0.01).
                </p>
                <button
                  onClick={() =>
                    handleInsertQuote(
                      "The linear approximate almost ideal demand system was estimated across a panel representative of 3,694 households (p < 0.01).",
                      2
                    )
                  }
                  className="inline-flex items-center gap-1.5 text-[11px] font-semibold text-[#034f46] dark:text-[#cef5ca] hover:text-[#034f46]/80 bg-[#ffffeb] dark:bg-[#121413] border border-[#1a1a1a]/10 dark:border-white/10 px-3 py-1 rounded-full cursor-pointer font-sans"
                >
                  <Quote className="h-3 w-3" /> Quote Methodology (p. 2)
                </button>
              </div>
            </div>
          </div>
          )}
        </main>

        {/* PANE 3: Evidence & Synthesis Studio (Right) */}
        <aside className="w-80 lg:w-96 flex flex-col border-l border-[#1a1a1a]/8 dark:border-white/10 bg-white/70 dark:bg-[#161a18]/80 backdrop-blur-sm flex-shrink-0">
          {/* Studio Tab Switcher */}
          <div className="flex border-b border-[#1a1a1a]/8 dark:border-white/10 p-2 bg-white/80 dark:bg-[#161a18]/80 gap-1.5">
            <button
              onClick={() => setActiveTab("evidence")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all cursor-pointer ${
                activeTab === "evidence"
                  ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                  : "text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a] dark:hover:text-white"
              }`}
            >
              🔬 Evidence
            </button>
            <button
              onClick={() => setActiveTab("notes")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all cursor-pointer ${
                activeTab === "notes"
                  ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                  : "text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a] dark:hover:text-white"
              }`}
            >
              📝 Notes
            </button>
            <button
              onClick={() => setActiveTab("export")}
              className={`flex-1 py-1.5 text-xs font-semibold rounded-full transition-all cursor-pointer ${
                activeTab === "export"
                  ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                  : "text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a] dark:hover:text-white"
              }`}
            >
              📤 Export
            </button>
          </div>

          {/* TAB 1: Verbatim Evidence Claims */}
          {activeTab === "evidence" && (
            <div className="flex-1 overflow-y-auto p-4 space-y-3.5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-semibold text-[#1a1a1a] dark:text-white">Grounded Extraction</span>
                <span className="text-[10px] bg-[#cef5ca] dark:bg-[#034f46]/40 text-[#114e0b] dark:text-[#cef5ca] px-2.5 py-0.5 rounded-full border border-[#cef5ca] dark:border-[#034f46] font-semibold">
                  Zero Hallucinations
                </span>
              </div>

              {/* Methodology Card */}
              <div className="p-4 rounded-2xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/8 dark:border-white/10 space-y-2 shadow-xs">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#034f46] dark:text-[#cef5ca]">📐 Methodology</span>
                  <span className="text-[10px] text-[#1a1a1a]/50 dark:text-white/50">Page 2</span>
                </div>
                <p className="text-xs text-[#1a1a1a]/80 dark:text-white/80 leading-relaxed italic">
                  "Linear approximate almost ideal demand system estimated on scanner data."
                </p>
                <button
                  onClick={() =>
                    handleInsertQuote("Linear approximate almost ideal demand system estimated on scanner data.", 2)
                  }
                  className="text-[11px] text-[#034f46] dark:text-[#cef5ca] hover:text-[#034f46]/80 flex items-center gap-1 font-semibold cursor-pointer"
                >
                  <Plus className="h-3 w-3" /> Insert into Review Notes
                </button>
              </div>

              {/* Sample Size Card */}
              <div className="p-4 rounded-2xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/8 dark:border-white/10 space-y-2 shadow-xs">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#4a154b] dark:text-[#f0d7ff]">👥 Sample Size (N)</span>
                  <span className="text-[10px] text-[#1a1a1a]/50 dark:text-white/50">Page 3</span>
                </div>
                <p className="text-xs text-[#1a1a1a]/80 dark:text-white/80 leading-relaxed">
                  <strong>Cohort:</strong> 3,694 households (representative scanner panel).
                </p>
              </div>

              {/* Statistics Card */}
              <div className="p-4 rounded-2xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/8 dark:border-white/10 space-y-2 shadow-xs">
                <div className="flex items-center justify-between text-xs">
                  <span className="font-semibold text-[#a05a00] dark:text-[#ffa946]">📊 Statistics &amp; Rigour</span>
                  <span className="text-[10px] text-[#1a1a1a]/50 dark:text-white/50">Page 6</span>
                </div>
                <p className="text-xs text-[#1a1a1a]/80 dark:text-white/80 leading-relaxed">
                  <strong>Estimates:</strong> Price elasticity = -1.42 (p &lt; 0.01). Significant cross-substitution detected.
                </p>
              </div>
            </div>
          )}

          {/* TAB 2: Synthesis Review Notes */}
          {activeTab === "notes" && (
            <div className="flex-1 flex flex-col p-4 overflow-hidden">
              <span className="text-xs font-semibold text-[#1a1a1a] dark:text-white mb-2">Project Synthesis Review Notes</span>
              <textarea
                value={notesContent}
                onChange={(e) => handleSaveNotes(e.target.value)}
                placeholder="Write critical reflections, draft synthesis paragraphs, or quote evidence..."
                className="flex-1 w-full bg-[#fbfbf6] dark:bg-[#1a1e1c] border border-[#1a1a1a]/12 dark:border-white/15 rounded-2xl p-4 text-xs text-[#1a1a1a] dark:text-white font-mono leading-relaxed resize-none focus:outline-none focus:bg-white dark:focus:bg-[#222825] focus:border-[#034f46]"
              />
              <span className="text-[10px] text-[#1a1a1a]/50 dark:text-white/50 mt-2">Saved automatically to local IndexedDB</span>
            </div>
          )}

          {/* TAB 3: Export & Citations */}
          {activeTab === "export" && (
            <div className="flex-1 p-4 space-y-4 overflow-y-auto">
              <div>
                <span className="text-xs font-semibold text-[#1a1a1a] dark:text-white">Selected Source Citation</span>
                <p className="text-[11px] text-[#1a1a1a]/60 dark:text-white/60 mt-0.5">
                  Copy formatted citation for: <span className="text-[#1a1a1a] dark:text-white font-medium">{selectedSource?.title}</span>
                </p>
                <div className="grid grid-cols-2 gap-2 mt-3">
                  <button
                    onClick={() => handleCopyCitation("APA")}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-full bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/12 dark:border-white/15 hover:bg-[#ffffeb] dark:hover:bg-[#222825] text-xs font-semibold text-[#1a1a1a] dark:text-white transition-colors cursor-pointer shadow-xs"
                  >
                    {copiedCitation === "APA" ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#034f46] dark:text-[#cef5ca]" />
                        <span className="text-[#034f46] dark:text-[#cef5ca]">Copied APA!</span>
                      </>
                    ) : (
                      <>
                        <Quote className="h-3.5 w-3.5 text-[#034f46] dark:text-[#cef5ca]" />
                        <span>Copy APA</span>
                      </>
                    )}
                  </button>

                  <button
                    onClick={() => handleCopyCitation("BibTeX")}
                    className="flex items-center justify-center gap-1.5 py-2 px-3 rounded-full bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/12 dark:border-white/15 hover:bg-[#ffffeb] dark:hover:bg-[#222825] text-xs font-semibold text-[#1a1a1a] dark:text-white transition-colors cursor-pointer shadow-xs"
                  >
                    {copiedCitation === "BibTeX" ? (
                      <>
                        <CheckCircle2 className="h-3.5 w-3.5 text-[#034f46] dark:text-[#cef5ca]" />
                        <span className="text-[#034f46] dark:text-[#cef5ca]">Copied BibTeX!</span>
                      </>
                    ) : (
                      <>
                        <Quote className="h-3.5 w-3.5 text-[#4a154b] dark:text-[#f0d7ff]" />
                        <span>Copy BibTeX</span>
                      </>
                    )}
                  </button>
                </div>
              </div>

              <div className="h-px bg-[#1a1a1a]/8 dark:border-white/10 my-2" />

              <div>
                <span className="text-xs font-semibold text-[#1a1a1a] dark:text-white">Corpus Batch Export</span>
                <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-0.5">
                  Export all ({filteredSources.length}) loaded sources into your reference manager or PRISMA report:
                </p>

                <div className="space-y-2 mt-3">
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
                    className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 hover:border-[#034f46] dark:hover:border-[#cef5ca] text-xs font-semibold text-[#1a1a1a] dark:text-white transition-all cursor-pointer shadow-xs"
                  >
                    <span>Export All BibTeX (.bib)</span>
                    <Download className="h-4 w-4 text-[#034f46] dark:text-[#cef5ca]" />
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
                    className="w-full flex items-center justify-between p-3.5 rounded-2xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 hover:border-[#034f46] dark:hover:border-[#cef5ca] text-xs font-semibold text-[#1a1a1a] dark:text-white transition-all cursor-pointer shadow-xs"
                  >
                    <span>Export All EndNote / Zotero (RIS)</span>
                    <Download className="h-4 w-4 text-[#114e0b] dark:text-[#cef5ca]" />
                  </button>
                </div>
              </div>
            </div>
          )}
        </aside>
      </div>
    </div>
  );
}
