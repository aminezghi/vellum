"use client";

import React, { useState } from "react";
import { AcademicPaperResult } from "@/app/api/search/route";
import { fetchAndStorePaperPdf, triggerBrowserFileDownload } from "@/lib/pdfDownloader";
import { STORAGE_KEYS } from "@/lib/storageNamespace";
import { TokensModal } from "./TokensModal";
import {
  Search,
  SlidersHorizontal,
  BookmarkPlus,
  BookOpen,
  Sparkles,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Zap,
  Key,
  Database,
  Filter,
  RotateCcw,
  ArrowUpRight,
  GraduationCap,
  X,
  Plus,
  GitFork,
  Code2,
} from "lucide-react";

interface AcademicSearchHubProps {
  onAddToNotebook: (paper: AcademicPaperResult) => void;
  onInspectPaper: (paper: AcademicPaperResult) => void;
  onOpenConnectedGraph?: (seed: string) => void;
}

export interface BooleanClause {
  id: string;
  field: "All fields" | "Title / Abstract" | "Author" | "Topic / Keyword" | "Publication Year";
  term: string;
  connector: "AND" | "OR" | "NOT";
}

export const RESEARCH_FIELDS = [
  {
    id: "biomedicine",
    label: "Biomedicine & Health",
    icon: "🧬",
    suggestions: [
      "mRNA therapeutic delivery systems",
      "GLP-1 receptor agonists clinical outcomes",
      "Gut microbiome metabolic axis",
      "Single-cell RNA sequencing in oncology",
      "CRISPR-Cas9 in vivo clinical trials",
    ],
  },
  {
    id: "ai",
    label: "AI & Computer Science",
    icon: "🧠",
    suggestions: [
      "Chain-of-thought mathematical reasoning",
      "Direct preference optimization alignment",
      "Diffusion models for inverse problems",
      "KV-cache compression in transformers",
      "Mechanistic interpretability neural networks",
    ],
  },
  {
    id: "economics",
    label: "Economics & Public Policy",
    icon: "📈",
    suggestions: [
      "Universal basic income randomized trials",
      "Carbon border adjustment mechanism impacts",
      "Monetary policy transmission digital banking",
      "Minimum wage dynamic employment elasticity",
      "Corporate ESG decoupling econometrics",
    ],
  },
  {
    id: "climate",
    label: "Climate & Agriculture",
    icon: "🌱",
    suggestions: [
      "Soil carbon sequestration regenerative agriculture",
      "Drought-resilient C4 crop genetic engineering",
      "Precision nitrogen fertilizer emissions",
      "Agroforestry microclimate temperature buffering",
      "Satellite NDVI remote sensing yield forecasting",
    ],
  },
  {
    id: "neuro",
    label: "Neuroscience & Cognition",
    icon: "⚡",
    suggestions: [
      "Synaptic plasticity hippocampal CA1",
      "Default mode network functional connectivity",
      "Optogenetic control cortical circuits",
      "Microglial activation in neurodegeneration",
      "Deep brain stimulation oscillatory dynamics",
    ],
  },
  {
    id: "physics",
    label: "Physics & Materials",
    icon: "🔬",
    suggestions: [
      "Perovskite tandem solar cell degradation",
      "Quantum error correction surface codes",
      "Topological insulators band structure",
      "High-entropy alloys mechanical properties",
      "Twisted bilayer graphene superconductivity",
    ],
  },
];

const AVAILABLE_SOURCES = [
  { id: "openalex", label: "OpenAlex (250M+)", badge: "Global Corpus" },
  { id: "arxiv", label: "arXiv (Preprints)", badge: "Preprints" },
  { id: "semanticscholar", label: "Semantic Scholar", badge: "AI Graph" },
  { id: "crossref", label: "Crossref", badge: "Publishers" },
];

/**
 * True when at least one provider token has been saved in this browser.
 *
 * Read as the initial value of `hasCustomTokens` rather than in a mount effect:
 * the studio only mounts after the notebook index has loaded, so there is no
 * server-rendered HTML to disagree with, and no second render is needed.
 */
function hasStoredTokens(): boolean {
  if (typeof window === "undefined") return false;
  const stored = localStorage.getItem(STORAGE_KEYS.tokens);
  if (!stored) return false;
  try {
    const parsed: unknown = JSON.parse(stored);
    if (typeof parsed !== "object" || parsed === null) return false;
    return Object.values(parsed).some(
      (value) => typeof value === "string" && value.trim().length > 0
    );
  } catch {
    return false;
  }
}

/** The research field last chosen, or the first one if none was stored. */
function readResearcherField(): string {
  const fallback = RESEARCH_FIELDS[0].id;
  if (typeof window === "undefined") return fallback;
  const saved = localStorage.getItem(STORAGE_KEYS.researcherField);
  return saved && RESEARCH_FIELDS.some((field) => field.id === saved) ? saved : fallback;
}

