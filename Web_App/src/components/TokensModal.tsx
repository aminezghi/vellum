"use client";

import React, { useState, useEffect } from "react";
import { Key, ShieldCheck, Check, X, Sparkles, ExternalLink, HelpCircle } from "lucide-react";
import { STORAGE_KEYS } from "@/lib/storageNamespace";

export interface CustomTokens {
  openAlexToken: string;
  semanticScholarKey: string;
  crossrefEmail: string;
  ncbiApiKey: string;
}

interface TokensModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSave?: (tokens: CustomTokens) => void;
}

export function TokensModal({ isOpen, onClose, onSave }: TokensModalProps) {
  const [tokens, setTokens] = useState<CustomTokens>({
    openAlexToken: "",
    semanticScholarKey: "",
    crossrefEmail: "",
    ncbiApiKey: "",
  });
  const [savedSuccess, setSavedSuccess] = useState(false);

  useEffect(() => {
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem(STORAGE_KEYS.tokens);
      if (stored) {
        try {
          setTokens(JSON.parse(stored));
        } catch (e) {
          console.error("Failed to parse tokens from storage", e);
        }
      }
    }
  }, [isOpen]);

  if (!isOpen) return null;

  const handleSave = () => {
    if (typeof window !== "undefined") {
      localStorage.setItem(STORAGE_KEYS.tokens, JSON.stringify(tokens));
    }
    if (onSave) onSave(tokens);
    setSavedSuccess(true);
    setTimeout(() => {
      setSavedSuccess(false);
      onClose();
    }, 1200);
  };

  const handleClear = () => {
    const emptyTokens = {
      openAlexToken: "",
      semanticScholarKey: "",
      crossrefEmail: "",
      ncbiApiKey: "",
    };
    setTokens(emptyTokens);
    if (typeof window !== "undefined") {
      localStorage.removeItem(STORAGE_KEYS.tokens);
    }
    if (onSave) onSave(emptyTokens);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/40 backdrop-blur-2xl animate-in fade-in duration-200">
      <div className="apple-glass relative w-full max-w-lg rounded-[2rem] bg-white/90 dark:bg-[#1c1c1e]/90 border border-black/10 dark:border-white/15 p-6 sm:p-7 shadow-2xl space-y-5 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div className="flex items-center gap-3">
            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-[#0071e3] text-white shadow-xs">
              <Key className="h-5 w-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-[#1a1a1a] dark:text-white tracking-tight">
                API Keys &amp; Custom Tokens
              </h3>
              <p className="text-xs text-[#1a1a1a]/60 dark:text-white/60 font-medium">
                Increase rate limits &amp; unlock fast-lane queries
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="apple-press p-1.5 rounded-full text-[#1a1a1a]/40 dark:text-white/40 hover:text-[#1a1a1a] dark:hover:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Privacy & Fast-Lane Note */}
        <div className="p-3.5 rounded-2xl bg-[#34c759]/10 border border-[#34c759]/30 flex items-start gap-2.5">
          <ShieldCheck className="h-4 w-4 text-[#248a3d] dark:text-[#30d158] flex-shrink-0 mt-0.5" />
          <div className="text-[11px] text-[#248a3d] dark:text-[#30d158] leading-relaxed font-medium">
            <p>
              <strong>100% Client-Side Privacy:</strong> Your keys are saved only in your local browser and sent directly to academic providers.
            </p>
            <p className="mt-0.5 opacity-90">
              Tokens and polite emails are <strong>100% free</strong> and boost request speed, citation depth, and rate limits.
            </p>
          </div>
        </div>

        {/* Form Fields with Direct Provider Links */}
        <div className="space-y-4">
          {/* 1. OpenAlex Token / Polite Email */}
          <div className="p-4 rounded-2xl bg-[#ffffeb]/40 dark:bg-[#121413]/50 border border-[#1a1a1a]/10 dark:border-white/10 space-y-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="text-xs font-semibold text-[#1a1a1a] dark:text-white flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#034f46] dark:bg-[#23a07a]" />
                <span>OpenAlex Polite Email or API Key</span>
              </label>
              <a
                href="https://docs.openalex.org/how-to-use-the-api/rate-limits-and-authentication"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[11px] font-semibold text-[#034f46] dark:text-[#cef5ca] hover:bg-[#ffffeb] dark:hover:bg-white/10 transition-colors shadow-2xs"
                title="Open OpenAlex documentation & registration in a new tab"
              >
                <span>Get Key / Polite Info</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <input
              type="text"
              value={tokens.openAlexToken}
              onChange={(e) => setTokens({ ...tokens, openAlexToken: e.target.value })}
              placeholder="e.g. researcher@university.edu or api_key_..."
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
            />
            <div className="flex items-center justify-between text-[10px] text-[#1a1a1a]/60 dark:text-white/50 pt-0.5">
              <span>Entering your email joins OpenAlex&apos;s 10 req/s polite pool (no payment needed).</span>
              <a
                href="https://openalex.org"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline text-[#034f46] dark:text-[#cef5ca] font-medium hidden sm:inline"
              >
                openalex.org ↗
              </a>
            </div>
          </div>

          {/* 2. Semantic Scholar API Key */}
          <div className="p-4 rounded-2xl bg-[#ffffeb]/40 dark:bg-[#121413]/50 border border-[#1a1a1a]/10 dark:border-white/10 space-y-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="text-xs font-semibold text-[#1a1a1a] dark:text-white flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#f0d7ff]" />
                <span>Semantic Scholar API Key (x-api-key)</span>
              </label>
              <a
                href="https://www.semanticscholar.org/product/api#api-key-form"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[11px] font-semibold text-[#4a154b] dark:text-[#f0d7ff] hover:bg-[#ffffeb] dark:hover:bg-white/10 transition-colors shadow-2xs"
                title="Fill the official Semantic Scholar free API key request form"
              >
                <span>Request Free API Key</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <input
              type="password"
              value={tokens.semanticScholarKey}
              onChange={(e) => setTokens({ ...tokens, semanticScholarKey: e.target.value })}
              placeholder="Paste Semantic Scholar API Key..."
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
            />
            <div className="flex items-center justify-between text-[10px] text-[#1a1a1a]/60 dark:text-white/50 pt-0.5">
              <span>Free keys unlock 100 requests/minute and full AI citation graph traversal.</span>
              <a
                href="https://www.semanticscholar.org/product/api"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:underline text-[#4a154b] dark:text-[#f0d7ff] font-medium hidden sm:inline"
              >
                API Overview ↗
              </a>
            </div>
          </div>

          {/* 3. Crossref Polite Email */}
          <div className="p-4 rounded-2xl bg-[#ffffeb]/40 dark:bg-[#121413]/50 border border-[#1a1a1a]/10 dark:border-white/10 space-y-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="text-xs font-semibold text-[#1a1a1a] dark:text-white flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#cef5ca]" />
                <span>Crossref Polite User-Agent Email</span>
              </label>
              <a
                href="https://www.crossref.org/documentation/retrieve-metadata/rest-api/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[11px] font-semibold text-[#114e0b] dark:text-[#cef5ca] hover:bg-[#ffffeb] dark:hover:bg-white/10 transition-colors shadow-2xs"
                title="Read Crossref REST API & polite etiquette guide"
              >
                <span>Crossref Polite Guide</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <input
              type="email"
              value={tokens.crossrefEmail}
              onChange={(e) => setTokens({ ...tokens, crossrefEmail: e.target.value })}
              placeholder="e.g. your-name@institution.org"
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
            />
            <p className="text-[10px] text-[#1a1a1a]/60 dark:text-white/50">
              No registration needed. Providing your email routes DOI queries to Crossref&apos;s dedicated polite cluster.
            </p>
          </div>

          {/* 4. NCBI / PubMed API Key */}
          <div className="p-4 rounded-2xl bg-[#ffffeb]/40 dark:bg-[#121413]/50 border border-[#1a1a1a]/10 dark:border-white/10 space-y-2">
            <div className="flex items-center justify-between flex-wrap gap-2">
              <label className="text-xs font-semibold text-[#1a1a1a] dark:text-white flex items-center gap-1.5">
                <span className="h-2 w-2 rounded-full bg-[#ffa946]" />
                <span>NCBI / PubMed API Key</span>
              </label>
              <a
                href="https://www.ncbi.nlm.nih.gov/account/settings/"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 px-2.5 py-1 rounded-full bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[11px] font-semibold text-[#994800] dark:text-[#ffa946] hover:bg-[#ffffeb] dark:hover:bg-white/10 transition-colors shadow-2xs"
                title="Log into NCBI account settings and create an API key"
              >
                <span>Generate Key in Settings</span>
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
            <input
              type="password"
              value={tokens.ncbiApiKey}
              onChange={(e) => setTokens({ ...tokens, ncbiApiKey: e.target.value })}
              placeholder="NCBI API key from NCBI account settings"
              className="w-full px-3.5 py-2 text-xs rounded-xl bg-white dark:bg-[#1a1e1c] border border-[#1a1a1a]/15 dark:border-white/15 text-[#1a1a1a] dark:text-white placeholder-[#1a1a1a]/35 dark:placeholder-white/30 focus:outline-none focus:border-[#034f46]"
            />
            <div className="flex items-center justify-between text-[10px] text-[#1a1a1a]/60 dark:text-white/50 pt-0.5">
              <span>Go to NCBI Account Settings → API Key Management → Click &quot;Create an API Key&quot; (raises limit to 10 req/s).</span>
            </div>
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-black/8 dark:border-white/10">
          <button
            type="button"
            onClick={handleClear}
            className="apple-press text-xs text-red-600 dark:text-red-400 hover:underline cursor-pointer font-medium"
          >
            Clear all tokens
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="apple-press px-4 py-2 rounded-full border border-black/15 dark:border-white/15 text-xs font-medium text-[#1a1a1a] dark:text-white hover:bg-black/5 dark:hover:bg-white/10 transition-colors cursor-pointer"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="apple-press flex items-center gap-1.5 px-5 py-2 rounded-full bg-[#0071e3] hover:bg-[#0077ed] text-white text-xs font-semibold shadow-xs transition-all cursor-pointer"
            >
              {savedSuccess ? (
                <>
                  <Check className="h-3.5 w-3.5 text-white" />
                  <span>Saved!</span>
                </>
              ) : (
                <span>Save Tokens</span>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
