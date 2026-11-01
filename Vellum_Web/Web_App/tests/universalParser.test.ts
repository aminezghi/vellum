import { describe, it, expect } from "./harness";
import {
  parseUniversalFile,
  parseRisText,
  parseBibtexText,
  parseCsvRows,
} from "@/lib/activeLearning";

describe("Universal Bibliographic Parser (activeLearning.ts)", () => {
  describe("RIS Parsing", () => {
    it("parses standard RIS record correctly", () => {
      const ris = `
TY  - JOUR
TI  - Deep Learning for Systematic Reviews
AU  - van de Schoot, Rens
AU  - de Bruin, Jonathan
AB  - Active learning algorithms significantly accelerate title and abstract screening.
PY  - 2021
JO  - Nature Machine Intelligence
DO  - 10.1038/s42256-020-00287-7
ER  - 
      `;
      const results = parseRisText(ris);
      expect(results.length).toBe(1);
      expect(results[0].title).toBe("Deep Learning for Systematic Reviews");
      expect(results[0].authors).toEqual(["van de Schoot, Rens", "de Bruin, Jonathan"]);
      expect(results[0].year).toBe(2021);
      expect(results[0].journal).toBe("Nature Machine Intelligence");
      expect(results[0].doi).toBe("10.1038/s42256-020-00287-7");
    });

    it("handles multi-line title and abstract continuations in RIS", () => {
      const ris = `
TY  - JOUR
TI  - First line of long title
 and second line of long title
AB  - First paragraph of abstract.
 Second line of abstract continuation.
ER  - 
      `;
      const results = parseRisText(ris);
      expect(results[0].title).toBe("First line of long title and second line of long title");
      expect(results[0].abstract).toContain("Second line of abstract continuation");
    });
  });

  describe("BibTeX Parsing", () => {
    it("parses standard @article BibTeX entry", () => {
      const bib = `
@article{vaswani2017attention,
  title = {Attention Is All You Need},
  author = {Vaswani, Ashish and Shazeer, Noam and Parmar, Niki},
  journal = {Advances in Neural Information Processing Systems},
  year = {2017},
  doi = {10.48550/arXiv.1706.03762},
  abstract = {The dominant sequence transduction models are based on complex recurrent neural networks.}
}
      `;
      const results = parseBibtexText(bib);
      expect(results.length).toBe(1);
      expect(results[0].title).toBe("Attention Is All You Need");
      expect(results[0].authors).toEqual(["Vaswani, Ashish", "Shazeer, Noam", "Parmar, Niki"]);
      expect(results[0].year).toBe(2017);
      expect(results[0].doi).toBe("10.48550/arXiv.1706.03762");
    });
  });

  describe("CSV & TSV Parsing", () => {
    it("parses comma-separated values with quoted cells and commas", () => {
      const csv = `Title,Authors,Year,Abstract,DOI\n"Precision Oncology, A Review","Smith, J.; Doe, A.",2022,"Targeted kinase inhibitors, monoclonal antibodies.",10.1001/jama.2022.01`;
      const results = parseUniversalFile(csv, "dataset.csv");
      expect(results.length).toBe(1);
      expect(results[0].title).toBe("Precision Oncology, A Review");
      expect(results[0].authors).toEqual(["Smith, J.", "Doe, A."]);
      expect(results[0].year).toBe(2022);
      expect(results[0].doi).toBe("10.1001/jama.2022.01");
    });

    it("parses tab-separated values (.tsv)", () => {
      const tsv = "Title\tAuthors\tYear\tAbstract\nGene Therapy in Mice\tBrown, K.\t2023\tViral vectors.";
      const results = parseUniversalFile(tsv, "papers.tsv");
      expect(results.length).toBe(1);
      expect(results[0].title).toBe("Gene Therapy in Mice");
      expect(results[0].year).toBe(2023);
    });

    it("parses CSV rows via parseCsvRows with escaped quotes", () => {
      const raw = `a,b,"c ""quoted"" d"\n1,2,3`;
      const rows = parseCsvRows(raw);
      expect(rows.length).toBe(2);
      expect(rows[0][2]).toBe('c "quoted" d');
    });
  });

  describe("JSON Parsing", () => {
    it("parses JSON array of candidate objects", () => {
      const json = JSON.stringify([
        { title: "Paper Alpha", authors: ["Author 1"], year: 2023, abstract: "Abstract text" },
      ]);
      const results = parseUniversalFile(json, "export.json");
      expect(results.length).toBe(1);
      expect(results[0].title).toBe("Paper Alpha");
    });

    it("parses nested JSON wrapper ({ papers: [...] })", () => {
      const json = JSON.stringify({
        papers: [{ title: "Nested Paper", authors: "Alice, Bob", year: 2024 }],
      });
      const results = parseUniversalFile(json);
      expect(results.length).toBe(1);
      expect(results[0].title).toBe("Nested Paper");
      expect(results[0].authors).toEqual(["Alice", "Bob"]);
    });

    it("returns empty array for invalid or empty input", () => {
      expect(parseUniversalFile("")).toEqual([]);
      expect(parseUniversalFile("   ")).toEqual([]);
    });
  });
});
