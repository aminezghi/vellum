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
import { DashboardBento } from "@/components/DashboardBento";
import { Footer } from "@/components/Footer";
import { db, Notebook, Source, initializeStorage } from "@/lib/db";
import { AddablePaper } from "@/lib/paper";
import { AcademicPaperResult } from "@/app/api/search/route";
import {
  Plus,
  Layers,
  CheckCircle2,
  X,
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
  const [toastNotification, setToastNotification] = useState<{
    message: string;
    notebookId?: string;
    notebookTitle?: string;
  } | null>(null);

  const showToast = (message: string, notebookId?: string, notebookTitle?: string) => {
    setToastNotification({ message, notebookId, notebookTitle });
    setTimeout(() => {
      setToastNotification(null);
    }, 4500);
  };

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
      abstract: paper.abstract,
      status: "ready",
      addedAt: Date.now(),
    };

    await db.notebooks.put(newNb);
    await db.sources.put(newSource);
    await fetchNotebooks();
    setActiveNotebook(newNb);
  };

  // 1-Click Preset Benchmark Loading (from Dashboard Bento)
  const handleLoadSample = async (
    title: string,
    emoji: string,
    category: string,
    sampleDoi?: string
  ) => {
    const sampleId = `nb-sample-${Date.now()}`;
    const newNb: Notebook = {
      id: sampleId,
      title,
      emoji,
      category,
      description: `Demonstration systematic review on ${title}.`,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      sourcesCount: 1,
      isFeatured: true,
    };

    const sampleSource: Source = {
      id: `src-sample-${Date.now()}`,
      notebookId: sampleId,
      title,
      authors: ["Lead Investigator et al."],
      year: 2024,
      journal: category,
      doi: sampleDoi || "10.3390/s16070988",
      abstract: `This systematic review investigates foundational methodology, benchmarking datasets, and quantitative appraisal protocols in ${category}.`,
      status: "ready",
      addedAt: Date.now(),
    };

    await db.notebooks.put(newNb);
    await db.sources.put(sampleSource);
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
        onOpenConnectedGraph={(seed) => {
          setActiveNotebook(null);
          handleOpenConnectedGraph(seed);
        }}
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
            {/* DASHBOARD TAB (Landing Mission Control with 3 Core Engines & Sample Presets) */}
            {activeTab === "all" && !searchQuery && (
              <DashboardBento
                notebooksCount={notebooks.length}
                totalSourcesCount={totalSourcesCount}
                onNewProject={() => setIsModalOpen(true)}
                onNavigateTab={(tab) => {
                  setActiveTab(tab);
                  window.scrollTo({ top: 0, behavior: "smooth" });
                }}
                onLoadSample={handleLoadSample}
              />
            )}

            {/* ACADEMIC SEARCH TAB */}
            {activeTab === "search" && (
              <AcademicSearchHub
                onAddToNotebook={(p) => setPaperForAddModal(p)}
                onInspectPaper={handleInspectPaper}
                onOpenConnectedGraph={handleOpenConnectedGraph}
              />
            )}

            {/* CONNECTED PAPERS TAB */}
            {activeTab === "connected" && (
              <ConnectedGraphHub
                initialSeed={connectedSeed}
                onAddToNotebook={(p) => setPaperForAddModal(p)}
              />
            )}

            {/* TRENDING RADAR TAB */}
            {activeTab === "trends" && (
              <TrendingRadar
                onAddToNotebook={(p) => setPaperForAddModal(p)}
                onInspectPaper={handleInspectPaper}
                onOpenConnectedGraph={handleOpenConnectedGraph}
              />
            )}

            {/* BATCH DOWNLOADER TAB */}
            {activeTab === "downloader" && (
              <BatchDownloaderHub notebooks={notebooks} />
            )}

            {/* ASREVIEW ACTIVE LEARNING SCREENING TAB */}
            {activeTab === "screening" && (
              <ScreeningHub notebooks={notebooks} />
            )}

            {/* BOTTOM ZONE: Research Notebooks & Collections */}
            {(activeTab === "all" || activeTab === "my-notebooks" || activeTab === "collections") && (
              <div id="notebooks-section" className="pt-2">
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
                    <button
                      onClick={() => setIsModalOpen(true)}
                      className="btn-fernly-primary flex items-center gap-2 px-4 sm:px-5 py-2 rounded-full text-xs font-semibold shadow-xs cursor-pointer"
                    >
                      <Plus className="h-4 w-4" />
                      <span>New Project</span>
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
                          onViewAll={() => {
                            setActiveTab("collections");
                            window.scrollTo({ top: 350, behavior: "smooth" });
                          }}
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
          showToast(`✓ Added to "${target?.title || "Notebook"}"`, nbId, target?.title);
        }}
      />

      {/* Non-intrusive Toast for Added Papers */}
      {toastNotification && (
        <div className="fixed bottom-6 right-6 z-50 flex items-center gap-3 px-4 py-3 rounded-2xl bg-[var(--card)] border border-[var(--g-500)] text-[var(--ink)] shadow-2xl animate-in slide-in-from-bottom-5 duration-300 max-w-md">
          <div className="h-8 w-8 rounded-full bg-[var(--g-100)] text-[var(--g-800)] flex items-center justify-center flex-shrink-0">
            <CheckCircle2 className="h-4 w-4" />
          </div>
          <div className="flex flex-col text-xs flex-1 min-w-0">
            <span className="font-semibold truncate">{toastNotification.message}</span>
            {toastNotification.notebookTitle && (
              <span className="text-[10px] text-[var(--muted)] truncate">
                Saved in {toastNotification.notebookTitle} • Keep exploring or open project
              </span>
            )}
          </div>
          {toastNotification.notebookId && (
            <button
              onClick={() => {
                const target = notebooks.find((n) => n.id === toastNotification.notebookId);
                if (target) {
                  setActiveNotebook(target);
                  setToastNotification(null);
                }
              }}
              className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-[var(--g-800)] text-white hover:bg-[var(--g-950)] cursor-pointer flex-shrink-0"
            >
              Open →
            </button>
          )}
          <button
            onClick={() => setToastNotification(null)}
            className="p-1 rounded-full text-[var(--muted)] hover:text-[var(--ink)] cursor-pointer flex-shrink-0"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      )}
    </div>
  );
}
