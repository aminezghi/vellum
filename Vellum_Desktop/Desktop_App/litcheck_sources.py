"""
Literature-search source adapters.

Every adapter turns one bibliographic database into the SAME canonical record
dict, so results from twelve sources can be pooled, deduplicated and exported as
one table. Adapters return (records, info) where info carries the real
hit-count reported by the database plus any truncation warnings.

Design rules learned from the live APIs:
  * Every source caps how deep it will page. Adapters report `truncated`
    rather than silently returning a partial answer as if it were complete.
  * Sources that need a key are still registered: they report `status="needs key"`
    instead of disappearing, so a reviewer can see exactly what was skipped.
  * Nothing raises out of an adapter. Failures come back as a status so one dead
    source never sinks a multi-source search.
"""

from __future__ import annotations

import html
import json
import re
import time
import urllib.parse as _up
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests

UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")
API_UA = "PDF-Downloader-Research-App/2.0 (mailto:{email})"

TIMEOUT = 45


# ── helpers ────────────────────────────────────────────────────────────────

def _clean(s, limit=0):
    if s is None:
        return None
    s = str(s)
    s = s.replace("﻿", "").replace("", "")
    s = re.sub(r"<[^>]+>", " ", s)
    s = html.unescape(s)
    s = re.sub(r"\s+", " ", s).strip()
    if limit and len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s or None


def _norm_doi(d):
    if not d:
        return None
    d = str(d).strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I)
    d = re.sub(r"^doi:\s*", "", d, flags=re.I)
    return d.lower().strip().rstrip(".") or None


def _year_of(item, *paths):
    for path in paths:
        cur = item
        for key in path:
            if isinstance(cur, dict):
                cur = cur.get(key)
            elif isinstance(cur, list) and cur:
                cur = cur[0]
            else:
                cur = None
                break
        if cur:
            m = re.search(r"(19|20)\d{2}", str(cur))
            if m:
                return int(m.group(0))
    return None


def _get(session, url, params=None, headers=None, tries=3, backoff=1.6,
         expect_json=True, timeout=None):
    """GET with retry on 429/5xx and honour for Retry-After."""
    last = None
    tmo = timeout or TIMEOUT
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, headers=headers, timeout=tmo)
        except Exception as exc:                      # network hiccup
            last = f"{type(exc).__name__}: {exc}"
            time.sleep(backoff ** attempt)
            continue
        if r.status_code == 200:
            if expect_json:
                try:
                    return r.json()
                except Exception:
                    last = "bad JSON"
                    time.sleep(backoff ** attempt)
                    continue
            return r
        if r.status_code in (429, 500, 502, 503, 504):
            ra = r.headers.get("Retry-After")
            wait = float(ra) if (ra or "").isdigit() else backoff ** (attempt + 1)
            last = f"HTTP {r.status_code}"
            time.sleep(min(wait, 30))
            continue
        return {"__error__": f"HTTP {r.status_code}: {r.text[:180]}"}
    return {"__error__": last or "request failed"}


def _session(email):
    s = requests.Session()
    s.headers.update({"User-Agent": API_UA.format(email=email or "anonymous"),
                      "Accept": "application/json"})
    return s


def _blank(src):
    return {
        "doi": None, "title": None, "authors": [], "year": None,
        "publication_date": None, "epub_date": None, "journal": None,
        "abstract": None,
        "keywords": [], "type": None, "language": None, "issn": [],
        "volume": None, "issue": None, "pages": None, "cited_by": None,
        "is_oa": None, "oa_status": None, "pdf_url": None, "landing_url": None,
        "pmid": None, "pmcid": None, "arxiv_id": None, "openalex_id": None,
        "source": src,
    }


def _invert_abstract(idx):
    """OpenAlex ships no abstract text, only a word -> positions map."""
    if not isinstance(idx, dict) or not idx:
        return None
    slots = {}
    for word, positions in idx.items():
        for p in positions:
            slots[p] = word
    if not slots:
        return None
    n = max(slots) + 1
    return " ".join(slots.get(i, "") for i in range(n)).strip() or None


# ── OpenAlex ───────────────────────────────────────────────────────────────

def _oa_year(w):
    dp = w.get("publication_date") or ""
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", dp)
    if m:
        return int(m.group(1)), dp
    py = w.get("publication_year")
    return (int(py), f"{py}-01-01" if py else None)


