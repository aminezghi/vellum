"use client";

import React, { useState, useEffect } from "react";
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
import { Footer } from "@/components/Footer";
import { db, Notebook, Source, initializeStorage } from "@/lib/db";
import { AcademicPaperResult } from "@/app/api/search/route";
import { Plus, BookOpen, Layers, Sparkles, Flame, Search, Trash2 } from "lucide-react";

export default function Home() {
  const [notebooks, setNotebooks] = useState<Notebook[]>([]);
  const [activeNotebook, setActiveNotebook] = useState<Notebook | null>(null);
  const [activeTab, setActiveTab] = useState("all");
  const [searchQuery, setSearchQuery] = useState("");
  const [viewMode, setViewMode] = useState<"grid" | "list">("grid");
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isCleanModalOpen, setIsCleanModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  // Modal for adding a paper to a notebook
  const [paperForAddModal, setPaperForAddModal] = useState<AcademicPaperResult | null>(null);

  const fetchNotebooks = async () => {
    await initializeStorage();
    const all = await db.notebooks.toArray();
    all.sort((a, b) => b.updatedAt - a.updatedAt);
    setNotebooks(all);
    setLoading(false);
  };

  useEffect(() => {
    fetchNotebooks();
  }, []);

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
    <div className="min-h-screen bg-[#ffffeb] dark:bg-[#121413] text-[#1a1a1a] dark:text-[#e8eae6] flex flex-col font-sans selection:bg-[#cef5ca] selection:text-[#114e0b] dark:selection:bg-[#034f46] dark:selection:text-[#cef5ca] transition-colors duration-200">
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

      {/* Main Container: All-in-One Dashboard (Fluid Full-Screen Responsive) */}
      <main className="flex-1 w-full px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14 py-6 sm:py-8 space-y-8">
        {loading ? (
          <div className="flex items-center justify-center py-20 text-xs text-[#1a1a1a]/50 dark:text-white/50">
            <span className="animate-pulse">Loading research studio...</span>
          </div>
        ) : (
          <>
            {/* TOP ZONE: Academic Literature Search & Trending Radar */}
            {(activeTab === "all" || activeTab === "search") && (
              <AcademicSearchHub
                onAddToNotebook={(p) => setPaperForAddModal(p)}
                onInspectPaper={handleInspectPaper}
              />
            )}

            {(activeTab === "all" || activeTab === "trends") && (
              <TrendingRadar
                onAddToNotebook={(p) => setPaperForAddModal(p)}
                onInspectPaper={handleInspectPaper}
              />
            )}

            {/* BOTTOM ZONE: Research Notebooks & Collections */}
            {(activeTab === "all" || activeTab === "my-notebooks" || activeTab === "collections") && (
              <div className="pt-2">
                {/* Consistent Section Header */}
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 pb-4 border-b border-[#1a1a1a]/8 dark:border-white/10 mb-6">
                  <div className="flex items-start sm:items-center gap-3">
                    <div className="flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center rounded-2xl bg-[#034f46] text-[#ffffeb] shadow-xs flex-shrink-0">
                      <Layers className="h-5 w-5 text-[#cef5ca]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2 flex-wrap">
                        <h2 className="text-base sm:text-lg font-bold tracking-tight text-[#1a1a1a] dark:text-[#ffffeb]">
                          {activeTab === "collections"
                            ? "Curated Research Collections"
                            : "My Systematic Review Notebooks"}
                        </h2>
                        <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#cef5ca] text-[#114e0b] dark:bg-[#034f46] dark:text-[#cef5ca] border border-[#114e0b]/20">
                          Local-First Corpus
                        </span>
                      </div>
                      <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-0.5 font-medium leading-relaxed">
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
                      className="flex items-center gap-2 px-4 sm:px-5 py-2 rounded-full bg-[#034f46] hover:bg-[#023630] text-[#ffffeb] text-xs font-semibold shadow-xs transition-all cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
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
                      <h3 className="text-sm font-semibold text-[#1a1a1a] dark:text-white tracking-tight flex items-center gap-2">
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
