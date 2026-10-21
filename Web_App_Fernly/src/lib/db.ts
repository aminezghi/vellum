import Dexie, { Table } from "dexie";
import {
  APP_ID,
  DB_NAME,
  LEGACY_CLAIM_KEY,
  LEGACY_DB_NAME,
} from "./storageNamespace";

export interface Notebook {
  id: string;
  title: string;
  emoji: string;
  description?: string;
  createdAt: number;
  updatedAt: number;
  sourcesCount: number;
  isFeatured?: boolean;
  category?: string;
  authorName?: string;
}

export interface Source {
  id: string;
  notebookId: string;
  title: string;
  authors: string[];
  year?: number;
  abstract?: string;
  journal?: string;
  doi?: string;
  pdfBlob?: Blob;
  sizeBytes?: number;
  pageCount?: number;
  status: "ready" | "processing" | "error";
  addedAt: number;
}

export interface Note {
  id: string;
  notebookId: string;
  content: string;
  updatedAt: number;
}

export interface EvidenceExtraction {
  id: string;
  notebookId: string;
  sourceId: string;
  category: "method" | "sampling" | "statistics" | "rigour";
  claim: string;
  pageNumber: number;
  confidence: number;
}

export interface ScreeningSession {
  id: string;
  name: string;
  description?: string;
  createdAt: number;
  updatedAt: number;
  totalCount: number;
  screenedCount: number;
  includedCount: number;
  excludedCount: number;
  consecutiveExcludes: number;
  sourcesList: string[];
  duplicatesRemoved: number;
}

export interface ScreeningItem {
  id: string;
  sessionId: string;
  notebookId?: string;
  title: string;
  abstract: string;
  authors: string[];
  year?: number;
  journal?: string;
  doi?: string;
  sourceOrigin?: string;
  decision: "pending" | "included" | "excluded";
  relevanceScore?: number;
  screenedAt?: number;
  notes?: string;
}

export class VellumDatabase extends Dexie {
  notebooks!: Table<Notebook, string>;
  sources!: Table<Source, string>;
  notes!: Table<Note, string>;
  evidence!: Table<EvidenceExtraction, string>;
  screeningItems!: Table<ScreeningItem, string>;
  screeningSessions!: Table<ScreeningSession, string>;

  constructor() {
    super(DB_NAME);
    this.version(1).stores({
      notebooks: "id, title, createdAt, updatedAt, isFeatured, category",
      sources: "id, notebookId, doi, addedAt",
      notes: "id, notebookId, updatedAt",
      evidence: "id, notebookId, sourceId, category",
    });
    this.version(2).stores({
      notebooks: "id, title, createdAt, updatedAt, isFeatured, category",
      sources: "id, notebookId, doi, addedAt",
      notes: "id, notebookId, updatedAt",
      evidence: "id, notebookId, sourceId, category",
      screeningItems: "id, notebookId, decision, doi, relevanceScore, screenedAt",
    });
    this.version(3).stores({
      notebooks: "id, title, createdAt, updatedAt, isFeatured, category",
      sources: "id, notebookId, doi, addedAt",
      notes: "id, notebookId, updatedAt",
      evidence: "id, notebookId, sourceId, category",
      screeningItems: "id, sessionId, notebookId, decision, doi, relevanceScore, screenedAt",
      screeningSessions: "id, name, createdAt, updatedAt",
    });
  }
}

export const db = new VellumDatabase();

type LegacyRows = Record<string, unknown[]>;

/**
 * Open an existing IndexedDB database without touching its schema.
 *
 * Opened without a version so an existing database is read at whatever version
 * it was left at. A missing database is created empty by the browser, which we
 * detect and discard.
 */
