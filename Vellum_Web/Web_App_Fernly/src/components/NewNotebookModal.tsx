"use client";

import React, { useState } from "react";
import { db, Notebook } from "@/lib/db";
import { Sparkles, Upload } from "lucide-react";
import { Modal } from "@/components/Modal";

interface NewNotebookModalProps {
  isOpen: boolean;
  onClose: () => void;
  onCreated: (notebook: Notebook) => void;
}

const EMOJI_OPTIONS = ["📚", "🔬", "🛒", "🌾", "🧠", "📈", "🧬", "🥗", "🦠", "💊", "🏛️", "🌍"];

export function NewNotebookModal({ isOpen, onClose, onCreated }: NewNotebookModalProps) {
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [selectedEmoji, setSelectedEmoji] = useState("📚");
  const [category, setCategory] = useState("General");
  const [files, setFiles] = useState<File[]>([]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  if (!isOpen) return null;

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files) {
      setFiles(Array.from(e.target.files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;

    setIsSubmitting(true);
    const newId = `nb-${Date.now()}`;
    const newNotebook: Notebook = {
      id: newId,
      title: title.trim(),
      emoji: selectedEmoji,
      description: description.trim(),
      createdAt: Date.now(),
      updatedAt: Date.now(),
      sourcesCount: files.length,
      category: category,
      isFeatured: false,
    };

    await db.notebooks.put(newNotebook);

    // Save initial files if provided
    for (const f of files) {
      const cleanTitle = f.name
        .replace(/\.pdf$/i, "")
        .replace(/^[a-zA-Z0-9_\-]+ - \d{4} - /, "")
        .replace(/_/g, " ");

      await db.sources.put({
        id: `src-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        notebookId: newId,
        title: cleanTitle,
        authors: [f.name.includes(" - ") ? f.name.split(" - ")[0] : "Author"],
        year: parseInt((f.name.match(/\b(19|20)\d{2}\b/) || ["2024"])[0], 10),
        pdfBlob: f,
        sizeBytes: f.size,
        status: "ready",
        addedAt: Date.now(),
      });
    }

    setIsSubmitting(false);
    onCreated(newNotebook);
    onClose();
  };

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title="Create Research Project Vault"
      subtitle="Initialize a dedicated systematic review corpus"
      icon={<Sparkles className="h-5 w-5" />}
    >
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Emoji & Title */}
        <div>
          <label htmlFor="nb-title" className="block text-xs font-semibold text-[var(--muted)] mb-1.5">
            Project Icon &amp; Title
          </label>
          <div className="flex items-center gap-2">
            <div
              className="flex gap-1 overflow-x-auto pb-1 max-w-[170px] no-scrollbar"
              role="radiogroup"
              aria-label="Project icon"
            >
              {EMOJI_OPTIONS.map((em) => (
                <button
                  type="button"
                  key={em}
                  role="radio"
                  aria-checked={selectedEmoji === em}
                  aria-label={`Use ${em} as the project icon`}
                  onClick={() => setSelectedEmoji(em)}
                  className={`h-9 w-9 flex-shrink-0 flex items-center justify-center rounded-xl text-base transition-all cursor-pointer ${
                    selectedEmoji === em
                      ? "bg-[var(--g-100)] border-2 border-[var(--g-700)] scale-105"
                      : "bg-[var(--panel)] border border-[var(--hair)] hover:bg-[var(--card)]"
                  }`}
                >
                  {em}
                </button>
              ))}
            </div>
            <input
              id="nb-title"
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="e.g. Cognitive Biases in Consumer Choice"
              className="fernly-input flex-1"
            />
          </div>
        </div>

        {/* Description */}
        <div>
          <label htmlFor="nb-desc" className="block text-xs font-semibold text-[var(--muted)] mb-1.5">
            Description &amp; Research Scope
          </label>
          <textarea
            id="nb-desc"
            rows={2}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="e.g. Exploring heuristics, framing effects, and purchase decisions across retail formats..."
            className="fernly-input w-full resize-none"
          />
        </div>

          {/* Category */}
          <div>
            <label htmlFor="nb-category" className="block text-xs font-semibold text-[var(--muted)] mb-1.5">
              Discipline / Category
            </label>
            <input
              id="nb-category"
              type="text"
              value={category}
              onChange={(e) => setCategory(e.target.value)}
              placeholder="e.g. Quantitative Economics, Biomedicine, AI"
              className="fernly-input w-full"
            />
          </div>

          {/* Initial PDF Files Upload */}
          <div>
            <label
              htmlFor="nb-files"
              className="block text-xs font-semibold text-[var(--muted)] mb-1.5"
            >
              Initial Paper PDFs (Optional)
            </label>
            <label
              htmlFor="nb-files"
              className="flex flex-col items-center justify-center p-5 border-2 border-dashed border-[var(--hair)] hover:border-[var(--g-400)] rounded-2xl bg-[var(--panel)] cursor-pointer transition-colors"
            >
              <Upload className="h-6 w-6 text-[var(--g-700)] mb-1.5" aria-hidden="true" />
              <span className="text-xs font-semibold text-[var(--ink)]">
                {files.length > 0 ? `${files.length} paper(s) selected` : "Drop PDF files or browse"}
              </span>
              <span className="text-[11px] text-[var(--faint)] mt-0.5">Will be indexed into local-first IndexedDB</span>
              <input
                id="nb-files"
                type="file"
                multiple
                accept=".pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[var(--hair)]">
            <button
              type="button"
              onClick={onClose}
              className="btn-fernly-ghost !h-10 !px-4 !text-xs"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="btn-fernly-primary !h-10 !px-5 !text-xs disabled:opacity-50"
            >
              {isSubmitting ? "Creating..." : "Initialize Vault"}
            </button>
          </div>
        </form>
    </Modal>
  );
}
