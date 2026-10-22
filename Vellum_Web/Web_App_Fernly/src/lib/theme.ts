"use client";

/**
 * The studio's single source of truth for light/dark.
 *
 * Light/dark used to be held in component state in two places (the header and
 * the notebook workspace), each with its own copy of the same effect: read
 * localStorage, decide, then write three attributes onto <html> plus one class
 * onto <body>, then mirror the result back into React state. Because the two
 * copies only ran on mount they could disagree — toggling in the header left
 * the workspace's toggle showing the old value until it remounted.
 *
 * Here the DOM *is* the state. `useSyncExternalStore` reads it, and every
 * writer goes through `setTheme`, which updates the DOM and notifies React.
 * That also removes the setState-inside-an-effect that the compiler objects to:
 * React is being told about an external change, which is what an effect is for.
 */

import { useSyncExternalStore } from "react";
import { STORAGE_KEYS } from "./storageNamespace";

export type Theme = "light" | "dark";

/** The four Fernly accent colourways. */
export type Accent = "emerald" | "ocean" | "plum" | "ember";

const listeners = new Set<() => void>();

function notify(): void {
  for (const listener of listeners) listener();
}

function subscribe(listener: () => void): () => void {
  listeners.add(listener);
  // Another tab changing the theme should move this one too.
  window.addEventListener("storage", listener);
  return () => {
    listeners.delete(listener);
    window.removeEventListener("storage", listener);
  };
}

/** The theme currently applied to the document. */
function readTheme(): Theme {
  return document.documentElement.classList.contains("dark") ? "dark" : "light";
}

/** The server has no document; it always renders the light shell. */
function readServerTheme(): Theme {
  return "light";
}

/** Apply a theme to the document, persist it, and tell React. */
export function setTheme(theme: Theme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.setAttribute("data-theme", theme);
  document.body.classList.toggle("dark", theme === "dark");
  localStorage.setItem(STORAGE_KEYS.theme, theme);
  notify();
}

/**
 * Apply the saved theme and accent, or the operating system's theme preference,
 * on first mount. A theme is only persisted when the user picks one, so the OS
 * preference keeps winning until then.
 */
export function initializeAppearance(): void {
  const savedTheme = localStorage.getItem(STORAGE_KEYS.theme);
  const prefersDark = window.matchMedia("(prefers-color-scheme: dark)").matches;
  const theme: Theme =
    savedTheme === "dark" || savedTheme === "light"
      ? savedTheme
      : prefersDark
        ? "dark"
        : "light";

  const root = document.documentElement;
  root.classList.toggle("dark", theme === "dark");
  root.setAttribute("data-theme", theme);
  document.body.classList.toggle("dark", theme === "dark");

  const savedAccent = localStorage.getItem(STORAGE_KEYS.accent);
  root.setAttribute("data-accent", isAccent(savedAccent) ? savedAccent : "emerald");

  notify();
}

function isAccent(value: string | null): value is Accent {
  return value === "emerald" || value === "ocean" || value === "plum" || value === "ember";
}

/** Switch the accent colourway. */
export function setAccent(accent: Accent): void {
  document.documentElement.setAttribute("data-accent", accent);
  localStorage.setItem(STORAGE_KEYS.accent, accent);
  notify();
}

/** The accent currently applied to the document. */
function readAccent(): Accent {
  const value = document.documentElement.getAttribute("data-accent");
  return isAccent(value) ? value : "emerald";
}

function readServerAccent(): Accent {
  return "emerald";
}

/** The theme as React sees it. */
export function useTheme(): Theme {
  return useSyncExternalStore(subscribe, readTheme, readServerTheme);
}

/** The accent as React sees it. */
export function useAccent(): Accent {
  return useSyncExternalStore(subscribe, readAccent, readServerAccent);
}
