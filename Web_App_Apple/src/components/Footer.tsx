"use client";

import React from "react";
import {
  BookOpen,
  ShieldCheck,
  Zap,
  ExternalLink,
  Heart,
  Terminal,
  Code2,
  Database,
  ArrowUp,
  Sparkles,
  UserCheck,
  Award,
} from "lucide-react";

interface FooterProps {
  onClearAllNotebooks?: () => void;
  notebooksCount?: number;
}

export function Footer({ onClearAllNotebooks, notebooksCount = 0 }: FooterProps) {
  const scrollToTop = () => {
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <footer className="w-full mt-16 border-t border-[#1a1a1a]/8 dark:border-white/10 bg-[#ffffeb]/60 dark:bg-[#121413]/60 backdrop-blur-sm transition-colors duration-200">
      <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14 py-10 sm:py-14">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10 pb-10 border-b border-[#1a1a1a]/8 dark:border-white/10">
          {/* Brand & Purpose */}
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[#034f46] text-[#ffffeb] shadow-xs">
                <BookOpen className="h-4 w-4 text-[#cef5ca]" />
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-[#1a1a1a] dark:text-[#ffffeb]">
                  Vellum Web
                </span>
                <span className="ml-2 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#cef5ca] text-[#114e0b] dark:bg-[#034f46] dark:text-[#cef5ca]">
                  v2.4 Dual Pack
                </span>
              </div>
            </div>
            <p className="text-xs text-[#1a1a1a]/65 dark:text-white/65 leading-relaxed font-medium">
              Free, local-first academic literature research studio and systematic review engine with multi-database discovery and multi-tier PDF retrieval.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-[#114e0b] dark:text-[#cef5ca]">
              <ShieldCheck className="h-3.5 w-3.5" />
              <span className="font-semibold">100% Client-Side Private Storage</span>
            </div>
          </div>

          {/* Academic Sources Connected */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#1a1a1a]/70 dark:text-white/70">
              Integrated Corpus Sources
            </h4>
            <ul className="text-xs space-y-1.5 text-[#1a1a1a]/60 dark:text-white/60 font-medium">
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[#034f46] dark:bg-[#23a07a]" />
                <span>OpenAlex — 250M+ Works &amp; Citations</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[#ffa946]" />
                <span>arXiv API — Physics, Math, CS Preprints</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[#f0d7ff]" />
                <span>Semantic Scholar — Graph &amp; Authors</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[#cef5ca]" />
                <span>Crossref &amp; Unpaywall — DOI Resolution</span>
              </li>
            </ul>
          </div>

          {/* Authorship & Creator Credits: Amine Zouaghi */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#1a1a1a]/70 dark:text-white/70 flex items-center gap-1.5">
              <Award className="h-3.5 w-3.5 text-[#034f46] dark:text-[#23a07a]" />
              <span>Creator &amp; Lead Engineer</span>
            </h4>
            <div className="space-y-1.5 text-xs text-[#1a1a1a]/75 dark:text-white/75 font-medium">
              <p className="flex items-center gap-1.5">
                <UserCheck className="h-4 w-4 text-[#034f46] dark:text-[#cef5ca] flex-shrink-0" />
                <span className="text-sm font-bold text-[#1a1a1a] dark:text-white">Amine Zouaghi</span>
              </p>
              <p className="text-[11px] text-[#1a1a1a]/65 dark:text-white/65 leading-snug">
                Author &amp; Lead Architect of <strong>Vellum Web</strong> &amp; the <strong>PDF Downloader Dual Pack</strong>.
              </p>
              <p className="text-[11px] text-[#1a1a1a]/55 dark:text-white/55">
                Engineered for systematic reviews, evidence synthesis &amp; open-access literature mining.
              </p>
            </div>
            <div className="pt-1 flex items-center gap-1.5 flex-wrap">
              <span className="inline-flex items-center gap-1 text-[10px] text-[#034f46] dark:text-[#cef5ca] bg-[#cef5ca]/50 dark:bg-[#034f46]/30 px-2 py-0.5 rounded-full font-semibold">
                <Terminal className="h-3 w-3" />
                <span>Next.js 16 Turbopack</span>
              </span>
              <span className="inline-flex items-center gap-1 text-[10px] text-[#4a154b] dark:text-[#f0d7ff] bg-[#f0d7ff]/50 dark:bg-[#4a154b]/30 px-2 py-0.5 rounded-full font-semibold">
                <Database className="h-3 w-3" />
                <span>Dexie.js IndexedDB</span>
              </span>
            </div>
          </div>

          {/* Quick Management & Actions */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[#1a1a1a]/70 dark:text-white/70">
              Workspace Operations
            </h4>
            <div className="flex flex-col gap-2">
              <button
                onClick={scrollToTop}
                className="inline-flex items-center justify-between px-3.5 py-2 rounded-xl bg-white dark:bg-[#1a1d1b] border border-[#1a1a1a]/10 dark:border-white/10 hover:border-[#034f46] dark:hover:border-[#23a07a] text-xs font-medium text-[#1a1a1a] dark:text-white transition-all cursor-pointer shadow-xs"
              >
                <span>Back to top</span>
                <ArrowUp className="h-3.5 w-3.5 text-[#034f46] dark:text-[#23a07a]" />
              </button>

              {onClearAllNotebooks && notebooksCount > 0 && (
                <button
                  onClick={onClearAllNotebooks}
                  className="inline-flex items-center justify-between px-3.5 py-2 rounded-xl bg-red-50 dark:bg-red-950/30 border border-red-200 dark:border-red-800/40 hover:bg-red-100 dark:hover:bg-red-900/40 text-xs font-semibold text-red-700 dark:text-red-400 transition-all cursor-pointer"
                >
                  <span>Clean / Reset All Notebooks</span>
                  <span className="text-[10px] px-1.5 py-0.2 rounded-full bg-red-200 dark:bg-red-900 text-red-800 dark:text-red-200">
                    {notebooksCount}
                  </span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#1a1a1a]/55 dark:text-white/50">
          <div className="flex items-center gap-2 flex-wrap text-center sm:text-left">
            <span>© 2026 Vellum Academic · Developed by <strong className="text-[#1a1a1a] dark:text-white font-semibold">Amine Zouaghi</strong>.</span>
            <span className="hidden sm:inline">·</span>
            <span className="flex items-center gap-1">
              Crafted with <Heart className="h-3 w-3 text-red-500 inline fill-red-500" /> for researchers &amp; academics worldwide
            </span>
          </div>

          <div className="flex items-center gap-4 text-[11px] font-medium">
            <span className="flex items-center gap-1.5 text-[#114e0b] dark:text-[#cef5ca]">
              <Database className="h-3 w-3" />
              <span>IndexedDB Active</span>
            </span>
            <span>·</span>
            <span className="flex items-center gap-1.5 text-[#034f46] dark:text-[#23a07a]">
              <Zap className="h-3 w-3" />
              <span>Multi-Source Resolver</span>
            </span>
          </div>
        </div>
      </div>
    </footer>
  );
}
