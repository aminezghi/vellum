"use client";

import React, { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { ShieldAlert, RotateCcw, Home, ChevronDown, ChevronUp, Copy, Check } from "lucide-react";

interface ErrorBoundaryProps {
  error: Error & { digest?: string };
  reset: () => void;
}

export default function ErrorBoundary({ error, reset }: ErrorBoundaryProps) {
  const router = useRouter();
  const [showDetails, setShowDetails] = useState(false);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    // Log unexpected client exceptions for diagnostic auditing
    console.error("[Vellum_Web ErrorBoundary Catch]", error);
  }, [error]);

  const handleCopyDiagnostics = async () => {
    const diagnosticPayload = `[Vellum Error Report]\nMessage: ${error.message}\nDigest: ${
      error.digest || "none"
    }\nStack: ${error.stack || "none"}\nTimestamp: ${new Date().toISOString()}`;
    await navigator.clipboard.writeText(diagnosticPayload);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="min-h-screen bg-[var(--canvas)] flex items-center justify-center p-6 text-[var(--ink)]">
      <div className="fernly-card max-w-lg w-full p-8 rounded-[2rem] border border-[var(--hair)] shadow-xl flex flex-col items-center text-center">
        {/* Botanical Icon Pill */}
        <div className="h-16 w-16 rounded-2xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30 shadow-xs flex items-center justify-center mb-5">
          <ShieldAlert className="h-8 w-8 text-[var(--g-700)]" />
        </div>

        {/* Title & Subtitle */}
        <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-[var(--ink)]">
          Research Studio Interrupted
        </h1>
        <p className="text-xs sm:text-sm text-[var(--muted)] mt-2 leading-relaxed font-medium">
          A client rendering exception occurred in this studio view. Your local review data in
          IndexedDB is completely secure and uncorrupted.
        </p>

        {/* Primary Action Buttons */}
        <div className="flex flex-wrap items-center justify-center gap-3 mt-6 w-full">
          <button
            onClick={() => reset()}
            className="btn-fernly-primary flex-1 min-w-[140px] flex items-center justify-center gap-2 px-5 py-2.5 rounded-full text-xs font-semibold shadow-xs cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reset View</span>
          </button>

          <button
            onClick={() => window.location.reload()}
            className="btn-fernly-ghost flex-1 min-w-[140px] flex items-center justify-center gap-2 px-5 py-2.5 rounded-full text-xs font-semibold cursor-pointer"
          >
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Reload Studio</span>
          </button>

          <button
            onClick={() => {
              router.push("/");
            }}
            className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-full border border-[var(--hair)] text-xs font-medium text-[var(--muted)] hover:text-[var(--ink)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
          >
            <Home className="h-3.5 w-3.5" />
            <span>Return to Dashboard</span>
          </button>
        </div>

        {/* Diagnostic Drawer */}
        <div className="w-full mt-6 pt-5 border-t border-[var(--hair)] text-left">
          <button
            onClick={() => setShowDetails(!showDetails)}
            className="w-full flex items-center justify-between text-xs font-semibold text-[var(--muted)] hover:text-[var(--ink)] transition-colors cursor-pointer"
          >
            <span>Diagnostic Details</span>
            {showDetails ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
          </button>

          {showDetails && (
            <div className="mt-3 p-3.5 rounded-xl bg-[var(--panel)] border border-[var(--hair)] font-mono text-[11px] text-[var(--ink-muted)] break-all space-y-2">
              <div className="flex items-center justify-between">
                <span className="font-semibold text-[var(--ink)]">Exception Trace</span>
                <button
                  onClick={handleCopyDiagnostics}
                  className="flex items-center gap-1 text-[10px] text-[var(--g-700)] hover:underline cursor-pointer"
                >
                  {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
                  <span>{copied ? "Copied" : "Copy Log"}</span>
                </button>
              </div>
              <p className="text-red-600 dark:text-red-400 font-semibold">{error.message || "Unknown error"}</p>
              {error.digest && <p className="text-[10px] text-[var(--faint)]">Digest: {error.digest}</p>}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
