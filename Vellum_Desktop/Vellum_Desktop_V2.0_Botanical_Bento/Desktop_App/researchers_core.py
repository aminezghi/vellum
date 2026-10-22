"""Researcher directory: search author profiles and keep the ones you like.

Backed by three free, key-free (or key-optional) identity sources:

* **OpenAlex** — canonical author records, works counts, citation totals,
  h-index via ``summary_stats``, ORCID and affiliations.
* **ORCID** — the authoritative identity record; confirms a person is who they
  say they are and which works they claim.
* **Semantic Scholar** — an independent citation count, useful as a sanity
  check when the other two disagree.

Each adapter returns the same normalised profile dict so results can be shown
side by side, and saved profiles can be compared. Nothing raises: a dead
source returns a status, mirroring ``litcheck_sources``.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.parse as _up
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
TIMEOUT = 30
MAILTO = "amine.zouaghi@unipr.it"

STORE = Path(os.path.expanduser("~/.vellum/researchers.json"))
_STORE_LOCK = threading.Lock()


def _clean(s, limit=0):
    if s is None:
        return None
    s = re.sub(r"<[^>]+>", " ", str(s))
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s or None


def _norm_orcid(o):
    if not o:
        return None
    o = str(o).strip().upper()
    o = re.sub(r"^(HTTPS?://(ORCID\.ORG/)?)?", "", o)
    o = re.sub(r"[^0-9X\-]", "", o)
    if re.fullmatch(r"\d{4}-\d{4}-\d{4}-\d{3}[\dX]", o):
        return o
    return None


def _norm_doi(d):
    """Normalise a DOI to its bare lower-case form, without a resolver prefix.

    Kept separate from ``_norm_orcid``: an ORCID validator rejects every DOI,
    so routing DOIs through it silently dropped them all.
    """
    if not d:
        return None
    d = str(d).strip().lower()
    d = re.sub(r"^(https?://)?((dx\.)?doi\.org/|doi:)", "", d)
    d = d.strip().strip("/")
    return d or None


def _int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _session(email=None):
    s = requests.Session()
    s.headers.update({
        "User-Agent": UA if not email else
        f"Vellum/3.0 (academic research companion; mailto:{email})",
    })
    return s


def _mailto(email):
    return {"mailto": email} if email else {"mailto": MAILTO}


# ── profile shape ────────────────────────────────────────────────────────────
def blank_profile():
    return {
        "key": "",            # stable id: "<source>:<id>"
        "source": "",
        "source_id": "",
        "name": "",
        "alternative_names": [],
        "orcid": None,
        "affiliations": [],
        "department": "",
        "works_count": None,
        "citations": None,
        "h_index": None,
        "i10_index": None,
        "oa_works": None,
        "topics": [],
        "homepage": None,
        "works": [],
        "status": "ok",
        "note": "",
    }


def _affiliation_names(items):
    out = []
    for a in items or []:
        if isinstance(a, str):
            name = a
        elif isinstance(a, dict):
            name = (a.get("raw_affiliation_strings")
                    or a.get("raw_affiliation_string")
                    or a.get("institution") or a.get("name"))
            if isinstance(name, list):
                name = "; ".join(str(x) for x in name if x)
        else:
            name = None
        name = _clean(name, 200)
        if name and name not in out:
            out.append(name)
    return out


# ── OpenAlex ─────────────────────────────────────────────────────────────────
OA = "https://api.openalex.org"


def _oa_author(a):
    p = blank_profile()
    p["source"] = "OpenAlex"
    p["source_id"] = a.get("id") or ""
    p["key"] = f"openalex:{p['source_id'].rsplit('/', 1)[-1]}"
    p["name"] = _clean(a.get("display_name"), 200)
    p["orcid"] = _norm_orcid(a.get("orcid"))
    p["alternative_names"] = [_clean(x, 200) for x in (a.get("display_name_alternatives") or [])[:4]
                              if _clean(x, 200) and _clean(x, 200) != p["name"]]
    insts = a.get("last_known_institutions") or []
    p["affiliations"] = _affiliation_names(insts)
    p["department"] = _clean((a.get("last_known_institutions") or [{}])[0].get("department"), 120) or ""
    p["works_count"] = _int(a.get("works_count"))
    p["citations"] = _int(a.get("cited_by_count"))
    stats = a.get("summary_stats") or {}
    p["h_index"] = _int(stats.get("h_index"))
    p["i10_index"] = _int(stats.get("i10_index"))
    p["topics"] = [{"name": _clean(t.get("display_name"), 80),
                    "share": t.get("works_count")}
                   for t in (a.get("topics") or [])[:6] if t.get("display_name")]
    counts = a.get("counts_by_year") or []
    if counts:
        p["oa_works"] = None
    return p


def oa_search(query, email=None, limit=25):
    """Search OpenAlex authors."""
    try:
        r = _session(email).get(
            f"{OA}/authors",
            params={"search": query, "per-page": max(1, min(limit, 50)), **_mailto(email)},
            timeout=TIMEOUT)
        if r.status_code == 429:
            return [], "OpenAlex rate limit — wait a moment and retry"
        r.raise_for_status()
        data = r.json()
        return [_oa_author(a) for a in data.get("results", [])], None
    except requests.RequestException as e:
        return [], f"OpenAlex unavailable ({type(e).__name__})"


def oa_works(author_id, email=None, limit=200):
    """Fetch an author's works from OpenAlex (cursor-free, capped)."""
    aid = str(author_id).rsplit("/", 1)[-1]
    try:
        r = _session(email).get(
            f"{OA}/works",
            params={"filter": f"author.id:{aid}", "per-page": min(limit, 200),
                    "mailto": (email or MAILTO)},
            timeout=TIMEOUT + 15)
        r.raise_for_status()
        out = []
        for w in r.json().get("results", []):
            loc = (w.get("primary_location") or {}) or {}
            src = (loc.get("source") or {}) or {}
            doi = (w.get("doi") or "")
            doi = re.sub(r"^https?://(dx\.)?doi\.org/", "", doi, flags=re.I) or None
            auths = [a.get("author", {}).get("display_name")
                     for a in (w.get("authorships") or [])]
            out.append({
                "doi": doi,
                "title": _clean(w.get("title") or w.get("display_name"), 400),
                "authors": [a for a in auths if a],
                "year": _int(w.get("publication_year")),
                "journal": _clean((src.get("display_name")), 200),
                "cited_by": _int(w.get("cited_by_count")),
                "is_oa": bool((w.get("open_access") or {}).get("is_oa")),
                "oa_status": _clean((w.get("open_access") or {}).get("oa_status"), 40),
                "type": _clean(w.get("type"), 40),
                "pdf_url": _clean((loc.get("pdf_url")), 500),
                "landing": _clean(loc.get("landing_page_url"), 500),
                "publisher": _clean(src.get("host_organization_name"), 120),
            })
        return out, None
    except requests.RequestException as e:
        return [], f"OpenAlex works unavailable ({type(e).__name__})"


