"use client";

import React, { useState } from "react";
import { db, Notebook, Source } from "@/lib/db";
import { AcademicPaperResult } from "@/app/api/search/route";
import { X, Plus, CheckCircle2, BookmarkPlus, ArrowRight } from "lucide-react";

interface AddToNotebookModalProps {
  paper: AcademicPaperResult | null;
  notebooks: Notebook[];
  isOpen: boolean;
  onClose: () => void;
  onAdded: (notebookId: string) => void;
}

export function AddToNotebookModal({
  paper,
  notebooks,
  isOpen,
  onClose,
  onAdded,
}: AddToNotebookModalProps) {
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>(
    notebooks.length > 0 ? notebooks[0].id : ""
  );
  const [isCreatingNew, setIsCreatingNew] = useState(notebooks.length === 0);
  const [newTitle, setNewTitle] = useState(paper ? `${paper.title.slice(0, 45)} Review` : "");
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  if (!isOpen || !paper) return null;

  const handleSave = async () => {
    setIsSaving(true);
    let targetNotebookId = selectedNotebookId;

    if (isCreatingNew) {
      if (!newTitle.trim()) return;
      const newNb: Notebook = {
        id: `nb-${Date.now()}`,
        title: newTitle.trim(),
        emoji: "📚",
        description: `Created from academic search for "${paper.title.slice(0, 40)}..."`,
        createdAt: Date.now(),
        updatedAt: Date.now(),
        sourcesCount: 1,
        category: "Literature Review",
        isFeatured: false,
      };
      await db.notebooks.put(newNb);
      targetNotebookId = newNb.id;
    }

    if (!targetNotebookId) {
      setIsSaving(false);
      return;
    }

    // Add source to IndexedDB
    const newSource: Source = {
      id: `src-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      notebookId: targetNotebookId,
      title: paper.title,
      authors: paper.authors,
      year: paper.year,
      journal: paper.venue,
      doi: paper.doi,
      status: "ready",
      addedAt: Date.now(),
    };

    await db.sources.put(newSource);

    // Update notebook counts
    const count = await db.sources.where("notebookId").equals(targetNotebookId).count();
    await db.notebooks.update(targetNotebookId, {
      sourcesCount: count,
      updatedAt: Date.now(),
    });

    setIsSaving(false);
    setSuccess(true);
    setTimeout(() => {
      setSuccess(false);
      onAdded(targetNotebookId);
      onClose();
    }, 1000);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-md rounded-[2rem] bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 p-6 shadow-2xl relative text-[#1a1a1a] dark:text-[#ffffeb]">
        <button
          onClick={onClose}
          className="absolute right-5 top-5 p-2 rounded-full text-[#1a1a1a]/50 dark:text-white/40 hover:text-[#1a1a1a] dark:hover:text-white hover:bg-[#1a1a1a]/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2.5 mb-4">
          <div className="p-2.5 rounded-2xl bg-[#cef5ca] dark:bg-[#034f46] text-[#114e0b] dark:text-[#cef5ca] border border-[#cef5ca] dark:border-transparent">
            <BookmarkPlus className="h-4 w-4" />
          </div>
          <div>
            <h2 className="text-base font-semibold tracking-tight text-[#1a1a1a] dark:text-white">Add to Notebook</h2>
            <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60">Save to your local systematic review corpus</p>
          </div>
        </div>

        {/* Paper Summary Pill */}
        <div className="p-3.5 rounded-2xl bg-[#ffffeb] dark:bg-[#121413] border border-[#1a1a1a]/8 dark:border-white/10 mb-4">
          <p className="text-xs font-medium text-[#1a1a1a] dark:text-white line-clamp-2 leading-snug">{paper.title}</p>
          <p className="text-[11px] text-[#1a1a1a]/60 dark:text-white/60 mt-1">
            {paper.authors?.[0] || "Author"} · {paper.year} · {paper.venue}
          </p>
        </div>

        {success ? (
          <div className="py-8 flex flex-col items-center justify-center text-center space-y-2">
            <CheckCircle2 className="h-10 w-10 text-[#034f46] animate-bounce" />
            <span className="text-sm font-semibold text-[#1a1a1a]">Paper Added to Notebook!</span>
            <span className="text-xs text-[#1a1a1a]/60">Opening workspace...</span>
          </div>
        ) : (
          <div className="space-y-4">
            {!isCreatingNew ? (
              <div>
                <label className="block text-xs font-semibold text-[#1a1a1a]/80 mb-2">Select Target Notebook</label>
                <div className="space-y-1.5 max-h-48 overflow-y-auto pr-1">
                  {notebooks.map((nb) => {
                    const isSelected = selectedNotebookId === nb.id;
                    return (
                      <div
                        key={nb.id}
                        onClick={() => setSelectedNotebookId(nb.id)}
                        className={`p-3 rounded-2xl border transition-all cursor-pointer flex items-center justify-between ${
                          isSelected
                            ? "bg-[#cef5ca]/40 border-[#034f46]/40 text-[#1a1a1a]"
                            : "bg-[#ffffeb]/60 border-[#1a1a1a]/8 hover:bg-[#ffffeb] text-[#1a1a1a]/80"
                        }`}
                      >
                        <div className="flex items-center gap-2.5 truncate">
                          <span className="text-lg">{nb.emoji}</span>
                          <div className="truncate">
                            <p className="text-xs font-medium truncate">{nb.title}</p>
                            <p className="text-[10px] text-[#1a1a1a]/50">{nb.sourcesCount || 0} papers</p>
                          </div>
                        </div>
                        {isSelected && <CheckCircle2 className="h-4 w-4 text-[#034f46] flex-shrink-0" />}
                      </div>
                    );
                  })}
                </div>

                <button
                  type="button"
                  onClick={() => setIsCreatingNew(true)}
                  className="w-full mt-2.5 flex items-center justify-center gap-1.5 py-2.5 rounded-full border border-dashed border-[#1a1a1a]/20 hover:border-[#034f46] text-xs font-medium text-[#1a1a1a]/70 hover:text-[#034f46] transition-colors cursor-pointer"
                >
                  <Plus className="h-3.5 w-3.5" />
                  <span>Create a New Notebook</span>
                </button>
              </div>
            ) : (
              <div>
                <label className="block text-xs font-semibold text-[#1a1a1a]/80 mb-1.5">New Notebook Title</label>
                <input
                  type="text"
                  autoFocus
                  value={newTitle}
                  onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Meta-analysis on CRISPR Oncology"
                  className="w-full bg-[#f8f9fa] border border-[#1a1a1a]/15 rounded-full px-4 py-2.5 text-xs text-[#1a1a1a] placeholder-[#1a1a1a]/40 focus:outline-none focus:bg-white focus:border-[#034f46] focus:ring-1 focus:ring-[#034f46]/20"
                />
                <button
                  type="button"
                  onClick={() => setIsCreatingNew(false)}
                  className="text-[11px] text-[#034f46] font-medium hover:underline mt-2 inline-block cursor-pointer"
                >
                  ← Pick from existing notebooks
                </button>
              </div>
            )}

            <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1a1a1a]/8">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-full text-xs font-semibold text-[#1a1a1a]/70 hover:text-[#1a1a1a] hover:bg-[#1a1a1a]/5 transition-colors cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                disabled={isSaving || (!selectedNotebookId && !newTitle.trim())}
                onClick={handleSave}
                className="flex items-center gap-1.5 px-5 py-2.5 rounded-full text-xs font-semibold bg-[#034f46] hover:bg-[#034f46]/90 text-[#ffffeb] shadow-sm shadow-[#034f46]/20 disabled:opacity-40 transition-all cursor-pointer"
              >
                <span>{isSaving ? "Saving..." : "Add to Notebook"}</span>
                <ArrowRight className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
