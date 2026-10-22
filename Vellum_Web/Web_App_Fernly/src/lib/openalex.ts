/**
 * Shared helpers for reading the OpenAlex REST API.
 *
 * Three API routes (search, trends, connected) each talked to OpenAlex and
 * each carried its own copy of `reconstructAbstract`, which is how they drifted
 * apart: one of them silently stopped reading concept names when OpenAlex
 * renamed the field. The shape below is deliberately partial — it describes
 * only the fields we read, so that a new OpenAlex field costs us nothing and a
 * removed one fails the type check.
 *
 * OpenAlex is a third-party API. Everything that arrives from it is `unknown`
 * until it has been narrowed, which is what the route casts here are for.
 */

export interface OpenAlexWork {
  id?: string;
  title?: string;
  authorships?: { author?: { display_name?: string } }[];
  primary_location?: { source?: { display_name?: string }; pdf_url?: string };
  host_venue?: { display_name?: string };
  open_access?: { oa_url?: string };
  best_oa_location?: { pdf_url?: string };
  abstract_inverted_index?: Record<string, number[]>;
  topics?: { display_name?: string }[];
  concepts?: { display_name?: string }[];
  doi?: string;
  publication_year?: number;
  cited_by_count?: number;
  is_oa?: boolean;
  related_works?: string[];
  referenced_works?: string[];
}

/** The envelope every OpenAlex list endpoint returns. */
export interface OpenAlexPage {
  results?: OpenAlexWork[];
}

/** Keep only the non-empty strings out of a mapped list of optional values. */
export function nonEmpty(values: (string | undefined | null)[]): string[] {
  return values.filter((v): v is string => typeof v === "string" && v.length > 0);
}

/** Turn an OpenAlex `abstract_inverted_index` back into running prose. */
export function reconstructAbstract(
  invertedIndex?: Record<string, number[]>
): string | undefined {
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

/** Author display names, in order, with blanks dropped. */
export function authorNames(work: OpenAlexWork): string[] {
  return nonEmpty((work.authorships ?? []).map((a) => a.author?.display_name));
}

/** OpenAlex renamed `concepts` to `topics`; accept whichever is present. */
export function workTopics(work: OpenAlexWork, limit = 3): string[] {
  return nonEmpty(
    (work.topics ?? work.concepts ?? []).slice(0, limit).map((c) => c.display_name)
  );
}

/** A DOI as bare text, not as a resolvable URL. */
export function bareDoi(doi?: string): string | undefined {
  return doi ? doi.replace(/^https?:\/\/doi\.org\//i, "") : undefined;
}
