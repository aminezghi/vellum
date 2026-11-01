"use client";

import React, { useState, useEffect } from "react";
import { AcademicPaperResult } from "@/app/api/search/route";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload } from "@/lib/pdfDownloader";
import {
  Flame,
  Share2,
  BookmarkPlus,
  Zap,
  ArrowUpRight,
} from "lucide-react";

interface TrendingRadarProps {
  onAddToNotebook: (paper: AcademicPaperResult) => void;
  onInspectPaper: (paper: AcademicPaperResult) => void;
  onOpenConnectedGraph?: (seed: string) => void;
}

const DOMAINS = [
  { id: "ai", label: "AI & Machine Learning", icon: "🧠" },
  { id: "biomedicine", label: "Biomedicine & Oncology", icon: "🧬" },
  { id: "economics", label: "Economics & Society", icon: "📈" },
  { id: "environment", label: "Climate & Agronomy", icon: "🌱" },
  { id: "neuroscience", label: "Neuroscience", icon: "⚡" },
];

export function TrendingRadar({
  onAddToNotebook,
  onInspectPaper,
  onOpenConnectedGraph,
}: TrendingRadarProps) {
  const [activeDomain, setActiveDomain] = useState("ai");
  const [papers, setPapers] = useState<(AcademicPaperResult & { velocityBadge?: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [downloadStates, setDownloadStates] = useState<
    Record<string, { status: string; message: string; landingUrl?: string }>
  >({});

  const handleDownloadPdf = async (paper: AcademicPaperResult) => {
    setDownloadStates((prev) => ({
      ...prev,
      [paper.id]: { status: "resolving", message: "Resolving tiers..." },
    }));

    const res = await fetchAndStorePaperPdf(
      { doi: paper.doi, title: paper.title, pdfUrl: paper.pdfUrl },
      (status, details) => {
        setDownloadStates((prev) => ({
          ...prev,
          [paper.id]: { status, message: details || "" },
        }));
      }
    );

    if (res.success && res.blob) {
      triggerBrowserFileDownload(res.blob, paper.title);
    } else if (res.landingUrl) {
      setDownloadStates((prev) => ({
        ...prev,
        [paper.id]: {
          status: "paywalled",
          message: "Paywalled",
          landingUrl: res.landingUrl,
        },
      }));
    }
  };

  useEffect(() => {
    async function loadTrends() {
      setLoading(true);
      try {
        const res = await fetch(`/api/trends?domain=${activeDomain}`);
        if (!res.ok) throw new Error("Failed to load trends");
        const data = await res.json();
        setPapers(data.papers || []);
      } catch (err) {
        console.error("Trends error:", err);
        setPapers([]);
      } finally {
        setLoading(false);
      }
    }
    loadTrends();
  }, [activeDomain]);

  return (
    <div className="fernly-card p-6 sm:p-7 space-y-6">
      {/* Head / Mode Switcher */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[var(--hair)] pb-5">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30 shadow-xs flex-shrink-0">
            <Flame className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="text-base sm:text-lg font-bold tracking-tight text-[var(--ink)]">
                Literature Velocity &amp; Citation Radar
              </h2>
              <span className="fernly-badge badge-prog text-[10px]">
                Live Velocity
              </span>
            </div>
            <p className="text-xs text-[var(--muted)] mt-0.5 font-medium">
              Real-time high-momentum preprints, milestone discoveries, and connected clusters
            </p>
          </div>
        </div>

        {/* Current view, and a way into the citation graph */}
        <div className="flex items-center bg-[var(--panel)] p-1 rounded-full border border-[var(--hair)] self-start sm:self-auto">
          <span
            aria-current="page"
            className="px-3 py-1 rounded-full text-xs font-semibold bg-[var(--card)] text-[var(--g-800)] shadow-xs"
          >
            Velocity Feed
          </span>
          <button
            onClick={() =>
              onOpenConnectedGraph?.(
                "DeepFruits: A Fruit Detection System Using Deep Neural Networks"
              )
            }
            className="px-3 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer text-[var(--muted)] hover:text-[var(--ink)] flex items-center gap-1.5"
            title="Open Interactive Force-Directed Connected Papers Graph"
          >
            <Share2 className="h-3 w-3 text-purple-600 dark:text-purple-400" />
            <span>Connected Graph</span>
          </button>
        </div>
      </div>

      <div className="space-y-6">
        {/* Domain Category Filter Chips */}
        <div className="flex items-center gap-2 overflow-x-auto pb-1 no-scrollbar">
          {DOMAINS.map((dom) => (
            <button
              key={dom.id}
              onClick={() => setActiveDomain(dom.id)}
              className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                activeDomain === dom.id
                  ? "bg-gradient-to-b from-[var(--g-700)] to-[var(--g-950)] text-[#f1f8f4] shadow-xs"
                  : "bg-[var(--panel)] text-[var(--muted)] border border-[var(--hair)] hover:text-[var(--ink)] hover:bg-[var(--card)]"
              }`}
            >
              <span>{dom.icon}</span>
              <span>{dom.label}</span>
            </button>
          ))}
        </div>

        {/* Papers Bento Grid */}
        {loading ? (
          <div className="py-16 flex flex-col items-center justify-center space-y-2 text-[var(--muted)]">
            <div className="h-6 w-6 border-2 border-[var(--g-700)] border-t-transparent rounded-full animate-spin" aria-hidden="true" />
            <span className="text-xs font-medium animate-pulse" role="status" aria-live="polite">
              Scanning academic velocity engines...
            </span>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4" role="status" aria-live="polite" aria-label={`${papers.length} trending papers`}>
            {papers.map((p) => (
              <div
                key={p.id}
                className="fernly-card p-5 sm:p-6 flex flex-col justify-between group gap-4"
              >
                <div className="space-y-3">
                  {/* Top Row: Venue, Velocity, Citations */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <span className="px-2.5 py-0.5 rounded-full bg-[var(--panel)] border border-[var(--hair)] text-[11px] font-medium text-[var(--muted)] truncate max-w-[170px]">
                      {p.venue || "Peer-Reviewed"} · {p.year || 2024}
                    </span>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      <span className="fernly-badge badge-prog text-[10px]">
                        <Flame className="h-2.5 w-2.5" />
                        {p.velocityBadge || "High Velocity"}
                      </span>
                      <span className="fernly-badge badge-sky text-[10px] font-mono">
                        {p.citationCount || 0} cites
                      </span>
                    </div>
                  </div>

                  {/* Title & Authors */}
                  <div>
                    <h3 className="text-sm sm:text-base font-semibold text-[var(--ink)] group-hover:text-[var(--g-700)] transition-colors line-clamp-2 leading-snug tracking-tight">
                      {p.title}
                    </h3>
                    <p className="text-xs text-[var(--muted)] mt-1 font-medium">
                      {p.authors?.slice(0, 2).join(", ")}
                      {p.authors && p.authors.length > 2 ? " et al." : ""}
                    </p>
                  </div>

                  {/* Abstract Quote */}
                  {p.abstract && (
                    <div className="bg-[var(--panel)] p-3 rounded-2xl border border-[var(--hair)]">
                      <p className="text-xs text-[var(--muted)] line-clamp-2 leading-relaxed">
                        {p.abstract}
                      </p>
                    </div>
                  )}
                </div>

                {/* Actions Row */}
                <div className="flex flex-wrap items-center justify-between pt-3 border-t border-[var(--hair)] gap-2">
                  <button
                    onClick={() => {
                      const target = p.doi || p.title;
                      if (onOpenConnectedGraph && target) {
                        onOpenConnectedGraph(target);
                      }
                    }}
                    className="text-[11px] text-purple-700 dark:text-purple-400 hover:underline flex items-center gap-1 font-semibold cursor-pointer"
                    title="Explore Connected Papers graph for this work"
                  >
                    <Share2 className="h-3 w-3" /> Map cluster
                  </button>

                  <div className="flex items-center gap-1.5">
                    {/* Download PDF button */}
                    {downloadStates[p.id] ? (
                      <span className="text-[10px] text-[var(--g-800)] px-2.5 py-1 rounded-full bg-[var(--g-100)] border border-[var(--g-400)]/30 font-semibold animate-pulse">
                        {downloadStates[p.id].message}
                      </span>
                    ) : (
                      <button
                        onClick={() => handleDownloadPdf(p)}
                        className="px-3 py-1.5 rounded-full bg-gradient-to-b from-[var(--g-700)] to-[var(--g-950)] text-[#f1f8f4] text-[11px] font-semibold flex items-center gap-1 transition-all cursor-pointer shadow-xs hover:scale-[1.02] active:scale-[0.98]"
                        title="Instant multi-source PDF download"
                      >
                        <Zap className="h-3 w-3 text-[#5dbd8b]" />
                        <span>PDF</span>
                      </button>
                    )}

                    <button
                      onClick={() => onAddToNotebook(p)}
                      className="px-3 py-1.5 rounded-full bg-[var(--panel)] hover:bg-[var(--g-100)] text-[var(--ink)] border border-[var(--hair)] text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer shadow-xs"
                    >
                      <BookmarkPlus className="h-3 w-3" />
                      <span>Add</span>
                    </button>

                    {/* Fernly Signature Rotating Arrow Pill */}
                    <button
                      onClick={() => onInspectPaper(p)}
                      className="fernly-arrow !w-7 !h-7 !border-[var(--hair)] text-[var(--ink)] hover:!bg-[var(--g-700)] hover:!text-white hover:!border-[var(--g-700)]"
                      title="Deep Systematic Appraisal"
                    >
                      <ArrowUpRight className="h-3.5 w-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
