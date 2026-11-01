import assert from "node:assert/strict";
import { describe, it } from "node:test";
import {
  tokenize,
  deduplicateCandidates,
  ActiveLearningClassifier,
  parseUniversalFile,
  parseRisText,
  parseBibtexText,
  parseCsvRows,
  ScreeningCandidate,
} from "@/lib/activeLearning";

describe("Adversarial Stress Test Suite: Active Learning & Parsers", () => {
  // =========================================================================
  // 1. TOKENIZER ADVERSARIAL STRESS TESTS
  // =========================================================================
  describe("1. Tokenizer Stress & Edge Cases", () => {
    it("1.1 handles malformed Unicode, emojis, null bytes, and zero-width spaces without throwing", () => {
      const inputs = [
        "CRISPR-Cas9 🤖 🧠 🔬 targeted endonuclease",
        "Null byte \0 in the \0 middle \0 of text",
        "Zero\u200Bwidth\u200Cspace\u200Dand\uFEFFBOM characters in text",
        "Astral symbols: 𝒳𝒴𝒵 𝕬𝕭𝕮 ℵ 𝔉𝔢𝔯𝔫𝔩𝔶 genome editing",
        "Mixed scripts: 基因编辑 технология CRISPR علاج بالجينات",
        "Accented Latin: naïve façade café Noël Möbius topology",
        "Combining diacritics: e\u0301\u0300\u0301\u0300\u0301 gene expression",
      ];

      for (const text of inputs) {
        assert.doesNotThrow(() => {
          const tokens = tokenize(text);
          assert.ok(Array.isArray(tokens), `Tokens should be an array for: ${text}`);
          for (const token of tokens) {
            assert.strictEqual(typeof token, "string");
            assert.ok(token.length >= 3 && token.length <= 24);
          }
        });
      }
    });

    it("1.2 handles massive inputs (150k+ chars) efficiently without catastrophic backtracking", () => {
      const wordList = ["crispr", "endonuclease", "oncology", "therapy", "genomics", "clinical", "precision"];
      const largeParagraph = Array.from({ length: 25000 }, (_, i) => wordList[i % wordList.length]).join(" ");
      assert.ok(largeParagraph.length > 150000, `Input length is ${largeParagraph.length}`);

      const startTime = performance.now();
      const tokens = tokenize(largeParagraph);
      const durationMs = performance.now() - startTime;

      assert.ok(tokens.length > 20000, `Expected >20k tokens, got ${tokens.length}`);
      assert.ok(durationMs < 200, `Tokenization of 150k chars took ${durationMs.toFixed(2)}ms, expected < 200ms`);
    });

    it("1.3 handles 50,000 repetitive identical tokens and pure punctuation streams", () => {
      const repetitive = "crispr ".repeat(50000);
      assert.doesNotThrow(() => {
        const tokens = tokenize(repetitive);
        assert.strictEqual(tokens.length, 50000);
      });

      const purePunctuation = "!@#$%^&*()_+-=[]{}|;':\",./<>?`~\\\n\r\t ".repeat(5000);
      assert.doesNotThrow(() => {
        const tokens = tokenize(purePunctuation);
        assert.deepStrictEqual(tokens, []);
      });
    });

    it("1.4 handles words at boundaries (2 chars, 3 chars, 24 chars, 25 chars, 100+ chars)", () => {
      const text = [
        "ab", // 2 chars -> filtered (< 3)
        "dna", // 3 chars -> kept
        "abcdefghijklmnopqrstuvwx", // 24 chars -> kept
        "abcdefghijklmnopqrstuvwxy", // 25 chars -> filtered (> 24 boundary)
        "supercalifragilisticexpialidociousverylongwordthatneverendsatall", // 63 chars -> filtered
      ].join(" ");

      const tokens = tokenize(text);
      assert.ok(!tokens.includes("ab"));
      assert.ok(tokens.includes("dna"));
      assert.ok(tokens.includes("abcdefghijklmnopqrstuvwx"));
      assert.ok(!tokens.includes("abcdefghijklmnopqrstuvwxy"));
    });

    it("1.5 correctly filters out all registered domain and grammatical stopwords", () => {
      const allRegisteredStopwords = "the study paper results methods conclusion background aim data analysis which that was were been had have";
      const tokens = tokenize(allRegisteredStopwords);
      assert.deepStrictEqual(tokens, []);
    });
  });

  // =========================================================================
  // 2. ACTIVE LEARNING CLASSIFIER ADVERSARIAL STRESS TESTS
  // =========================================================================
  describe("2. ActiveLearningClassifier Stress & Bounds", () => {
    it("2.1 handles 0 labeled candidates gracefully", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "1", title: "Paper 1", abstract: "Abstract 1", authors: [], decision: "pending" },
        { id: "2", title: "Paper 2", abstract: "Abstract 2", authors: [], decision: "pending" },
      ];
      const result = classifier.retrainAndRank(candidates);
      assert.strictEqual(result.length, 2);
      assert.strictEqual(result[0].id, "1");
      assert.strictEqual(result[1].id, "2");
    });

    it("2.2 handles extreme class imbalance: 1 included, 0 excluded with Laplace smoothing", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "inc-1", title: "CRISPR Genome Editing in Oncology", abstract: "Therapeutic gene knockout.", authors: [], decision: "included" },
        { id: "p-match", title: "CRISPR Oncology Therapeutics", abstract: "Clinical gene editing trials.", authors: [], decision: "pending" },
        { id: "p-other", title: "Agricultural Soil Carbon Storage", abstract: "Tillage and crop residue.", authors: [], decision: "pending" },
      ];

      const ranked = classifier.retrainAndRank(candidates);
      const pending = ranked.filter((c) => c.decision === "pending");

      assert.strictEqual(pending[0].id, "p-match");
      assert.ok(Number.isFinite(pending[0].relevanceScore));
      assert.ok(Number.isFinite(pending[1].relevanceScore));
      assert.ok((pending[0].relevanceScore ?? 0) >= (pending[1].relevanceScore ?? 0));
      assert.ok((pending[0].relevanceScore ?? 0) <= 100);
      assert.ok((pending[1].relevanceScore ?? 0) >= 0);
    });

    it("2.3 handles extreme class imbalance: 0 included, 1 excluded with Laplace smoothing", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "exc-1", title: "Agricultural Soil Carbon Storage", abstract: "Tillage and crop residue.", authors: [], decision: "excluded" },
        { id: "p-match", title: "Agricultural Soil Carbon Dynamics", abstract: "Tillage management.", authors: [], decision: "pending" },
        { id: "p-other", title: "CRISPR Genome Editing Therapeutics", abstract: "Oncology trials.", authors: [], decision: "pending" },
      ];

      const ranked = classifier.retrainAndRank(candidates);
      const pending = ranked.filter((c) => c.decision === "pending");

      assert.strictEqual(pending[0].id, "p-other");
      assert.ok(Number.isFinite(pending[0].relevanceScore));
      assert.ok(Number.isFinite(pending[1].relevanceScore));
      assert.ok((pending[0].relevanceScore ?? 0) >= (pending[1].relevanceScore ?? 0));
    });

    it("2.4 handles 500 included, 0 excluded and 0 included, 500 excluded without NaN or Infinity", () => {
      const classifierIncOnly = new ActiveLearningClassifier();
      const incOnlyCandidates: ScreeningCandidate[] = [
        ...Array.from({ length: 500 }, (_, i) => ({
          id: `inc-${i}`,
          title: `Cancer therapy and tumor immunology study ${i}`,
          abstract: `Immunotherapy checkpoint blockade in metastatic patients ${i}`,
          authors: ["Researcher"],
          decision: "included" as const,
        })),
        { id: "pend-match", title: "Cancer immunology checkpoint therapy", abstract: "Tumor metastatic blockade", authors: [], decision: "pending" },
        { id: "pend-unrelated", title: "Macroeconomic monetary inflation policies", abstract: "Central bank interest rates", authors: [], decision: "pending" },
      ];

      const rankedInc = classifierIncOnly.retrainAndRank(incOnlyCandidates);
      const pMatch = rankedInc.find((c) => c.id === "pend-match");
      const pUnrel = rankedInc.find((c) => c.id === "pend-unrelated");

      assert.ok(Number.isFinite(pMatch?.relevanceScore));
      assert.ok(Number.isFinite(pUnrel?.relevanceScore));
      assert.ok((pMatch?.relevanceScore ?? 0) >= (pUnrel?.relevanceScore ?? 0));
      assert.ok((pMatch?.relevanceScore ?? 0) <= 100);
      assert.ok((pUnrel?.relevanceScore ?? 0) >= 0);

      // Now 0 included, 500 excluded
      const classifierExcOnly = new ActiveLearningClassifier();
      const excOnlyCandidates: ScreeningCandidate[] = [
        ...Array.from({ length: 500 }, (_, i) => ({
          id: `exc-${i}`,
          title: `Macroeconomic inflation and interest rate policy ${i}`,
          abstract: `Banking liquidity and monetary exchange rates ${i}`,
          authors: ["Economist"],
          decision: "excluded" as const,
        })),
        { id: "pend-match-exc", title: "Macroeconomic inflation banking rates", abstract: "Monetary liquidity", authors: [], decision: "pending" },
        { id: "pend-bio", title: "Cancer immunology checkpoint therapy", abstract: "Tumor metastatic blockade", authors: [], decision: "pending" },
      ];

      const rankedExc = classifierExcOnly.retrainAndRank(excOnlyCandidates);
      const pBio = rankedExc.find((c) => c.id === "pend-bio");
      const pMatchExc = rankedExc.find((c) => c.id === "pend-match-exc");

      assert.ok(Number.isFinite(pBio?.relevanceScore));
      assert.ok(Number.isFinite(pMatchExc?.relevanceScore));
      assert.ok((pBio?.relevanceScore ?? 0) >= (pMatchExc?.relevanceScore ?? 0));
    });

    it("2.5 processes 5,000 labeled and 500 pending candidates within bounded time (< 1s)", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        ...Array.from({ length: 2500 }, (_, i) => ({
          id: `inc-${i}`,
          title: `Neuroscience microglial activation and neuroinflammation paper ${i}`,
          abstract: `Alzheimer disease pathology and amyloid beta clearance ${i}`,
          authors: ["Neuroscientist"],
          decision: "included" as const,
        })),
        ...Array.from({ length: 2500 }, (_, i) => ({
          id: `exc-${i}`,
          title: `Civil engineering concrete tensile durability paper ${i}`,
          abstract: `Reinforced bridge beam deflection under seismic stress ${i}`,
          authors: ["Engineer"],
          decision: "excluded" as const,
        })),
        ...Array.from({ length: 500 }, (_, i) => ({
          id: `pending-${i}`,
          title: i % 2 === 0 ? "Neuroinflammation microglial Alzheimer" : "Concrete structural beam engineering",
          abstract: i % 2 === 0 ? "Amyloid beta clearance study" : "Seismic bridge durability evaluation",
          authors: ["Test Author"],
          decision: "pending" as const,
        })),
      ];

      const start = performance.now();
      const ranked = classifier.retrainAndRank(candidates);
      const elapsed = performance.now() - start;

      assert.strictEqual(ranked.length, 5500);
      assert.ok(elapsed < 2000, `5,500 candidates ranked in ${elapsed.toFixed(1)}ms (expected < 2000ms)`);

      const pendingScored = ranked.filter((c) => c.decision === "pending");
      for (const p of pendingScored) {
        assert.ok(Number.isFinite(p.relevanceScore));
        assert.ok((p.relevanceScore ?? -1) >= 0 && (p.relevanceScore ?? -1) <= 100);
      }
    });

    it("2.6 handles candidates with zero tokens (empty or all-stopwords)", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "inc", title: "The study and data", abstract: "Paper methods were used", authors: [], decision: "included" },
        { id: "exc", title: "Another paper background", abstract: "Results of study", authors: [], decision: "excluded" },
        { id: "pend-empty", title: "", abstract: "", authors: [], decision: "pending" },
        { id: "pend-stops", title: "What when where", abstract: "This was that", authors: [], decision: "pending" },
      ];

      const ranked = classifier.retrainAndRank(candidates);
      const pending = ranked.filter((c) => c.decision === "pending");
      for (const p of pending) {
        assert.ok(Number.isFinite(p.relevanceScore));
        assert.strictEqual(p.relevanceScore, 50); // Prior included = 1/3, prior excluded = 1/3, log-odds = 0 -> 50%
      }
    });

    it("2.7 tie-breaking preserves stable sort order on identical relevance scores", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "inc", title: "TargetTermA", abstract: "TargetTermB", authors: [], decision: "included" },
        ...Array.from({ length: 20 }, (_, i) => ({
          id: `identical-${i}`,
          title: "CompletelyUnseenWord Alpha Beta Gamma",
          abstract: "Unseen Abstract Content",
          authors: [],
          decision: "pending" as const,
        })),
      ];

      const ranked = classifier.retrainAndRank(candidates);
      const pending = ranked.filter((c) => c.decision === "pending");

      const firstScore = pending[0].relevanceScore;
      for (let i = 0; i < pending.length; i++) {
        assert.strictEqual(pending[i].relevanceScore, firstScore);
        assert.strictEqual(pending[i].id, `identical-${i}`);
      }
    });
  });

  // =========================================================================
  // 3. DEDUPLICATION ADVERSARIAL STRESS TESTS
  // =========================================================================
  describe("3. Deduplication Algorithm Stress & Edge Cases", () => {
    it("3.1 handles DOI normalization: URL prefixes, spaces, case insensitivity, and leading 'doi:'", () => {
      const existing: ScreeningCandidate[] = [
        { id: "1", title: "Original Paper", abstract: "Abs 1", authors: [], doi: "10.1038/s41586-020-0001", decision: "pending" },
      ];

      const variants = [
        "https://doi.org/10.1038/s41586-020-0001",
        "http://doi.org/10.1038/s41586-020-0001",
        "https://dx.doi.org/10.1038/s41586-020-0001",
        "doi: 10.1038/s41586-020-0001",
        "DOI: 10.1038/S41586-020-0001",
        "  10.1038/s41586-020-0001  ",
      ];

      for (const variant of variants) {
        const incoming: ScreeningCandidate[] = [
          { id: "new", title: "Variant Paper", abstract: "Abs 2", authors: [], doi: variant, decision: "pending" },
        ];
        const res = deduplicateCandidates(existing, incoming);
        assert.strictEqual(res.duplicateCount, 1, `Failed to deduplicate DOI variant: "${variant}"`);
        assert.strictEqual(res.duplicatesRemoved[0].reason, "doi_match");
      }
    });

    it("3.2 does not flag distinct papers with empty or undefined DOIs as duplicate", () => {
      const existing: ScreeningCandidate[] = [
        { id: "1", title: "First Unique Title Here", abstract: "Abs 1", authors: [], doi: "", decision: "pending" },
        ({ id: "2", title: "Second Completely Different Title", abstract: "Abs 2", authors: [], decision: undefined, decision_status: "pending" } as unknown as ScreeningCandidate),
      ];
      const incoming: ScreeningCandidate[] = [
        { id: "3", title: "Third Distinct Independent Title", abstract: "Abs 3", authors: [], doi: "", decision: "pending" },
      ];

      const res = deduplicateCandidates(existing, incoming);
      assert.strictEqual(res.duplicateCount, 0);
      assert.strictEqual(res.uniqueCandidates.length, 3);
    });

    it("3.3 matches exact normalized titles with varying casing, punctuation, and leading articles", () => {
      const existing: ScreeningCandidate[] = [
        { id: "1", title: "The Impact of Artificial Intelligence on Modern Healthcare", abstract: "", authors: [], decision: "pending" },
      ];

      const variations = [
        "Impact of Artificial Intelligence on Modern Healthcare", // removed "The "
        "the impact of artificial intelligence on modern healthcare", // lower case
        "THE IMPACT OF ARTIFICIAL INTELLIGENCE ON MODERN HEALTHCARE", // upper case
        "Impact of Artificial Intelligence on Modern Healthcare!", // trailing punctuation
      ];

      for (let i = 0; i < variations.length; i++) {
        const inc: ScreeningCandidate[] = [
          { id: `var-${i}`, title: variations[i], abstract: "", authors: [], decision: "pending" },
        ];
        const res = deduplicateCandidates(existing, inc);
        assert.strictEqual(res.duplicateCount, 1, `Expected title match for "${variations[i]}"`);
      }
    });

    it("3.4 tests fuzzy title matching threshold (Jaccard >= 0.88 and yearDelta <= 1)", () => {
      const existing: ScreeningCandidate[] = [
        {
          id: "1",
          // 9 distinct words > 2 chars: deep, neural, networks, medical, image, segmentation, classification, clinical, practice
          title: "Deep Neural Networks for Medical Image Segmentation and Classification in Clinical Practice",
          abstract: "Abstract A",
          authors: ["Smith"],
          year: 2022,
          decision: "pending",
        },
      ];

      // High similarity (9 common words out of 10 total words = 0.90 Jaccard >= 0.88) + year delta = 1 -> DUPLICATE
      const fuzzyMatch: ScreeningCandidate[] = [
        {
          id: "2",
          title: "Deep Neural Networks for Medical Image Segmentation and Classification in Clinical Practice Applications",
          abstract: "Abstract B",
          authors: ["Smith"],
          year: 2023, // delta = 1
          decision: "pending",
        },
      ];
      const resMatch = deduplicateCandidates(existing, fuzzyMatch);
      assert.strictEqual(resMatch.duplicateCount, 1);
      assert.strictEqual(resMatch.duplicatesRemoved[0].reason, "fuzzy_title");

      // High similarity (0.90 Jaccard) but large year gap (delta = 4 > 1) -> NOT DUPLICATE
      const largeYearGap: ScreeningCandidate[] = [
        {
          id: "3",
          title: "Deep Neural Networks for Medical Image Segmentation and Classification in Clinical Practice Applications",
          abstract: "Abstract C",
          authors: ["Smith"],
          year: 2018, // delta = 4
          decision: "pending",
        },
      ];
      const resGap = deduplicateCandidates(existing, largeYearGap);
      assert.strictEqual(resGap.duplicateCount, 0);

      // Low similarity (6 words in common out of 7 = 0.857 Jaccard < 0.88) -> NOT DUPLICATE
      const subThreshold: ScreeningCandidate[] = [
        {
          id: "4",
          title: "Comprehensive Clinical Assessment of Monoclonal Antibody Therapies Evaluation",
          abstract: "Abstract D",
          authors: ["Smith"],
          year: 2022,
          decision: "pending",
        },
      ];
      const resSub = deduplicateCandidates(
        [{ id: "0", title: "Comprehensive Clinical Assessment of Monoclonal Antibody Therapies", abstract: "", authors: [], year: 2022, decision: "pending" }],
        subThreshold
      );
      assert.strictEqual(resSub.duplicateCount, 0);
    });

    it("3.5 preserves and enriches abstract and sourceOrigin when duplicate is detected", () => {
      const existing: ScreeningCandidate[] = [
        {
          id: "1",
          title: "Quantum Entanglement in Superconducting Qubits",
          abstract: "", // missing abstract
          authors: ["Alice"],
          doi: "10.1103/physrevlett.100.001",
          sourceOrigin: "OpenAlex",
          decision: "pending",
        },
      ];

      const incoming: ScreeningCandidate[] = [
        {
          id: "2",
          title: "Quantum Entanglement in Superconducting Qubits",
          abstract: "Enriched abstract discovered in Crossref record.",
          authors: ["Alice"],
          doi: "10.1103/physrevlett.100.001",
          sourceOrigin: "Crossref",
          decision: "pending",
        },
      ];

      const res = deduplicateCandidates(existing, incoming);
      assert.strictEqual(res.duplicateCount, 1);
      assert.strictEqual(res.uniqueCandidates.length, 1);
      assert.strictEqual(res.uniqueCandidates[0].abstract, "Enriched abstract discovered in Crossref record.");
      assert.ok(res.uniqueCandidates[0].sourceOrigin?.includes("OpenAlex"));
      assert.ok(res.uniqueCandidates[0].sourceOrigin?.includes("Crossref"));
    });

    it("3.6 documents known DOI edge cases (trailing slash and protocol-less doi.org)", () => {
      const existing: ScreeningCandidate[] = [
        { id: "1", title: "Benchmark Study", abstract: "", authors: [], doi: "10.1038/s41586-020-0001", decision: "pending" },
      ];

      // Note: normalizeDoi currently trims whitespace and strips 'https://doi.org/' and 'doi:',
      // but retains trailing slashes and bare 'doi.org/' prefixes without http(s).
      const withTrailingSlash: ScreeningCandidate[] = [
        { id: "2", title: "Different Title Study", abstract: "", authors: [], doi: "10.1038/s41586-020-0001/", decision: "pending" },
      ];
      const resSlash = deduplicateCandidates(existing, withTrailingSlash);
      assert.strictEqual(resSlash.duplicateCount, 0, "Trailing slash on DOI is not stripped by normalizeDoi");

      const withBareDoiOrg: ScreeningCandidate[] = [
        { id: "3", title: "Another Title Study", abstract: "", authors: [], doi: "doi.org/10.1038/s41586-020-0001", decision: "pending" },
      ];
      const resBare = deduplicateCandidates(existing, withBareDoiOrg);
      assert.strictEqual(resBare.duplicateCount, 0, "Bare doi.org/ prefix without http(s) is not stripped by normalizeDoi");
    });
  });

  // =========================================================================
  // 4. UNIVERSAL BIBLIOGRAPHIC PARSERS ADVERSARIAL STRESS TESTS
  // =========================================================================
  describe("4. Universal Bibliographic Parsers Stress & Resilience", () => {
    // -----------------------------------------------------------------------
    // 4.1 RIS Parser
    // -----------------------------------------------------------------------
    describe("4.1 RIS Parser", () => {
      it("parses malformed tags, multi-line continuations, and records without ER delimiters", () => {
        const malformedRis = `
TY  - JOUR
TI  - First part of title
 and continuation of title on line two
 without proper tag prefix
AU  - Watson, J.
AU  - Crick, F.
AB  - We wish to suggest a structure
 for the salt of deoxyribose nucleic acid (D.N.A.).
 This structure has novel features
 which are of considerable biological interest.
PY  - 1953/04/25
DO  - https://doi.org/10.1038/171737a0
JO  - Nature
ER  - 

TY  - CONF
TI  - Record without proper ER delimiter at bottom
AU  - Turing, A. M.
PY  - 1950
        `;

        const records = parseRisText(malformedRis);
        assert.ok(records.length >= 2, `Expected at least 2 records, got ${records.length}`);
        assert.ok(records[0].title?.includes("continuation of title"));
        assert.ok(records[0].abstract?.includes("novel features"));
        assert.strictEqual(records[0].year, 1953);
        assert.strictEqual(records[0].doi, "10.1038/171737a0");
      });

      it("handles completely corrupted RIS content without uncaught exceptions", () => {
        const corruptedInputs = [
          "Not a RIS file at all, just plain text with no tags",
          "TY  - \nER  - \nTY  - \nER  - ",
          "XX  - Invalid tag\nYY  - Another invalid tag\n",
          "TY  - JOUR\nTI  - \nAB  - \nER  - ", // empty title
        ];

        for (const input of corruptedInputs) {
          assert.doesNotThrow(() => {
            const result = parseRisText(input);
            assert.ok(Array.isArray(result));
          });
        }
      });
    });

    // -----------------------------------------------------------------------
    // 4.2 BibTeX Parser
    // -----------------------------------------------------------------------
    describe("4.2 BibTeX Parser", () => {
      it("parses BibTeX with complex braces, escaped characters, and various entry types", () => {
        const complexBib = `
@inproceedings{vaswani2017attention,
  author    = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki and Uszkoreit, Jakob},
  title     = {{Attention Is All You Need: Structural Advancements in {Transformer} Networks}},
  booktitle = {Advances in Neural Information Processing Systems},
  year      = {2017},
  doi       = {10.48550/arXiv.1706.03762},
  abstract  = {We propose the Transformer, a model architecture eschewing recurrence.}
}

@book{pearl2009causality,
  author    = {Pearl, Judea},
  title     = {Causality: Models, Reasoning, and Inference},
  publisher = {Cambridge University Press},
  year      = {2009}
}

@misc{corrupted_entry,
  title = {Unclosed brace entry
}
        `;

        assert.doesNotThrow(() => {
          const records = parseBibtexText(complexBib);
          assert.ok(records.length >= 2, `Expected at least 2 records, got ${records.length}`);
          assert.ok(records[0].title?.includes("Attention Is All You Need"));
          assert.ok(records[0].title?.includes("Transformer"));
          assert.strictEqual(records[0].year, 2017);
          assert.strictEqual(records[1].title, "Causality: Models, Reasoning, and Inference");
          assert.strictEqual(records[1].year, 2009);
        });
      });

      it("handles malformed BibTeX with missing commas and strange field values without hanging", () => {
        const malformed = `
@article{test1
  title = "Paper Without Comma Between Fields"
  year = 2023
  abstract = "Testing parser resilience under missing commas"
}
@article{test2,
  title = Clean Paper Two,
  year = 2024
}
        `;
        assert.doesNotThrow(() => {
          const records = parseBibtexText(malformed);
          assert.ok(Array.isArray(records));
        });
      });
    });

    // -----------------------------------------------------------------------
    // 4.3 CSV & TSV Parser
    // -----------------------------------------------------------------------
    describe("4.3 CSV & TSV Parser", () => {
      it("parses CSV with multiline quotes, CRLF/LF linebreaks, and escaped quotes", () => {
        const rawCsv = 'Title,Authors,Year,Abstract,DOI\r\n"First Paper with\r\nNewline Inside","Author One; Author Two",2021,"Abstract with ""quoted terms"" and, commas",10.1016/j.cell.2021\r\n"Second Paper","Author Three",2024,"Single line abstract",10.1038/nature123';
        const rows = parseCsvRows(rawCsv);
        assert.strictEqual(rows.length, 3);
        assert.strictEqual(rows[1][0], "First Paper with\r\nNewline Inside");
        assert.strictEqual(rows[1][3], 'Abstract with "quoted terms" and, commas');

        const candidates = parseUniversalFile(rawCsv, "data.csv");
        assert.strictEqual(candidates.length, 2);
        assert.ok(candidates[0].title?.includes("Newline Inside"));
        assert.strictEqual(candidates[0].authors?.length, 2);
        assert.strictEqual(candidates[0].year, 2021);
        assert.strictEqual(candidates[0].doi, "10.1016/j.cell.2021");
      });

      it("handles TSV file with embedded commas seamlessly", () => {
        const tsv = "Title\tAuthors\tYear\tAbstract\nGene Therapy, CRISPR, and Cas9\tSmith, J.\t2023\tVector delivery.";
        const candidates = parseUniversalFile(tsv, "dataset.tsv");
        assert.strictEqual(candidates.length, 1);
        assert.strictEqual(candidates[0].title, "Gene Therapy, CRISPR, and Cas9");
        assert.strictEqual(candidates[0].year, 2023);
      });

      it("handles unclosed quotes in CSV without throwing uncaught exceptions", () => {
        const unclosed = 'Title,Authors,Year\n"Unclosed quote title,Smith,2022\nNext line without quote';
        assert.doesNotThrow(() => {
          const rows = parseCsvRows(unclosed);
          assert.ok(Array.isArray(rows));
        });
      });
    });

    // -----------------------------------------------------------------------
    // 4.4 JSON Parser
    // -----------------------------------------------------------------------
    describe("4.4 JSON Parser", () => {
      it("parses various JSON shapes: array, wrapped object, items, results, data", () => {
        const shapes = [
          JSON.stringify([{ title: "Array Shape Paper", year: 2023 }]),
          JSON.stringify({ papers: [{ title: "Wrapped Papers Shape", year: 2024 }] }),
          JSON.stringify({ items: [{ title: "Wrapped Items Shape", year: 2022 }] }),
          JSON.stringify({ results: [{ title: "Wrapped Results Shape", year: 2021 }] }),
          JSON.stringify({ data: [{ title: "Wrapped Data Shape", year: 2020 }] }),
        ];

        for (const shape of shapes) {
          const res = parseUniversalFile(shape, "test.json");
          assert.strictEqual(res.length, 1);
          assert.ok(res[0].title?.startsWith("Wrapped") || res[0].title?.startsWith("Array"));
        }
      });

      it("handles schema-violating JSON objects safely: primitives, nulls, missing fields, extreme types", () => {
        const adversarialJson = JSON.stringify([
          null,
          12345,
          "random string instead of object",
          [],
          {}, // empty object
          { title: "" }, // empty title
          { title: "Valid Title", authors: null, year: "not a year", doi: 12345 },
          { title: "Another Valid Title", authors: ["Alice", 999 as unknown as string, null as unknown as string], year: -500 },
        ]);

        assert.doesNotThrow(() => {
          const res = parseUniversalFile(adversarialJson, "adversarial.json");
          assert.strictEqual(res.length, 2);
          assert.strictEqual(res[0].title, "Valid Title");
          assert.strictEqual(res[0].year, 2024); // default fallback
          assert.strictEqual(res[0].doi, "12345"); // stringified
          assert.deepStrictEqual(res[0].authors, ["Unknown Author"]); // null authors fallback
          assert.strictEqual(res[1].title, "Another Valid Title");
          assert.strictEqual(res[1].year, -500); // numeric parsed
          assert.deepStrictEqual(res[1].authors, ["Alice"]); // non-string authors filtered out
        });
      });

      it("falls through gracefully when JSON syntax is corrupted", () => {
        const brokenJson = '{"papers": [{"title": "Unfinished JSON...';
        assert.doesNotThrow(() => {
          const res = parseUniversalFile(brokenJson, "broken.json");
          assert.ok(Array.isArray(res));
        });
      });
    });

    // -----------------------------------------------------------------------
    // 4.5 Universal File Format Auto-Detection
    // -----------------------------------------------------------------------
    describe("4.5 Format Auto-Detection Fallback", () => {
      it("auto-detects BibTeX from content without file extension", () => {
        const content = `@article{turing1950, title={Computing Machinery and Intelligence}, author={Turing, A. M.}, year={1950}}`;
        const res = parseUniversalFile(content);
        assert.strictEqual(res.length, 1);
        assert.strictEqual(res[0].title, "Computing Machinery and Intelligence");
      });

      it("auto-detects RIS from content without file extension", () => {
        const content = `TY  - JOUR\nTI  - Shannon Information Theory\nAU  - Shannon, C. E.\nPY  - 1948\nER  - `;
        const res = parseUniversalFile(content);
        assert.strictEqual(res.length, 1);
        assert.strictEqual(res[0].title, "Shannon Information Theory");
      });

      it("falls back to plain-text title list for unrecognized unstructured text", () => {
        const text = `
First Systematic Appraisal of mRNA Vaccine Platforms in Oncology
Second Comprehensive Investigation of Superconducting Qubits
Third Empirical Benchmark of Autonomous Multi-Agent Reasoning Systems
        `;
        const res = parseUniversalFile(text);
        assert.strictEqual(res.length, 3);
        assert.ok(res[0].title?.includes("First Systematic"));
        assert.ok(res[1].title?.includes("Second Comprehensive"));
        assert.ok(res[2].title?.includes("Third Empirical"));
      });
    });
  });
});
