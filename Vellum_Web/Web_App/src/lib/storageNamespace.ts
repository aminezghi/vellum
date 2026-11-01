/**
 * Storage identity for this edition.
 *
 * IndexedDB and localStorage are both partitioned by origin (scheme://host:port).
 * The database and the localStorage keys are nevertheless named explicitly, for
 * two reasons:
 *
 * 1. Earlier builds of every Vellum web edition shared one database called
 *    "VellumWebDB" and one set of localStorage keys. Anything already stored
 *    under those names is migrated once, into the namespaced names below, so
 *    existing notebooks, preferences and API tokens survive the rename.
 * 2. The namespace keeps this edition's data under a name of its own, so it
 *    can never be read or overwritten by another Vellum app running on the same
 *    origin (for example when a dev server falls back to a busy port).
 *
 * Edition: Vellum Web - Fernly Botanical Bento (port 3002).
 */

/** Identifies this edition. Must stay unique across the Vellum web editions. */
export const APP_ID = "fernly" as const;

export const APP_LABEL = "Vellum Web by Amine";

/** IndexedDB database owned by this edition. */
export const DB_NAME = `VellumWebDB_${APP_ID}`;

/** Pre-namespace database. Read-only migration source, never written to again. */
export const LEGACY_DB_NAME = "VellumWebDB";

/**
 * Which app already migrated LEGACY_DB_NAME on this origin.
 *
 * Deliberately not app-scoped: every Vellum app sharing an origin must observe
 * the same claim, otherwise two of them would each copy the same legacy library
 * and the collision would survive the migration.
 */
export const LEGACY_CLAIM_KEY = "vellum:legacy-db-claim";

/** Namespace a localStorage key so no other app can overwrite this edition's state. */
export function scopedKey(key: string): string {
  return `vellum:${APP_ID}:${key}`;
}

/** localStorage keys this edition reads and writes, already namespaced. */
export const STORAGE_KEYS = {
  theme: scopedKey("theme"),
  tokens: scopedKey("tokens"),
  accent: scopedKey("accent"),
  researcherField: scopedKey("researcher-field"),
  activeScreeningSession: scopedKey("active-screening-session"),
} as const;

/**
 * Pre-namespace localStorage keys mapped to their replacement. Values are copied
 * on first run so preferences and API tokens survive the rename.
 */
export const LEGACY_STORAGE_KEYS: Record<string, string> = {
  "vellum-theme": STORAGE_KEYS.theme,
  "vellum-custom-tokens": STORAGE_KEYS.tokens,
  "fernly-accent": STORAGE_KEYS.accent,
  "vellum-researcher-field": STORAGE_KEYS.researcherField,
  "vellum_active_screening_session": STORAGE_KEYS.activeScreeningSession,
};

/**
 * Boot snippet that copies legacy localStorage values into their namespaced
 * replacements. Safe to run on every page load: it only fills in keys that are
 * still missing.
 */
export const LEGACY_STORAGE_BOOT = `
try {
  var __vellumLegacy = ${JSON.stringify(LEGACY_STORAGE_KEYS)};
  for (var __vellumKey in __vellumLegacy) {
    var __vellumValue = localStorage.getItem(__vellumKey);
    if (__vellumValue !== null && localStorage.getItem(__vellumLegacy[__vellumKey]) === null) {
      localStorage.setItem(__vellumLegacy[__vellumKey], __vellumValue);
    }
  }
} catch (e) {}
`;
