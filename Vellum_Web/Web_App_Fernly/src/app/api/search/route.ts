import { NextRequest, NextResponse } from "next/server";

export interface AcademicPaperResult {
  id: string;
  title: string;
  authors: string[];
  year: number;
  venue: string;
  doi?: string;
  citationCount: number;
  isOpenAccess: boolean;
  pdfUrl?: string;
  abstract?: string;
  source: "OpenAlex" | "arXiv" | "Semantic Scholar" | "Crossref" | "PubMed";
  topics?: string[];
}

// Helper to reconstruct abstract from OpenAlex inverted index
function reconstructAbstract(invertedIndex?: Record<string, number[]>): string | undefined {
  if (!invertedIndex || Object.keys(invertedIndex).length === 0) return undefined;
  const positions: [number, string][] = [];
  for (const [word, indices] of Object.entries(invertedIndex)) {
    for (const idx of indices) {
      positions.push([idx, word]);
    }
  }
  positions.sort((a, b) => a[0] - b[0]);
  return positions.map((p) => p[1]).join(" ");
}

// Parse arXiv Atom XML using regex without heavy dependencies
function parseArxivXml(xml: string): AcademicPaperResult[] {
  const results: AcademicPaperResult[] = [];
  const entries = xml.split("<entry>");
  
  for (let i = 1; i < entries.length; i++) {
    const entry = entries[i].split("</entry>")[0];
    
    const idMatch = entry.match(/<id>([^<]+)<\/id>/);
    const titleMatch = entry.match(/<title>([^<]+)<\/title>/);
    const summaryMatch = entry.match(/<summary>([^<]+)<\/summary>/);
    const publishedMatch = entry.match(/<published>(\d{4})-[^<]+<\/published>/);
    const pdfLinkMatch = entry.match(/<link[^>]+title=["']pdf["'][^>]+href=["']([^"']+)["']/i) ||
                         entry.match(/<link[^>]+href=["'](https?:\/\/arxiv\.org\/pdf\/[^"']+)["']/i);
    const doiMatch = entry.match(/<arxiv:doi[^>]*>([^<]+)<\/arxiv:doi>/i);
    
    // Extract authors
    const authorMatches = [...entry.matchAll(/<author>\s*<name>([^<]+)<\/name>/g)];
    const authors = authorMatches.map((m) => m[1].trim()).filter(Boolean);

    const rawTitle = titleMatch ? titleMatch[1].replace(/\s+/g, " ").trim() : "Untitled arXiv Paper";
    const rawSummary = summaryMatch ? summaryMatch[1].replace(/\s+/g, " ").trim() : undefined;
    const year = publishedMatch ? parseInt(publishedMatch[1], 10) : new Date().getFullYear();
    const arxivUrl = idMatch ? idMatch[1].trim() : "";
    const arxivId = arxivUrl.split("/abs/").pop() || `arxiv-${Date.now()}-${i}`;
    let pdfUrl = pdfLinkMatch ? pdfLinkMatch[1].trim() : undefined;
    if (!pdfUrl && arxivId) {
      pdfUrl = `https://arxiv.org/pdf/${arxivId}.pdf`;
    }

    results.push({
      id: `arxiv-${arxivId}`,
      title: rawTitle,
      authors: authors.length > 0 ? authors : ["arXiv Contributor"],
      year,
      venue: "arXiv Preprint",
      doi: doiMatch ? doiMatch[1].trim() : undefined,
      citationCount: 0,
      isOpenAccess: true,
      pdfUrl,
      abstract: rawSummary,
      source: "arXiv",
      topics: ["Preprint", "Open Access"],
    });
  }

  return results;
}

// Clean and normalize title for deduplication
function normalizeTitle(t: string): string {
  return t.toLowerCase().replace(/[^a-z0-9]/g, "");
}

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const rawQuery = searchParams.get("q") || "";
  const sourcesParam = searchParams.get("sources") || "openalex";
  const activeSources = sourcesParam.toLowerCase().split(",").map((s) => s.trim());
  const openAccessOnly = searchParams.get("oa") === "true";
  const startYear = searchParams.get("fromYear") || "2015";
  const endYear = searchParams.get("toYear") || new Date().getFullYear().toString();
  const sortBy = searchParams.get("sortBy") || "relevance";
  const field = searchParams.get("field") || "all"; // all, title, author, doi

  // Advanced keywords & boolean combinations
  const mustInclude = searchParams.get("mustInclude") || "";
  const anyInclude = searchParams.get("anyInclude") || "";
  const mustExclude = searchParams.get("mustExclude") || "";
  const exactPhrase = searchParams.get("exactPhrase") || "";
  const authorQuery = searchParams.get("author") || "";
  const doiQuery = searchParams.get("doi") || "";

  // User Custom Tokens (kept client-side, sent via headers or query)
  const tokenOpenAlex = req.headers.get("x-token-openalex") || searchParams.get("tokenOpenAlex") || "";
  const tokenSemanticScholar = req.headers.get("x-token-semanticscholar") || searchParams.get("tokenSemanticScholar") || "";
  const tokenCrossref = req.headers.get("x-token-crossref") || searchParams.get("tokenCrossref") || "";

  // Compose synthesized query string
  let queryTerms: string[] = [];
  if (doiQuery.trim()) {
    queryTerms.push(doiQuery.trim());
  }
  if (exactPhrase.trim()) {
    queryTerms.push(`"${exactPhrase.trim()}"`);
  }
  if (rawQuery.trim()) {
    queryTerms.push(rawQuery.trim());
  }
  if (mustInclude.trim()) {
    queryTerms.push(mustInclude.trim());
  }
  if (anyInclude.trim()) {
    queryTerms.push(anyInclude.trim());
  }

  let finalQuery = queryTerms.join(" ").trim();
  if (authorQuery.trim() && field === "all") {
    finalQuery = `${finalQuery} ${authorQuery.trim()}`.trim();
  }

  if (!finalQuery) {
    return NextResponse.json({ results: [], total: 0, query: "" });
  }

  const results: AcademicPaperResult[] = [];
  const errors: string[] = [];

  // ==========================================
  // SOURCE 1: OPENALEX (Primary 250M+ Index)
  // ==========================================
  if (activeSources.includes("openalex") || activeSources.includes("all")) {
    try {
      const filterParts: string[] = [`publication_year:${startYear}-${endYear}`];
      if (openAccessOnly) filterParts.push("is_oa:true");
      if (field === "title") {
        filterParts.push(`title.search:${encodeURIComponent(finalQuery)}`);
      }
      if (authorQuery.trim()) {
        filterParts.push(`raw_author_name.search:${encodeURIComponent(authorQuery.trim())}`);
      }
      if (doiQuery.trim()) {
        const cleanDoi = doiQuery.replace(/^https?:\/\/doi\.org\//i, "");
        filterParts.push(`doi:https://doi.org/${cleanDoi}`);
      }

      const openAlexUrl = new URL("https://api.openalex.org/works");
      if (field !== "title") {
        openAlexUrl.searchParams.set("search", finalQuery);
      }
      openAlexUrl.searchParams.set("filter", filterParts.join(","));
      openAlexUrl.searchParams.set("per_page", "15");

      if (tokenOpenAlex.trim()) {
        if (tokenOpenAlex.includes("@")) {
          // OpenAlex polite pool via mailto
          openAlexUrl.searchParams.set("mailto", tokenOpenAlex.trim());
        } else {
          openAlexUrl.searchParams.set("api_key", tokenOpenAlex.trim());
        }
      }

      if (sortBy === "citations") {
        openAlexUrl.searchParams.set("sort", "cited_by_count:desc");
      } else if (sortBy === "date") {
        openAlexUrl.searchParams.set("sort", "publication_date:desc");
      }

      const oaRes = await fetch(openAlexUrl.toString(), {
        headers: {
          "User-Agent": `Vellum-Research-Web/1.0 (mailto:${tokenOpenAlex.includes("@") ? tokenOpenAlex : "vellum@research.local"})`,
        },
        next: { revalidate: 1800 },
      });

      if (oaRes.ok) {
        const data = await oaRes.json();
        for (const w of data.results || []) {
          const authors = (w.authorships || [])
            .map((a: any) => a.author?.display_name)
            .filter(Boolean);

          const venue =
            w.primary_location?.source?.display_name ||
            w.host_venue?.display_name ||
            "Academic Publication";

          const pdfUrl =
            w.open_access?.oa_url ||
            w.primary_location?.pdf_url ||
            (w.best_oa_location?.pdf_url ?? undefined);

          const abstract = reconstructAbstract(w.abstract_inverted_index);
          const topics = (w.topics || w.concepts || []).slice(0, 3).map((c: any) => c.display_name);
          const doiClean = w.doi ? w.doi.replace(/^https?:\/\/doi\.org\//i, "") : undefined;

          results.push({
            id: w.id || `openalex-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
            title: w.title || "Untitled Research Article",
            authors: authors.length > 0 ? authors : ["Anonymous / Collaboration"],
            year: w.publication_year || parseInt(startYear, 10),
            venue,
            doi: doiClean,
            citationCount: w.cited_by_count || 0,
            isOpenAccess: !!w.is_oa,
            pdfUrl: pdfUrl || undefined,
            abstract,
            source: "OpenAlex",
            topics,
          });
        }
      }
    } catch (err: any) {
      console.error("OpenAlex source error:", err);
      errors.push(`OpenAlex: ${err.message}`);
    }
  }

  // ==========================================
  // SOURCE 2: arXiv (Preprints & Exact Science)
  // ==========================================
  if (activeSources.includes("arxiv") || activeSources.includes("all")) {
    try {
      let arxivQuery = "";
      if (field === "title") {
        arxivQuery = `ti:${encodeURIComponent(finalQuery)}`;
      } else if (authorQuery.trim()) {
        arxivQuery = `au:${encodeURIComponent(authorQuery.trim())} AND all:${encodeURIComponent(finalQuery)}`;
      } else {
        arxivQuery = `all:${encodeURIComponent(finalQuery)}`;
      }

      if (mustExclude.trim()) {
        const excludeParts = mustExclude.split(/\s+/).map((e) => `ANDNOT all:${encodeURIComponent(e)}`).join(" ");
        arxivQuery = `${arxivQuery} ${excludeParts}`;
      }

      const arxivUrl = `https://export.arxiv.org/api/query?search_query=${arxivQuery}&start=0&max_results=10&sortBy=relevance`;
      const arxivRes = await fetch(arxivUrl, {
        headers: { "User-Agent": "Vellum-Research-Web/1.0" },
        next: { revalidate: 3600 },
      });

      if (arxivRes.ok) {
        const xmlText = await arxivRes.text();
        const arxivPapers = parseArxivXml(xmlText);
        results.push(...arxivPapers);
      }
    } catch (err: any) {
      console.error("arXiv source error:", err);
      errors.push(`arXiv: ${err.message}`);
    }
  }

  // ==========================================
  // SOURCE 3: Semantic Scholar Graph API
  // ==========================================
  if (activeSources.includes("semanticscholar") || activeSources.includes("all")) {
    try {
      const s2Url = new URL("https://api.semanticscholar.org/graph/v1/paper/search");
      s2Url.searchParams.set("query", finalQuery);
      s2Url.searchParams.set("limit", "10");
      s2Url.searchParams.set(
        "fields",
        "paperId,title,abstract,authors,year,venue,citationCount,isOpenAccess,openAccessPdf,externalIds"
      );
      if (startYear && endYear) {
        s2Url.searchParams.set("year", `${startYear}-${endYear}`);
      }

      const s2Headers: Record<string, string> = {
        "User-Agent": "Vellum-Research-Web/1.0",
      };
      if (tokenSemanticScholar.trim()) {
        s2Headers["x-api-key"] = tokenSemanticScholar.trim();
      }

      const s2Res = await fetch(s2Url.toString(), {
        headers: s2Headers,
        next: { revalidate: 1800 },
      });

      if (s2Res.ok) {
        const s2Data = await s2Res.json();
        for (const p of s2Data.data || []) {
          const authors = (p.authors || []).map((a: any) => a.name).filter(Boolean);
          const doi = p.externalIds?.DOI || undefined;
          results.push({
            id: `s2-${p.paperId}`,
            title: p.title || "Untitled Paper",
            authors: authors.length > 0 ? authors : ["Semantic Scholar Indexed"],
            year: p.year || parseInt(startYear, 10),
            venue: p.venue || "Peer-Reviewed",
            doi,
            citationCount: p.citationCount || 0,
            isOpenAccess: !!p.isOpenAccess,
            pdfUrl: p.openAccessPdf?.url || undefined,
            abstract: p.abstract || undefined,
            source: "Semantic Scholar",
            topics: ["Semantic Graph", "Citation Network"],
          });
        }
      }
    } catch (err: any) {
      console.error("Semantic Scholar source error:", err);
      errors.push(`Semantic Scholar: ${err.message}`);
    }
  }

  // ==========================================
  // SOURCE 4: Crossref REST API
  // ==========================================
  if (activeSources.includes("crossref") || activeSources.includes("all")) {
    try {
      const crUrl = new URL("https://api.crossref.org/works");
      crUrl.searchParams.set("query", finalQuery);
      crUrl.searchParams.set("rows", "10");
      crUrl.searchParams.set("filter", `from-pub-date:${startYear}`);

      const crHeaders: Record<string, string> = {
        "User-Agent": `Vellum-Research-Web/1.0 (mailto:${tokenCrossref || "vellum@research.local"})`,
      };

      const crRes = await fetch(crUrl.toString(), {
        headers: crHeaders,
        next: { revalidate: 3600 },
      });

      if (crRes.ok) {
        const crData = await crRes.json();
        for (const item of crData.message?.items || []) {
          const authors = (item.author || []).map((a: any) => `${a.given || ""} ${a.family || ""}`.trim()).filter(Boolean);
          const title = item.title?.[0] || "Crossref Document";
          const year = item["published-print"]?.["date-parts"]?.[0]?.[0] ||
                       item["published-online"]?.["date-parts"]?.[0]?.[0] ||
                       item.created?.["date-parts"]?.[0]?.[0] ||
                       parseInt(startYear, 10);
          const venue = item["container-title"]?.[0] || item.publisher || "Crossref Publication";
          const doi = item.DOI;
          const pdfLink = item.link?.find((l: any) => l["content-type"] === "application/pdf")?.URL;

          results.push({
            id: `crossref-${item.DOI || Math.random().toString(36).substring(2, 6)}`,
            title,
            authors: authors.length > 0 ? authors : ["Crossref Publisher Index"],
            year,
            venue,
            doi,
            citationCount: item["is-referenced-by-count"] || 0,
            isOpenAccess: item.license && item.license.length > 0,
            pdfUrl: pdfLink || undefined,
            abstract: item.abstract ? item.abstract.replace(/<[^>]+>/g, "").trim() : undefined,
            source: "Crossref",
            topics: ["Publisher Direct", "DOI Registered"],
          });
        }
      }
    } catch (err: any) {
      console.error("Crossref source error:", err);
      errors.push(`Crossref: ${err.message}`);
    }
  }

  // ==========================================
  // Deduplication & Filtering
  // ==========================================
  const seenDois = new Set<string>();
  const seenTitles = new Set<string>();
  const deduplicatedResults: AcademicPaperResult[] = [];

  for (const paper of results) {
    if (paper.doi) {
      const cleanDoi = paper.doi.toLowerCase().trim();
      if (seenDois.has(cleanDoi)) continue;
      seenDois.add(cleanDoi);
    }

    const normTitle = normalizeTitle(paper.title);
    if (normTitle.length > 10) {
      if (seenTitles.has(normTitle)) continue;
      seenTitles.add(normTitle);
    }

    // Apply client-side exclude keyword filter if present
    if (mustExclude.trim()) {
      const excludeTerms = mustExclude.toLowerCase().split(/\s+/).filter(Boolean);
      const textToSearch = `${paper.title} ${paper.abstract || ""}`.toLowerCase();
      const hasExcluded = excludeTerms.some((term) => textToSearch.includes(term));
      if (hasExcluded) continue;
    }

    // Apply open access filter if requested
    if (openAccessOnly && !paper.isOpenAccess && !paper.pdfUrl) {
      continue;
    }

    deduplicatedResults.push(paper);
  }

  // Apply sorting
  if (sortBy === "citations") {
    deduplicatedResults.sort((a, b) => (b.citationCount || 0) - (a.citationCount || 0));
  } else if (sortBy === "date") {
    deduplicatedResults.sort((a, b) => (b.year || 0) - (a.year || 0));
  }

  return NextResponse.json({
    results: deduplicatedResults,
    total: deduplicatedResults.length,
    query: finalQuery,
    sourcesUsed: activeSources,
    errors: errors.length > 0 ? errors : undefined,
  });
}
