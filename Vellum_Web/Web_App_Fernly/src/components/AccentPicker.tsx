"use client";

import React, { useEffect, useRef, useState } from "react";
import type { Accent } from "@/lib/theme";

/**
 * AccentPicker — the four Fernly accent colourways, behind one control.
 *
 * The header used to show four colour swatches side by side. Four extra
 * targets in the top bar, all of them pure colour with no text, is a lot to
 * ask of a glance - and colour alone is not an accessible way to encode a
 * choice. One button now opens the palette, and each option carries a name
 * that is spoken rather than only seen.
 */

export type FernlyAccent = Accent;

const ACCENTS: { id: FernlyAccent; name: string; color: string }[] = [
  { id: "emerald", name: "Emerald Green", color: "#10b981" },
  { id: "ocean", name: "Deep Ocean", color: "#3b82f6" },
  { id: "plum", name: "Royal Plum", color: "#a855f7" },
  { id: "ember", name: "Warm Ember", color: "#f97316" },
];

interface AccentPickerProps {
  value: FernlyAccent;
  onChange: (accent: FernlyAccent) => void;
}

export function AccentPicker({ value, onChange }: AccentPickerProps) {
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const firstOptionRef = useRef<HTMLButtonElement>(null);

  const current = ACCENTS.find((a) => a.id === value) ?? ACCENTS[0];

  // Close when the user clicks away.
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: MouseEvent) => {
      if (wrapRef.current && !wrapRef.current.contains(event.target as Node)) {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onPointerDown);
    return () => document.removeEventListener("mousedown", onPointerDown);
  }, [open]);

  // Move focus into the palette when it opens so the keyboard can use it.
  useEffect(() => {
    if (open) {
      firstOptionRef.current?.focus();
    }
  }, [open]);

  const onKeyDown = (event: React.KeyboardEvent) => {
    if (event.key === "Escape" && open) {
      event.stopPropagation();
      setOpen(false);
      buttonRef.current?.focus();
      return;
    }
    if (!open && (event.key === "ArrowDown" || event.key === "Enter" || event.key === " ")) {
      event.preventDefault();
      setOpen(true);
    }
  };

  const onOptionKeyDown = (event: React.KeyboardEvent, index: number) => {
    if (event.key === "ArrowRight" || event.key === "ArrowDown") {
      event.preventDefault();
      const next = ACCENTS[(index + 1) % ACCENTS.length];
      onChange(next.id);
      const buttons = wrapRef.current?.querySelectorAll<HTMLButtonElement>('[role="option"]');
      buttons?.[(index + 1) % ACCENTS.length]?.focus();
    } else if (event.key === "ArrowLeft" || event.key === "ArrowUp") {
      event.preventDefault();
      const prev = ACCENTS[(index - 1 + ACCENTS.length) % ACCENTS.length];
      onChange(prev.id);
      const buttons = wrapRef.current?.querySelectorAll<HTMLButtonElement>('[role="option"]');
      buttons?.[(index - 1 + ACCENTS.length) % ACCENTS.length]?.focus();
    }
  };

  return (
    <div ref={wrapRef} className="relative" onKeyDown={onKeyDown}>
      <button
        ref={buttonRef}
        type="button"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`Accent colourway: ${current.name}. Change colourway`}
        title="Choose Accent Colourway"
        className="w-6 h-6 rounded-full border-2 border-[var(--hair)] shadow-xs transition-transform hover:scale-105 cursor-pointer"
        style={{ backgroundColor: "var(--g-600)" }}
      />

      {open ? (
        <div
          role="listbox"
          aria-label="Accent colourway"
          className="absolute right-0 top-full mt-2 z-50 flex flex-col gap-1 p-1.5 rounded-2xl bg-[var(--card)] border border-[var(--hair)] shadow-lg"
        >
          {ACCENTS.map((accent, index) => {
            const selected = accent.id === value;
            return (
              <button
                key={accent.id}
                ref={index === 0 ? firstOptionRef : undefined}
                type="button"
                role="option"
                aria-selected={selected}
                tabIndex={selected ? 0 : -1}
                onClick={() => {
                  onChange(accent.id);
                  setOpen(false);
                  buttonRef.current?.focus();
                }}
                onKeyDown={(e) => onOptionKeyDown(e, index)}
                className={`flex items-center gap-2 px-2.5 py-1.5 rounded-xl text-xs font-semibold transition-colors cursor-pointer ${
                  selected
                    ? "bg-[var(--panel)] text-[var(--ink)]"
                    : "text-[var(--muted)] hover:bg-[var(--panel)] hover:text-[var(--ink)]"
                }`}
              >
                <span
                  aria-hidden="true"
                  className="w-4 h-4 rounded-full border border-black/10"
                  style={{ backgroundColor: accent.color }}
                />
                {accent.name}
              </button>
            );
          })}
        </div>
      ) : null}
    </div>
  );
}
