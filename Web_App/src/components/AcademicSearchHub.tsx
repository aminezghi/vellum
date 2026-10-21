"use client";

import React, { useState, useEffect } from "react";
import { AcademicPaperResult } from "@/app/api/search/route";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload } from "@/lib/pdfDownloader";
import { TokensModal, CustomTokens } from "./TokensModal";
import {
  Search,
  SlidersHorizontal,
  FileText,
  Download,
  BookmarkPlus,
  BookOpen,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Layers,
  Zap,
  CheckCircle2,
  AlertCircle,
  Key,
  Database,
  Filter,
  Check,
  RotateCcw,
} from "lucide-react";

interface AcademicSearchHubProps {
  onAddToNotebook: (paper: AcademicPaperResult) => void;
  onInspectPaper: (paper: AcademicPaperResult) => void;
}

const POPULAR_QUERIES = [
  "Animal welfare & consumer demand",
  "Large language models reasoning",
  "Non-communicable disease policy",
  "CRISPR gene editing in oncology",
  "Agricultural climate resilience",
];

const AVAILABLE_SOURCES = [
  { id: "openalex", label: "OpenAlex (250M+)", badge: "Global Corpus", color: "bg-[#034f46] text-[#ffffeb]" },
  { id: "arxiv", label: "arXiv (Preprints)", badge: "Preprints", color: "bg-[#ffa946]/20 text-[#994800] dark:text-[#ffa946]" },
  { id: "semanticscholar", label: "Semantic Scholar", badge: "AI Graph", color: "bg-[#f0d7ff] text-[#4a154b] dark:bg-[#4a154b]/40 dark:text-[#f0d7ff]" },
  { id: "crossref", label: "Crossref", badge: "Publishers", color: "bg-[#cef5ca] text-[#114e0b] dark:bg-[#034f46]/40 dark:text-[#cef5ca]" },
];