# ── ORCID ────────────────────────────────────────────────────────────────────
ORCID = "https://pub.orcid.org/v3.0"
ORCID_ACCEPT = "application/json"


_ORG_WORDS = (
    "dept", "dep", "department", "univ", "university", "institute", "inst",
    "school", "faculty", "college", "academy", "centre", "center", "lab",
    "laboratory", "hospital", "foundation", "assoc", "association", "society",
    "of", "and", "the", "for", "at", "in", "on",
)


def _orcid_query(query):
    """Translate a plain name into ORCID's precise expanded-search syntax.

    ORCID treats a bare string as a fuzzy match across every field, so
    searching "Amine Zouaghi" returns unrelated people. When the query looks
    like a personal name, use ``given-names:`` / ``family-name:`` instead;
    anything already containing a field prefix or a DOI is passed through
    untouched.
    """
    q = query.strip()
    if "://" in q:
        q = q.rsplit("/", 1)[-1]
    q = q.strip()
    if _norm_orcid(q):
        return f"orcid:{_norm_orcid(q)}"
    if re.search(r"[a-z-]+:", q):          # already uses ORCID field syntax
        return q
    if re.search(r"[@/]|https?:", q):      # an email, DOI or affiliation phrase
        return q

    # "Family, Given Middle" is unambiguous, so it is handled before the
    # token-count cases below — otherwise a two-token "Family, Given" would be
    # split and swapped. An affiliation like "Dept. of Math, University of
    # Parma" also contains a comma but is not a personal name, so it is left
    # alone rather than queried backwards.
    if "," in q:
        family, _, given = q.partition(",")
        family_tokens = [t for t in re.split(r"\s+", family.strip()) if t]
        if family_tokens and not any(
                re.search(r"\b(" + "|".join(_ORG_WORDS) + r")\b", t, re.I)
                for t in family_tokens):
            return (f"given-names:{given.strip()} AND "
                    f"family-name:{family.strip()}")
        return q

    parts = [p for p in re.split(r"\s+", q) if p]
    if len(parts) == 1:
        return f"given-names:{parts[0]} AND family-name:{parts[0]}"
    if len(parts) == 2:
        return f"given-names:{parts[0]} AND family-name:{parts[1]}"
    # "First Middle Last" — assume the first token is the given name and
    # everything after it is the family name.
    return f"given-names:{parts[0]} AND family-name:{' '.join(parts[1:])}"


