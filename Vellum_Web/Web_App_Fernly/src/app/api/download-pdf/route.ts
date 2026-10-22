import { NextRequest, NextResponse } from "next/server";

const SCIHUB_MIRRORS = [
  "https://sci-hub.se/",
  "https://sci-hub.st/",
  "https://sci-hub.ru/",
];

const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

function isValidPdf(buffer: Uint8Array): boolean {
  if (buffer.length < 1500) return false;
  const header = String.fromCharCode(...buffer.slice(0, 1024));
  return header.includes("%PDF");
}

async function fetchPdfBuffer(url: string, timeoutMs = 8000): Promise<{ buf: Uint8Array; url: string } | null> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    let origin = "https://scholar.google.com/";
    try {
      origin = new URL(url).origin + "/";
    } catch {}
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "application/pdf,application/octet-stream,*/*;q=0.8",
        Referer: origin,
      },
      redirect: "follow",
    });
    if (res.ok) {
      const buf = new Uint8Array(await res.arrayBuffer());
      if (isValidPdf(buf)) {
        return { buf, url };
      }
    }
    return null;
  } catch {
    return null;
  } finally {
    clearTimeout(id);
  }
}

// ---------------------------------------------------------------------------
// Upstream payloads. Four registries are consulted in parallel and each has its
// own shape; only the fields this route reads are described.
// ---------------------------------------------------------------------------

interface CrossrefEnvelope {
  message?: {
    title?: string[];
    link?: { URL?: string }[];
  };
}

interface UnpaywallEnvelope {
  oa_locations?: { url_for_pdf?: string; url?: string }[];
}

interface SemanticScholarEnvelope {
  openAccessPdf?: { url?: string };
}

interface OpenAlexEnvelope {
  title?: string;
  display_name?: string;
  primary_location?: { pdf_url?: string };
  best_oa_location?: { pdf_url?: string };
  open_access?: { oa_url?: string };
}

async function fetchJsonWithTimeout<T>(url: string, timeoutMs = 5000): Promise<T | null> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: { "User-Agent": USER_AGENT },
    });
    if (res.ok) return (await res.json()) as T;
    return null;
  } catch {
    return null;
  } finally {
    clearTimeout(id);
  }
}

async function fetchHtmlWithTimeout(url: string, timeoutMs = 6000): Promise<{ html: string; finalUrl: string } | null> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const res = await fetch(url, {
      signal: controller.signal,
      headers: {
        "User-Agent": USER_AGENT,
        Accept: "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
      },
      redirect: "follow",
    });
    if (res.ok) {
      const html = await res.text();
      return { html, finalUrl: res.url || url };
    }
    return null;
  } catch {
    return null;
  } finally {
    clearTimeout(id);
  }
}

