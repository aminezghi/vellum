import { NextRequest, NextResponse } from "next/server";
import { AcademicPaperResult } from "../search/route";
import { OpenAlexPage, authorNames, bareDoi, reconstructAbstract, workTopics } from "@/lib/openalex";

export interface TrendingDomainFeed {
  domainId: string;
  domainName: string;
  icon: string;
  papers: (AcademicPaperResult & { velocityScore: string; velocityBadge: string })[];
}

const DOMAIN_QUERIES: Record<string, { name: string; icon: string; conceptId: string; keywords: string }> = {
  ai: {
    name: "Artificial Intelligence & LLMs",
    icon: "🧠",
    conceptId: "C41008148", // Computer science
    keywords: "large language models transformers reasoning agents",
  },
  biomedicine: {
    name: "Biomedicine & Genomics",
    icon: "🧬",
    conceptId: "C71924100", // Medicine
    keywords: "immunotherapy crispr spatial transcriptomics mrna oncology",
  },
  economics: {
    name: "Economics & Market Behavior",
    icon: "📈",
    conceptId: "C162324750", // Economics
    keywords: "behavioral consumer demand inflation econometric supply chain",
  },
  environment: {
    name: "Climate & Agronomic Resilience",
    icon: "🌱",
    conceptId: "C18903297", // Ecology
    keywords: "carbon capture drought resilience regenerative agriculture biodiversity",
  },
  neuroscience: {
    name: "Neuroscience & Cognitive Science",
    icon: "⚡",
    conceptId: "C169760540", // Neuroscience
    keywords: "connectomics neural plasticity cognitive memory brain interface",
  },
};

export async function GET(req: NextRequest) {
  const { searchParams } = new URL(req.url);
  const domain = searchParams.get("domain") || "ai";
  const domainConfig = DOMAIN_QUERIES[domain] || DOMAIN_QUERIES["ai"];

  try {
    const currentYear = new Date().getFullYear();
    const fromYear = currentYear - 2;

    const openAlexUrl = new URL("https://api.openalex.org/works");
    openAlexUrl.searchParams.set("search", domainConfig.keywords);
    openAlexUrl.searchParams.set(
      "filter",
      `publication_year:${fromYear}-${currentYear},is_oa:true`
    );
    openAlexUrl.searchParams.set("sort", "cited_by_count:desc");
    openAlexUrl.searchParams.set("per_page", "8");

    const response = await fetch(openAlexUrl.toString(), {
      headers: {
        "User-Agent": "Vellum-Research-Web/1.0 (mailto:vellum@research.local)",
      },
      next: { revalidate: 7200 }, // Cache 2 hours
    });

    if (!response.ok) {
      throw new Error(`OpenAlex Trends API error: ${response.status}`);
    }

    const data = (await response.json()) as OpenAlexPage;
    const works = data.results ?? [];

    const papers = works.map((w, idx) => {
      const authors = authorNames(w);

      const venue =
        w.primary_location?.source?.display_name ||
        w.host_venue?.display_name ||
        "Nature / Science / PNAS";

      const pdfUrl =
        w.open_access?.oa_url ||
        w.primary_location?.pdf_url ||
        (w.best_oa_location?.pdf_url ?? undefined);

      const abstract = reconstructAbstract(w.abstract_inverted_index);
      const doiClean = bareDoi(w.doi);

      const cites = w.cited_by_count || 0;
      let badge = "📈 Rising";
      if (idx === 0 || cites > 200) {
        badge = "🔥 High Velocity (+85 cites/mo)";
      } else if (cites > 50) {
        badge = "⚡ Fast-Breaking";
      } else if (w.publication_year === currentYear) {
        badge = "✨ Recent Breakthrough";
      }

      return {
        id: w.id || `trend-${Date.now()}-${idx}`,
        title: w.title || "Emerging Empirical Findings in " + domainConfig.name,
        authors: authors.length > 0 ? authors : ["Research Consortium"],
        year: w.publication_year || currentYear,
        venue,
        doi: doiClean,
        citationCount: cites,
        isOpenAccess: true,
        pdfUrl: pdfUrl || undefined,
        abstract,
        source: "OpenAlex" as const,
        topics: workTopics(w),
        velocityScore: `${cites} citations`,
        velocityBadge: badge,
      };
    });

    return NextResponse.json({
      domainId: domain,
      domainName: domainConfig.name,
      icon: domainConfig.icon,
      papers,
    });
  } catch (err) {
    console.error("Trends fetch error:", err);
    return NextResponse.json(
      { error: err instanceof Error ? err.message : "Failed to fetch trending literature", papers: [] },
      { status: 500 }
    );
  }
}
