"use client";

import React, { useState } from "react";
import { Notebook, db } from "@/lib/db";
import { MoreVertical, Trash2, ArrowUpRight, BookOpen, Layers } from "lucide-react";

interface NotebookGridProps {
  notebooks: Notebook[];
  onSelectNotebook: (notebook: Notebook) => void;
  viewMode: "grid" | "list";
  onRefresh: () => void;
}

export function NotebookGrid({
  notebooks,
  onSelectNotebook,
  viewMode,
  onRefresh,
}: NotebookGridProps) {
  const [activeMenuId, setActiveMenuId] = useState<string | null>(null);

  const handleDelete = async (e: React.MouseEvent, id: string, title?: string) => {
    e.stopPropagation();
    if (confirm(`Delete project "${title || id}" and all its saved evidence sources?`)) {
      try {
        // One transaction so a failure part-way never leaves orphaned rows.
        await db.transaction("rw", [db.notebooks, db.sources, db.notes, db.evidence], async () => {
          await db.notebooks.delete(id);
          await db.sources.where("notebookId").equals(id).delete();
          await db.notes.where("notebookId").equals(id).delete();
          await db.evidence.where("notebookId").equals(id).delete();
        });
      } catch (err) {
        console.error("Failed to delete project:", err);
        alert("Could not delete this project. Please try again.");
      }
      onRefresh();
    }
    setActiveMenuId(null);
  };

  if (notebooks.length === 0) {
    return (
      <div className="fernly-card flex flex-col items-center justify-center p-14 text-center border-dashed">
        <div className="relative mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30 shadow-sm">
          <BookOpen className="h-6 w-6 text-[var(--g-700)]" />
          <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-md bg-[var(--g-950)] text-white shadow-xs">
            <Layers className="h-3 w-3" />
          </div>
        </div>
        <h3 className="text-sm font-semibold text-[var(--ink)]">No projects match this view</h3>
        <p className="text-xs text-[var(--muted)] mt-1.5 max-w-sm leading-relaxed font-medium">
          Create a new research vault or screen papers using the academic search engine above.
        </p>
      </div>
    );
  }

  if (viewMode === "list") {
    return (
      <div className="flex flex-col gap-3">
        {notebooks.map((nb) => {
          const dateStr = new Date(nb.updatedAt).toLocaleDateString("en-US", {
            month: "short",
            day: "numeric",
            year: "numeric",
          });

          return (
            <div
              key={nb.id}
              onClick={() => onSelectNotebook(nb)}
              className="fernly-card group flex items-center justify-between p-4 sm:p-5 rounded-2xl cursor-pointer gap-3"
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <span className="text-2xl p-2.5 rounded-[14px] bg-[var(--panel)] border border-[var(--hair)] group-hover:scale-105 transition-transform flex-shrink-0 shadow-xs">
                  {nb.emoji}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-[var(--ink)] group-hover:text-[var(--g-700)] truncate transition-colors tracking-tight">
                      {nb.title}
                    </h3>
                    {nb.category && (
                      <span className="text-[10px] text-[var(--muted)] bg-[var(--panel)] border border-[var(--hair)] px-2.5 py-0.5 rounded-full font-semibold hidden sm:inline">
                        {nb.category}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-[var(--muted)] truncate mt-0.5 font-normal tracking-tight">
                    {nb.description || "Systematic literature review & verbatim evidence pool"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 sm:gap-4 flex-shrink-0 text-xs text-[var(--muted)]">
                <span className="fernly-badge badge-done text-[11px]">
                  {nb.sourcesCount} {nb.sourcesCount === 1 ? "source" : "sources"}
                </span>
                <span className="hidden md:inline font-medium text-[var(--faint)]">{dateStr}</span>
                <button
                  onClick={(e) => handleDelete(e, nb.id, nb.title)}
                  className="p-1.5 text-[var(--faint)] hover:text-red-600 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
                  title="Delete project"
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </div>
          );
        })}
      </div>
    );
  }

  // Grid Mode (Fernly Bento Cards)
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-4">
      {notebooks.map((nb) => {
        const dateStr = new Date(nb.updatedAt).toLocaleDateString("en-US", {
          month: "short",
          day: "numeric",
          year: "numeric",
        });

        const isMenuOpen = activeMenuId === nb.id;

        return (
          <div
            key={nb.id}
            onClick={() => onSelectNotebook(nb)}
            className="fernly-card group relative min-h-[220px] p-5 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            {/* Top row: Emoji Icon & Delete / Context menu */}
            <div className="flex items-start justify-between">
              <span className="text-2xl p-2.5 rounded-[14px] bg-[var(--panel)] border border-[var(--hair)] shadow-xs group-hover:scale-105 transition-transform flex items-center justify-center">
                {nb.emoji}
              </span>

              <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                <div className="relative">
                  <button
                    onClick={() => setActiveMenuId(isMenuOpen ? null : nb.id)}
                    className="p-1.5 rounded-full text-[var(--faint)] hover:text-[var(--ink)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
                    title="Project actions"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>

                  {isMenuOpen && (
                    <div className="absolute right-0 top-7 w-36 py-1 bg-[var(--card)] border border-[var(--hair)] rounded-2xl shadow-xl z-30 text-xs">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectNotebook(nb);
                        }}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-[var(--ink)] hover:bg-[var(--g-100)] text-left cursor-pointer font-medium"
                      >
                        <ArrowUpRight className="h-3.5 w-3.5 text-[var(--g-700)]" /> Open Studio
                      </button>
                      <button
                        onClick={(e) => handleDelete(e, nb.id, nb.title)}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 text-left cursor-pointer font-medium"
                      >
                        <Trash2 className="h-3.5 w-3.5" /> Delete
                      </button>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Bottom row: Title & Date / Source Count */}
            <div className="mt-4">
              {nb.category && (
                <span className="text-[10px] text-[var(--g-800)] bg-[var(--g-100)] border border-[var(--g-400)]/30 px-2 py-0.5 rounded-full inline-block font-semibold mb-1.5 truncate max-w-full">
                  {nb.category}
                </span>
              )}
              <h3 className="text-xs sm:text-sm font-semibold text-[var(--ink)] line-clamp-2 group-hover:text-[var(--g-700)] transition-colors leading-snug tracking-tight">
                {nb.title}
              </h3>
              <div className="text-[11px] text-[var(--muted)] mt-3 flex items-center justify-between pt-2.5 border-t border-[var(--hair)]">
                <span className="font-medium">{dateStr}</span>
                <span className="fernly-badge badge-done text-[10px]">
                  {nb.sourcesCount} {nb.sourcesCount === 1 ? "source" : "sources"}
                </span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}
