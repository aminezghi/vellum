"""
citation_core.py — Graph data provider for Vellum's Citation Network.

Fetches bi-directional citation neighborhoods (seed paper + top references +
top citing derivative papers) using the OpenAlex and Semantic Scholar APIs.
Completely free, no mandatory API keys required.
"""

from __future__ import annotations

import html
import json
import re
import urllib.parse
import time
from typing import Any, Dict, List, Optional, Tuple

import requests

OPENALEX_WORK_URL = "https://api.openalex.org/works/{id}"
OPENALEX_SEARCH_URL = "https://api.openalex.org/works"
S2_PAPER_URL = "https://api.semanticscholar.org/graph/v1/paper/{paper_id}"

HEADERS = {
    "User-Agent": "VellumWorkbench/1.0 (mailto:academic-research@vellum.local)",
    "Accept": "application/json",
}


def _get_with_retry(
    url: str,
    headers: Dict[str, str],
    session: Optional[Any] = None,
    timeout: int = 12,
    max_retries: int = 2,
    backoff: float = 0.5,
) -> Optional[requests.Response]:
    """Execute GET request with exponential backoff on 429 or transient errors."""
    client = session or requests
    for attempt in range(max_retries + 1):
        try:
            resp = client.get(url, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp
            if resp.status_code == 429 and attempt < max_retries:
                # Rate limited, back off
                retry_after = resp.headers.get("Retry-After")
                wait_time = float(retry_after) if retry_after and retry_after.isdigit() else backoff * (2 ** attempt)
                time.sleep(wait_time)
                continue
            # Non-retryable error
            return None
        except Exception:
            if attempt < max_retries:
                time.sleep(backoff * (2 ** attempt))
                continue
            return None
    return None


def clean_doi(raw: str) -> str:
    """Normalize DOI string, removing URL prefixes or spaces."""
    s = (raw or "").strip()
    m = re.search(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", s)
    return m.group(0).rstrip(".,;") if m else s


def resolve_seed(
    query: str,
    api_key: str = "",
    session: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    """
    Find a seed paper by DOI, OpenAlex ID, or Title search.
    Returns normalized paper metadata dictionary.
    Supports optional session injection for testability.
    """
    q = (query or "").strip()
    if not q:
        return None

    doi = clean_doi(q)
    headers = dict(HEADERS)
    if api_key:
        headers["api-key"] = api_key

    # 1. Direct DOI lookup
    if doi.startswith("10."):
        url = f"https://api.openalex.org/works/https://doi.org/{urllib.parse.quote(doi)}"
        resp = _get_with_retry(url, headers=headers, session=session, timeout=10)
        if resp and resp.status_code == 200:
            return _parse_openalex_work(resp.json())

    # 2. OpenAlex ID lookup (e.g. W123456789 or https://openalex.org/W123456789)
    m_oa = re.search(r"W\d+", q, re.IGNORECASE)
    if m_oa:
        url = f"https://api.openalex.org/works/{m_oa.group(0).upper()}"
        resp = _get_with_retry(url, headers=headers, session=session, timeout=10)
        if resp and resp.status_code == 200:
            return _parse_openalex_work(resp.json())

    # 3. Title search fallback
    search_url = f"{OPENALEX_SEARCH_URL}?search={urllib.parse.quote(q)}&per-page=1"
    resp = _get_with_retry(search_url, headers=headers, session=session, timeout=10)
    if resp and resp.status_code == 200:
        data = resp.json()
        results = data.get("results", [])
        if results:
            return _parse_openalex_work(results[0])

    return None


def _parse_openalex_work(item: Dict[str, Any]) -> Dict[str, Any]:
    """Extract standard metadata from an OpenAlex work object."""
    oa_id = (item.get("id") or "").replace("https://openalex.org/", "")
    doi = clean_doi(item.get("doi") or "")

    # Authors
    authors = []
    for authorship in item.get("authorships", []):
        author_name = authorship.get("author", {}).get("display_name")
        if author_name:
            authors.append(author_name)

    # Primary venue
    location = item.get("primary_location") or {}
    source = location.get("source") or {}
    venue = source.get("display_name") or "Unknown Venue"

    # PDF / OA URL
    pdf_url = location.get("pdf_url") or ""
    landing_url = location.get("landing_page_url") or ""

    # Reconstruct abstract from inverted index if present
    abstract = ""
    inv = item.get("abstract_inverted_index")
    if inv:
        word_positions: List[Tuple[int, str]] = []
        for word, positions in inv.items():
            for p in positions:
                word_positions.append((p, word))
        word_positions.sort()
        abstract = " ".join(w for _, w in word_positions)

    return {
        "id": oa_id or doi,
        "openalex_id": oa_id,
        "doi": doi,
        "title": item.get("title") or "Untitled",
        "year": item.get("publication_year") or 0,
        "authors": authors,
        "venue": venue,
        "cited_by_count": item.get("cited_by_count") or 0,
        "referenced_works": item.get("referenced_works") or [],
        "pdf_url": pdf_url or landing_url,
        "abstract": abstract,
        "is_oa": (item.get("open_access") or {}).get("is_oa", False),
    }


def build_citation_network(
    seed: Dict[str, Any],
    max_references: int = 15,
    max_citations: int = 15,
    api_key: str = "",
    session: Optional[Any] = None,
) -> Dict[str, Any]:
    """
    Build a complete graph structure around a seed paper.
    Returns:
      {
        "nodes": [{"id", "title", "year", "authors", "venue", "citations", "type", "doi", "pdf_url"}, ...],
        "links": [{"source", "target", "type"}, ...],
        "seed_id": seed["id"]
      }
    """
    seed_id = seed["id"]
    nodes: Dict[str, Dict[str, Any]] = {}
    links: List[Dict[str, Any]] = []

    # 1. Add Seed Node
    nodes[seed_id] = {
        "id": seed_id,
        "title": seed["title"],
        "year": seed["year"],
        "authors": ", ".join(seed["authors"][:3]) + (" et al." if len(seed["authors"]) > 3 else ""),
        "full_authors": seed["authors"],
        "venue": seed["venue"],
        "citations": seed["cited_by_count"],
        "doi": seed["doi"],
        "pdf_url": seed["pdf_url"],
        "abstract": seed.get("abstract", ""),
        "type": "seed",
    }

    headers = dict(HEADERS)
    if api_key:
        headers["api-key"] = api_key

    # 2. Fetch Upstream Referenced Works (Papers cited by the seed)
    ref_ids = [r.replace("https://openalex.org/", "") for r in seed.get("referenced_works", [])][:max_references]
    if ref_ids:
        # OpenAlex batch filter: filter=openalex_id:W1|W2|...
        filter_str = "|".join(ref_ids[:25])
        url = f"{OPENALEX_SEARCH_URL}?filter=openalex_id:{filter_str}&per-page=25"
        resp = _get_with_retry(url, headers=headers, session=session, timeout=12)
        if resp and resp.status_code == 200:
            for item in resp.json().get("results", []):
                ref_data = _parse_openalex_work(item)
                rid = ref_data["id"]
                if rid not in nodes:
                    nodes[rid] = {
                        "id": rid,
                        "title": ref_data["title"],
                        "year": ref_data["year"],
                        "authors": ", ".join(ref_data["authors"][:3]) + (" et al." if len(ref_data["authors"]) > 3 else ""),
                        "full_authors": ref_data["authors"],
                        "venue": ref_data["venue"],
                        "citations": ref_data["cited_by_count"],
                        "doi": ref_data["doi"],
                        "pdf_url": ref_data["pdf_url"],
                        "abstract": ref_data.get("abstract", ""),
                        "type": "reference",
                    }
                # Seed cites this reference
                links.append({"source": seed_id, "target": rid, "type": "cites"})

    # 3. Fetch Downstream Citing Works (Papers citing the seed)
    oa_id = seed.get("openalex_id")
    if oa_id:
        url = (
            f"{OPENALEX_SEARCH_URL}?filter=cites:{oa_id}"
            f"&sort=cited_by_count:desc&per-page={max_citations}"
        )
        resp = _get_with_retry(url, headers=headers, session=session, timeout=12)
        if resp and resp.status_code == 200:
            for item in resp.json().get("results", []):
                cite_data = _parse_openalex_work(item)
                cid = cite_data["id"]
                if cid not in nodes:
                    nodes[cid] = {
                        "id": cid,
                        "title": cite_data["title"],
                        "year": cite_data["year"],
                        "authors": ", ".join(cite_data["authors"][:3]) + (" et al." if len(cite_data["authors"]) > 3 else ""),
                        "full_authors": cite_data["authors"],
                        "venue": cite_data["venue"],
                        "citations": cite_data["cited_by_count"],
                        "doi": cite_data["doi"],
                        "pdf_url": cite_data["pdf_url"],
                        "abstract": cite_data.get("abstract", ""),
                        "type": "citation",
                    }
                # Citing paper cites the seed
                links.append({"source": cid, "target": seed_id, "type": "cites"})

    # 4. Check for secondary cross-connections among nodes
    node_keys = set(nodes.keys())
    existing_link_pairs = {(l["source"], l["target"]) for l in links}

    return {
        "nodes": list(nodes.values()),
        "links": links,
        "seed_id": seed_id,
        "stats": {
            "total_nodes": len(nodes),
            "total_links": len(links),
            "references_count": len([n for n in nodes.values() if n["type"] == "reference"]),
            "citations_count": len([n for n in nodes.values() if n["type"] == "citation"]),
        },
    }
