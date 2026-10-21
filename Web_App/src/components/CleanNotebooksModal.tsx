"use client";

import React, { useState } from "react";
import { db } from "@/lib/db";
import { AlertTriangle, Trash2, X, ShieldAlert, CheckCircle2 } from "lucide-react";

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
        // Clean only empty notebooks (0 sources)
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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-2xl animate-in fade-in duration-200">
      <div className="apple-glass relative w-full max-w-md rounded-[2rem] bg-white/90 dark:bg-[#1c1c1e]/90 border border-black/10 dark:border-white/15 p-6 sm:p-7 shadow-2xl space-y-5">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#ff3b30]/15 text-[#ff3b30] dark:text-[#ff453a]">
              <AlertTriangle className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#1a1a1a] dark:text-white tracking-tight">
                Clean Research Workspace
              </h3>
              <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 font-medium">
                Manage and reset local IndexedDB storage
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="apple-press p-1.5 rounded-full text-[#1a1a1a]/40 dark:text-white/40 hover:text-[#1a1a1a] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Clean Mode Selector */}
        <div className="space-y-2.5">
          <label className="text-xs font-semibold text-[#1a1a1a]/80 dark:text-white/80">
            Select Cleaning Scope:
          </label>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
            <button
              type="button"
              onClick={() => setCleanMode("all")}
              className={`apple-press p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                cleanMode === "all"
                  ? "bg-[#ff3b30]/10 border-[#ff3b30]/40 text-[#ff3b30] dark:text-[#ff453a] font-semibold shadow-xs"
                  : "bg-black/5 dark:bg-white/5 border-black/10 dark:border-white/10 text-[#1a1a1a]/70 dark:text-white/70 hover:bg-black/10 dark:hover:bg-white/10"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span>Wipe All ({totalNotebooks})</span>
                <Trash2 className="h-3.5 w-3.5 text-[#ff3b30] dark:text-[#ff453a]" />
              </div>
              <p className="text-[10px] text-[#1a1a1a]/60 dark:text-white/50 font-normal">
                Reset entire local database to fresh state.
              </p>
            </button>

            <button
              type="button"
              onClick={() => setCleanMode("empty")}
              className={`apple-press p-3 rounded-2xl border text-left transition-all cursor-pointer ${
                cleanMode === "empty"
                  ? "bg-[#34c759]/15 border-[#34c759]/40 text-[#248a3d] dark:text-[#30d158] font-semibold shadow-xs"
                  : "bg-black/5 dark:bg-white/5 border-black/10 dark:border-white/10 text-[#1a1a1a]/70 dark:text-white/70 hover:bg-black/10 dark:hover:bg-white/10"
              }`}
            >
              <div className="flex items-center justify-between mb-1">
                <span>Clean Empty Only</span>
                <CheckCircle2 className="h-3.5 w-3.5 text-[#248a3d] dark:text-[#30d158]" />
              </div>
              <p className="text-[10px] text-[#1a1a1a]/60 dark:text-white/50 font-normal">
                Keep notebooks with papers; purge unused ones.
              </p>
            </button>
          </div>
        </div>

        {/* Confirmation Input for Complete Wipe */}
        {cleanMode === "all" && (
          <div className="space-y-2 p-3.5 rounded-2xl bg-[#ff3b30]/10 border border-[#ff3b30]/30">
            <p className="text-xs text-[#ff3b30] dark:text-[#ff453a] font-medium">
              Type <strong className="font-bold underline">delete</strong> below to confirm wiping all {totalNotebooks} notebooks, sources, and synthesis notes:
            </p>
            <input
              type="text"
              value={confirmText}
              onChange={(e) => setConfirmText(e.target.value)}
              placeholder='Type "delete" to confirm'
              className="w-full px-3 py-2 text-xs rounded-xl bg-white dark:bg-[#121413] border border-[#ff3b30]/40 text-[#1a1a1a] dark:text-white placeholder-[#ff3b30]/50 focus:outline-none focus:ring-2 focus:ring-[#ff3b30]/30 font-mono"
            />
          </div>
        )}

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-2.5 pt-2 border-t border-black/8 dark:border-white/10">
          <button
            type="button"
            onClick={onClose}
            className="apple-press px-4 py-2 rounded-full border border-black/15 dark:border-white/15 text-xs font-medium text-[#1a1a1a] dark:text-white hover:bg-black/5 dark:hover:bg-white/5 transition-colors cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!isConfirmed || cleaning}
            onClick={handleExecuteClean}
            className="apple-press flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#ff3b30] hover:bg-[#e0352b] text-white text-xs font-semibold shadow-xs disabled:opacity-40 transition-all cursor-pointer"
          >
            <Trash2 className="h-3.5 w-3.5" />
            <span>{cleaning ? "Cleaning..." : cleanMode === "all" ? "Wipe All Notebooks" : "Clean Empty Notebooks"}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
