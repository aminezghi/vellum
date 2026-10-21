"use client";

import React from "react";
import {
  BookOpen,
  ShieldCheck,
  Award,
  UserCheck,
  ArrowUp,
  Trash2,
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
    <footer className="w-full mt-16 border-t border-[var(--hair)] bg-[var(--panel)] transition-colors duration-250">
      <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-12 py-10 sm:py-14">
        {/* Top Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 mb-10 pb-10 border-b border-[var(--hair)]">
          {/* Brand & Purpose */}
          <div className="space-y-3">
            <div className="flex items-center gap-2.5">
              <div className="flex h-9 w-9 items-center justify-center rounded-2xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30 shadow-xs">
                <BookOpen className="h-4 w-4" />
              </div>
              <div>
                <span className="text-base font-bold tracking-tight text-[var(--ink)]">
                  Vellum
                </span>
                <span className="ml-2 text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[var(--g-100)] text-[var(--g-800)] border border-[var(--g-400)]/30">
                  Fernly Bento Edition
                </span>
              </div>
            </div>
            <p className="text-xs text-[var(--muted)] leading-relaxed font-medium">
              A calm, organic botanical academic workspace that moves as one product. Local-first systematic reviews, multi-database discovery, and multi-tier PDF retrieval.
            </p>
            <div className="flex items-center gap-2 text-[11px] text-[var(--g-800)]">
              <ShieldCheck className="h-3.5 w-3.5 text-[var(--g-700)]" />
              <span className="font-semibold">100% Client-Side Private Storage (IndexedDB)</span>
            </div>
          </div>

          {/* Academic Sources Connected */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              Integrated Corpus Sources
            </h4>
            <ul className="text-xs space-y-1.5 text-[var(--muted)] font-medium">
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--g-600)]" />
                <span>OpenAlex — 250M+ Works &amp; Citations</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--amber)]" />
                <span>arXiv API — Physics, Math, CS Preprints</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--sky)]" />
                <span>Semantic Scholar — Citation Graph</span>
              </li>
              <li className="flex items-center gap-1.5">
                <span className="h-1.5 w-1.5 rounded-full bg-[var(--g-400)]" />
                <span>Crossref &amp; Unpaywall — DOI Resolution</span>
              </li>
            </ul>
          </div>

          {/* Authorship & Creator Credits: Amine Zouaghi */}
          <div className="space-y-2.5">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--muted)] flex items-center gap-1.5">
              <Award className="h-3.5 w-3.5 text-[var(--g-700)]" />
              <span>Creator &amp; Lead Engineer</span>
            </h4>
            <div className="space-y-1.5 text-xs text-[var(--muted)] font-medium">
              <p className="flex items-center gap-1.5">
                <UserCheck className="h-4 w-4 text-[var(--g-700)] flex-shrink-0" />
                <span className="text-sm font-bold text-[var(--ink)]">Amine Zouaghi</span>
              </p>
              <p className="text-[11px] leading-snug">
                University of Parma · Author &amp; Lead Architect of <strong>Vellum</strong>.
              </p>
              <p className="text-[11px] text-[var(--faint)]">
                Engineered for systematic reviews, evidence synthesis &amp; open-access literature mining.
              </p>
            </div>
          </div>

          {/* Quick Storage & Back to Top */}
          <div className="space-y-3">
            <h4 className="text-xs font-bold uppercase tracking-wider text-[var(--muted)]">
              Workspace Health
            </h4>
            <div className="p-3 rounded-2xl bg-[var(--card)] border border-[var(--hair)] space-y-2 text-xs">
              <div className="flex justify-between items-center text-[var(--muted)]">
                <span>Active Vaults:</span>
                <span className="font-bold text-[var(--ink)]">{notebooksCount}</span>
              </div>
              <div className="flex justify-between items-center text-[var(--muted)]">
                <span>Storage Engine:</span>
                <span className="text-[10px] font-semibold text-[var(--g-800)] bg-[var(--g-100)] px-2 py-0.5 rounded-full">
                  IndexedDB Dexie
                </span>
              </div>
            </div>

            <div className="flex items-center gap-2 pt-1">
              {onClearAllNotebooks && notebooksCount > 0 && (
                <button
                  onClick={onClearAllNotebooks}
                  className="flex-1 flex items-center justify-center gap-1.5 px-3 py-2 rounded-full border border-red-200 text-red-600 hover:bg-red-50 text-xs font-semibold transition-all cursor-pointer shadow-xs"
                >
                  <Trash2 className="h-3 w-3" />
                  <span>Clean Storage</span>
                </button>
              )}
              <button
                onClick={scrollToTop}
                className="p-2 rounded-full bg-[var(--card)] border border-[var(--hair)] text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[var(--panel)] transition-all cursor-pointer shadow-xs"
                title="Scroll back to top"
              >
                <ArrowUp className="h-4 w-4" />
              </button>
            </div>
          </div>
        </div>

        {/* Bottom Copyright */}
        <div className="flex flex-col sm:flex-row items-center justify-between text-xs text-[var(--faint)] font-medium gap-3">
          <p>© 2026 Vellum — Fernly Botanical Bento Edition. All research data remains on your workstation.</p>
          <div className="flex items-center gap-4">
            <span>Client-Side Local-First</span>
            <span>•</span>
            <span>Free &amp; Open Source</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
