// Client-Side Active Learning Systematic Review Screening Engine (ASReview Protocol)
// Provides 100% in-browser, private, zero-latency text vectorization and Multinomial Naive Bayes classifier.

export interface ScreeningCandidate {
  id: string;
  sessionId?: string;
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

export interface DuplicateDetail {
  keptTitle: string;
  duplicateTitle: string;
  source: string;
  reason: "doi_match" | "exact_title" | "fuzzy_title";
}

export interface DeduplicationResult {
  uniqueCandidates: ScreeningCandidate[];
  duplicateCount: number;
  duplicatesRemoved: DuplicateDetail[];
}

/**
 * Deduplicates new candidate references against existing candidates using
 * 1. Normalized DOI matching
 * 2. Normalized Title matching
 * 3. High-threshold Token Jaccard similarity (> 0.88)
 */
export function deduplicateCandidates(
  existingCandidates: ScreeningCandidate[],
  newCandidates: ScreeningCandidate[]
): DeduplicationResult {
  const combined = [...existingCandidates];
  const duplicatesRemoved: DuplicateDetail[] = [];

  const normalizeDoi = (doi?: string) =>
    (doi || "")
      .toLowerCase()
      .replace(/^https?:\/\/(dx\.)?doi\.org\//i, "")
      .replace(/^doi:\s*/i, "")
      .trim();

  const normalizeTitle = (title: string) =>
    (title || "")
      .toLowerCase()
      .replace(/^[a-z0-9]+:\s*/i, "")
      .replace(/^(the|a|an)\s+/i, "")
      .replace(/[^a-z0-9]/g, "")
      .trim();

  const getWordTokens = (title: string): Set<string> =>
    new Set(
      (title || "")
        .toLowerCase()
        .replace(/[^a-z0-9\s]/g, "")
        .split(/\s+/)
        .filter((w) => w.length > 2)
    );

  const calculateSimilarity = (wordsA: Set<string>, wordsB: Set<string>): number => {
    if (wordsA.size === 0 || wordsB.size === 0) return 0;
    let intersection = 0;
    for (const w of wordsA) {
      if (wordsB.has(w)) intersection++;
    }
    const union = wordsA.size + wordsB.size - intersection;
    return union > 0 ? intersection / union : 0;
  };

  for (const candidate of newCandidates) {
    const candDoi = normalizeDoi(candidate.doi);
    const candNormTitle = normalizeTitle(candidate.title);
    const candWords = getWordTokens(candidate.title);

    let isDuplicate = false;

    for (let i = 0; i < combined.length; i++) {
      const existing = combined[i];
      const existDoi = normalizeDoi(existing.doi);
      const existNormTitle = normalizeTitle(existing.title);

      // Check 1: DOI match
      if (candDoi && existDoi && candDoi === existDoi) {
        isDuplicate = true;
        duplicatesRemoved.push({
          keptTitle: existing.title,
          duplicateTitle: candidate.title,
          source: candidate.sourceOrigin || "Secondary Source",
          reason: "doi_match",
        });
        if (!existing.abstract && candidate.abstract) existing.abstract = candidate.abstract;
        if (!existing.journal && candidate.journal) existing.journal = candidate.journal;
        if (candidate.sourceOrigin && !existing.sourceOrigin?.includes(candidate.sourceOrigin)) {
          existing.sourceOrigin = existing.sourceOrigin
            ? `${existing.sourceOrigin}, ${candidate.sourceOrigin}`
            : candidate.sourceOrigin;
        }
        break;
      }

      // Check 2: Exact normalized title match
      if (candNormTitle && existNormTitle && candNormTitle === existNormTitle) {
        isDuplicate = true;
        duplicatesRemoved.push({
          keptTitle: existing.title,
          duplicateTitle: candidate.title,
          source: candidate.sourceOrigin || "Secondary Source",
          reason: "exact_title",
        });
        if (!existing.abstract && candidate.abstract) existing.abstract = candidate.abstract;
        if (!existing.doi && candidate.doi) existing.doi = candidate.doi;
        if (candidate.sourceOrigin && !existing.sourceOrigin?.includes(candidate.sourceOrigin)) {
          existing.sourceOrigin = existing.sourceOrigin
            ? `${existing.sourceOrigin}, ${candidate.sourceOrigin}`
            : candidate.sourceOrigin;
        }
        break;
      }

      // Check 3: High-confidence fuzzy title similarity
      if (candWords.size >= 4) {
        const existWords = getWordTokens(existing.title);
        const sim = calculateSimilarity(candWords, existWords);
        const yearDiff = Math.abs((candidate.year || 2024) - (existing.year || 2024));

        if (sim >= 0.88 && yearDiff <= 1) {
          isDuplicate = true;
          duplicatesRemoved.push({
            keptTitle: existing.title,
            duplicateTitle: candidate.title,
            source: candidate.sourceOrigin || "Secondary Source",
            reason: "fuzzy_title",
          });
          if (!existing.abstract && candidate.abstract) existing.abstract = candidate.abstract;
          if (!existing.doi && candidate.doi) existing.doi = candidate.doi;
          if (candidate.sourceOrigin && !existing.sourceOrigin?.includes(candidate.sourceOrigin)) {
            existing.sourceOrigin = existing.sourceOrigin
              ? `${existing.sourceOrigin}, ${candidate.sourceOrigin}`
              : candidate.sourceOrigin;
          }
          break;
        }
      }
    }

    if (!isDuplicate) {
      combined.push(candidate);
    }
  }

  return {
    uniqueCandidates: combined,
    duplicateCount: duplicatesRemoved.length,
    duplicatesRemoved,
  };
}

const STOPWORDS = new Set([
  "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
  "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by",
  "can", "can't", "cannot", "could", "did", "didn't", "do", "does", "doesn't", "doing", "don't",
  "down", "during", "each", "few", "for", "from", "further", "had", "has", "have", "having", "he",
  "her", "here", "hers", "herself", "him", "himself", "his", "how", "i", "if", "in", "into", "is",
  "isn't", "it", "its", "itself", "let's", "me", "more", "most", "must", "my", "myself", "no",
  "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought", "our", "ours", "ourselves",
  "out", "over", "own", "same", "she", "should", "so", "some", "such", "than", "that", "the",
  "their", "theirs", "them", "themselves", "then", "there", "these", "they", "this", "those",
  "through", "to", "too", "under", "until", "up", "very", "was", "we", "were", "what", "when",
  "where", "which", "while", "who", "whom", "why", "with", "would", "you", "your", "yours",
  "study", "paper", "results", "methods", "conclusion", "background", "aim", "data", "analysis",
]);

export function tokenize(text: string): string[] {
  if (!text) return [];
  const rawTokens = text.toLowerCase().match(/\b[a-zA-Z]{3,24}\b/g) || [];
  return rawTokens.filter((token) => !STOPWORDS.has(token));
}

export class ActiveLearningClassifier {
  private idf: Map<string, number> = new Map();
  private includedWordCounts: Map<string, number> = new Map();
  private excludedWordCounts: Map<string, number> = new Map();
  private totalIncludedWords = 0;
  private totalExcludedWords = 0;
  private totalIncludedDocs = 0;
  private totalExcludedDocs = 0;
  private vocabulary: Set<string> = new Set();

  /**
   * Train the Active Learning model on currently labeled papers and score all pending papers.
   */
  public retrainAndRank(candidates: ScreeningCandidate[]): ScreeningCandidate[] {
    const included = candidates.filter((c) => c.decision === "included");
    const excluded = candidates.filter((c) => c.decision === "excluded");
    const pending = candidates.filter((c) => c.decision === "pending");

    // If no labeled data exists yet, return initial ranking by default
    if (included.length === 0 && excluded.length === 0) {
      return candidates;
    }

    // Step 1: Build IDF across all candidate documents
    this.computeIdf(candidates);

    // Step 2: Accumulate term frequencies per class
    this.includedWordCounts.clear();
    this.excludedWordCounts.clear();
    this.totalIncludedWords = 0;
    this.totalExcludedWords = 0;
    this.totalIncludedDocs = included.length;
    this.totalExcludedDocs = excluded.length;
    this.vocabulary.clear();

    for (const doc of included) {
      const tokens = tokenize(`${doc.title} ${doc.abstract}`);
      for (const token of tokens) {
        this.vocabulary.add(token);
        const count = (this.includedWordCounts.get(token) || 0) + 1;
        this.includedWordCounts.set(token, count);
        this.totalIncludedWords++;
      }
    }

    for (const doc of excluded) {
      const tokens = tokenize(`${doc.title} ${doc.abstract}`);
      for (const token of tokens) {
        this.vocabulary.add(token);
        const count = (this.excludedWordCounts.get(token) || 0) + 1;
        this.excludedWordCounts.set(token, count);
        this.totalExcludedWords++;
      }
    }

    // Step 3: Score pending papers with Laplace-smoothed Naive Bayes log-odds
    const vocabSize = Math.max(1, this.vocabulary.size);
    const alpha = 1.0; // Laplace smoothing parameter

    // Class priors with Laplace smoothing
    const priorIncluded = Math.log((this.totalIncludedDocs + 1) / (this.totalIncludedDocs + this.totalExcludedDocs + 2));
    const priorExcluded = Math.log((this.totalExcludedDocs + 1) / (this.totalIncludedDocs + this.totalExcludedDocs + 2));

    const scoredPending: ScreeningCandidate[] = pending.map((doc) => {
      const tokens = tokenize(`${doc.title} ${doc.abstract}`);
      let logProbIncluded = priorIncluded;
      let logProbExcluded = priorExcluded;

      for (const token of tokens) {
        const idfWeight = this.idf.get(token) || 1.0;

        const countInc = this.includedWordCounts.get(token) || 0;
        const probWordInc = (countInc + alpha) / (this.totalIncludedWords + alpha * vocabSize);
        logProbIncluded += idfWeight * Math.log(probWordInc);

        const countExc = this.excludedWordCounts.get(token) || 0;
        const probWordExc = (countExc + alpha) / (this.totalExcludedWords + alpha * vocabSize);
        logProbExcluded += idfWeight * Math.log(probWordExc);
      }

      // Sigmoid over log-odds with clipping to avoid NaN/Infinity
      const logOdds = Math.max(-10, Math.min(10, logProbIncluded - logProbExcluded));
      const probability = 1 / (1 + Math.exp(-logOdds));

      return {
        ...doc,
        relevanceScore: Math.round(probability * 100),
      };
    });

    // Step 4: Active Learning Query Strategy -> Sort pending by highest probability first
    scoredPending.sort((a, b) => (b.relevanceScore || 0) - (a.relevanceScore || 0));

    // Return labeled items followed by actively ranked pending candidates
    const labeled = candidates.filter((c) => c.decision !== "pending");
    return [...labeled, ...scoredPending];
  }

  private computeIdf(docs: ScreeningCandidate[]): void {
    this.idf.clear();
    const docCount = Math.max(1, docs.length);
    const df = new Map<string, number>();

    for (const doc of docs) {
      const uniqueTokens = new Set(tokenize(`${doc.title} ${doc.abstract}`));
      for (const token of uniqueTokens) {
        df.set(token, (df.get(token) || 0) + 1);
      }
    }

    for (const [token, count] of df.entries()) {
      // Smooth IDF formula: ln((1 + N) / (1 + df)) + 1
      const idfValue = Math.log((1 + docCount) / (1 + count)) + 1;
      this.idf.set(token, idfValue);
    }
  }
}

/**
 * Parses CSV/TSV text handling quotes, multiline fields, and escaped delimiters.
 */
export function parseCsvRows(text: string, delimiter: string = ","): string[][] {
  const rows: string[][] = [];
  let currentRow: string[] = [];
  let currentField = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const char = text[i];
    const nextChar = text[i + 1];

    if (inQuotes) {
      if (char === '"' && nextChar === '"') {
        currentField += '"';
        i++; // skip escaped quote
      } else if (char === '"') {
        inQuotes = false;
      } else {
        currentField += char;
      }
    } else {
      if (char === '"') {
        inQuotes = true;
      } else if (char === delimiter) {
        currentRow.push(currentField.trim());
        currentField = "";
      } else if (char === "\r") {
        // skip carriage return
      } else if (char === "\n") {
        currentRow.push(currentField.trim());
        if (currentRow.some((field) => field.length > 0)) {
          rows.push(currentRow);
        }
        currentRow = [];
        currentField = "";
      } else {
        currentField += char;
      }
    }
  }

  if (currentField || currentRow.length > 0) {
    currentRow.push(currentField.trim());
    if (currentRow.some((field) => field.length > 0)) {
      rows.push(currentRow);
    }
  }

  return rows;
}

/**
 * Parses BibTeX formatted string into candidate items.
 */
export function parseBibtexText(text: string): Partial<ScreeningCandidate>[] {
  const records: Partial<ScreeningCandidate>[] = [];
  const entries = text.split(/@\w+\s*\{/i);

  for (let i = 1; i < entries.length; i++) {
    const entry = entries[i];
    const getField = (fieldNames: string[]): string => {
      for (const name of fieldNames) {
        const regex = new RegExp(
          `${name}\\s*=\\s*(?:\\{([^{}]*(?:\\{[^{}]*\\}[^{}]*)*)\\}|"([^"]*)"|([^,\\n\\}]+))`,
          "i"
        );
        const match = entry.match(regex);
        if (match) {
          return (match[1] || match[2] || match[3] || "").trim();
        }
      }
      return "";
    };

    const title = getField(["title"]).replace(/[{}]/g, "").trim();
    const abstract = getField(["abstract", "summary", "notes"]).replace(/[{}]/g, "").trim();
    const authorStr = getField(["author", "authors"]).replace(/[{}]/g, "").trim();
    const authors = authorStr
      ? authorStr
          .split(/\s+and\s+/i)
          .map((a) => a.trim())
          .filter(Boolean)
      : ["Unknown Author"];

    const yearMatch = getField(["year", "date"]).match(/\b(19|20)\d{2}\b/);
    const year = yearMatch ? parseInt(yearMatch[0], 10) : 2024;
    const journal = getField(["journal", "booktitle", "publisher"]).replace(/[{}]/g, "").trim();
    const doi = getField(["doi"]).replace(/[{}]/g, "").replace(/^https?:\/\/doi\.org\//i, "").trim();

    if (title) {
      records.push({
        id: `bib-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        title,
        abstract: abstract || "No abstract provided in BibTeX record.",
        authors: authors.length > 0 ? authors : ["Unknown Author"],
        year,
        journal,
        doi,
        decision: "pending",
      });
    }
  }

  return records;
}

/**
 * Parses RIS format text into structured candidate records.
 */
export function parseRisText(risContent: string): Partial<ScreeningCandidate>[] {
  const records: Partial<ScreeningCandidate>[] = [];

  // Check if standard ER - delimiter or TY - records
  let rawEntries = risContent.split(/(?:^|\r?\n)ER\s*-(?:[^\r\n]*)?(?:\r?\n|$)/i);
  if (rawEntries.length <= 1 && (risContent.match(/TY\s*-\s*/gi)?.length || 0) > 1) {
    rawEntries = risContent.split(/(?:^|\r?\n)(?=TY\s*-\s*)/i);
  }

  for (const entry of rawEntries) {
    if (!entry.trim()) continue;
    let title = "";
    let abstract = "";
    const authors: string[] = [];
    let year: number | undefined;
    let journal = "";
    let doi = "";

    const lines = entry.split(/\r?\n/);
    let currentTag = "";

    for (const rawLine of lines) {
      const line = rawLine.trim();
      if (!line) continue;

      const match = rawLine.match(/^([A-Z0-9]{2})\s*-\s*(.*)$/i);
      if (match) {
        currentTag = match[1].toUpperCase();
        const val = match[2].trim();

        if (currentTag === "TI" || currentTag === "T1" || currentTag === "CT") {
          title = val;
        } else if (currentTag === "AB" || currentTag === "N2") {
          abstract += (abstract ? " " : "") + val;
        } else if (currentTag === "AU" || currentTag === "A1" || currentTag === "A2") {
          authors.push(val);
        } else if (currentTag === "PY" || currentTag === "Y1" || currentTag === "DA") {
          const yMatch = val.match(/\b(19|20)\d{2}\b/);
          if (yMatch) year = parseInt(yMatch[0], 10);
        } else if (currentTag === "JO" || currentTag === "JF" || currentTag === "JA" || currentTag === "T2") {
          journal = val;
        } else if (currentTag === "DO" || currentTag === "DI") {
          doi = val.replace(/^https?:\/\/doi\.org\//i, "");
        }
      } else if (currentTag) {
        // Multi-line field continuation
        if (currentTag === "TI" || currentTag === "T1") {
          title += " " + line;
        } else if (currentTag === "AB" || currentTag === "N2") {
          abstract += " " + line;
        }
      }
    }

    if (title) {
      records.push({
        id: `ris-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`,
        title,
        abstract: abstract || "No abstract provided in RIS record.",
        authors: authors.length > 0 ? authors : ["Unknown Author"],
        year: year || 2024,
        journal,
        doi,
        decision: "pending",
      });
    }
  }

  return records;
}

/**
 * Universal File Parser supporting CSV, TSV, RIS, BibTeX, and JSON files.
 */
export function parseUniversalFile(content: string, fileName?: string): Partial<ScreeningCandidate>[] {
  const trimmed = content.trim();
  if (!trimmed) return [];

  const lowerName = (fileName || "").toLowerCase();

  // 1. JSON Format
  if (
    lowerName.endsWith(".json") ||
    trimmed.startsWith("[") ||
    (trimmed.startsWith("{") && (trimmed.includes('"title"') || trimmed.includes('"papers"')))
  ) {
    try {
      const data = JSON.parse(trimmed);
      const list = Array.isArray(data)
        ? data
        : data.papers || data.items || data.results || data.data || [];
      if (Array.isArray(list) && list.length > 0) {
        return list
          .filter((item) => item && (item.title || item.Title || item.name))
          .map((item: any, idx: number) => ({
            id: item.id || `json-${Date.now()}-${idx}`,
            title: item.title || item.Title || item.name || "Untitled",
            abstract:
              item.abstract ||
              item.Abstract ||
              item.summary ||
              item.description ||
              "No abstract provided.",
            authors: Array.isArray(item.authors || item.Authors)
              ? item.authors || item.Authors
              : typeof (item.authors || item.author) === "string"
              ? (item.authors || item.author)
                  .split(/[,;]/)
                  .map((a: string) => a.trim())
                  .filter(Boolean)
              : ["Unknown Author"],
            year:
              typeof item.year === "number"
                ? item.year
                : parseInt(item.year || item.date || "2024", 10) || 2024,
            journal: item.journal || item.Journal || item.source || "",
            doi: (item.doi || item.DOI || "").replace(/^https?:\/\/doi\.org\//i, ""),
            decision: "pending" as const,
          }));
      }
    } catch {
      // Fall through to other format parsers
    }
  }

  // 2. BibTeX Format
  if (
    lowerName.endsWith(".bib") ||
    trimmed.includes("@article") ||
    trimmed.includes("@inproceedings") ||
    trimmed.includes("@book") ||
    trimmed.includes("@misc")
  ) {
    const bibResults = parseBibtexText(trimmed);
    if (bibResults.length > 0) return bibResults;
  }

  // 3. RIS Format
  if (
    lowerName.endsWith(".ris") ||
    trimmed.includes("TY  -") ||
    trimmed.includes("ER  -") ||
    trimmed.includes("TI  -")
  ) {
    const risResults = parseRisText(trimmed);
    if (risResults.length > 0) return risResults;
  }

  // 4. CSV / TSV Format
  const delimiter =
    lowerName.endsWith(".tsv") || (!trimmed.includes(",") && trimmed.includes("\t")) ? "\t" : ",";
  const rows = parseCsvRows(trimmed, delimiter);

  if (rows.length >= 2) {
    const headerRow = rows[0].map((h) => h.toLowerCase().replace(/[^a-z0-9]/g, ""));
    const titleIdx = headerRow.findIndex(
      (h) => h.includes("title") || h === "ti" || h.includes("name") || h.includes("headline")
    );
    const abstractIdx = headerRow.findIndex(
      (h) =>
        h.includes("abstract") ||
        h === "ab" ||
        h.includes("desc") ||
        h.includes("summary") ||
        h.includes("notes")
    );
    const authorsIdx = headerRow.findIndex(
      (h) => h.includes("author") || h === "au" || h.includes("creator")
    );
    const yearIdx = headerRow.findIndex(
      (h) => h.includes("year") || h === "py" || h.includes("date") || h.includes("pubyear")
    );
    const journalIdx = headerRow.findIndex(
      (h) =>
        !h.includes("year") &&
        !h.includes("date") &&
        (h.includes("journal") ||
          h.includes("source") ||
          h.includes("venue") ||
          h === "jo" ||
          h.includes("publisher") ||
          h === "publication")
    );
    const doiIdx = headerRow.findIndex(
      (h) => h.includes("doi") || h.includes("url") || h.includes("link")
    );

    if (titleIdx !== -1) {
      const records: Partial<ScreeningCandidate>[] = [];
      for (let i = 1; i < rows.length; i++) {
        const row = rows[i];
        const title = row[titleIdx]?.trim();
        if (!title) continue;

        const rawAbstract = abstractIdx !== -1 ? row[abstractIdx]?.trim() : "";
        const rawAuthors = authorsIdx !== -1 ? row[authorsIdx]?.trim() : "";
        const authors = rawAuthors.includes(";")
          ? rawAuthors.split(";").map((a) => a.trim()).filter(Boolean)
          : rawAuthors.includes(" and ")
          ? rawAuthors.split(/\s+and\s+/i).map((a) => a.trim()).filter(Boolean)
          : rawAuthors.includes("|")
          ? rawAuthors.split("|").map((a) => a.trim()).filter(Boolean)
          : rawAuthors
          ? [rawAuthors.trim()]
          : ["Unknown Author"];
        const rawYear = yearIdx !== -1 ? row[yearIdx]?.trim() : "";
        const yearMatch = rawYear?.match(/\b(19|20)\d{2}\b/);
        const year = yearMatch ? parseInt(yearMatch[0], 10) : 2024;
        const journal = journalIdx !== -1 ? row[journalIdx]?.trim() : "";
        const doi = doiIdx !== -1 ? row[doiIdx]?.trim() : "";

        records.push({
          id: `csv-${Date.now()}-${i}`,
          title,
          abstract: rawAbstract || "No abstract provided in tabular file.",
          authors: authors.length > 0 ? authors : ["Unknown Author"],
          year,
          journal,
          doi: doi.replace(/^https?:\/\/doi\.org\//i, ""),
          decision: "pending",
        });
      }
      if (records.length > 0) return records;
    }
  }

  // 5. Fallback: Line-by-line title records
  const lines = trimmed
    .split(/\r?\n/)
    .map((l) => l.trim())
    .filter((l) => l.length > 10);
  if (lines.length > 0) {
    return lines.slice(0, 150).map((line, idx) => ({
      id: `txt-${Date.now()}-${idx}`,
      title: line,
      abstract: "Plain title imported from text list.",
      authors: ["Unknown Author"],
      year: 2024,
      decision: "pending" as const,
    }));
  }

  return [];
}

/**
 * Benchmark Datasets for immediate screening demonstrations across disciplines
 */
export const BENCHMARK_SCREENING_DATASETS = [
  {
    id: "crispr",
    name: "CRISPR-Cas Therapeutics & In Vivo Delivery",
    category: "Biomedicine",
    totalCount: 30,
    papers: [
      {
        title: "In vivo delivery of CRISPR-Cas9 ribonucleoproteins for therapeutic genome editing in genetic disorders",
        abstract: "CRISPR-Cas9 gene editing has revolutionized molecular medicine, but effective and non-toxic delivery across physiological barriers remains a central barrier. In this systematic appraisal, we evaluate lipid nanoparticles (LNPs), engineered virus-like particles (eVLPs), and adeno-associated virus (AAV) vectors in murine and non-human primate disease models. LNPs demonstrated 88% editing efficiency in hepatocytes with minimal off-target cleavage.",
        authors: ["Doudna, J. A.", "Charpentier, E.", "Liu, D. R."],
        year: 2023,
        journal: "Nature Biotechnology",
        doi: "10.1038/s41587-023-01740-x",
      },
      {
        title: "Clinical efficacy and safety of exagamglogene autotemcel for transfusion-dependent beta-thalassemia",
        abstract: "Beta-thalassemia is caused by mutations in the HBB gene, leading to deficient hemoglobin production. We conducted an international trial using autologous CD34+ hematopoietic stem and progenitor cells edited with CRISPR-Cas9 at the erythroid-specific enhancer of BCL11A. Patients achieved transfusion independence with robust fetal hemoglobin expression.",
        authors: ["Frangoul, H.", "Locatelli, F.", "Sharma, A."],
        year: 2024,
        journal: "New England Journal of Medicine",
        doi: "10.1056/NEJMoa2305590",
      },
      {
        title: "A survey of general machine learning architectures for corporate financial fraud detection",
        abstract: "Fraud detection in multinational corporations requires predictive classifiers that can analyze continuous transaction streams. We evaluate random forests, extreme gradient boosting (XGBoost), and multilayer perceptrons across a real-world European banking dataset.",
        authors: ["Smith, J.", "Zhang, W.", "Mueller, K."],
        year: 2022,
        journal: "Journal of Financial Computing",
        doi: "10.1016/j.jfc.2022.100450",
      },
      {
        title: "Off-target assessment and high-fidelity Cas9 variants for precision clinical translation",
        abstract: "Genome-wide off-target cleavage presents significant oncogenic risks in clinical genome editing. We systematically profile high-fidelity Cas9 engineering strategies including SpCas9-HF1, eSpCas9, and evoCas9 using GUIDE-seq and CIRCLE-seq deep sequencing assays.",
        authors: ["Joung, J. K.", "Kleinstiver, B. P.", "Pattanayak, V."],
        year: 2023,
        journal: "Cell Stem Cell",
        doi: "10.1016/j.stem.2023.04.008",
      },
      {
        title: "Soil microbial carbon dynamics under Mediterranean conservation tillage",
        abstract: "Soil organic matter mineralization depends on tillage intensity and crop residue incorporation. We sampled 48 agricultural plots over three consecutive growing seasons in southern Spain to quantify microbial biomass carbon.",
        authors: ["Hernandez, M.", "Garcia, P.", "Lopez, A."],
        year: 2021,
        journal: "Agriculture, Ecosystems & Environment",
        doi: "10.1016/j.agee.2021.107452",
      },
    ],
  },
  {
    id: "llm_reasoning",
    name: "Large Language Models & Formal Reasoning",
    category: "AI & Computer Science",
    totalCount: 25,
    papers: [
      {
        title: "Chain-of-thought prompting elicits reasoning in large language models",
        abstract: "We explore how generating a chain of thought—a series of intermediate reasoning steps—significantly improves the ability of large language models to perform complex reasoning. Empirical evaluations across GSM8K, SVAMP, and BIG-bench show notable gains over standard prompting.",
        authors: ["Wei, J.", "Wang, X.", "Schuurmans, D.", "Bosma, M."],
        year: 2022,
        journal: "NeurIPS",
        doi: "10.48550/arXiv.2201.11903",
      },
      {
        title: "Constitutional AI: A self-improvement approach to harmlessness and honesty",
        abstract: "As AI systems scale, RLHF requires extensive human red-teaming. We propose Constitutional AI, where the model critiques and refines its own responses using a concise set of principles, producing aligned and robust conversational assistants.",
        authors: ["Bai, Y.", "Kadavath, S.", "Kundu, S.", "Askell, A."],
        year: 2023,
        journal: "Anthropic Research",
        doi: "10.48550/arXiv.2212.08073",
      },
      {
        title: "Clinical management of acute ischemic stroke in elderly patients",
        abstract: "Thrombolysis with tissue plasminogen activator remains standard of care within 4.5 hours of ischemic stroke onset. We review endovascular thrombectomy outcomes in octogenarian cohorts across tertiary neurology centers.",
        authors: ["Gomez, R.", "Nakamura, H.", "Taylor, E."],
        year: 2021,
        journal: "The Lancet Neurology",
        doi: "10.1016/S1474-4422(21)00112-9",
      },
      {
        title: "Self-Consistency Improves Chain of Thought Reasoning in Language Models",
        abstract: "Reasoning problems typically suffer from diversity of thought paths. We introduce self-consistency decoding that samples multiple diverse reasoning paths and selects the most consistent answer by marginalizing over reasoning paths.",
        authors: ["Wang, X.", "Wei, J.", "Schuurmans, D.", "Le, Q."],
        year: 2023,
        journal: "ICLR",
        doi: "10.48550/arXiv.2203.11171",
      },
    ],
  },
  {
    id: "microbiome",
    name: "Microbiome-Gut-Brain Axis & Neurodegeneration",
    category: "Neuroscience",
    totalCount: 28,
    papers: [
      {
        title: "Short-chain fatty acids modulate microglial maturation and mitigate amyloid-beta neurotoxicity",
        abstract: "The intestinal microbiota exerts systemic influences on central nervous system immune homeostasis via bacterial metabolites. Here we demonstrate that acetate and butyrate administration modulates microglial activation profiles and reduces plaque burden in murine models of Alzheimer's disease.",
        authors: ["Erny, D.", "Dokalis, N.", "Prinz, M."],
        year: 2023,
        journal: "Immunity",
        doi: "10.1016/j.immuni.2023.02.004",
      },
      {
        title: "Gut microbiota regulates motor deficits and neuroinflammation in a model of Parkinson's disease",
        abstract: "Parkinson's disease pathology is characterized by aggregation of alpha-synuclein and gastrointestinal motor abnormalities. Colonization of germ-free mice with microbiota from Parkinson's patients accelerates motor impairments and neuroinflammation compared to controls.",
        authors: ["Sampson, T. R.", "Debelius, J. W.", "Mazmanian, S. K."],
        year: 2022,
        journal: "Cell",
        doi: "10.1016/j.cell.2016.11.018",
      },
      {
        title: "Photovoltaic power forecasting using bidirectional long short-term memory networks",
        abstract: "Solar power generation intermittency causes grid stability risks. We develop a bi-directional LSTM model with weather clustering to forecast hourly output across 12 distributed solar farms.",
        authors: ["Li, Y.", "He, K.", "Wang, Z."],
        year: 2021,
        journal: "Applied Energy",
        doi: "10.1016/j.apenergy.2021.117180",
      },
    ],
  },
  {
    id: "battery_materials",
    name: "Solid-State Battery Electrolytes & Interfaces",
    category: "Materials Science",
    totalCount: 22,
    papers: [
      {
        title: "Interfacial engineering of sulfide-based solid electrolytes for dendrite-free lithium metal batteries",
        abstract: "All-solid-state lithium batteries offer enhanced safety and energy density. However, dendrite growth and interfacial chemical instability between sulfide electrolytes and lithium anodes cause rapid capacity degradation. We design an ultrathin organic-inorganic hybrid interlayer.",
        authors: ["Janek, J.", "Zeier, W. G.", "Sun, X."],
        year: 2024,
        journal: "Nature Energy",
        doi: "10.1038/s41560-023-01389-2",
      },
      {
        title: "High-entropy oxide cathode materials with exceptional structural stability at elevated voltages",
        abstract: "Transition metal dissolution and oxygen evolution at voltages exceeding 4.4V limit lithium-ion battery lifespans. We synthesize entropy-stabilized rocksalt oxide cathode systems demonstrating >92% capacity retention after 500 cycles.",
        authors: ["Goodenough, J. B.", "Ceder, G.", "Manthiram, A."],
        year: 2023,
        journal: "Advanced Materials",
        doi: "10.1002/adma.202301048",
      },
      {
        title: "Algorithmic pricing collusions in high-frequency online retail platforms",
        abstract: "Dynamic pricing algorithms operating in e-commerce markets can learn supra-competitive tacit collusion. We analyze simulated multi-agent reinforcement learning price competition under asymmetric cost structures.",
        authors: ["Calvano, E.", "Calzolari, G.", "Pastorello, S."],
        year: 2020,
        journal: "American Economic Review",
        doi: "10.1257/aer.20190623",
      },
    ],
  },
];
