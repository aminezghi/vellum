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
  LayoutGrid,
  List,
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
  viewMode: "grid" | "list";
  setViewMode: (mode: "grid" | "list") => void;
}

export function Header({
  activeTab,
  setActiveTab,
  searchQuery,
  setSearchQuery,
  onNewNotebook,
  onClearNotebooks,
  totalNotebooks,
  viewMode,
  setViewMode,
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
      <div className="w-full px-4 sm:px-6 lg:px-8 py-2.5 flex items-center justify-between gap-2 sm:gap-4 overflow-hidden">
        
        {/* Brand Logo & Section Navigation */}
        <div className="flex items-center gap-3 lg:gap-6 min-w-0 flex-shrink">
          <div
            className="flex items-center gap-2.5 cursor-pointer group flex-shrink-0"
            onClick={() => setActiveTab("all")}
          >
            {/* Fernly SVG Logo Mark */}
            <div className="flex h-9 w-9 items-center justify-center rounded-[12px] bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30 shadow-xs transition-transform group-hover:scale-105">
              <svg className="w-4.5 h-4.5 stroke-[2.2px]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <rect x="3" y="3" width="18" height="18" rx="6" />
                <path d="M12 17V8" />
                <path d="M12 12c0-3 2-5 5-5 0 3-2 5-5 5Z" />
                <path d="M12 14c0-2.5-1.8-4-4.2-4 0 2.5 1.8 4 4.2 4Z" />
              </svg>
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5">
                <span className="text-lg font-bold tracking-tight text-[var(--ink)]">
                  Vellum
                </span>
                <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded-full bg-[var(--g-100)] text-[var(--g-800)] border border-[var(--g-400)]/40 tracking-tight">
                  Fernly
                </span>
              </div>
            </div>
          </div>

          {/* Fernly Stretchy Nav Capsule (Responsive labels to prevent any overlap) */}
          <nav className="hidden md:flex items-center bg-[var(--card)] p-1 rounded-full border border-[var(--hair)] shadow-xs flex-shrink-0 overflow-x-auto no-scrollbar">
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
                      ? "text-[#f1f8f3] bg-gradient-to-b from-[var(--g-700)] to-[var(--g-950)] shadow-xs"
                      : "text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[var(--panel)]"
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${isActive ? "text-[#5dbd8b]" : "text-[var(--faint)]"}`} />
                  <span className="hidden xl:inline">{tab.label}</span>
                  <span className="xl:hidden">{tab.shortLabel}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Tools: Search, 4-Accent Palette Switcher, Theme Mode, View Mode, Clean, New Notebook */}
        <div className="flex items-center gap-1.5 sm:gap-2.5 flex-shrink-0">
          
          {/* Fernly Search input with ⌘K badge (explicit padding so icon never overlaps text) */}
          <div className="relative w-32 sm:w-40 md:w-44 lg:w-52">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-[var(--faint)] pointer-events-none" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search library..."
              className="w-full !pl-8.5 pr-10 py-1.5 text-xs bg-[var(--card)] border border-[var(--hair)] rounded-full text-[var(--ink)] placeholder-[var(--faint)] focus:outline-none focus:border-[var(--g-600)] focus:ring-2 focus:ring-[var(--g-400)]/20 transition-all shadow-xs"
            />
            <kbd className="hidden sm:inline-flex absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded text-[9px] font-mono text-[var(--faint)] bg-[var(--panel)] border border-[var(--hair)] pointer-events-none">
              ⌘K
            </kbd>
          </div>

          {/* Fernly accent colourway - one control, four options */}
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

          {/* Grid / List View Toggle */}
          <div className="hidden md:flex items-center bg-[var(--card)] p-0.5 rounded-full border border-[var(--hair)]">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                viewMode === "grid"
                  ? "bg-[var(--g-700)] text-[#f1f8f3] shadow-xs"
                  : "text-[var(--faint)] hover:text-[var(--ink)]"
              }`}
              title="Grid View"
            >
              <LayoutGrid className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-full transition-colors cursor-pointer ${
                viewMode === "list"
                  ? "bg-[var(--g-700)] text-[#f1f8f3] shadow-xs"
                  : "text-[var(--faint)] hover:text-[var(--ink)]"
              }`}
              title="List View"
            >
              <List className="h-3.5 w-3.5" />
            </button>
          </div>

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
            className="flex items-center gap-1.5 px-3 sm:px-4 py-1.5 sm:py-2 rounded-full text-xs font-semibold text-[#f1f8f3] bg-gradient-to-b from-[var(--g-700)] to-[var(--g-950)] hover:from-[var(--g-600)] hover:to-[var(--g-800)] shadow-xs transition-all cursor-pointer hover:scale-[1.02] active:scale-[0.98]"
          >
            <Plus className="h-3.5 w-3.5" />
            <span className="hidden sm:inline">Add Project</span>
          </button>
        </div>
      </div>
    </header>
  );
}
