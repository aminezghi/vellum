"use client";

import React from "react";
import { Notebook } from "@/lib/db";
import { BookOpen, ChevronRight, Globe, User } from "lucide-react";

interface FeaturedCarouselProps {
  notebooks: Notebook[];
  onSelectNotebook: (notebook: Notebook) => void;
}

export function FeaturedCarousel({ notebooks, onSelectNotebook }: FeaturedCarouselProps) {
  if (notebooks.length === 0) return null;

  return (
    <div className="mb-10">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded-xl bg-[#034f46] text-[#ffffeb] shadow-xs">
            <BookOpen className="h-4 w-4" />
          </div>
          <h2 className="text-sm sm:text-base font-bold text-[#1a1a1a] dark:text-[#ffffeb] tracking-tight">
            Featured Notebooks
          </h2>
        </div>
        <button className="text-xs text-[#034f46] dark:text-[#cef5ca] hover:underline flex items-center gap-1 transition-colors font-medium cursor-pointer">
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
              className="group relative flex-shrink-0 w-68 h-44 rounded-[1.75rem] p-5 bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 hover:border-[#034f46]/35 dark:hover:border-[#23a07a]/40 hover:shadow-md hover:-translate-y-0.5 transition-all cursor-pointer flex flex-col justify-between overflow-hidden shadow-xs"
            >
              {/* Top Row: Author badge & Category */}
              <div className="flex items-center justify-between gap-2">
                <div className="flex items-center gap-1.5 bg-[#ffffeb] dark:bg-[#121413] px-2.5 py-0.5 rounded-full border border-[#1a1a1a]/10 dark:border-white/10 text-[11px] text-[#1a1a1a]/80 dark:text-white/80 font-medium">
                  <User className="h-3 w-3 text-[#034f46] dark:text-[#cef5ca]" />
                  <span className="truncate max-w-[120px]">{nb.authorName || "Open Scholar"}</span>
                </div>
                <span className="text-xl">{nb.emoji}</span>
              </div>

              {/* Title & Metadata */}
              <div className="mt-2">
                <h3 className="text-xs sm:text-sm font-semibold text-[#1a1a1a] dark:text-white line-clamp-2 group-hover:text-[#034f46] dark:group-hover:text-[#cef5ca] transition-colors leading-snug tracking-tight">
                  {nb.title}
                </h3>
                <div className="flex items-center gap-2 mt-2 text-[10px] text-[#1a1a1a]/60 dark:text-white/60">
                  <span className="font-medium">{dateStr}</span>
                  <span>•</span>
                  <span className="text-[#114e0b] dark:text-[#cef5ca] bg-[#cef5ca] dark:bg-[#034f46] px-2 py-0.5 rounded-full font-semibold">
                    {nb.sourcesCount} sources
                  </span>
                  <span>•</span>
                  <Globe className="h-3 w-3 text-[#1a1a1a]/40 dark:text-white/40" />
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
