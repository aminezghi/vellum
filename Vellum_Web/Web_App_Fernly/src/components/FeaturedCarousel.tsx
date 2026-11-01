"use client";

import React from "react";
import { Notebook } from "@/lib/db";
import { BookOpen, ChevronRight, Globe, User } from "lucide-react";

interface FeaturedCarouselProps {
  notebooks: Notebook[];
  onSelectNotebook: (notebook: Notebook) => void;
  onViewAll?: () => void;
}

export function FeaturedCarousel({
  notebooks,
  onSelectNotebook,
  onViewAll,
}: FeaturedCarouselProps) {
  if (notebooks.length === 0) return null;

  return (
    <div className="mb-8">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30 shadow-xs">
            <BookOpen className="h-4 w-4" />
          </div>
          <h2 className="text-sm sm:text-base font-bold text-[var(--ink)] tracking-tight">
            Featured Research Vaults
          </h2>
        </div>
        <button
          onClick={onViewAll}
          className="text-xs text-[var(--g-700)] hover:underline flex items-center gap-1 transition-colors font-semibold cursor-pointer"
          title="View all curated research collections"
        >
          View all <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>

      <div className="flex items-center gap-4 overflow-x-auto pb-4 no-scrollbar">
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
              className="fernly-card group flex-shrink-0 w-72 h-44 p-5 flex flex-col justify-between cursor-pointer"
            >
              {/* Top Row: Author badge & Category */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 bg-[var(--panel)] px-2.5 py-0.5 rounded-full border border-[var(--hair)] text-[11px] text-[var(--muted)] font-medium">
                  <User className="h-3 w-3 text-[var(--g-700)]" />
                  <span className="truncate max-w-[120px]">{nb.authorName || "Open Scholar"}</span>
                </div>
                <span className="text-xl">{nb.emoji}</span>
              </div>

              {/* Title & Metadata */}
              <div className="mt-2">
                <h3 className="text-sm font-semibold text-[var(--ink)] line-clamp-2 group-hover:text-[var(--g-700)] transition-colors leading-snug tracking-tight">
                  {nb.title}
                </h3>
                <div className="flex items-center gap-2 mt-2 text-[11px] text-[var(--muted)]">
                  <span className="font-medium">{dateStr}</span>
                  <span>•</span>
                  <span className="fernly-badge badge-done text-[10px]">
                    {nb.sourcesCount || 0} sources
                  </span>
                  <span>•</span>
                  <Globe className="h-3 w-3 text-[var(--faint)]" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
