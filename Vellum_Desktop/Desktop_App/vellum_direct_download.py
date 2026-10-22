"""
vellum_direct_download.py — Resilient Multi-Tier PDF Downloader & Queue Manager.

Enables:
  1. Instant '⚡ Download Now' for any paper with Cloudflare bypass (cloudscraper).
  2. Multi-tier resolution:
     - Direct URL / OpenAlex primary location
     - Springer / BioMed Central / Nature direct OA routes
     - Unpaywall API (all OA locations)
     - Semantic Scholar Open Access API
     - Sci-Hub fallback mirrors
  3. Returns browser fallback URL for seamless manual access if CAPTCHA blocks retrieval.
  4. Synchronized persistent Download Queue with bulk processing.
"""

from __future__ import annotations

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from urllib.parse import quote_plus, urljoin
from bs4 import BeautifulSoup
import requests
try:
    import cloudscraper
except ImportError:
    cloudscraper = None
try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None

import vellum_workspace as VW

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
SCIHUB_MIRRORS = ["https://sci-hub.se/", "https://sci-hub.st/", "https://sci-hub.ru/"]


def _get_scraper():
    """Create a cloudscraper instance capable of solving JS/Cloudflare challenges."""
    if cloudscraper:
        try:
            return cloudscraper.create_scraper(
                browser={"browser": "chrome", "platform": "windows", "desktop": True}
            )
        except Exception:
            pass
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept": "application/pdf,*/*"})
    return s


def _is_real_title(t: Optional[str], doi: str = "") -> bool:
    if not t:
        return False
    ts = str(t).strip()
    if len(ts) < 6:
        return False
    tl = ts.lower()
    if tl in ("untitled paper", "direct download", "paper"):
        return False
    if tl.startswith(("10.", "http://", "https://", "doi:", "doi ", "paper with doi")):
        return False
    if doi and tl == doi.strip().lower():
        return False
    return True


def sanitize_filename(title: str, max_len: int = 160) -> str:
    """Create a safe filesystem filename from paper title."""
    clean = re.sub(r'[\\/*?:"<>|\n\r\t]', " ", title)
    clean = re.sub(r"\s+", " ", clean).strip()
    clean = clean[:max_len].rstrip(". ")
    return f"{clean or 'Paper'}.pdf"


def _verify_pdf_bytes(content: bytes) -> bool:
    """Check if content begins with valid PDF header and has reasonable size."""
    if not content or len(content) < 1500:
        return False
    return content.startswith(b"%PDF") or (b"%PDF-" in content[:1024])


def _fetch_pdf_bytes_resilient(url: str, scraper, timeout: int = 30) -> Optional[bytes]:
    """Fetch PDF bytes with cloudscraper first, falling back to curl_cffi Chrome TLS impersonation."""
    if not url or not url.startswith("http"):
        return None
    try:
        r = scraper.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code in (200, 206) and _verify_pdf_bytes(r.content):
            return r.content
    except Exception:
        pass
    if curl_requests is not None:
        try:
            s = curl_requests.Session(impersonate="chrome")
            base = "/".join(url.split("/")[:3]) + "/"
            try:
                s.get(base, timeout=12)
            except Exception:
                pass
            r2 = s.get(
                url,
                timeout=timeout,
                allow_redirects=True,
                headers={
                    "User-Agent": UA,
                    "Accept": "application/pdf,application/octet-stream,*/*;q=0.8",
                    "Referer": base,
                },
            )
            if _verify_pdf_bytes(r2.content):
                return r2.content
        except Exception:
            pass
    return None


