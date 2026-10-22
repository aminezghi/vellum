"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { FeaturedCarousel } from "@/components/FeaturedCarousel";
import { NotebookGrid } from "@/components/NotebookGrid";
import { NewNotebookModal } from "@/components/NewNotebookModal";
import { NotebookWorkspace } from "@/components/NotebookWorkspace";
import { AcademicSearchHub } from "@/components/AcademicSearchHub";
import { TrendingRadar } from "@/components/TrendingRadar";
import { AddToNotebookModal } from "@/components/AddToNotebookModal";
import { EmptyNotebooksState } from "@/components/EmptyNotebooksState";
import { CleanNotebooksModal } from "@/components/CleanNotebooksModal";
import { BatchDownloaderHub } from "@/components/BatchDownloaderHub";
import { ScreeningHub } from "@/components/ScreeningHub";
import { ConnectedGraphHub } from "@/components/ConnectedGraphHub";
import { Footer } from "@/components/Footer";
import { db, Notebook, Source, initializeStorage } from "@/lib/db";
import { AddablePaper } from "@/lib/paper";
import { AcademicPaperResult } from "@/app/api/search/route";
import {
  Plus,
  Layers,
  Sparkles,
  Search,
  Trash2,
  ArrowUpRight,
  Database,
  FileText,
  ShieldCheck,
  TrendingUp,
} from "lucide-react";

/** Everything the page shell needs to know about the notebook index. */
interface NotebookSnapshot {
  notebooks: Notebook[];
  totalSources: number;
}

/** Read the notebook index out of IndexedDB. I/O only — touches no React state. */
async function readNotebookSnapshot(): Promise<NotebookSnapshot> {
  await initializeStorage();
  const all = await db.notebooks.toArray();
  all.sort((a, b) => b.updatedAt - a.updatedAt);
  const totalSources = await db.sources.count();
  return { notebooks: all, totalSources };
}

