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
    if (confirm(`Delete notebook "${title || id}" and all its saved evidence sources?`)) {
      await db.notebooks.delete(id);
      await db.sources.where("notebookId").equals(id).delete();
      await db.notes.where("notebookId").equals(id).delete();
      onRefresh();
    }
    setActiveMenuId(null);
  };

  if (notebooks.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-14 text-center border border-dashed border-[#1a1a1a]/20 dark:border-white/20 rounded-[2rem] bg-white/50 dark:bg-white/5 backdrop-blur-sm">
        <div className="relative mb-4 flex h-14 w-14 items-center justify-center rounded-2xl bg-[#ffffeb] dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 text-[#1a1a1a]/60 dark:text-white/60 shadow-sm">
          <BookOpen className="h-6 w-6 text-[#034f46] dark:text-[#cef5ca]" />
          <div className="absolute -bottom-1 -right-1 flex h-5 w-5 items-center justify-center rounded-md bg-[#034f46] text-[#ffffeb] shadow-sm">
            <Layers className="h-3 w-3" />
          </div>
        </div>
        <h3 className="text-sm font-semibold text-[#1a1a1a] dark:text-white">No notebooks match this view</h3>
        <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-1.5 max-w-sm leading-relaxed font-medium">
          Create a new research notebook or screen papers using the academic search hub above.
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
              className="apple-card apple-press group flex items-center justify-between p-4 sm:p-5 rounded-2xl cursor-pointer gap-3"
            >
              <div className="flex items-center gap-3.5 min-w-0">
                <span className="text-2xl p-2.5 rounded-[14px] bg-black/5 dark:bg-white/10 border border-black/5 dark:border-white/10 group-hover:scale-105 transition-transform flex-shrink-0 shadow-xs">
                  {nb.emoji}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-semibold text-neutral-900 dark:text-neutral-100 group-hover:text-[#0071e3] dark:group-hover:text-[#0a84ff] truncate transition-colors tracking-tight">
                      {nb.title}
                    </h3>
                    {nb.category && (
                      <span className="text-[10px] text-neutral-600 dark:text-neutral-300 bg-black/5 dark:bg-white/10 border border-black/5 dark:border-white/10 px-2.5 py-0.5 rounded-full font-semibold hidden sm:inline">
                        {nb.category}
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-neutral-500 dark:text-neutral-400 truncate mt-0.5 font-normal tracking-tight">
                    {nb.description || "Systematic literature review & verbatim evidence pool"}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-3 sm:gap-4 flex-shrink-0 text-xs text-neutral-500 dark:text-neutral-400">
                <span className="px-3 py-1 rounded-full bg-[#0071e3]/10 dark:bg-[#0a84ff]/20 text-[#0071e3] dark:text-[#64b5ff] border border-[#0071e3]/20 text-[11px] font-semibold">
                  {nb.sourcesCount} {nb.sourcesCount === 1 ? "source" : "sources"}
                </span>
                <span className="hidden md:inline font-medium text-neutral-400">{dateStr}</span>
                <button
                  onClick={(e) => handleDelete(e, nb.id, nb.title)}
                  className="apple-press p-1.5 text-neutral-400 hover:text-red-600 dark:hover:text-red-400 rounded-lg hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
                  title="Delete notebook"
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

  // Grid Mode (Apple Elevated Squircle Cards)
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
            className="apple-card apple-press group relative min-h-[220px] rounded-[1.5rem] p-5 cursor-pointer flex flex-col justify-between overflow-hidden"
          >
            {/* Top row: Emoji Icon & Delete / Context menu */}
            <div className="flex items-start justify-between">
              <span className="text-2xl p-2.5 rounded-[14px] bg-black/5 dark:bg-white/10 border border-black/5 dark:border-white/10 shadow-xs group-hover:scale-105 transition-transform flex items-center justify-center">
                {nb.emoji}
              </span>

              <div className="flex items-center gap-1" onClick={(e) => e.stopPropagation()}>
                {/* Direct quick delete icon on hover */}
                <button
                  onClick={(e) => handleDelete(e, nb.id, nb.title)}
                  className="apple-press p-1.5 rounded-full text-neutral-400 hover:text-red-600 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer"
                  title="Delete notebook"
                >
                  <Trash2 className="h-3.5 w-3.5" />
                </button>

                <div className="relative">
                  <button
                    onClick={() => setActiveMenuId(isMenuOpen ? null : nb.id)}
                    className="p-1.5 rounded-full text-[#1a1a1a]/40 dark:text-white/40 hover:text-[#1a1a1a] dark:hover:text-white hover:bg-[#1a1a1a]/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
                  >
                    <MoreVertical className="h-4 w-4" />
                  </button>

                  {isMenuOpen && (
                    <div className="absolute right-0 top-7 w-36 py-1 bg-white dark:bg-[#121413] border border-[#1a1a1a]/15 dark:border-white/15 rounded-2xl shadow-xl z-30 text-xs">
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          onSelectNotebook(nb);
                        }}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-[#1a1a1a] dark:text-white hover:bg-[#ffffeb] dark:hover:bg-white/5 text-left cursor-pointer font-medium"
                      >
                        <ArrowUpRight className="h-3.5 w-3.5 text-[#034f46] dark:text-[#cef5ca]" /> Open Studio
                      </button>
                      <button
                        onClick={(e) => handleDelete(e, nb.id, nb.title)}
                        className="w-full flex items-center gap-2 px-3 py-1.5 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 text-left cursor-pointer font-medium"
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
                <span className="text-[10px] text-[#034f46] dark:text-[#cef5ca] bg-[#ffffeb] dark:bg-white/5 border border-[#034f46]/15 dark:border-white/10 px-2 py-0.5 rounded-full inline-block font-semibold mb-1.5 truncate max-w-full">
                  {nb.category}
                </span>
              )}
              <h3 className="text-xs sm:text-sm font-semibold text-[#1a1a1a] dark:text-white line-clamp-2 group-hover:text-[#034f46] dark:group-hover:text-[#cef5ca] transition-colors leading-snug tracking-tight">
                {nb.title}
              </h3>
              <div className="text-[11px] text-[#1a1a1a]/55 dark:text-white/50 mt-3 flex items-center justify-between pt-2.5 border-t border-[#1a1a1a]/8 dark:border-white/10">
                <span className="font-medium">{dateStr}</span>
                <span className="font-semibold text-[#114e0b] dark:text-[#cef5ca] bg-[#cef5ca] dark:bg-[#034f46] px-2.5 py-0.5 rounded-full text-[10px] border border-[#114e0b]/15">
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
