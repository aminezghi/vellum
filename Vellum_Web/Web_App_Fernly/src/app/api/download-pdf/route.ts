import { NextRequest, NextResponse } from "next/server";

const DEFAULT_SCIHUB_MIRRORS = [
  "https://sci-hub.se/",
  "https://sci-hub.st/",
  "https://sci-hub.ru/",
  "https://sci-hub.ee/",
];

const DEFAULT_EMAIL = "scholar.vellum@gmail.com";

const USER_AGENT =
  "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36";

function isValidPdf(buffer: Uint8Array): boolean {
  if (buffer.length < 1500) return false;
  const header = String.fromCharCode(...buffer.slice(0, 1024));
  return header.includes("%PDF");
}

async function fetchPdfBuffer(
  url: string,
  timeoutMs = 8000,
  extraHeaders: Record<string, string> = {}
): Promise<{ buf: Uint8Array; url: string } | null> {
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
        ...extraHeaders,
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
// Upstream payloads
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

interface EuropePmcEnvelope {
  resultList?: {
    result?: Array<{ pmcid?: string }>;
  };
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

  // 1. Meta citation tags
  const metaRegex = /<meta[^>]+(?:name|property)=["'](?:citation_pdf_url|bepress_citation_pdf_url|eprints\.document_url)["'][^>]+content=["']([^"']+)["']/gi;
  let m: RegExpExecArray | null;
  while ((m = metaRegex.exec(html)) !== null) {
    if (m[1]) addUrl(m[1]);
  }
  const metaRegexRev = /<meta[^>]+content=["']([^"']+)["'][^>]+(?:name|property)=["'](?:citation_pdf_url|bepress_citation_pdf_url|eprints\.document_url)["']/gi;
  while ((m = metaRegexRev.exec(html)) !== null) {
    if (m[1]) addUrl(m[1]);
  }

  // 2. Anchor tags with pdf links
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

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const doi = searchParams.get("doi");
  if (!doi) {
    return NextResponse.json(
      { error: "Query parameter 'doi' is required." },
      { status: 400 }
    );
  }
  return POST(
    new NextRequest(req.url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        doi,
        title: searchParams.get("title") || "",
        pdfUrl: searchParams.get("pdfUrl") || "",
        email: searchParams.get("email") || "",
        elsevierApiKey: searchParams.get("elsevierApiKey") || "",
        customMirror: searchParams.get("customMirror") || "",
        ezproxyUrl: searchParams.get("ezproxyUrl") || "",
      }),
    })
  );
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const rawDoi = (body.doi || "").trim();
    const doi = rawDoi.toLowerCase().replace(/^https?:\/\/(?:dx\.)?doi\.org\//i, "");
    let title = (body.title || "document").trim();
    const initialPdfUrl = (body.pdfUrl || (rawDoi.startsWith("http") && !rawDoi.includes("doi.org/") ? rawDoi : "")).trim();

    // User-configured paywall bypass & resolver settings
    const email = (body.email || DEFAULT_EMAIL).trim();
    const elsevierApiKey = (body.elsevierApiKey || process.env.ELSEVIER_API_KEY || "").trim();
    const customMirror = (body.customMirror || "").trim();
    const ezproxyUrl = (body.ezproxyUrl || "").trim();

    const cleanTitle = title.replace(/[^\w\s-]/gi, "").slice(0, 50).trim();
    const filename = `${cleanTitle || "Paper"}.pdf`;

    // Format EZProxy landing URL if paywalled
    const getLandingUrl = (rawDoiUrl: string) => {
      if (!ezproxyUrl) return rawDoiUrl;
      const proxy = ezproxyUrl.trim();
      if (proxy.includes("url=")) {
        return `${proxy}${rawDoiUrl}`;
      }
      return `${proxy.replace(/\/$/, "")}/${rawDoiUrl}`;
    };

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
          landingUrl: initialPdfUrl ? getLandingUrl(initialPdfUrl) : undefined,
        },
        { status: 404 }
      );
    }

    // ── Tier 2: Elsevier / ScienceDirect Official API (Dev Key Bypass) ────────
    if (elsevierApiKey && (doi.startsWith("10.1016/") || doi.includes("elsevier") || doi.includes("sciencedirect"))) {
      try {
        const elsRes = await fetchPdfBuffer(
          `https://api.elsevier.com/content/article/doi/${doi}?httpAccept=application/pdf`,
          10000,
          { "X-ELS-APIKey": elsevierApiKey }
        );
        if (elsRes) {
          return new Response(Buffer.from(elsRes.buf), {
            status: 200,
            headers: {
              "Content-Type": "application/pdf",
              "Content-Disposition": `inline; filename="${filename}"`,
              "X-Vellum-Resolved-Source": "Elsevier ScienceDirect API",
            },
          });
        }
      } catch {}
    }

    // ── Tier 3: Direct Publisher Open Access Routes ──────────────────────────
    const candidateUrls: { url: string; source: string }[] = [];

    // MDPI Direct Route (100% OA)
    if (doi.startsWith("10.3390/")) {
      const slug = doi.replace("10.3390/", "");
      candidateUrls.push({
        url: `https://www.mdpi.com/${slug}/pdf`,
        source: "MDPI Open Access Direct",
      });
    }

    // Springer / Nature / BMC
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

    // Wiley direct routes
    if (doi.startsWith("10.1111/") || doi.startsWith("10.1002/")) {
      candidateUrls.push({
        url: `https://onlinelibrary.wiley.com/doi/pdfdirect/${doi}`,
        source: "Wiley Online Library Direct",
      });
    }

    // arXiv Preprints
    if (doi.toLowerCase().startsWith("10.48550/arxiv.")) {
      const arxivId = doi.split(/arxiv\./i).pop();
      candidateUrls.push({
        url: `https://arxiv.org/pdf/${arxivId}.pdf`,
        source: "arXiv Preprints",
      });
    }

    // bioRxiv / medRxiv Direct
    if (doi.startsWith("10.1101/")) {
      candidateUrls.push({
        url: `https://www.biorxiv.org/content/${doi}v1.full.pdf`,
        source: "bioRxiv / medRxiv Direct",
      });
    }

    // ── Parallel Registry Queries (Unpaywall, OpenAlex, Semantic Scholar, Crossref, Europe PMC) ──
    const unpaywallUrl = `https://api.unpaywall.org/v2/${doi}?email=${encodeURIComponent(email)}`;
    const openAlexUrl = `https://api.openalex.org/works/https://doi.org/${doi}?mailto=${encodeURIComponent(email)}`;

    const [crData, unpData, s2Data, oaData, epmcData] = await Promise.all([
      fetchJsonWithTimeout<CrossrefEnvelope>(`https://api.crossref.org/works/${doi}`, 5000),
      fetchJsonWithTimeout<UnpaywallEnvelope>(unpaywallUrl, 6000),
      fetchJsonWithTimeout<SemanticScholarEnvelope>(`https://api.semanticscholar.org/graph/v1/paper/DOI:${doi}?fields=openAccessPdf,title`, 5000),
      fetchJsonWithTimeout<OpenAlexEnvelope>(openAlexUrl, 6000),
      fetchJsonWithTimeout<EuropePmcEnvelope>(`https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:%22${encodeURIComponent(doi)}%22&format=json&resultType=core`, 5000),
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

    if (epmcData?.resultList?.result?.[0]?.pmcid) {
      const pmcid = epmcData.resultList.result[0].pmcid;
      candidateUrls.push({
        url: `https://www.ncbi.nlm.nih.gov/pmc/articles/${pmcid}/pdf/`,
        source: "Europe PMC / PubMed Central",
      });
    }

    // Try candidate OA URLs in parallel
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

    // ── Tier 4: Publisher HTML Metadata & Google Scholar Scraping ────────────
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

    // ── Tier 5: Academic Mirrors (Sci-Hub, LibGen) ───────────────────────────
    const mirrors = customMirror
      ? [customMirror, ...DEFAULT_SCIHUB_MIRRORS.filter((m) => m !== customMirror)]
      : DEFAULT_SCIHUB_MIRRORS;

    const mirrorPromises = mirrors.map(async (mirror) => {
      const cleanMirror = mirror.endsWith("/") ? mirror : `${mirror}/`;
      try {
        const shRes = await fetch(`${cleanMirror}${doi}`, {
          headers: { "User-Agent": USER_AGENT },
          signal: AbortSignal.timeout(6000),
        });
        if (shRes.ok) {
          const text = await shRes.text();

          // 1. Check for iframe/embed id="pdf"
          let pdfUrl: string | null = null;
          const embedMatch = text.match(/<(?:iframe|embed)[^>]+src=["']([^"']+)["'][^>]*id=["']pdf["']/i) ||
                             text.match(/id=["']pdf["'][^>]+src=["']([^"']+)["']/i) ||
                             text.match(/<(?:iframe|embed)[^>]+src=["']([^"']+\.pdf[^"']*)["']/i);
          if (embedMatch && embedMatch[1]) {
            pdfUrl = embedMatch[1];
          }

          // 2. Check for onclick="location.href='...'"
          if (!pdfUrl) {
            const clickMatch = text.match(/location\.href\s*=\s*['"]([^'"]+)['"]/i);
            if (clickMatch && clickMatch[1]) {
              pdfUrl = clickMatch[1];
            }
          }

          // 3. Regex search for any .pdf url
          if (!pdfUrl) {
            const rawPdfMatch = text.match(/(?:https?:)?\/\/[^\s'"<>]+\.pdf[^\s'"<>]*/i);
            if (rawPdfMatch && rawPdfMatch[0]) {
              pdfUrl = rawPdfMatch[0];
            }
          }

          if (pdfUrl) {
            if (pdfUrl.startsWith("//")) pdfUrl = "https:" + pdfUrl;
            else if (pdfUrl.startsWith("/")) pdfUrl = cleanMirror.replace(/\/$/, "") + pdfUrl;

            const finalPdf = await fetchPdfBuffer(pdfUrl, 8000);
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

    const defaultLanding = `https://doi.org/${doi}`;
    return NextResponse.json(
      {
        success: false,
        message: "Paper is paywalled by the publisher. Direct open access was not found across repositories.",
        doi,
        landingUrl: getLandingUrl(defaultLanding),
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