def _fetch_html_resilient(url: str, scraper, timeout: int = 20) -> Tuple[Optional[str], str]:
    """Fetch HTML using scraper first, falling back to curl_cffi Chrome TLS impersonation."""
    try:
        r = scraper.get(url, timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and r.text:
            return r.text, str(r.url)
    except Exception:
        pass
    if curl_requests is not None:
        try:
            s = curl_requests.Session(impersonate="chrome")
            r2 = s.get(url, timeout=timeout, allow_redirects=True, headers={"User-Agent": UA})
            if r2.status_code == 200 and r2.text:
                return r2.text, str(r2.url)
        except Exception:
            pass
    return None, url


def _extract_pdf_links_from_html(html_text: str, base_url: str) -> List[str]:
    """Extract meta citation_pdf_url and direct PDF download links from an HTML page."""
    found: List[str] = []
    if not html_text:
        return found
    soup = BeautifulSoup(html_text, "html.parser")
    for meta in soup.find_all("meta"):
        mname = (meta.get("name") or meta.get("property") or "").lower()
        if mname in ("citation_pdf_url", "bepress_citation_pdf_url", "eprints.document_url"):
            content = (meta.get("content") or "").strip()
            if content:
                full_u = urljoin(base_url, content)
                if full_u.startswith("http") and full_u not in found:
                    found.append(full_u)
    for a in soup.select("a[href]"):
        text = a.get_text(" ", strip=True).lower()
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("javascript:", "mailto:", "#")):
            continue
        hlow = href.lower()
        if (
            text in ("pdf", "download", "download pdf", "full text pdf", "view pdf")
            or any(p in text for p in ["download pdf", "pdf download", "full text pdf", "[pdf]", "view pdf"])
            or hlow.endswith(".pdf")
            or any(p in hlow for p in ["/file/get?code=", "/file/download", "download_pub", "pdf.sciencedirectassets.com", "pdfft", "/article/download/"])
        ):
            full_u = urljoin(base_url, href)
            if full_u.startswith("http") and full_u not in found:
                found.append(full_u)
    return found


