import { NextRequest, NextResponse } from "next/server";
import { AcademicPaperResult } from "../search/route";

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const seedId = searchParams.get("seedId") || "";
  const doi = searchParams.get("doi") || "";

  if (!seedId && !doi) {
    return NextResponse.json({ error: "seedId or doi is required", related: [] }, { status: 400 });
  }

  try {
    const identifier = seedId.startsWith("http") ? seedId : doi ? `https://doi.org/${doi}` : `https://openalex.org/${seedId}`;
    const openAlexUrl = new URL(`https://api.openalex.org/works/${encodeURIComponent(identifier)}`);

    const response = await fetch(openAlexUrl.toString(), {
      headers: {
        "User-Agent": "Vellum-Research-Web/1.0 (mailto:vellum@research.local)",
      },
      next: { revalidate: 3600 },
    });

    if (!response.ok) {
      throw new Error(`OpenAlex paper lookup error: ${response.status}`);
    }

    const work = await response.json();
    const relatedUrls = work.related_works || [];

    // Fetch details for related works
    let relatedPapers: AcademicPaperResult[] = [];
    if (relatedUrls.length > 0) {
      const idsToFetch = relatedUrls.slice(0, 6).map((u: string) => u.split("/").pop()).join("|");
      const batchUrl = `https://api.openalex.org/works?filter=openalex:${idsToFetch}`;
      const batchRes = await fetch(batchUrl, {
        headers: { "User-Agent": "Vellum-Research-Web/1.0" },
      });
      if (batchRes.ok) {
        const batchData = await batchRes.json();
        relatedPapers = (batchData.results || []).map((w: any) => ({
          id: w.id,
          title: w.title,
          authors: (w.authorships || []).map((a: any) => a.author?.display_name).filter(Boolean),
          year: w.publication_year,
          venue: w.primary_location?.source?.display_name || "Journal",
          doi: w.doi ? w.doi.replace(/^https?:\/\/doi\.org\//i, "") : undefined,
          citationCount: w.cited_by_count || 0,
          isOpenAccess: !!w.is_oa,
          pdfUrl: w.open_access?.oa_url || w.primary_location?.pdf_url || undefined,
          source: "OpenAlex" as const,
        }));
      }
    }

    return NextResponse.json({
      seedTitle: work.title,
      seedYear: work.publication_year,
      citationCount: work.cited_by_count,
      related: relatedPapers,
    });
  } catch (err: any) {
    console.error("Connected papers error:", err);
    return NextResponse.json(
      { error: err.message || "Failed to find connected papers", related: [] },
      { status: 500 }
    );
  }
}
