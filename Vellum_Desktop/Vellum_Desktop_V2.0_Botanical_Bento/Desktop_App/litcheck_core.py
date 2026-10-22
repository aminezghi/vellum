"""
Literature-check core: normalisation, cross-source deduplication, OA/PDF
resolution, screening state, PRISMA accounting and exports.

This module holds no Streamlit and no HTTP of its own beyond the Unpaywall
resolver, so every function here is unit-testable headlessly.
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import unicodedata
from collections import Counter, OrderedDict
from datetime import datetime

from litcheck_sources import _norm_doi

try:
    from difflib import SequenceMatcher
except Exception:                                    # pragma: no cover
    SequenceMatcher = None

FIELDNAMES = [
    "doi", "title", "authors", "author_count", "year", "publication_date",
    "epub_date", "journal", "abstract", "keywords", "type", "language",
    "issn", "volume", "issue", "pages", "cited_by", "is_oa", "oa_status",
    "pdf_url", "landing_url", "pmid", "pmcid", "arxiv_id", "openalex_id",
    "sources", "source_count", "match_method", "screen_status",
    "screen_reason", "pdf_ready", "notes",
]


# ── text normalisation ─────────────────────────────────────────────────────

def norm_title(t):
    """Fold a title to a comparable key: no punctuation, no accents, no case."""
    if not t:
        return ""
    t = unicodedata.normalize("NFKD", str(t))
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"<[^>]+>", " ", t)
    t = re.sub(r"[^a-z0-9]+", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def title_tokens(t):
    return set(norm_title(t).split())


def sim_norm_title(na, nb, ta=None, tb=None):
    """Similarity of two already-normalised titles in 0..1."""
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta = ta if ta is not None else set(na.split())
    tb = tb if tb is not None else set(nb.split())
    inter = len(ta & tb)
    union_len = len(ta | tb)
    jac = inter / union_len if union_len else 0.0
    if jac >= 0.85:
        return jac
    if jac < 0.65:
        return jac
    seq = SequenceMatcher(None, na, nb).ratio() if SequenceMatcher else 0.0
    return max(seq, jac)


def sim_title(a, b):
    """Similarity of two titles in 0..1, combining sequence and token overlap."""
    na, nb = norm_title(a), norm_title(b)
    return sim_norm_title(na, nb)


_STOP = {"the", "a", "an", "of", "on", "in", "and", "for", "to", "with", "study",
         "analysis", "its", "from", "by", "at", "is", "are", "using", "via"}


def fingerprint(r):
    """Content fingerprint for a record, used to confirm a fuzzy merge."""
    bits = []
    if r.get("year"):
        bits.append(str(r["year"]))
    if r.get("doi"):
        bits.append(_norm_doi(r["doi"]))
    first = (r.get("authors") or [""])[0]
    if first:
        bits.append(norm_title(first).split()[-1] if norm_title(first) else "")
    return "|".join(bits)


def author_key(a):
    """Comparable author key so 'A One' and 'A. One' collapse on merge."""
    n = norm_title(a)
    return n.replace(" ", "")


def _title_merge_allowed(ri, rj, slack):
    """
    A shared title alone is NOT enough to merge two rows.

    Two different registered DOIs sharing a title are normally genuinely
    distinct works (a republished conference paper, a same-titled study by
    another group), and merging them silently corrupts the PRISMA count. So a
    title match only merges when the years are compatible and the two rows do
    not carry conflicting DOIs.
    """
    yi, yj = ri.get("year"), rj.get("year")
    if yi and yj and abs(int(yi) - int(yj)) > slack:
        return False
    di, dj = _norm_doi(ri.get("doi")), _norm_doi(rj.get("doi"))
    if di and dj and di != dj:
        return False
    return True


# ── deduplication ──────────────────────────────────────────────────────────

def deduplicate(records, threshold=0.92, year_slack=1, progress=None):
    """
    Collapse records describing the same work into one row.

    Pass 1 groups by exact normalised DOI (and by arXiv id / PMCID when the DOI
    is absent, so a preprint and its journal version can be linked).
    Pass 2 groups remaining rows by exact normalised title.
    Pass 3 does fuzzy title matching inside year-bucketed blocks.

    Returns (unique_records, audit_rows, conflicts). `sources` on each merged
    row lists every database the work was found in, `match_method` records how
    the merge was decided, and `conflicts` lists same-titled pairs that were
    deliberately NOT merged so a reviewer can check them by hand.
    """
    audit = []
    rows = [dict(r) for r in records]
    for r in rows:
        r["sources"] = [r.get("source")] if r.get("source") else []
        r["match_method"] = ""

    parent = list(range(len(rows)))
    conflicts = []

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    def union(i, j, method, score=None):
        ri, rj = find(i), find(j)
        if ri == rj:
            return
        parent[rj] = ri
        audit.append({
            "kept_index": ri, "merged_index": rj, "method": method,
            "similarity": round(score, 4) if score is not None else "",
            "doi": rows[ri].get("doi") or rows[rj].get("doi") or "",
            "title": rows[ri].get("title") or rows[rj].get("title") or "",
        })

    # ── pass 1: identifiers ──
    by_id = {}
    for i, r in enumerate(rows):
        keys = []
        if r.get("doi"):
            keys.append("doi:" + _norm_doi(r["doi"]))
        if r.get("arxiv_id"):
            keys.append("arxiv:" + str(r["arxiv_id"]).lower())
        if r.get("pmcid"):
            keys.append("pmcid:" + str(r["pmcid"]).lower())
        for k in keys:
            if k in by_id:
                union(by_id[k], i, "identifier")
            else:
                by_id[k] = i

    # ── pass 2: exact normalised title ──
    by_title = {}
    for i, r in enumerate(rows):
        key = norm_title(r.get("title"))
        if len(key) < 12:
            continue
        prior = by_title.get(key)
        if prior is not None:
            if _title_merge_allowed(rows[prior], r, year_slack):
                union(prior, i, "exact title")
            else:
                conflicts.append({
                    "index": i, "other_index": prior, "reason":
                    "same title but distinct DOI/year — not merged",
                    "title": r.get("title") or "",
                })
        else:
            by_title[key] = i

    # ── pass 3: fuzzy within year blocks (accelerated for 2000+ records) ──
    groups = OrderedDict()
    for i, r in enumerate(rows):
        groups.setdefault(find(i), []).append(i)
    buckets = {}
    for i in list(groups.keys()):
        r = rows[i]
        nt = norm_title(r.get("title"))
        if len(nt) < 12:
            continue
        buckets.setdefault(r.get("year") or 0, []).append((i, nt))

    for bkey, items in buckets.items():
        # Sort items by title length to enable immediate branch pruning
        items.sort(key=lambda x: len(x[1]))
        n_items = len(items)
        token_cache = {idx: set(nt.split()) for idx, nt in items}

        for a in range(n_items):
            i, ni = items[a]
            len_a = len(ni)
            tokens_a = token_cache[i]
            if not tokens_a:
                continue

            for b in range(a + 1, n_items):
                j, nj = items[b]
                len_b = len(nj)

                # Length pruning: since items are sorted by length, once len_b exceeds the
                # allowed difference for the given threshold, all subsequent items will too.
                if (len_b - len_a) > len_b * (1.0 - threshold):
                    break

                if find(i) == find(j):
                    continue
                if not _title_merge_allowed(rows[i], rows[j], year_slack):
                    continue

                # Fast token overlap gate (O(1) in C) before invoking slow SequenceMatcher
                tokens_b = token_cache[j]
                if not tokens_b:
                    continue
                inter = len(tokens_a & tokens_b)
                if not inter:
                    continue
                union_len = len(tokens_a | tokens_b)
                if union_len > 0 and (inter / union_len) < (threshold - 0.20):
                    continue

                s = sim_norm_title(ni, nj, tokens_a, tokens_b)
                if s >= threshold:
                    union(i, j, "fuzzy title", s)

    # ── merge ──
    merged = OrderedDict()
    for i in range(len(rows)):
        merged.setdefault(find(i), []).append(i)
    out = []
    for members in merged.values():
        base = dict(rows[members[0]])
        base["doi"] = _norm_doi(base.get("doi"))
        base.setdefault("authors", [])
        if not isinstance(base["authors"], list):
            base["authors"] = list(base["authors"]) if base["authors"] else []
        all_sources, methods = [], []
        for m in members:
            all_sources.extend(rows[m].get("sources") or [])
            if rows[m].get("match_method"):
                methods.append(rows[m]["match_method"])
            for f in ("abstract", "pdf_url", "landing_url", "journal",
                      "issn", "pmid", "pmcid", "arxiv_id", "openalex_id",
                      "volume", "issue", "pages", "keywords", "cited_by",
                      "is_oa", "oa_status", "type", "language", "publication_date"):
                if not base.get(f) and rows[m].get(f):
                    base[f] = rows[m][f]
            # a preprint row usually has no DOI; adopt the published version's
            if not base.get("doi") and rows[m].get("doi"):
                base["doi"] = _norm_doi(rows[m]["doi"])
            for a in (rows[m].get("authors") or []):
                if a and not any(author_key(a) == author_key(b)
                                 for b in base["authors"]):
                    base["authors"].append(a)
        base["authors"] = base["authors"][:60]
        base["sources"] = sorted(set(s for s in all_sources if s))
        base["source_count"] = len(base["sources"])
        if methods:
            base["match_method"] = "; ".join(sorted(set(methods)))
        elif len(members) > 1:
            base["match_method"] = "identifier"
        if len(members) == 1:
            base["match_method"] = "unique"
        out.append(base)
    out.sort(key=lambda r: (-(r.get("cited_by") or 0), str(r.get("title"))))
    if progress:
        progress(len(out), len(audit))
    return out, audit, conflicts


def roots(groups):
    return list(groups.keys())


# ── table building / screening ─────────────────────────────────────────────

def _join(v):
    """Join a list-ish field to a CSV cell.

    Sources are inconsistent (Scopus nests values as {'value': [...]}, some
    return bare strings), so never assume a list of str.
    """
    if v is None:
        return ""
    if isinstance(v, str):
        return v
    if isinstance(v, (list, tuple, set)):
        out = []
        for x in v:
            if isinstance(x, dict):
                x = x.get("$") or x.get("value") or x.get("#text") or ""
                if isinstance(x, (list, tuple)):
                    x = "; ".join(str(y) for y in x)
            if x not in (None, ""):
                out.append(str(x))
        return "; ".join(out)
    return str(v)


def to_row(r):
    authors = r.get("authors") or []
    if isinstance(authors, str):
        authors = [authors]
    return {
        "doi": r.get("doi") or "",
        "title": r.get("title") or "",
        "authors": "; ".join(str(a) for a in authors if a),
        "author_count": len(authors),
        "year": r.get("year") or "",
        "publication_date": r.get("publication_date") or "",
        "epub_date": r.get("epub_date") or "",
        "journal": r.get("journal") or "",
        "abstract": r.get("abstract") or "",
        "keywords": _join(r.get("keywords")),
        "type": r.get("type") or "",
        "language": r.get("language") or "",
        "issn": _join(r.get("issn")),
        "volume": r.get("volume") or "",
        "issue": r.get("issue") or "",
        "pages": r.get("pages") or "",
        "cited_by": r.get("cited_by") if r.get("cited_by") is not None else "",
        "is_oa": r.get("is_oa") if r.get("is_oa") is not None else "",
        "oa_status": r.get("oa_status") or "",
        "pdf_url": r.get("pdf_url") or "",
        "landing_url": r.get("landing_url") or "",
        "pmid": r.get("pmid") or "",
        "pmcid": r.get("pmcid") or "",
        "arxiv_id": r.get("arxiv_id") or "",
        "openalex_id": r.get("openalex_id") or "",
        "sources": _join(r.get("sources")),
        "source_count": r.get("source_count") or len(r.get("sources") or []),
        "match_method": r.get("match_method") or "",
        "screen_status": r.get("screen_status") or "",
        "screen_reason": r.get("screen_reason") or "",
        "pdf_ready": "yes" if is_pdf_ready(r) else "",
        "notes": r.get("notes") or "",
    }


def is_pdf_ready(r):
    """True when the row already carries a direct PDF URL we can hand to the
    downloader."""
    u = r.get("pdf_url") or ""
    return bool(u) and u.lower().startswith(("http://", "https://"))


# ── filters ────────────────────────────────────────────────────────────────

def apply_filters(rows, f):
    """Client-side refinement. The API filters are best-effort; these are exact."""
    out = []
    for r in rows:
        y = r.get("year")
        if f.get("year_from") and y and y < f["year_from"]:
            continue
        if f.get("year_to") and y and y > f["year_to"]:
            continue
        if f.get("oa_only") and not (r.get("is_oa") or r.get("pdf_url")):
            continue
        if f.get("has_fulltext") and not r.get("pdf_url"):
            continue
        if f.get("has_abstract") and not r.get("abstract"):
            continue
        if f.get("min_citations") and (r.get("cited_by") or 0) < f["min_citations"]:
            continue
        if f.get("language") and (r.get("language") or "").lower() != \
                str(f["language"]).lower():
            continue
        types = f.get("doc_types")
        if types:
            t = str(r.get("type") or "").lower().replace(" ", "-")
            if t and not any(t.startswith(x.replace(" ", "-")) or
                             x.replace(" ", "-") in t for x in types):
                continue
        if f.get("journal_contains"):
            if f["journal_contains"].lower() not in str(r.get("journal") or "").lower():
                continue
        if f.get("author_contains"):
            if f["author_contains"].lower() not in \
                    " ".join(r.get("authors") or []).lower():
                continue
        q = f.get("title_contains")
        if q and q.lower() not in norm_title(r.get("title")):
            continue
        out.append(r)
    return out


# ── PRISMA ─────────────────────────────────────────────────────────────────

def prisma(reports, unique, screened_included, screened_excluded, queue):
    """
    Build PRISMA 2020 style identification/screening counts.

    `reports` is the per-source report list from run_search, so "identified"
    uses each database's own reported hit count rather than only what we
    actually downloaded — that distinction is the whole point of the diagram.
    """
    per_source = []
    identified = duplicates_removed = 0
    for rep in reports:
        n = rep.get("reported")
        n = n if isinstance(n, int) and n >= 0 else rep.get("n", 0)
        identified += n
        per_source.append({
            "database": rep.get("label") or rep.get("source"),
            "reported_hits": n,
            "retrieved": rep.get("n", 0),
            "truncated": bool(rep.get("truncated")),
            "status": rep.get("status") or "ok",
        })
    retrieved = sum(r.get("n", 0) for r in reports)
    duplicates_removed = max(0, retrieved - len(unique))
    return {
        "per_source": per_source,
        "identified": identified,
        "retrieved": retrieved,
        "duplicates_removed": duplicates_removed,
        "after_dedup": len(unique),
        "screened": len(unique),
        "excluded_at_screening": screened_excluded,
        "included": screened_included,
        "pdf_queue": len(queue),
        "generated": datetime.now().isoformat(timespec="seconds"),
    }


# ── exports ────────────────────────────────────────────────────────────────

def _csv(rows, cols=None):
    cols = cols or FIELDNAMES
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=cols, extrasaction="ignore")
    w.writeheader()
    for r in rows:
        if isinstance(r, dict) and set(r) <= set(cols):
            w.writerow({c: _join(r.get(c, "")) for c in cols})
        else:
            w.writerow({c: _join((r or {}).get(c, "")) for c in cols})
    return buf.getvalue()


def export_csv(rows, cols=None):
    """Accepts raw canonical records or already-flattened rows."""
    cols = cols or FIELDNAMES
    return _csv([r if isinstance(r, dict) and set(r) <= set(cols) else to_row(r)
                 for r in rows], cols)


def export_duplicates(audit):
    cols = ["kept_index", "merged_index", "method", "similarity", "doi", "title"]
    return _csv(audit, cols)


def _bibtex_key(r):
    first = (r.get("authors") or ["anon"])[0]
    last = re.sub(r"[^A-Za-z]", "", (str(first).split() or ["anon"])[-1]) or "anon"
    doi = str(r.get("doi") or "")
    suffix = doi.split("/")[-1][:6] if doi else ""
    return f"{last.lower()}{r.get('year') or 'nd'}{suffix}"


def export_bibtex(rows):
    out = []
    for r in rows:
        key = _bibtex_key(r)
        auth = " and ".join(str(a) for a in (r.get("authors") or [])) or "Anon"
        fields = [("title", "{%s}" % (r.get("title") or "")),
                  ("author", "{%s}" % auth),
                  ("journal", r.get("journal") or ""),
                  ("year", str(r.get("year") or "")),
                  ("doi", r.get("doi") or ""),
                  ("url", r.get("landing_url") or r.get("pdf_url") or ""),
                  ("abstract", (r.get("abstract") or "")[:900])]
        body = ",\n".join(f"  {k} = {v}" for k, v in fields if v)
        out.append(f"@article{{{key},\n{body}\n}}")
    return "\n\n".join(out) + "\n"


def export_ris(rows):
    out = []
    for r in rows:
        lines = ["TY  - JOUR"]
        for a in (r.get("authors") or []):
            lines.append(f"AU  - {a}")
        for k, v in (("TI", r.get("title")), ("JO", r.get("journal")),
                     ("PY", r.get("year")), ("DO", r.get("doi")),
                     ("AB", r.get("abstract")), ("UR", r.get("landing_url")),
                     ("VL", r.get("volume")), ("IS", r.get("issue")),
                     ("SP", r.get("pages"))):
            if v:
                lines.append(f"{k}  - {v}")
        for kw in (r.get("keywords") or [])[:12]:
            lines.append(f"KW  - {kw}")
        lines.append("ER  - ")
        out.append("\n".join(lines))
    return "\n\n".join(out) + "\n"


def export_prisma_json(p):
    return json.dumps(p, indent=2)


def export_prisma_csv(p):
    cols = ["stage", "count"]
    rows = [("Records identified (all databases, as reported)", p["identified"]),
            ("Records actually retrieved", p["retrieved"]),
            ("Duplicates removed", p["duplicates_removed"]),
            ("Records after deduplication", p["after_dedup"]),
            ("Records screened", p["screened"]),
            ("Records excluded at screening", p["excluded_at_screening"]),
            ("Records included", p["included"]),
            ("Records in PDF download queue", p["pdf_queue"])]
    return _csv([{"stage": a, "count": b} for a, b in rows], cols)


# ── download queue ─────────────────────────────────────────────────────────

def build_queue(rows, prefer_oa=True):
    """
    Turn screened rows into the list handed to the existing downloader.

    Only rows with a resolvable identifier survive: a DOI (which the downloader
    can resolve through Unpaywall/OpenAlex/publisher routes) or a direct PDF URL.
    """
    q, seen = [], set()
    for r in rows:
        doi = _norm_doi(r.get("doi"))
        pdf_url = r.get("pdf_url") or ""
        key = doi or pdf_url
        if not key or key in seen:
            continue
        seen.add(key)
        authors = r.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        cited = r.get("cited_by")
        q.append({
            "doi": doi or "",
            "title": r.get("title") or "",
            "year": r.get("year") or "",
            "journal": r.get("journal") or "",
            "authors": "; ".join(str(a) for a in authors)[:300],
            "pdf_url": pdf_url,
            "landing_url": r.get("landing_url") or "",
            "oa": bool(r.get("is_oa")),
            "oa_status": r.get("oa_status") or "",
            "sources": _join(r.get("sources")),
            "cited_by": cited if isinstance(cited, int) else "",
        })
    if prefer_oa:
        q.sort(key=lambda x: (not x["oa"], -x["cited_by"] if x["cited_by"] else 0))
    return q


# ── project persistence ────────────────────────────────────────────────────

PROJECTS_DIR = os.path.expanduser("~/.pdf_downloader_projects")


def save_project(name, payload):
    os.makedirs(PROJECTS_DIR, exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name))[:80] or "project"
    path = os.path.join(PROJECTS_DIR, safe + ".json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(payload, fh, indent=2, default=str)
    return path


def load_projects():
    if not os.path.isdir(PROJECTS_DIR):
        return []
    out = []
    for fn in sorted(os.listdir(PROJECTS_DIR)):
        if fn.endswith(".json"):
            out.append(fn[:-5])
    return out


def load_project(name):
    safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", str(name))[:80] or "project"
    path = os.path.join(PROJECTS_DIR, safe + ".json")
    if not os.path.exists(path):
        return None
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


# ── snowballing ────────────────────────────────────────────────────────────

def seed_dois(rows, limit=25):
    """Pick well-cited, DOI-bearing seeds for backward snowballing."""
    cand = [r for r in rows if _norm_doi(r.get("doi"))]
    cand.sort(key=lambda r: -(r.get("cited_by") or 0)
              if isinstance(r.get("cited_by"), int) else 0)
    return [_norm_doi(r["doi"]) for r in cand[:limit]]


def cited_by_doi(doi, email=None, key=None):
    """OpenAlex works that cite `doi` — the backward-snowball pass."""
    import requests
    s = requests.Session()
    s.headers.update({"User-Agent": f"PDF-Downloader-Research-App/2.0 (mailto:{email or 'anonymous'})"})
    params = {"filter": f"cites:{_norm_doi(doi)}", "per-page": 200,
              "select": "id,doi,title,publication_year,authorships,cited_by_count"}
    if key:
        params["api_key"] = key
    r = s.get("https://api.openalex.org/works", params=params, timeout=45)
    if r.status_code != 200:
        return []
    return [w for w in (r.json().get("results") or []) if w.get("doi")]