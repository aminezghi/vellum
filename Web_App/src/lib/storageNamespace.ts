/**
 * Per-edition storage identity.
 *
 * IndexedDB and localStorage are both partitioned by origin (scheme://host:port),
 * so editions served on different ports already get separate storage. Naming the
 * database and the localStorage keys per edition makes that isolation independent
 * of the port assignment: `next dev` falls back to the next free port when the
 * requested one is busy, which can place two editions on one origin. With
 * per-edition names they still cannot read or overwrite each other's notebooks.
 *
 * Editions: Web_App (port 3000), Web_App_Apple (port 3001), Web_App_Fernly (port 3002).
 */

/** Identifies this edition. Must stay unique across the Vellum web editions. */
export const APP_ID = "web" as const;

export const APP_LABEL = "Vellum Web";

/** IndexedDB database owned by this edition. */
export const DB_NAME = `VellumWebDB_${APP_ID}`;

/** Pre-namespace database. Read-only migration source, never written to again. */
export const LEGACY_DB_NAME = "VellumWebDB";

/**
 * Which edition already migrated LEGACY_DB_NAME on this origin.
 *
 * Deliberately not app-scoped: every edition sharing an origin must observe the
 * same claim, otherwise two editions would each copy the same legacy library and
 * the collision would survive the migration.
 */
export const LEGACY_CLAIM_KEY = "vellum:legacy-db-claim";

/** Namespace a localStorage key so editions cannot overwrite each other's state. */
export function scopedKey(key: string): string {
  return `vellum:${APP_ID}:${key}`;
}

/** localStorage keys this edition reads and writes, already namespaced. */
export const STORAGE_KEYS = {
  theme: scopedKey("theme"),
  designStyle: scopedKey("design-style"),
  tokens: scopedKey("tokens"),
} as const;

/**
 * Pre-namespace localStorage keys mapped to their replacement. Values are copied
 * on first run so preferences and API tokens survive the rename.
 */
export const LEGACY_STORAGE_KEYS: Record<string, string> = {
  "vellum-theme": STORAGE_KEYS.theme,
  "vellum-design-style": STORAGE_KEYS.designStyle,
  "vellum-custom-tokens": STORAGE_KEYS.tokens,
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