def download_single_paper_direct(
    paper: Dict[str, Any],
    project_name: Optional[str] = None,
) -> Tuple[bool, str, Optional[str], Optional[Path]]:
    """
    Downloads a single paper PDF directly into the active project vault.
    Returns (success, message, browser_fallback_url, local_path).
    """
    p_dir = VW.get_project_dir(project_name)
    papers_dir = p_dir / "papers"
    papers_dir.mkdir(parents=True, exist_ok=True)

    title = (paper.get("title") or "").strip()
    doi = (paper.get("doi") or "").strip()
    if doi.lower().startswith("https://doi.org/"):
        doi = doi[16:].strip()
    elif doi.lower().startswith("http://doi.org/"):
        doi = doi[15:].strip()
    pdf_url = (paper.get("pdf_url") or "").strip()

    scraper = _get_scraper()
    cr_links: List[str] = []

    if doi and doi.startswith("10."):
        try:
            r_cr = requests.get(f"https://api.crossref.org/works/{doi}", headers={"User-Agent": UA}, timeout=10)
            if r_cr.status_code == 200:
                msg = r_cr.json().get("message", {})
                if not _is_real_title(title, doi):
                    t_cr = (msg.get("title") or [None])[0]
                    if t_cr:
                        cand_t = re.sub(r"<[^>]+>", "", t_cr).strip()
                        if _is_real_title(cand_t, doi):
                            title = cand_t
                for lk in msg.get("link", []):
                    u_lk = lk.get("URL", "")
                    if u_lk and u_lk.startswith("http") and u_lk not in cr_links:
                        cr_links.append(u_lk)
        except Exception:
            pass

    if _is_real_title(title, doi):
        filename = sanitize_filename(title)
    elif doi:
        filename = sanitize_filename(doi.replace("/", "_"))
    else:
        filename = sanitize_filename(title or "Paper")
    dest = papers_dir / filename

    # 0. Check if already downloaded
    if dest.exists() and dest.stat().st_size > 2000:
        return True, "Already in Vault", None, dest

    if doi:
        for p in papers_dir.glob("*.pdf"):
            if doi.replace("/", "_") in p.name:
                return True, "Already in Vault", None, p

    fallback_url = pdf_url or (f"https://doi.org/{doi}" if doi else None)

    # 1. Direct PDF URL (with curl_cffi Chrome TLS fallback)
    if pdf_url and pdf_url.startswith("http"):
        content = _fetch_pdf_bytes_resilient(pdf_url, scraper)
        if content:
            dest.write_bytes(content)
            return True, f"Saved: {dest.name}", None, dest

    # 2. Crossref Full-Text Links
    for u_lk in cr_links:
        content = _fetch_pdf_bytes_resilient(u_lk, scraper)
        if content:
            dest.write_bytes(content)
            return True, f"Saved via Crossref: {dest.name}", None, dest

    # 3. OpenAlex Primary Location, OA URLs & Title Search Fallback
    if doi and doi.startswith("10."):
        try:
            oa_api = f"https://api.openalex.org/works/https://doi.org/{doi}"
            r_oa = scraper.get(oa_api, timeout=12)
            if r_oa.status_code == 200:
                js_oa = r_oa.json()
                if not title or title == "Untitled Paper":
                    title = js_oa.get("title") or js_oa.get("display_name") or title
                cand_urls = []
                oa_info = js_oa.get("open_access") or {}
                if oa_info.get("oa_url"):
                    cand_urls.append(oa_info["oa_url"])
                for loc in [js_oa.get("best_oa_location") or {}, js_oa.get("primary_location") or {}] + (js_oa.get("locations") or []):
                    u_p = (loc or {}).get("pdf_url")
                    if u_p and u_p not in cand_urls:
                        cand_urls.append(u_p)
                for u in cand_urls:
                    if u and u.startswith("http"):
                        fallback_url = u
                        content = _fetch_pdf_bytes_resilient(u, scraper)
                        if content:
                            dest.write_bytes(content)
                            return True, f"Saved via OpenAlex OA: {dest.name}", None, dest
        except Exception:
            pass

    # 3b. OpenAlex Title Search (catches preprints like preprints.org under another DOI)
    if title and len(title) > 10 and title != "Untitled Paper":
        try:
            norm_target = re.sub(r"[^a-z0-9]", "", title.lower())
            r_oat = scraper.get(f"https://api.openalex.org/works?search={quote_plus(title)}&per-page=4", timeout=12)
            if r_oat.status_code == 200:
                for work in r_oat.json().get("results", []):
                    wt = work.get("title") or work.get("display_name") or ""
                    norm_wt = re.sub(r"[^a-z0-9]", "", wt.lower())
                    if norm_wt and (norm_wt == norm_target or norm_target in norm_wt or norm_wt in norm_target):
                        oa_u = (work.get("open_access") or {}).get("oa_url")
                        locs = [oa_u] + [(l or {}).get("pdf_url") for l in ([work.get("best_oa_location"), work.get("primary_location")] + (work.get("locations") or []))]
                        for u in locs:
                            if u and u.startswith("http"):
                                content = _fetch_pdf_bytes_resilient(u, scraper)
                                if content:
                                    dest.write_bytes(content)
                                    return True, f"Saved via OpenAlex (Preprint/OA): {dest.name}", None, dest
        except Exception:
            pass

    # 4. Unpaywall API (Iterating across all OA locations)
    if doi and doi.startswith("10."):
        try:
            unp_url = f"https://api.unpaywall.org/v2/{doi}?email=researcher@vellum.app"
            r_unp = scraper.get(unp_url, timeout=12)
            if r_unp.status_code == 200:
                js_unp = r_unp.json()
                locs = ([js_unp.get("best_oa_location")] if js_unp.get("best_oa_location") else []) + (js_unp.get("oa_locations") or [])
                for loc in locs:
                    u_pdf = (loc or {}).get("url_for_pdf") or (loc or {}).get("url")
                    if u_pdf and u_pdf.startswith("http"):
                        fallback_url = fallback_url or u_pdf
                        content = _fetch_pdf_bytes_resilient(u_pdf, scraper)
                        if content:
                            dest.write_bytes(content)
                            return True, f"Saved via Unpaywall: {dest.name}", None, dest
        except Exception:
            pass

    # 5. Google Scholar (DOI + Title + All Versions Cluster)
    scholar_queries = []
    if doi:
        scholar_queries.append(f"https://scholar.google.com/scholar?hl=en&q={quote_plus(doi)}")
    if title and len(title) > 8 and title != "Untitled Paper":
        scholar_queries.append(f"https://scholar.google.com/scholar?hl=en&q={quote_plus(title)}")
    for sq in scholar_queries:
        try:
            html_s, _ = _fetch_html_resilient(sq, scraper, timeout=20)
            if not html_s:
                continue
            soup_s = BeautifulSoup(html_s, "html.parser")
            s_cands = []
            for a in soup_s.select("div.gs_or_ggsm a[href], div.gs_ggs a[href]"):
                h = (a.get("href") or "").strip()
                if h.startswith("http") and h not in s_cands:
                    s_cands.append(h)
            for a in soup_s.select("a[href]"):
                h = (a.get("href") or "").strip()
                txt = a.get_text(" ", strip=True).lower()
                if h.startswith("http") and "scholar.google." not in h:
                    if "[pdf]" in txt or h.lower().endswith(".pdf") or any(k in h.lower() for k in ("download_pub", "/file/download", "/file/get?code=")):
                        if h not in s_cands:
                            s_cands.append(h)
            for cand in s_cands:
                content = _fetch_pdf_bytes_resilient(cand, scraper)
                if content:
                    dest.write_bytes(content)
                    return True, f"Saved via Google Scholar: {dest.name}", None, dest
        except Exception:
            continue

    # 6. Publisher Landing Page & Direct OA Routing
    if doi and doi.startswith("10."):
        html_lp, final_lp = _fetch_html_resilient(f"https://doi.org/{doi}", scraper, timeout=20)
        if html_lp:
            for link in _extract_pdf_links_from_html(html_lp, final_lp):
                content = _fetch_pdf_bytes_resilient(link, scraper)
                if content:
                    dest.write_bytes(content)
                    return True, f"Saved via Publisher Direct: {dest.name}", None, dest

    # 7. Semantic Scholar Open Access API
    if doi and doi.startswith("10."):
        try:
            s2_url = f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf"
            r_s2 = scraper.get(s2_url, timeout=12)
            if r_s2.status_code == 200:
                js_s2 = r_s2.json()
                s2_pdf = (js_s2.get("openAccessPdf") or {}).get("url")
                if s2_pdf and s2_pdf.startswith("http"):
                    fallback_url = fallback_url or s2_pdf
                    content = _fetch_pdf_bytes_resilient(s2_pdf, scraper)
                    if content:
                        dest.write_bytes(content)
                        return True, f"Saved via Semantic Scholar: {dest.name}", None, dest
        except Exception:
            pass

    # 8. Sci-Hub Fallback
    if doi and doi.startswith("10."):
        for mirror in SCIHUB_MIRRORS:
            try:
                sh_url = f"{mirror}{doi}"
                r_sh = scraper.get(sh_url, timeout=15)
                if r_sh.status_code == 200 and _verify_pdf_bytes(r_sh.content):
                    dest.write_bytes(r_sh.content)
                    return True, f"Saved via Sci-Hub: {dest.name}", None, dest
                m = re.search(r'(?:src|href)=["\']([^"\']+\.pdf[^"\']*)["\']', r_sh.text, re.I)
                if m:
                    target_url = m.group(1)
                    if target_url.startswith("//"):
                        target_url = "https:" + target_url
                    elif target_url.startswith("/"):
                        target_url = mirror.rstrip("/") + target_url
                    content = _fetch_pdf_bytes_resilient(target_url, scraper)
                    if content:
                        dest.write_bytes(content)
                        return True, f"Saved via Sci-Hub: {dest.name}", None, dest
            except Exception:
                continue

    return False, "Could not auto-download PDF due to publisher verification/paywall.", fallback_url, None


