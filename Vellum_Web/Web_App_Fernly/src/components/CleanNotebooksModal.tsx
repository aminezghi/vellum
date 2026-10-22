"use client";

import React, { useState } from "react";
import { db } from "@/lib/db";
import { AlertTriangle, Trash2, X } from "lucide-react";

interface CleanNotebooksModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCleaned: () => void;
  totalNotebooks: number;
}

export function CleanNotebooksModal({
  isOpen,
  onClose,
  onCleaned,
  totalNotebooks,
}: CleanNotebooksModalProps) {
  const [cleaning, setCleaning] = useState(false);
  const [cleanMode, setCleanMode] = useState<"all" | "empty">("all");
  const [confirmText, setConfirmText] = useState("");

  if (!isOpen) return null;

  const handleExecuteClean = async () => {
    setCleaning(true);
    try {
      if (cleanMode === "all") {
        await db.notebooks.clear();
        await db.sources.clear();
        await db.notes.clear();
      } else {
        const emptyNbs = await db.notebooks.filter((nb) => !nb.sourcesCount || nb.sourcesCount === 0).toArray();
        for (const nb of emptyNbs) {
          await db.notebooks.delete(nb.id);
          await db.notes.where("notebookId").equals(nb.id).delete();
        }
      }
      onCleaned();
      onClose();
    } catch (err) {
      console.error("Failed to clean notebooks:", err);
      alert("Error cleaning notebooks from database.");
    } finally {
      setCleaning(false);
    }
  };

  const isConfirmed = cleanMode === "empty" || confirmText.toLowerCase() === "delete";

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="fernly-card relative w-full max-w-md p-6 sm:p-7 space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--rose-bg)] text-[var(--rose)] border border-[var(--rose)]/30">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[var(--ink)] tracking-tight">
                Clean Research Workspace
              </h3>
              <p className="text-xs text-[var(--muted)] font-medium">
                Manage and reset local IndexedDB storage
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-full text-[var(--faint)] hover:text-[var(--ink)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Clean Mode Selector */}
        <div className="space-y-2.5">
          <label className="text-xs font-semibold text-[var(--muted)]">
            Select Cleaning Scope:
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => setCleanMode("all")}
              className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                cleanMode === "all"
                  ? "bg-[var(--rose-bg)] border-[var(--rose)]/40 text-[var(--rose)] font-semibold shadow-xs"
                  : "bg-[var(--panel)] border-[var(--hair)] text-[var(--muted)] hover:bg-[var(--card)]"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span>Wipe All ({totalNotebooks})</span>
                <Trash2 className="h-3.5 w-3.5 text-[var(--rose)]" />
              </div>
              <p className="text-[10px] text-[var(--faint)] font-normal">
                Reset entire local database to fresh state.
              </p>
            </button>

            <button
              type="button"
              onClick={() => setCleanMode("empty")}
              className={`p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                cleanMode === "empty"
                  ? "bg-[var(--g-100)] border-[var(--g-600)] text-[var(--g-800)] font-semibold shadow-xs"
                  : "bg-[var(--panel)] border-[var(--hair)] text-[var(--muted)] hover:bg-[var(--card)]"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span>Empty Vaults Only</span>
                <Trash2 className="h-3.5 w-3.5 text-[var(--g-700)]" />
              </div>
              <p className="text-[10px] text-[var(--faint)] font-normal">
                Prune projects with 0 saved papers.
              </p>
            </button>
          </div>
        </div>

        {/* Confirmation Input for "Wipe All" */}
        {cleanMode === "all" && (
          <div className="space-y-1.5 p-3.5 rounded-2xl bg-[var(--rose-bg)] border border-[var(--rose)]/30">
            <label className="text-xs font-semibold text-[var(--rose)] flex items-center justify-between">
              <span>Type "delete" to confirm:</span>
              <span className="text-[10px] font-normal text-[var(--rose)]/80">Irreversible local action</span>
            </label>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder="delete"
              className="fernly-input w-full bg-[var(--card)] !border-[var(--rose)]/30 focus:!border-[var(--rose)]"
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-[var(--hair)]">
          <button
            type="button"
            onClick={onClose}
            className="btn-fernly-ghost !h-10 !px-4 !text-xs"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleExecuteClean}
            disabled={!isConfirmed || cleaning}
            className="px-5 py-2.5 rounded-full bg-[var(--rose)] text-white hover:opacity-90 text-xs font-semibold disabled:opacity-40 transition-all cursor-pointer shadow-xs"
          >
            {cleaning ? "Purging..." : "Confirm & Clean"}
          </button>
        </div>
      </div>
    </div>
  );
}