def _oa_record(w, src="openalex"):
    r = _blank(src)
    r["openalex_id"] = (w.get("id") or "").rsplit("/", 1)[-1] or None
    r["doi"] = _norm_doi(w.get("doi") or (w.get("ids") or {}).get("doi"))
    r["title"] = _clean(w.get("title") or w.get("display_name"), 600)
    auth = []
    for a in (w.get("authorships") or []):
        nm = _clean((a.get("author") or {}).get("display_name"), 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth
    y, dp = _oa_year(w)
    r["year"], r["publication_date"] = y, dp
    pl = w.get("primary_location") or {}
    src_obj = pl.get("source") or {}
    r["journal"] = _clean(src_obj.get("display_name"), 300)
    r["issn"] = [i for i in ([src_obj.get("issn"), src_obj.get("issn_l")] or []) if i]
    oa = w.get("open_access") or {}
    r["is_oa"] = oa.get("is_oa")
    r["oa_status"] = oa.get("oa_status")
    r["landing_url"] = _clean(pl.get("landing_page_url"), 500)
    # best_oa_location first, then any location carrying a pdf_url
    cands = []
    best = w.get("best_oa_location") or {}
    if best.get("pdf_url"):
        cands.append(best["pdf_url"])
    for loc in (w.get("locations") or []):
        if loc.get("pdf_url"):
            cands.append(loc["pdf_url"])
    if oa.get("oa_url"):
        cands.append(oa["oa_url"])
    for c in cands:
        if c and not str(c).startswith("https://doi.org/"):
            r["pdf_url"] = _clean(c, 500)
            break
    else:
        r["pdf_url"] = _clean(cands[0], 500) if cands else None
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    r["abstract"] = _clean(_invert_abstract(w.get("abstract_inverted_index")), 4000)
    kws = []
    for t in (w.get("topics") or [])[:12]:
        d = _clean(t.get("display_name"), 80)
        if d:
            kws.append(d)
    r["keywords"] = kws
    r["type"] = w.get("type")
    r["language"] = w.get("language")
    b = w.get("biblio") or {}
    r["volume"], r["issue"], r["pages"] = b.get("volume"), b.get("issue"), b.get("first_page")
    r["cited_by"] = w.get("cited_by_count")
    ids = w.get("ids") or {}
    r["pmid"] = str(ids.get("pmid", "")).rsplit("/", 1)[-1] or None
    r["pmcid"] = str(ids.get("pmcid", "")).rsplit("/", 1)[-1] or None
    return r


def search_openalex(query, *, year_from=None, year_to=None, oa_only=False,
                    doc_types=None, language=None, min_citations=None,
                    is_retracted_excluded=True, has_fulltext=None,
                    per_source=200, max_records=1000, key=None, email=None):
    s = _session(email)
    out, cursor, fetched, cap = [], "*", 0, min(per_source, 100)
    info = {"source": "openalex", "reported": None, "truncated": False}
    params = {"per_page": cap, "cursor": cursor,
              "mailto": email} if email else {"per_page": cap, "cursor": cursor}
    if key:
        params["api_key"] = key
    if query:
        params["search"] = query
    flt = []
    if year_from and year_to:
        flt.append(f"publication_year:{year_from}-{year_to}")
    elif year_from:
        flt.append(f"publication_year:>{year_from - 1}")
    elif year_to:
        flt.append(f"publication_year:<{year_to + 1}")
    if oa_only:
        flt.append("is_oa:true")
    if doc_types:
        flt.append("type:" + "|".join(doc_types))
    if language:
        flt.append(f"language:{language}")
    if min_citations:
        flt.append(f"cited_by_count:>{min_citations}")
    if is_retracted_excluded:
        flt.append("is_retracted:false")
    if has_fulltext:
        flt.append("has_pdf_url:true")
    if flt:
        params["filter"] = ",".join(flt)
    while cursor is not None and fetched < max_records:
        params["cursor"] = cursor
        d = _get(s, "https://api.openalex.org/works", params=params)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        meta = d.get("meta") or {}
        info["reported"] = meta.get("count")
        for w in (d.get("results") or []):
            out.append(_oa_record(w))
            if len(out) >= max_records:
                break
        fetched += len(d.get("results") or [])
        cursor = meta.get("next_cursor")
        if not d.get("results"):
            break
        if fetched >= max_records or fetched >= (info["reported"] or 0):
            cursor = None
    if cursor:
        info["truncated"] = True
    return out, info


# ── Crossref ───────────────────────────────────────────────────────────────

_XREF_TYPES = {
    "journal-article": "journal-article", "book": "book", "book-chapter": "book-chapter",
    "proceedings-article": "proceedings-article", "dissertation": "dissertation",
    "report": "report", "dataset": "dataset", "posted-content": "posted-content",
}


def _xref_record(it):
    r = _blank("crossref")
    r["doi"] = _norm_doi(it.get("DOI"))
    r["title"] = _clean((it.get("title") or [None])[0], 600)
    auth = []
    for a in (it.get("author") or []):
        nm = _clean(" ".join(x for x in [a.get("given"), a.get("family")] if x), 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth
    dp = ((it.get("published") or it.get("issued") or {}).get("date-parts") or [[]])[0]
    if dp:
        r["year"] = int(dp[0]) if re.match(r"^(19|20)\d{2}$", str(dp[0])) else None
        try:
            r["publication_date"] = "-".join(
                [f"{dp[0]:04d}"] + [f"{int(x):02d}" for x in dp[1:3]]).strip("-")
        except Exception:
            r["publication_date"] = str(dp[0])
    r["journal"] = _clean((it.get("container-title") or [None])[0], 300)
    r["issn"] = list(it.get("ISSN") or [])
    r["volume"], r["issue"] = it.get("volume"), it.get("issue")
    r["pages"] = _clean(it.get("page"), 60)
    r["type"] = it.get("type")
    r["cited_by"] = it.get("is-referenced-by-count")
    r["language"] = it.get("language")
    r["abstract"] = _clean(it.get("abstract"), 4000)
    r["keywords"] = [k for k in map(_clean, it.get("subject") or []) if k][:12]
    r["landing_url"] = _clean(it.get("URL"), 500)
    r["oa_status"] = None
    for lk in (it.get("link") or []):
        if lk.get("content-type") == "application/pdf":
            r["pdf_url"] = _clean(lk.get("URL"), 500)
            r["is_oa"] = True
            break
    if r["doi"] and not r["landing_url"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


def search_crossref(query, *, year_from=None, year_to=None, doc_types=None,
                    issn=None, has_abstract=None, min_citations=None,
                    per_source=200, max_records=1000, key=None, email=None):
    s = _session(email)
    info = {"source": "crossref", "reported": None, "truncated": False}
    if key:
        s.headers["Crossref-Plus-API-Token"] = f"Bearer {key}"
    rows = min(per_source, 1000)
    out, offset = [], 0
    while len(out) < max_records and offset < 10000:
        params = {"rows": rows, "offset": offset,
                  "query.bibliographic": query or "",
                  "select": ("DOI,title,author,container-title,issued,published,"
                             "abstract,type,volume,issue,page,ISSN,is-referenced-by-count,"
                             "link,URL,subject")}
        if email:
            params["mailto"] = email
        flt = []
        if year_from:
            flt.append(f"from-pub-date:{year_from}-01-01")
        if year_to:
            flt.append(f"until-pub-date:{year_to}-12-31")
        if doc_types:
            good = [_XREF_TYPES.get(t, t) for t in doc_types]
            good = [g for g in good if g in
                    ("journal-article", "book", "book-chapter", "proceedings-article",
                     "dissertation", "report", "dataset", "posted-content")]
            if good:
                flt.append("type:" + "|".join(good))
        if issn:
            flt.append("issn:" + issn)
        if has_abstract:
            flt.append("has-abstract:1")
        if flt:
            params["filter"] = ",".join(flt)
        if min_citations:
            # Crossref has no citation-count filter; sort instead and cut client side
            params["sort"] = "is-referenced-by-count"
            params["order"] = "desc"
        d = _get(s, "https://api.crossref.org/works", params=params)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        msg = d.get("message") or {}
        info["reported"] = msg.get("total-results")
        items = msg.get("items") or []
        for it in items:
            rec = _xref_record(it)
            if min_citations and (rec["cited_by"] or 0) < min_citations:
                continue
            out.append(rec)
            if len(out) >= max_records:
                break
        if not items:
            break
        offset += rows
        if offset >= (info["reported"] or 0):
            info["truncated"] = False
            break
    else:
        info["truncated"] = True
    return out, info


# ── Europe PMC ─────────────────────────────────────────────────────────────

def _epmc_record(res, src="europepmc"):
    r = _blank(src)
    r["doi"] = _norm_doi(res.get("doi"))
    r["title"] = _clean(res.get("title"), 600)
    auth = []
    for a in ((res.get("authorList") or {}).get("author") or []):
        nm = _clean(a.get("fullName") or " ".join(
            x for x in [a.get("firstName"), a.get("lastName")] if x), 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth
    ji = res.get("journalInfo") or {}
    r["year"] = ji.get("yearOfPublication") or _year_of(res, ("pubYear",))
    j = ji.get("journal") or {}
    r["journal"] = _clean(j.get("title") or res.get("bookOrReportDetails", {}).get("publisher"), 300)
    if j.get("journalIssn"):
        r["issn"] = [j["journalIssn"]]
    r["volume"], r["issue"] = ji.get("volume"), ji.get("issue")
    r["pages"] = _clean(res.get("pageInfo"), 60)
    r["abstract"] = _clean(res.get("abstractText"), 4000)
    kws = [k for k in ((res.get("keywordList") or {}).get("keyword") or []) if k]
    r["keywords"] = [str(k)[:80] for k in kws][:15]
    mesh = [m.get("descriptorName") for m in
            ((res.get("meshHeadingList") or {}).get("meshHeading") or [])
            if m.get("descriptorName")]
    r["type"] = (mesh or [None])[0]
    if r["doi"] and r["doi"].endswith(".pdf"):
        r["doi"] = r["doi"][:-4]
    r["pmid"] = res.get("pmid")
    r["pmcid"] = res.get("pmcid")
    r["is_oa"] = res.get("isOpenAccess") == "Y"
    r["landing_url"] = None
    if res.get("pmcid"):
        r["landing_url"] = f"https://europepmc.org/article/PMC/{res['pmcid']}"
    elif r["pmid"]:
        r["landing_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{r['pmid']}/"
    elif r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    for u in ((res.get("fullTextUrlList") or {}).get("fullTextUrl") or []):
        if str(u.get("documentStyle", "")).lower() == "pdf":
            r["pdf_url"] = _clean(u.get("url"), 500)
            break
    return r


def search_europepmc(query, *, year_from=None, year_to=None, doc_types=None,
                     oa_only=False, has_fulltext=False, per_source=200,
                     max_records=1000, key=None, email=None):
    s = _session(email)
    info = {"source": "europepmc", "reported": None, "truncated": False}
    q = _epmc_query(query, year_from, year_to, doc_types, oa_only, has_fulltext)
    cursor, fetched, out = "*", 0, []
    page = min(per_source, 1000)
    while cursor and fetched < max_records:
        params = {"query": q, "format": "json", "resultType": "core",
                  "pageSize": page, "cursorMark": cursor}
        d = _get(s, "https://www.ebi.ac.uk/europepmc/webservices/rest/search",
                 params=params)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        info["reported"] = int((d.get("hitCount") or 0))
        results = ((d.get("resultList") or {}).get("result") or [])
        for res in results:
            rec = _epmc_record(res)
            if rec["title"]:
                out.append(rec)
        fetched += len(results)
        nxt = d.get("nextCursorMark")
        cursor = nxt if nxt and results else None
    if cursor:
        info["truncated"] = True
    return out[:max_records], info


def _epmc_query(query, y_from, y_to, types, oa_only, has_fulltext):
    parts = [f"({query})"] if query else []
    if y_from and y_to:
        parts.append(f"(PUB_YEAR:[{y_from} TO {y_to}])")
    elif y_from:
        parts.append(f"(PUB_YEAR:[{y_from} TO 3000])")
    elif y_to:
        parts.append(f"(PUB_YEAR:[1500 TO {y_to}])")
    if types:
        tmap = {"journal-article": "JOURNAL", "preprint": "PREPRINT",
                "book": "BOOK", "book-chapter": "BOOK_CHAPTER",
                "dissertation": "THESIS", "conference-paper": "CONFERENCE",
                "dataset": "DATASET", "review": "REVIEW"}
        vals = [tmap.get(t, t.upper().replace("-", "_")) for t in types]
        parts.append("(" + " OR ".join(vals) + ")")
    if oa_only:
        parts.append("(OPEN_ACCESS:Y)")
    if has_fulltext:
        parts.append("(HAS_FTP:Y)")
    return " AND ".join(parts) if parts else "*"


def _pubmed_query(query, y_from, y_to, oa_only):
    """PubMed does NOT accept Europe PMC syntax: ranges are `2020:2024[dp]`."""
    parts = [f"({query})"] if query else []
    if y_from and y_to:
        parts.append(f'("{y_from}"[PDAT] : "{y_to}"[PDAT])')
    elif y_from:
        parts.append(f'("{y_from}"[PDAT] : "3000"[PDAT])')
    elif y_to:
        parts.append(f'("1500"[PDAT] : "{y_to}"[PDAT])')
    if oa_only:
        parts.append('("free full text"[Filter])')
    return " AND ".join(parts) if parts else "*"


# ── PubMed ─────────────────────────────────────────────────────────────────

def search_pubmed(query, *, year_from=None, year_to=None, oa_only=False,
                  per_source=200, max_records=1000, key=None, email=None):
    s = _session(email)
    info = {"source": "pubmed", "reported": None, "truncated": False}
    q = _pubmed_query(query, year_from, year_to, oa_only)
    kp = {"db": "pubmed", "term": q, "retmax": min(per_source, 10000),
          "retmode": "json"}
    if key:
        kp["api_key"] = key
        if email:
            kp["email"] = email
        s.headers["Accept"] = "application/json"
    d = _get(s, "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi", params=kp)
    if "__error__" in d:
        info["status"] = d["__error__"]
        return [], info
    res = (d.get("esearchresult") or {})
    ids = res.get("idlist") or []
    info["reported"] = int(res.get("count") or 0)
    if not ids:
        return [], info
    if len(ids) > max_records:
        info["truncated"] = True
    ids = ids[:max_records]
    out = []
    # efetch in batches of 200 returns the abstract, esummary does not
    for i in range(0, len(ids), 200):
        batch = ids[i:i + 200]
        p = {"db": "pubmed", "id": ",".join(batch), "retmode": "xml"}
        if key:
            p["api_key"] = key
        if email:
            p["email"] = email
        xml = _get(s, "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
                   params=p, expect_json=False)
        try:
            root = ET.fromstring(xml.content)
        except Exception:
            continue
        for art in root.findall(".//PubmedArticle"):
            out.append(_pubmed_record(art))
    return [r for r in out if r["title"]], info


def _pubmed_record(art):
    r = _blank("pubmed")
    med = art.find(".//MedlineCitation")
    a = med.find("Article") if med is not None else None
    if a is None:
        return r
    r["title"] = _clean("".join(a.find("ArticleTitle").itertext())
                        if a.find("ArticleTitle") is not None else None, 600)
    auth = []
    for au in a.findall(".//Author"):
        ln = au.findtext("LastName")
        ini = au.findtext("Initials")
        coll = au.findtext("CollectiveName")
        nm = " ".join(x for x in [ini, ln] if x) or coll
        nm = _clean(nm, 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth
    jr = a.find("Journal")
    if jr is not None:
        r["journal"] = _clean(jr.findtext("Title"), 300)
        r["volume"] = jr.findtext("JournalIssue/Volume")
        iss = jr.find("JournalIssue/Issue")
        r["issue"] = iss.text if iss is not None else None
    pd = a.find("Journal/JournalIssue/PubDate")
    if pd is not None:
        r["year"] = _year_of_text(pd.findtext("Year") or "") or \
            _year_of_text((pd.findtext("MedlineDate") or ""))
    # PubMed's own [PDAT] filter and the citation date disagree for
    # ahead-of-print articles (e.g. PMID 38239985: issue 2023, ePub 2024).
    # The issue year is what a reference list shows, so it stays primary and
    # the electronic date is kept alongside it for transparency.
    for ad in a.findall("ArticleDate"):
        y = _year_of_text(ad.findtext("Year") or "")
        if y:
            m, d0 = ad.findtext("Month"), ad.findtext("Day")
            r["epub_date"] = (f"{y}-{int(m):02d}-{int(d0):02d}"
                              if (m and d0) else str(y))
            break
    r["pages"] = _clean(a.findtext("Pagination/MedlinePgn"), 60)
    for aid in a.findall("ELocationID"):
        if aid.get("EIdType") == "doi":
            r["doi"] = _norm_doi(aid.text)
    abst = a.find("Abstract")
    if abst is not None:
        parts = []
        for t in abst.findall("AbstractText"):
            lab = t.get("Label")
            txt = "".join(t.itertext()).strip()
            parts.append(f"{lab}: {txt}" if lab else txt)
        r["abstract"] = _clean(" ".join(parts), 4000)
    for kw in a.findall(".//Keyword"):
        if kw.text:
            r["keywords"].append(kw.text[:80])
    pmid = med.findtext("PMID")
    r["pmid"] = pmid
    r["landing_url"] = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/" if pmid else None
    if not r["doi"] and pmid:
        r["doi"] = None
    return r


def _year_of_text(t):
    m = re.search(r"(19|20)\d{2}", t or "")
    return int(m.group(0)) if m else None


# ── arXiv ──────────────────────────────────────────────────────────────────

_ATX = "{http://www.w3.org/2005/Atom}"


def search_arxiv(query, *, year_from=None, year_to=None, categories=None,
                 per_source=200, max_records=1000, key=None, email=None):
    s = requests.Session()
    s.headers["User-Agent"] = API_UA.format(email=email or "anonymous")
    info = {"source": "arxiv", "reported": None, "truncated": False}
    sq = _arxiv_query(query, year_from, year_to, categories)
    out, start = [], 0
    step = min(per_source, 2000)
    while len(out) < max_records:
        params = {"search_query": sq, "start": start, "max_results": step,
                  "sortBy": "submittedDate", "sortOrder": "descending"}
        r = _get(s, "http://export.arxiv.org/api/query", params=params,
                 expect_json=False, timeout=20, tries=2, backoff=2.0)
        if isinstance(r, dict):
            info["status"] = r.get("__error__", "request failed")
            break
        try:
            root = ET.fromstring(r.content)
        except Exception as exc:
            info["status"] = f"bad XML: {exc}"
            break
        total = root.findtext("{http://a9.com/-/spec/opensearch/1.1/}totalResults")
        info["reported"] = int(total) if total else None
        entries = root.findall(f"{_ATX}entry")
        if not entries:
            break
        for e in entries:
            rec = _arxiv_record(e)
            if rec["title"]:
                out.append(rec)
        start += step
        if info["reported"] is not None and start >= info["reported"]:
            break
        if len(entries) < step:
            break
        time.sleep(1.0)
    if len(out) >= max_records and (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _arxiv_query(query, y_from, y_to, cats):
    """Clean query for arXiv: strip pubmed field tags and handle booleans properly."""
    # Strip any PubMed style tags like [Title/Abstract] or [tiab]
    q_clean = re.sub(r"\[[A-Za-z0-9_/\s-]+\]", "", query or "").strip()
    terms = _split_terms(q_clean)
    bits = []
    for t in terms:
        t_upper = t.upper()
        if t_upper in ("AND", "OR", "ANDNOT", "NOT"):
            bits.append("ANDNOT" if t_upper == "NOT" else t_upper)
        elif t.startswith(("ti:", "au:", "abs:", "cat:", "co:", "jr:", "all:")):
            bits.append(t)
        elif t.startswith('"') and t.endswith('"'):
            bits.append(f'all:{t}')
        elif t in ("(", ")"):
            bits.append(t)
        else:
            # Clean punctuation from term edge
            t_clean = t.strip("()[]")
            if t_clean:
                bits.append(f"all:{t_clean}")
    if cats:
        bits.append("AND (" + " OR ".join(f"cat:{c}" for c in cats) + ")")
    
    # Assemble query string cleanly
    q_assembled = []
    for i, b in enumerate(bits):
        if i > 0 and b not in ("AND", "OR", "ANDNOT") and bits[i-1] not in ("AND", "OR", "ANDNOT", "(") and b != ")":
            q_assembled.append("AND")
        q_assembled.append(b)
    q = " ".join(q_assembled) if q_assembled else "cat:cs.LG"

    if y_from or y_to:
        lo, hi = y_from or 1991, y_to or 3000
        q += f" AND (submittedDate:[{lo:04d}01010000 TO {hi:04d}12312359])"
    return q


def _split_terms(query):
    """Tokenise on whitespace but keep double-quoted phrases intact."""
    out, buf, inq = [], "", False
    for ch in (query or ""):
        if ch == '"':
            inq = not inq
            buf += ch
        elif ch.isspace() and not inq:
            if buf:
                out.append(buf)
                buf = ""
        else:
            buf += ch
    if buf:
        out.append(buf)
    return out


def _arxiv_record(e):
    r = _blank("arxiv")
    r["title"] = _clean(" ".join(e.findtext(f"{_ATX}title", "").split()), 600)
    r["abstract"] = _clean(e.findtext(f"{_ATX}summary"), 4000)
    auth = [_clean(a.findtext(f"{_ATX}name"), 200)
            for a in e.findall(f"{_ATX}author")]
    r["authors"] = [a for a in auth if a]
    pub = e.findtext(f"{_ATX}published") or ""
    r["year"] = _year_of_text(pub)
    r["publication_date"] = pub[:10] or None
    eid = e.findtext(f"{_ATX}id") or ""
    r["arxiv_id"] = eid.rsplit("/", 1)[-1] or None
    r["doi"] = _norm_doi(e.findtext(f"{_ATX}doi"))
    r["landing_url"] = eid
    r["pdf_url"] = f"https://arxiv.org/pdf/{r['arxiv_id']}" if r["arxiv_id"] else None
    r["is_oa"] = True
    r["oa_status"] = "green"
    jr = e.findtext(f"{_ATX}journal_ref")
    r["journal"] = _clean(jr, 300)
    cats = [c.get("term") for c in e.findall(f"{_ATX}category")]
    r["keywords"] = [c for c in cats if c][:10]
    r["type"] = "preprint"
    doi_el = e.find("{http://arxiv.org/schemas/atom}doi")
    if doi_el is not None and doi_el.text:
        r["doi"] = _norm_doi(doi_el.text)
    return r


# ── Semantic Scholar ───────────────────────────────────────────────────────

def search_semanticscholar(query, *, year_from=None, year_to=None, oa_only=False,
                           doc_types=None, min_citations=None, per_source=100,
                           max_records=400, key=None, email=None):
    s = _session(email)
    if key:
        s.headers["x-api-key"] = key
    info = {"source": "semantic_scholar", "reported": None, "truncated": False}
    if not key:
        # The keyless pool is shared and 429s constantly; back off hard and say
        # so, rather than reporting a bogus zero-result search.
        info["status"] = ("keyless rate limit — add a free Semantic Scholar API key "
                          "for reliable results")
    yq = ""
    if year_from or year_to:
        yq = f"{year_from or ''}-{year_to or ''}"
    fields = ("title,abstract,year,publicationDate,authors,venue,journal,externalIds,"
              "openAccessPdf,citationCount,publicationTypes,fieldsOfStudy,url,"
              "publicationVenue")
    out, offset = [], 0
    while len(out) < max_records:
        params = {"query": query or "", "limit": min(per_source, 100),
                  "offset": offset, "fields": fields}
        if yq:
            params["year"] = yq
        if oa_only:
            params["openAccessPdf"] = ""
        d = _get(s, "https://api.semanticscholar.org/graph/v1/paper/search",
                 params=params, tries=2)
        if "__error__" in d:
            err = d["__error__"]
            info["status"] = ("rate limited (HTTP 429) — run this source alone or add "
                              "a free API key") if "429" in err else err
            break
        info["reported"] = d.get("total")
        data = d.get("data") or []
        for it in data:
            rec = _s2_record(it)
            if oa_only and not rec["pdf_url"]:
                continue
            if min_citations and (rec["cited_by"] or 0) < min_citations:
                continue
            out.append(rec)
        if len(data) < min(per_source, 100) or "next" not in d:
            break
        offset += min(per_source, 100)
    if len(out) >= max_records and (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _s2_record(it):
    r = _blank("semantic_scholar")
    ext = it.get("externalIds") or {}
    r["doi"] = _norm_doi(ext.get("DOI"))
    r["title"] = _clean(it.get("title"), 600)
    r["authors"] = [_clean(a.get("name"), 200) for a in (it.get("authors") or [])][:60]
    r["year"] = it.get("year")
    r["publication_date"] = it.get("publicationDate")
    r["journal"] = _clean(it.get("venue") or ((it.get("journal") or {}).get("name")), 300)
    r["abstract"] = _clean(it.get("abstract"), 4000)
    oap = it.get("openAccessPdf") or {}
    r["pdf_url"] = _clean(oap.get("url"), 500)
    r["is_oa"] = bool(r["pdf_url"])
    r["oa_status"] = "green" if r["is_oa"] else None
    r["landing_url"] = _clean(it.get("url"), 500) or (
        f"https://doi.org/{r['doi']}" if r["doi"] else None)
    r["cited_by"] = it.get("citationCount")
    pt = it.get("publicationTypes") or []
    r["type"] = ("review" if "Review" in pt else
                 (pt[0].lower().replace(" ", "-") if pt else None))
    r["keywords"] = [_clean(f, 80) for f in (it.get("fieldsOfStudy") or [])][:10]
    r["arxiv_id"] = ext.get("ArXiv")
    r["pmid"] = str(ext.get("PubMed") or "") or None
    r["pmcid"] = ext.get("PubMedCentral") or None
    return r


# ── DataCite ───────────────────────────────────────────────────────────────

_DC_TYPES = {
    "journal-article": "JournalArticle", "preprint": "Preprint",
    "dataset": "Dataset", "book": "Book", "book-chapter": "BookChapter",
    "conference-paper": "ConferencePaper", "dissertation": "Dissertation",
    "report": "Report", "software": "Software", "poster": "Poster",
    "presentation": "Presentation", "other": "Text",
}


def search_datacite(query, *, year_from=None, year_to=None, doc_types=None,
                    per_source=200, max_records=1000, key=None, email=None):
    s = _session(email)
    if key:
        s.auth = (key, "")
    info = {"source": "datacite", "reported": None, "truncated": False}
    q = _datacite_query(query, year_from, year_to, doc_types)
    out, cursor = [], "1"
    size = min(per_source, 1000)
    while len(out) < max_records and cursor:
        params = {"query": q, "page[size]": size, "page[cursor]": cursor}
        d = _get(s, "https://api.datacite.org/dois", params=params)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        info["reported"] = ((d.get("meta") or {}).get("total"))
        for item in (d.get("data") or []):
            rec = _datacite_record(item)
            if rec["title"]:
                out.append(rec)
        nxt = (d.get("links") or {}).get("next")
        cursor = None if not nxt else _up.urlparse(nxt).query
    if cursor:
        info["truncated"] = True
    return out[:max_records], info


def _datacite_query(query, y_from, y_to, types):
    parts = []
    if query:
        parts.append(f'({query})')
    if y_from:
        parts.append(f"publicationYear:[{y_from} TO {y_to or 3000}]")
    elif y_to:
        parts.append(f"publicationYear:[1500 TO {y_to}]")
    if types:
        vals = [_DC_TYPES.get(t, t) for t in types]
        parts.append("types.resourceTypeGeneral:(" + " OR ".join(vals) + ")")
    return " AND ".join(parts) if parts else "*"


def _datacite_record(item):
    at = item.get("attributes") or {}
    r = _blank("datacite")
    r["doi"] = _norm_doi(at.get("doi"))
    titles = [t.get("title") for t in (at.get("titles") or []) if t.get("title")]
    r["title"] = _clean(titles[0] if titles else None, 600)
    auth = []
    for c in (at.get("creators") or []):
        nm = _clean(c.get("name") or " ".join(
            x for x in [c.get("givenName"), c.get("familyName")] if x), 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth[:60]
    r["year"] = at.get("publicationYear")
    r["publication_date"] = str(at.get("publicationYear") or "") or None
    r["journal"] = _clean(at.get("publisher"), 300)
    ty = at.get("types") or {}
    r["type"] = (ty.get("resourceTypeGeneral") or "").lower() or None
    r["language"] = at.get("language")
    r["landing_url"] = _clean(at.get("url"), 500)
    r["pdf_url"] = _clean(at.get("contentUrl"), 500)
    if r["pdf_url"] and not re.search(r"\.pdf($|\?)", r["pdf_url"], re.I):
        r["pdf_url"] = None
    r["is_oa"] = True if r["pdf_url"] else None
    r["cited_by"] = at.get("citationCount")
    r["keywords"] = [_clean(s0.get("subject"), 80)
                     for s0 in (at.get("subjects") or [])][:15]
    descr = at.get("descriptions") or []
    for d0 in descr:
        if d0.get("description"):
            r["abstract"] = _clean(d0["description"], 4000)
            break
    r["openalex_id"] = None
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


# ── DOAJ ───────────────────────────────────────────────────────────────────

def search_doaj(query, *, year_from=None, year_to=None, per_source=100,
                max_records=1000, key=None, email=None):
    s = _session(email)
    if key:
        s.headers["Authorization"] = f"Bearer {key}"
    info = {"source": "doaj", "reported": None, "truncated": False}
    q = query or "*"
    if year_from and year_to:
        q = f"({q}) AND bibjson.year:[{year_from} TO {year_to}]"
    elif year_from:
        q = f"({q}) AND bibjson.year:[{year_from} TO 3000]"
    elif year_to:
        q = f"({q}) AND bibjson.year:[1500 TO {year_to}]"
    out, page = [], 1
    size = min(per_source, 100)
    while len(out) < max_records:
        params = {"pageSize": size, "page": page}
        d = _get(s, f"https://doaj.org/api/search/articles/{_up.quote(q)}", params=params)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        info["reported"] = d.get("total")
        res = d.get("results") or []
        if not res:
            break
        for it in res:
            rec = _doaj_record(it)
            if rec["title"]:
                out.append(rec)
        if page * size >= (info["reported"] or 0):
            break
        page += 1
    if len(out) >= max_records and (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _doaj_record(it):
    r = _blank("doaj")
    b = it.get("bibjson") or {}
    r["title"] = _clean((b.get("title") or ""), 600)
    r["abstract"] = _clean(b.get("abstract"), 4000)
    auth = []
    for a in (b.get("author") or []):
        nm = _clean(a.get("name"), 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth[:60]
    j = b.get("journal") or {}
    r["journal"] = _clean(j.get("title"), 300)
    r["issn"] = [i for i in [j.get("issn")] if i]
    y = b.get("year")
    r["year"] = int(y) if str(y).isdigit() else None
    for ident in (b.get("identifier") or []):
        if str(ident.get("type", "")).lower() == "doi":
            r["doi"] = _norm_doi(ident.get("id"))
            break
    for lk in (b.get("link") or []):
        if lk.get("type") == "fulltext":
            r["landing_url"] = _clean(lk.get("url"), 500)
            break
    kws = b.get("keywords") or []
    if isinstance(kws, list):
        r["keywords"] = [_clean(k0, 80) for k0 in kws][:15]
    r["is_oa"] = True
    r["oa_status"] = "gold"
    r["type"] = "journal-article"
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


# ── OpenAIRE ───────────────────────────────────────────────────────────────

def search_openaire(query, *, year_from=None, year_to=None, oa_only=True,
                    per_source=100, max_records=500, key=None, email=None):
    """OpenAIRE is a genuinely flaky public endpoint (503s and >60s hangs are
    routine). It is best-effort: keep the source, but let the status say so."""
    s = _session(email)
    info = {"source": "openaire", "reported": None, "truncated": False}
    base = {"keywords": query or "", "format": "json", "size": min(per_source, 100)}
    if year_from:
        base["fromDateAccepted"] = f"{year_from}-01-01"
    if year_to:
        base["toDateAccepted"] = f"{year_to}-12-31"
    if oa_only:
        base["OA"] = "true"
    out, page = [], 1
    while len(out) < max_records:
        params = dict(base, page=page)
        d = _get(s, "https://api.openaire.eu/search/publications", params=params,
                 tries=4, backoff=3.0)
        if "__error__" in d:
            info["status"] = f"{d['__error__']} (OpenAIRE is often unavailable)"
            break
        resp = (d.get("response") or {})
        hdr = ((resp.get("header") or {}).get("total") or {})
        info["reported"] = int(hdr.get("$", 0)) if str(hdr.get("$", 0)).isdigit() else None
        results = (((resp.get("results") or {}).get("result")) or [])
        if not results:
            break
        for it in results:
            rec = _openaire_record(it)
            if rec["title"]:
                out.append(rec)
        if info["reported"] is None or page * base["size"] >= info["reported"]:
            break
        page += 1
    if len(out) >= max_records and (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _openaire_record(it):
    r = _blank("openaire")
    md = it.get("metadata") or {}
    oaf = md.get("oaf:entity") or {}
    res = (oaf.get("oaf:result") or {})
    mdobj = res.get("metadata") if isinstance(res.get("metadata"), dict) else md.get("metadata")
    mdobj = mdobj or {}
    t = mdobj.get("title")
    if isinstance(t, list):
        t = t[0] if t else None
    if isinstance(t, dict):
        t = t.get("$")
    r["title"] = _clean(t, 600)
    creators = mdobj.get("creator") or []
    if isinstance(creators, dict):
        creators = [creators]
    auth = []
    for c in (creators if isinstance(creators, list) else []):
        if isinstance(c, dict):
            nm = _clean(c.get("$"), 200)
            if nm:
                auth.append(nm)
    r["authors"] = auth[:60]
    r["year"] = _year_of_text(mdobj.get("dateofacceptance") or "")
    r["publication_date"] = _clean(mdobj.get("dateofacceptance"), 40)
    pid = mdobj.get("pid")
    pids = pid if isinstance(pid, list) else [pid]
    for p in (pids if isinstance(pids, list) else []):
        if isinstance(p, dict) and str(p.get("@classid", "")).lower() == "doi":
            r["doi"] = _norm_doi(p.get("$"))
    jr = mdobj.get("journal")
    if isinstance(jr, str):
        r["journal"] = _clean(jr, 300)
    elif isinstance(jr, dict):
        r["journal"] = _clean(jr.get("$"), 300)
    insts = mdobj.get("children")
    inst = ((insts or {}).get("instance") if isinstance(insts, dict) else None)
    insts_list = inst if isinstance(inst, list) else [inst]
    for i0 in (insts_list or []):
        if not isinstance(i0, dict):
            continue
        for wu in ((i0.get("webresource") or []) if isinstance(
                i0.get("webresource"), list) else [i0.get("webresource")]):
            if not isinstance(wu, dict):
                continue
            url = wu.get("url")
            if url and str(wu.get("classname", "")).lower() == "webpage":
                r["landing_url"] = _clean(url, 500)
            elif url and not r["pdf_url"]:
                r["pdf_url"] = _clean(url, 500)
    r["is_oa"] = True
    r["oa_status"] = "gold"
    r["type"] = "journal-article"
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


# ── Scopus (Elsevier) ──────────────────────────────────────────────────────

def search_scopus(query, *, year_from=None, year_to=None, doc_types=None,
                  subject_area=None, min_citations=None, per_source=200,
                  max_records=2000, key=None, email=None):
    """Search only. Scopus caps at 2000 records without an institutional
    entitlement; the adapter reports that as `truncated` rather than hiding it.
    `view=COMPLETE` (abstracts, affiliations) needs an entitlement and will 401."""
    s = _session(email)
    info = {"source": "scopus", "reported": None, "truncated": False}
    headers = {"X-ELS-APIKey": key or "", "Accept": "application/json"}
    q = _scopus_query(query, year_from, year_to, doc_types, subject_area)
    out, start = [], 0
    # Verified live: this service level rejects count>25 with HTTP 400
    # ("Exceeds the maximum number allowed for the service level").
    count = max(1, min(per_source, 25))
    while len(out) < max_records and start < 2000:
        params = {"query": q, "count": count, "start": start}
        if key:
            params["apiKey"] = key
        d = _get(s, "https://api.elsevier.com/content/search/scopus",
                 params=params, headers=headers, tries=2)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        sr = d.get("search-results") or {}
        info["reported"] = int((sr.get("opensearch:totalResults") or 0)) or None
        entries = sr.get("entry") or []
        if isinstance(entries, dict):
            entries = [entries]
        for it in entries:
            if not isinstance(it, dict):
                continue
            rec = _scopus_record(it)
            if min_citations and (rec["cited_by"] or 0) < min_citations:
                continue
            if rec["title"]:
                out.append(rec)
        if not entries:
            break
        start += count
    if (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _scopus_query(query, y_from, y_to, types, subject):
    bits = []
    if query:
        bits.append(f"TITLE-ABS-KEY({query})" if not re.search(
            r"\b(AND|OR|NOT|WITHIN|TITLE|ABS-KEY|AUTHKEY)\b", query, re.I)
            else f"({query})")
    if y_from or y_to:
        lo, hi = y_from or 1870, y_to or 3000
        bits.append(f"PUBYEAR > {lo - 1} AND PUBYEAR < {hi + 1}")
    if types:
        smap = {"journal-article": "article", "review": "review",
                "conference-paper": "conf", "book-chapter": "ch",
                "book": "book"}
        vals = [smap.get(t, t) for t in types]
        bits.append("(" + " OR ".join(f"DOCTYPE({v})" for v in vals) + ")")
    return " AND ".join(bits) if bits else "*"


def _scopus_record(it):
    r = _blank("scopus")
    r["title"] = _clean(it.get("dc:title"), 600)
    r["doi"] = _norm_doi(it.get("prism:doi"))
    dp = it.get("prism:coverDate") or ""
    r["year"] = _year_of_text(dp)
    # Elsevier stamps online-first articles with the FUTURE issue date
    # (a 2026 DOI can carry coverDate 2027-12). Prefer a sane year.
    today_year = datetime.now().year
    if (r["year"] or 0) > today_year + 1:
        for cand in (it.get("prism:pubDate"), it.get("prism:coverDisplayDate")):
            cy = _year_of_text(str(cand or ""))
            if cy and cy <= today_year + 1:
                r["year"] = cy
                break
        else:
            dy = _year_of_text(r["doi"] or "")
            if dy and dy <= today_year + 1:
                r["year"] = dy
    r["publication_date"] = dp or None
    r["journal"] = _clean(it.get("prism:publicationName"), 300)
    r["volume"], r["issue"] = it.get("prism:volume"), it.get("prism:issueIdentifier")
    r["pages"] = _clean(it.get("prism:pageRange"), 60)
    r["issn"] = [str(x) for x in
               _scopus_values(it.get("prism:issn")) +
               _scopus_values(it.get("prism:eIssn")) if x]
    auth = []
    if it.get("author"):
        au = it["author"]
        if isinstance(au, dict):
            au = [au]
        for a in au:
            if isinstance(a, dict):
                nm = _clean(" ".join(x for x in [a.get("given-name"), a.get("surname")]
                                     if x), 200)
                if nm:
                    auth.append(nm)
    if not auth:
        # BASIC view ships authors as one "Last, First; Last, First" string
        for part in re.split(r"\s*;\s*|\s*,\s*(?=[A-Z])", it.get("dc:creator") or ""):
            nm = _clean(part, 200)
            if nm and len(nm) > 2:
                auth.append(nm)
    r["authors"] = auth[:60]
    r["cited_by"] = _scopus_int(it.get("citedby-count"))
    r["is_oa"] = _scopus_flag(it.get("openaccess"))
    fr = _scopus_values(it.get("freetoread"))
    lab = " ".join(_scopus_values(it.get("freetoreadLabel"))).lower()
    if "gold" in lab:
        r["oa_status"] = "gold"
    elif "hybrid" in lab:
        r["oa_status"] = "hybrid"
    elif "bronze" in lab:
        r["oa_status"] = "bronze"
    elif "green" in lab:
        r["oa_status"] = "green"
    elif fr:
        r["oa_status"] = "bronze"
    r["type"] = _clean(it.get("subtype") or it.get("subtypeDescription"), 80)
    r["landing_url"] = _clean(it.get("prism:url"), 500)
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


def _scopus_int(v):
    if isinstance(v, dict):
        v = v.get("$")
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _scopus_values(v):
    """Scopus BASIC wraps scalars as {'value': ['all', ...]}."""
    if v is None:
        return []
    if isinstance(v, dict):
        v = v.get("value")
        if v is None:
            return []
    if isinstance(v, list):
        return [x.get("$") if isinstance(x, dict) else x for x in v]
    return [v]


def _scopus_flag(v):
    vals = [str(x) for x in _scopus_values(v)]
    if not vals:
        return None
    return True if any(x in ("1", "true", "True") for x in vals) else (
        False if any(x in ("0", "false") for x in vals) else None)


# ── CORE ───────────────────────────────────────────────────────────────────

def search_core(query, *, year_from=None, year_to=None, oa_only=False,
                doc_types=None, per_source=100, max_records=500, key=None,
                email=None):
    s = _session(email)
    info = {"source": "core", "reported": None, "truncated": False}
    out, page = [], 1
    size = min(per_source, 100)
    while len(out) < max_records:
        params = {"q": query or "", "limit": size, "page": page}
        if year_from and year_to:
            params["yearPublishedDate"] = f"[{year_from}-01-01 TO {year_to}-12-31]"
        elif year_from:
            params["yearPublishedDate"] = f"[{year_from}-01-01 TO 3000-12-31]"
        elif year_to:
            params["yearPublishedDate"] = f"[1500-01-01 TO {year_to}-12-31]"
        if oa_only:
            params["isOpenAccess"] = "true"
        d = _get(s, "https://api.core.ac.uk/v3/search/works", params=params, tries=2)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        info["reported"] = d.get("totalHits")
        items = d.get("results") or []
        if not items:
            break
        for it in items:
            rec = _core_record(it)
            # CORE's yearPublishedDate filter is unreliable, so enforce the
            # window here as well as server-side.
            if rec["year"] and year_from and rec["year"] < year_from:
                continue
            if rec["year"] and year_to and rec["year"] > year_to:
                continue
            if rec["title"]:
                out.append(rec)
        if page * size >= (info["reported"] or 0):
            break
        page += 1
    if len(out) >= max_records and (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _core_record(it):
    r = _blank("core")
    r["title"] = _clean(it.get("title"), 600)
    r["doi"] = _norm_doi(it.get("doi"))
    abstract = it.get("abstract")
    if not abstract and isinstance(it.get("abstractInvertedIndex"), dict):
            abstract = _invert_abstract(it["abstractInvertedIndex"])
    r["abstract"] = _clean(abstract, 4000)
    r["year"] = it.get("yearPublished") or _year_of_text(it.get("publishedDate") or "")
    r["publication_date"] = _clean(it.get("publishedDate"), 40)
    r["journal"] = _clean(it.get("publisher") or it.get("sourceFullName"), 300)
    r["type"] = _clean(it.get("documentType"), 80)
    auth = []
    for a0 in (it.get("authors") or []):
        nm = _clean(a0.get("name") if isinstance(a0, dict) else a0, 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth[:60]
    r["is_oa"] = True if it.get("downloadUrl") else it.get("isOpenAccess")
    r["landing_url"] = _clean(it.get("sourceFullNameUrls") and
                              (it.get("sourceFullNameUrls") or [None])[0], 500)
    r["pdf_url"] = _clean(it.get("downloadUrl"), 500)
    r["oa_status"] = "green"
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


# ── Web of Science ─────────────────────────────────────────────────────────

def search_wos(query, *, year_from=None, year_to=None, doc_types=None,
               oa_only=False, per_source=100, max_records=500, key=None,
               email=None, base_url="https://api.clarivate.com/apis/wos-starter/v1"):
    """Web of Science Expanded API. Requires both a subscription and a bearer
    token; the starter tier caps at 200 records. Without a token this returns a
    clear status rather than a confusing 401."""
    if not key:
        return [], {"source": "wos", "reported": None, "truncated": False,
                    "status": "needs key (Clarivate Expanded API token + subscription)"}
    s = _session(email)
    s.headers["Authorization"] = f"Bearer {key}"
    info = {"source": "wos", "reported": None, "truncated": False}
    out, start = [], 1
    size = min(per_source, 100)
    while len(out) < max_records:
        params = {"q": f'TS=({query})' if query else "TS=(*)",
                  "limit": size, "start": start}
        if year_from:
            params.update({"PY": f">{year_from - 1}"})
        if year_to:
            params.setdefault("PY", "")
            params["PY"] = (params["PY"] + f" <{year_to + 1}").strip()
        d = _get(s, f"{base_url}/documents", params=params, tries=2)
        if "__error__" in d:
            info["status"] = d["__error__"]
            break
        meta = d.get("MetaData") or {}
        info["reported"] = (meta.get("TotalRecords")
                            if isinstance(meta.get("TotalRecords"), int) else None)
        data = d.get("Data") or []
        for it in data:
            rec = _wos_record(it)
            if rec["title"]:
                out.append(rec)
        if not data:
            break
        start += 1
    if (info["reported"] or 0) > len(out):
        info["truncated"] = True
    return out[:max_records], info


def _wos_record(it):
    r = _blank("wos")
    fields = (it.get("completeStructures") or [{}])[0]
    r["title"] = _clean(fields.get("title"), 600)
    abstract = fields.get("abstract")
    if isinstance(abstract, dict):
        abstract = " ".join(abstract.values())
    r["abstract"] = _clean(abstract, 4000)
    ids = it.get("UID") or ""
    if str(ids).startswith("DOI:"):
        r["doi"] = _norm_doi(ids[4:])
    r["year"] = fields.get("pubYear")
    r["journal"] = _clean((fields.get("sourceTitle") or [None])[0]
                          if isinstance(fields.get("sourceTitle"), list)
                          else fields.get("sourceTitle"), 300)
    auth = []
    for a in (fields.get("authors") or []):
        nm = _clean(a.get("authorName") if isinstance(a, dict) else a, 200)
        if nm:
            auth.append(nm)
    r["authors"] = auth[:60]
    kw = fields.get("authorKeywords") or fields.get("keywords") or []
    r["keywords"] = [_clean(k0.get("keyword") if isinstance(k0, dict) else k0, 80)
                     for k0 in kw][:15]
    r["cited_by"] = (fields.get("timesCited") or [{}])[0] if fields.get("timesCited") else None
    r["type"] = _clean((fields.get("documentTypes") or [None])[0]
                       if isinstance(fields.get("documentTypes"), list) else None, 80)
    doi_links = (fields.get("doiLink") or [None])[0]
    if doi_links:
        r["landing_url"] = _clean(doi_links, 500)
    if not r["landing_url"] and r["doi"]:
        r["landing_url"] = f"https://doi.org/{r['doi']}"
    return r


# ── registry ───────────────────────────────────────────────────────────────

SOURCE_REGISTRY = [
    {"id": "openalex", "label": "OpenAlex",
     "note": "Best free all-round source: 250M+ works, boolean AND/OR/NOT, OA PDF links, citations.",
     "key": "OPENALEX_API_KEY", "key_label": "OpenAlex API key (optional, free — 10× rate limit)",
     "needs_key": False, "free": True, "cap": 10000,
     "fn": "search_openalex"},
    {"id": "crossref", "label": "Crossref",
     "note": "DOI registry — the best source for anything with a DOI, strongest for older journals.",
     "key": "CROSSREF_PLUS_TOKEN", "key_label": "Crossref Plus token (optional)",
     "needs_key": False, "free": True, "cap": 10000,
     "fn": "search_crossref"},
    {"id": "scopus", "label": "Scopus (Elsevier)",
     "note": "Broadest multidisciplinary index. API key required; capped at 2000 records without an institutional entitlement.",
     "key": "ELSEVIER_USER_KEY", "key_label": "Elsevier / Scopus API key",
     "needs_key": True, "free": False, "cap": 2000,
     "fn": "search_scopus"},
    {"id": "wos", "label": "Web of Science",
     "note": "Clarivate Expanded API — needs both a subscription and a bearer token. Starter tier caps at 200.",
     "key": "WOS_API_TOKEN", "key_label": "Clarivate WOS bearer token",
     "needs_key": True, "free": False, "cap": 200,
     "fn": "search_wos"},
    {"id": "europepmc", "label": "Europe PMC",
     "note": "Biomedical + life sciences. Full-text OA repository, MeSH terms, grants.",
     "key": None, "key_label": None, "needs_key": False, "free": True, "cap": 10000,
     "fn": "search_europepmc"},
    {"id": "pubmed", "label": "PubMed",
     "note": "Biomedical. Authoritative abstracts. Optional NCBI key raises the limit to 10/s.",
     "key": "NCBI_API_KEY", "key_label": "NCBI E-utilities API key (optional, free)",
     "needs_key": False, "free": True, "cap": 10000,
     "fn": "search_pubmed"},
    {"id": "arxiv", "label": "arXiv",
     "note": "Preprints in physics, CS, maths, quant bio, econ. Always free full text.",
     "key": None, "key_label": None, "needs_key": False, "free": True, "cap": 8000,
     "fn": "search_arxiv"},
    {"id": "semantic_scholar", "label": "Semantic Scholar",
     "note": "Good citation graph and TLDR summaries, but its shared keyless pool rate-limits hard — run it alone or add a key.",
     "key": "S2_API_KEY", "key_label": "Semantic Scholar API key (strongly recommended)",
     "needs_key": False, "free": True, "cap": 400,
     "fn": "search_semanticscholar"},
    {"id": "datacite", "label": "DataCite",
     "note": "Datasets, software, preprints, reports, other research output — complementary to OpenAlex.",
     "key": None, "key_label": None, "needs_key": False, "free": True, "cap": 10000,
     "fn": "search_datacite"},
    {"id": "doaj", "label": "DOAJ",
     "note": "Quality-checked fully open-access journals.",
     "key": "DOAJ_API_KEY", "key_label": "DOAJ API key (optional)",
     "needs_key": False, "free": True, "cap": 10000,
     "fn": "search_doaj"},
    {"id": "openaire", "label": "OpenAIRE",
     "note": "European open scholarly infrastructure graph.",
     "key": None, "key_label": None, "needs_key": False, "free": True, "cap": 1000,
     "fn": "search_openaire"},
    {"id": "core", "label": "CORE",
     "note": "Aggregates repositories worldwide. Works keyless at low volume; a free key raises the limit.",
     "key": "CORE_API_KEY", "key_label": "CORE API key",
     "needs_key": False, "free": True, "cap": 500,
     "fn": "search_core"},
]

SOURCE_BY_ID = {s["id"]: s for s in SOURCE_REGISTRY}


def available_sources(keys):
    """
    Split the registry into runnable sources and blocked ones.

    Only sources whose key is genuinely REQUIRED are blocked. OpenAlex,
    Crossref, PubMed, DOAJ and Semantic Scholar all work keyless (just more
    slowly / with tighter limits), so a missing optional key must never hide
    them from the user.
    """
    ok, blocked = [], []
    for s in SOURCE_REGISTRY:
        if s["needs_key"] and s["key"] and not keys.get(s["key"]):
            blocked.append({**s, "reason": f"missing {s['key_label']}"})
        else:
            ok.append(s)
    return ok, blocked


def run_search(source_ids, query, filters, keys, email, workers=4,
               progress=None):
    """
    Run the same query across several sources in parallel.

    Each adapter only accepts the filters its API can actually honour, so a
    missing keyword argument is never raised: unsupported filters are dropped
    per-source and listed in the report as `ignored`. That keeps the canonical
    UI filter set free to grow without every adapter having to implement it.

    Returns (records, reports) where reports is one status dict per source:
    {"source", "label", "n", "reported", "truncated", "status", "elapsed"}.
    A source that fails is recorded as failed; the search still succeeds.
    """
    import inspect
    records, reports = [], []
    todo = []
    for sid in source_ids:
        spec = SOURCE_BY_ID.get(sid)
        if not spec:
            continue
        fn = globals().get(spec["fn"])
        if not fn:
            continue
        todo.append((spec, fn))

    def one(spec, fn):
        t0 = time.time()
        requested_max = int(filters.get("max_records") or 1000)
        cap = int(min(requested_max, spec["cap"]))
        wanted = {
            "year_from": filters.get("year_from"),
            "year_to": filters.get("year_to"),
            "doc_types": filters.get("doc_types"),
            "oa_only": filters.get("oa_only"),
            "issn": filters.get("issn"),
            "language": filters.get("language"),
            "min_citations": filters.get("min_citations"),
            "categories": filters.get("categories"),
            "subject_area": filters.get("subject_area"),
            "has_fulltext": filters.get("has_fulltext"),
            "has_abstract": filters.get("has_abstract"),
            "is_retracted_excluded": filters.get("exclude_retracted", True),
            "per_source": cap,
            "max_records": cap,
            "key": keys.get(spec["key"]) if spec["key"] else None,
            "email": email,
        }
        supported = set(inspect.signature(fn).parameters)
        accepted = {k: v for k, v in wanted.items() if k in supported}
        ignored = sorted(k for k in wanted if k not in supported)
        recs, info = fn(query, **accepted)
        # Defensive year gate: some APIs round dates, stamp future issue dates
        # or silently ignore a range. A systematic review must not pool
        # out-of-window records, so re-check client side.
        yf, yt = filters.get("year_from"), filters.get("year_to")
        if yf or yt:
            before = len(recs)
            recs = [r for r in recs
                    if not r.get("year") or ((not yf or r["year"] >= yf)
                                             and (not yt or r["year"] <= yt))]
            dropped = before - len(recs)
            if dropped:
                info["year_filtered_out"] = dropped
        info = info or {}
        info.update({"source": spec["id"], "label": spec["label"], "n": len(recs),
                     "elapsed": round(time.time() - t0, 1)})
        info.setdefault("status", "ok")
        if ignored:
            info["ignored"] = ignored
        return recs, info

    with ThreadPoolExecutor(max_workers=max(1, min(workers, len(todo) or 1))) as ex:
        futs = {ex.submit(one, spec, fn): spec for spec, fn in todo}
        for fut in as_completed(futs):
            spec = futs[fut]
            try:
                recs, info = fut.result()
            except Exception as exc:
                recs, info = [], {"source": spec["id"], "label": spec["label"],
                                  "n": 0, "status": f"{type(exc).__name__}: {exc}",
                                  "elapsed": 0, "reported": None, "truncated": False}
            records.extend(recs)
            reports.append(info)
            if progress:
                progress(info, len(records))
    order = {s["id"]: i for i, s in enumerate(SOURCE_REGISTRY)}
    reports.sort(key=lambda r: order.get(r["source"], 99))
    return records, reports