def get_download_queue(project_name: Optional[str] = None) -> List[Dict[str, Any]]:
    """Retrieve items currently in the download queue for the project."""
    data = VW.load_project_data(project_name)
    return data.get("download_queue", [])


def add_to_download_queue(
    paper: Dict[str, Any],
    project_name: Optional[str] = None,
) -> bool:
    """Add a paper to the download queue."""
    data = VW.load_project_data(project_name)
    queue = data.get("download_queue", [])
    doi = paper.get("doi") or ""
    title = paper.get("title") or "Untitled Paper"

    # Avoid duplicate
    for q in queue:
        if (doi and q.get("doi") == doi) or (q.get("title") == title):
            return False

    queue.append({
        "doi": doi,
        "title": title,
        "pdf_url": paper.get("pdf_url") or "",
        "year": paper.get("year") or 0,
        "authors": paper.get("authors") or [],
        "added_at": time.time(),
    })
    data["download_queue"] = queue
    VW.save_project_data(data, project_name)
    return True


def clear_download_queue(project_name: Optional[str] = None) -> None:
    """Clear all items in the project's download queue."""
    data = VW.load_project_data(project_name)
    data["download_queue"] = []
    VW.save_project_data(data, project_name)


def download_all_in_queue(
    project_name: Optional[str] = None,
) -> Dict[str, int]:
    """Process all queued items and attempt to download each."""
    queue = get_download_queue(project_name)
    success_count = 0
    fail_count = 0
    remaining = []

    for item in queue:
        ok, msg, fallback, path = download_single_paper_direct(item, project_name)
        if ok:
            success_count += 1
        else:
            fail_count += 1
            remaining.append(item)

    data = VW.load_project_data(project_name)
    data["download_queue"] = remaining
    VW.save_project_data(data, project_name)

    return {"success": success_count, "failed": fail_count, "remaining": len(remaining)}