function extractPdfLinksFromHtml(html: string, baseUrl: string): string[] {
  const found: string[] = [];
  const addUrl = (raw: string) => {
    try {
      const u = new URL(raw.replace(/&amp;/g, "&"), baseUrl).toString();
      if (u.startsWith("http") && !found.includes(u)) found.push(u);
    } catch {}
  };

  // 1. <meta name="citation_pdf_url" content="...">
  const metaRegex = /<meta[^>]+(?:name|property)=["'](?:citation_pdf_url|bepress_citation_pdf_url|eprints\.document_url)["'][^>]+content=["']([^"']+)["']/gi;
  let m: RegExpExecArray | null;
  while ((m = metaRegex.exec(html)) !== null) {
    if (m[1]) addUrl(m[1]);
  }
  const metaRegexRev = /<meta[^>]+content=["']([^"']+)["'][^>]+(?:name|property)=["'](?:citation_pdf_url|bepress_citation_pdf_url|eprints\.document_url)["']/gi;
  while ((m = metaRegexRev.exec(html)) !== null) {
    if (m[1]) addUrl(m[1]);
  }

  // 2. Direct PDF / Download anchor tags (OJS, Detritus, Preprints, ScienceDirect, etc.)
  const anchorRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  while ((m = anchorRegex.exec(html)) !== null) {
    const href = (m[1] || "").trim();
    const text = (m[2] || "").replace(/<[^>]+>/g, " ").trim().toLowerCase();
    if (!href || href.startsWith("javascript:") || href.startsWith("#") || href.startsWith("mailto:")) continue;
    const hlow = href.toLowerCase();
    if (
      text === "pdf" ||
      text === "download" ||
      text.includes("download pdf") ||
      text.includes("full text pdf") ||
      text.includes("[pdf]") ||
      hlow.endsWith(".pdf") ||
      hlow.includes("/file/get?code=") ||
      hlow.includes("/file/download") ||
      hlow.includes("download_pub") ||
      hlow.includes("pdf.sciencedirectassets.com") ||
      hlow.includes("pdfft") ||
      hlow.includes("/article/download/")
    ) {
      addUrl(href);
    }
  }
  return found;
}

function extractScholarPdfLinks(html: string): string[] {
  const found: string[] = [];
  const anchorRegex = /<a[^>]+href=["']([^"']+)["'][^>]*>([\s\S]*?)<\/a>/gi;
  let m: RegExpExecArray | null;
  while ((m = anchorRegex.exec(html)) !== null) {
    const href = (m[1] || "").replace(/&amp;/g, "&").trim();
    const text = (m[2] || "").replace(/<[^>]+>/g, " ").trim().toLowerCase();
    if (!href.startsWith("http") || href.includes("scholar.google.") || href.includes("google.com/")) continue;
    const hlow = href.toLowerCase();
    if (
      text.includes("[pdf]") ||
      hlow.endsWith(".pdf") ||
      hlow.includes("download_pub") ||
      hlow.includes("/file/download") ||
      hlow.includes("/file/get?code=") ||
      hlow.includes("/pdf/")
    ) {
      if (!found.includes(href)) found.push(href);
    }
  }
  return found;
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const rawDoi = (body.doi || "").trim();
    const doi = rawDoi.toLowerCase().replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "");
    let title = (body.title || "document").trim();
    const initialPdfUrl = (body.pdfUrl || (rawDoi.startsWith("http") && !rawDoi.includes("doi.org/") ? rawDoi : "")).trim();

    const cleanTitle = title.replace(/[^\w\s-]/gi, "").slice(0, 50).trim();
    const filename = `${cleanTitle || "Paper"}.pdf`;

    // ── Tier 1: Immediate Direct OA URL Check ────────────────────────────────
    if (initialPdfUrl && initialPdfUrl.startsWith("http")) {
      const direct = await fetchPdfBuffer(initialPdfUrl, 8000);
      if (direct) {
        return new Response(Buffer.from(direct.buf), {
          status: 200,
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `inline; filename="${filename}"`,
            "X-Vellum-Resolved-Source": "Direct Open Access URL",
          },
        });
      }
    }

    if (!doi || !doi.startsWith("10.")) {
      return NextResponse.json(
        {
          success: false,
          message: "No DOI available for multi-tier repository lookup.",
          landingUrl: initialPdfUrl || undefined,
        },
        { status: 404 }
      );
    }

    // ── Tier 2: Build candidate URLs concurrently ───────────────────────────
    const candidateUrls: { url: string; source: string }[] = [];

    // Publisher direct routes
    if (doi.startsWith("10.1186/") || doi.startsWith("10.1007/")) {
      candidateUrls.push({
        url: `https://link.springer.com/content/pdf/${doi}.pdf`,
        source: "Springer / BMC Direct OA",
      });
    }
    if (doi.startsWith("10.1038/")) {
      const artId = doi.split("/").pop();
      candidateUrls.push({
        url: `https://www.nature.com/articles/${artId}.pdf`,
        source: "Nature Publishing Direct",
      });
    }
    if (doi.startsWith("10.48550/arxiv.")) {
      const arxivId = doi.split("arxiv.").pop();
      candidateUrls.push({
        url: `https://arxiv.org/pdf/${arxivId}.pdf`,
        source: "arXiv Preprints",
      });
    }

    // ── Fast Parallel Queries across Registries (Crossref, Unpaywall, Semantic Scholar, OpenAlex) ─
    const [crData, unpData, s2Data, oaData] = await Promise.all([
      fetchJsonWithTimeout<CrossrefEnvelope>(`https://api.crossref.org/works/${doi}`, 5000),
      fetchJsonWithTimeout<UnpaywallEnvelope>(`https://api.unpaywall.org/v2/${doi}?email=researcher@vellum.app`, 5000),
      fetchJsonWithTimeout<SemanticScholarEnvelope>(`https://api.semanticscholar.org/graph/v1/paper/DOI:${doi}?fields=openAccessPdf,title`, 5000),
      fetchJsonWithTimeout<OpenAlexEnvelope>(`https://api.openalex.org/works/https://doi.org/${doi}`, 5000),
    ]);

    if (crData?.message) {
      const crMsg = crData.message;
      if ((!title || title === "document") && Array.isArray(crMsg.title) && crMsg.title[0]) {
        title = String(crMsg.title[0]).replace(/<[^>]+>/g, "").trim();
      }
      if (Array.isArray(crMsg.link)) {
        for (const lk of crMsg.link) {
          const u = lk.URL;
          if (u && u.startsWith("http")) {
            candidateUrls.push({ url: u, source: "Crossref Full-Text" });
          }
        }
      }
    }

    if (unpData?.oa_locations) {
      for (const loc of unpData.oa_locations) {
        const u = loc.url_for_pdf || loc.url;
        if (u && u.startsWith("http")) candidateUrls.push({ url: u, source: "Unpaywall Registry" });
      }
    }

    if (s2Data?.openAccessPdf?.url) {
      candidateUrls.push({ url: s2Data.openAccessPdf.url, source: "Semantic Scholar API" });
    }

    if (oaData) {
      if ((!title || title === "document") && (oaData.title || oaData.display_name)) {
        title = oaData.title || oaData.display_name;
      }
      if (oaData.primary_location?.pdf_url) {
        candidateUrls.push({ url: oaData.primary_location.pdf_url, source: "OpenAlex Repository" });
      }
      if (oaData.best_oa_location?.pdf_url) {
        candidateUrls.push({ url: oaData.best_oa_location.pdf_url, source: "OpenAlex Best OA" });
      }
      if (oaData.open_access?.oa_url) {
        candidateUrls.push({ url: oaData.open_access.oa_url, source: "OpenAlex OA Gateway" });
      }
    }

    // Try all candidate OA URLs in parallel!
    if (candidateUrls.length > 0) {
      const fetchPromises = candidateUrls.slice(0, 8).map(async (cand) => {
        const result = await fetchPdfBuffer(cand.url, 8000);
        if (result) return { ...result, source: cand.source };
        return null;
      });

      const results = await Promise.all(fetchPromises);
      const successful = results.find((r) => r !== null);
      if (successful) {
        return new Response(Buffer.from(successful.buf), {
          status: 200,
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `inline; filename="${filename}"`,
            "X-Vellum-Resolved-Source": successful.source,
          },
        });
      }
    }

    // ── Tier 3: Publisher Landing Page (<meta name="citation_pdf_url"> & direct PDF links) + Google Scholar ──
    const scholarQueries = [
      `https://scholar.google.com/scholar?hl=en&q=${encodeURIComponent(doi)}`,
    ];
    if (title && title !== "document" && title.length > 8) {
      scholarQueries.push(`https://scholar.google.com/scholar?hl=en&q=${encodeURIComponent(title)}`);
    }

    const [landingPage, ...scholarPages] = await Promise.all([
      fetchHtmlWithTimeout(`https://doi.org/${doi}`, 6000),
      ...scholarQueries.map((sq) => fetchHtmlWithTimeout(sq, 6000)),
    ]);

    const discoveredUrls: { url: string; source: string }[] = [];
    if (landingPage) {
      for (const u of extractPdfLinksFromHtml(landingPage.html, landingPage.finalUrl)) {
        discoveredUrls.push({ url: u, source: "Publisher Direct" });
      }
    }
    for (const sp of scholarPages) {
      if (sp) {
        for (const u of extractScholarPdfLinks(sp.html)) {
          discoveredUrls.push({ url: u, source: "Google Scholar" });
        }
      }
    }

    if (discoveredUrls.length > 0) {
      const discResults = await Promise.all(
        discoveredUrls.slice(0, 6).map(async (cand) => {
          const result = await fetchPdfBuffer(cand.url, 8000);
          if (result) return { ...result, source: cand.source };
          return null;
        })
      );
      const discSuccess = discResults.find((r) => r !== null);
      if (discSuccess) {
        return new Response(Buffer.from(discSuccess.buf), {
          status: 200,
          headers: {
            "Content-Type": "application/pdf",
            "Content-Disposition": `inline; filename="${filename}"`,
            "X-Vellum-Resolved-Source": discSuccess.source,
          },
        });
      }
    }

    // ── Tier 4: Fast Sci-Hub Mirror Check (Parallel) ──────────────────────────
    const mirrorPromises = SCIHUB_MIRRORS.map(async (mirror) => {
      try {
        const shRes = await fetch(`${mirror}${doi}`, {
          headers: { "User-Agent": USER_AGENT },
          signal: AbortSignal.timeout(5000),
        });
        if (shRes.ok) {
          const text = await shRes.text();
          const match = text.match(/(?:src|href)=["']([^"']+\.pdf[^"']*)["']/i);
          if (match && match[1]) {
            let pdfUrl = match[1];
            if (pdfUrl.startsWith("//")) pdfUrl = "https:" + pdfUrl;
            else if (pdfUrl.startsWith("/")) pdfUrl = mirror.replace(/\/$/, "") + pdfUrl;

            const finalPdf = await fetchPdfBuffer(pdfUrl, 7000);
            if (finalPdf) return finalPdf;
          }
        }
      } catch {}
      return null;
    });

    const mirrorResults = await Promise.all(mirrorPromises);
    const mirrorSuccess = mirrorResults.find((m) => m !== null);
    if (mirrorSuccess) {
      return new Response(Buffer.from(mirrorSuccess.buf), {
        status: 200,
        headers: {
          "Content-Type": "application/pdf",
          "Content-Disposition": `inline; filename="${filename}"`,
          "X-Vellum-Resolved-Source": "Sci-Hub Academic Mirror",
        },
      });
    }

    return NextResponse.json(
      {
        success: false,
        message: "Paper is paywalled by the publisher. Direct open access was not found across repositories.",
        doi,
        landingUrl: `https://doi.org/${doi}`,
      },
      { status: 404 }
    );
  } catch (err) {
    console.error("Fast download-pdf error:", err);
    return NextResponse.json(
      { success: false, message: err instanceof Error ? err.message : "Failed to download PDF" },
      { status: 500 }
    );
  }
}