export function AcademicSearchHub({
  onAddToNotebook,
  onInspectPaper,
  onOpenConnectedGraph,
}: AcademicSearchHubProps) {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<AcademicPaperResult[]>([]);
  const [totalCount, setTotalCount] = useState<number | null>(null);
  const [loading, setLoading] = useState(false);
  const [openAccessOnly, setOpenAccessOnly] = useState(true); // Default to Open Access Priority
  const [fromYear, setFromYear] = useState("2018");
  const [sortBy, setSortBy] = useState("relevance");
  const [showFilters, setShowFilters] = useState(false);
  const [showAdvancedBuilder, setShowAdvancedBuilder] = useState(false);
  const [builderTab, setBuilderTab] = useState<"visual" | "raw">("visual");
  const [showTokensModal, setShowTokensModal] = useState(false);
  const [hasCustomTokens, setHasCustomTokens] = useState(hasStoredTokens);
  const [selectedField, setSelectedField] = useState(readResearcherField);

  // Desktop Style Visual Boolean Clauses
  const [clauses, setClauses] = useState<BooleanClause[]>([
    { id: "c-1", connector: "AND", field: "All fields", term: "" },
    { id: "c-2", connector: "AND", field: "Title / Abstract", term: "" },
  ]);

  // Source selections
  const [selectedSources, setSelectedSources] = useState<string[]>([
    "openalex",
    "arxiv",
    "semanticscholar",
  ]);

  // Advanced query builder fields (Raw mode)
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

  // Compile clauses into Desktop-style boolean query string
  const compileClauses = (clauseList: BooleanClause[]): string => {
    const parts: string[] = [];
    clauseList.forEach((c) => {
      const term = (c.term || "").trim();
      if (!term) return;

      let quoted = term;
      if (term.includes(" ") && !(term.startsWith('"') && term.endsWith('"'))) {
        quoted = `"${term}"`;
      }

      let segment = quoted;
      if (c.field === "Title / Abstract") {
        segment = `${quoted}[Title/Abstract]`;
      } else if (c.field === "Author") {
        segment = `au:${quoted}`;
      } else if (c.field === "Topic / Keyword") {
        segment = `topic:${quoted}`;
      } else if (c.field === "Publication Year") {
        segment = `year:${quoted}`;
      }

      if (parts.length === 0) {
        parts.push(segment);
      } else {
        parts.push(`${c.connector} ${segment}`);
      }
    });
    return parts.join(" ");
  };

  const compiledBooleanQuery = compileClauses(clauses);

  const addClause = () => {
    setClauses((prev) => [
      ...prev,
      {
        id: `c-${Date.now()}-${Math.random().toString(36).slice(2, 5)}`,
        connector: "AND",
        field: "All fields",
        term: "",
      },
    ]);
  };

  const removeClause = (id: string) => {
    if (clauses.length <= 1) return;
    setClauses((prev) => prev.filter((c) => c.id !== id));
  };

  const updateClause = (id: string, updates: Partial<BooleanClause>) => {
    setClauses((prev) =>
      prev.map((c) => (c.id === id ? { ...c, ...updates } : c))
    );
  };

  const applyCompiledQueryToSearchBar = (qStr?: string) => {
    const target = qStr !== undefined ? qStr : compiledBooleanQuery;
    if (target.trim()) {
      setQuery(target.trim());
    }
  };

  // Saved tokens and research field are read as initial state (see the
  // module-level readers above); nothing needs to run on mount.

  const handleFieldChange = (fieldId: string) => {
    setSelectedField(fieldId);
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEYS.researcherField, fieldId);
    }
  };

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
    let combinedQuery = searchQuery.trim() || query.trim();

    if (showAdvancedBuilder) {
      if (builderTab === "visual" && compiledBooleanQuery.trim()) {
        combinedQuery = compiledBooleanQuery.trim();
        setQuery(combinedQuery);
      } else if (builderTab === "raw") {
        const parts: string[] = [];
        if (exactPhrase.trim()) parts.push(`"${exactPhrase.trim()}"`);
        if (mustInclude.trim()) parts.push(mustInclude.trim());
        if (anyInclude.trim()) {
          const orTerms = anyInclude.trim().split(/\s+/).join(" OR ");
          parts.push(`(${orTerms})`);
        }
        if (mustExclude.trim()) {
          const notTerms = mustExclude.trim().split(/\s+/).map((t) => `NOT ${t}`).join(" ");
          parts.push(notTerms);
        }
        if (authorQuery.trim()) parts.push(`author:"${authorQuery.trim()}"`);
        if (doiQuery.trim()) parts.push(`doi:${doiQuery.trim()}`);

        if (parts.length > 0) {
          combinedQuery = parts.join(" ");
          setQuery(combinedQuery);
        }
      }
    }

    if (!combinedQuery && !authorQuery.trim() && !doiQuery.trim()) return;

    setLoading(true);
    try {
      const params = new URLSearchParams({
        q: combinedQuery,
        fromYear,
        sortBy,
        sources: selectedSources.join(","),
        openAccessOnly: openAccessOnly ? "true" : "false",
        fieldScope,
      });

      const res = await fetch(`/api/search?${params.toString()}`);
      if (!res.ok) throw new Error("Search request failed");
      const data = await res.json();

      setResults(data.results || []);
      setTotalCount(data.total || data.results?.length || 0);
    } catch (err) {
      console.error("Search error:", err);
      setResults([]);
      setTotalCount(0);
    } finally {
      setLoading(false);
    }
  };

  const resetAdvancedBuilder = () => {
    setClauses([
      { id: "c-1", connector: "AND", field: "All fields", term: "" },
      { id: "c-2", connector: "AND", field: "Title / Abstract", term: "" },
    ]);
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

  const currentFieldObj = RESEARCH_FIELDS.find((f) => f.id === selectedField) || RESEARCH_FIELDS[0];

  return (
    <div className="w-full fernly-card rounded-[2rem] p-5 sm:p-7 mb-8 transition-colors duration-200">
      {/* Section Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3.5 pb-5 border-b border-[var(--card-bdr)] mb-5">
        <div className="flex items-start sm:items-center gap-3.5">
          <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--g-950)] dark:bg-[var(--g-900)] text-[var(--g-300)] shadow-xs flex-shrink-0 border border-[var(--g-800)]">
            <Search className="h-5 w-5" />
          </div>
          <div>
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-base sm:text-lg font-bold tracking-tight text-[var(--ink)]">
                Live Academic Literature Search
              </h2>
              <span className="fernly-badge fernly-badge-leaf text-[10px] font-semibold">
                250M+ Multi-Source Corpus
              </span>
            </div>
            <p className="text-xs text-[var(--ink-muted)] mt-0.5 font-medium leading-relaxed">
              Multi-source querying across OpenAlex, arXiv, Semantic Scholar, and Crossref with direct PDF discovery
            </p>
          </div>
        </div>

        {/* Action Controls Header */}
        <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
          {/* API / Tokens Button */}
          <button
            onClick={() => setShowTokensModal(true)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border text-xs font-semibold transition-all cursor-pointer shadow-xs ${
              hasCustomTokens
                ? "bg-[var(--g-100)] text-[var(--g-950)] border-[var(--g-300)] dark:bg-[var(--g-900)] dark:text-[var(--g-200)] dark:border-[var(--g-800)]"
                : "bg-[var(--panel)] border-[var(--card-bdr)] text-[var(--ink)] hover:border-[var(--g-500)]"
            }`}
            title="Configure OpenAlex, Semantic Scholar & PubMed API tokens"
          >
            <Key className="h-3.5 w-3.5 text-[var(--g-600)]" />
            <span className="hidden sm:inline">API Tokens</span>
            {hasCustomTokens && <span className="h-1.5 w-1.5 rounded-full bg-[var(--g-500)]" />}
          </button>

          {/* Advanced Query Builder Toggle */}
          <button
            onClick={() => setShowAdvancedBuilder(!showAdvancedBuilder)}
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border text-xs font-semibold transition-all cursor-pointer shadow-xs ${
              showAdvancedBuilder || mustInclude || exactPhrase || authorQuery || doiQuery
                ? "btn-fernly-primary text-white border-transparent"
                : "btn-fernly-ghost text-[var(--ink)]"
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
            className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-full border text-xs font-semibold transition-all cursor-pointer shadow-xs ${
              showFilters || fromYear !== "2018"
                ? "btn-fernly-primary text-white border-transparent"
                : "btn-fernly-ghost text-[var(--ink)]"
            }`}
          >
            <SlidersHorizontal className="h-3.5 w-3.5" />
            <span>Filters</span>
          </button>
        </div>
      </div>

      {/* Row 1: Researcher Field Customization & Open Access Priority Bar */}
      <div className="mb-4 flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-3 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)]">
        <div className="flex items-center gap-2 flex-wrap">
          <span className="text-[11px] font-bold text-[var(--ink)] flex items-center gap-1.5">
            <GraduationCap className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
            <span>Researcher Field:</span>
          </span>
          <div className="flex items-center gap-1 flex-wrap">
            {RESEARCH_FIELDS.map((rf) => (
              <button
                key={rf.id}
                onClick={() => handleFieldChange(rf.id)}
                className={`px-2.5 py-1 rounded-full text-xs font-semibold transition-all cursor-pointer border ${
                  selectedField === rf.id
                    ? "bg-[var(--g-800)] text-white border-[var(--g-700)] shadow-xs"
                    : "bg-[var(--card)] text-[var(--ink-muted)] border-[var(--card-bdr)] hover:border-[var(--g-400)]"
                }`}
              >
                <span>{rf.icon}</span> <span className="hidden md:inline">{rf.label}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Open Access Priority Switch */}
        <label className="flex items-center gap-2 cursor-pointer select-none self-start sm:self-auto bg-[var(--card)] px-3 py-1 rounded-full border border-[var(--card-bdr)]">
          <input
            type="checkbox"
            checked={openAccessOnly}
            onChange={(e) => setOpenAccessOnly(e.target.checked)}
            className="rounded border-[var(--card-bdr)] text-[var(--g-600)] focus:ring-0 cursor-pointer"
          />
          <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-1">
            <span>🌿 Open Access Only</span>
            <span className="text-[10px] text-[var(--g-600)] font-normal hidden lg:inline">(Free full-text PDFs)</span>
          </span>
        </label>
      </div>

      {/* Source Selection Pill Bar */}
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold text-[var(--ink-muted)] flex items-center gap-1.5 mr-1">
          <Database className="h-3.5 w-3.5 text-[var(--g-600)] dark:text-[var(--g-400)]" />
          <span>Active Sources:</span>
        </span>
        {AVAILABLE_SOURCES.map((src) => {
          const isSelected = selectedSources.includes(src.id);
          return (
            <button
              key={src.id}
              onClick={() => toggleSource(src.id)}
              className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium transition-all cursor-pointer border ${
                isSelected
                  ? "bg-[var(--g-50)] dark:bg-[var(--g-950)] border-[var(--g-600)] dark:border-[var(--g-400)] text-[var(--ink)] shadow-xs"
                  : "bg-transparent border-[var(--card-bdr)] text-[var(--ink-muted)] hover:border-[var(--g-400)]"
              }`}
            >
              <div
                className={`h-2 w-2 rounded-full transition-colors ${
                  isSelected ? "bg-[var(--g-600)] dark:bg-[var(--g-400)]" : "bg-transparent border border-[var(--ink-muted)]"
                }`}
              />
              <span>{src.label}</span>
            </button>
          );
        })}
      </div>

      {/* Main Search Input Form (With explicit left padding so text never overlaps icon) */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSearch();
        }}
        className="relative flex items-center gap-2.5"
      >
        <div className="relative flex-1 group">
          <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-4 w-4 text-[var(--ink-muted)] group-focus-within:text-[var(--g-600)] transition-colors pointer-events-none" />
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={`Search 250M+ global papers (${currentFieldObj.label}), authors, or DOIs...`}
            title="Federated literature query across OpenAlex, arXiv, Semantic Scholar, and Crossref"
            className="fernly-input fernly-input-search w-full !pl-12 !pr-10 py-3 rounded-full text-xs sm:text-sm text-[var(--ink)] placeholder-[var(--ink-muted)] transition-all shadow-xs"
          />
          {query && (
            <button
              type="button"
              onClick={() => setQuery("")}
              className="absolute right-3.5 top-1/2 -translate-y-1/2 p-1 rounded-full text-[var(--ink-muted)] hover:text-[var(--ink)] cursor-pointer"
              title="Clear search"
            >
              <X className="h-3.5 w-3.5" />
            </button>
          )}
        </div>
        <button
          type="submit"
          disabled={loading || (!query.trim() && !mustInclude && !exactPhrase && !doiQuery && !authorQuery)}
          className="btn-fernly-primary px-6 py-3 rounded-full text-xs sm:text-sm font-semibold shadow-xs disabled:opacity-50 transition-all cursor-pointer flex-shrink-0 flex items-center gap-2"
        >
          {loading ? (
            <span className="animate-pulse" role="status" aria-live="polite">
              Searching academic sources...
            </span>
          ) : (
            <>
              <span>Search</span>
              <span className="fernly-arrow bg-white/20 text-white w-4 h-4 rounded-full flex items-center justify-center">
                <ArrowUpRight className="h-3 w-3" />
              </span>
            </>
          )}
        </button>
      </form>

      {/* Advanced Search & Boolean Query Builder Drawer (Desktop-Style Clause Builder) */}
      {showAdvancedBuilder && (
        <div className="mt-4 p-5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] space-y-4 animate-in fade-in slide-in-from-top-2 duration-200">
          {/* Header with Mode Switcher (Visual Boolean vs Raw Query) */}
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2.5 pb-3 border-b border-[var(--card-bdr)]">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-1.5">
                <Sparkles className="h-3.5 w-3.5 text-[var(--g-500)]" />
                <span>Desktop Boolean Engine</span>
              </span>
              <div className="flex items-center gap-1 bg-[var(--card)] p-0.5 rounded-full border border-[var(--card-bdr)] text-[11px]">
                <button
                  type="button"
                  onClick={() => setBuilderTab("visual")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                    builderTab === "visual"
                      ? "bg-[var(--g-800)] text-white shadow-xs"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  <span>🧩 Visual Boolean Builder</span>
                </button>
                <button
                  type="button"
                  onClick={() => setBuilderTab("raw")}
                  className={`px-3 py-1 rounded-full font-semibold transition-all cursor-pointer flex items-center gap-1.5 ${
                    builderTab === "raw"
                      ? "bg-[var(--g-800)] text-white shadow-xs"
                      : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                  }`}
                >
                  <Code2 className="h-3 w-3" />
                  <span>✍️ Advanced Raw Query</span>
                </button>
              </div>
            </div>

            <button
              type="button"
              onClick={resetAdvancedBuilder}
              className="text-[11px] text-[var(--ink-muted)] hover:text-red-600 dark:hover:text-red-400 flex items-center gap-1 cursor-pointer font-medium self-start sm:self-auto"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Reset clauses</span>
            </button>
          </div>

          {/* MODE 1: VISUAL BOOLEAN CLAUSE-BY-CLAUSE BUILDER (Matches Desktop litcheck_ui.py lines 156-251) */}
          {builderTab === "visual" && (
            <div className="space-y-3">
              <p className="text-[11px] text-[var(--ink-muted)]">
                Combine concepts using boolean logic. Multi-word phrases are quoted automatically and mapped to standard field tags (<code className="px-1 py-0.5 rounded bg-[var(--card)] border border-[var(--card-bdr)]">[Title/Abstract]</code>, <code className="px-1 py-0.5 rounded bg-[var(--card)] border border-[var(--card-bdr)]">au:</code>, <code className="px-1 py-0.5 rounded bg-[var(--card)] border border-[var(--card-bdr)]">year:</code>).
              </p>

              {/* Clause Rows */}
              <div className="space-y-2.5">
                {clauses.map((clause, idx) => (
                  <div
                    key={clause.id}
                    className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 p-2.5 rounded-xl bg-[var(--card)] border border-[var(--card-bdr)]"
                  >
                    {/* Connector: WHERE for first row, AND / OR / NOT for subsequent rows */}
                    <div className="w-full sm:w-28 flex-shrink-0">
                      {idx === 0 ? (
                        <div className="px-3 py-2 rounded-xl bg-[var(--panel)] border border-[var(--card-bdr)] text-center text-xs font-bold text-[var(--ink-muted)] tracking-wider">
                          WHERE
                        </div>
                      ) : (
                        <select
                          value={clause.connector}
                          onChange={(e) =>
                            updateClause(clause.id, {
                              connector: e.target.value as "AND" | "OR" | "NOT",
                            })
                          }
                          className="fernly-input w-full px-3 py-2 rounded-xl text-xs font-bold text-[var(--ink)] cursor-pointer"
                        >
                          <option value="AND">AND</option>
                          <option value="OR">OR</option>
                          <option value="NOT">NOT</option>
                        </select>
                      )}
                    </div>

                    {/* Field Scope Selector */}
                    <div className="w-full sm:w-44 flex-shrink-0">
                      <select
                        value={clause.field}
                        onChange={(e) =>
                          updateClause(clause.id, {
                            field: e.target.value as BooleanClause["field"],
                          })
                        }
                        className="fernly-input w-full px-3 py-2 rounded-xl text-xs font-medium text-[var(--ink)] cursor-pointer"
                      >
                        <option value="All fields">All fields</option>
                        <option value="Title / Abstract">Title / Abstract</option>
                        <option value="Author">Author</option>
                        <option value="Topic / Keyword">Topic / Keyword</option>
                        <option value="Publication Year">Publication Year</option>
                      </select>
                    </div>

                    {/* Term Input */}
                    <div className="flex-1 relative">
                      <input
                        type="text"
                        value={clause.term}
                        onChange={(e) => updateClause(clause.id, { term: e.target.value })}
                        placeholder={
                          idx === 0
                            ? 'e.g. "fruit detection" or neural networks'
                            : idx === 1
                            ? "e.g. deep learning or YOLO"
                            : "Enter keyword, author name, or year..."
                        }
                        className="fernly-input w-full px-3.5 py-2 rounded-xl text-xs text-[var(--ink)] placeholder-[var(--ink-muted)]"
                      />
                    </div>

                    {/* Delete Clause Action */}
                    {clauses.length > 1 && (
                      <button
                        type="button"
                        onClick={() => removeClause(clause.id)}
                        className="p-2 rounded-xl text-[var(--ink-muted)] hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-950/30 transition-colors cursor-pointer self-end sm:self-center"
                        title="Remove clause"
                      >
                        <X className="h-4 w-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>

              {/* Add Clause Button */}
              <div className="flex items-center gap-2 pt-1">
                <button
                  type="button"
                  onClick={addClause}
                  className="flex items-center gap-1.5 px-3.5 py-1.5 rounded-full bg-[var(--card)] hover:bg-[var(--panel)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-[var(--ink)] text-xs font-semibold transition-all cursor-pointer shadow-xs"
                >
                  <Plus className="h-3.5 w-3.5 text-[var(--g-600)]" />
                  <span>Add Clause</span>
                </button>
              </div>

              {/* Live Compiled Query Box (Just like in Desktop litcheck_ui.py) */}
              {compiledBooleanQuery && (
                <div className="p-3.5 rounded-xl bg-[var(--g-50)] dark:bg-[var(--g-950)] border border-[var(--g-300)] dark:border-[var(--g-800)] flex flex-col md:flex-row md:items-center justify-between gap-3 animate-in fade-in">
                  <div className="min-w-0 flex-1">
                    <span className="text-[10px] font-bold text-[var(--g-800)] dark:text-[var(--g-300)] uppercase tracking-wider block mb-1">
                      Live Compiled Query:
                    </span>
                    <code className="text-xs font-mono text-[var(--g-950)] dark:text-[var(--g-100)] break-all select-all font-semibold">
                      {compiledBooleanQuery}
                    </code>
                  </div>
                  <div className="flex items-center gap-2 flex-shrink-0">
                    <button
                      type="button"
                      onClick={() => applyCompiledQueryToSearchBar()}
                      className="px-3 py-1.5 rounded-full bg-[var(--panel)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-[var(--ink)] text-xs font-semibold transition-all cursor-pointer shadow-xs"
                    >
                      Apply to Search Bar
                    </button>
                    <button
                      type="button"
                      onClick={() => handleSearch(compiledBooleanQuery)}
                      className="btn-fernly-primary px-4 py-1.5 rounded-full text-xs font-semibold shadow-xs cursor-pointer flex items-center gap-1.5"
                    >
                      <span>Search Literature</span>
                      <ArrowUpRight className="h-3 w-3" />
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* MODE 2: ADVANCED RAW QUERY & SPECIFIC FIELDS */}
          {builderTab === "raw" && (
            <div className="space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3.5 text-xs">
                {/* Must Include ALL (AND) */}
                <div className="space-y-1">
                  <label className="font-semibold text-[var(--ink)] flex items-center justify-between">
                    <span>Must include ALL words (AND):</span>
                    <span className="text-[10px] text-[var(--g-600)] dark:text-[var(--g-400)] font-semibold">Required</span>
                  </label>
                  <input
                    type="text"
                    value={mustInclude}
                    onChange={(e) => setMustInclude(e.target.value)}
                    placeholder="e.g. reasoning alignment safety"
                    className="fernly-input w-full px-3 py-2 rounded-xl text-[var(--ink)] placeholder-[var(--ink-muted)] text-xs"
                  />
                </div>

                {/* Must Include ANY (OR) */}
                <div className="space-y-1">
                  <label className="font-semibold text-[var(--ink)]">
                    Include ANY of these words (OR):
                  </label>
                  <input
                    type="text"
                    value={anyInclude}
                    onChange={(e) => setAnyInclude(e.target.value)}
                    placeholder="e.g. ethics governance oversight"
                    className="fernly-input w-full px-3 py-2 rounded-xl text-[var(--ink)] placeholder-[var(--ink-muted)] text-xs"
                  />
                </div>

                {/* Must EXCLUDE (NOT) */}
                <div className="space-y-1">
                  <label className="font-semibold text-[var(--ink)] flex items-center justify-between">
                    <span>Must EXCLUDE words (NOT):</span>
                    <span className="text-[10px] text-red-600 dark:text-red-400 font-semibold">Purge</span>
                  </label>
                  <input
                    type="text"
                    value={mustExclude}
                    onChange={(e) => setMustExclude(e.target.value)}
                    placeholder="e.g. survey overview editorial"
                    className="fernly-input w-full px-3 py-2 rounded-xl text-[var(--ink)] placeholder-[var(--ink-muted)] text-xs"
                  />
                </div>

                {/* Exact Phrase Match */}
                <div className="space-y-1">
                  <label className="font-semibold text-[var(--ink)]">
                    Exact Phrase (&quot;quotes&quot;):
                  </label>
                  <input
                    type="text"
                    value={exactPhrase}
                    onChange={(e) => setExactPhrase(e.target.value)}
                    placeholder='e.g. "large language models"'
                    className="fernly-input w-full px-3 py-2 rounded-xl text-[var(--ink)] placeholder-[var(--ink-muted)] text-xs"
                  />
                </div>

                {/* Author Specific Query */}
                <div className="space-y-1">
                  <label className="font-semibold text-[var(--ink)]">
                    Specific Author Name:
                  </label>
                  <input
                    type="text"
                    value={authorQuery}
                    onChange={(e) => setAuthorQuery(e.target.value)}
                    placeholder="e.g. Geoffrey Hinton, Yann LeCun"
                    className="fernly-input w-full px-3 py-2 rounded-xl text-[var(--ink)] placeholder-[var(--ink-muted)] text-xs"
                  />
                </div>

                {/* Direct DOI Lookup */}
                <div className="space-y-1">
                  <label className="font-semibold text-[var(--ink)]">
                    Direct DOI (Digital Object Identifier):
                  </label>
                  <input
                    type="text"
                    value={doiQuery}
                    onChange={(e) => setDoiQuery(e.target.value)}
                    placeholder="e.g. 10.1038/s41586-023-00000-0"
                    className="fernly-input w-full px-3 py-2 rounded-xl text-[var(--ink)] placeholder-[var(--ink-muted)] text-xs"
                  />
                </div>
              </div>

              <div className="flex items-center justify-between pt-2">
                <div className="flex items-center gap-2">
                  <span className="text-[11px] text-[var(--ink-muted)] font-medium">Match scope:</span>
                  <div className="flex items-center gap-1 bg-[var(--card)] p-0.5 rounded-full border border-[var(--card-bdr)] text-[11px]">
                    {(["all", "title", "author", "doi"] as const).map((sc) => (
                      <button
                        key={sc}
                        type="button"
                        onClick={() => setFieldScope(sc)}
                        className={`px-3 py-0.5 rounded-full capitalize transition-all cursor-pointer ${
                          fieldScope === sc
                            ? "bg-[var(--g-800)] text-[var(--g-100)] font-semibold"
                            : "text-[var(--ink-muted)] hover:text-[var(--ink)]"
                        }`}
                      >
                        {sc === "all" ? "All fields" : sc}
                      </button>
                    ))}
                  </div>
                </div>

                <button
                  type="button"
                  onClick={() => handleSearch()}
                  className="btn-fernly-primary px-4 py-1.5 rounded-full text-xs font-semibold shadow-xs cursor-pointer transition-all"
                >
                  Run Combined Query
                </button>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Collapsible Filter Bar */}
      {showFilters && (
        <div className="mt-4 p-4 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] flex flex-wrap items-center gap-4 text-xs text-[var(--ink)]">
          <div className="flex items-center gap-1.5">
            <span className="text-[var(--ink-muted)] font-medium">From Year:</span>
            <select
              value={fromYear}
              onChange={(e) => setFromYear(e.target.value)}
              className="fernly-input rounded-full px-3 py-1 text-xs text-[var(--ink)] font-medium"
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
            <span className="text-[var(--ink-muted)] font-medium">Sort by:</span>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              className="fernly-input rounded-full px-3 py-1 text-xs text-[var(--ink)] font-medium"
            >
              <option value="relevance">Relevance</option>
              <option value="citations">Most Cited</option>
              <option value="date">Newest First</option>
            </select>
          </div>
        </div>
      )}

      {/* Suggested Topic Chips (Dynamically tailored to the selected Researcher Field!) */}
      {!results.length && !loading && (
        <div className="mt-4 flex flex-wrap items-center gap-1.5">
          <span className="text-[11px] text-[var(--ink-muted)] mr-1 flex items-center gap-1 font-semibold">
            <Sparkles className="h-3 w-3 text-[var(--g-500)]" /> {currentFieldObj.label} Suggestions:
          </span>
          {currentFieldObj.suggestions.map((q) => (
            <button
              key={q}
              onClick={() => {
                setQuery(q);
                handleSearch(q);
              }}
              className="btn-fernly-ghost px-3 py-1 rounded-full text-[11px] text-[var(--ink-muted)] hover:text-[var(--ink)] transition-all cursor-pointer font-medium"
            >
              {q}
            </button>
          ))}
        </div>
      )}

      {/* Results Header
          The count is inside a live region: without it, a screen-reader user
          who starts a search is told nothing when the results arrive. */}
      {totalCount !== null && (
        <div className="mt-6 pt-4 border-t border-[var(--card-bdr)] flex items-center justify-between">
          <span
            className="text-xs font-semibold text-[var(--ink)]"
            role="status"
            aria-live="polite"
          >
            {results.length} papers retrieved across {selectedSources.length} sources
            {openAccessOnly && " (Open Access prioritized)"}
          </span>
          <span className="text-[11px] text-[var(--ink-muted)] font-medium">
            Multi-Tier PDF &amp; Citation Resolver
          </span>
        </div>
      )}

      {/* Paper Results Grid (Fluid Full Screen Responsive) */}
      {loading ? (
        <div className="py-16 flex flex-col items-center justify-center space-y-3">
          <div className="h-8 w-8 border-2 border-[var(--g-600)] border-t-transparent rounded-full animate-spin" />
          <span className="text-xs text-[var(--ink-muted)] animate-pulse font-medium">
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
                className="fernly-card p-5 sm:p-6 rounded-[1.5rem] flex flex-col justify-between group gap-3.5 hover:border-[var(--g-400)] transition-all"
              >
                <div className="space-y-2.5">
                  {/* Top Metadata: Source, Venue, and Citations */}
                  <div className="flex items-center justify-between gap-2 flex-wrap">
                    <div className="flex items-center gap-1.5">
                      <span className="fernly-badge fernly-badge-leaf text-[10px] font-semibold uppercase tracking-wider">
                        {paper.source}
                      </span>
                      <span className="px-2.5 py-0.5 rounded-full bg-[var(--panel)] border border-[var(--card-bdr)] text-[11px] font-medium text-[var(--ink-muted)] truncate max-w-[140px]">
                        {paper.venue} · {paper.year}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5 flex-shrink-0">
                      {paper.isOpenAccess && (
                        <span className="fernly-badge fernly-badge-mint text-[10px] font-semibold">
                          OA
                        </span>
                      )}
                      <span className="fernly-badge fernly-badge-neutral text-[10px] font-mono font-medium">
                        {paper.citationCount} cites
                      </span>
                    </div>
                  </div>

                  {/* Title & Authors */}
                  <div>
                    <h3 className="text-sm sm:text-base font-bold text-[var(--ink)] group-hover:text-[var(--g-600)] dark:group-hover:text-[var(--g-400)] transition-colors line-clamp-2 leading-snug tracking-tight">
                      {paper.title}
                    </h3>
                    <p className="text-xs text-[var(--ink-muted)] mt-1 font-medium truncate">
                      {paper.authors.slice(0, 3).join(", ")}
                      {paper.authors.length > 3 ? " et al." : ""}
                    </p>
                  </div>

                  {/* Abstract preview */}
                  {paper.abstract && (
                    <div className="bg-[var(--panel)] p-3.5 rounded-2xl border border-[var(--card-bdr)]">
                      <p
                        className={`text-xs text-[var(--ink-muted)] leading-relaxed font-sans ${
                          isAbstractExpanded ? "" : "line-clamp-3"
                        }`}
                      >
                        {paper.abstract}
                      </p>
                      {paper.abstract.length > 180 && (
                        <button
                          onClick={() => toggleAbstract(paper.id)}
                          className="mt-1.5 text-[11px] text-[var(--g-600)] dark:text-[var(--g-400)] hover:underline flex items-center gap-0.5 font-semibold cursor-pointer"
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
                          className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--panel)] border border-[var(--card-bdr)] text-[var(--ink-muted)]"
                        >
                          {t}
                        </span>
                      ))}
                    </div>
                  )}
                </div>

                {/* Actions Row */}
                <div className="flex flex-wrap items-center justify-between pt-3 border-t border-[var(--card-bdr)] gap-2">
                  <div className="flex items-center gap-1.5">
                    {paper.doi ? (
                      <a
                        href={`https://doi.org/${paper.doi}`}
                        target="_blank"
                        rel="noreferrer"
                        className="text-[11px] text-[var(--ink-muted)] hover:text-[var(--g-600)] dark:hover:text-[var(--g-400)] flex items-center gap-0.5 transition-colors"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span className="font-mono text-[10px]">DOI</span>
                      </a>
                    ) : (
                      <span className="text-[10px] text-[var(--ink-muted)] opacity-60 font-mono">No DOI</span>
                    )}
                  </div>

                  <div className="flex items-center gap-1.5">
                    {/* Multi-tier PDF download button */}
                    {downloadState ? (
                      <span className="text-[10px] text-[var(--g-600)] dark:text-[var(--g-400)] animate-pulse px-2.5 py-1 rounded-full bg-[var(--panel)] border border-[var(--card-bdr)] font-medium">
                        {downloadState.message}
                      </span>
                    ) : (
                      <button
                        onClick={() => handleDownloadPdf(paper)}
                        className="btn-fernly-primary px-3 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1.5 transition-all cursor-pointer shadow-xs"
                        title="Download PDF across Springer, Nature, Unpaywall, Semantic Scholar & Sci-Hub"
                      >
                        <Zap className="h-3 w-3 text-white/90" />
                        <span>PDF</span>
                      </button>
                    )}

                    {/* Connected Graph Force Network */}
                    {onOpenConnectedGraph && (
                      <button
                        onClick={() => onOpenConnectedGraph(paper.title)}
                        className="btn-fernly-ghost px-3 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1 text-[var(--ink)] hover:text-purple-600 dark:hover:text-purple-400 transition-colors cursor-pointer"
                        title="Explore Connected Papers citation network graph"
                      >
                        <GitFork className="h-3 w-3 text-purple-600 dark:text-purple-400" />
                        <span>Graph</span>
                      </button>
                    )}

                    {/* Add to Notebook button */}
                    <button
                      onClick={() => onAddToNotebook(paper)}
                      className="btn-fernly-ghost px-3 py-1.5 rounded-full text-[11px] font-semibold flex items-center gap-1 text-[var(--ink)] hover:text-[var(--g-600)] transition-colors cursor-pointer"
                      title="Add paper to systematic review notebook"
                    >
                      <BookmarkPlus className="h-3 w-3" />
                      <span>Add</span>
                    </button>

                    {/* Deep Inspect */}
                    <button
                      onClick={() => onInspectPaper(paper)}
                      className="group/btn flex items-center gap-1 px-3 py-1.5 rounded-full bg-[var(--panel)] hover:bg-[var(--card)] border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-[var(--ink)] text-[11px] font-semibold transition-all cursor-pointer"
                      title="Open in deep synthesis workspace"
                    >
                      <BookOpen className="h-3 w-3 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                      <span>Inspect</span>
                      <span className="fernly-arrow inline-flex items-center justify-center w-3.5 h-3.5 rounded-full bg-[var(--card-bdr)] text-[var(--ink)] group-hover/btn:bg-[var(--g-800)] group-hover/btn:text-white transition-all ml-0.5">
                        <ArrowUpRight className="h-2.5 w-2.5" />
                      </span>
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
