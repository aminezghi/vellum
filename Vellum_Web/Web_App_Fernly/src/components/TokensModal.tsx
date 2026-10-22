"use client";

import React, { useState } from "react";
import { Key, ShieldCheck, Check, ExternalLink } from "lucide-react";
import { STORAGE_KEYS } from "@/lib/storageNamespace";
import { Modal } from "@/components/Modal";

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

/** Read saved provider tokens. Safe on the server, where there is no storage. */
function readStoredTokens(): CustomTokens {
  const empty: CustomTokens = {
    openAlexToken: "",
    semanticScholarKey: "",
    crossrefEmail: "",
    ncbiApiKey: "",
  };
  if (typeof window === "undefined") return empty;
  const stored = localStorage.getItem(STORAGE_KEYS.tokens);
  if (!stored) return empty;
  try {
    return { ...empty, ...(JSON.parse(stored) as Partial<CustomTokens>) };
  } catch (e) {
    console.error("Failed to parse tokens from storage", e);
    return empty;
  }
}

export function TokensModal({ isOpen, onClose, onSave }: TokensModalProps) {
  // The dialog is mounted only while it is open, so its fields are seeded from
  // storage on every open without an effect. Previously an effect re-read
  // localStorage and called setState, which re-rendered the whole form.
  if (!isOpen) return null;
  return <TokensDialog onClose={onClose} onSave={onSave} />;
}

function TokensDialog({ onClose, onSave }: Omit<TokensModalProps, "isOpen">) {
  const [tokens, setTokens] = useState<CustomTokens>(readStoredTokens);
  const [savedSuccess, setSavedSuccess] = useState(false);

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
    <Modal
      isOpen={true}
      onClose={onClose}
      title="API Keys & Provider Tokens"
      subtitle="Increase rate limits & unlock fast-lane queries"
      icon={<Key className="h-5 w-5" />}
      panelClassName="max-w-lg space-y-5 max-h-[90vh] overflow-y-auto"
    >
        {/* Privacy Note */}
        <div className="p-3.5 rounded-2xl bg-[var(--g-100)] border border-[var(--g-400)]/30 flex items-start gap-2.5">
          <ShieldCheck className="h-4 w-4 text-[var(--g-700)] flex-shrink-0 mt-0.5" aria-hidden="true" />
          <div className="text-[11px] text-[var(--g-800)] leading-relaxed font-medium">
            <p>
              <strong>100% Client-Side Privacy:</strong> Your keys are saved only in your local browser and sent directly to academic providers.
            </p>
          </div>
        </div>

        {/* Fields */}
        <div className="space-y-4 text-xs">
          {/* OpenAlex Token */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label htmlFor="tok-openalex" className="font-semibold text-[var(--muted)] flex items-center gap-1.5">
                <span>OpenAlex Premium Token</span>
                <span className="text-[10px] text-[var(--faint)] font-normal">(Optional)</span>
              </label>
              <a
                href="https://openalex.org"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-[var(--g-700)] hover:underline inline-flex items-center gap-0.5"
              >
                <span>openalex.org</span>
                <ExternalLink className="h-2.5 w-2.5" aria-hidden="true" />
              </a>
            </div>
            <input
              id="tok-openalex"
              type="password"
              value={tokens.openAlexToken}
              onChange={(e) => setTokens({ ...tokens, openAlexToken: e.target.value })}
              placeholder="Bearer token or leave empty for public API"
              className="fernly-input w-full font-mono text-xs"
            />
          </div>

          {/* Semantic Scholar API Key */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label htmlFor="tok-s2" className="font-semibold text-[var(--muted)] flex items-center gap-1.5">
                <span>Semantic Scholar API Key</span>
                <span className="text-[10px] text-[var(--faint)] font-normal">(Optional)</span>
              </label>
              <a
                href="https://www.semanticscholar.org/product/api"
                target="_blank"
                rel="noreferrer"
                className="text-[10px] text-[var(--g-700)] hover:underline inline-flex items-center gap-0.5"
              >
                <span>semanticscholar.org</span>
                <ExternalLink className="h-2.5 w-2.5" aria-hidden="true" />
              </a>
            </div>
            <input
              id="tok-s2"
              type="password"
              value={tokens.semanticScholarKey}
              onChange={(e) => setTokens({ ...tokens, semanticScholarKey: e.target.value })}
              placeholder="x-api-key token"
              className="fernly-input w-full font-mono text-xs"
            />
          </div>

          {/* Crossref Polite Email */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label htmlFor="tok-crossref" className="font-semibold text-[var(--muted)] flex items-center gap-1.5">
                <span>Crossref &quot;Polite Pool&quot; Email</span>
                <span className="text-[10px] text-[var(--faint)] font-normal">(Recommended)</span>
              </label>
              <span className="text-[10px] text-[var(--faint)] font-mono">10x rate boost</span>
            </div>
            <input
              id="tok-crossref"
              type="email"
              value={tokens.crossrefEmail}
              onChange={(e) => setTokens({ ...tokens, crossrefEmail: e.target.value })}
              placeholder="e.g. researcher@university.edu"
              className="fernly-input w-full text-xs"
            />
          </div>

          {/* NCBI / PubMed API Key */}
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <label htmlFor="tok-ncbi" className="font-semibold text-[var(--muted)] flex items-center gap-1.5">
                <span>NCBI / PubMed API Key</span>
                <span className="text-[10px] text-[var(--faint)] font-normal">(Optional)</span>
              </label>
              <span className="text-[10px] text-[var(--faint)] font-mono">3 req/s &rarr; 10 req/s</span>
            </div>
            <input
              id="tok-ncbi"
              type="password"
              value={tokens.ncbiApiKey}
              onChange={(e) => setTokens({ ...tokens, ncbiApiKey: e.target.value })}
              placeholder="NCBI API key"
              className="fernly-input w-full font-mono text-xs"
            />
          </div>
        </div>

        {/* Footer Actions */}
        <div className="flex items-center justify-between pt-3 border-t border-[var(--hair)]">
          <button
            type="button"
            onClick={handleClear}
            className="text-xs text-[var(--rose)] hover:underline font-semibold cursor-pointer"
          >
            Clear Stored Keys
          </button>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={onClose}
              className="btn-fernly-ghost !h-9 !px-3.5 !text-xs"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleSave}
              className="btn-fernly-primary !h-9 !px-4 !text-xs flex items-center gap-1"
            >
              {savedSuccess ? (
                <>
                  <Check className="h-3.5 w-3.5 text-[#5dbd8b]" aria-hidden="true" />
                  <span>Saved!</span>
                </>
              ) : (
                <span>Save Keys</span>
              )}
            </button>
          </div>
        </div>
    </Modal>
  );
}
