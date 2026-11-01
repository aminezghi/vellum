import { describe, it } from "node:test";
import { expect } from "./harness";
import { parseInputFilesToCandidates, normalizeDoi } from "@/lib/bibliographicParser";

describe("Batch Downloader Input Parser (bibliographicParser.ts)", () => {
  it("normalizes DOI strings cleanly", () => {
    expect(normalizeDoi("https://doi.org/10.1057/s41270-026-00470-6")).toBe("10.1057/s41270-026-00470-6");
    expect(normalizeDoi("http://dx.doi.org/10.1016/S2214-109X(23)00000-0")).toBe("10.1016/s2214-109x(23)00000-0");
    expect(normalizeDoi("doi: 10.1038/s41586-023-00000-0.")).toBe("10.1038/s41586-023-00000-0");
    expect(normalizeDoi("not a doi")).toBe(null);
  });

  it("parses BibTeX without creating fake items from metadata lines (W1.bib bug fix)", () => {
    // Simulating a multi-line WoS / Scopus BibTeX file with 30+ lines of metadata
    const bibContent = `
@article{ WOS:001429373700001,
Author = {Romanyi, Reinpeter and Cygu, Steve Biko and Kiragga, Agnes and Odero, Henry Owoko and Ng'etich, Silas and Kigen, Bartilol and Chemweno, Ernest and Musinguzi, Denis and Masaba, Denis and Ouma, Walter and Kusemererwa, Sheila and Nsubuga, Rebecca and Kampiire, Lillian and Mugisha, Emmanuel and Ssetaala, Annet and Nielsen, Peter and Kiwanuka, Noah},
Title = {Big data in consumer behavior research: a systematic review of data sources, analytical methods, and research questions},
Journal = {JOURNAL OF MARKETING ANALYTICS},
Year = {2026},
Volume = {14},
Number = {1},
Pages = {45-62},
DOI = {10.1057/s41270-026-00470-6},
Abstract = {Consumer behavior analytics leverages high-volume digital traces to predict market shifts.}
}

@article{ WOS:000999999999999,
Author = {Vaswani, Ashish and Shazeer, Noam},
Title = {Attention Is All You Need},
Journal = {NeurIPS},
Year = {2017},
DOI = {10.48550/arXiv.1706.03762}
}

@misc{ EntryWithoutDoi,
Author = {Anonymous},
Title = {A Working Paper With No DOI},
Year = {2024}
}
`;

    const { candidates, summary } = parseInputFilesToCandidates(bibContent, "W1.bib");

    // Must NOT be 30+ items; must only be 2 items with valid DOIs!
    expect(candidates.length).toBe(2);
    expect(candidates[0].doi).toBe("10.1057/s41270-026-00470-6");
    expect(candidates[0].title).toBe(
      "Big data in consumer behavior research: a systematic review of data sources, analytical methods, and research questions"
    );
    expect(candidates[0].authors).toContain("Romanyi");
    expect(candidates[0].year).toBe(2026);
    expect(candidates[0].journal).toBe("JOURNAL OF MARKETING ANALYTICS");

    expect(candidates[1].doi).toBe("10.48550/arxiv.1706.03762");
    expect(candidates[1].title).toBe("Attention Is All You Need");

    // Summary must accurately record the skipped entry
    expect(summary.validWithDoi).toBe(2);
    expect(summary.skippedWithoutDoi).toBe(1);
    expect(summary.duplicatesRemoved).toBe(0);
  });

  it("parses CSV files and extracts only rows containing DOIs", () => {
    const csvContent = `Title,Authors,Year,DOI
"Paper One","Author A",2023,10.1038/s41586-023-00000-0
"Paper Two Without DOI","Author B",2022,
"Paper Three","Author C",2021,https://doi.org/10.1016/S2214-109X(23)00000-0`;

    const { candidates, summary } = parseInputFilesToCandidates(csvContent, "papers.csv");

    expect(candidates.length).toBe(2);
    expect(candidates[0].doi).toBe("10.1038/s41586-023-00000-0");
    expect(candidates[1].doi).toBe("10.1016/s2214-109x(23)00000-0");
    expect(summary.validWithDoi).toBe(2);
    expect(summary.skippedWithoutDoi).toBe(1);
  });

  it("strictly filters plain text input and deduplicates identical DOIs", () => {
    const rawText = `
Random notes from research meeting:
Look up 10.1057/s41270-026-00470-6 for marketing analytics.
Also check out https://doi.org/10.1057/s41270-026-00470-6 (duplicate).
Non-DOI line with more than five characters that should never be enqueued.
Another DOI: 10.1038/s41586-023-00000-0.
`;

    const { candidates, summary } = parseInputFilesToCandidates(rawText, "pasted.txt");

    expect(candidates.length).toBe(2);
    expect(candidates[0].doi).toBe("10.1057/s41270-026-00470-6");
    expect(candidates[1].doi).toBe("10.1038/s41586-023-00000-0");
    expect(summary.duplicatesRemoved).toBe(1);
  });
});