function openExistingDatabase(name: string): Promise<IDBDatabase | null> {
  return new Promise((resolve) => {
    if (typeof indexedDB === "undefined") {
      resolve(null);
      return;
    }

    let settled = false;
    const finish = (value: IDBDatabase | null) => {
      if (settled) return;
      settled = true;
      resolve(value);
    };

    let request: IDBOpenDBRequest;
    try {
      request = indexedDB.open(name);
    } catch {
      resolve(null);
      return;
    }

    request.onsuccess = () => {
      const handle = request.result;
      if (settled) {
        handle.close();
        return;
      }
      if (handle.objectStoreNames.length === 0) {
        handle.close();
        finish(null);
        return;
      }
      finish(handle);
    };
    request.onerror = () => finish(null);
    request.onblocked = () => finish(null);
  });
}

/**
 * Whether a database already exists on this origin.
 *
 * `indexedDB.open` creates the database as a side effect, so probing for a
 * legacy database that is not there would leave an empty one behind. Where the
 * browser can enumerate its databases we ask first and only open a known
 * database; older browsers fall back to opening it.
 */
async function databaseExists(name: string): Promise<boolean> {
  if (typeof indexedDB === "undefined" || typeof indexedDB.databases !== "function") {
    return true;
  }
  try {
    const databases = await indexedDB.databases();
    return databases.some((database) => database.name === name);
  } catch {
    return true;
  }
}

/** Read every object store of an existing database. */
function readAllStores(handle: IDBDatabase): Promise<LegacyRows> {
  const storeNames = Array.from(handle.objectStoreNames);
  return new Promise((resolve, reject) => {
    const rows: LegacyRows = {};
    if (storeNames.length === 0) {
      resolve(rows);
      return;
    }

    const transaction = handle.transaction(storeNames, "readonly");
    for (const storeName of storeNames) {
      const request = transaction.objectStore(storeName).getAll();
      request.onsuccess = () => {
        rows[storeName] = request.result as unknown[];
      };
      request.onerror = () => reject(request.error);
    }
    transaction.oncomplete = () => resolve(rows);
    transaction.onerror = () => reject(transaction.error);
    transaction.onabort = () => reject(transaction.error);
  });
}

/**
 * Copy the pre-namespace library into this edition's database, once.
 *
 * Runs only when this edition's database is still empty, the legacy database
 * still exists, and no other edition on this origin has claimed it. The legacy
 * database is left untouched so the copy stays recoverable.
 */
export async function migrateLegacyDatabase(): Promise<boolean> {
  if (typeof indexedDB === "undefined" || typeof localStorage === "undefined") {
    return false;
  }

  try {
    for (const table of db.tables) {
      if ((await table.count()) > 0) {
        return false;
      }
    }

    if (localStorage.getItem(LEGACY_CLAIM_KEY)) {
      return false;
    }

    if (!(await databaseExists(LEGACY_DB_NAME))) {
      return false;
    }

    const legacy = await openExistingDatabase(LEGACY_DB_NAME);
    if (!legacy) {
      return false;
    }

    const rows = await readAllStores(legacy);
    legacy.close();

    const owned = new Set(db.tables.map((table) => table.name));
    let copied = 0;
    for (const [storeName, records] of Object.entries(rows)) {
      if (!owned.has(storeName) || records.length === 0) {
        continue;
      }
      await db.table<unknown, string>(storeName).bulkPut(records);
      copied += records.length;
    }

    localStorage.setItem(LEGACY_CLAIM_KEY, APP_ID);
    console.info(
      `[storage] migrated ${copied} record(s) from "${LEGACY_DB_NAME}" into "${DB_NAME}"`,
    );
    return copied > 0;
  } catch (error) {
    console.warn("[storage] legacy database migration skipped:", error);
    return false;
  }
}

// Starting point is clean & empty per user specifications.
export async function seedInitialNotebooks(): Promise<void> {
  try {
    // Clean up any legacy pre-seeded demo notebooks (nb-1 to nb-7) if present
    const demoIds = ["nb-1", "nb-2", "nb-3", "nb-4", "nb-5", "nb-6", "nb-7"];
    await db.notebooks.bulkDelete(demoIds);
  } catch (err) {
    console.debug("IndexedDB initialization note:", err);
  }
}

/** Prepare this edition's storage: adopt any legacy library, then clear demo notebooks. */
export async function initializeStorage(): Promise<void> {
  await migrateLegacyDatabase();
  await seedInitialNotebooks();
}

