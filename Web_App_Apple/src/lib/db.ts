import Dexie, { Table } from "dexie";

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

export class VellumDatabase extends Dexie {
  notebooks!: Table<Notebook, string>;
  sources!: Table<Source, string>;
  notes!: Table<Note, string>;
  evidence!: Table<EvidenceExtraction, string>;

  constructor() {
    super("VellumWebDB");
    this.version(1).stores({
      notebooks: "id, title, createdAt, updatedAt, isFeatured, category",
      sources: "id, notebookId, doi, addedAt",
      notes: "id, notebookId, updatedAt",
      evidence: "id, notebookId, sourceId, category",
    });
  }
}

export const db = new VellumDatabase();

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