export function AcademicSearchHub({ onAddToNotebook, onInspectPaper }: AcademicSearchHubProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AcademicPaperResult[]>([]);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [openAccessOnly, setOpenAccessOnly] = useState(false);
  const [fromYear, setFromYear] = useState("2018");
  const [sortBy, setSortBy] = useState("relevance");
  const [showFilters, setShowFilters] = useState(false);
  const [showAdvancedBuilder, setShowAdvancedBuilder] = useState(false);
  const [showTokensModal, setShowTokensModal] = useState(false);
  const [hasCustomTokens, setHasCustomTokens] = useState(false);

  // Source selections
  const [selectedSources, setSelectedSources] = useState<string[]>([
    "openalex",
    "arxiv",
    "semanticscholar",
  ]);

  // Advanced query builder fields
  const [fieldScope, setFieldScope] = useState<"all" | "title" | "author" | "doi">("all");
  const [mustInclude, setMustInclude] = useState("");
  const [anyInclude, setAnyInclude] = useState("");
  const [mustExclude, setMustExclude] = useState("");
  const [exactPhrase, setExactPhrase] = useState("");
  const [authorQuery, setAuthorQuery] = useState("");
  const [doiQuery, setDoiQuery] = useState("");

  const [expandedAbstracts, setExpandedAbstracts] = useState<Record<string, boolean>>({});
  const [downloadStates, setDownloadStates] = useState<
    Record<string, { status: string; message: string; landingUrl?: string }>
  >({});

  // Check custom tokens on mount
  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("vellum-custom-tokens");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          const hasAny = Object.values(parsed).some((v) => !!v && (v as string).trim().length > 0);
          setHasCustomTokens(hasAny);
        } catch {}
      }
    }
  }, []);

  const toggleSource = (sourceId: string) => {
    setSelectedSources((prev) => {
      if (prev.includes(sourceId)) {
        if (prev.length === 1) return prev; // Keep at least one
        return prev.filter((s) => s !== sourceId);
      } else {
        return [...prev, sourceId];
      }
    });
  };

  const handleDownloadPdf = async (paper: AcademicPaperResult) => {
    setDownloadStates((prev) => ({
      ...prev,
      [paper.id]: { status: "resolving", message: "Resolving multi-tier sources..." },
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
          message: "Publisher paywalled",
          landingUrl: res.landingUrl,
        },
      }));
    }
  };

  const handleSearch = async (searchQuery: string = query) => {
    const activeQ = searchQuery.trim() || mustInclude.trim() || exactPhrase.trim() || doiQuery.trim() || query.trim();
    if (!activeQ && !authorQuery.trim()) return;

    setLoading(true);
    setQuery(searchQuery || query);

    try {
      const params = new URLSearchParams({
        q: searchQuery.trim() || query.trim(),
        sources: selectedSources.join(","),
        oa: openAccessOnly ? "true" : "false",
        fromYear,
        toYear: new Date().getFullYear().toString(),
        sortBy,
        field: fieldScope,
      });

      if (mustInclude.trim()) params.set("mustInclude", mustInclude.trim());
      if (anyInclude.trim()) params.set("anyInclude", anyInclude.trim());
      if (mustExclude.trim()) params.set("mustExclude", mustExclude.trim());
      if (exactPhrase.trim()) params.set("exactPhrase", exactPhrase.trim());
      if (authorQuery.trim()) params.set("author", authorQuery.trim());
      if (doiQuery.trim()) params.set("doi", doiQuery.trim());

      // Read custom tokens
      let headers: Record<string, string> = {};
      if (typeof window !== "undefined") {
        const stored = localStorage.getItem("vellum-custom-tokens");
        if (stored) {
          try {
            const tokens: CustomTokens = JSON.parse(stored);
            if (tokens.openAlexToken) headers["x-token-openalex"] = tokens.openAlexToken;
            if (tokens.semanticScholarKey) headers["x-token-semanticscholar"] = tokens.semanticScholarKey;
            if (tokens.crossrefEmail) headers["x-token-crossref"] = tokens.crossrefEmail;
          } catch {}
        }
      }

      const res = await fetch(`/api/search?${params.toString()}`, { headers });
      if (!res.ok) throw new Error("Search request failed");
      const data = await res.json();
      setResults(data.results || []);
      setTotalCount(data.total || 0);
    } catch (err) {
      console.error("Search failed:", err);
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  const resetAdvancedBuilder = () => {
    setMustInclude("");
    setAnyInclude("");
    setMustExclude("");
    setExactPhrase("");
    setAuthorQuery("");
    setDoiQuery("");
    setFieldScope("all");
  };

  const toggleAbstract = (id: string) => {
    setExpandedAbstracts((prev) => ({ ...prev, [id]: !prev[id] }));
  };

  return (
    <div className="w-full bg-white/95 dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10 rounded-[2rem] p-5 sm:p-7 mb-8 shadow-xs transition-colors duration-200">
      {/* Consistent Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 pb-4 border-b border-[#1a1a1a]/8 dark:border-white/10 mb-5">
        <div className="flex items-start sm:items-center gap-3">
          <div className="flex h-10 w-10 sm:h-11 sm:w-11 items-center justify-center rounded-2xl bg-[#034f46] text-[#ffffeb] shadow-xs flex-shrink-0">
            <Search className="h-5 w-5 text-[#cef5ca]" />
          </div>
          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h2 className="text-base sm:text-lg font-bold tracking-tight text-[#1a1a1a] dark:text-[#ffffeb]">
                Live Academic Literature Search
              </h2>
              <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-[#cef5ca] text-[#114e0b] dark:bg-[#034f46] dark:text-[#cef5ca] border border-[#114e0b]/20">
                250M+ Multi-Source Corpus
              </span>
            </div>
            <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-0.5 font-medium leading-relaxed">
              Multi-source querying across OpenAlex, arXiv, Semantic Scholar, and Crossref with direct PDF discovery
            </p>
          </div>
        </div>

        {/* Action Controls Header */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {/* API / Tokens Button */}
          <button
            onClick={() => setShowTokensModal(true)}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all cursor-pointer shadow-xs ${
              hasCustomTokens
                ? "bg-[#cef5ca] text-[#114e0b] border-[#114e0b]/20 dark:bg-[#034f46] dark:text-[#cef5ca]"
                : "bg-white dark:bg-[#121413] border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white hover:bg-[#ffffeb] dark:hover:bg-white/5"
            }`}
            title="Configure OpenAlex, Semantic Scholar & PubMed API tokens"
          >
            <Key className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">API Tokens</span>
            {hasCustomTokens && <span className="h-1.5 w-1.5 rounded-full bg-[#34c759]" />}
          </button>

          {/* Advanced Query Builder Toggle */}
          <button
            onClick={() => setShowAdvancedBuilder(!showAdvancedBuilder)}
            className={`apple-press flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all cursor-pointer shadow-xs ${
              showAdvancedBuilder || mustInclude || exactPhrase || authorQuery || doiQuery
                ? "bg-[#0071e3] dark:bg-[#0a84ff] text-white border-transparent"
                : "bg-white/70 dark:bg-white/10 border-black/15 dark:border-white/15 text-[#1a1a1a] dark:text-white hover:bg-white dark:hover:bg-white/20"
            }`}
          >
            <Filter className="h-3.5 w-3.5" />
            <span>Advanced Search</span>
            {(mustInclude || exactPhrase || authorQuery || doiQuery) && (
              <span className="h-1.5 w-1.5 rounded-full bg-white" />
            )}
          </button>

          {/* Quick Filters Toggle */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={`apple-press flex items-center gap-1.5 px-3 py-1.5 rounded-full border text-xs font-semibold transition-all cursor-pointer shadow-xs ${
              showFilters || openAccessOnly || fromYear !== "2018"
                ? "bg-[#0071e3] dark:bg-[#0a84ff] text-white border-transparent"
                : "bg-white/70 dark:bg-white/10 border-black/15 dark:border-white/15 text-[#1a1a1a] dark:text-white hover:bg-white dark:hover:bg-white/20"
            }`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Source Selection Pill Bar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold text-[#1a1a1a]/60 dark:text-white/60 flex items-center gap-1 mr-1">
          <Database className="h-3.5 w-3.5 text-[#034f46] dark:text-[#23a07a]" />
          <span>Active Sources:</span>
        </span>
        {AVAILABLE_SOURCES.map((src) => {
          const isSelected = selectedSources.includes(src.id);
          return (
            <button
              key={src.id}
              onClick={() => toggleSource(src.id)}
              className={`apple-press flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer border ${
                isSelected
                  ? "bg-[#ffffeb] dark:bg-[#121413] border-[#034f46] dark:border-[#23a07a] text-[#1a1a1a] dark:text-white shadow-xs"
                  : "bg-transparent border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a]/50 dark:text-white/40 hover:border-[#1a1a1a]/30"
              }`}
            >
              <div
                className={`h-2 w-2 rounded-full ${
                  isSelected ? "bg-[#034f46] dark:bg-[#23a07a]" : "bg-transparent border border-[#1a1a1a]/40 dark:border-white/40"
                }`}
              />
              <span>{src.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Search Input Form */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
        className="relative flex items-center gap-2.5"
      >
        <div className="relative flex-1 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[#1a1a1a]/40 dark:text-white/40 group-focus-within:text-[#0071e3] transition-colors" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search keywords, topics, author names, or paste a DOI..."
            className="w-full pl-11 pr-4 py-3 bg-white/80 dark:bg-black/40 backdrop-blur-xl border border-black/10 dark:border-white/15 rounded-full text-xs sm:text-sm text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/40 dark:placeholder-white/35 focus:outline-none focus:border-[#0071e3] dark:focus:border-[#0a84ff] focus:ring-4 focus:ring-[#0071e3]/15 transition-all shadow-sm"
          />
        </div>
        <button
          type="submit"
          disabled={loading || (!query.trim() && !mustInclude && !exactPhrase && !doiQuery && !authorQuery)}
          className="apple-press px-6 py-3 rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-white text-xs sm:text-sm font-semibold shadow-sm disabled:opacity-50 transition-all cursor-pointer flex-shrink-0"
        >
          {loading ? "Searching..." : "Search"}
        </button>
      </form>

      {/* Advanced Search & Boolean Query Builder Drawer */}
      {showAdvancedBuilder && (
        <div className="mt-4 p-5 rounded-2xl bg-[#ffffeb]/70 dark:bg-[#121413]/70 border border-[#1a1a1a]/10 dark:border-white/10 space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          <div className="flex items-center justify-between pb-2 border-b border-[#1a1a1a]/8 dark:border-white/10">
            <span className="text-xs font-bold text-[#1a1a1a] dark:text-white flex items-center gap-1.5">
              <Sparkles className="h-3.5 w-3.5 text-[#ffa946]" />
              <span>Boolean Operators &amp; Field Targeting</span>
            </span>
            <button
              onClick={resetAdvancedBuilder}
              className="text-[11px] text-[#1a1a1a]/60 dark:text-white/60 hover:text-red-600 dark:hover:text-red-400 flex items-center gap-1 cursor-pointer font-medium"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset fields</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 text-xs">
            {/* Must Include ALL (AND) */}
            <div className="space-y-1">
              <label className="font-semibold text-[#1a1a1a] dark:text-white flex items-center justify-between">
                <span>Must include ALL words (AND):</span>
                <span className="text-[10px] text-[#034f46] dark:text-[#cef5ca]">Required</span>
              </label>
              <input
                type="text"
                value={mustInclude}
                onChange={(e) => setMustInclude(e.target.value)}
                placeholder="e.g. reasoning alignment safety"
                className="w-full px-3 py-1.5 rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
              />
            </div>

            {/* Must Include ANY (OR) */}
            <div className="space-y-1">
              <label className="font-semibold text-[#1a1a1a] dark:text-white">
                Include ANY of these words (OR):
              </label>
              <input
                type="text"
                value={anyInclude}
                onChange={(e) => setAnyInclude(e.target.value)}
                placeholder="e.g. ethics governance oversight"
                className="w-full px-3 py-1.5 rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
              />
            </div>

            {/* Must EXCLUDE (NOT) */}
            <div className="space-y-1">
              <label className="font-semibold text-[#1a1a1a] dark:text-white flex items-center justify-between">
                <span>Must EXCLUDE words (NOT):</span>
                <span className="text-[10px] text-red-600 dark:text-red-400">Purge</span>
              </label>
              <input
                type="text"
                value={mustExclude}
                onChange={(e) => setMustExclude(e.target.value)}
                placeholder="e.g. survey overview editorial"
                className="w-full px-3 py-1.5 rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
              />
            </div>

            {/* Exact Phrase Match */}
            <div className="space-y-1">
              <label className="font-semibold text-[#1a1a1a] dark:text-white">
                Exact Phrase (&quot;quotes&quot;):
              </label>
              <input
                type="text"
                value={exactPhrase}
                onChange={(e) => setExactPhrase(e.target.value)}
                placeholder='e.g. "large language models"'
                className="w-full px-3 py-1.5 rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
              />
            </div>

            {/* Author Specific Query */}
            <div className="space-y-1">
              <label className="font-semibold text-[#1a1a1a] dark:text-white">
                Specific Author Name:
              </label>
              <input
                type="text"
                value={authorQuery}
                onChange={(e) => setAuthorQuery(e.target.value)}
                placeholder="e.g. Geoffrey Hinton, Yann LeCun"
                className="w-full px-3 py-1.5 rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
              />
            </div>

            {/* Direct DOI Lookup */}
            <div className="space-y-1">
              <label className="font-semibold text-[#1a1a1a] dark:text-white">
                Direct DOI (Digital Object Identifier):
              </label>
              <input
                type="text"
                value={doiQuery}
                onChange={(e) => setDoiQuery(e.target.value)}
                placeholder="e.g. 10.1038/s41586-023-00000-0"
                className="w-full px-3 py-1.5 rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
              />
            </div>
          </div>

          <div className="flex items-center justify-between pt-2">
            <div className="flex items-center gap-2">
              <span className="text-[11px] text-[#1a1a1a]/60 dark:text-white/60 font-medium">Match scope:</span>
              <div className="flex items-center gap-1 bg-white dark:bg-[#1a1e1c] p-0.5 rounded-full border border-[#1a1a1a]/10 dark:border-white/10 text-[11px]">
                {(["all", "title", "author", "doi"] as const).map((sc) => (
                  <button
                    key={sc}
                    onClick={() => setFieldScope(sc)}
                    className={`px-2.5 py-0.5 rounded-full capitalize transition-all cursor-pointer ${
                      fieldScope === sc
                        ? "bg-[#034f46] text-[#ffffeb] font-semibold"
                        : "text-[#1a1a1a]/60 dark:text-white/60 hover:text-[#1a1a1a]"
                    }`}
                  >
                    {sc === "all" ? "All fields" : sc}
                  </button>
                ))}
              </div>
            </div>

            <button
              onClick={() => handleSearch()}
              className="px-4 py-1.5 rounded-full bg-[#034f46] hover:bg-[#023630] text-[#ffffeb] text-xs font-semibold shadow-xs cursor-pointer transition-all"
            >
              Run Combined Query
            </button>
          </div>
        </div>
      )}

      {/* Collapsible Filter Bar */}
      {showFilters && (
        <div className="mt-4 p-4 rounded-2xl bg-[#ffffeb]/70 dark:bg-[#121413]/70 border border-[#1a1a1a]/10 dark:border-white/10 flex flex-wrap items-center gap-4 text-xs text-[#1a1a1a] dark:text-white">
          <label className="flex items-center gap-2 cursor-pointer select-none">
            <input
              type="checkbox"
              checked={openAccessOnly}
              onChange={(e) => setOpenAccessOnly(e.target.checked)}
              className="rounded border-[#1a1a1a]/30 text-[#034f46] focus:ring-0"
            />
            <span className="font-semibold text-xs">Open Access PDF only</span>
          </label>

          <div className="flex items-center gap-1.5">
            <span className="text-[#1a1a1a]/60 dark:text-white/60 font-medium">From Year:</span>
            <select
              value={fromYear}
              onChange={(e) => setFromYear(e.target.value)}
              className="bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 rounded-full px-3 py-1 text-xs text-[#1a1a1a] dark:text-white focus:outline-none font-medium"
            >
              <option value="2026">2026 (Current)</option>
              <option value="2024">2024</option>
              <option value="2022">2022+</option>
              <option value="2020">2020+</option>
              <option value="2018">2018+</option>
              <option value="2010">2010+</option>
              <option value="2000">2000+</option>
            </select>
          </div>

          <div className="flex items-center gap-1.5">
            <span className="text-[#1a1a1a]/60 dark:text-white/60 font-medium">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 rounded-full px-3 py-1 text-xs text-[#1a1a1a] dark:text-white focus:outline-none font-medium"
            >
              <option value="relevance">Relevance</option>
              <option value="citations">Most Cited</option>
              <option value="date">Newest First</option>
            </select>
          </div>
        </div>
      )}

      {/* Suggested Topic Chips */}
      {!results.length && !loading && (
        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-[#1a1a1a]/50 dark:text-white/40 mr-1 flex items-center gap-1 font-medium">
            <Sparkles className="h-3 w-3 text-[#0071e3] dark:text-[#0a84ff]" /> Suggested:
          </span>
          {POPULAR_QUERIES.map((q) => (
            <button
              key={q}
              onClick={() => handleSearch(q)}
              className="apple-press px-3 py-1 rounded-full bg-white/70 dark:bg-white/10 hover:bg-white dark:hover:bg-white/20 text-[11px] text-[#1a1a1a]/80 dark:text-white/80 hover:text-[#0071e3] dark:hover:text-[#0a84ff] border border-black/10 dark:border-white/15 transition-all cursor-pointer font-medium"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Results Header */}
      {totalCount !== null && (
        <div className="mt-6 pt-4 border-t border-black/8 dark:border-white/10 flex items-center justify-between">
          <span className="text-xs font-semibold text-[#1a1a1a]/80 dark:text-white/80">
            {results.length} papers retrieved across {selectedSources.length} sources
          </span>
          <span className="text-[11px] text-[#1a1a1a]/50 dark:text-white/40">
            Multi-Tier PDF &amp; Citation Resolver
          </span>
        </div>
      )}

      {/* Paper Results Grid (Fluid Full Screen Responsive) */}
      {loading ? (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <div className="h-8 w-8 border-2 border-[#0071e3] dark:border-[#0a84ff] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-[#1a1a1a]/60 dark:text-white/60 animate-pulse font-medium">
            Querying {selectedSources.join(", ")} and resolving open-access preprints...
          </span>
        </div>
      ) : results.length > 0 ? (
        <div className="mt-5 grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-4 gap-4 sm:gap-5">
          {results.map((paper) => {
            const isAbstractExpanded = !!expandedAbstracts[paper.id];
            const downloadState = downloadStates[paper.id];

            return (
              <div
                key={paper.id}
                className="apple-card p-5 sm:p-6 rounded-[1.5rem] bg-white dark:bg-[#1c1c1e] border border-black/8 dark:border-white/10 flex flex-col justify-between group gap-3.5"
              >
                <div className="space-y-2.5">
                  {/* Top Metadata: Source, Venue, and Citations */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5">
                      <span className="px-2 py-0.5 rounded-full bg-[#0071e3]/10 dark:bg-[#0a84ff]/20 text-[#0071e3] dark:text-[#64d2ff] text-[10px] font-semibold">
                        {paper.source}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full bg-black/5 dark:bg-white/10 text-[11px] font-medium text-[#1a1a1a]/80 dark:text-white/80 truncate max-w-[140px]">
                        {paper.venue} · {paper.year}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {paper.isOpenAccess && (
                        <span className="px-2 py-0.5 rounded-full bg-[#34c759]/15 text-[#248a3d] dark:text-[#30d158] text-[10px] font-semibold">
                          OA
                        </span>
                      )}
                      <span className="px-2.5 py-0.5 rounded-full bg-[#af52de]/15 text-[#af52de] dark:text-[#bf5af2] text-[10px] font-mono font-medium">
                        {paper.citationCount} cites
                      </span>
                    </div>
                  </div>

                  {/* Title & Authors */}
                  <div>
                    <h3 className="text-sm sm:text-base font-semibold text-[#1a1a1a] dark:text-white group-hover:text-[#0071e3] dark:group-hover:text-[#0a84ff] transition-colors line-clamp-2 leading-snug tracking-tight">
                      {paper.title}
                    </h3>
                    <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 mt-1 font-medium truncate">
                      {paper.authors.slice(0, 3).join(", ")}
                      {paper.authors.length > 3 ? " et al." : ""}
                    </p>
                  </div>

                  {/* Abstract preview in Serif styling */}
                  {paper.abstract && (
                    <div className="bg-black/[0.02] dark:bg-white/[0.04] p-3 rounded-2xl border border-black/5 dark:border-white/5">
                      <p
                        className={`text-xs text-[#1a1a1a]/75 dark:text-white/75 font-serif leading-relaxed ${
                          isAbstractExpanded ? "" : "line-clamp-3"
                        }`}
                      >
                        {paper.abstract}
                      </p>
                      {paper.abstract.length > 180 && (
                        <button
                          onClick={() => toggleAbstract(paper.id)}
                          className="mt-1.5 text-[11px] text-[#0071e3] dark:text-[#0a84ff] hover:underline flex items-center gap-0.5 font-semibold cursor-pointer"
                        >
                          {isAbstractExpanded ? (
                            <>
                              <span>Collapse</span>
                              <ChevronUp className="h-3 w-3" />
                            </>
                          ) : (
                            <>
                              <span>Read more</span>
                              <ChevronDown className="h-3 w-3" />
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Topics Pills */}
                  {paper.topics && paper.topics.length > 0 && (
                    <div className="flex flex-wrap gap-1 pt-1">
                      {paper.topics.slice(0, 2).map((t) => (
                        <span
                          key={t}
                          className="text-[10px] px-2 py-0.5 rounded-full bg-black/5 dark:bg-white/10 text-[#1a1a1a]/70 dark:text-white/70"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions Row */}
                <div className="flex flex-wrap items-center justify-between pt-3 border-t border-black/8 dark:border-white/10 gap-2">
                  <div className="flex items-center gap-1.5">
                    {paper.doi ? (
                      <a
                        href={`https://doi.org/${paper.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-[#1a1a1a]/50 dark:text-white/50 hover:text-[#0071e3] dark:hover:text-[#0a84ff] flex items-center gap-0.5 transition-colors"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span className="font-mono text-[10px]">DOI</span>
                      </a>
                    ) : (
                      <span className="text-[10px] text-[#1a1a1a]/40 dark:text-white/40 font-mono">No DOI</span>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5">
                    {/* Multi-tier PDF download button */}
                    {downloadState ? (
                      <span className="text-[10px] text-[#0071e3] dark:text-[#0a84ff] animate-pulse px-2.5 py-1 rounded-full bg-black/5 dark:bg-white/10 border border-black/10 dark:border-white/15 font-medium">
                        {downloadState.message}
                      </span>
                    ) : (
                      <button
                        onClick={() => handleDownloadPdf(paper)}
                        className="apple-press px-3 py-1.5 rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-white text-[11px] font-semibold flex items-center gap-1 transition-all cursor-pointer shadow-xs"
                        title="Download PDF across Springer, Nature, Unpaywall, Semantic Scholar & Sci-Hub"
                      >
                        <Zap className="h-3 w-3 text-white/90" />
                        <span>PDF</span>
                      </button>
                    )}

                    {/* Add to Notebook button */}
                    <button
                      onClick={() => onAddToNotebook(paper)}
                      className="apple-press px-3 py-1.5 rounded-full bg-[#34c759]/15 hover:bg-[#34c759]/25 text-[#248a3d] dark:text-[#30d158] text-[11px] font-semibold flex items-center gap-1 transition-colors cursor-pointer"
                      title="Add paper to systematic review notebook"
                    >
                      <BookmarkPlus className="h-3 w-3" />
                      <span>Add</span>
                    </button>

                    {/* Deep Inspect */}
                    <button
                      onClick={() => onInspectPaper(paper)}
                      className="apple-press px-3 py-1.5 rounded-full bg-black/5 dark:bg-white/10 hover:bg-black/10 dark:hover:bg-white/15 text-[#1a1a1a] dark:text-white text-[11px] font-medium flex items-center gap-1 transition-colors cursor-pointer"
                      title="Open in deep synthesis workspace"
                    >
                      <BookOpen className="h-3 w-3 text-[#0071e3] dark:text-[#0a84ff]" />
                      <span>Inspect</span>
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      ) : null}

      {/* API Tokens Configuration Modal */}
      <TokensModal
        isOpen={showTokensModal}
        onClose={() => setShowTokensModal(false)}
        onSave={() => {
          setHasCustomTokens(true);
        }}
      />
    </div>
  );
}