def orcid_search(query, email=None, limit=25):
    """Search ORCID public API.

    Supports a bare name, an ORCID, or ORCID's own ``field:value`` syntax.
    A plain name is upgraded to field syntax by :func:`_orcid_query` so the
    results are actual name matches rather than fuzzy noise.
    """
    headers = {"Accept": ORCID_ACCEPT}
    params = {"q": _orcid_query(query), "rows": max(1, min(limit, 50))}
    try:
        r = requests.get(f"{ORCID}/expanded-search/", params=params,
                         headers={**headers, "User-Agent": UA}, timeout=TIMEOUT)
        if r.status_code == 404:
            return [], "ORCID found no match"
        r.raise_for_status()
        results = (r.json() or {}).get("expanded-result") or []
        out = []
        for item in results:
            p = blank_profile()
            p["source"] = "ORCID"
            p["source_id"] = str(item.get("orcid-id") or "")
            p["key"] = f"orcid:{p['source_id']}"
            name = " ".join(x for x in [item.get("given-names"),
                                        item.get("family-name")] if x)
            p["name"] = _clean(name, 200) or "(no name)"
            p["orcid"] = _norm_orcid(p["source_id"]) or p["source_id"]
            affs = item.get("affiliation-org-name") or {}
            vals = affs if isinstance(affs, list) else ([affs] if affs else [])
            p["affiliations"] = _affiliation_names(
                [{"institution": v} for v in vals if v])
            p["works_count"] = _int(item.get("work-count"))
            out.append(p)
        return out, None
    except requests.RequestException as e:
        return [], f"ORCID unavailable ({type(e).__name__})"


