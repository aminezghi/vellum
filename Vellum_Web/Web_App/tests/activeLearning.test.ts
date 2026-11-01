import { describe, it, expect } from "./harness";
import {
  tokenize,
  deduplicateCandidates,
  ActiveLearningClassifier,
  ScreeningCandidate,
} from "@/lib/activeLearning";

describe("Active Learning Engine (activeLearning.ts)", () => {
  describe("tokenize()", () => {
    it("lowercases and filters common stop words", () => {
      const tokens = tokenize("The study presents a novel methods paper");
      expect(tokens).not.toContain("the");
      expect(tokens).not.toContain("study");
      expect(tokens).not.toContain("methods");
      expect(tokens).not.toContain("paper");
      expect(tokens).toContain("presents");
      expect(tokens).toContain("novel");
    });

    it("filters short tokens (< 3 chars) and preserves domain terms", () => {
      const tokens = tokenize("AI in DNA and RNA sequencing of CRISPR cas");
      expect(tokens).not.toContain("ai");
      expect(tokens).not.toContain("in");
      expect(tokens).toContain("dna");
      expect(tokens).toContain("rna");
      expect(tokens).toContain("sequencing");
      expect(tokens).toContain("crispr");
      expect(tokens).toContain("cas");
    });

    it("returns empty array for empty or whitespace text", () => {
      expect(tokenize("")).toEqual([]);
      expect(tokenize("   \n\t  ")).toEqual([]);
    });
  });

  describe("deduplicateCandidates()", () => {
    it("flags duplicate records with identical normalized DOIs", () => {
      const existing: ScreeningCandidate[] = [
        {
          id: "1",
          title: "Quantum Computing Advances",
          abstract: "Abstract 1",
          authors: ["Alice"],
          doi: "10.1038/s41586-020-0001",
          decision: "pending",
        },
      ];
      const incoming: ScreeningCandidate[] = [
        {
          id: "2",
          title: "Quantum Computing Advances (Preprint)",
          abstract: "Abstract 2",
          authors: ["Alice"],
          doi: "https://doi.org/10.1038/s41586-020-0001",
          decision: "pending",
        },
      ];
      const res = deduplicateCandidates(existing, incoming);
      expect(res.duplicateCount).toBe(1);
      expect(res.uniqueCandidates.length).toBe(1);
      expect(res.duplicatesRemoved[0].reason).toBe("doi_match");
    });

    it("flags duplicate records with identical normalized titles", () => {
      const existing: ScreeningCandidate[] = [
        {
          id: "1",
          title: "The Effects of Exercise on Cognitive Health",
          abstract: "Abstract A",
          authors: ["Bob"],
          decision: "pending",
        },
      ];
      const incoming: ScreeningCandidate[] = [
        {
          id: "2",
          title: "Effects of Exercise on Cognitive Health",
          abstract: "Abstract B",
          authors: ["Bob"],
          decision: "pending",
        },
      ];
      const res = deduplicateCandidates(existing, incoming);
      expect(res.duplicateCount).toBe(1);
      expect(res.duplicatesRemoved[0].reason).toBe("exact_title");
    });

    it("flags fuzzy title duplicates with Jaccard >= 0.88 and year delta <= 1", () => {
      const existing: ScreeningCandidate[] = [
        {
          id: "1",
          title: "Deep Neural Networks for Medical Image Segmentation and Classification",
          abstract: "Abstract",
          authors: ["Carol"],
          year: 2023,
          decision: "pending",
        },
      ];
      const incoming: ScreeningCandidate[] = [
        {
          id: "2",
          title: "Deep Neural Networks for Medical Image Segmentation and Classification Studies",
          abstract: "Abstract",
          authors: ["Carol"],
          year: 2024,
          decision: "pending",
        },
      ];
      const res = deduplicateCandidates(existing, incoming);
      expect(res.duplicateCount).toBe(1);
      expect(res.duplicatesRemoved[0].reason).toBe("fuzzy_title");
    });

    it("preserves distinct candidate references", () => {
      const existing: ScreeningCandidate[] = [
        { id: "1", title: "CRISPR Genome Editing", abstract: "A", authors: ["Dave"], decision: "pending" },
      ];
      const incoming: ScreeningCandidate[] = [
        { id: "2", title: "Solar Photovoltaic Efficiency", abstract: "B", authors: ["Eve"], decision: "pending" },
      ];
      const res = deduplicateCandidates(existing, incoming);
      expect(res.duplicateCount).toBe(0);
      expect(res.uniqueCandidates.length).toBe(2);
    });
  });

  describe("ActiveLearningClassifier", () => {
    it("returns candidates unchanged when no labeled data exists", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "1", title: "Paper 1", abstract: "Abstract 1", authors: [], decision: "pending" },
        { id: "2", title: "Paper 2", abstract: "Abstract 2", authors: [], decision: "pending" },
      ];
      const ranked = classifier.retrainAndRank(candidates);
      expect(ranked).toEqual(candidates);
    });

    it("actively prioritizes papers matching included features above excluded features", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        {
          id: "train-inc",
          title: "CRISPR Cas9 targeted endonuclease in human oncology therapeutics",
          abstract: "Gene editing treatment shows high efficacy in oncology trials.",
          authors: ["Author A"],
          decision: "included",
        },
        {
          id: "train-exc",
          title: "Econometric forecasting of stock market inflation and liquidity",
          abstract: "Macroeconomic asset pricing models under interest rate volatility.",
          authors: ["Author B"],
          decision: "excluded",
        },
        {
          id: "test-bio",
          title: "CRISPR endonuclease therapies for metastatic oncology",
          abstract: "Evaluating gene editing protocols in clinical oncology.",
          authors: ["Author C"],
          decision: "pending",
        },
        {
          id: "test-econ",
          title: "Monetary policy liquidity and macroeconomic inflation",
          abstract: "Asset pricing under banking interest rate pressures.",
          authors: ["Author D"],
          decision: "pending",
        },
      ];

      const ranked = classifier.retrainAndRank(candidates);
      const pendingRanked = ranked.filter((c) => c.decision === "pending");

      // The biological paper matching the included record must rank first with higher relevance
      expect(pendingRanked[0].id).toBe("test-bio");
      expect(pendingRanked[1].id).toBe("test-econ");
      expect(pendingRanked[0].relevanceScore).toBeGreaterThan(pendingRanked[1].relevanceScore || 0);
    });

    it("Laplace smoothing prevents -Infinity and sigmoid bounds score between 0 and 100", () => {
      const classifier = new ActiveLearningClassifier();
      const candidates: ScreeningCandidate[] = [
        { id: "inc", title: "SpecificUniqueTerm", abstract: "Foo", authors: [], decision: "included" },
        { id: "exc", title: "OtherUniqueTerm", abstract: "Bar", authors: [], decision: "excluded" },
        { id: "pend", title: "UnseenWordOne UnseenWordTwo", abstract: "Baz", authors: [], decision: "pending" },
      ];
      const ranked = classifier.retrainAndRank(candidates);
      const pend = ranked.find((c) => c.id === "pend");
      expect(pend?.relevanceScore).toBeDefined();
      expect(Number.isFinite(pend?.relevanceScore)).toBe(true);
      expect(pend!.relevanceScore!).toBeGreaterThanOrEqual(0);
      expect(pend!.relevanceScore!).toBeLessThanOrEqual(100);
    });
  });
});
