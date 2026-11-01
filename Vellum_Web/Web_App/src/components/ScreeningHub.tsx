"use client";

import React, { useState, useEffect, useRef, useCallback } from "react";
import { Notebook, Source, db, ScreeningSession, ScreeningItem } from "@/lib/db";
import { STORAGE_KEYS } from "@/lib/storageNamespace";
import { Modal } from "@/components/Modal";
import {
  ActiveLearningClassifier,
  ScreeningCandidate,
  BENCHMARK_SCREENING_DATASETS,
  parseUniversalFile,
  deduplicateCandidates,
  DuplicateDetail,
} from "@/lib/activeLearning";
import {
  CheckCircle2,
  XCircle,
  RotateCcw,
  Sparkles,
  Layers,
  Upload,
  TrendingUp,
  ExternalLink,
  BookOpen,
  Download,
  ShieldCheck,
  ChevronRight,
  ChevronDown,
  FolderSync,
  Plus,
  Trash2,
  Edit3,
  Database,
} from "lucide-react";

interface ScreeningHubProps {
  notebooks: Notebook[];
}

interface StagedSource {
  id: string;
  name: string;
  type: "csv" | "ris" | "bib" | "json" | "notebook" | "benchmark";
  count: number;
  candidates: ScreeningCandidate[];
}

/** File extensions the import path accepts; anything else is treated as CSV. */
const STAGED_FILE_TYPES = ["csv", "ris", "bib", "json"] as const;

function isStagedFileType(value: string): value is (typeof STAGED_FILE_TYPES)[number] {
  return (STAGED_FILE_TYPES as readonly string[]).includes(value);
}