def orcid_record(orcid_id, email=None):
    """Fetch one ORCID record: identity plus claimed works."""
    oid = _norm_orcid(orcid_id)
    if not oid:
        return None, "Not a valid ORCID iD"
    try:
        r = requests.get(f"{ORCID}/{oid}/record", headers={"Accept": ORCID_ACCEPT,
                                                          "User-Agent": UA},
                         timeout=TIMEOUT)
        if r.status_code == 404:
            return None, f"ORCID {oid} not found"
        r.raise_for_status()
        data = r.json() or {}

        person = ((data.get("person") or {}).get("name") or {})
        given = ((person.get("given-names") or {}).get("value"))
        family = ((person.get("family-name") or {}).get("value"))
        p = blank_profile()
        p["source"] = "ORCID"
        p["source_id"] = oid
        p["key"] = f"orcid:{oid}"
        p["name"] = _clean(f"{given or ''} {family or ''}".strip(), 200) or "(no name)"
        p["orcid"] = oid
        p["homepage"] = f"https://orcid.org/{oid}"

        employ = ((data.get("activities-summary") or {}).get("employments") or {})
        affs = []
        for group in (employ.get("affiliation-group") or []):
            for s in (group.get("summaries") or []):
                e = ((s.get("employment-summary") or {}).get("organization") or {})
                nm = e.get("name")
                if isinstance(nm, str):
                    affs.append({"institution": nm})
                elif isinstance(nm, dict):
                    affs.append({"institution": nm.get("value")})
        p["affiliations"] = _affiliation_names(affs)

        keywords = []
        for group in (data.get("person", {}).get("keywords") or {}).get("keyword", []) or []:
            v = (group or {}).get("content")
            if v:
                keywords.append({"name": _clean(v, 60), "share": None})
        p["topics"] = keywords[:8]

        works = ((data.get("activities-summary") or {}).get("works") or {}).get("group") or []
        out = []
        for g in works:
            summaries = g.get("work-summary") or []
            s = summaries[0] if summaries else {}
            title = (((s.get("title") or {}).get("title") or {}).get("value"))
            ext = None
            for eid in (s.get("external-ids") or {}).get("external-id", []) or []:
                if (eid or {}).get("external-id-type") == "doi":
                    ext = (eid or {}).get("external-id-value")
                    break
            year = None
            for pd in ((s.get("publication-date") or {}).get("year") or {}), :
                pass
            yv = ((s.get("publication-date") or {}).get("year") or {}).get("value")
            year = _int(yv)
            out.append({
                "doi": _norm_doi(ext) or None,
                "title": _clean(title, 400),
                "authors": [p["name"]],
                "year": year,
                "journal": None,
                "cited_by": None,
                "is_oa": "",
                "oa_status": "",
                "type": _clean(((s.get("type") or "")), 40),
                "pdf_url": None,
                "landing": None,
                "publisher": None,
                "source": "ORCID",
            })
        p["works"] = out
        p["works_count"] = len(out) or None
        return p, None
    except requests.RequestException as e:
        return None, f"ORCID unavailable ({type(e).__name__})"


# ── Semantic Scholar ─────────────────────────────────────────────────────────
SS = "https://api.semanticscholar.org/graph/v1"
SS_FIELDS = "name,affiliations,paperCount,citationCount,hIndex,url"


def ss_search(query, email=None, limit=25, api_key=None):
    """Search Semantic Scholar authors. Keyless calls are often rate limited."""
    try:
        r = requests.get(f"{SS}/author/search",
                         params={"query": query, "limit": max(1, min(limit, 100)),
                                 "fields": SS_FIELDS},
                         headers={"User-Agent": UA,
                                  **({"x-api-key": api_key} if api_key else {})},
                         timeout=TIMEOUT)
        if r.status_code == 429:
            return [], ("Semantic Scholar rate limit — add an API key in the "
                        "sidebar or try again shortly")
        r.raise_for_status()
        out = []
        for a in r.json().get("data", []):
            p = blank_profile()
            p["source"] = "Semantic Scholar"
            p["source_id"] = str(a.get("authorId") or "")
            p["key"] = f"s2:{p['source_id']}"
            p["name"] = _clean(a.get("name"), 200)
            p["affiliations"] = _affiliation_names(a.get("affiliations"))
            p["works_count"] = _int(a.get("paperCount"))
            p["citations"] = _int(a.get("citationCount"))
            p["h_index"] = _int(a.get("hIndex"))
            p["homepage"] = a.get("url")
            out.append(p)
        return out, None
    except requests.RequestException as e:
        return [], f"Semantic Scholar unavailable ({type(e).__name__})"