export default function Home() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [activeNotebook, setActiveNotebook] = useState<Notebook | null>(null);
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCleanModalOpen, setIsCleanModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [totalSourcesCount, setTotalSourcesCount] = useState(0);

  // Modal for adding a paper to a notebook
  const [paperForAddModal, setPaperForAddModal] = useState<AddablePaper | null>(null);
  const [connectedSeed, setConnectedSeed] = useState<string>("DeepFruits: A Fruit Detection System Using Deep Neural Networks");

  const handleOpenConnectedGraph = (seed: string) => {
    setConnectedSeed(seed);
    setActiveTab("connected");
  };

  const applySnapshot = useCallback((snapshot: NotebookSnapshot) => {
    setNotebooks(snapshot.notebooks);
    setTotalSourcesCount(snapshot.totalSources);
    setLoading(false);
  }, []);

  const fetchNotebooks = useCallback(async () => {
    applySnapshot(await readNotebookSnapshot());
  }, [applySnapshot]);

  useEffect(() => {
    let active = true;
    readNotebookSnapshot().then((snapshot) => {
      // Bail if the page unmounted while IndexedDB was answering.
      if (active) applySnapshot(snapshot);
    });
    return () => {
      active = false;
    };
  }, [applySnapshot]);

  const handleSelectNotebook = (nb: Notebook) => {
    setActiveNotebook(nb);
  };

  // 1-Click Deep Inspection from Search or Trending feed
  const handleInspectPaper = async (paper: AcademicPaperResult) => {
    const inspectionNbId = `nb-inspect-${Date.now()}`;
    const newNb: Notebook = {
      id: inspectionNbId,
      title: paper.title,
      emoji: "🔬",
      description: `Deep systematic appraisal for ${paper.authors?.[0] || "Author"} (${paper.year || 2024})`,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      sourcesCount: 1,
      category: "Deep Appraisal",
      isFeatured: false,
    };

    const newSource: Source = {
      id: `src-${Date.now()}`,
      notebookId: inspectionNbId,
      title: paper.title,
      authors: paper.authors,
      year: paper.year,
      journal: paper.venue,
      doi: paper.doi,
      status: "ready",
      addedAt: Date.now(),
    };

    await db.notebooks.put(newNb);
    await db.sources.put(newSource);
    await fetchNotebooks();
    setActiveNotebook(newNb);
  };

  // If a notebook is actively open, render the Tri-Pane Workspace!
  if (activeNotebook) {
    return (
      <NotebookWorkspace
        notebook={activeNotebook}
        onBack={() => {
          setActiveNotebook(null);
          fetchNotebooks();
        }}
        onUpdate={fetchNotebooks}
      />
    );
  }

  // Filter notebooks by search query and active tab
  const filteredNotebooks = notebooks.filter((nb) => {
    const matchesSearch =
      nb.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (nb.description && nb.description.toLowerCase().includes(searchQuery.toLowerCase())) ||
      (nb.category && nb.category.toLowerCase().includes(searchQuery.toLowerCase()));

    if (!matchesSearch) return false;

    if (activeTab === "collections") {
      return (nb.sourcesCount || 0) > 10;
    }
    return true;
  });

  const featuredNotebooks = notebooks.filter((nb) => nb.isFeatured || (nb.sourcesCount || 0) > 100);

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[var(--ink)] flex flex-col font-sans transition-colors duration-200">
      {/* Top Header */}
      <Header
        activeTab={activeTab}
        setActiveTab={setActiveTab}
        searchQuery={searchQuery}
        setSearchQuery={setSearchQuery}
        onNewNotebook={() => setIsModalOpen(true)}
        onClearNotebooks={() => setIsCleanModalOpen(true)}
        totalNotebooks={notebooks.length}
        viewMode={viewMode}
        setViewMode={setViewMode}
      />

      {/* Main Container: All-in-One Bento Dashboard */}
      <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14 py-6 sm:py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-xs text-[var(--ink-muted)]">
            <span className="animate-pulse">Loading research studio...</span>
          </div>
        ) : (
          <>
            {/* FERNLY BENTO HERO BOARD (Shown on All or My Notebooks) */}
            {activeTab === "all" && !searchQuery && (
              <section className="space-y-4">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                  <div>
                    <div className="flex items-center gap-2">
                      <span className="fernly-badge fernly-badge-leaf text-[11px] font-semibold">
                        Systematic Literature Intelligence
                      </span>
                      <span className="text-[11px] text-[var(--ink-muted)] font-medium">
                        v2.1 · Local-First Architecture
                      </span>
                    </div>
                    <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[var(--ink)] mt-1">
                      Academic Research Studio
                    </h1>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      onClick={() => {
                        setActiveTab("search");
                        window.scrollTo({ top: 300, behavior: "smooth" });
                      }}
                      className="btn-fernly-ghost flex items-center gap-1.5 px-4 py-2 rounded-full text-xs font-semibold"
                    >
                      <Search className="h-3.5 w-3.5" />
                      <span>Live Search</span>
                    </button>
                    <button
                      onClick={() => setIsModalOpen(true)}
                      className="btn-fernly-primary flex items-center gap-1.5 px-5 py-2 rounded-full text-xs font-semibold shadow-xs"
                    >
                      <Plus className="h-4 w-4" />
                      <span>New Project</span>
                    </button>
                  </div>
                </div>

                {/* 4 Bento Stat Cards Row */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                  {/* Card 1: Stat Hero Deep Botanical */}
                  <div
                    onClick={() => setIsModalOpen(true)}
                    className="fernly-stat-hero p-5 rounded-[1.75rem] flex flex-col justify-between cursor-pointer group min-h-[140px]"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--g-200)] tracking-wide">
                        Active Reviews
                      </span>
                      <span className="fernly-arrow w-7 h-7 rounded-full bg-white/10 group-hover:bg-white/20 text-white flex items-center justify-center transition-all">
                        <ArrowUpRight className="h-4 w-4" />
                      </span>
                    </div>
                    <div className="mt-3">
                      <div className="text-3xl sm:text-4xl font-extrabold text-white tracking-tight">
                        {notebooks.length}
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[var(--g-200)]">
                        <TrendingUp className="h-3.5 w-3.5" />
                        <span>Systematic synthesis notebooks</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 2: Indexed Evidence */}
                  <div className="fernly-card p-5 rounded-[1.75rem] flex flex-col justify-between min-h-[140px] group">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--ink-muted)]">
                        Local Corpus
                      </span>
                      <span className="fernly-arrow w-7 h-7 rounded-full bg-[var(--panel)] text-[var(--ink)] group-hover:bg-[var(--g-800)] group-hover:text-white flex items-center justify-center transition-all">
                        <Database className="h-3.5 w-3.5" />
                      </span>
                    </div>
                    <div className="mt-3">
                      <div className="text-3xl sm:text-4xl font-extrabold text-[var(--ink)] tracking-tight">
                        {totalSourcesCount}
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[var(--ink-muted)]">
                        <FileText className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                        <span>Papers &amp; preprints stored</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 3: Academic Corpus */}
                  <div
                    onClick={() => setActiveTab("search")}
                    className="fernly-card p-5 rounded-[1.75rem] flex flex-col justify-between min-h-[140px] cursor-pointer group"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--ink-muted)]">
                        Global Corpus
                      </span>
                      <span className="fernly-arrow w-7 h-7 rounded-full bg-[var(--panel)] text-[var(--ink)] group-hover:bg-[var(--g-800)] group-hover:text-white flex items-center justify-center transition-all">
                        <ArrowUpRight className="h-4 w-4" />
                      </span>
                    </div>
                    <div className="mt-3">
                      <div className="text-3xl sm:text-4xl font-extrabold text-[var(--ink)] tracking-tight">
                        250M+
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[var(--ink-muted)]">
                        <Sparkles className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                        <span>OpenAlex · arXiv · Crossref</span>
                      </div>
                    </div>
                  </div>

                  {/* Card 4: Local Privacy Guarantee */}
                  <div className="fernly-card p-5 rounded-[1.75rem] flex flex-col justify-between min-h-[140px] group">
                    <div className="flex items-center justify-between">
                      <span className="text-xs font-semibold text-[var(--ink-muted)]">
                        Privacy &amp; Storage
                      </span>
                      <span className="w-7 h-7 rounded-full bg-[var(--panel)] text-[var(--g-600)] dark:text-[var(--g-400)] flex items-center justify-center">
                        <ShieldCheck className="h-4 w-4" />
                      </span>
                    </div>
                    <div className="mt-3">
                      <div className="text-xl sm:text-2xl font-bold text-[var(--ink)] tracking-tight">
                        100% Local
                      </div>
                      <div className="flex items-center gap-1.5 mt-1 text-[11px] text-[var(--ink-muted)]">
                        <span>IndexedDB · Zero telemetry</span>
                      </div>
                    </div>
                  </div>
                </div>
              </section>
            )}

            {/* TOP ZONE: Academic Literature Search & Trending Radar */}
            {/* ACADEMIC SEARCH HUB (With Boolean & Desktop Style Search) */}
            {(activeTab === "all" || activeTab === "search") && (
              <AcademicSearchHub
                onAddToNotebook={(p) => setPaperForAddModal(p)}
                onInspectPaper={handleInspectPaper}
                onOpenConnectedGraph={handleOpenConnectedGraph}
              />
            )}

            {/* CONNECTED PAPERS HUB (Interactive Citation Network Force Graph) */}
            {activeTab === "connected" && (
              <ConnectedGraphHub
                initialSeed={connectedSeed}
                onAddToNotebook={(p) => setPaperForAddModal(p)}
              />
            )}

            {(activeTab === "all" || activeTab === "trends") && (
              <TrendingRadar
                onAddToNotebook={(p) => setPaperForAddModal(p)}
                onInspectPaper={handleInspectPaper}
                onOpenConnectedGraph={handleOpenConnectedGraph}
              />
            )}

            {/* BATCH DOWNLOADER HUB (Incorporated from Desktop Engine) */}
            {activeTab === "downloader" && (
              <BatchDownloaderHub notebooks={notebooks} />
            )}

            {/* ASREVIEW ACTIVE LEARNING SCREENING HUB */}
            {activeTab === "screening" && (
              <ScreeningHub notebooks={notebooks} />
            )}

            {/* BOTTOM ZONE: Research Notebooks & Collections */}
            {(activeTab === "all" || activeTab === "my-notebooks" || activeTab === "collections") && (
              <div className="pt-2">
                {/* Consistent Section Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 pb-4 border-b border-[var(--card-bdr)] mb-6">
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center rounded-2xl bg-[var(--g-950)] dark:bg-[var(--g-900)] text-[var(--g-300)] shadow-xs flex-shrink-0 border border-[var(--g-800)]">
                      <Layers className="h-5 w-5" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="text-base sm:text-lg font-bold tracking-tight text-[var(--ink)]">
                          {activeTab === "collections"
                            ? "Curated Research Collections"
                            : "My Systematic Review Notebooks"}
                        </h2>
                        <span className="fernly-badge fernly-badge-leaf text-[10px] font-semibold">
                          Local-First Corpus
                        </span>
                      </div>
                      <p className="text-xs text-[var(--ink-muted)] mt-0.5 font-medium leading-relaxed">
                        Indexed systematic reviews and synthesized evidence · 100% free and stored privately on your machine
                      </p>
                    </div>
                  </div>

                  {/* Notebook Action Buttons */}
                  <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
                    {notebooks.length > 0 && (
                      <button
                        onClick={() => setIsCleanModalOpen(true)}
                        className="flex items-center gap-1.5 px-3.5 py-2 rounded-full border border-red-200 dark:border-red-900/40 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs font-semibold transition-all cursor-pointer shadow-xs"
                        title="Clean or reset notebooks from local storage"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                        <span>Clean Workspace</span>
                      </button>
                    )}

                    <button
                      onClick={() => setIsModalOpen(true)}
                      className="btn-fernly-primary flex items-center gap-2 px-4 sm:px-5 py-2 rounded-full text-xs font-semibold shadow-xs cursor-pointer"
                    >
                      <Plus className="h-4 w-4" />
                      <span>New notebook</span>
                    </button>
                  </div>
                </div>

                {/* If no notebooks exist yet and no search query, show Empty State */}
                {notebooks.length === 0 && !searchQuery ? (
                  <EmptyNotebooksState
                    onCreateNotebook={() => setIsModalOpen(true)}
                    onExploreSearch={() => {
                      setActiveTab("search");
                      window.scrollTo({ top: 0, behavior: "smooth" });
                    }}
                    onQuickStart={async (title, emoji, category) => {
                      const newNb: Notebook = {
                        id: `nb-${Date.now()}`,
                        title,
                        emoji,
                        category,
                        description: `Systematic review on ${title}.`,
                        createdAt: Date.now(),
                        updatedAt: Date.now(),
                        sourcesCount: 0,
                        isFeatured: false,
                      };
                      await db.notebooks.put(newNb);
                      await fetchNotebooks();
                      setActiveNotebook(newNb);
                    }}
                  />
                ) : (
                  <>
                    {/* Featured Notebooks Carousel (Shown on 'all' or 'my-notebooks' if not searching) */}
                    {!searchQuery && activeTab !== "collections" && featuredNotebooks.length > 0 && (
                      <div className="mb-8">
                        <FeaturedCarousel
                          notebooks={featuredNotebooks}
                          onSelectNotebook={handleSelectNotebook}
                        />
                      </div>
                    )}

                    {/* Recent Notebooks Grid Header */}
                    <div className="flex items-center justify-between mb-4">
                      <h3 className="text-sm font-bold text-[var(--ink)] tracking-tight flex items-center gap-2">
                        <span>
                          {searchQuery
                            ? `Search Results (${filteredNotebooks.length})`
                            : activeTab === "collections"
                            ? "Collections"
                            : "Recent notebooks"}
                        </span>
                      </h3>
                    </div>

                    {/* Notebook Cards Grid */}
                    <NotebookGrid
                      notebooks={filteredNotebooks}
                      onSelectNotebook={handleSelectNotebook}
                      viewMode={viewMode}
                      onRefresh={fetchNotebooks}
                    />
                  </>
                )}
              </div>
            )}
          </>
        )}
      </main>

      {/* Authorship & Developer Footer */}
      <Footer
        onClearAllNotebooks={() => setIsCleanModalOpen(true)}
        notebooksCount={notebooks.length}
      />

      {/* Create New Notebook Modal */}
      <NewNotebookModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreated={(newNb) => {
          fetchNotebooks();
          setActiveNotebook(newNb);
        }}
      />

      {/* Clean / Delete Notebooks Modal */}
      <CleanNotebooksModal
        isOpen={isCleanModalOpen}
        onClose={() => setIsCleanModalOpen(false)}
        onCleaned={fetchNotebooks}
        totalNotebooks={notebooks.length}
      />

      {/* Add Paper to Notebook Modal */}
      <AddToNotebookModal
        paper={paperForAddModal}
        notebooks={notebooks}
        isOpen={!!paperForAddModal}
        onClose={() => setPaperForAddModal(null)}
        onAdded={(nbId) => {
          fetchNotebooks();
          const target = notebooks.find((n) => n.id === nbId);
          if (target) {
            setActiveNotebook(target);
          }
        }}
      />
    </div>
  );
}
