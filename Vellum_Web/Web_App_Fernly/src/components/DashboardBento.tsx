"use client";

import React from "react";
import {
  FileDown,
  GitFork,
  CheckCheck,
  Plus,
  Search,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Database,
  BookOpen,
  Zap,
  Globe2,
} from "lucide-react";

interface DashboardBentoProps {
  notebooksCount: number;
  totalSourcesCount: number;
  onNewProject: () => void;
  onNavigateTab: (tabId: string) => void;
  onLoadSample: (title: string, emoji: string, category: string, sampleDoi?: string) => void;
}

export function DashboardBento({
  notebooksCount,
  totalSourcesCount,
  onNewProject,
  onNavigateTab,
  onLoadSample,
}: DashboardBentoProps) {
  const samplePresets = [
    {
      title: "DeepFruits: Fruit Detection with Deep Neural Networks",
      emoji: "🍎",
      category: "Computer Vision",
      tag: "Seminal Benchmark",
      doi: "10.3390/s16070988",
      desc: "State-of-the-art fruit recognition and spatial detection using Faster R-CNN.",
    },
    {
      title: "Attention Is All You Need: Transformer Architectures",
      emoji: "⚡",
      category: "Deep Learning",
      tag: "Foundational LLM",
      doi: "10.48550/arXiv.1706.03762",
      desc: "The landmark architecture replacing recurrence and convolution with self-attention.",
    },
    {
      title: "Consumer Behavior in Digital Marketing: Systematic Review",
      emoji: "🛍️",
      category: "Marketing Science",
      tag: "W1 Empirical Review",
      doi: "10.1057/s41270-026-00470-6",
      desc: "Comprehensive synthesis of analytical methods and empirical findings in consumer science.",
    },
  ];

  return (
    <div className="space-y-8 animate-fadeIn">
      {/* ── 1. Hero Showcase Section (Apple HIG & Conversion Architecture) ── */}
      <section className="relative overflow-hidden rounded-[2rem] bg-gradient-to-b from-[var(--card)] via-[var(--card)] to-[var(--panel)] border border-[var(--hair)] p-6 sm:p-8 lg:p-10 shadow-xs">
        {/* Ambient Subtle Radial Glow */}
        <div
          className="pointer-events-none absolute -top-24 -right-24 h-96 w-96 rounded-full blur-3xl opacity-20"
          style={{ backgroundColor: "var(--g-500)" }}
        />

        <div className="relative z-10 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="max-w-2xl space-y-3">
            {/* Tagline Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-[var(--g-100)] text-[var(--g-800)] dark:text-[var(--g-300)] dark:bg-[var(--g-950)]/70 border border-[var(--g-400)]/30 text-[11px] font-semibold tracking-wide">
              <span className="w-1.5 h-1.5 rounded-full bg-[var(--g-600)] animate-pulse" />
              <span>Systematic Literature Intelligence · v2.1 Local-First</span>
            </div>

            {/* Headline */}
            <h1 className="text-2xl sm:text-3xl lg:text-4xl font-extrabold tracking-tight text-[var(--ink)] leading-tight">
              Academic Research Studio
            </h1>

            {/* Value Proposition Subhead */}
            <p className="text-xs sm:text-sm text-[var(--muted)] leading-relaxed font-normal">
              High-throughput PDF harvesting, force-directed citation networks, and active-learning
              systematic screening — completely private, running directly on your machine.
            </p>

            {/* Trust / Proof Strip */}
            <div className="pt-2 flex flex-wrap items-center gap-3 text-[11px] font-medium text-[var(--faint)]">
              <div className="flex items-center gap-1.5 bg-[var(--panel)]/70 px-2.5 py-1 rounded-md border border-[var(--hair)]">
                <Globe2 className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                <span>250M+ OpenAlex Corpus</span>
              </div>
              <div className="flex items-center gap-1.5 bg-[var(--panel)]/70 px-2.5 py-1 rounded-md border border-[var(--hair)]">
                <ShieldCheck className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                <span>100% Local IndexedDB Vault</span>
              </div>
              <div className="flex items-center gap-1.5 bg-[var(--panel)]/70 px-2.5 py-1 rounded-md border border-[var(--hair)]">
                <Zap className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                <span>Multi-Tier Unpaywall &amp; Resolvers</span>
              </div>
            </div>
          </div>

          {/* Quick CTA Actions */}
          <div className="flex flex-row sm:flex-col lg:flex-row items-center gap-3 flex-shrink-0">
            <button
              onClick={() => onNavigateTab("search")}
              className="btn-fernly-ghost flex items-center justify-center gap-2 px-4 py-2.5 rounded-full text-xs font-semibold w-full sm:w-auto"
            >
              <Search className="h-3.5 w-3.5" />
              <span>Live Search</span>
            </button>
            <button
              onClick={onNewProject}
              className="btn-fernly-primary flex items-center justify-center gap-2 px-5 py-2.5 rounded-full text-xs font-semibold shadow-xs hover:scale-[1.02] active:scale-[0.98] transition-transform w-full sm:w-auto"
            >
              <Plus className="h-4 w-4" />
              <span>New Project</span>
            </button>
          </div>
        </div>
      </section>

      {/* ── 2. The 3 Core Engine Bento Cards (Product Pathways) ── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold tracking-tight text-[var(--ink)]">
              Core Research Engines
            </h2>
            <p className="text-xs text-[var(--muted)]">
              Instant access to high-velocity literature processing tools.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 sm:gap-5">
          {/* Engine 1: Batch Downloader */}
          <div
            onClick={() => onNavigateTab("downloader")}
            className="group relative flex flex-col justify-between p-5 sm:p-6 rounded-[1.75rem] bg-[var(--card)] border border-[var(--hair)] hover:border-[var(--g-400)]/60 hover:shadow-md transition-all duration-200 cursor-pointer"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--g-100)] dark:bg-[var(--g-950)] text-[var(--g-700)] dark:text-[var(--g-300)] border border-[var(--g-400)]/30 group-hover:scale-105 transition-transform">
                  <FileDown className="h-5 w-5" />
                </div>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[var(--panel)] text-[var(--muted)] border border-[var(--hair)]">
                  Multi-Tier Resolvers
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-[var(--ink)] group-hover:text-[var(--g-700)] dark:group-hover:text-[var(--g-300)] transition-colors">
                Academic Batch Downloader
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Bulk harvest full texts from BibTeX, RIS, or CSV with DOI deduplication, Unpaywall,
                Elsevier API, and university EZProxy bypass.
              </p>
            </div>
            <div className="mt-5 pt-3 border-t border-[var(--hair)] flex items-center justify-between text-xs font-semibold text-[var(--g-700)] dark:text-[var(--g-400)]">
              <span>Open Batch Downloader</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Engine 2: Connected Papers Citation Graph */}
          <div
            onClick={() => onNavigateTab("connected")}
            className="group relative flex flex-col justify-between p-5 sm:p-6 rounded-[1.75rem] bg-[var(--card)] border border-[var(--hair)] hover:border-[var(--g-400)]/60 hover:shadow-md transition-all duration-200 cursor-pointer"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--g-100)] dark:bg-[var(--g-950)] text-[var(--g-700)] dark:text-[var(--g-300)] border border-[var(--g-400)]/30 group-hover:scale-105 transition-transform">
                  <GitFork className="h-5 w-5" />
                </div>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[var(--panel)] text-[var(--muted)] border border-[var(--hair)]">
                  Force-Directed Canvas
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-[var(--ink)] group-hover:text-[var(--g-700)] dark:group-hover:text-[var(--g-300)] transition-colors">
                Connected Papers Network
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Interactive real-time physics mapping seminal origins, prior foundational citations,
                and derivative breakthroughs in force-directed clusters.
              </p>
            </div>
            <div className="mt-5 pt-3 border-t border-[var(--hair)] flex items-center justify-between text-xs font-semibold text-[var(--g-700)] dark:text-[var(--g-400)]">
              <span>Explore Citation Graph</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
            </div>
          </div>

          {/* Engine 3: ASReview AI Systematic Screening */}
          <div
            onClick={() => onNavigateTab("screening")}
            className="group relative flex flex-col justify-between p-5 sm:p-6 rounded-[1.75rem] bg-[var(--card)] border border-[var(--hair)] hover:border-[var(--g-400)]/60 hover:shadow-md transition-all duration-200 cursor-pointer"
          >
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--g-100)] dark:bg-[var(--g-950)] text-[var(--g-700)] dark:text-[var(--g-300)] border border-[var(--g-400)]/30 group-hover:scale-105 transition-transform">
                  <CheckCheck className="h-5 w-5" />
                </div>
                <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[var(--panel)] text-[var(--muted)] border border-[var(--hair)]">
                  Active Learning ML
                </span>
              </div>
              <h3 className="text-sm sm:text-base font-bold text-[var(--ink)] group-hover:text-[var(--g-700)] dark:group-hover:text-[var(--g-300)] transition-colors">
                AI Systematic Screening
              </h3>
              <p className="text-xs text-[var(--muted)] leading-relaxed">
                Screen thousands of candidate titles and abstracts with Naive Bayes prior rankers,
                stopping heuristics, hotkeys, and PRISMA 2020 exports.
              </p>
            </div>
            <div className="mt-5 pt-3 border-t border-[var(--hair)] flex items-center justify-between text-xs font-semibold text-[var(--g-700)] dark:text-[var(--g-400)]">
              <span>Launch Screening Hub</span>
              <ArrowRight className="h-4 w-4 transform group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </div>
      </section>

      {/* ── 3. Four Compact Metric Chips ── */}
      <section className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--hair)] flex items-center justify-between">
          <div>
            <div className="text-xs text-[var(--muted)] font-medium">Active Reviews</div>
            <div className="text-xl sm:text-2xl font-bold text-[var(--ink)] mt-0.5">
              {notebooksCount}
            </div>
          </div>
          <div className="h-9 w-9 rounded-xl bg-[var(--panel)] flex items-center justify-center text-[var(--g-700)] dark:text-[var(--g-400)]">
            <BookOpen className="h-4 w-4" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--hair)] flex items-center justify-between">
          <div>
            <div className="text-xs text-[var(--muted)] font-medium">Local Corpus</div>
            <div className="text-xl sm:text-2xl font-bold text-[var(--ink)] mt-0.5">
              {totalSourcesCount}
            </div>
          </div>
          <div className="h-9 w-9 rounded-xl bg-[var(--panel)] flex items-center justify-center text-[var(--g-700)] dark:text-[var(--g-400)]">
            <Database className="h-4 w-4" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--hair)] flex items-center justify-between">
          <div>
            <div className="text-xs text-[var(--muted)] font-medium">Global Coverage</div>
            <div className="text-xl sm:text-2xl font-bold text-[var(--ink)] mt-0.5">
              250M+
            </div>
          </div>
          <div className="h-9 w-9 rounded-xl bg-[var(--panel)] flex items-center justify-center text-[var(--g-700)] dark:text-[var(--g-400)]">
            <Sparkles className="h-4 w-4" />
          </div>
        </div>

        <div className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--hair)] flex items-center justify-between">
          <div>
            <div className="text-xs text-[var(--muted)] font-medium">Local Privacy</div>
            <div className="text-xl sm:text-2xl font-bold text-[var(--ink)] mt-0.5">
              100% Local
            </div>
          </div>
          <div className="h-9 w-9 rounded-xl bg-[var(--panel)] flex items-center justify-center text-[var(--g-700)] dark:text-[var(--g-400)]">
            <ShieldCheck className="h-4 w-4" />
          </div>
        </div>
      </section>

      {/* ── 4. Instant Sample Demonstrations (1-Click Onboarding) ── */}
      <section className="space-y-3">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-base sm:text-lg font-bold tracking-tight text-[var(--ink)]">
              Quick-Start Preset Demonstrations
            </h2>
            <p className="text-xs text-[var(--muted)]">
              Instantly seed a review notebook to explore the workspace without uploading files.
            </p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 sm:gap-4">
          {samplePresets.map((preset) => (
            <div
              key={preset.title}
              onClick={() => onLoadSample(preset.title, preset.emoji, preset.category, preset.doi)}
              className="p-4 rounded-2xl bg-[var(--card)] border border-[var(--hair)] hover:border-[var(--g-400)]/60 hover:shadow-xs transition-all cursor-pointer group flex flex-col justify-between"
            >
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-2xl">{preset.emoji}</span>
                  <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[var(--panel)] text-[var(--muted)] border border-[var(--hair)]">
                    {preset.tag}
                  </span>
                </div>
                <div className="text-xs font-bold text-[var(--ink)] group-hover:text-[var(--g-700)] dark:group-hover:text-[var(--g-300)] line-clamp-1 transition-colors">
                  {preset.title}
                </div>
                <p className="text-[11px] text-[var(--muted)] line-clamp-2 leading-relaxed">
                  {preset.desc}
                </p>
              </div>
              <div className="mt-3 pt-2 border-t border-[var(--hair)] flex items-center justify-between text-[11px] font-semibold text-[var(--g-700)] dark:text-[var(--g-400)]">
                <span>Load Sample Workspace</span>
                <Plus className="h-3.5 w-3.5 transform group-hover:rotate-90 transition-transform" />
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
}