def ss_works(author_id, email=None, limit=100, api_key=None):
    try:
        r = requests.get(
            f"{SS}/author/{author_id}/papers",
            params={"limit": min(limit, 100),
                    "fields": "title,year,venue,citationCount,externalIds,openAccessPdf,publicationTypes"},
            headers={"User-Agent": UA,
                     **({"x-api-key": api_key} if api_key else {})},
            timeout=TIMEOUT + 15)
        r.raise_for_status()
        out = []
        for w in r.json().get("data", []):
            ext = w.get("externalIds") or {}
            oa = w.get("openAccessPdf") or {}
            out.append({
                "doi": _norm_doi(ext.get("DOI")),
                "title": _clean(w.get("title"), 400),
                "authors": [],
                "year": _int(w.get("year")),
                "journal": _clean(w.get("venue"), 200),
                "cited_by": _int(w.get("citationCount")),
                "is_oa": "yes" if oa.get("url") else "",
                "oa_status": "gold" if oa.get("url") else "",
                "type": _clean(", ".join(w.get("publicationTypes") or []), 60),
                "pdf_url": _clean(oa.get("url"), 500),
                "landing": None,
                "publisher": None,
                "source": "Semantic Scholar",
            })
        return out, None
    except requests.RequestException as e:
        return [], f"Semantic Scholar works unavailable ({type(e).__name__})"


# ── Aggregate search ─────────────────────────────────────────────────────────
SOURCES = {
    "openalex": "OpenAlex",
    "orcid": "ORCID",
    "s2": "Semantic Scholar",
}


def search(query, sources=("openalex", "orcid", "s2"), per_source=15,
           email=None, s2_key=None):
    """Search several identity sources at once.

    Returns ``(profiles, notes)``. *profiles* is a de-duplicated list where the
    richest record for each ORCID wins, so a person found by all three sources
    appears once with the union of their fields.
    """
    query = (query or "").strip()
    if not query:
        return [], []

    notes = []
    collected = []

    def run(name):
        if name == "openalex":
            return oa_search(query, email, per_source)
        if name == "orcid":
            return orcid_search(query, email, per_source)
        if name == "s2":
            return ss_search(query, email, per_source, s2_key)
        return [], f"unknown source {name}"

    with ThreadPoolExecutor(max_workers=min(3, len(sources) or 1)) as ex:
        futs = {ex.submit(run, s): s for s in sources if s in SOURCES}
        for fut in as_completed(futs):
            name = futs[fut]
            try:
                res, err = fut.result()
            except Exception as exc:  # never let one source sink the search
                res, err = [], f"{SOURCES.get(name, name)} failed ({type(exc).__name__})"
            collected.extend(res)
            if err:
                notes.append(err)

    return _merge(collected), notes


def _richness(p):
    return sum(1 for f in ("orcid", "works_count", "citations", "h_index",
                           "affiliations", "homepage", "topics") if p.get(f))


def _merge(profiles):
    """Collapse duplicates by ORCID, else by normalised name."""
    by_key: dict = {}
    order = []
    for p in profiles:
        ident = f"orcid:{p['orcid']}" if p.get("orcid") else \
               f"name:{(p.get('name') or '').lower().strip()}"
        if not p.get("name") and not p.get("orcid"):
            continue
        if ident in by_key:
            cur = by_key[ident]
            if _richness(p) > _richness(cur):
                merged = dict(p)
                merged["also_found_in"] = sorted(set(cur.get("also_found_in", [])
                                                     + [cur["source"]]) - {p["source"]})
                for f in ("orcid", "citations", "h_index", "works_count",
                          "affiliations", "homepage", "topics"):
                    if not merged.get(f) and cur.get(f):
                        merged[f] = cur[f]
                by_key[ident] = merged
            else:
                cur["also_found_in"] = sorted(set(cur.get("also_found_in", [])
                                                 + [p["source"]]) - {cur["source"]})
        else:
            p["also_found_in"] = []
            by_key[ident] = p
            order.append(ident)

    out = [by_key[k] for k in order]
    out.sort(key=lambda p: (-(p.get("citations") or 0), p.get("name") or ""))
    return out


