"use client";

import React, { useState } from "react";
import { db, Notebook, Source } from "@/lib/db";
import { AddablePaper } from "@/lib/paper";
import { CheckCircle2, BookmarkPlus } from "lucide-react";
import { Modal } from "@/components/Modal";

interface AddToNotebookModalProps {
  paper: AddablePaper | null;
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
  // The dialog is mounted only while it is open, so its fields are seeded from
  // the current paper and notebook list on every open. This component used to
  // stay mounted for the app's lifetime, which meant its initialisers captured
  // the props of the very first render — when `paper` was still null. The new
  // project title therefore came up empty instead of prefilled, and the
  // destination notebook could point at a project created after mount.
  if (!isOpen || !paper) return null;
  return (
    <AddToNotebookDialog
      paper={paper}
      notebooks={notebooks}
      onClose={onClose}
      onAdded={onAdded}
    />
  );
}

interface AddToNotebookDialogProps {
  paper: AddablePaper;
  notebooks: Notebook[];
  onClose: () => void;
  onAdded: (notebookId: string) => void;
}

function AddToNotebookDialog({
  paper,
  notebooks,
  onClose,
  onAdded,
}: AddToNotebookDialogProps) {
  const [selectedNotebookId, setSelectedNotebookId] = useState<string>(
    () => notebooks[0]?.id ?? ""
  );
  const [isCreatingNew, setIsCreatingNew] = useState(() => notebooks.length === 0);
  const [newTitle, setNewTitle] = useState(() => `${paper.title.slice(0, 45)} Review`);
  const [isSaving, setIsSaving] = useState(false);
  const [success, setSuccess] = useState(false);

  const canSave = !isCreatingNew || newTitle.trim().length > 0;

  const handleSave = async () => {
    // Check before flipping `isSaving`, otherwise an empty title leaves the
    // button stuck on "Saving..." forever with the dialog open.
    if (!canSave) return;
    setIsSaving(true);
    let targetNotebookId = selectedNotebookId;

    if (isCreatingNew) {
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

    const newSource: Source = {
      id: `src-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
      notebookId: targetNotebookId,
      title: paper.title,
      authors: paper.authors,
      year: paper.year,
      journal: paper.venue ?? paper.journal,
      doi: paper.doi,
      abstract: paper.abstract,
      status: "ready",
      addedAt: Date.now(),
    };

    await db.sources.put(newSource);

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
    }, 450);
  };

  return (
    <Modal
      isOpen={true}
      onClose={onClose}
      title="Save to Research Project"
      subtitle="Add reference & verbatim evidence to local vault"
      icon={<BookmarkPlus className="h-5 w-5" />}
      panelClassName="max-w-md space-y-4"
    >
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
            <div
              className="flex items-center bg-[var(--panel)] p-1 rounded-full border border-[var(--hair)]"
              role="radiogroup"
              aria-label="Destination"
            >
              <button
                type="button"
                role="radio"
                aria-checked={!isCreatingNew}
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
                role="radio"
                aria-checked={isCreatingNew}
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
              <label htmlFor="addto-existing" className="text-xs font-semibold text-[var(--muted)]">
                Choose Destination Project:
              </label>
              <select
                id="addto-existing"
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
              <label htmlFor="addto-new" className="text-xs font-semibold text-[var(--muted)]">
                New Project Title:
              </label>
              <input
                id="addto-new"
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
            disabled={isSaving || success || !canSave}
            className="btn-fernly-primary !h-10 !px-5 !text-xs flex items-center gap-1.5"
          >
            {success ? (
              <>
                <CheckCircle2 className="h-4 w-4 text-[#5dbd8b]" aria-hidden="true" />
                <span>Saved!</span>
              </>
            ) : isSaving ? (
              <span>Saving...</span>
            ) : (
              <span>Add to Project</span>
            )}
          </button>
        </div>
    </Modal>
  );
}
