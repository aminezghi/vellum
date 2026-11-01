"use client";

import React, { useCallback, useEffect, useId, useRef } from "react";

/**
 * Modal — the one dialog primitive used by the whole studio.
 *
 * Every modal in the app used to be a bare <div> with `fixed inset-0`. That
 * looks like a dialog but is not one: a screen reader announces it as
 * ordinary content, the keyboard can tab straight out of it into the page
 * behind, and Escape does nothing. Four different modals also each had their
 * own slightly different behaviour.
 *
 * This component gives all of them the same, correct behaviour:
 *
 *   - role="dialog" + aria-modal so assistive technology announces a dialog
 *   - focus moves into the dialog when it opens and returns to the trigger
 *     when it closes
 *   - Tab and Shift+Tab cycle inside the dialog instead of escaping it
 *   - Escape closes it
 *   - the page behind cannot be scrolled
 */

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  /** The dialog's accessible name. */
  title: string;
  /** Optional supporting line, announced with the title. */
  subtitle?: string;
  /** Decorative icon shown next to the title. */
  icon?: React.ReactNode;
  /** Extra classes for the dialog panel. */
  panelClassName?: string;
  children: React.ReactNode;
}

const FOCUSABLE =
  'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), [tabindex]:not([tabindex="-1"])';

export function Modal({
  isOpen,
  onClose,
  title,
  subtitle,
  icon,
  panelClassName = "",
  children,
}: ModalProps) {
  const panelRef = useRef<HTMLDivElement>(null);
  const restoreFocusRef = useRef<HTMLElement | null>(null);
  const baseId = useId();
  const titleId = `${baseId}-title`;
  const subtitleId = `${baseId}-subtitle`;

  const getFocusable = useCallback(() => {
    const panel = panelRef.current;
    if (!panel) return [] as HTMLElement[];
    return Array.from(panel.querySelectorAll<HTMLElement>(FOCUSABLE)).filter(
      (el) => el.offsetParent !== null || el === document.activeElement
    );
  }, []);

  // Move focus in on open, and hand it back to the trigger on close.
  useEffect(() => {
    if (!isOpen) return;

    restoreFocusRef.current = document.activeElement as HTMLElement | null;

    const focusFirst = () => {
      const focusable = getFocusable();
      if (focusable.length > 0) {
        focusable[0].focus();
      } else {
        panelRef.current?.focus();
      }
    };

    // Move focus now — the panel is already laid out by the time effects run.
    // Then check again on the next frame in case the first attempt landed
    // before layout settled. The retry matters: requestAnimationFrame is
    // throttled (or skipped entirely) in a background tab, so relying on it
    // alone would leave focus stranded on <body> and strand a screen reader
    // outside the dialog it just announced.
    focusFirst();
    const raf = requestAnimationFrame(() => {
      if (!panelRef.current?.contains(document.activeElement)) focusFirst();
    });

    const { overflow } = document.body.style;
    document.body.style.overflow = "hidden";

    return () => {
      cancelAnimationFrame(raf);
      document.body.style.overflow = overflow;
      const restore = restoreFocusRef.current;
      if (restore && typeof restore.focus === "function") {
        restore.focus();
      }
    };
  }, [isOpen, getFocusable]);

  // Escape closes; Tab stays inside the dialog.
  const onKeyDown = (event: React.KeyboardEvent<HTMLDivElement>) => {
    if (event.key === "Escape") {
      event.stopPropagation();
      onClose();
      return;
    }

    if (event.key !== "Tab") return;

    const focusable = getFocusable();
    if (focusable.length === 0) {
      event.preventDefault();
      panelRef.current?.focus();
      return;
    }

    const first = focusable[0];
    const last = focusable[focusable.length - 1];
    const active = document.activeElement as HTMLElement | null;

    if (event.shiftKey && (active === first || active === panelRef.current)) {
      event.preventDefault();
      last.focus();
    } else if (!event.shiftKey && active === last) {
      event.preventDefault();
      first.focus();
    }
  };

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm animate-in fade-in duration-200"
      onMouseDown={(e) => {
        // Only a click that starts and ends on the backdrop dismisses.
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        ref={panelRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={subtitle ? subtitleId : undefined}
        tabIndex={-1}
        onKeyDown={onKeyDown}
        className={`fernly-card w-full max-w-lg p-7 relative outline-none ${panelClassName}`}
      >
        <button
          type="button"
          onClick={onClose}
          aria-label={`Close ${title}`}
          className="absolute right-5 top-5 p-2 rounded-full text-[var(--faint)] hover:text-[var(--ink)] hover:bg-[var(--panel)] transition-colors cursor-pointer"
        >
          <svg className="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" aria-hidden="true">
            <path d="M18 6 6 18M6 6l12 12" />
          </svg>
        </button>

        <div className="flex items-center gap-2.5 mb-5 pr-8">
          {icon ? (
            <div className="p-2.5 rounded-2xl bg-[var(--g-100)] text-[var(--g-700)] border border-[var(--g-400)]/30">
              {icon}
            </div>
          ) : null}
          <div>
            <h2 id={titleId} className="text-lg font-bold tracking-tight text-[var(--ink)]">
              {title}
            </h2>
            {subtitle ? (
              <p id={subtitleId} className="text-xs text-[var(--muted)]">
                {subtitle}
              </p>
            ) : null}
          </div>
        </div>

        {children}
      </div>
    </div>
  );
}
