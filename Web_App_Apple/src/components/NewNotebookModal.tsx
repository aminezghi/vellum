"use client";

import React, { useState } from "react";
import { db, Notebook } from "@/lib/db";
import { X, Sparkles, Upload, FileText } from "lucide-react";

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
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="w-full max-w-lg rounded-[2.5rem] bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 p-7 shadow-2xl relative text-[#1a1a1a] dark:text-[#ffffeb]">
        <button
          onClick={onClose}
          className="absolute right-5 top-5 p-2 rounded-full text-[#1a1a1a]/50 dark:text-white/40 hover:text-[#1a1a1a] dark:hover:text-white hover:bg-[#1a1a1a]/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
        >
          <X className="h-4 w-4" />
        </button>

        <div className="flex items-center gap-2.5 mb-5">
          <div className="p-2.5 rounded-2xl bg-[#f0d7ff] dark:bg-[#4a154b]/50 text-[#4a154b] dark:text-[#f0d7ff] border border-[#f0d7ff] dark:border-transparent">
            <Sparkles className="h-5 w-5" />
          </div>
          <div>
            <h2 className="text-lg font-semibold tracking-tight text-[#1a1a1a] dark:text-white">Create Research Notebook</h2>
            <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60">Initialize a corpus for your literature review &amp; analysis</p>
          </div>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Emoji & Title */}
          <div>
            <label className="block text-xs font-semibold text-[#1a1a1a]/80 mb-1.5">Notebook Icon & Title</label>
            <div className="flex items-center gap-2">
              <div className="flex-shrink-0">
                <select
                  value={selectedEmoji}
                  onChange={(e) => setSelectedEmoji(e.target.value)}
                  className="bg-[#f8f9fa] border border-[#1a1a1a]/15 rounded-2xl px-3 py-2.5 text-xl focus:outline-none focus:border-[#034f46] cursor-pointer"
                >
                  {EMOJI_OPTIONS.map((e) => (
                    <option key={e} value={e}>
                      {e}
                    </option>
                  ))}
                </select>
              </div>
              <input
                type="text"
                required
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="e.g. Systematic Review on Microplastics in Food"
                className="w-full bg-[#f8f9fa] border border-[#1a1a1a]/15 rounded-full px-4 py-2.5 text-xs text-[#1a1a1a] placeholder-[#1a1a1a]/40 focus:outline-none focus:bg-white focus:border-[#034f46] focus:ring-1 focus:ring-[#034f46]/20 transition-all"
              />
            </div>
          </div>

          {/* Description */}
          <div>
            <label className="block text-xs font-semibold text-[#1a1a1a]/80 mb-1.5">Description (Optional)</label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Research objective, search strategy, or screening criteria..."
              rows={2}
              className="w-full bg-[#f8f9fa] border border-[#1a1a1a]/15 rounded-2xl px-4 py-2.5 text-xs text-[#1a1a1a] placeholder-[#1a1a1a]/40 focus:outline-none focus:bg-white focus:border-[#034f46] focus:ring-1 focus:ring-[#034f46]/20 transition-all"
            />
          </div>

          {/* Initial PDFs Dropzone */}
          <div>
            <label className="block text-xs font-semibold text-[#1a1a1a]/80 mb-1.5">Upload Initial PDFs (Optional)</label>
            <label className="flex flex-col items-center justify-center p-5 border border-dashed border-[#1a1a1a]/20 hover:border-[#034f46] rounded-2xl bg-[#ffffeb]/60 hover:bg-[#ffffeb] cursor-pointer transition-colors group">
              <Upload className="h-6 w-6 text-[#1a1a1a]/40 group-hover:text-[#034f46] transition-colors mb-1.5" />
              <span className="text-xs text-[#1a1a1a] font-medium">Click or drag & drop PDFs here</span>
              <span className="text-[10px] text-[#1a1a1a]/50 mt-0.5">Stored 100% locally on your machine</span>
              <input
                type="file"
                multiple
                accept="application/pdf"
                onChange={handleFileChange}
                className="hidden"
              />
            </label>

            {files.length > 0 && (
              <div className="mt-2 space-y-1.5 max-h-24 overflow-y-auto">
                {files.map((f, idx) => (
                  <div key={idx} className="flex items-center gap-2 text-[11px] text-[#1a1a1a] bg-[#ffffeb] border border-[#1a1a1a]/8 px-3 py-1.5 rounded-xl">
                    <FileText className="h-3.5 w-3.5 text-[#034f46]" />
                    <span className="truncate flex-1 font-medium">{f.name}</span>
                    <span className="text-[#1a1a1a]/50 text-[10px]">{(f.size / 1024).toFixed(0)} KB</span>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Actions */}
          <div className="flex items-center justify-end gap-2.5 pt-3 border-t border-[#1a1a1a]/8">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 rounded-full text-xs font-semibold text-[#1a1a1a]/70 hover:text-[#1a1a1a] hover:bg-[#1a1a1a]/5 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={isSubmitting || !title.trim()}
              className="px-6 py-2.5 rounded-full text-xs font-semibold bg-[#034f46] hover:bg-[#034f46]/90 text-[#ffffeb] shadow-sm shadow-[#034f46]/20 disabled:opacity-40 transition-all cursor-pointer"
            >
              {isSubmitting ? "Creating..." : "Create Notebook"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
