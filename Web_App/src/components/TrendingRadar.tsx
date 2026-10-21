"use client";

import React, { useState, useEffect } from "react";
import { AcademicPaperResult } from "@/app/api/search/route";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload } from "@/lib/pdfDownloader";
import {
  Flame,
  TrendingUp,
  Share2,
  Sparkles,
  BookmarkPlus,
  BookOpen,
  ArrowRight,
  ExternalLink,
  Layers,
  Search,
  Zap,
  CheckCircle2,
  AlertCircle,
} from "lucide-react";

interface TrendingRadarProps {
  onAddToNotebook: (paper: AcademicPaperResult) => void;
  onInspectPaper: (paper: AcademicPaperResult) => void;
}

const DOMAINS = [
  { id: "ai", label: "AI & Machine Learning", icon: "🧠" },
  { id: "biomedicine", label: "Biomedicine & Oncology", icon: "🧬" },
  { id: "economics", label: "Economics & Consumer Behavior", icon: "📈" },
  { id: "environment", label: "Climate & Agronomy", icon: "🌱" },
  { id: "neuroscience", label: "Neuroscience", icon: "⚡" },
];

export function TrendingRadar({ onAddToNotebook, onInspectPaper }: TrendingRadarProps) {
  const [activeDomain, setActiveDomain] = useState("ai");
  const [papers, setPapers] = useState<(AcademicPaperResult & { velocityBadge?: string })[]>([]);
  const [loading, setLoading] = useState(true);
  const [viewMode, setViewMode] = useState<"trends" | "connected">("trends");
  const [seedDoi, setSeedDoi] = useState("");
  const [connectedResults, setConnectedResults] = useState<{
    seedTitle?: string;
    related: AcademicPaperResult[];
  } | null>(null);
  const [connectedLoading, setConnectedLoading] = useState(false);
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

  const handleConnectedSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!seedDoi.trim()) return;
    setConnectedLoading(true);
    try {
      const res = await fetch(`/api/connected?doi=${encodeURIComponent(seedDoi.trim())}`);
      if (!res.ok) throw new Error("Connected papers lookup failed");
      const data = await res.json();
      setConnectedResults(data);
    } catch (err) {
      console.error("Connected search error:", err);
      setConnectedResults(null);
    } finally {
      setConnectedLoading(false);
    }
  };

  return (
    <div className="w-full bg-white/95 dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 rounded-[2rem] p-5 sm:p-7 mb-8 shadow-xs transition-colors duration-200">
      {/* Consistent Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 pb-4 border-b border-[#1a1a1a]/8 dark:border-white/10 mb-5">
        <div className="flex items-start sm:items-center gap-3">
          <div className="flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center rounded-2xl bg-[#034f46] text-[#ffffeb] shadow-xs flex-shrink-0">
            <Flame className="h-5 w-5 text-[#ffa946]" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base sm:text-lg font-bold tracking-tight text-[#1a1a1a] dark:text-[#ffffeb]">
                Trending Research Radar &amp; Discovery
              </h2>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#ffa946]/15 text-[#994800] dark:text-[#ffa946] border border-[#ffa946]/30">
                Momentum Radar
              </span>
            </div>
            <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-0.5 font-medium leading-relaxed">
              Surfacing high-velocity breakthrough papers, rising topics, and citation clusters across scientific fields
            </p>
          </div>
        </div>

        {/* Mode Toggle */}
        <div className="flex items-center bg-[#1a1a1a]/5 dark:bg-white/5 border border-[#1a1a1a]/10 dark:border-white/10 rounded-full p-1 text-xs self-start sm:self-auto">
          <button
            onClick={() => setViewMode("trends")}
            className={`px-3.5 py-1.5 rounded-full font-semibold transition-all cursor-pointer ${
              viewMode === "trends"
                ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                : "text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a] dark:hover:text-white"
            }`}
          >
            🔥 Momentum Streams
          </button>
          <button
            onClick={() => setViewMode("connected")}
            className={`px-3.5 py-1.5 rounded-full font-semibold transition-all cursor-pointer ${
              viewMode === "connected"
                ? "bg-[#034f46] text-[#ffffeb] shadow-xs"
                : "text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a] dark:hover:text-white"
            }`}
          >
            🌐 Connected Citation Radar
          </button>
        </div>
      </div>

      {viewMode === "trends" ? (
        <div>
          {/* Domain Category Selector Pills */}
          <div className="flex items-center gap-2 overflow-x-auto pb-2 mb-4 scrollbar-none">
            {DOMAINS.map((d) => {
              const isActive = activeDomain === d.id;
              return (
                <button
                  key={d.id}
                  onClick={() => setActiveDomain(d.id)}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                    isActive
                      ? "bg-[#034f46] text-[#ffffeb] shadow-sm"
                      : "bg-[#ffffeb] dark:bg-[#121413] hover:bg-white dark:hover:bg-[#252a27] text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white border border-[#1a1a1a]/10 dark:border-white/10"
                  }`}
                >
                  <span>{d.icon}</span>
                  <span>{d.label}</span>
                </button>
              );
            })}
          </div>

          {/* Trending Papers Grid */}
          {loading ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-2">
              <div className="h-6 w-6 border-2 border-[#034f46] dark:border-[#23a07a] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-[#1a1a1a]/60 dark:text-white/60 animate-pulse font-medium">
                Fetching high-momentum publications for 2024-2026...
              </span>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
              {papers.map((p) => (
                <div
                  key={p.id}
                  className="p-5 sm:p-6 rounded-[1.75rem] bg-white dark:bg-[#121413] border border-[#1a1a1a]/10 dark:border-white/10 hover:border-[#034f46]/35 dark:hover:border-[#23a07a]/40 hover:shadow-md transition-all duration-200 flex flex-col justify-between group shadow-xs gap-3.5"
                >
                  <div className="space-y-2.5">
                    {/* Top Row: Venue, Velocity, and Citations */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                      <span className="px-2.5 py-0.5 rounded-full bg-[#ffffeb] dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 text-[11px] font-medium text-[#1a1a1a]/80 dark:text-white/80 truncate max-w-[170px]">
                        {p.venue || "Journal"} · {p.year}
                      </span>

                      <div className="flex items-center gap-1.5 flex-shrink-0">
                        <span className="px-2.5 py-0.5 rounded-full bg-[#ffa946]/15 text-[#994800] dark:text-[#ffa946] border border-[#ffa946]/30 text-[10px] font-semibold flex items-center gap-1">
                          <Flame className="h-2.5 w-2.5" />
                          {p.velocityBadge || "High Velocity"}
                        </span>
                        <span className="px-2.5 py-0.5 rounded-full bg-[#f0d7ff] dark:bg-[#4a154b]/50 text-[#4a154b] dark:text-[#f0d7ff] text-[10px] font-mono font-medium">
                          {p.citationCount}
                        </span>
                      </div>
                    </div>

                    {/* Title & Authors */}
                    <div>
                      <h3 className="text-sm sm:text-base font-semibold text-[#1a1a1a] dark:text-white group-hover:text-[#034f46] dark:group-hover:text-[#23a07a] transition-colors line-clamp-2 leading-snug tracking-tight">
                        {p.title}
                      </h3>
                      <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-1 font-medium">
                        {p.authors?.slice(0, 2).join(", ")}
                        {p.authors?.length > 2 ? " et al." : ""}
                      </p>
                    </div>

                    {/* Abstract Quote in Serif */}
                    {p.abstract && (
                      <div className="bg-[#fbfbf6] dark:bg-[#181c1a] p-3 rounded-2xl border border-[#1a1a1a]/6 dark:border-white/5">
                        <p className="text-xs text-[#1a1a1a]/75 dark:text-white/75 font-serif line-clamp-2 leading-relaxed">
                          {p.abstract}
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Actions Row */}
                  <div className="flex flex-wrap items-center justify-between pt-3 border-t border-[#1a1a1a]/8 dark:border-white/10 gap-2">
                    <button
                      onClick={() => {
                        if (p.doi) {
                          setSeedDoi(p.doi);
                          setViewMode("connected");
                        }
                      }}
                      className="text-[11px] text-[#034f46] dark:text-[#cef5ca] hover:underline flex items-center gap-1 font-semibold cursor-pointer"
                    >
                      <Share2 className="h-3 w-3" /> Find connected
                    </button>

                    <div className="flex items-center gap-1.5">
                      {/* Download PDF button */}
                      {downloadStates[p.id] ? (
                        <span className="text-[10px] text-[#034f46] dark:text-[#cef5ca] animate-pulse px-2.5 py-1 rounded-full bg-[#ffffeb] dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 font-medium">
                          {downloadStates[p.id].message}
                        </span>
                      ) : (
                        <button
                          onClick={() => handleDownloadPdf(p)}
                          className="px-3 py-1.5 rounded-full bg-[#034f46] hover:bg-[#023630] text-[#ffffeb] text-[11px] font-semibold flex items-center gap-1 transition-all cursor-pointer shadow-xs hover:scale-[1.02] active:scale-[0.98]"
                          title="Download PDF across Springer, Nature, Unpaywall, Semantic Scholar & Sci-Hub"
                        >
                          <Zap className="h-3 w-3 text-[#cef5ca]" />
                          <span>PDF</span>
                        </button>
                      )}

                      <button
                        onClick={() => onAddToNotebook(p)}
                        className="px-3 py-1.5 rounded-full bg-[#cef5ca] hover:bg-[#b8f0b4] text-[#114e0b] dark:bg-[#034f46] dark:text-[#cef5ca] text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer shadow-xs"
                      >
                        <BookmarkPlus className="h-3 w-3" />
                        <span>Add</span>
                      </button>
                      <button
                        onClick={() => onInspectPaper(p)}
                        className="px-3 py-1.5 rounded-full bg-white dark:bg-[#1a1e1c] hover:bg-[#ffffeb] dark:hover:bg-[#252a27] text-[#1a1a1a] dark:text-white border border-[#1a1a1a]/15 dark:border-white/15 text-[11px] font-medium flex items-center gap-1 transition-colors cursor-pointer shadow-xs"
                      >
                        <BookOpen className="h-3 w-3 text-[#034f46] dark:text-[#23a07a]" />
                        <span>Inspect</span>
                      </button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        /* Connected Papers Radar View */
        <div className="space-y-4">
          <form onSubmit={handleConnectedSearch} className="flex gap-2.5">
            <div className="relative flex-1">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#1a1a1a]/40" />
              <input
                type="text"
                value={seedDoi}
                onChange={(e) => setSeedDoi(e.target.value)}
                placeholder="Enter a seed DOI (e.g. 10.1016/S2214-109X(23)00000-0) to map related citation clusters..."
                className="w-full pl-11 pr-4 py-2.5 bg-[#ffffeb]/70 border border-[#1a1a1a]/15 rounded-full text-xs sm:text-sm text-[#1a1a1a] placeholder-[#1a1a1a]/40 focus:outline-none focus:border-[#034f46] focus:ring-1 focus:ring-[#034f46]/20 font-medium"
              />
            </div>
            <button
              type="submit"
              disabled={connectedLoading || !seedDoi.trim()}
              className="px-5 py-2.5 rounded-full bg-[#034f46] hover:bg-[#023630] text-[#ffffeb] text-xs font-semibold disabled:opacity-50 transition-all cursor-pointer flex-shrink-0 shadow-sm"
            >
              {connectedLoading ? "Mapping..." : "Map Citation Cluster"}
            </button>
          </form>

          {connectedLoading ? (
            <div className="py-12 flex flex-col items-center justify-center space-y-2">
              <div className="h-6 w-6 border-2 border-[#034f46] border-t-transparent rounded-full animate-spin" />
              <span className="text-xs text-[#1a1a1a]/60 animate-pulse font-medium">
                Mapping citation graph, co-citations, and foundational ancestors...
              </span>
            </div>
          ) : connectedResults ? (
            <div className="space-y-3">
              <div className="p-3.5 bg-[#cef5ca]/60 border border-[#114e0b]/20 rounded-2xl text-xs text-[#114e0b]">
                <span className="font-bold">Seed Paper:</span>{" "}
                {connectedResults.seedTitle || seedDoi}
              </div>

              <h4 className="text-xs font-semibold text-[#1a1a1a] mt-2">
                Connected Seminal &amp; Derivative Papers ({connectedResults.related?.length || 0})
              </h4>

              <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4">
                {connectedResults.related?.map((rp) => (
                  <div
                    key={rp.id}
                    className="p-5 sm:p-6 rounded-[1.75rem] bg-white border border-[#1a1a1a]/10 hover:border-[#034f46]/35 hover:shadow-md transition-all duration-200 flex flex-col justify-between group shadow-xs gap-3.5"
                  >
                    <div className="space-y-2.5">
                      <div className="flex items-center justify-between gap-2 flex-wrap">
                        <span className="px-2.5 py-0.5 rounded-full bg-[#ffffeb] border border-[#1a1a1a]/10 text-[11px] font-medium text-[#1a1a1a]/80 truncate max-w-[170px]">
                          {rp.venue || "Journal"} · {rp.year}
                        </span>
                        <span className="px-2.5 py-0.5 rounded-full bg-[#f0d7ff] text-[#4a154b] text-[10px] font-mono font-medium">
                          {rp.citationCount} cites
                        </span>
                      </div>

                      <div>
                        <h5 className="text-sm sm:text-base font-semibold text-[#1a1a1a] group-hover:text-[#034f46] transition-colors line-clamp-2 leading-snug tracking-tight">
                          {rp.title}
                        </h5>
                        <p className="text-xs text-[#1a1a1a]/60 mt-1 font-medium truncate">
                          {rp.authors?.join(", ")}
                        </p>
                      </div>

                      {rp.abstract && (
                        <div className="bg-[#fbfbf6] p-3 rounded-2xl border border-[#1a1a1a]/6">
                          <p className="text-xs text-[#1a1a1a]/75 font-serif line-clamp-2 leading-relaxed">
                            {rp.abstract}
                          </p>
                        </div>
                      )}
                    </div>

                    <div className="flex flex-wrap items-center justify-end pt-3 border-t border-[#1a1a1a]/8 gap-1.5">
                      {downloadStates[rp.id] ? (
                        <span className="text-[10px] text-[#034f46] animate-pulse px-2.5 py-1 rounded-full bg-[#ffffeb] border border-[#1a1a1a]/15 font-medium">
                          {downloadStates[rp.id].message}
                        </span>
                      ) : (
                        <button
                          onClick={() => handleDownloadPdf(rp)}
                          className="px-3 py-1.5 rounded-full bg-[#034f46] hover:bg-[#023630] text-[#ffffeb] text-[11px] font-semibold flex items-center gap-1 transition-all cursor-pointer shadow-xs hover:scale-[1.02] active:scale-[0.98]"
                          title="Download PDF"
                        >
                          <Zap className="h-3 w-3 text-[#cef5ca]" />
                          <span>PDF</span>
                        </button>
                      )}

                      <button
                        onClick={() => onAddToNotebook(rp)}
                        className="px-3 py-1.5 rounded-full bg-[#cef5ca] hover:bg-[#b8f0b4] text-[#114e0b] text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer shadow-xs"
                      >
                        <BookmarkPlus className="h-3 w-3" />
                        <span>Add</span>
                      </button>
                      <button
                        onClick={() => onInspectPaper(rp)}
                        className="px-3 py-1.5 rounded-full bg-white hover:bg-[#ffffeb] text-[#1a1a1a] border border-[#1a1a1a]/15 text-[11px] font-medium flex items-center gap-1 transition-colors cursor-pointer shadow-xs"
                      >
                        <BookOpen className="h-3 w-3 text-[#034f46]" />
                        <span>Inspect</span>
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-xs text-[#1a1a1a]/50 py-6 text-center font-medium">
              Enter any paper's DOI or click "Find connected papers" on any trending paper to discover its citation cluster.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
