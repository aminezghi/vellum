"use client";

import React, { useEffect, useState } from "react";
import {
  Plus,
  Search,
  LayoutGrid,
  List,
  Sparkles,
  BookOpen,
  Flame,
  Layers,
  ShieldCheck,
  Moon,
  Sun,
  Trash2,
} from "lucide-react";

interface HeaderProps {
  activeTab: string;
  setActiveTab: (tab: string) => void;
  searchQuery: string;
  setSearchQuery: (query: string) => void;
  onNewNotebook: () => void;
  onClearNotebooks?: () => void;
  viewMode: "grid" | "list";
  setViewMode: (mode: "grid" | "list") => void;
  totalNotebooks?: number;
}

export function Header({
  activeTab,
  setActiveTab,
  searchQuery,
  setSearchQuery,
  onNewNotebook,
  onClearNotebooks,
  viewMode,
  setViewMode,
  totalNotebooks = 0,
}: HeaderProps) {
  const searchInputRef = React.useRef<HTMLInputElement>(null);
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [designStyle, setDesignStyle] = useState<"apple" | "wispr">("apple");

  // Initialize theme and design style from localStorage or system preference
  useEffect(() => {
    if (typeof window !== "undefined") {
      const savedTheme = localStorage.getItem("vellum-theme");
      const shouldBeDark =
        savedTheme === "dark" ||
        (!savedTheme && window.matchMedia("(prefers-color-scheme: dark)").matches);

      if (shouldBeDark) {
        setIsDarkMode(true);
        document.documentElement.classList.add("dark");
        document.body.classList.add("dark");
        document.documentElement.setAttribute("data-theme", "dark");
      } else {
        setIsDarkMode(false);
        document.documentElement.classList.remove("dark");
        document.body.classList.remove("dark");
        document.documentElement.setAttribute("data-theme", "light");
      }

      const savedDesign = (localStorage.getItem("vellum-design-style") as "apple" | "wispr") || "apple";
      setDesignStyle(savedDesign);
      document.documentElement.setAttribute("data-design", savedDesign);
    }
  }, []);

  const toggleTheme = () => {
    const nextDark = !isDarkMode;
    setIsDarkMode(nextDark);
    if (typeof window !== "undefined") {
      if (nextDark) {
        document.documentElement.classList.add("dark");
        document.body.classList.add("dark");
        document.documentElement.setAttribute("data-theme", "dark");
        localStorage.setItem("vellum-theme", "dark");
      } else {
        document.documentElement.classList.remove("dark");
        document.body.classList.remove("dark");
        document.documentElement.setAttribute("data-theme", "light");
        localStorage.setItem("vellum-theme", "light");
      }
    }
  };

  const toggleDesign = () => {
    const nextDesign = designStyle === "apple" ? "wispr" : "apple";
    setDesignStyle(nextDesign);
    if (typeof window !== "undefined") {
      localStorage.setItem("vellum-design-style", nextDesign);
      document.documentElement.setAttribute("data-design", nextDesign);
    }
  };

  const tabs = [
    { id: "all", label: "Dashboard", icon: Sparkles },
    { id: "search", label: "Academic Search", icon: Search },
    { id: "trends", label: "Trending Radar", icon: Flame },
    { id: "my-notebooks", label: "My Notebooks", icon: BookOpen },
    { id: "collections", label: "Collections", icon: Layers },
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
    <header className="sticky top-0 z-40 w-full apple-glass border-b border-black/[0.08] dark:border-white/[0.12] transition-all duration-200 shadow-xs">
      <div className="w-full px-4 sm:px-6 lg:px-8 xl:px-10 2xl:px-14 py-2.5 sm:py-3 flex items-center justify-between gap-3 sm:gap-6">
        {/* Brand Logo & Section Tabs */}
        <div className="flex items-center gap-3 sm:gap-6 lg:gap-8 min-w-0">
          <div
            className="flex items-center gap-2.5 cursor-pointer group flex-shrink-0 apple-press"
            onClick={() => setActiveTab("all")}
          >
            <div className={`relative flex h-9 w-9 sm:h-10 sm:w-10 items-center justify-center rounded-[14px] shadow-sm transition-transform ${
              designStyle === "apple"
                ? "bg-[#0071e3] text-white shadow-blue-500/20"
                : "bg-[#034f46] text-[#ffffeb]"
            }`}>
              <BookOpen className="h-4 w-4 sm:h-5 sm:w-5 text-white" />
            </div>
            <div className="flex flex-col">
              <div className="flex items-center gap-1.5 sm:gap-2">
                <span className="text-base sm:text-lg font-semibold tracking-[-0.03em] text-[#1a1a1a] dark:text-[#ffffeb]">
                  Vellum
                </span>
                <span className={`text-[10px] font-semibold px-2 py-0.5 rounded-full border ${
                  designStyle === "apple"
                    ? "bg-[#0071e3]/10 text-[#0071e3] dark:bg-[#0a84ff]/20 dark:text-[#64b5ff] border-[#0071e3]/20"
                    : "bg-[#cef5ca] text-[#114e0b] dark:bg-[#034f46] dark:text-[#cef5ca] border-[#114e0b]/20"
                }`}>
                  {designStyle === "apple" ? "Apple Pro 2.5" : "Web 2.4"}
                </span>
              </div>
              <span className="text-[10px] text-[#1a1a1a]/60 dark:text-white/60 hidden md:inline -mt-0.5 font-medium tracking-tight truncate">
                Local-First Research Studio · by Amine Zouaghi
              </span>
            </div>
          </div>

          {/* Navigation Pills */}
          <nav className="hidden md:flex items-center apple-segmented overflow-x-auto">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`apple-segmented-item apple-press flex items-center gap-1.5 whitespace-nowrap cursor-pointer ${
                    isActive ? "active" : ""
                  }`}
                >
                  <Icon className={`h-3.5 w-3.5 ${
                    isActive
                      ? (designStyle === "apple" ? "text-[#0071e3] dark:text-[#64b5ff]" : "text-[#034f46] dark:text-[#cef5ca]")
                      : "text-neutral-400"
                  }`} />
                  <span className="hidden lg:inline">{tab.label}</span>
                  <span className="lg:hidden">{tab.label.split(" ")[0]}</span>
                </button>
              );
            })}
          </nav>
        </div>

        {/* Right Tools: Search, Design Mode, Reading Mode, View Mode, Clean, New Notebook */}
        <div className="flex items-center gap-2 sm:gap-2.5 flex-shrink-0">
          {/* Search bar with Ctrl+K shortcut */}
          <div className="relative w-32 sm:w-44 md:w-52 lg:w-60 xl:w-68">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-neutral-400" />
            <input
              ref={searchInputRef}
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="Search library..."
              className="w-full pl-8 pr-8 sm:pr-12 py-1.5 text-xs bg-black/5 dark:bg-white/10 border border-black/10 dark:border-white/15 rounded-full text-[#1a1a1a] dark:text-white placeholder-neutral-400 focus:outline-none focus:border-[#0071e3] dark:focus:border-[#0a84ff] focus:ring-2 focus:ring-[#0071e3]/20 transition-all shadow-xs"
            />
            <kbd className="hidden sm:inline-flex absolute right-2.5 top-1/2 -translate-y-1/2 px-1.5 py-0.5 rounded text-[10px] font-mono text-neutral-500 bg-white/80 dark:bg-black/60 border border-black/10 dark:border-white/10 shadow-xs">
              ⌘K
            </kbd>
          </div>

          {/* Design Style Switcher Pill: Apple Fluid vs Wispr Flow */}
          <button
            onClick={toggleDesign}
            className="apple-press hidden sm:flex items-center gap-1 px-2.5 py-1.5 rounded-full border border-black/10 dark:border-white/15 bg-white/60 dark:bg-white/10 hover:bg-white dark:hover:bg-white/20 text-xs font-semibold transition-all cursor-pointer shadow-xs"
            title={designStyle === "apple" ? "Current: Apple Fluid (Click to switch to Wispr Flow)" : "Current: Wispr Flow (Click to switch to Apple Fluid)"}
          >
            <span className="text-[11px]">{designStyle === "apple" ? "🍏 Apple" : "🌿 Wispr"}</span>
          </button>

          {/* Reading Mode / Dark Mode Toggle Button */}
          <button
            onClick={toggleTheme}
            className="apple-press p-1.5 sm:p-2 rounded-full border border-black/10 dark:border-white/15 bg-white/70 dark:bg-white/10 text-[#1a1a1a] dark:text-white hover:bg-white dark:hover:bg-white/20 transition-all cursor-pointer shadow-xs flex items-center gap-1"
            title={isDarkMode ? "Switch to Light Canvas" : "Switch to Night Mode"}
          >
            {isDarkMode ? (
              <Sun className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#ffa946]" />
            ) : (
              <Moon className="h-3.5 w-3.5 sm:h-4 sm:w-4 text-[#0071e3] dark:text-[#0a84ff]" />
            )}
          </button>

          {/* View Mode Toggle (Grid vs List) */}
          <div className="hidden sm:flex items-center apple-segmented">
            <button
              onClick={() => setViewMode("grid")}
              className={`p-1.5 rounded-full transition-all cursor-pointer apple-press ${
                viewMode === "grid"
                  ? "bg-white dark:bg-white/20 text-[#0071e3] dark:text-white shadow-xs"
                  : "text-neutral-400 hover:text-neutral-700 dark:hover:text-white"
              }`}
              title="Grid view"
            >
              <LayoutGrid className="h-3.5 w-3.5" />
            </button>
            <button
              onClick={() => setViewMode("list")}
              className={`p-1.5 rounded-full transition-all cursor-pointer apple-press ${
                viewMode === "list"
                  ? "bg-white dark:bg-white/20 text-[#0071e3] dark:text-white shadow-xs"
                  : "text-neutral-400 hover:text-neutral-700 dark:hover:text-white"
              }`}
              title="List view"
            >
              <List className="h-3.5 w-3.5" />
            </button>
          </div>

          {/* Clean / Delete Notebooks Quick Button (if notebooks exist) */}
          {onClearNotebooks && totalNotebooks > 0 && (
            <button
              onClick={onClearNotebooks}
              className="apple-press hidden lg:flex items-center gap-1 px-3 py-1.5 rounded-full border border-red-200 dark:border-red-900/40 text-red-600 dark:text-red-400 hover:bg-red-50 dark:hover:bg-red-950/30 text-xs font-semibold transition-all cursor-pointer shadow-xs"
              title="Clean or reset notebooks from storage"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Clean ({totalNotebooks})</span>
            </button>
          )}

          {/* New Notebook CTA */}
          <button
            onClick={onNewNotebook}
            className={`apple-press flex items-center gap-1.5 px-3.5 sm:px-5 py-2 rounded-full text-xs font-semibold shadow-sm transition-all cursor-pointer ${
              designStyle === "apple"
                ? "apple-btn-primary"
                : "wispr-btn-primary"
            }`}
          >
            <Plus className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
            <span className="hidden sm:inline">New notebook</span>
            <span className="sm:hidden font-medium">New</span>
          </button>
        </div>
      </div>

      {/* Mobile Sub-Navigation Bar (Phones < 768px) */}
      <div className="md:hidden w-full px-3 py-2 overflow-x-auto no-scrollbar border-t border-[#1a1a1a]/8 dark:border-white/10 bg-[#ffffeb]/90 dark:bg-[#121413]/90">
        <nav className="flex items-center gap-1.5">
          {tabs.map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-1 px-3 py-1.5 rounded-full text-xs font-medium whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? "bg-[#034f46] text-[#ffffeb] shadow-sm"
                    : "text-[#1a1a1a]/70 dark:text-white/70 hover:text-[#1a1a1a] dark:hover:text-white bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/10 dark:border-white/10"
                }`}
              >
                <Icon className={`h-3 w-3 ${isActive ? "text-[#cef5ca]" : "text-[#1a1a1a]/50 dark:text-white/50"}`} />
                <span>{tab.label}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </header>
  );
}
