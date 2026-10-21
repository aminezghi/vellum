"use client";

import React from "react";
import { Plus, Search, Sparkles, BookOpen, Layers, Compass, ArrowUpRight, ShieldCheck, Zap } from "lucide-react";

interface EmptyNotebooksStateProps {
  onCreateNotebook: () => void;
  onExploreSearch: () => void;
  onQuickStart: (title: string, emoji: string, category: string) => void;
}

export function EmptyNotebooksState({
  onCreateNotebook,
  onExploreSearch,
  onQuickStart,
}: EmptyNotebooksStateProps) {
  const sampleTopics = [
    {
      title: "Reasoning & Cognitive Alignment in LLMs",
      emoji: "🧠",
      category: "Artificial Intelligence",
      papersHint: "O1 architecture, chain-of-thought, verification",
      growth: "+142% citations",
    },
    {
      title: "Microplastics & Environmental Bioaccumulation",
      emoji: "🌱",
      category: "Ecology & Climate",
      papersHint: "Trophic transfer, marine ecosystems, health impact",
      growth: "+89% citations",
    },
    {
      title: "Mediterranean Diet & Cardiovascular Biomarkers",
      emoji: "🥗",
      category: "Medicine & Health",
      papersHint: "Endothelial function, lipid profiles, randomized trials",
      growth: "+64% citations",
    },
    {
      title: "Consumer Demand Elasticities in Grocery Retail",
      emoji: "📈",
      category: "Quantitative Economics",
      papersHint: "AIDS models, inflation shocks, substitution effects",
      growth: "+51% citations",
    },
  ];

  return (
    <div className="relative overflow-hidden rounded-[2.5rem] border border-[#1a1a1a]/10 dark:border-white/10 bg-white/95 dark:bg-[#1a1e1c] p-8 sm:p-14 text-center shadow-[0_12px_40px_rgba(26,26,26,0.04)] transition-colors duration-200">
      {/* Background Ambient Radial Glows */}
      <div className="pointer-events-none absolute -top-32 left-1/2 -translate-x-1/2 h-96 w-[36rem] rounded-full bg-gradient-to-tr from-[#cef5ca]/40 dark:from-[#034f46]/30 via-[#f0d7ff]/30 dark:via-[#4a154b]/20 to-[#ffffeb] dark:to-[#121413] blur-3xl" />
      <div className="pointer-events-none absolute -bottom-32 right-1/4 h-64 w-80 rounded-full bg-[#cef5ca]/20 dark:bg-[#034f46]/20 blur-3xl" />

      {/* Modern Center Illustration Graphic */}
      <div className="relative mx-auto mb-7 flex items-center justify-center">
        {/* Outer Ring */}
        <div className="absolute h-28 w-28 rounded-full bg-[#034f46]/5 dark:bg-[#23a07a]/10 border border-[#034f46]/15 dark:border-[#23a07a]/20 animate-pulse" />

        {/* Core Icon Hexagon / Badge */}
        <div className="relative flex h-20 w-20 items-center justify-center rounded-3xl bg-[#ffffeb] dark:bg-[#121413] border border-[#1a1a1a]/10 dark:border-white/10 shadow-md group">
          <BookOpen className="h-9 w-9 text-[#034f46] dark:text-[#cef5ca] group-hover:scale-105 transition-transform duration-300" />
          <div className="absolute -top-1.5 -right-1.5 flex h-7 w-7 items-center justify-center rounded-xl bg-[#034f46] text-[#ffffeb] shadow-sm">
            <Sparkles className="h-4 w-4 text-[#cef5ca]" />
          </div>
        </div>
      </div>

      {/* Value Guarantee Pill */}
      <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[#cef5ca] dark:bg-[#034f46] border border-[#114e0b]/20 text-[#114e0b] dark:text-[#cef5ca] text-xs font-semibold mb-3">
        <ShieldCheck className="h-3.5 w-3.5" />
        <span>100% Free · Zero Login · Local-First (IndexedDB)</span>
      </div>

      {/* Main Copywriting with EB Garamond Editorial Accent */}
      <h3 className="relative text-2xl sm:text-3xl font-bold tracking-tight text-[#1a1a1a] dark:text-[#ffffeb] mb-3">
        Your Research Workspace is{" "}
        <span className="font-serif italic font-normal text-[#034f46] dark:text-[#23a07a]">Clean &amp; Ready</span>
      </h3>
      <p className="relative max-w-xl mx-auto text-xs sm:text-sm text-[#1a1a1a]/70 dark:text-white/70 leading-relaxed mb-8 font-medium">
        No notebooks created yet. Search over 250M+ peer-reviewed papers above, explore citation momentum streams, or initialize your first systematic review canvas below.
      </p>

      {/* Primary Action Buttons */}
      <div className="relative flex flex-wrap items-center justify-center gap-3.5 mb-12">
        <button
          onClick={onCreateNotebook}
          className="flex items-center gap-2 px-6 py-3 rounded-full bg-[#034f46] hover:bg-[#023630] text-[#ffffeb] text-xs sm:text-sm font-semibold shadow-sm hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer"
        >
          <Plus className="h-4 w-4" />
          <span>Create Blank Notebook</span>
        </button>

        <button
          onClick={onExploreSearch}
          className="flex items-center gap-2 px-6 py-3 rounded-full bg-white dark:bg-[#121413] hover:bg-[#ffffeb] dark:hover:bg-[#252a27] text-[#1a1a1a] dark:text-white border border-[#1a1a1a]/15 dark:border-white/15 text-xs sm:text-sm font-semibold hover:border-[#034f46]/40 hover:scale-[1.02] active:scale-[0.98] transition-all cursor-pointer shadow-sm"
        >
          <Search className="h-4 w-4 text-[#034f46] dark:text-[#cef5ca]" />
          <span>Search 250M+ Papers</span>
        </button>
      </div>

      {/* Quick Starter Suggestions */}
      <div className="relative pt-8 border-t border-[#1a1a1a]/10 dark:border-white/10 w-full max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <span className="text-[11px] font-semibold uppercase tracking-wider text-[#1a1a1a]/70 dark:text-white/70 flex items-center gap-1.5">
            <Zap className="h-3.5 w-3.5 text-[#ffa946]" />
            <span>Or launch with a popular systematic review template:</span>
          </span>
          <span className="text-[10px] text-[#1a1a1a]/50 dark:text-white/40 hidden sm:inline font-medium">1-click seed with search query</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 text-left">
          {sampleTopics.map((topic) => (
            <div
              key={topic.title}
              onClick={() => onQuickStart(topic.title, topic.emoji, topic.category)}
              className="group p-4 rounded-2xl bg-white dark:bg-[#121413] hover:bg-[#ffffeb]/60 dark:hover:bg-white/5 border border-[#1a1a1a]/10 dark:border-white/10 hover:border-[#034f46]/40 hover:shadow-md transition-all cursor-pointer flex items-start justify-between"
            >
              <div className="flex items-start gap-3 truncate">
                <span className="text-2xl p-2 rounded-xl bg-[#ffffeb] dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 group-hover:scale-105 transition-transform flex-shrink-0">
                  {topic.emoji}
                </span>
                <div className="min-w-0">
                  <div className="flex items-center gap-2">
                    <p className="text-xs font-semibold text-[#1a1a1a] dark:text-white group-hover:text-[#034f46] dark:group-hover:text-[#cef5ca] truncate transition-colors">
                      {topic.title}
                    </p>
                  </div>
                  <p className="text-[11px] text-[#1a1a1a]/60 dark:text-white/60 truncate mt-0.5">
                    {topic.papersHint}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-[#1a1a1a]/70 dark:text-white/70 bg-[#1a1a1a]/5 dark:bg-white/5 px-2 py-0.5 rounded-full font-medium">
                      {topic.category}
                    </span>
                    <span className="text-[10px] text-[#114e0b] dark:text-[#cef5ca] bg-[#cef5ca] dark:bg-[#034f46] px-2 py-0.5 rounded-full font-semibold">
                      {topic.growth}
                    </span>
                  </div>
                </div>
              </div>
              <ArrowUpRight className="h-4 w-4 text-[#1a1a1a]/40 dark:text-white/40 group-hover:text-[#034f46] dark:group-hover:text-[#cef5ca] group-hover:translate-x-0.5 group-hover:-translate-y-0.5 transition-all flex-shrink-0 ml-2" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

