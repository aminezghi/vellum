"use client";

import React, { useEffect, useRef } from "react";
import {
  Sparkles,
  BookOpen,
  Layers,
  Search,
  Plus,
  Moon,
  Sun,
  Flame,
  Trash2,
  DownloadCloud,
  CheckCircle2,
  GitFork,
} from "lucide-react";
import {
  initializeAppearance,
  setAccent,
  setTheme,
  useAccent,
  useTheme,
} from "@/lib/theme";
import { AccentPicker, type FernlyAccent } from "@/components/AccentPicker";

export type { FernlyAccent };

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onNewNotebook: () => void;
  onClearNotebooks: () => void;
  totalNotebooks: number;
  viewMode?: "grid" | "list";
  setViewMode?: (mode: "grid" | "list") => void;
}

export function Header({
  activeTab,
  setActiveTab,
  searchQuery,
  setSearchQuery,
  onNewNotebook,
  onClearNotebooks,
  totalNotebooks,
}: HeaderProps) {
  // Theme and accent live in one place (see lib/theme); the DOM is the source
  // of truth, so neither needs to be mirrored into component state.
  const theme = useTheme();
  const activeAccent = useAccent();
  const isDarkMode = theme === "dark";
  const searchInputRef = useRef<HTMLInputElement>(null);

  // Apply the saved theme and accent once, on mount.
  useEffect(() => {
    initializeAppearance();
  }, []);

  const toggleTheme = () => {
    setTheme(isDarkMode ? "light" : "dark");
  };

  const handleAccentChange = (accent: FernlyAccent) => {
    setAccent(accent);
  };

  const tabs = [
    { id: "all", label: "Dashboard", shortLabel: "Home", icon: Sparkles },
    { id: "search", label: "Academic Search", shortLabel: "Search", icon: Search },
    { id: "connected", label: "Connected Papers", shortLabel: "Graph", icon: GitFork },
    { id: "screening", label: "AI Screening", shortLabel: "Screening", icon: CheckCircle2 },
    { id: "trends", label: "Trending Radar", shortLabel: "Trends", icon: Flame },
    { id: "downloader", label: "Batch Downloader", shortLabel: "Downloader", icon: DownloadCloud },
    { id: "my-notebooks", label: "My Notebooks", shortLabel: "Notebooks", icon: BookOpen },
    { id: "collections", label: "Collections", shortLabel: "Collections", icon: Layers },
  ];

  // Global Ctrl+K / Cmd+K search shortcut
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === "k") {
        e.preventDefault();
        searchInputRef.current?.focus();
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  return (
    <header className="sticky top-0 z-40 w-full bg-[var(--panel)]/95 backdrop-blur-md border-b border-[var(--hair)] transition-all duration-200">
      {/* Top Toolbar Row */}
      <div className="w-full px-4 sm:px-6 lg:px-8 py-2.5 flex items-center justify-between gap-3">
        {/* Brand Logo */}
        <div
          className="flex items-center gap-2.5 cursor-pointer group flex-shrink-0"
          onClick={() => setActiveTab("all")}
        >
          {/* Vellum Folded Folio Logo Mark */}
          <div className="flex h-9 w-9 items-center justify-center rounded-[12px] bg-[#0B0F19] border border-emerald-500/30 shadow-xs transition-transform group-hover:scale-105 overflow-hidden">
            <svg className="w-5 h-5" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
              <polygon points="112,96 186,96 256,358 206,445 112,96" fill="#10B981" />
              <polygon points="400,96 326,96 256,358 306,445 400,96" fill="#059669" />
              <polygon points="256,176 326,96 256,358 186,96" fill="#34D399" />
            </svg>
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="text-lg font-bold tracking-tight text-[var(--ink)]">
                Vellum <span className="text-xs font-normal text-[var(--muted)]">by Amine</span>
              </span>
              <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-[var(--g-100)] text-[var(--g-800)] border border-[var(--g-400)]/40 tracking-tight">
                Studio
              </span>
            </div>
          </div>
        </div>

        {/* Right Tools: Search, 4-Accent Palette Switcher, Theme Mode, View Mode, Clean, New Project */}
        <div className="flex items-center gap-2 sm:gap-2.5 flex-wrap justify-end">
          {/* Fernly Search input with ⌘K badge */}
          <div className="relative w-36 sm:w-44 md:w-56">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--faint)] pointer-events-none" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search local notebooks (⌘K)..."
              title="Filter local systematic review notebooks in your browser vault"
              className="w-full !pl-8.5 pr-10 py-1.5 text-xs bg-[var(--card)] border border-[var(--hair)] rounded-full text-[var(--ink)] placeholder-[var(--faint)] focus:outline-none focus:border-[var(--g-600)] focus:ring-2 focus:ring-[var(--g-400)]/20 transition-all shadow-xs"
            />
            <kbd className="hidden sm:inline-flex absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded text-[9px] font-mono text-[var(--faint)] bg-[var(--panel)] border border-[var(--hair)] pointer-events-none">
              ⌘K
            </kbd>
          </div>

          {/* Fernly accent colourway */}
          <div className="hidden sm:block">
            <AccentPicker value={activeAccent} onChange={handleAccentChange} />
          </div>

          {/* Theme Mode Toggle (☀️ Day Sage / 🌙 Night Forest) */}
          <button
            onClick={toggleTheme}
            className="p-1.5 sm:p-2 rounded-full bg-[var(--card)] border border-[var(--hair)] text-[var(--ink)] hover:bg-[var(--g-100)] transition-all cursor-pointer shadow-xs flex items-center justify-center"
            title={isDarkMode ? "Switch to Day (Sage Canvas)" : "Switch to Night (Nocturnal Forest)"}
          >
            {isDarkMode ? (
              <Sun className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[var(--g-400)]" />
            ) : (
              <Moon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[var(--g-700)]" />
            )}
          </button>

          {/* Clean / Reset Workspace Button */}
          {totalNotebooks > 0 && (
            <button
              onClick={onClearNotebooks}
              className="p-1.5 sm:p-2 rounded-full bg-[var(--card)] border border-red-200 dark:border-red-900/40 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 transition-all cursor-pointer shadow-xs flex items-center justify-center"
              title="Clean or reset notebooks from storage"
            >
              <Trash2 className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            </button>
          )}

          {/* Primary Action Button: New Notebook */}
          <button
            onClick={onNewNotebook}
            className="btn-fernly-primary !h-auto !py-1.5 sm:!py-2 !px-3 sm:!px-4 !text-xs !shadow-xs hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">New Project</span>
          </button>
        </div>
      </div>

      {/* Row 2: Dedicated Segmented Navigation Toolbar */}
      <div className="w-full px-4 sm:px-6 lg:px-8 pb-2 pt-0.5 border-t border-[var(--hair)]/40 overflow-x-auto no-scrollbar">
        <nav className="flex items-center gap-1.5 bg-[var(--card)] p-1 rounded-full border border-[var(--hair)] shadow-xs w-max min-w-full sm:min-w-0 sm:w-fit">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                title={tab.label}
                className={`relative flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? "text-white bg-gradient-to-b from-[var(--g-600)] to-[var(--g-800)] shadow-xs"
                    : "text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[var(--panel)]"
                }`}
              >
                <Icon className={`h-3.5 w-3.5 ${isActive ? "text-[var(--g-300)]" : "text-[var(--faint)]"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