def fetch_details(profile, email=None, s2_key=None, work_limit=200):
    """Fill in ``works`` for a profile, from whichever source owns it."""
    src, sid = profile.get("source"), profile.get("source_id")
    works, err = [], None
    if src == "OpenAlex":
        works, err = oa_works(sid, email, work_limit)
    elif src == "ORCID":
        rec, err = orcid_record(sid, email)
        if rec:
            works = rec.get("works") or []
    elif src == "Semantic Scholar":
        works, err = ss_works(sid, email, min(work_limit, 100), s2_key)

    if works:
        works.sort(key=lambda w: (-(w.get("year") or 0), -(w.get("cited_by") or 0)))
        profile = dict(profile)
        profile["works"] = works
        profile["works_count"] = len(works) if len(works) > (profile.get("works_count") or 0) \
            else profile.get("works_count")
        if profile.get("citations") is None:
            profile["citations"] = sum(w.get("cited_by") or 0 for w in works)
        if profile.get("h_index") is None:
            profile["h_index"] = _h_index([w.get("cited_by") or 0 for w in works])
    return profile, err


def _h_index(citations):
    counts = sorted((c for c in citations if c), reverse=True)
    h = 0
    for i, c in enumerate(counts, 1):
        if c >= i:
            h = i
        else:
            break
    return h or None


# ── Saved profile store ──────────────────────────────────────────────────────
def _read_store():
    try:
        if STORE.exists():
            data = json.loads(STORE.read_text())
            if isinstance(data, list):
                return data
    except Exception:
        pass
    return []


def _write_store(items):
    STORE.parent.mkdir(parents=True, exist_ok=True)
    tmp = STORE.with_suffix(".tmp")
    tmp.write_text(json.dumps(items, indent=1, default=str))
    tmp.replace(STORE)


def list_saved():
    """All saved profiles, newest first."""
    with _STORE_LOCK:
        items = _read_store()
    items.sort(key=lambda p: p.get("saved_at") or 0, reverse=True)
    return items


def save_profile(profile, note=""):
    """Add or update a profile in the local store (keyed by ORCID or name)."""
    ident = profile.get("orcid") or (profile.get("name") or "").lower().strip()
    if not ident:
        return False, "Profile has no name or ORCID to identify it."
    with _STORE_LOCK:
        items = _read_store()
        entry = {k: v for k, v in profile.items() if k != "works"}
        entry["works"] = profile.get("works") or []
        entry["note"] = note
        entry["saved_at"] = time.time()
        for i, existing in enumerate(items):
            e_id = existing.get("orcid") or (existing.get("name") or "").lower().strip()
            if e_id == ident:
                entry["saved_at"] = existing.get("saved_at") or entry["saved_at"]
                items[i] = entry
                _write_store(items)
                return True, "Updated."
        items.append(entry)
        _write_store(items)
    return True, "Saved."


def remove_profile(ident):
    ident = (ident or "").strip()
    with _STORE_LOCK:
        items = _read_store()
        keep = []
        removed = False
        for existing in items:
            e_id = existing.get("orcid") or (existing.get("name") or "").lower().strip()
            if e_id == ident or existing.get("key") == ident:
                removed = True
                continue
            keep.append(existing)
        if removed:
            _write_store(keep)
    return removed


def saved_works():
    """Every work across every saved profile, with a `profile` column."""
    rows = []
    for p in list_saved():
        for w in p.get("works") or []:
            rec = dict(w)
            rec["profile"] = p.get("name")
            rec["profile_orcid"] = p.get("orcid")
            rows.append(rec)
    return rows