export function ScreeningHub({ notebooks }: ScreeningHubProps) {
  // Session State
  const [sessions, setSessions] = useState<ScreeningSession[]>([]);
  const [activeSession, setActiveSession] = useState<ScreeningSession | null>(null);
  const [sessionName, setSessionName] = useState<string>("Systematic Review Screening");
  const [isEditingName, setIsEditingName] = useState(false);
  const [showSessionsModal, setShowSessionsModal] = useState(false);

  // Active Screening Data
  const [candidates, setCandidates] = useState<ScreeningCandidate[]>([]);
  const [history, setHistory] = useState<{ id: string; decision: "included" | "excluded" }[]>([]);
  const [classifier] = useState(() => new ActiveLearningClassifier());
  const [consecutiveExcludes, setConsecutiveExcludes] = useState(0);
  const [showIncludedDrawer, setShowIncludedDrawer] = useState(false);
  const [feedbackAnimation, setFeedbackAnimation] = useState<"included" | "excluded" | null>(null);

  // Multi-Source Staging & Deduplication
  const [stagedSources, setStagedSources] = useState<StagedSource[]>([]);
  const [duplicatesRemoved, setDuplicatesRemoved] = useState<DuplicateDetail[]>([]);
  const [showDuplicateModal, setShowDuplicateModal] = useState(false);
  const [showAddSourcesModal, setShowAddSourcesModal] = useState(false);

  // File Upload Progress
  const [uploadProgress, setUploadProgress] = useState<{
    isUploading: boolean;
    progress: number;
    stepLabel: string;
    fileName: string;
  }>({
    isUploading: false,
    progress: 0,
    stepLabel: "",
    fileName: "",
  });

  const [selectedNotebookId, setSelectedNotebookId] = useState<string>("");
  const fileInputRef = useRef<HTMLInputElement>(null);
  const addMoreFileInputRef = useRef<HTMLInputElement>(null);

  // 1. Activate / Switch to a Session
  const activateSession = useCallback(async (session: ScreeningSession) => {
    setActiveSession(session);
    setSessionName(session.name);
    setConsecutiveExcludes(session.consecutiveExcludes || 0);
    localStorage.setItem(STORAGE_KEYS.activeScreeningSession, session.id);

    // Load candidate items for this session
    const items = await db.screeningItems.where("sessionId").equals(session.id).toArray();
    const sorted = classifier.retrainAndRank(items as ScreeningCandidate[]);
    setCandidates(sorted);
    setHistory([]);
  }, [classifier]);

  // 2. Initial Load: restore the most recent session, or adopt any records left
  // over from version 2. This lives in the effect rather than a helper because
  // it stamps records with the current time, which is only safe off-render.
  useEffect(() => {
    const load = async () => {
      try {
        const allSessions = await db.screeningSessions.orderBy("updatedAt").reverse().toArray();
        setSessions(allSessions);

        const savedActiveId = localStorage.getItem(STORAGE_KEYS.activeScreeningSession);
        let current = allSessions.find((s) => s.id === savedActiveId);

        if (!current && allSessions.length > 0) {
          current = allSessions[0];
        }

        if (current) {
          await activateSession(current);
          return;
        }

        // No session yet: adopt any records left behind by version 2.
        const legacyItems = await db.screeningItems.toArray();
        if (legacyItems.length === 0) return;

        const defaultSession: ScreeningSession = {
          id: `session-migrated-${Date.now()}`,
          name: "Default Systematic Review",
          createdAt: Date.now(),
          updatedAt: Date.now(),
          totalCount: legacyItems.length,
          screenedCount: legacyItems.filter((i) => i.decision !== "pending").length,
          includedCount: legacyItems.filter((i) => i.decision === "included").length,
          excludedCount: legacyItems.filter((i) => i.decision === "excluded").length,
          consecutiveExcludes: 0,
          sourcesList: ["Migrated Records"],
          duplicatesRemoved: 0,
        };
        await db.screeningSessions.put(defaultSession);
        for (const item of legacyItems) {
          await db.screeningItems.update(item.id, { sessionId: defaultSession.id });
        }
        setSessions([defaultSession]);
        await activateSession(defaultSession);
      } catch (err) {
        console.error("Error loading screening sessions:", err);
      }
    };

    void load();
  }, [activateSession]);

  // 3. Create a New Session
  const handleCreateNewSession = async (customName?: string) => {
    const newSessionId = `session-${Date.now()}`;
    const name =
      customName ||
      `Review Project #${sessions.length + 1} (${new Date().toLocaleDateString(undefined, {
        month: "short",
        day: "numeric",
      })})`;

    const newSession: ScreeningSession = {
      id: newSessionId,
      name,
      createdAt: Date.now(),
      updatedAt: Date.now(),
      totalCount: 0,
      screenedCount: 0,
      includedCount: 0,
      excludedCount: 0,
      consecutiveExcludes: 0,
      sourcesList: [],
      duplicatesRemoved: 0,
    };

    await db.screeningSessions.put(newSession);
    const updatedSessions = [newSession, ...sessions];
    setSessions(updatedSessions);
    setActiveSession(newSession);
    setSessionName(name);
    setCandidates([]);
    setStagedSources([]);
    setDuplicatesRemoved([]);
    setHistory([]);
    setConsecutiveExcludes(0);
    localStorage.setItem(STORAGE_KEYS.activeScreeningSession, newSessionId);
    setShowSessionsModal(false);
  };

  // 4. Delete Session
  const handleDeleteSession = async (sessionId: string) => {
    const confirmDelete = window.confirm(
      "Are you sure you want to permanently delete this screening session and all its decisions?"
    );
    if (!confirmDelete) return;

    await db.screeningSessions.delete(sessionId);
    await db.screeningItems.where("sessionId").equals(sessionId).delete();

    const remaining = sessions.filter((s) => s.id !== sessionId);
    setSessions(remaining);

    if (activeSession?.id === sessionId) {
      if (remaining.length > 0) {
        await activateSession(remaining[0]);
      } else {
        setActiveSession(null);
        setCandidates([]);
        setStagedSources([]);
      }
    }
  };

  // 5. Update Session Name
  const handleSaveSessionName = async () => {
    if (!activeSession) return;
    const trimmed = sessionName.trim() || "Untitled Screening Session";
    const updated = { ...activeSession, name: trimmed, updatedAt: Date.now() };
    await db.screeningSessions.put(updated);
    setActiveSession(updated);
    setSessions((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    setIsEditingName(false);
  };

  // 6. Sync candidate changes to DB
  const syncCandidatesToDb = useCallback(async (
    updatedCandidates: ScreeningCandidate[],
    updatedSessionMeta?: Partial<ScreeningSession>
  ) => {
    if (!activeSession) return;

    const total = updatedCandidates.length;
    const included = updatedCandidates.filter((c) => c.decision === "included").length;
    const excluded = updatedCandidates.filter((c) => c.decision === "excluded").length;
    const screened = included + excluded;

    const updatedSession: ScreeningSession = {
      ...activeSession,
      totalCount: total,
      screenedCount: screened,
      includedCount: included,
      excludedCount: excluded,
      updatedAt: Date.now(),
      ...updatedSessionMeta,
    };

    // Bulk put candidates with sessionId
    const itemsToStore = updatedCandidates.map((c) => ({
      ...c,
      sessionId: activeSession.id,
    }));

    // Bulk upsert candidate records without destructive table purging
    await db.screeningItems.bulkPut(itemsToStore as ScreeningItem[]);
    await db.screeningSessions.put(updatedSession);

    setActiveSession(updatedSession);
    setSessions((prev) => prev.map((s) => (s.id === updatedSession.id ? updatedSession : s)));
  }, [activeSession]);

  // 7. Simulated upload progress helper
  const simulateUploadProgress = async (
    fileName: string,
    executeExtraction: () => Promise<ScreeningCandidate[]>
  ) => {
    setUploadProgress({
      isUploading: true,
      progress: 20,
      stepLabel: "Reading file stream...",
      fileName,
    });

    await new Promise((r) => setTimeout(r, 120));

    setUploadProgress({
      isUploading: true,
      progress: 55,
      stepLabel: "Parsing citation schema & abstracts...",
      fileName,
    });

    const parsed = await executeExtraction();

    setUploadProgress({
      isUploading: true,
      progress: 85,
      stepLabel: "Cross-referencing & deduplicating records...",
      fileName,
    });

    await new Promise((r) => setTimeout(r, 150));

    setUploadProgress({
      isUploading: false,
      progress: 100,
      stepLabel: "Import complete",
      fileName,
    });

    return parsed;
  };

  // 8. Add a file to Staging
  const handleStageFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const candidates = await simulateUploadProgress(file.name, async () => {
        const text = await file.text();
        if (!text || !text.trim()) {
          throw new Error("File is empty.");
        }
        const raw = parseUniversalFile(text, file.name);
        return raw.map((p, idx) => ({
          id: p.id || `file-${Date.now()}-${idx}`,
          title: p.title || "Untitled Paper",
          abstract: p.abstract || "No abstract available.",
          authors: p.authors || ["Unknown Author"],
          year: p.year || 2024,
          journal: p.journal,
          doi: p.doi,
          sourceOrigin: file.name,
          decision: "pending" as const,
          relevanceScore: 50,
        }));
      });

      if (candidates.length === 0) {
        alert(
          `Could not detect valid candidate papers in "${file.name}".\n\nPlease ensure your file is in CSV, TSV, RIS, BibTeX, or JSON format.`
        );
        return;
      }

      const ext = file.name.split(".").pop()?.toLowerCase() || "csv";
      const newSource: StagedSource = {
        id: `source-${Date.now()}`,
        name: file.name,
        type: isStagedFileType(ext) ? ext : "csv",
        count: candidates.length,
        candidates,
      };

      setStagedSources((prev) => [...prev, newSource]);
    } catch (err) {
      alert(`Error reading file "${file.name}": ${err instanceof Error ? err.message : String(err)}`);
    } finally {
      if (fileInputRef.current) fileInputRef.current.value = "";
      if (addMoreFileInputRef.current) addMoreFileInputRef.current.value = "";
    }
  };

  // 9. Add a benchmark to Staging
  const handleStageBenchmark = (benchmarkId: string) => {
    const bm = BENCHMARK_SCREENING_DATASETS.find((b) => b.id === benchmarkId);
    if (!bm) return;

    const bmCandidates: ScreeningCandidate[] = bm.papers.map((p, idx) => ({
      id: `bm-${benchmarkId}-${idx}-${Date.now()}`,
      title: p.title,
      abstract: p.abstract,
      authors: p.authors,
      year: p.year,
      journal: p.journal,
      doi: p.doi,
      sourceOrigin: `Benchmark: ${bm.name}`,
      decision: "pending",
      relevanceScore: 50,
    }));

    const newSource: StagedSource = {
      id: `source-${Date.now()}`,
      name: `Benchmark: ${bm.name}`,
      type: "benchmark",
      count: bmCandidates.length,
      candidates: bmCandidates,
    };

    setStagedSources((prev) => [...prev, newSource]);
  };

  // 10. Add from Notebook to Staging
  const handleStageNotebook = async (nbId: string) => {
    const nb = notebooks.find((n) => n.id === nbId);
    if (!nb) return;

    const sources = await db.sources.where("notebookId").equals(nbId).toArray();
    if (sources.length === 0) {
      alert(`Notebook "${nb.title}" has no papers saved.`);
      return;
    }

    const nbCandidates: ScreeningCandidate[] = sources.map((s, idx) => ({
      id: `nb-${s.id}-${idx}`,
      title: s.title,
      abstract: s.abstract || "No abstract recorded in notebook.",
      authors: s.authors || ["Unknown Author"],
      year: s.year || 2024,
      journal: s.journal,
      doi: s.doi,
      sourceOrigin: `Notebook: ${nb.title}`,
      decision: "pending",
      relevanceScore: 50,
    }));

    const newSource: StagedSource = {
      id: `source-${Date.now()}`,
      name: `Notebook: ${nb.emoji} ${nb.title}`,
      type: "notebook",
      count: nbCandidates.length,
      candidates: nbCandidates,
    };

    setStagedSources((prev) => [...prev, newSource]);
  };

  // 11. Remove a Staged Source
  const handleRemoveStagedSource = (sourceId: string) => {
    setStagedSources((prev) => prev.filter((s) => s.id !== sourceId));
  };

  // 12. Compute overall deduplicated candidates from Staged Sources
  const allStagedRaw = stagedSources.flatMap((s) => s.candidates);
  const dedupStaged = deduplicateCandidates([], allStagedRaw);

  // 13. Finalize Staging -> Start Screening Session
  const handleStartScreeningFromStaged = async () => {
    if (stagedSources.length === 0) return;

    let targetSession = activeSession;
    if (!targetSession) {
      const newSessionId = `session-${Date.now()}`;
      targetSession = {
        id: newSessionId,
        name: sessionName || "Systematic Review Screening",
        createdAt: Date.now(),
        updatedAt: Date.now(),
        totalCount: dedupStaged.uniqueCandidates.length,
        screenedCount: 0,
        includedCount: 0,
        excludedCount: 0,
        consecutiveExcludes: 0,
        sourcesList: stagedSources.map((s) => `${s.name} (${s.count})`),
        duplicatesRemoved: dedupStaged.duplicateCount,
      };
      await db.screeningSessions.put(targetSession);
      setSessions((prev) => [targetSession!, ...prev]);
      setActiveSession(targetSession);
      localStorage.setItem(STORAGE_KEYS.activeScreeningSession, newSessionId);
    } else {
      targetSession = {
        ...targetSession,
        sourcesList: [
          ...(targetSession.sourcesList || []),
          ...stagedSources.map((s) => `${s.name} (${s.count})`),
        ],
        duplicatesRemoved: (targetSession.duplicatesRemoved || 0) + dedupStaged.duplicateCount,
      };
    }

    setDuplicatesRemoved(dedupStaged.duplicatesRemoved);
    setCandidates(dedupStaged.uniqueCandidates);
    setStagedSources([]);
    await syncCandidatesToDb(dedupStaged.uniqueCandidates, targetSession);
  };

  // 14. Ingest Additional Sources into ACTIVE screening session
  const handleIngestMoreSources = async (incoming: ScreeningCandidate[], sourceLabel: string) => {
    if (!activeSession) return;

    // Deduplicate incoming candidates against already existing candidates
    const result = deduplicateCandidates(candidates, incoming);

    setDuplicatesRemoved((prev) => [...prev, ...result.duplicatesRemoved]);
    const updatedCandidates = classifier.retrainAndRank(result.uniqueCandidates);
    setCandidates(updatedCandidates);

    const updatedSources = [
      ...(activeSession.sourcesList || []),
      `${sourceLabel} (${incoming.length})`,
    ];

    await syncCandidatesToDb(updatedCandidates, {
      sourcesList: updatedSources,
      duplicatesRemoved: (activeSession.duplicatesRemoved || 0) + result.duplicateCount,
    });

    alert(
      `Added ${incoming.length} records from "${sourceLabel}".\nMerged ${result.duplicateCount} duplicates.\nTotal active candidate pool is now ${result.uniqueCandidates.length} papers.`
    );
    setShowAddSourcesModal(false);
  };

  // 15. The active candidate to screen is the first pending candidate
  const pendingCandidates = candidates.filter((c) => c.decision === "pending");
  const currentCandidate = pendingCandidates.length > 0 ? pendingCandidates[0] : null;

  const totalCount = candidates.length;
  const includedCount = candidates.filter((c) => c.decision === "included").length;
  const excludedCount = candidates.filter((c) => c.decision === "excluded").length;
  const screenedCount = includedCount + excludedCount;
  const progressPercent = totalCount > 0 ? Math.round((screenedCount / totalCount) * 100) : 0;

  // 16. Decision Handler (Include / Exclude)
  const handleDecision = useCallback(async (decision: "included" | "excluded") => {
    if (!currentCandidate || !activeSession) return;

    setFeedbackAnimation(decision);
    setTimeout(() => setFeedbackAnimation(null), 300);

    const targetItemId = currentCandidate.id;
    const now = Date.now();

    const updatedCandidate: ScreeningCandidate = {
      ...currentCandidate,
      decision,
      screenedAt: now,
    };

    const newConsecutive = decision === "excluded" ? consecutiveExcludes + 1 : 0;
    setConsecutiveExcludes(newConsecutive);
    setHistory((prev) => [...prev, { id: targetItemId, decision }]);

    const updatedCandidates = candidates.map((c) =>
      c.id === targetItemId ? updatedCandidate : c
    );

    const reranked = classifier.retrainAndRank(updatedCandidates);
    setCandidates(reranked);

    // Compute updated session counts
    const newIncluded = updatedCandidates.filter((c) => c.decision === "included").length;
    const newExcluded = updatedCandidates.filter((c) => c.decision === "excluded").length;
    const newScreened = newIncluded + newExcluded;

    const updatedSession: ScreeningSession = {
      ...activeSession,
      screenedCount: newScreened,
      includedCount: newIncluded,
      excludedCount: newExcluded,
      consecutiveExcludes: newConsecutive,
      updatedAt: now,
    };

    // Atomic single-item update in Dexie — NO table wiping or bulk churning!
    await db.screeningItems.update(targetItemId, {
      decision,
      screenedAt: now,
    });
    await db.screeningSessions.update(activeSession.id, {
      screenedCount: newScreened,
      includedCount: newIncluded,
      excludedCount: newExcluded,
      consecutiveExcludes: newConsecutive,
      updatedAt: now,
    });

    setActiveSession(updatedSession);
    setSessions((prev) => prev.map((s) => (s.id === updatedSession.id ? updatedSession : s)));
  }, [currentCandidate, activeSession, consecutiveExcludes, candidates, classifier]);

  // 17. Undo Last Decision
  const handleUndo = useCallback(async () => {
    if (history.length === 0 || !activeSession) return;
    const lastAction = history[history.length - 1];
    const targetItemId = lastAction.id;
    const now = Date.now();

    const updatedCandidates = candidates.map((c) =>
      c.id === targetItemId
        ? { ...c, decision: "pending" as const, screenedAt: undefined }
        : c
    );

    setHistory((prev) => prev.slice(0, -1));
    const reranked = classifier.retrainAndRank(updatedCandidates);
    setCandidates(reranked);

    const newIncluded = updatedCandidates.filter((c) => c.decision === "included").length;
    const newExcluded = updatedCandidates.filter((c) => c.decision === "excluded").length;
    const newScreened = newIncluded + newExcluded;

    const updatedSession: ScreeningSession = {
      ...activeSession,
      screenedCount: newScreened,
      includedCount: newIncluded,
      excludedCount: newExcluded,
      updatedAt: now,
    };

    // Atomic single-item rollback in Dexie — NO table wiping!
    await db.screeningItems.update(targetItemId, {
      decision: "pending",
      screenedAt: undefined,
    });
    await db.screeningSessions.update(activeSession.id, {
      screenedCount: newScreened,
      includedCount: newIncluded,
      excludedCount: newExcluded,
      updatedAt: now,
    });

    setActiveSession(updatedSession);
    setSessions((prev) => prev.map((s) => (s.id === updatedSession.id ? updatedSession : s)));
  }, [history, activeSession, candidates, classifier]);

  // 18. Keyboard Shortcuts (I = Include, E = Exclude, U = Undo)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (
        document.activeElement?.tagName === "INPUT" ||
        document.activeElement?.tagName === "TEXTAREA" ||
        showSessionsModal ||
        showDuplicateModal ||
        showAddSourcesModal
      ) {
        return;
      }

      if (e.key.toLowerCase() === "i") {
        e.preventDefault();
        handleDecision("included");
      } else if (e.key.toLowerCase() === "e") {
        e.preventDefault();
        handleDecision("excluded");
      } else if (e.key.toLowerCase() === "u") {
        e.preventDefault();
        handleUndo();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [currentCandidate, history, showSessionsModal, showDuplicateModal, showAddSourcesModal, handleDecision, handleUndo]);

  // 19. Flow to Review Notebook
  const handleSaveToNotebook = async () => {
    if (!selectedNotebookId) return;
    const included = candidates.filter((c) => c.decision === "included");
    if (included.length === 0) return;

    const now = Date.now();
    const newSources: Source[] = included.map((item, idx) => ({
      id: `src-${now}-${idx}-${Math.random().toString(36).substring(2, 6)}`,
      notebookId: selectedNotebookId,
      title: item.title,
      abstract: item.abstract,
      authors: item.authors,
      year: item.year,
      journal: item.journal,
      doi: item.doi,
      status: "ready" as const,
      addedAt: now,
    }));

    // Single atomic bulk transaction
    await db.sources.bulkPut(newSources);

    const count = await db.sources.where("notebookId").equals(selectedNotebookId).count();
    await db.notebooks.update(selectedNotebookId, {
      sourcesCount: count,
      updatedAt: now,
    });

    alert(`Successfully transferred ${included.length} screened papers to selected notebook!`);
  };

  // 20. Export PRISMA Decision Matrix
  const handleExportPrisma = () => {
    const csvRows = [
      [
        "Title",
        "Authors",
        "Year",
        "Journal",
        "DOI",
        "Source_Origin",
        "Screening_Decision",
        "Predicted_Relevance_Score",
        "Screened_Timestamp",
      ],
    ];

    candidates.forEach((c) => {
      csvRows.push([
        `"${c.title.replace(/"/g, '""')}"`,
        `"${c.authors.join(", ")}"`,
        `${c.year || ""}`,
        `"${c.journal || ""}"`,
        `${c.doi || ""}`,
        `"${c.sourceOrigin || ""}"`,
        c.decision.toUpperCase(),
        `${c.relevanceScore || 0}%`,
        c.screenedAt ? new Date(c.screenedAt).toISOString() : "",
      ]);
    });

    const csvContent = csvRows.map((r) => r.join(",")).join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `PRISMA_Decisions_${(activeSession?.name || "Screening").replace(/\s+/g, "_")}_${Date.now()}.csv`;
    a.click();
  };

  return (
    <div className="w-full space-y-6 animate-fade-in-up">
      {/* =========================================================================
          TOP COMMAND BAR & SESSION IDENTITY
      ========================================================================= */}
      <div className="fernly-card p-6 sm:p-7 rounded-[2rem] flex flex-col gap-5 border border-[var(--card-bdr)]">
        {/* Row 1: Session Selector & Actions */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
          {/* Active Session Name with Inline Edit */}
          <div className="flex items-center gap-3 flex-wrap">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--g-950)] text-[var(--g-300)] border border-[var(--g-800)] shadow-xs flex-shrink-0">
              <Sparkles className="h-5 w-5" />
            </div>

            <div className="space-y-0.5">
              <div className="flex items-center gap-2 flex-wrap">
                {isEditingName ? (
                  <div className="flex items-center gap-1.5">
                    <input
                      type="text"
                      value={sessionName}
                      onChange={(e) => setSessionName(e.target.value)}
                      onKeyDown={(e) => e.key === "Enter" && handleSaveSessionName()}
                      className="fernly-input py-1 px-3 text-sm font-bold w-64 sm:w-80 rounded-xl"
                      autoFocus
                    />
                    <button
                      onClick={handleSaveSessionName}
                      className="btn-fernly-primary py-1 px-3 rounded-xl text-xs font-semibold"
                    >
                      Save
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-2 group">
                    <h2
                      onClick={() => setIsEditingName(true)}
                      className="text-base sm:text-lg font-bold tracking-tight text-[var(--ink)] cursor-pointer hover:text-[var(--g-600)] transition-colors"
                      title="Click to rename session"
                    >
                      {activeSession?.name || "Systematic Review Screening"}
                    </h2>
                    <button
                      onClick={() => setIsEditingName(true)}
                      className="text-[var(--ink-muted)] hover:text-[var(--ink)] opacity-60 group-hover:opacity-100 transition-opacity cursor-pointer"
                      title="Rename session"
                    >
                      <Edit3 className="h-3.5 w-3.5" />
                    </button>
                  </div>
                )}

                <span className="fernly-badge fernly-badge-leaf text-[10px] font-semibold">
                  Active Learning
                </span>
              </div>

              {/* Auto-saved timestamp indicator */}
              <div className="flex items-center gap-2 text-[11px] text-[var(--ink-muted)]">
                <span className="flex items-center gap-1 text-[var(--g-600)] dark:text-[var(--g-400)] font-medium">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                  Auto-saved in IndexedDB
                </span>
                <span>·</span>
                <span>{candidates.length} unique papers</span>
                {(activeSession?.duplicatesRemoved || duplicatesRemoved.length > 0) && (
                  <>
                    <span>·</span>
                    <button
                      onClick={() => setShowDuplicateModal(true)}
                      className="text-[var(--g-600)] hover:underline cursor-pointer"
                    >
                      {activeSession?.duplicatesRemoved || duplicatesRemoved.length} duplicates merged
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Session Switcher & New Session Buttons */}
          <div className="flex items-center gap-2.5 self-start md:self-auto flex-wrap">
            <button
              onClick={() => setShowSessionsModal(true)}
              className="btn-fernly-ghost px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border border-[var(--card-bdr)] shadow-xs"
            >
              <FolderSync className="h-3.5 w-3.5 text-[var(--g-600)]" />
              <span>Sessions ({sessions.length})</span>
            </button>

            <button
              onClick={() => handleCreateNewSession()}
              className="btn-fernly-primary px-4 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 shadow-xs"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>New Screening</span>
            </button>
          </div>
        </div>

        {/* Row 2: Live PRISMA Tally Pill */}
        <div className="pt-3 border-t border-[var(--card-bdr)] flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3 bg-[var(--panel)] p-2 rounded-2xl border border-[var(--card-bdr)]">
            <div className="text-center px-3">
              <span className="text-[10px] font-semibold text-[var(--ink-muted)] block">Progress</span>
              <span className="text-sm font-bold text-[var(--ink)]">
                {screenedCount} / {totalCount} ({progressPercent}%)
              </span>
            </div>
            <div className="h-6 w-px bg-[var(--card-bdr)]" />
            <div className="text-center px-3">
              <span className="text-[10px] font-semibold text-[var(--g-600)] block">Included</span>
              <span className="text-sm font-bold text-[var(--g-700)] dark:text-[var(--g-300)]">
                {includedCount}
              </span>
            </div>
            <div className="h-6 w-px bg-[var(--card-bdr)]" />
            <div className="text-center px-3">
              <span className="text-[10px] font-semibold text-rose-600 block">Excluded</span>
              <span className="text-sm font-bold text-rose-600">{excludedCount}</span>
            </div>
          </div>

          {candidates.length > 0 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setShowAddSourcesModal(true)}
                className="btn-fernly-ghost px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border border-[var(--card-bdr)] hover:border-[var(--g-500)]"
              >
                <Plus className="h-3.5 w-3.5 text-[var(--g-600)]" />
                <span>+ Ingest More Sources</span>
              </button>

              <button
                onClick={handleExportPrisma}
                className="btn-fernly-ghost px-3.5 py-2 rounded-xl text-xs font-semibold flex items-center gap-1.5 border border-[var(--card-bdr)]"
                title="Export PRISMA Matrix (.csv)"
              >
                <Download className="h-3.5 w-3.5" />
                <span>PRISMA Export</span>
              </button>
            </div>
          )}
        </div>
      </div>

      {/* =========================================================================
          FILE UPLOAD PROGRESS BAR (Triggered during parsing)
      ========================================================================= */}
      {uploadProgress.isUploading && (
        <div className="fernly-card p-5 rounded-2xl border border-[var(--g-500)]/40 bg-[var(--panel)] space-y-2 animate-pulse">
          <div className="flex items-center justify-between text-xs font-medium">
            <span className="text-[var(--ink)] flex items-center gap-2">
              <Sparkles className="h-4 w-4 text-[var(--g-600)] animate-spin" />
              <span>{uploadProgress.stepLabel}</span>
              <span className="text-[var(--ink-muted)]">({uploadProgress.fileName})</span>
            </span>
            <span className="font-bold text-[var(--g-600)] font-mono">
              {uploadProgress.progress}%
            </span>
          </div>
          <div className="w-full bg-[var(--card-bdr)] h-2 rounded-full overflow-hidden">
            <div
              className="bg-[var(--g-600)] h-full transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress.progress}%` }}
            />
          </div>
        </div>
      )}

      {/* =========================================================================
          STAGE 1: MULTI-SOURCE STAGING & SETUP (If no candidates started yet)
      ========================================================================= */}
      {candidates.length === 0 ? (
        <div className="fernly-card p-6 sm:p-9 rounded-[2rem] space-y-8 max-w-4xl mx-auto border border-[var(--card-bdr)]">
          <div className="text-center space-y-2 max-w-xl mx-auto">
            <div className="h-14 w-14 mx-auto rounded-3xl bg-[var(--panel)] border border-[var(--card-bdr)] flex items-center justify-center text-[var(--g-600)] shadow-xs">
              <Layers className="h-7 w-7" />
            </div>
            <h3 className="text-xl font-bold text-[var(--ink)]">
              Build Your Systematic Review Callset
            </h3>
            <p className="text-xs text-[var(--ink-muted)] leading-relaxed">
              Combine multiple databases (e.g. PubMed CSV + Scopus RIS + Web of Science BibTeX + Notebooks).
              Vellum automatically detects duplicates and merges identical papers before screening starts.
            </p>
          </div>

          {/* Staged Sources Shelf */}
          {stagedSources.length > 0 && (
            <div className="p-5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-2">
                  <Database className="h-4 w-4 text-[var(--g-600)]" />
                  <span>Staged Article Sources ({stagedSources.length})</span>
                </span>
                <span className="text-[11px] font-mono text-[var(--ink-muted)]">
                  {allStagedRaw.length} raw records
                </span>
              </div>

              {/* Source Chips */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {stagedSources.map((source) => (
                  <div
                    key={source.id}
                    className="p-3 rounded-xl bg-[var(--card)] border border-[var(--card-bdr)] flex items-center justify-between gap-3 text-xs"
                  >
                    <div className="flex items-center gap-2.5 min-w-0">
                      <span className="fernly-badge fernly-badge-leaf text-[9px] uppercase font-bold flex-shrink-0">
                        {source.type}
                      </span>
                      <span className="font-semibold text-[var(--ink)] truncate">
                        {source.name}
                      </span>
                    </div>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <span className="text-[11px] text-[var(--ink-muted)] font-mono">
                        {source.count} papers
                      </span>
                      <button
                        onClick={() => handleRemoveStagedSource(source.id)}
                        className="text-[var(--ink-muted)] hover:text-rose-600 cursor-pointer p-1"
                        title="Remove source"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Deduplication Live Pill */}
              <div className="pt-3 border-t border-[var(--card-bdr)] flex flex-wrap items-center justify-between gap-3 text-xs">
                <div className="flex items-center gap-2 text-[var(--ink-muted)]">
                  <ShieldCheck className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <span>
                    <strong>{dedupStaged.uniqueCandidates.length}</strong> unique papers ready ·{" "}
                    <span className="text-emerald-700 dark:text-emerald-300 font-semibold">
                      {dedupStaged.duplicateCount} duplicates merged
                    </span>
                  </span>
                </div>

                {dedupStaged.duplicateCount > 0 && (
                  <button
                    onClick={() => {
                      setDuplicatesRemoved(dedupStaged.duplicatesRemoved);
                      setShowDuplicateModal(true);
                    }}
                    className="text-[11px] font-semibold text-[var(--g-600)] hover:underline cursor-pointer"
                  >
                    Inspect merged duplicates →
                  </button>
                )}
              </div>

              {/* Start Screening Action */}
              <div className="pt-2">
                <button
                  onClick={handleStartScreeningFromStaged}
                  className="btn-fernly-primary w-full py-3 rounded-full text-xs font-bold shadow-md cursor-pointer flex items-center justify-center gap-2"
                >
                  <Sparkles className="h-4 w-4" />
                  <span>
                    Start Screening {dedupStaged.uniqueCandidates.length} Unique Papers
                  </span>
                </button>
              </div>
            </div>
          )}

          {/* Source Adders Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-left">
            {/* Box 1: File Ingestion */}
            <div className="p-5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] flex flex-col justify-between space-y-4">
              <div>
                <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-2">
                  <Upload className="h-4 w-4 text-[var(--g-600)]" />
                  <span>Add Database File</span>
                </span>
                <p className="text-[11px] text-[var(--ink-muted)] mt-1.5 leading-relaxed">
                  Ingest files from PubMed, Scopus, Rayyan, Web of Science, or Zotero.
                  You can upload multiple files sequentially.
                </p>
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {["CSV", "TSV", "RIS", "BibTeX", "JSON"].map((ext) => (
                    <span
                      key={ext}
                      className="px-2 py-0.5 rounded-md text-[10px] font-mono bg-[var(--card)] border border-[var(--card-bdr)] text-[var(--ink-muted)]"
                    >
                      .{ext.toLowerCase()}
                    </span>
                  ))}
                </div>
              </div>

              <label className="btn-fernly-primary px-4 py-2.5 rounded-full text-xs font-semibold cursor-pointer shadow-xs flex items-center justify-center gap-2 w-full">
                <Upload className="h-4 w-4" />
                <span>Choose File to Stage</span>
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".ris,.txt,.bib,.csv,.tsv,.json"
                  onChange={handleStageFileUpload}
                  className="hidden"
                />
              </label>
            </div>

            {/* Box 2: Notebook & Benchmarks */}
            <div className="p-5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] flex flex-col justify-between space-y-4">
              <div>
                <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-2">
                  <BookOpen className="h-4 w-4 text-[var(--g-600)]" />
                  <span>Add from Notebook or Benchmark</span>
                </span>
                <p className="text-[11px] text-[var(--ink-muted)] mt-1.5 leading-relaxed">
                  Stage references directly from an existing research notebook, or pick a standard ASReview benchmark dataset.
                </p>
              </div>

              <div className="space-y-2">
                {notebooks.length > 0 && (
                  <select
                    defaultValue=""
                    onChange={(e) => {
                      if (e.target.value) handleStageNotebook(e.target.value);
                    }}
                    className="fernly-input w-full rounded-xl text-xs py-2"
                  >
                    <option value="" disabled>
                      Stage from a notebook...
                    </option>
                    {notebooks.map((nb) => (
                      <option key={nb.id} value={nb.id}>
                        {nb.emoji} {nb.title} ({nb.sourcesCount || 0} papers)
                      </option>
                    ))}
                  </select>
                )}

                <select
                  defaultValue=""
                  onChange={(e) => {
                    if (e.target.value) handleStageBenchmark(e.target.value);
                  }}
                  className="fernly-input w-full rounded-xl text-xs py-2"
                >
                  <option value="" disabled>
                    Stage a benchmark dataset...
                  </option>
                  {BENCHMARK_SCREENING_DATASETS.map((bm) => (
                    <option key={bm.id} value={bm.id}>
                      {bm.name} ({bm.totalCount} papers)
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </div>
        </div>
      ) : (
        /* =========================================================================
            STAGE 2: ACTIVE SCREENING WORKSPACE
        ========================================================================= */
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* LEFT: Candidate Screening Card */}
          <div className="lg:col-span-8 space-y-4">
            {currentCandidate ? (
              <div
                className={`fernly-card p-6 sm:p-8 rounded-[2rem] space-y-5 transition-all duration-300 relative border border-[var(--card-bdr)] ${
                  feedbackAnimation === "included"
                    ? "ring-4 ring-emerald-500/40 bg-emerald-50/10"
                    : feedbackAnimation === "excluded"
                    ? "ring-4 ring-rose-500/40 bg-rose-50/10"
                    : ""
                }`}
              >
                {/* Card Top Metadata & Relevance Pill */}
                <div className="flex items-center justify-between gap-3 flex-wrap">
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-[var(--ink-muted)] font-mono">
                      Paper {screenedCount + 1} of {totalCount}
                    </span>
                    <span className="text-[11px] text-[var(--ink-muted)]">
                      · {currentCandidate.year || 2024}
                    </span>
                    {currentCandidate.sourceOrigin && (
                      <span className="fernly-badge fernly-badge-mint text-[9px] font-mono">
                        {currentCandidate.sourceOrigin}
                      </span>
                    )}
                  </div>

                  {/* Active Learning Relevance Probability Score */}
                  <div className="flex items-center gap-1.5">
                    <span className="fernly-badge fernly-badge-leaf text-xs font-mono font-bold flex items-center gap-1">
                      <TrendingUp className="h-3.5 w-3.5" />
                      <span>{currentCandidate.relevanceScore || 50}% Relevance Match</span>
                    </span>
                  </div>
                </div>

                {/* Title */}
                <div>
                  <h3 className="text-lg sm:text-xl font-bold text-[var(--ink)] leading-snug tracking-tight">
                    {currentCandidate.title}
                  </h3>
                  <p className="text-xs text-[var(--ink-muted)] mt-1.5 font-medium">
                    {currentCandidate.authors.join(", ")} ·{" "}
                    <span className="italic">{currentCandidate.journal || "Journal / Proceedings"}</span>
                  </p>
                  {currentCandidate.doi && (
                    <a
                      href={`https://doi.org/${currentCandidate.doi}`}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1 text-[11px] text-[var(--g-600)] dark:text-[var(--g-400)] hover:underline mt-1 font-mono"
                    >
                      <span>https://doi.org/{currentCandidate.doi}</span>
                      <ExternalLink className="h-3 w-3" />
                    </a>
                  )}
                </div>

                {/* Abstract Canvas */}
                <div className="p-5 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] space-y-2">
                  <span className="text-[10px] font-bold text-[var(--ink-muted)] uppercase tracking-wider block">
                    Abstract
                  </span>
                  <p className="text-xs sm:text-sm text-[var(--ink)] leading-relaxed font-sans select-text">
                    {currentCandidate.abstract}
                  </p>
                </div>

                {/* Action Bar with Keyboard Controls */}
                <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-4 border-t border-[var(--card-bdr)]">
                  {/* Undo Button */}
                  <button
                    onClick={handleUndo}
                    disabled={history.length === 0}
                    className="btn-fernly-ghost px-4 py-2 rounded-full text-xs font-semibold disabled:opacity-40 cursor-pointer flex items-center gap-1.5"
                    title="Undo last decision (U)"
                  >
                    <RotateCcw className="h-3.5 w-3.5" />
                    <span>Undo</span>
                    <kbd className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-[var(--card)] border border-[var(--card-bdr)]">
                      U
                    </kbd>
                  </button>

                  {/* Primary Decision Triggers */}
                  <div className="flex items-center gap-3 w-full sm:w-auto">
                    {/* EXCLUDE BUTTON */}
                    <button
                      onClick={() => handleDecision("excluded")}
                      className="flex-1 sm:flex-initial flex items-center justify-center gap-2 px-6 py-3 rounded-full border border-rose-300 dark:border-rose-900 bg-rose-50 dark:bg-rose-950/40 text-rose-700 dark:text-rose-300 hover:bg-rose-100 dark:hover:bg-rose-900/40 font-bold text-xs sm:text-sm shadow-xs transition-all cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
                      title="Exclude paper (E)"
                    >
                      <XCircle className="h-4 w-4" />
                      <span>Exclude</span>
                      <kbd className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-white/60 dark:bg-black/30 border border-rose-300">
                        E
                      </kbd>
                    </button>

                    {/* INCLUDE BUTTON */}
                    <button
                      onClick={() => handleDecision("included")}
                      className="flex-1 sm:flex-initial btn-fernly-primary flex items-center justify-center gap-2 px-8 py-3 rounded-full font-bold text-xs sm:text-sm shadow-md transition-all cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
                      title="Include paper (I)"
                    >
                      <CheckCircle2 className="h-4 w-4 text-[#5dbd8b]" />
                      <span>Include</span>
                      <kbd className="px-1.5 py-0.5 rounded text-[9px] font-mono bg-white/20 text-white">
                        I
                      </kbd>
                    </button>
                  </div>
                </div>
              </div>
            ) : (
              /* All Screened Screen */
              <div className="fernly-card p-10 rounded-[2rem] text-center space-y-5 border border-[var(--card-bdr)]">
                <div className="h-16 w-16 mx-auto rounded-3xl bg-[var(--g-100)] text-[var(--g-800)] flex items-center justify-center shadow-xs">
                  <CheckCircle2 className="h-8 w-8" />
                </div>
                <div>
                  <h3 className="text-xl font-bold text-[var(--ink)]">
                    Screening Session Complete!
                  </h3>
                  <p className="text-xs text-[var(--ink-muted)] max-w-md mx-auto mt-1.5 leading-relaxed">
                    You have reviewed all {totalCount} candidate papers in &quot;{activeSession?.name}&quot;.{" "}
                    {includedCount} papers met your inclusion criteria.
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
                  <button
                    onClick={handleExportPrisma}
                    className="btn-fernly-primary px-5 py-2.5 rounded-full text-xs font-semibold cursor-pointer shadow-xs flex items-center gap-2"
                  >
                    <Download className="h-4 w-4" />
                    <span>Export PRISMA Matrix (.csv)</span>
                  </button>

                  <button
                    onClick={() => handleCreateNewSession()}
                    className="btn-fernly-ghost px-5 py-2.5 rounded-full text-xs font-semibold cursor-pointer flex items-center gap-2 border border-[var(--card-bdr)]"
                  >
                    <Plus className="h-4 w-4" />
                    <span>Start Another Screening</span>
                  </button>
                </div>
              </div>
            )}
          </div>

          {/* RIGHT: Session Inspector & Stopping Heuristic */}
          <div className="lg:col-span-4 space-y-4">
            {/* Session Info & Actions */}
            <div className="fernly-card p-5 rounded-2xl space-y-3 border border-[var(--card-bdr)]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-1.5">
                  <Database className="h-4 w-4 text-[var(--g-600)]" />
                  <span>Session References</span>
                </span>
                <span className="text-[10px] text-[var(--ink-muted)] font-mono">
                  {totalCount} total
                </span>
              </div>

              {activeSession?.sourcesList && activeSession.sourcesList.length > 0 && (
                <div className="space-y-1.5">
                  {activeSession.sourcesList.map((src, i) => (
                    <div
                      key={i}
                      className="p-2 rounded-xl bg-[var(--panel)] border border-[var(--card-bdr)] text-[11px] text-[var(--ink)] flex items-center justify-between"
                    >
                      <span className="truncate">{src}</span>
                    </div>
                  ))}
                </div>
              )}

              <button
                onClick={() => setShowAddSourcesModal(true)}
                className="btn-fernly-ghost w-full py-2 rounded-xl text-xs font-semibold cursor-pointer flex items-center justify-center gap-1.5 border border-[var(--card-bdr)] hover:border-[var(--g-500)] text-[var(--g-600)]"
              >
                <Plus className="h-3.5 w-3.5" />
                <span>Add More Sources to Session</span>
              </button>
            </div>

            {/* Stopping Rule & Saturation Heuristic */}
            <div className="fernly-card p-5 rounded-2xl space-y-3 border border-[var(--card-bdr)]">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-1.5">
                  <ShieldCheck className="h-4 w-4 text-[var(--g-600)] dark:text-[var(--g-400)]" />
                  <span>Stopping Heuristic</span>
                </span>
                <span className="text-[10px] text-[var(--ink-muted)] font-mono">ASReview Rule</span>
              </div>

              <div className="p-3 rounded-xl bg-[var(--panel)] border border-[var(--card-bdr)] space-y-1.5">
                <div className="flex items-center justify-between text-xs">
                  <span className="text-[var(--ink-muted)]">Consecutive Excludes:</span>
                  <span className="font-bold text-[var(--ink)] font-mono">
                    {consecutiveExcludes} / 25
                  </span>
                </div>
                <div className="w-full bg-[var(--card-bdr)] h-1.5 rounded-full overflow-hidden">
                  <div
                    className="bg-[var(--g-600)] h-full transition-all"
                    style={{ width: `${Math.min(100, (consecutiveExcludes / 25) * 100)}%` }}
                  />
                </div>
                <p className="text-[10px] text-[var(--ink-muted)] mt-1">
                  {consecutiveExcludes >= 25
                    ? "✨ Saturation threshold reached! High statistical confidence that >95% of relevant literature has been identified."
                    : "The active learning model continuously bubbles up relevant papers first."}
                </p>
              </div>
            </div>

            {/* Notebook Integration: Flow Screened into Review Notebook */}
            <div className="fernly-card p-5 rounded-2xl space-y-3 border border-[var(--card-bdr)]">
              <span className="text-xs font-bold text-[var(--ink)] block">
                Flow into Review Notebook
              </span>
              <p className="text-[11px] text-[var(--ink-muted)] leading-relaxed">
                Send all {includedCount} included papers to a notebook for full-text PDF retrieval:
              </p>
              <select
                value={selectedNotebookId}
                onChange={(e) => setSelectedNotebookId(e.target.value)}
                className="fernly-input w-full rounded-xl text-xs py-2"
              >
                <option value="">Select destination notebook...</option>
                {notebooks.map((nb) => (
                  <option key={nb.id} value={nb.id}>
                    {nb.emoji} {nb.title} ({nb.sourcesCount || 0} papers)
                  </option>
                ))}
              </select>
              <button
                onClick={handleSaveToNotebook}
                disabled={!selectedNotebookId || includedCount === 0}
                className="btn-fernly-primary w-full py-2.5 rounded-full text-xs font-semibold shadow-xs disabled:opacity-50 cursor-pointer flex items-center justify-center gap-1.5"
              >
                <BookOpen className="h-3.5 w-3.5" />
                <span>Attach {includedCount} Papers to Notebook</span>
              </button>
            </div>

            {/* Included Papers Drawer Preview */}
            <div className="fernly-card p-5 rounded-2xl space-y-3 border border-[var(--card-bdr)]">
              <div
                onClick={() => setShowIncludedDrawer(!showIncludedDrawer)}
                className="flex items-center justify-between cursor-pointer"
              >
                <span className="text-xs font-bold text-[var(--ink)] flex items-center gap-1.5">
                  <CheckCircle2 className="h-4 w-4 text-[var(--g-600)]" />
                  <span>Included Papers ({includedCount})</span>
                </span>
                {showIncludedDrawer ? (
                  <ChevronDown className="h-4 w-4 text-[var(--ink-muted)]" />
                ) : (
                  <ChevronRight className="h-4 w-4 text-[var(--ink-muted)]" />
                )}
              </div>

              {showIncludedDrawer && (
                <div className="space-y-2 max-h-56 overflow-y-auto pt-2 border-t border-[var(--card-bdr)]">
                  {candidates
                    .filter((c) => c.decision === "included")
                    .map((item, idx) => (
                      <div
                        key={item.id}
                        className="p-2.5 rounded-xl bg-[var(--panel)] border border-[var(--card-bdr)] text-xs space-y-1"
                      >
                        <span className="font-bold text-[var(--ink)] line-clamp-1">
                          {idx + 1}. {item.title}
                        </span>
                        <p className="text-[10px] text-[var(--ink-muted)] truncate">
                          {item.authors[0] || "Author"} · {item.year || 2024}
                        </p>
                      </div>
                    ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* =========================================================================
          MODAL 1: SESSIONS HUB (Switch / Manage Multiple Screening Sessions)
      ========================================================================= */}
      {showSessionsModal && (
        <Modal
          isOpen={showSessionsModal}
          onClose={() => setShowSessionsModal(false)}
          title="Screening Sessions Studio"
          subtitle="Switch between saved review projects or launch a new screening."
          panelClassName="max-w-xl space-y-5"
        >
            {/* List of Sessions */}
            <div className="space-y-2.5 max-h-72 overflow-y-auto pr-1">
              {sessions.map((s) => {
                const isSelected = activeSession?.id === s.id;
                const percent =
                  s.totalCount > 0 ? Math.round((s.screenedCount / s.totalCount) * 100) : 0;

                return (
                  <div
                    key={s.id}
                    className={`p-4 rounded-2xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-3 ${
                      isSelected
                        ? "border-[var(--g-500)] bg-[var(--g-50)]/20 dark:bg-[var(--g-950)]/40"
                        : "border-[var(--card-bdr)] bg-[var(--panel)] hover:border-[var(--g-500)]/60"
                    }`}
                  >
                    <button
                      onClick={() => {
                        activateSession(s);
                        setShowSessionsModal(false);
                      }}
                      className="cursor-pointer space-y-1 flex-1 text-left"
                    >
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-sm text-[var(--ink)]">{s.name}</span>
                        {isSelected && (
                          <span className="fernly-badge fernly-badge-leaf text-[9px] font-bold">
                            Active
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-2 text-[11px] text-[var(--ink-muted)]">
                        <span>{s.totalCount} papers</span>
                        <span>·</span>
                        <span>
                          {s.screenedCount} screened ({percent}%)
                        </span>
                        <span>·</span>
                        <span className="text-emerald-600 font-semibold">{s.includedCount} inc</span>
                      </div>
                    </button>

                    <div className="flex items-center gap-2 flex-shrink-0">
                      <button
                        onClick={() => {
                          activateSession(s);
                          setShowSessionsModal(false);
                        }}
                        className="btn-fernly-primary px-3 py-1.5 rounded-xl text-xs font-semibold"
                      >
                        {isSelected ? "Resume" : "Open"}
                      </button>
                      <button
                        onClick={() => handleDeleteSession(s.id)}
                        className="text-[var(--ink-muted)] hover:text-rose-600 p-2 rounded-xl hover:bg-[var(--card)] cursor-pointer"
                        title={`Delete session ${s.name}`}
                        aria-label={`Delete session ${s.name}`}
                      >
                        <Trash2 className="h-4 w-4" aria-hidden="true" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Bottom: Create New Session */}
            <div className="pt-3 border-t border-[var(--card-bdr)] flex items-center justify-between">
              <button
                onClick={() => handleCreateNewSession()}
                className="btn-fernly-primary px-5 py-2.5 rounded-full text-xs font-semibold flex items-center gap-2"
              >
                <Plus className="h-4 w-4" aria-hidden="true" />
                <span>Start New Screening Session</span>
              </button>

              <button
                onClick={() => setShowSessionsModal(false)}
                className="btn-fernly-ghost px-4 py-2 rounded-full text-xs font-semibold"
              >
                Close
              </button>
            </div>
        </Modal>
      )}

      {/* =========================================================================
          MODAL 2: INGEST MORE SOURCES INTO ACTIVE SESSION
      ========================================================================= */}
      {showAddSourcesModal && (
        <Modal
          isOpen={showAddSourcesModal}
          onClose={() => setShowAddSourcesModal(false)}
          title={`Add Additional Sources to "${activeSession?.name ?? ""}"`}
          subtitle="New records will be deduplicated automatically against existing candidates."
          panelClassName="max-w-lg space-y-5"
        >

            <div className="space-y-4 pt-1">
              {/* File Upload Option */}
              <div className="p-4 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] space-y-2">
                <span className="text-xs font-bold text-[var(--ink)] block">
                  Upload Secondary File
                </span>
                <p className="text-[11px] text-[var(--ink-muted)]">
                  Select a CSV, TSV, RIS, BibTeX, or JSON file to merge into this review.
                </p>
                <label className="btn-fernly-primary px-4 py-2.5 rounded-full text-xs font-semibold cursor-pointer shadow-xs flex items-center justify-center gap-2 w-full">
                  <Upload className="h-4 w-4" aria-hidden="true" />
                  <span>Choose Additional File</span>
                  <input
                    ref={addMoreFileInputRef}
                    type="file"
                    accept=".ris,.txt,.bib,.csv,.tsv,.json"
                    aria-label="Choose an additional bibliographic file"
                    onChange={async (e) => {
                      const file = e.target.files?.[0];
                      if (!file) return;
                      const text = await file.text();
                      const parsed = parseUniversalFile(text, file.name).map((p, idx) => ({
                        id: p.id || `file-${Date.now()}-${idx}`,
                        title: p.title || "Untitled Paper",
                        abstract: p.abstract || "No abstract available.",
                        authors: p.authors || ["Unknown Author"],
                        year: p.year || 2024,
                        journal: p.journal,
                        doi: p.doi,
                        sourceOrigin: file.name,
                        decision: "pending" as const,
                        relevanceScore: 50,
                      }));
                      handleIngestMoreSources(parsed, file.name);
                    }}
                    className="hidden"
                  />
                </label>
              </div>

              {/* Notebook Option */}
              {notebooks.length > 0 && (
                <div className="p-4 rounded-2xl bg-[var(--panel)] border border-[var(--card-bdr)] space-y-2">
                  <label
                    htmlFor="screening-import-notebook"
                    className="text-xs font-bold text-[var(--ink)] block"
                  >
                    Import from a Notebook
                  </label>
                  <select
                    id="screening-import-notebook"
                    defaultValue=""
                    onChange={async (e) => {
                      const nbId = e.target.value;
                      if (!nbId) return;
                      const nb = notebooks.find((n) => n.id === nbId);
                      if (!nb) return;
                      const sources = await db.sources.where("notebookId").equals(nbId).toArray();
                      const parsed: ScreeningCandidate[] = sources.map((s, idx) => ({
                        id: `nb-${s.id}-${idx}`,
                        title: s.title,
                        abstract: s.abstract || "No abstract recorded in notebook.",
                        authors: s.authors || ["Unknown Author"],
                        year: s.year || 2024,
                        journal: s.journal,
                        doi: s.doi,
                        sourceOrigin: `Notebook: ${nb.title}`,
                        decision: "pending",
                        relevanceScore: 50,
                      }));
                      handleIngestMoreSources(parsed, `Notebook: ${nb.title}`);
                    }}
                    className="fernly-input w-full rounded-xl text-xs py-2"
                  >
                    <option value="" disabled>
                      Select notebook to merge...
                    </option>
                    {notebooks.map((nb) => (
                      <option key={nb.id} value={nb.id}>
                        {nb.emoji} {nb.title} ({nb.sourcesCount || 0} papers)
                      </option>
                    ))}
                  </select>
                </div>
              )}
            </div>
        </Modal>
      )}

      {/* =========================================================================
          MODAL 3: DUPLICATE RECORDS INSPECTION
      ========================================================================= */}
      {showDuplicateModal && (
        <Modal
          isOpen={showDuplicateModal}
          onClose={() => setShowDuplicateModal(false)}
          title="Deduplication Audit Report"
          subtitle={`${duplicatesRemoved.length} duplicate citations detected and merged across sources.`}
          icon={<ShieldCheck className="h-5 w-5 text-emerald-600" />}
          panelClassName="max-w-2xl space-y-4"
        >
            <div className="space-y-2 max-h-80 overflow-y-auto pr-1">
              {duplicatesRemoved.length === 0 ? (
                <p className="text-xs text-[var(--ink-muted)] py-4 text-center">
                  No duplicates were detected. All imported citations are unique.
                </p>
              ) : (
                duplicatesRemoved.map((dup, idx) => (
                  <div
                    key={idx}
                    className="p-3.5 rounded-xl bg-[var(--panel)] border border-[var(--card-bdr)] text-xs space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="fernly-badge fernly-badge-leaf text-[9px] uppercase font-bold">
                        {dup.reason === "doi_match"
                          ? "Exact DOI Match"
                          : dup.reason === "exact_title"
                          ? "Exact Title Match"
                          : "Fuzzy Title Similarity"}
                      </span>
                      <span className="text-[10px] text-[var(--ink-muted)] font-mono">
                        Source: {dup.source}
                      </span>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-[var(--ink-muted)] uppercase block">
                        Kept Reference:
                      </span>
                      <p className="font-semibold text-[var(--ink)] line-clamp-1">{dup.keptTitle}</p>
                    </div>

                    <div>
                      <span className="text-[10px] font-bold text-rose-500 uppercase block">
                        Merged Duplicate:
                      </span>
                      <p className="text-[var(--ink-muted)] line-clamp-1">{dup.duplicateTitle}</p>
                    </div>
                  </div>
                ))
              )}
            </div>

            <div className="pt-3 border-t border-[var(--card-bdr)] flex justify-end">
              <button
                onClick={() => setShowDuplicateModal(false)}
                className="btn-fernly-primary px-5 py-2 rounded-full text-xs font-semibold"
              >
                Done
              </button>
            </div>
        </Modal>
      )}
    </div>
  );
}
