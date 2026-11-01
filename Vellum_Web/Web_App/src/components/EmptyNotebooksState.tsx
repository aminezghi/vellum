"use client";

import React from "react";
import { Plus, Search, Sparkles, BookOpen, ArrowUpRight, ShieldCheck, Zap } from "lucide-react";

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
    <div className="fernly-card relative overflow-hidden p-8 sm:p-12 text-center">
      {/* Background Ambient Radial Glow */}
      <div className="pointer-events-none absolute -top-32 left-1/2 -translate-x-1/2 h-96 w-[36rem] rounded-full bg-[var(--swirl)] blur-3xl opacity-50" />

      {/* Center Illustration Graphic */}
      <div className="relative mx-auto mb-6 flex items-center justify-center">
        <div className="absolute h-24 w-24 rounded-full bg-[var(--g-100)] border border-[var(--g-400)]/30 animate-pulse" />
        <div className="relative flex h-16 w-16 items-center justify-center rounded-2xl bg-[var(--card)] border border-[var(--hair)] shadow-md group">
          <BookOpen className="h-8 w-8 text-[var(--g-700)] group-hover:scale-105 transition-transform" />
          <div className="absolute -top-1 -right-1 flex h-6 w-6 items-center justify-center rounded-lg bg-[var(--g-950)] text-white shadow-xs">
            <Sparkles className="h-3.5 w-3.5 text-[var(--g-400)]" />
          </div>
        </div>
      </div>

      {/* Value Guarantee Pill */}
      <div className="inline-flex items-center gap-1.5 px-3.5 py-1 rounded-full bg-[var(--g-100)] border border-[var(--g-400)]/30 text-[var(--g-800)] text-xs font-semibold mb-3">
        <ShieldCheck className="h-3.5 w-3.5 text-[var(--g-700)]" />
        <span>100% Free · Zero Login · Local-First (IndexedDB)</span>
      </div>

      {/* Main Copywriting */}
      <h3 className="relative text-2xl sm:text-3xl font-bold tracking-tight text-[var(--ink)] mb-3">
        Your Research Workspace is{" "}
        <span className="text-[var(--g-700)]">Clean &amp; Ready</span>
      </h3>
      <p className="relative max-w-xl mx-auto text-xs sm:text-sm text-[var(--muted)] leading-relaxed mb-8 font-medium">
        No projects initialized yet. Search over 250M+ peer-reviewed papers above, explore citation momentum streams, or initialize your first systematic review canvas below.
      </p>

      {/* Primary Action Buttons */}
      <div className="relative flex flex-wrap items-center justify-center gap-3.5 mb-10">
        <button
          onClick={onCreateNotebook}
          className="btn-fernly-primary"
        >
          <Plus className="h-4 w-4" />
          <span>Create Blank Project</span>
        </button>

        <button
          onClick={onExploreSearch}
          className="btn-fernly-ghost"
        >
          <Search className="h-4 w-4 text-[var(--g-700)]" />
          <span>Search 250M+ Papers</span>
        </button>
      </div>

      {/* Quick Starter Suggestions */}
      <div className="relative pt-7 border-t border-[var(--hair)] w-full max-w-6xl mx-auto">
        <div className="flex items-center justify-between mb-4">
          <span className="text-xs font-semibold tracking-wider text-[var(--muted)] flex items-center gap-1.5 uppercase">
            <Zap className="h-3.5 w-3.5 text-[var(--amber)]" />
            <span>Launch with a curated review template:</span>
          </span>
          <span className="text-[11px] text-[var(--faint)] hidden sm:inline font-medium">1-click seed</span>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3.5 text-left">
          {sampleTopics.map((topic) => (
            <div
              key={topic.title}
              onClick={() => onQuickStart(topic.title, topic.emoji, topic.category)}
              className="fernly-card p-4 hover:border-[var(--g-600)] transition-all cursor-pointer flex items-start justify-between"
            >
              <div className="flex items-start gap-3 truncate">
                <span className="text-2xl p-2 rounded-xl bg-[var(--panel)] border border-[var(--hair)] flex-shrink-0">
                  {topic.emoji}
                </span>
                <div className="min-w-0">
                  <p className="text-xs font-semibold text-[var(--ink)] hover:text-[var(--g-700)] truncate transition-colors">
                    {topic.title}
                  </p>
                  <p className="text-[11px] text-[var(--muted)] truncate mt-0.5">
                    {topic.papersHint}
                  </p>
                  <div className="flex items-center gap-2 mt-2">
                    <span className="text-[10px] text-[var(--muted)] bg-[var(--panel)] border border-[var(--hair)] px-2 py-0.5 rounded-full font-medium">
                      {topic.category}
                    </span>
                    <span className="fernly-badge badge-done text-[10px]">
                      {topic.growth}
                    </span>
                  </div>
                </div>
              </div>
              <ArrowUpRight className="h-4 w-4 text-[var(--faint)] flex-shrink-0 ml-2" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
