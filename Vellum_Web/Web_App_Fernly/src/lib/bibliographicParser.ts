// Universal Bibliographic and Identifier Extraction Engine
// Parses BibTeX, RIS, CSV, TSV, and text lists to strictly extract verified papers with DOIs or URLs.

export interface ParsedPublication {
  id: string;
  doi: string;
  raw: string;
  title: string;
  authors?: string;
  year?: number;
  journal?: string;
}

export interface ImportSummary {
  fileName?: string;
  totalParsed: number;
  validWithDoi: number;
  duplicatesRemoved: number;
  skippedWithoutDoi: number;
}

/**
 * Normalizes DOI strings into canonical lowercase format: 10.xxxx/...
 */
export function normalizeDoi(raw?: string): string | null {
  if (!raw) return null;
  const cleaned = raw
    .trim()
    .replace(/^https?:\/\/(dx\.)?doi\.org\//i, "")
    .replace(/^doi:\s*/i, "")
    .replace(/[.,;)\]"'>]+$/, "")
    .trim();
  const match = cleaned.match(/10\.\d{4,9}\/[-._;()/:A-Za-z0-9]+/i);
  return match ? match[0].toLowerCase() : null;
}

/**
 * Formats multi-author strings into "FirstAuthor et al." or "FirstAuthor"
 */
export function formatAuthors(raw?: string): string {
  if (!raw) return "";
  const cleaned = raw.replace(/[{}]/g, "").trim();
  const parts = cleaned.split(/\s+(?:and|&|,)\s+/i);
  if (parts.length === 0 || !parts[0]) return "";
  return parts.length > 1 ? `${parts[0].trim()} et al.` : parts[0].trim();
}

/**
 * High-precision bibliographic parser for BibTeX, RIS, CSV, TSV, and text lists.
 * STRICTLY filters only real publication entries with valid DOIs or direct URLs.
 */
export function parseInputFilesToCandidates(
  content: string,
  fileName?: string
): { candidates: ParsedPublication[]; summary: ImportSummary } {
  const trimmed = content.trim();
  if (!trimmed) {
    return {
      candidates: [],
      summary: { totalParsed: 0, validWithDoi: 0, duplicatesRemoved: 0, skippedWithoutDoi: 0 },
    };
  }

  const lowerName = (fileName || "").toLowerCase();
  const rawCandidates: Array<{
    doi: string;
    raw: string;
    title: string;
    authors?: string;
    year?: number;
    journal?: string;
  }> = [];

  let skippedCount = 0;

  // 1. BibTeX Parsing (@article{...}, @book{...}, etc.)
  if (
    lowerName.endsWith(".bib") ||
    trimmed.includes("@article") ||
    trimmed.includes("@inproceedings") ||
    trimmed.includes("@book") ||
    trimmed.includes("@misc")
  ) {
    const entries = trimmed.split(/@\w+\s*\{/i);
    for (let i = 1; i < entries.length; i++) {
      const entry = entries[i];

      // Extract DOI
      let doi: string | null = null;
      const mDoi = entry.match(/\bdoi\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|([^,\n\}]+))/i);
      if (mDoi) {
        doi = normalizeDoi(mDoi[1] || mDoi[2] || mDoi[3]);
      }
      if (!doi) {
        const mInline = entry.match(/\b10\.\d{4,9}\/[-._;()/:A-Za-z0-9]+/i);
        if (mInline) {
          doi = normalizeDoi(mInline[0]);
        }
      }

      // Extract URL if DOI wasn't found
      let url: string | null = null;
      const mUrl = entry.match(/\burl\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|([^,\n\}]+))/i);
      if (mUrl) {
        const u = (mUrl[1] || mUrl[2] || mUrl[3] || "").trim();
        if (u.startsWith("http")) url = u;
      }

      // If neither valid DOI nor direct URL exists, skip this entry completely!
      if (!doi && !url) {
        skippedCount++;
        continue;
      }

      // Extract Title
      let title = "Academic Publication";
      const mTitle = entry.match(/\btitle\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|([^,\n\}]+))/i);
      if (mTitle) {
        const t = (mTitle[1] || mTitle[2] || mTitle[3] || "").replace(/[{}]/g, "").replace(/\s+/g, " ").trim();
        if (t.length > 3) title = t;
      }

      // Extract Author
      let authors = "";
      const mAuth = entry.match(/\bauthor\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|([^,\n\}]+))/i);
      if (mAuth) {
        authors = formatAuthors(mAuth[1] || mAuth[2] || mAuth[3]);
      }

      // Extract Year
      let year: number | undefined;
      const mYear = entry.match(/\byear\s*=\s*[\{"\']?(\d{4})[\}"\']?/i);
      if (mYear) {
        year = parseInt(mYear[1], 10);
      }

      // Extract Journal
      let journal = "";
      const mJournal = entry.match(/\b(?:journal|booktitle)\s*=\s*(?:\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}|"([^"]*)"|([^,\n\}]+))/i);
      if (mJournal) {
        journal = (mJournal[1] || mJournal[2] || mJournal[3] || "").replace(/[{}]/g, "").trim();
      }

      const identifier = doi || url!;
      rawCandidates.push({
        doi: identifier,
        raw: identifier,
        title,
        authors,
        year,
        journal,
      });
    }
  }
  // 2. RIS Format Parsing (TY .. ER)
  else if (
    lowerName.endsWith(".ris") ||
    trimmed.includes("TY  -") ||
    trimmed.includes("ER  -")
  ) {
    const records = trimmed.split(/(?:^|\r?\n)ER\s*-(?:[^\r\n]*)?(?:\r?\n|$)/i);
    for (const record of records) {
      if (!record.trim()) continue;

      let doi: string | null = null;
      let url: string | null = null;
      let title = "";
      let author = "";
      let year: number | undefined;
      let journal = "";

      for (const rawLine of record.split(/\r?\n/)) {
        const line = rawLine.trim();
        const m = line.match(/^([A-Z0-9]{2})\s*-\s*(.*)$/i);
        if (!m) continue;
        const tag = m[1].toUpperCase();
        const val = m[2].trim();

        if (tag === "DO" || tag === "DI") {
          doi = normalizeDoi(val);
        } else if (tag === "UR" || tag === "LK") {
          if (val.startsWith("http")) url = val;
          if (!doi) doi = normalizeDoi(val);
        } else if (tag === "TI" || tag === "T1") {
          title = (title ? `${title} ` : "") + val;
        } else if ((tag === "AU" || tag === "A1") && !author) {
          author = formatAuthors(val);
        } else if ((tag === "PY" || tag === "Y1") && !year) {
          const ym = val.match(/\b(19|20)\d{2}\b/);
          if (ym) year = parseInt(ym[0], 10);
        } else if (tag === "JO" || tag === "JF" || tag === "JA") {
          journal = val;
        }
      }

      if (!doi && !url) {
        skippedCount++;
        continue;
      }

      const identifier = doi || url!;
      rawCandidates.push({
        doi: identifier,
        raw: identifier,
        title: title || `Academic Article (${identifier.substring(0, 24)})`,
        authors: author,
        year,
        journal,
      });
    }
  }
  // 3. CSV / TSV Parsing
  else if (
    lowerName.endsWith(".csv") ||
    lowerName.endsWith(".tsv") ||
    (trimmed.includes(",") && trimmed.split("\n").length > 1)
  ) {
    const delimiter = lowerName.endsWith(".tsv") || (!trimmed.includes(",") && trimmed.includes("\t")) ? "\t" : ",";
    const lines = trimmed.split(/\r?\n/).filter((l) => l.trim().length > 0);

    if (lines.length > 0) {
      const headerTokens = lines[0]
        .split(delimiter)
        .map((h) => h.replace(/^["']|["']$/g, "").toLowerCase().replace(/[^a-z0-9]/g, ""));

      const doiCol = headerTokens.findIndex(
        (h) => h.includes("doi") || h === "di" || h === "digitalobjectidentifier" || h.includes("link") || h.includes("url")
      );
      const titleCol = headerTokens.findIndex((h) => h.includes("title") || h === "ti");
      const authorCol = headerTokens.findIndex((h) => h.includes("author") || h === "au" || h.includes("creator"));
      const yearCol = headerTokens.findIndex((h) => h.includes("year") || h === "py" || h.includes("date"));
      const journalCol = headerTokens.findIndex((h) => h.includes("journal") || h === "source" || h.includes("venue"));

      const startIdx = doiCol !== -1 || titleCol !== -1 ? 1 : 0;

      for (let i = startIdx; i < lines.length; i++) {
        const line = lines[i];
        const cells = line.split(delimiter).map((c) => c.replace(/^["']|["']$/g, "").trim());

        let doi: string | null = null;
        if (doiCol !== -1 && cells[doiCol]) {
          doi = normalizeDoi(cells[doiCol]);
        }
        if (!doi) {
          for (const cell of cells) {
            const m = cell.match(/\b10\.\d{4,9}\/[-._;()/:A-Za-z0-9]+/i);
            if (m) {
              doi = normalizeDoi(m[0]);
              break;
            }
          }
        }

        let url: string | null = null;
        if (!doi) {
          for (const cell of cells) {
            if (cell.startsWith("http://") || cell.startsWith("https://")) {
              url = cell;
              break;
            }
          }
        }

        if (!doi && !url) {
          skippedCount++;
          continue;
        }

        const identifier = doi || url!;
        const title = titleCol !== -1 && cells[titleCol] ? cells[titleCol] : `Academic Article (${identifier.substring(0, 24)})`;
        const authors = authorCol !== -1 && cells[authorCol] ? formatAuthors(cells[authorCol]) : "";
        let year: number | undefined;
        if (yearCol !== -1 && cells[yearCol]) {
          const ym = cells[yearCol].match(/\b(19|20)\d{2}\b/);
          if (ym) year = parseInt(ym[0], 10);
        }
        const journal = journalCol !== -1 && cells[journalCol] ? cells[journalCol] : "";

        rawCandidates.push({
          doi: identifier,
          raw: identifier,
          title,
          authors,
          year,
          journal,
        });
      }
    }
  }
  // 4. Plain Text / Pasted DOI List Fallback (STRICT DOI & URL extraction)
  else {
    const doiMatches = trimmed.matchAll(/\b10\.\d{4,9}\/[-._;()/:A-Za-z0-9]+/gi);
    for (const m of doiMatches) {
      const doi = normalizeDoi(m[0]);
      if (doi) {
        rawCandidates.push({
          doi,
          raw: doi,
          title: `Academic Publication (${doi})`,
        });
      }
    }

    const urlMatches = trimmed.matchAll(/https?:\/\/[^\s"'<>\),]+/gi);
    for (const m of urlMatches) {
      const u = m[0].replace(/[.,;)\]]+$/, "");
      // If it's a doi.org link, it was already matched by the DOI pattern above
      if (/https?:\/\/(dx\.)?doi\.org\//i.test(u)) {
        continue;
      }
      if (u.includes("arxiv.org") || u.includes("biorxiv.org") || u.endsWith(".pdf")) {
        rawCandidates.push({
          doi: u,
          raw: u,
          title: `Direct Academic Paper (${u.substring(0, 32)}...)`,
        });
      }
    }
  }

  // Deduplicate by normalized identifier
  const seen = new Map<string, typeof rawCandidates[0]>();
  let duplicatesCount = 0;

  for (const item of rawCandidates) {
    const key = item.doi.toLowerCase();
    if (seen.has(key)) {
      duplicatesCount++;
      const existing = seen.get(key)!;
      if (existing.title.startsWith("Academic") && !item.title.startsWith("Academic")) {
        existing.title = item.title;
      }
      if (!existing.authors && item.authors) existing.authors = item.authors;
      if (!existing.year && item.year) existing.year = item.year;
      if (!existing.journal && item.journal) existing.journal = item.journal;
    } else {
      seen.set(key, item);
    }
  }

  const finalCandidates: ParsedPublication[] = Array.from(seen.values()).map((item, idx) => ({
    id: `pub-${Date.now()}-${idx}-${Math.random().toString(36).substring(2, 6)}`,
    raw: item.raw,
    doi: item.doi,
    title: item.title,
    authors: item.authors,
    year: item.year,
    journal: item.journal,
  }));

  return {
    candidates: finalCandidates,
    summary: {
      fileName,
      totalParsed: rawCandidates.length + skippedCount,
      validWithDoi: finalCandidates.length,
      duplicatesRemoved: duplicatesCount,
      skippedWithoutDoi: skippedCount,
    },
  };
}
