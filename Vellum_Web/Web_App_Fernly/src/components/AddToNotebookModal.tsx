"use client";

import React, { useState } from "react";
import { db, Notebook, Source } from "@/lib/db";
import { AcademicPaperResult } from "@/app/api/search/route";
import { X, Plus, CheckCircle2, BookmarkPlus } from "lucide-react";

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
      <div className="fernly-card relative w-full max-w-md p-6 sm:p-7 space-y-4">
        <button
          onClick={onClose}
          className="absolute right-5 top-5 p-2 rounded-full text-[var(--faint)] hover:text-[var(--ink)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2.5 mb-2">
          <div className="p-2.5 rounded-2xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30">
            <BookmarkPlus className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-base font-bold text-[var(--ink)] tracking-tight">Save to Research Project</h2>
            <p className="text-xs text-[var(--muted)]">Add reference &amp; verbatim evidence to local vault</p>
          </div>
        </div>

        {/* Paper Mini Preview Card */}
        <div className="p-3.5 rounded-2xl bg-[var(--panel)] border border-[var(--hair)] space-y-1">
          <h4 className="text-xs font-semibold text-[var(--ink)] line-clamp-2 leading-snug">
            {paper.title}
          </h4>
          <p className="text-[11px] text-[var(--muted)]">
            {paper.authors?.[0] || "Author"} · {paper.year || 2024} · {paper.venue || "Academic Source"}
          </p>
        </div>

        {/* Existing vs New Toggle */}
        <div className="space-y-3 pt-1">
          {notebooks.length > 0 && (
            <div className="flex items-center bg-[var(--panel)] p-1 rounded-full border border-[var(--hair)]">
              <button
                type="button"
                onClick={() => setIsCreatingNew(false)}
                className={`flex-1 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  !isCreatingNew
                    ? "bg-[var(--card)] text-[var(--g-800)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--ink)]"
                }`}
              >
                Existing Vault ({notebooks.length})
              </button>
              <button
                type="button"
                onClick={() => setIsCreatingNew(true)}
                className={`flex-1 py-1.5 rounded-full text-xs font-semibold transition-all cursor-pointer ${
                  isCreatingNew
                    ? "bg-[var(--card)] text-[var(--g-800)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--ink)]"
                }`}
              >
                + New Project
              </button>
            </div>
          )}

          {!isCreatingNew && notebooks.length > 0 ? (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--muted)]">Choose Destination Project:</label>
              <select
                value={selectedNotebookId}
                onChange={(e) => setSelectedNotebookId(e.target.value)}
                className="fernly-input w-full cursor-pointer"
              >
                {notebooks.map((nb) => (
                  <option key={nb.id} value={nb.id}>
                    {nb.emoji} {nb.title} ({nb.sourcesCount || 0} papers)
                  </option>
                ))}
              </select>
            </div>
          ) : (
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-[var(--muted)]">New Project Title:</label>
              <input
                type="text"
                value={newTitle}
                onChange={(e) => setNewTitle(e.target.value)}
                placeholder="e.g. Cognitive Biases Literature Review"
                className="fernly-input w-full"
              />
            </div>
          )}
        </div>

        {/* Status or Submit Button */}
        <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[var(--hair)]">
          <button
            type="button"
            onClick={onClose}
            className="btn-fernly-ghost !h-10 !px-4 !text-xs"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={isSaving || success}
            className="btn-fernly-primary !h-10 !px-5 !text-xs flex items-center gap-1.5"
          >
            {success ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-[#5dbd8b]" />
                <span>Saved!</span>
              </>
            ) : isSaving ? (
              <span>Saving...</span>
            ) : (
              <span>Add to Project</span>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
