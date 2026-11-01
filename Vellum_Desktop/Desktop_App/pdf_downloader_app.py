
import streamlit as st
import vellum_analysis as VA
import vellum_brand as VB

import threading
import time
import tempfile
import re
import queue
import requests
import zipfile
import io
import os
import hashlib
import json
from pathlib import Path
from datetime import datetime
from collections import Counter

try:
    from pypdf import PdfReader
except ImportError:
    try:
        from PyPDF2 import PdfReader
    except ImportError:
        PdfReader = None

try:
    from curl_cffi import requests as curl_requests
except ImportError:
    curl_requests = None

import pandas as pd

# Shared analysis services live in vellum_analysis so the Analysis page can
# reuse them; this script registers its PDF extractors with VA at start-up.
_meta_frame = VA.meta_frame
find_duplicates = VA.find_duplicates
extract_all_metadata = VA.extract_all_metadata
_icon_path = os.path.join(os.path.dirname(__file__), "downloader.png")
st.set_page_config(
    page_title="Vellum by Amine",
    page_icon=_icon_path if os.path.exists(_icon_path) else "📄",
    layout="wide",
)

def _ui_palette():
    """Colours for hand-built components matching Apple HIG design system tokens."""
    try:
        import vellum_theme as VT
        dark = VT.is_dark_mode()
    except Exception:
        dark = False
    if dark:
        return {
            "accent": "#0a84ff",
            "muted": "#86868b",
            "card": "#161618",
            "border": "rgba(255, 255, 255, 0.09)",
            "ok": "#34c759",
            "fail": "#ff453a",
            "warn": "#ff9f0a",
            "track": "#2c2c2e",
        }
    return {
        "accent": "#0071e3",
        "muted": "#86868b",
        "card": "#ffffff",
        "border": "rgba(0, 0, 0, 0.06)",
        "ok": "#34c759",
        "fail": "#ff3b30",
        "warn": "#ff9f0a",
        "track": "#e5e5ea",
    }


_P = _ui_palette()

st.markdown(f"""
<style>
    .block-container {{
        padding-top: 0.8rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2.2rem !important;
        padding-right: 2.2rem !important;
        max-width: 100% !important;
        width: 100% !important;
    }}
    .header-row {{ display:flex; align-items:baseline; gap:0.7rem;
                   flex-wrap:wrap; margin-bottom:0.2rem; }}
    .header-title {{ color:{_P['accent']}; font-size:1.75rem; font-weight:700; }}
    .header-byline {{ color:{_P['muted']}; font-size:0.85rem; }}
    /* Sidebar credit block, rendered at the foot of the sidebar. */
    .brand-block {{ border-top:1px solid {_P['border']}; padding-top:0.75rem;
                    margin-top:0.35rem; }}
    .brand-name {{ color:{_P['accent']}; font-size:1.05rem; font-weight:700;
                   line-height:1.2; }}
    .brand-byline {{ color:{_P['muted']}; font-size:0.75rem; }}
    .brand-copy {{ color:{_P['muted']}; font-size:0.75rem;
                   margin-top:0.35rem; }}
    /* Contact links at the foot of the sidebar. Two columns of raw markdown
       wrapped awkwardly and set at body size, so the pair is one small row of
       inline links with a hairline above it. */
    .brand-contact {{ border-top:1px solid {_P['border']}; margin-top:0.7rem;
                      padding-top:0.55rem; font-size:0.72rem; line-height:1.9;
                      color:{_P['muted']}; white-space:nowrap; }}
    .brand-contact a {{ color:{_P['muted']}; text-decoration:none; }}
    .brand-contact a:hover {{ color:{_P['accent']}; text-decoration:underline; }}
    .brand-contact .sep {{ color:{_P['border']}; padding:0 0.4rem; }}
    .metric-card {{
        background:{_P['card']}; border:1px solid {_P['border']}; border-radius:12px;
        padding:1rem 1.4rem; text-align:center; margin-bottom:0.5rem;
    }}
    .metric-num   {{ font-size:2rem; font-weight:700; }}
    .metric-label {{ font-size:0.8rem; color:{_P['muted']}; margin-top:0.2rem;
                      text-transform:uppercase; letter-spacing:0.06em; }}
    .log-ok    {{ color:{_P['ok']}; font-size:0.83rem; padding:1px 0; }}
    .log-fail  {{ color:{_P['fail']}; font-size:0.83rem; padding:1px 0; }}
    .log-skip  {{ color:{_P['warn']}; font-size:0.83rem; padding:1px 0; }}
    .log-warn  {{ color:{_P['warn']}; font-size:0.83rem; padding:1px 0; }}
    .log-retry {{ color:{_P['warn']}; font-size:0.83rem; font-weight:600;
                  padding:3px 0; }}
    .log-stop  {{ color:{_P['fail']}; font-size:0.9rem;  font-weight:700;
                  padding:4px 0; }}
    .stProgress > div > div {{ background-color:{_P['accent']} !important; }}

    /* Hide Streamlit's native chrome so the app keeps its own header. */
    [data-testid="stStatusWidget"] {{ display: none !important; }}
    .stDeployButton,
    [data-testid="stDeployButton"],
    [data-testid="stAppDeployButton"],
    [data-testid="stMainMenu"] {{ display: none !important; }}

    /* The sidebar toggle lives inside the toolbar, so hiding the toolbar (or
       every header button) also hides stExpandSidebarButton -- the only way to
       reopen a collapsed sidebar. Hide the decorations individually instead and
       force the toggle to stay visible and legible on the cream background. */
    [data-testid="stExpandSidebarButton"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapsed"] {{
        display: flex !important;
        visibility: visible !important;
        opacity: 1 !important;
    }}
    [data-testid="stExpandSidebarButton"] button,
    [data-testid="stSidebarCollapseButton"] button {{
        display: inline-flex !important;
        background: {_P['accent']} !important;
        color: #ffffff !important;
        border-radius: 50% !important;
    }}
    [data-testid="stExpandSidebarButton"] svg,
    [data-testid="stSidebarCollapseButton"] svg {{
        fill: #ffffff !important;
        stroke: #ffffff !important;
    }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
</style>
""", unsafe_allow_html=True)

try:
    import cloudscraper
    from bs4 import BeautifulSoup
except ImportError as e:
    st.error(f"Missing dependency: {e}. Run: pip install cloudscraper beautifulsoup4")
    st.stop()

# ══════════════════════════════════════════════════════════════════════════════
# DOWNLOADER CORE
# ══════════════════════════════════════════════════════════════════════════════
SCIHUB_MIRRORS   = ["https://sci-hub.ee/", "https://sci-hub.se/", "https://sci-hub.st/", "https://sci-hub.ru/"]
ANNAS_SCIDB_BASE = "https://annas-archive.gd/scidb/"
# Never hard-code an API key. A committed key is public the moment the repo is
# pushed, and Elsevier keys are account-bound: it has to be rotated, not just
# deleted. Resolution order is Elsevier's own env var, then Streamlit secrets
# (set them in .streamlit/secrets.toml, which is git-ignored).
ELSEVIER_API_KEY = (os.environ.get("ELSEVIER_API_KEY")
                    or os.environ.get("SCOPUS_API_KEY") or "")
if not ELSEVIER_API_KEY:
    try:
        ELSEVIER_API_KEY = str(st.secrets["ELSEVIER_API_KEY"])
    except Exception:
        ELSEVIER_API_KEY = ""
ELSEVIER_API_URL = "https://api.elsevier.com/content/article/doi/{doi}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
}
PUBLISHER_PREFIXES = {
    "10.1016":"elsevier",
    "10.1108":"emerald",
    "10.1111":"wiley","10.1002":"wiley","10.1007":"springer","10.1038":"springer",
    "10.1057":"springer","10.1140":"springer","10.1080":"tandfonline","10.1081":"tandfonline",
    "10.3390":"mdpi","10.3389":"frontiers","10.1093":"pmc_candidate","10.1371":"plos",
    "10.1136":"bmj","10.1109":"ieee","10.1145":"acm","10.1021":"acs",
    "10.1017":"cambridge","10.1098":"royalsociety","10.1039":"rsc",
}

def make_scraper():
    s = cloudscraper.create_scraper(
        browser={"browser":"chrome","platform":"windows","mobile":False})
    apply_credentials(s)
    return s

# ── OPTIONAL PUBLISHER ACCESS ────────────────────────────────────────────────
# Wiley (and to a lesser extent Elsevier) gate their /doi/pdf/ endpoints behind
# an account. Both can be unlocked without touching the code:
#   WILEY_COOKIE -- paste the Cookie header from a browser tab where you are
#                   already signed in to onlinelibrary.wiley.com
#   ELSEVIER_API_KEY -- an Elsevier/Scopus API key (raises the entitlement tier)
# Both are optional; every other source keeps working with them empty.
WILEY_COOKIE     = ""
ELSEVIER_USER_KEY = ""
DIRECT_LINKS     = {}          # doi -> [url, ...]
DEFAULT_LINKS    = []          # urls tried for any DOI

def apply_credentials(scraper):
    """Attach the user's optional publisher credentials to a session."""
    cookie = (WILEY_COOKIE or "").strip()
    if cookie:
        try:
            pairs = [p.strip() for p in cookie.split(";") if "=" in p]
            scraper.cookies.set("I2KBRCK", "", domain="onlinelibrary.wiley.com", path="/")
            for p in pairs:
                k, _, v = p.partition("=")
                scraper.cookies.set(k.strip(), v.strip(),
                                    domain="onlinelibrary.wiley.com", path="/")
        except Exception:
            pass
    return scraper

def wiley_headers():
    h = {**HEADERS, "Referer": "https://onlinelibrary.wiley.com/"}
    cookie = (WILEY_COOKIE or "").strip()
    if cookie:
        h["Cookie"] = cookie
    return h

def parse_direct_links(raw):
    """
    Turn the user's textarea into DIRECT_LINKS / DEFAULT_LINKS.
    Accepted per line:
        10.1111/joss.70003 = https://...     DOI-pinned link
        10.1111/joss.70003  https://...      (whitespace separated)
        https://...                          bare url, matched by DOI later
    `{doi}` in any url is substituted with the DOI being processed.
    """
    links, defaults = {}, []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        doi, url = None, None
        if "=" in line and "://" in line.split("=")[-1]:
            doi, url = line.split("=", 1)
        elif line.count(" ") and "://" in line:
            parts = line.split(None, 1)
            doi, url = parts[0], parts[1]
        elif "://" in line:
            url = line
        else:
            continue
        doi = (doi or "").strip().lower()
        url = url.strip().strip('<>')
        if not url.startswith("http"):
            continue
        if doi:
            links.setdefault(doi, []).append(url)
        else:
            defaults.append(url)
    return links, defaults

def sanitize_filename(text):
    clean = re.sub(r'[\\/*?:"<>|\n\r\t]', " ", text)
    clean = re.sub(r' +', " ", clean).strip()
    return clean[:180].rstrip(". ") + ".pdf"

_TITLE_CACHE = {}

def _is_real_title(t, doi=""):
    """True only when `t` is a genuine article title and not a DOI or placeholder."""
    if not t:
        return False
    ts = str(t).strip()
    if len(ts) < 6:
        return False
    tl = ts.lower()
    if tl.startswith(("10.", "http://", "https://", "paper with doi", "doi:", "untitled")):
        return False
    if doi and tl == str(doi).strip().lower():
        return False
    if re.fullmatch(r"10\.\d{4,9}/\S+", tl):
        return False
    return True

def fetch_title(doi):
    if not doi:
        return None
    key = doi.strip().lower()
    if key in _TITLE_CACHE and _is_real_title(_TITLE_CACHE[key], key):
        return _TITLE_CACHE[key]
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=HEADERS, timeout=8)
        if r.status_code == 200:
            t = (r.json().get("message",{}).get("title") or [None])[0]
            if t:
                t = re.sub(r"<[^>]+>", "", str(t)).strip()
                if _is_real_title(t, key):
                    _TITLE_CACHE[key] = t
                    return t
    except Exception:
        pass
    try:
        r2 = requests.get(f"https://api.openalex.org/works/https://doi.org/{doi}", headers=HEADERS, timeout=8)
        if r2.status_code == 200:
            t = r2.json().get("title") or r2.json().get("display_name")
            if t:
                t = re.sub(r"<[^>]+>", "", str(t)).strip()
                if _is_real_title(t, key):
                    _TITLE_CACHE[key] = t
                    return t
    except Exception:
        pass
    try:
        r3 = requests.get(f"https://api.unpaywall.org/v2/{doi}?email={DEFAULT_EMAIL}", headers=HEADERS, timeout=8)
        if r3.status_code == 200:
            t = r3.json().get("title")
            if t:
                t = re.sub(r"<[^>]+>", "", str(t)).strip()
                if _is_real_title(t, key):
                    _TITLE_CACHE[key] = t
                    return t
    except Exception:
        pass
    return None

# ── PDF INTEGRITY ───────────────────────────────────────────────────────────
# Two things were previously invisible to the pipeline and both produce a PDF
# that opens as "only the first page":
#   1. truncated transfers -- a dropped connection still yields a body that
#      starts with %PDF and clears the size floor, but the page tree and xref
#      live at the END of the file, so the reader shows page 1 and stops.
#   2. publisher "preview" PDFs -- paywalled articles often return a genuine
#      1-page sample that passes every size/header check.
PDF_MIN_BYTES  = 10_000
DOWNLOAD_TRIES = 3
EOF_WINDOW     = 2048

_OBJ_RE = re.compile(rb"(\d+)\s+0\s+obj(.*?)endobj", re.S)

def count_pdf_pages(data):
    """
    Page count. Uses a real PDF parser first, because the page tree of many
    publisher PDFs lives inside a compressed object stream (/ObjStm) where
    regex cannot see /Type /Page at all -- those files used to be reported as
    1 page. Falls back to scanning uncompressed objects, then to 0 (unknown).
    """
    if PdfReader is not None:
        try:
            n = len(PdfReader(io.BytesIO(data), strict=False).pages)
            if n > 0:
                return n
        except Exception:
            pass
    page_objs, tree_max = 0, 0
    try:
        for _, body in _OBJ_RE.findall(data):
            if re.search(rb"/Type\s*/Pages\b", body):
                m = re.search(rb"/Count\s+(\d+)", body)
                if m:
                    c = int(m.group(1))
                    if c > tree_max:
                        tree_max = c
            elif re.search(rb"/Type\s*/Page\b", body):
                page_objs += 1
        if tree_max == 0 and page_objs == 0:
            page_objs = len(re.findall(rb"/Type\s*/Page\b", data))
    except Exception:
        pass
    count = tree_max or page_objs
    return count if count > 0 else 0

def pdf_is_complete(data):
    """(ok, reason) -- is this a whole PDF rather than a fragment or an error page?"""
    if not data.startswith(b"%PDF") and b"%PDF" not in data[:1024]:
        return False, "not a PDF (HTML or error page)"
    if b"%%EOF" not in data[-EOF_WINDOW:]:
        return False, "truncated: no %%EOF trailer"
    # Also check for common corruption indicators
    if b"Error 403" in data[:200] or b"Access Denied" in data[:200] or b"404 Not Found" in data[:200]:
        return False, "error page"
    return True, ""

def store_pdf(dest, data, min_bytes=PDF_MIN_BYTES):
    """Validate, then write. Returns (ok, pages); pages==0 means unknown."""
    if len(data) < min_bytes: return False, 0
    ok, _ = pdf_is_complete(data)
    if not ok: return False, 0
    dest.write_bytes(data)
    return True, count_pdf_pages(data)

def _length_mismatch(r, got):
    """True when the server promised more bytes than we actually received."""
    if r.headers.get("Content-Encoding"):   # compressed: Content-Length is the wire size
        return False
    cl = r.headers.get("Content-Length", "")
    return cl.isdigit() and int(cl) != got

def _curl_get_pdf_bytes(url, timeout=60):
    """
    Fetch a URL with a real browser TLS fingerprint (curl_cffi). Publishers and
    preprint servers behind Cloudflare/Akamai (preprints.org, MDPI, Wiley, etc.)
    often answer 403 to plain requests/cloudscraper but serve the document to
    a genuine Chrome TLS fingerprint. Returns bytes or None.
    """
    if curl_requests is None: return None
    try:
        s = curl_requests.Session(impersonate="chrome")
        base = "/".join(url.split("/")[:3]) + "/"
        try:
            s.get(base, timeout=15)
        except Exception:
            pass
        cookie = (WILEY_COOKIE or "").strip()
        hdrs = {**HEADERS, "Accept": "application/pdf,application/octet-stream,application/xhtml+xml,*/*;q=0.8",
                "Referer": base, "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate", "Sec-Fetch-Site": "same-origin"}
        if cookie and "wiley.com" in url:
            hdrs["Cookie"] = cookie
        r = s.get(url, timeout=timeout, allow_redirects=True, headers=hdrs)
        body = r.content
        if body and (body[:1024].lstrip()[:4] == b"%PDF" or b"%PDF" in body[:1024]):
            return body
    except Exception:
        pass
    return None

def _curl_get_html(url, timeout=25):
    """Fetch HTML with Chrome TLS impersonation (useful when Scholar or publisher blocks requests)."""
    if curl_requests is None: return None, None
    try:
        s = curl_requests.Session(impersonate="chrome")
        base = "/".join(url.split("/")[:3]) + "/"
        hdrs = {**HEADERS, "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Referer": base}
        r = s.get(url, timeout=timeout, allow_redirects=True, headers=hdrs)
        if r.status_code == 200 and r.text:
            return r.text, str(r.url)
    except Exception:
        pass
    return None, None

def save_pdf(url, dest, scraper, tries=DOWNLOAD_TRIES):
    """Download a PDF, rejecting truncated bodies and falling back to Chrome TLS impersonation on 401/403."""
    if not url or not url.startswith("http"):
        return False
    need_curl_fallback = False
    for _ in range(tries):
        try:
            h = {**HEADERS, "Accept":"application/pdf,application/octet-stream;q=0.9,*/*;q=0.8",
                 "Referer": "/".join(url.split("/")[:3])+"/",
                 "Cache-Control": "no-cache"}
            r = scraper.get(url, headers=h, timeout=60, stream=True, allow_redirects=True)
            if r.status_code in (401, 403, 429):
                need_curl_fallback = True
                break
            if r.status_code == 404:
                return False
            try:
                r.raise_for_status()
            except Exception:
                need_curl_fallback = True
                continue
            ct = r.headers.get("Content-Type","").lower()
            data = b"".join(r.iter_content(16384))
            if data[:1024].lstrip()[:4] == b"%PDF" or b"%PDF" in data[:1024]:
                if _length_mismatch(r, len(data)):
                    continue
                ok, _ = store_pdf(dest, data)
                if ok:
                    return True
            if "text/html" in ct and "pdf" not in ct:
                # Could be a landing page or a Cloudflare challenge HTML
                need_curl_fallback = True
                break
            if _length_mismatch(r, len(data)):
                continue                      # partial body: retry
            if not pdf_is_complete(data)[0]:
                need_curl_fallback = True
                continue                      # truncated: retry
            ok, pages = store_pdf(dest, data)
            if ok:
                return True
        except Exception:
            need_curl_fallback = True
            continue

    if need_curl_fallback or curl_requests is not None:
        raw_bytes = _curl_get_pdf_bytes(url, timeout=60)
        if raw_bytes:
            ok, _ = store_pdf(dest, raw_bytes)
            if ok:
                return True
    return False

def try_unpaywall(doi,dest,scraper,email):
    try:
        r = requests.get(f"https://api.unpaywall.org/v2/{doi}?email={email}", timeout=15)
        if r.status_code != 200: return False
        data = r.json(); cands = []
        best = data.get("best_oa_location") or {}
        for k in ("url_for_pdf","url"):
            if best.get(k): cands.append(best[k])
        for loc in data.get("oa_locations",[]):
            for k in ("url_for_pdf","url"):
                v = loc.get(k)
                if v and v not in cands: cands.append(v)
        for u in cands:
            if save_pdf(u,dest,scraper): return True
    except Exception: pass
    return False

def try_semantic_scholar(doi,dest,scraper,email):
    try:
        r = requests.get(f"https://api.semanticscholar.org/graph/v1/paper/DOI:{doi}?fields=openAccessPdf,title",
                         headers=HEADERS, timeout=15)
        if r.status_code == 200:
            j = r.json()
            t = j.get("title")
            if t and doi.strip().lower() not in _TITLE_CACHE:
                _TITLE_CACHE[doi.strip().lower()] = t
            u = (j.get("openAccessPdf") or {}).get("url")
            if u and save_pdf(u,dest,scraper): return True
    except Exception: pass
    return False

def _extract_openalex_urls(work):
    cands = []
    if not isinstance(work, dict):
        return cands
    oa = work.get("open_access") or {}
    if oa.get("oa_url"):
        cands.append(oa["oa_url"])
    locs = [work.get("best_oa_location") or {}, work.get("primary_location") or {}] + (work.get("locations") or [])
    for loc in locs:
        if not isinstance(loc, dict):
            continue
        for k in ("pdf_url", "landing_page_url"):
            u = loc.get(k)
            if u and u not in cands:
                if k == "pdf_url" or any(x in u.lower() for x in (".pdf", "download", "file/get", "manuscript")):
                    cands.append(u)
    return cands

def try_openalex(doi,dest,scraper,email):
    try:
        r = requests.get(f"https://api.openalex.org/works/https://doi.org/{doi}",
                         headers={**HEADERS,"mailto":email}, timeout=15)
        if r.status_code == 200:
            data = r.json()
            t = data.get("title") or data.get("display_name")
            if t and doi.strip().lower() not in _TITLE_CACHE:
                _TITLE_CACHE[doi.strip().lower()] = t
            for u in _extract_openalex_urls(data):
                if save_pdf(u, dest, scraper):
                    return True
    except Exception:
        pass
    # Fallback: search OpenAlex by title (catches preprints with a different DOI, e.g., preprints.org)
    try:
        title = fetch_title(doi)
        if title and len(title) > 12:
            from urllib.parse import quote_plus
            norm_target = re.sub(r"[^a-z0-9]", "", title.lower())
            r2 = requests.get(
                f"https://api.openalex.org/works?search={quote_plus(title)}&per-page=5",
                headers={**HEADERS, "mailto": email}, timeout=15
            )
            if r2.status_code == 200:
                for work in r2.json().get("results", []):
                    wt = work.get("title") or work.get("display_name") or ""
                    norm_wt = re.sub(r"[^a-z0-9]", "", wt.lower())
                    if norm_wt and (norm_wt == norm_target or norm_target in norm_wt or norm_wt in norm_target):
                        for u in _extract_openalex_urls(work):
                            if save_pdf(u, dest, scraper):
                                return True
    except Exception:
        pass
    return False

def try_crossref(doi,dest,scraper,email):
    """Check Crossref full-text links (message.link and primary resource URL)."""
    try:
        r = requests.get(f"https://api.crossref.org/works/{doi}", headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return False
        msg = r.json().get("message", {})
        t = (msg.get("title") or [None])[0]
        if t and doi.strip().lower() not in _TITLE_CACHE:
            _TITLE_CACHE[doi.strip().lower()] = re.sub(r"<[^>]+>", "", t).strip()
        cands = []
        for lk in msg.get("link", []):
            u = lk.get("URL", "")
            ct = (lk.get("content-type") or "").lower()
            if u and ("pdf" in ct or "unspecified" in ct or any(p in u.lower() for p in (".pdf", "download", "file/get", "article"))):
                if u not in cands:
                    cands.append(u)
        prim = (msg.get("resource") or {}).get("primary", {}).get("URL")
        if prim and any(p in prim.lower() for p in (".pdf", "download", "file/get")) and prim not in cands:
            cands.append(prim)
        for u in cands:
            if save_pdf(u, dest, scraper):
                return True
    except Exception:
        pass
    return False

def try_mdpi(doi,dest,scraper,email):
    if not doi.startswith("10.3390/"): return False
    try:
        r = requests.get(f"https://api.unpaywall.org/v2/{doi}?email={email}", timeout=15)
        if r.status_code != 200: return False
        data = r.json()
        for loc in data.get("oa_locations",[]):
            for k in ("url_for_pdf","url"):
                val = loc.get(k,"") or ""
                m = re.search(r'/pdf/([a-z0-9\-]+)\.pdf', val)
                if m:
                    slug = m.group(1); journal = slug.rsplit("-",2)[0]
                    url = f"https://res.mdpi.com/{journal}/{slug}/article_deploy/{slug}.pdf"
                    if save_pdf(url,dest,scraper): return True
    except Exception: pass
    return False

def try_elsevier(doi,dest,scraper,email):
    try:
        keys = [k for k in (ELSEVIER_USER_KEY, ELSEVIER_API_KEY) if k]
        env_k = os.environ.get("ELSEVIER_API_KEY") or os.environ.get("SCOPUS_API_KEY")
        if env_k and env_k not in keys:
            keys.append(env_k)

        cand_urls = [ELSEVIER_API_URL.format(doi=doi)]
        if doi.startswith("10.1016"):
            try:
                cr_r = requests.get(f"https://api.crossref.org/works/{doi}", headers=HEADERS, timeout=10)
                if cr_r.status_code == 200:
                    for lk in cr_r.json().get("message", {}).get("link", []):
                        u_lk = lk.get("URL", "")
                        if "PII:" in u_lk:
                            pii = u_lk.split("PII:")[1].split("?")[0]
                            cand_urls.append(f"https://api.elsevier.com/content/article/pii/{pii}?httpAccept=application/pdf")
                            cand_urls.append(f"https://www.sciencedirect.com/science/article/pii/{pii}/pdfft?isBuildApp=pdf")
            except Exception:
                pass

        for url in cand_urls:
            for key in (keys or [""]):
                h = {**HEADERS, "Accept": "application/pdf"}
                if key:
                    h["X-ELS-APIKey"] = key
                r = scraper.get(url, headers=h, timeout=30, stream=True)
                if r.status_code in (401, 403, 404, 429):
                    continue
                try:
                    r.raise_for_status()
                except Exception:
                    continue
                ct = r.headers.get("Content-Type", "").lower()
                data = b"".join(r.iter_content(16384))
                if data.startswith(b"%PDF") or ("pdf" in ct and len(data) > 3000):
                    ok, _ = store_pdf(dest, data)
                    if ok:
                        return True
    except Exception:
        pass
    return False

def resolve_doi_url(doi,scraper):
    try:
        r = scraper.get(f"https://doi.org/{doi}", headers=HEADERS, timeout=20, allow_redirects=True)
        if r.status_code == 200: return r.url
    except Exception: pass
    if curl_requests is not None:
        _, final_u = _curl_get_html(f"https://doi.org/{doi}", timeout=20)
        if final_u:
            return final_u
    return None

def _extract_pdf_links_from_page(soup, base_url):
    """Extract all candidate PDF URLs from a publisher/repository landing page."""
    from urllib.parse import urljoin
    found = []
    if not soup:
        return found
    # 1. Standard academic <meta name="citation_pdf_url"> / Highwire Press / Dublin Core tags
    for meta in soup.find_all("meta"):
        mname = (meta.get("name") or meta.get("property") or "").lower()
        if mname in ("citation_pdf_url", "bepress_citation_pdf_url", "eprints.document_url", "dc.identifier.uri"):
            content = (meta.get("content") or "").strip()
            if content:
                full_u = urljoin(base_url, content)
                if full_u.startswith("http") and full_u not in found:
                    found.append(full_u)
    # 2. Anchor links pointing to PDF downloads (OJS, Detritus, Preprints, ScienceDirect, etc.)
    for a in soup.select("a[href]"):
        text = a.get_text(" ", strip=True).lower()
        href = (a.get("href") or "").strip()
        if not href or href.startswith(("javascript:", "mailto:", "#")):
            continue
        href_low = href.lower()
        is_pdf_text = (
            text in ("pdf", "download", "download pdf", "full text pdf", "view pdf", "article pdf")
            or any(p in text for p in ["download pdf", "pdf download", "full text pdf", "[pdf]", "view pdf", "download full text", "scarica pdf"])
        )
        is_pdf_href = (
            href_low.endswith(".pdf")
            or ".pdf?" in href_low
            or any(p in href_low for p in [
                "/file/get?code=", "/file/download", "download_pub",
                "pdf.sciencedirectassets.com", "pdfft", "/article/download/",
                "/bitstream/", "/deliver/fulltext/"
            ])
        )
        if is_pdf_text or is_pdf_href:
            full_u = urljoin(base_url, href)
            if full_u.startswith("http") and full_u not in found:
                found.append(full_u)
    return found

def _extract_pdf_from_page(soup,base_url):
    links = _extract_pdf_links_from_page(soup, base_url)
    return links[0] if links else None

def _build_publisher_urls(doi,publisher,resolved_url=None):
    urls = []
    if publisher=="elsevier":
        urls += [
            f"https://api.elsevier.com/content/article/doi/{doi}?httpAccept=application/pdf",
        ]
        if resolved_url and "pii/" in resolved_url:
            pii_val = resolved_url.split("pii/")[1].split("?")[0].split("/")[0]
            urls.append(f"https://api.elsevier.com/content/article/pii/{pii_val}?httpAccept=application/pdf")
            urls.append(f"https://www.sciencedirect.com/science/article/pii/{pii_val}/pdfft?isBuildApp=pdf")
    elif publisher=="wiley":
        urls += [f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
                 f"https://onlinelibrary.wiley.com/doi/pdf/{doi}",
                 f"https://onlinelibrary.wiley.com/doi/epdf/{doi}",
                 f"https://onlinelibrary.wiley.com/doi/{doi}.pdf"]
        if resolved_url:
            base = resolved_url.split("?")[0].rstrip("/")
            for s in ["/pdf","/pdfdirect","/epdf",".pdf"]: urls.append(base+s)
    elif publisher=="springer":
        urls += [f"https://link.springer.com/content/pdf/{doi}.pdf",
                 f"https://link.springer.com/openurl/pdf?id=doi:{doi}"]
    elif publisher=="tandfonline":
        urls += [f"https://www.tandfonline.com/doi/pdf/{doi}",
                 f"https://www.tandfonline.com/doi/epdf/{doi}"]
    elif publisher=="frontiers":
        urls += [f"https://www.frontiersin.org/articles/{doi}/pdf"]
        if resolved_url: urls.append(resolved_url.split("?")[0].rstrip("/")+"/pdf")
    elif publisher=="plos":
        for j in ["plosone","plosbiology","ploscompbiol"]:
            urls.append(f"https://journals.plos.org/{j}/article/file?id={doi}&type=printable")
    elif publisher=="bmj":
        urls += [f"https://www.bmj.com/content/lookup/doi/{doi}.full.pdf"]
    elif publisher=="royalsociety":
        urls += [f"https://royalsocietypublishing.org/doi/pdf/{doi}",
                 f"https://royalsocietypublishing.org/doi/epdf/{doi}"]
    elif publisher=="rsc":  urls += [f"https://pubs.rsc.org/en/content/articlepdf/{doi}"]
    elif publisher=="acm":  urls += [f"https://dl.acm.org/doi/{doi}"]
    elif publisher=="acs":  urls += [f"https://pubs.acs.org/doi/pdf/{doi}"]
    elif publisher=="emerald":
        slug = doi.split("/", 1)[-1] if "/" in doi else doi
        urls += [
            f"https://www.emerald.com/insight/content/doi/{doi}/full/pdf",
            f"https://www.emerald.com/insight/content/doi/{doi}",
        ]
    if resolved_url:
        urls.append(resolved_url)
    urls.append(f"https://doi.org/{doi}")
    return urls

def try_publisher_direct(doi,dest,scraper,email):
    pub = PUBLISHER_PREFIXES.get(doi[:7])
    if pub in ("mdpi","pmc_candidate"): return False
    resolved = resolve_doi_url(doi,scraper)
    candidate_urls = _build_publisher_urls(doi,pub,resolved)
    if pub == "wiley":
        candidate_urls.insert(0, f"https://onlinelibrary.wiley.com/doi/epdf/{doi}")
    seen = set()
    urls = []
    for u in candidate_urls:
        if u and u not in seen:
            seen.add(u)
            urls.append(u)
    for url in urls:
        try:
            ref = "/".join(url.split("/")[:3]) + "/"
            r = scraper.get(url, headers={**HEADERS, "Referer": ref}, timeout=20, stream=True, allow_redirects=True)
            html_text = None
            final_url = url
            if r.status_code in (200, 206):
                final_url = str(r.url)
                ct = r.headers.get("Content-Type","").lower()
                data = b"".join(r.iter_content(16384))
                if data.startswith(b"%PDF") or b"%PDF" in data[:1024]:
                    ok, _ = store_pdf(dest, data)
                    if ok: return True
                if "pdf" in ct or "octet-stream" in ct:
                    if not _length_mismatch(r, len(data)):
                        ok, _ = store_pdf(dest, data)
                        if ok: return True
                try:
                    html_text = data.decode("utf-8", errors="ignore")
                except Exception:
                    html_text = None
            elif r.status_code in (401, 403, 429) and curl_requests is not None:
                html_text, curled_url = _curl_get_html(url, timeout=18)
                if curled_url:
                    final_url = curled_url
            if html_text:
                soup = BeautifulSoup(html_text, "html.parser")
                for link in _extract_pdf_links_from_page(soup, final_url):
                    if save_pdf(link, dest, scraper):
                        return True
        except Exception:
            continue
    return False

def try_pmc(doi,dest,scraper,email):
    try:
        conv = requests.get("https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/",
                            params={"ids":doi,"format":"json","email":email},
                            headers=HEADERS, timeout=10)
        if conv.status_code != 200: return False
        records = conv.json().get("records",[])
        if not records or "pmcid" not in records[0]: return False
        pmcid = records[0]["pmcid"]
        return save_pdf(f"https://www.ncbi.nlm.nih.gov/pmc/articles/{pmcid}/pdf/",dest,scraper)
    except Exception: pass
    return False

def try_core(doi,dest,scraper,email):
    try:
        r = requests.get("https://api.core.ac.uk/v3/works",
                         params={"q":f"doi:{doi}","limit":1}, headers=HEADERS, timeout=12)
        if r.status_code != 200: return False
        results = r.json().get("results",[])
        if not results: return False
        u = results[0].get("downloadUrl") or results[0].get("fullTextLink")
        if u and save_pdf(u,dest,scraper): return True
    except Exception: pass
    return False

_MIRROR_BLOCKED = {"annas": False, "scihub": set()}

def try_annas_archive(doi,dest,scraper,email):
    if _MIRROR_BLOCKED.get("annas"):
        return False
    try:
        r = scraper.get(ANNAS_SCIDB_BASE+doi, headers=HEADERS, timeout=8)
        if "Web Filter Violation" in (r.text or "") or "FortiGuard" in (r.text or ""):
            _MIRROR_BLOCKED["annas"] = True
            return False
        if r.status_code != 200: return False
        soup = BeautifulSoup(r.text,"html.parser"); pdf_url = None
        for a in soup.select("a[href]"):
            if a.get_text(strip=True).lower()=="download" and a.get("href","").startswith("http"):
                pdf_url = a["href"]; break
        if not pdf_url:
            for a in soup.select("a[href]"):
                h = a.get("href","")
                if ".pdf" in h and h.startswith("http"): pdf_url = h; break
        if pdf_url and save_pdf(pdf_url,dest,scraper): return True
    except Exception:
        _MIRROR_BLOCKED["annas"] = True
    return False

def _scholar_fetch_html(url, scraper):
    """Fetch a Google Scholar search page using cloudscraper, falling back to curl_cffi Chrome TLS."""
    try:
        r = scraper.get(url, headers={**HEADERS, "Accept-Language": "en-US,en;q=0.9"}, timeout=15)
        if r.status_code == 200 and r.text and "gs_r" in r.text:
            return r.text
    except Exception:
        pass
    html_text, _ = _curl_get_html(url, timeout=15)
    return html_text

def _scholar_extract_candidates(html_text):
    """Return (pdf_urls, cluster_urls) from a Google Scholar results page."""
    pdf_urls, cluster_urls = [], []
    if not html_text:
        return pdf_urls, cluster_urls
    soup = BeautifulSoup(html_text, "html.parser")
    # 1. Right-side direct [PDF] links (e.g. [PDF] preprints.org, [PDF] emerald.com, [PDF] researchgate.net)
    for a in soup.select("div.gs_or_ggsm a[href], div.gs_ggs a[href]"):
        href = (a.get("href") or "").strip()
        if href.startswith("http") and href not in pdf_urls:
            pdf_urls.append(href)
    # 2. Any other PDF link inside result blocks
    for a in soup.select("a[href]"):
        href = (a.get("href") or "").strip()
        text = a.get_text(" ", strip=True).lower()
        if not href:
            continue
        if "/scholar?cluster=" in href:
            full_cluster = "https://scholar.google.com" + href if href.startswith("/") else href
            if full_cluster not in cluster_urls:
                cluster_urls.append(full_cluster)
            continue
        if href.startswith("http") and "scholar.google." not in href and "google.com/" not in href:
            hlow = href.lower()
            if "[pdf]" in text or hlow.endswith(".pdf") or "casa_token=" in hlow or any(k in hlow for k in ("download_pub", "/file/download", "/file/get?code=", "/pdf/", "article-pdf")):
                if href not in pdf_urls:
                    pdf_urls.append(href)
    return pdf_urls, cluster_urls

def _scan_browser_sessions_and_downloads(doi, dest, scraper):
    """
    Check the user's local ~/Downloads folder and active Chrome/Edge session/history
    for any already-downloaded PDF or signed URL (such as Google Scholar `casa_token`
    or `pdf.sciencedirectassets.com`) matching this DOI.
    """
    slug = (doi.split("/", 1)[-1] if "/" in doi else doi).strip().lower()
    if not slug or len(slug) < 4:
        return False
    title = _TITLE_CACHE.get(doi.strip().lower(), "")
    clean_title_prefix = sanitize_filename(title)[:-4].lower()[:40] if _is_real_title(title, doi) else ""

    # 1. Check ~/Downloads for a matching PDF file downloaded in Chrome/Edge
    dl_dir = Path.home() / "Downloads"
    if dl_dir.exists():
        for p in sorted(dl_dir.glob("*.pdf"), key=lambda x: x.stat().st_mtime, reverse=True)[:80]:
            pname = p.stem.lower()
            # Strip Chrome's " (1)", " (2)" duplicate suffixes
            pname_base = re.sub(r"\s*\(\d+\)$", "", pname)
            if (
                pname_base == slug
                or slug in pname_base
                or doi.replace("/", "_").lower() in pname_base
                or (clean_title_prefix and len(clean_title_prefix) > 15 and clean_title_prefix in pname_base)
            ):
                try:
                    raw = p.read_bytes()
                    ok, _ = store_pdf(dest, raw)
                    if ok:
                        return True
                except Exception:
                    pass

    # 2. Scan active Chrome / Edge Sessions & History for signed PDF URLs (casa_token, sciencedirectassets, etc.)
    signed_urls = []
    local_app = Path(os.environ.get("LOCALAPPDATA", ""))
    browser_roots = [
        local_app / "Google/Chrome/User Data",
        local_app / "Microsoft/Edge/User Data",
    ]
    for root in browser_roots:
        if not root.exists():
            continue
        for prof in root.iterdir():
            if not prof.is_dir() or not (prof.name == "Default" or prof.name.startswith("Profile ")):
                continue
            # Check active session files (Tabs_*, Session_*)
            sess_dir = prof / "Sessions"
            if sess_dir.exists():
                for sf in sorted(sess_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)[:4]:
                    if not sf.name.startswith(("Tabs_", "Session_")):
                        continue
                    tmp_s = Path(tempfile.mktemp(prefix="vellum_sess_"))
                    try:
                        subprocess.run(["esentutl", "/y", str(sf), "/d", str(tmp_s), "/o"],
                                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
                        if tmp_s.exists():
                            b_data = tmp_s.read_bytes()
                            for m in re.finditer(rb'https?://[^\x00-\x1f\x7f-\xff"\'\s<>]{12,450}', b_data):
                                u = m.group(0).decode("ascii", errors="ignore")
                                u_low = u.lower()
                                if slug in u_low and (".pdf" in u_low or "casa_token=" in u_low or "pdfft" in u_low):
                                    if u not in signed_urls:
                                        signed_urls.append(u)
                    except Exception:
                        pass
                    finally:
                        tmp_s.unlink(missing_ok=True)

            # Check History SQLite DB
            hist_db = prof / "History"
            if hist_db.exists():
                tmp_h = Path(tempfile.mktemp( suffix=".db", prefix="vellum_hist_"))
                try:
                    subprocess.run(["esentutl", "/y", str(hist_db), "/d", str(tmp_h), "/o"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=4)
                    if tmp_h.exists():
                        import sqlite3
                        conn = sqlite3.connect(str(tmp_h))
                        cur = conn.cursor()
                        for row in cur.execute(
                            "SELECT url FROM urls WHERE url LIKE ? ORDER BY last_visit_time DESC LIMIT 10",
                            (f"%{slug}%",)
                        ):
                            u = row[0]
                            u_low = u.lower()
                            if ".pdf" in u_low or "casa_token=" in u_low or "pdfft" in u_low:
                                if u not in signed_urls:
                                    signed_urls.append(u)
                        conn.close()
                except Exception:
                    pass
                finally:
                    tmp_h.unlink(missing_ok=True)

    for u in signed_urls:
        if save_pdf(u, dest, scraper):
            return True
    return False

def try_google_scholar(doi,dest,scraper,email):
    """
    Search Google Scholar by DOI first, then by paper title (catching preprints
    such as [PDF] preprints.org, [PDF] emerald.com CASA links, or institutional
    repositories indexed under "All N versions"), and download any linked PDF.
    """
    if _scan_browser_sessions_and_downloads(doi, dest, scraper):
        return True

    from urllib.parse import quote_plus
    queries = [f"https://scholar.google.com/scholar?hl=en&q={quote_plus(doi)}"]
    title = fetch_title(doi)
    if _is_real_title(title, doi):
        q_title = f"https://scholar.google.com/scholar?hl=en&q={quote_plus(title)}"
        if q_title not in queries:
            queries.append(q_title)

    tried_urls = set()
    cluster_queue = []

    def _try_candidate_url(u):
        if u in tried_urls:
            return False
        tried_urls.add(u)
        if save_pdf(u, dest, scraper):
            return True
        # If the Scholar link points to a landing page (e.g. repository page), inspect its meta/PDF links
        try:
            html_page, final_u = _curl_get_html(u, timeout=15)
            if not html_page:
                r = scraper.get(u, headers=HEADERS, timeout=15, allow_redirects=True)
                if r.status_code == 200:
                    html_page, final_u = r.text, str(r.url)
            if html_page:
                psoup = BeautifulSoup(html_page, "html.parser")
                for sub_link in _extract_pdf_links_from_page(psoup, final_u or u)[:4]:
                    if sub_link not in tried_urls:
                        tried_urls.add(sub_link)
                        if save_pdf(sub_link, dest, scraper):
                            return True
        except Exception:
            pass
        return False

    for q_url in queries:
        html_text = _scholar_fetch_html(q_url, scraper)
        if not html_text:
            continue
        pdf_urls, clusters = _scholar_extract_candidates(html_text)
        for c in clusters:
            if c not in cluster_queue:
                cluster_queue.append(c)
        for u in pdf_urls:
            if _try_candidate_url(u):
                return True

    # Follow "All N versions" cluster links (up to 2 clusters) to catch alternate OA / preprint versions
    for c_url in cluster_queue[:2]:
        html_text = _scholar_fetch_html(c_url, scraper)
        if not html_text:
            continue
        pdf_urls, _ = _scholar_extract_candidates(html_text)
        for u in pdf_urls:
            if _try_candidate_url(u):
                return True

    return False

_BROWSER_LOCK = threading.Lock()

def try_browser_assisted(doi, dest, scraper, email):
    """
    Use a persistent Chromium browser profile (DrissionPage) to pass Cloudflare Turnstile
    challenges (Emerald, Wiley, Taylor & Francis, Elsevier) and check Google Scholar /
    publisher PDF endpoints, plus check local ~/Downloads.
    """
    if _scan_browser_sessions_and_downloads(doi, dest, scraper):
        return True
    try:
        from DrissionPage import ChromiumPage, ChromiumOptions
    except ImportError:
        return False

    if not _BROWSER_LOCK.acquire(timeout=25):
        return False
    page = None
    try:
        prof_dir = Path.home() / ".vellum_browser_profile"
        prof_dir.mkdir(parents=True, exist_ok=True)
        co = ChromiumOptions()
        co.set_paths(local_port=9345, user_data_path=str(prof_dir))
        co.headless(False)
        co.set_argument("--window-position=-32000,-32000")
        co.set_argument("--disable-blink-features=AutomationControlled")
        page = ChromiumPage(co)

        # 1. Check Google Scholar in browser (preserves Google Scholar CASA cookies if present)
        from urllib.parse import quote_plus, urljoin
        title = fetch_title(doi)
        q_str = title if _is_real_title(title, doi) else doi
        page.get(f"https://scholar.google.com/scholar?hl=en&q={quote_plus(q_str)}")
        time.sleep(1.5)
        html_sch = page.html or ""
        sch_pdfs, _ = _scholar_extract_candidates(html_sch)

        # 2. Visit DOI landing page to clear Cloudflare Turnstile and discover article-pdf links
        page.get(f"https://doi.org/{doi}")
        for _ in range(10):
            time.sleep(0.8)
            t_cur = (page.title or "").lower()
            if t_cur and "moment" not in t_cur and "cloudflare" not in t_cur:
                break
        cur_url = page.url or f"https://doi.org/{doi}"
        html_lp = page.html or ""
        soup_lp = BeautifulSoup(html_lp, "html.parser")
        lp_pdfs = _extract_pdf_links_from_page(soup_lp, cur_url)
        for m in re.finditer(r'/[a-zA-Z0-9_-]+/article-pdf/[^\s"\'<>]+?\.pdf(?:\?[^\s"\'<>]+)?', html_lp):
            full_em = urljoin(cur_url, m.group(0))
            if full_em not in lp_pdfs:
                lp_pdfs.append(full_em)

        all_cands = []
        for u in sch_pdfs + lp_pdfs:
            if u and u not in all_cands:
                all_cands.append(u)

        for cand in all_cands[:5]:
            try:
                page.run_js("""
                    window.__pdf_status = 'PENDING';
                    fetch(arguments[0], {credentials: 'include'}).then(async r => {
                        if (!r.ok) { window.__pdf_status = 'ERR:' + r.status; return; }
                        const buf = await r.arrayBuffer();
                        const bytes = new Uint8Array(buf);
                        if (bytes.length < 1500 || bytes[0] !== 0x25 || bytes[1] !== 0x50) {
                            window.__pdf_status = 'NOT_PDF';
                            return;
                        }
                        let binary = '';
                        const chunkSize = 0x8000;
                        for (let i = 0; i < bytes.length; i += chunkSize) {
                            binary += String.fromCharCode.apply(null, bytes.subarray(i, i + chunkSize));
                        }
                        window.__pdf_b64 = btoa(binary);
                        window.__pdf_status = 'OK';
                    }).catch(e => { window.__pdf_status = 'ERR:' + e; });
                """, cand)
                for _ in range(20):
                    time.sleep(0.4)
                    st_val = page.run_js("return window.__pdf_status;")
                    if st_val != "PENDING":
                        break
                if st_val == "OK":
                    import base64
                    b64_data = page.run_js("return window.__pdf_b64;")
                    if b64_data:
                        raw_bytes = base64.b64decode(b64_data)
                        ok, _ = store_pdf(dest, raw_bytes)
                        if ok:
                            return True
            except Exception:
                continue
    except Exception:
        pass
    finally:
        try:
            if page is not None:
                page.quit()
        except Exception:
            pass
        _BROWSER_LOCK.release()

    return _scan_browser_sessions_and_downloads(doi, dest, scraper)

def try_scihub(doi,dest,scraper,email):
    for mirror in SCIHUB_MIRRORS:
        if mirror in _MIRROR_BLOCKED["scihub"]:
            continue
        try:
            r = scraper.get(mirror+doi, headers=HEADERS, timeout=8, allow_redirects=True)
            if "Web Filter Violation" in (r.text or "") or "FortiGuard" in (r.text or ""):
                _MIRROR_BLOCKED["scihub"].add(mirror)
                continue
            if r.status_code in (403, 404, 429) or r.status_code >= 500:
                continue
            soup = BeautifulSoup(r.text,"html.parser"); pdf_url = None
            for tag in soup.find_all(["embed","iframe"], id="pdf"):
                src = tag.get("src","")
                if src: pdf_url = src if src.startswith("http") else ("https:"+src if src.startswith("//") else mirror.rstrip('/') + src)
                break
            if not pdf_url:
                m = re.search(r'(https?://[^\s\'"<>]+\.pdf[^\s\'"<>]*)', r.text)
                if m: pdf_url = m.group(1)
            if pdf_url:
                if pdf_url.startswith("//"): pdf_url = "https:"+pdf_url
                if save_pdf(pdf_url,dest,scraper): return True
        except Exception:
            _MIRROR_BLOCKED["scihub"].add(mirror)
            continue
    return False

def try_wiley_direct(doi,dest,scraper,email):
    if not (doi.startswith("10.1111/") or doi.startswith("10.1002/") or doi.lower() in DIRECT_LINKS):
        return False
    urls = [
        f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
        f"https://onlinelibrary.wiley.com/doi/pdf/{doi}",
        f"https://onlinelibrary.wiley.com/doi/epdf/{doi}",
        f"https://onlinelibrary.wiley.com/doi/{doi}.pdf",
    ]
    # A user-supplied Wiley link (from the browser address bar) always wins.
    urls = list(DIRECT_LINKS.get(doi.lower(), [])) + urls
    for url in urls:
        data = b""
        try:
            r = scraper.get(url, headers=wiley_headers(),
                            timeout=25, stream=True, allow_redirects=True)
            if r.status_code in (200, 206):
                data = b"".join(r.iter_content(32768))
        except Exception:
            data = b""
        if data[:1024].lstrip()[:4] != b"%PDF":
            data = _curl_get_pdf_bytes(url, timeout=20) or b""
        if data and store_pdf(dest, data)[0]:
            return True
    return False

def try_direct_link(doi,dest,scraper,email):
    """URLs the user pasted by hand, tried before every automated source."""
    urls = list(DIRECT_LINKS.get(doi.lower(), []))
    if not urls:
        urls = [u for u in DEFAULT_LINKS if doi.lower() in u.lower() or "{doi}" in u]
    for url in urls:
        url = url.replace("{doi}", doi)
        data = b""
        try:
            r = scraper.get(url, headers={**wiley_headers(), "Accept":"application/pdf,*/*;q=0.8"},
                            timeout=45, stream=True, allow_redirects=True)
            if r.status_code in (200, 206):
                data = b"".join(r.iter_content(32768))
        except Exception:
            data = b""
        if data[:1024].lstrip()[:4] != b"%PDF":
            # Cloudflare 403s the plain session but serves the browser-like one
            data = _curl_get_pdf_bytes(url, timeout=45) or b""
        if data and store_pdf(dest, data)[0]:
            return True
    return False

SOURCES = [
    ("Your PDF link",       try_direct_link),
    ("Unpaywall",           try_unpaywall),
    ("OpenAlex",            try_openalex),
    ("Crossref Full-Text",  try_crossref),
    ("Semantic Scholar",    try_semantic_scholar),
    ("Google Scholar",      try_google_scholar),
    ("Publisher Direct",    try_publisher_direct),
    ("MDPI Direct",         try_mdpi),
    ("Elsevier API",        try_elsevier),
    ("Wiley Direct",        try_wiley_direct),
    ("PubMed Central",      try_pmc),
    ("CORE",                try_core),
    ("Browser Session",     try_browser_assisted),
    ("Anna's Archive",      try_annas_archive),
    ("Sci-Hub",             try_scihub),
]

def active_sources():
    """SOURCES minus the user-link source when no links were supplied."""
    if DIRECT_LINKS or DEFAULT_LINKS:
        return SOURCES
    return SOURCES[1:]

def download_single_doi(doi, output_dir, scraper, email, pq, title_hint=None, direct_url=None):
    result = {"doi":doi,"title":None,"status":"failed","source":None,
              "filename":None,"size_kb":0.0,"pages":0,"partial":False}
    valid_hint = title_hint if _is_real_title(title_hint, doi) else None
    if valid_hint and doi:
        _TITLE_CACHE[doi.strip().lower()] = valid_hint
    title = valid_hint
    if not title and not (doi.startswith("http://") or doi.startswith("https://")):
        title = fetch_title(doi)
    if title and doi and _is_real_title(title, doi):
        _TITLE_CACHE[doi.strip().lower()] = title
    result["title"] = title
    clean_key = doi.split("/")[-1].split("?")[0] if ("/" in doi or "?" in doi) else doi
    if _is_real_title(title, doi):
        filename = sanitize_filename(title)
    else:
        filename = sanitize_filename(clean_key)
    result["filename"] = filename
    dest = output_dir / filename
    if dest.exists() and dest.stat().st_size > 3000:
        pages = count_pdf_pages(dest.read_bytes())
        result.update({"status":"success","source":"cached",
                       "size_kb":dest.stat().st_size/1024,"pages":pages,
                       "partial":pages==1})
        pq.put(("skip", doi, title, filename))
        return result

    # 0. Check direct URL first if supplied or if doi itself is a URL
    target_url = direct_url or (doi if (doi.startswith("http://") or doi.startswith("https://")) else None)
    if target_url:
        pq.put(("trying", doi, "Direct URL"))
        try:
            if save_pdf(target_url, dest, scraper):
                data_check = dest.read_bytes()
                pages = count_pdf_pages(data_check)
                size_kb = dest.stat().st_size / 1024
                result.update({"status":"success","source":"Direct URL","size_kb":size_kb,
                               "pages":pages,"partial":pages==1})
                pq.put(("success", doi, "Direct URL", title, filename, size_kb))
                return result
        except Exception:
            if dest.exists(): dest.unlink()

    # A 1-page result is usually a publisher preview rather than the real
    # article, so keep it only as a fallback: try every other source first and
    # prefer the first one that yields a multi-page PDF.
    fallback = None
    for name, fn in active_sources():
        pq.put(("trying", doi, name))
        try: ok = fn(doi, dest, scraper, email)
        except Exception: ok = False
        if not ok:
            if dest.exists(): dest.unlink()   # never leave a stale partial file
            continue
        data_check = dest.read_bytes()
        pages = count_pdf_pages(data_check)
        if pages == 1:
            # A journal article that is exactly 1 page is almost always the
            # publisher's free preview (Elsevier's API and Wiley's ePDF both
            # do this). Park it as a fallback and let the remaining sources try
            # for the real multi-page file.
            if len(data_check) >= 5000:
                fallback = (name, data_check)
                if dest.exists(): dest.unlink()
                pq.put(("preview", doi, name))
            else:
                if dest.exists(): dest.unlink()
            continue
        if pages == 0:
            # Page count undeterminable: only trust it if a real parser also
            # fails on a file this large (rare encrypted/large-scan case).
            size_kb = dest.stat().st_size / 1024
            if dest.stat().st_size > PDF_MIN_BYTES * 4:
                result.update({"status":"success","source":name,"size_kb":size_kb,
                               "pages":pages,"partial":False})
                pq.put(("success", doi, name, title, filename, size_kb))
                return result
            else:
                if dest.exists(): dest.unlink()
                continue
        size_kb = dest.stat().st_size / 1024
        result.update({"status":"success","source":name,"size_kb":size_kb,
                       "pages":pages,"partial":False})
        pq.put(("success", doi, name, title, filename, size_kb))
        return result

    if fallback:
        name, data = fallback
        dest.write_bytes(data)
        size_kb = dest.stat().st_size / 1024
        result.update({"status":"success","source":name,"size_kb":size_kb,
                       "pages":1,"partial":True})
        pq.put(("partial", doi, name, title, filename, size_kb))
        return result

    # Last resort: try generic direct PDF URLs
    last_resort_urls = [
        f"https://onlinelibrary.wiley.com/doi/epdf/{doi}",
        f"https://onlinelibrary.wiley.com/doi/pdf/{doi}",
        f"https://onlinelibrary.wiley.com/doi/pdfdirect/{doi}",
    ]
    if doi.startswith("10.1016/"):
        last_resort_urls.append(f"https://api.elsevier.com/content/article/doi/{doi}?httpAccept=application/pdf")
        last_resort_urls.append(f"https://www.sciencedirect.com/science/article/pii/{doi}/pdfft?isBuildApp=pdf")
    for url in [u for u in last_resort_urls if u]:
        try:
            import requests as _req
            r = _req.get(url, headers=HEADERS, timeout=30, stream=True, allow_redirects=True)
            if r.status_code == 200:
                data = b"".join(r.iter_content(16384))
                if data.startswith(b"%PDF"):
                    ok, pages = store_pdf(dest, data)
                    if ok:
                        size_kb = dest.stat().st_size / 1024
                        result.update({"status":"success","source":"Direct URL","size_kb":size_kb,
                                       "pages":pages,"partial":False})
                        pq.put(("success", doi, "Direct URL", title, filename, size_kb))
                        return result
        except Exception:
            continue

    pq.put(("fail", doi, title))
    return result

def build_artifacts(out_dir, results, elapsed, email):
    """Write report + zip and return (zip_bytes, report_bytes, failed_bytes)."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    sl = [r for r in results if r["status"]=="success"]
    fl = [r for r in results if r["status"]=="failed"]
    pl = [r for r in sl if r.get("partial")]
    lines = ["="*70,"  ACADEMIC PDF DOWNLOADER — DOWNLOAD REPORT","="*70,
             "  Created by : Amine Zouaghi","  Contact    : amine.zouaghi@unipr.it","="*70,
             f"  Date          : {now}",
             f"  Total         : {len(results)}",
             f"  Downloaded    : {len(sl)}",
             f"  Failed        : {len(fl)}",
             f"  Time elapsed  : {elapsed:.1f}s","="*70,"",
             f"DOWNLOADED ({len(sl)})","-"*70]
    for i,r in enumerate(sl,1):
        pg = r.get("pages") or 0
        pg_txt = f"{pg} page{'s' if pg != 1 else ''}" if pg else "pages unknown"
        warn = "   [!!] LIKELY INCOMPLETE - 1 page only, may be a publisher preview" \
               if r.get("partial") else ""
        lines += [f"  [{i}] {r['doi']}",
                  f"       {r['title'] or '(no title)'}",
                  f"       Source: {r['source']}  Size: {r['size_kb']:.0f} KB  "
                  f"Pages: {pg_txt}{warn}",""]
    if pl:
        lines += ["","INCOMPLETE DOWNLOADS -- these opened as 1 page only","-"*70,
                  "  Re-run these DOIs individually; the source that answered was",
                  "  most likely serving a preview rather than the full article.",""]
        for r in pl:
            lines += [f"  - {r['doi']}",f"      {r['title'] or '(no title)'}"
                      f"  (via {r['source']})",""]
    lines += [f"FAILED ({len(fl)})","-"*70]
    for i,r in enumerate(fl,1):
        lines += [f"  [{i}] {r['doi']}",f"       {r['title'] or '(no title)'}",""]
    report_path = out_dir / "download_report.txt"
    report_path.write_text("\n".join(lines), encoding="utf-8")
    failed_bytes = b""
    if fl:
        fp = out_dir / "failed_to_download.txt"
        fp.write_text("\n".join(r["doi"] for r in fl)+"\n", encoding="utf-8")
        failed_bytes = fp.read_bytes()
    zb = io.BytesIO()
    with zipfile.ZipFile(zb, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in out_dir.iterdir():
            if f.is_file():
                zf.write(f, f.name)
    return zb.getvalue(), report_path.read_bytes(), failed_bytes


# ══════════════════════════════════════════════════════════════════════════════
# ANALYSIS & EXTRACTION FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def compute_file_hash(filepath):
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception:
        return None

# ── RESEARCH METADATA EXTRACTION ─────────────────────────────────────────────
# Reads the whole document (not just the first pages) and derives the fields a
# systematic review needs: bibliographic identity, structured sections, study
# design, sample size, statistics, and the standard reporting statements.
#
# Everything is driven by PDF *spans* (text + font size + bold + position)
# rather than raw line text, because titles, authors and section headings are
# distinguished from body prose by typographic weight, not by wording. Line
# heuristics alone mis-assign titles and authors on most journal layouts.
MAX_PAGES_FOR_TEXT = 250          # guard against pathological files

BOILERPLATE = re.compile(
    r"^\s*(?:open\s+access|research\s+article|review\s+article|corrigendum|erratum|"
    r"editorial|comment(?:ary)?|letter(?:s)?|case\s+report|original\s+article|"
    r"abstract|highlights?|keywords?|graphical\s+abstract|©|\(c\)|all\s+rights\s+reserved|"
    r"downloaded\s+from|this\s+content\s+downloaded|received|revised|accepted|"
    r"published\s+(?:online|online\s+first)|first\s+published|doi\s*:|https?://|"
    r"page\s+\d+|\d{1,4}\s*$|issn|isbn|creative\s+commons|licen[sc]e|"
    r"wiley|elsevier|springer|taylor\s*&?\s*francis|sage|oxford\s+university\s+press|"
    r"copyright\s+\d{4}|article\s+type|contents\s+lists|available\s+online|"
    r"cc\s+by|open\s+access\s+article|is\s+an\s+open\s+access|"
    r"under\s+the\s+cc|licen[sc]e|all\s+rights\s+reserved|issn\s*\d|"
    r"\d{4}-\d{3,4}[\dxX]\s*/|"
    r"volume\s+\d|www\.|@)",
    re.I)

# A section shorter than this many characters is treated as a stub,
# so a heading followed straight away by a sub-heading does not swallow it.
MIN_SECTION_CHARS = 220

# Vertical gap (PDF units) that separates two typographic blocks on a page.
# Used to walk a multi-line title without swallowing the author block.
TITLE_LINE_GAP = 26.0

SECTION_PATTERNS = [
    ("abstract",     r"^abstract\b"),
    ("keywords",     r"^key\s?words?\b"),
    ("introduction", r"^(?:\d+(?:\.\d+)*\.?\s+)?introduction\b"),
    ("background",   r"^(?:\d+(?:\.\d+)*\.?\s+)?background\b"),
    ("literature",   r"^(?:\d+(?:\.\d+)*\.?\s+)?literature\s+review\b"),
    ("methods",      r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:materials?\s+and\s+methods?|"
                     r"method(?:ology|s)?|experimental\s+design|research\s+method|"
                     r"methods?|approach|study\s+design)\b"),
    ("participants", r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:participants?|subjects?|respondents?|sample)\b"),
    ("materials",    r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:materials?|apparatus|instruments?|stimuli)\b"),
    ("procedure",    r"^(?:\d+(?:\.\d+)*\.?\s+)?procedure\b"),
    ("analysis",     r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:data\s+analysis|statistical\s+analysis|"
                     r"analysis\s+strategy|statistical\s+methods?|statistics)\b"),
    ("results",      r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:results?|findings?)\b"),
    ("discussion",   r"^(?:\d+(?:\.\d+)*\.?\s+)?discussion\b"),
    ("conclusion",   r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:conclusions?|concluding\s+remarks?)\b"),
    ("limitations",  r"^(?:\d+(?:\.\d+)*\.?\s+)?limitations?\b"),
    ("future_work",  r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:future\s+(?:research|work|studies))\b"),
    ("implications", r"^(?:\d+(?:\.\d+)*\.?\s+)?(?:theoretical\s+and\s+|managerial\s+|"
                     r"practical\s+)?implications?\b"),
    ("references",   r"^(?:\d+(?:\.\d+)*\.?\s+)?references?\b"),
]

# Preferred reading order when several headings match the same pattern.
SECTION_PRIORITY = ["methods", "analysis", "results", "discussion", "conclusion",
                    "limitations", "implications", "future_work", "references"]

STAT_METHODS = [
    "ANOVA", "MANOVA", "ANCOVA", "t-test", "t test", "Mann-Whitney", "Wilcoxon",
    "chi-square", "chi square", "Pearson", "Spearman", "SEM", "structural equation",
    "logistic regression", "logit", "mixed-effects", "mixed effects", "multilevel",
    "factor analysis", "CFA", "mediation", "moderation", "conjoint", "discrete choice",
    "eye-tracking", "latent class", "k-means", "machine learning", "random forest",
    "neural network", "regression tree", "difference-in-differences", "Shapley",
    "bootstrap", "Bayesian", "Tobit", "PROBIT", "Kaplan-Meier", "log-rank",
]

STUDY_DESIGNS = [
    ("randomized controlled trial", r"randomi[sz]ed\s+(?:controlled|clinical|field)\s+trial|\bRCT\b"),
    ("quasi-experiment",            r"quasi-?experiment"),
    ("meta-analysis",               r"meta-?analys(?:is|es)"),
    ("systematic review",           r"systematic\s+review"),
    ("scoping review",              r"scoping\s+review"),
    ("secondary analysis",          r"second(?:ary)?\s+analys(?:is|es)"),
    ("longitudinal",                r"longitudinal"),
    ("cross-sectional",             r"cross-?sectional"),
    ("case study",                  r"case\s+stud(?:y|ies)"),
    ("field study",                 r"field\s+(?:study|experiment|work)"),
    ("eye-tracking study",          r"eye-?tracking|\beyetrack"),
    ("conjoint analysis",           r"\bconjoint\b"),
    ("choice experiment",           r"choice\s+(?:experiment|study|model|modelling|modeling)"),
    ("survey",                      r"\bsurvey\b|\bquestionnaire\b"),
    ("experiment",                  r"\bexperiment(?:al)?\b|\bexperiments?\s+were\s+(?:run|conducted)"),
    ("simulation",                  r"simulation\s+(?:stud(?:y|ies)|experiment)"),
]

STUDY_DESIGN_LABELS = {
    "randomized controlled trial": "RCT",
    "quasi-experiment": "quasi-experimental",
    "meta-analysis": "meta-analysis",
    "systematic review": "systematic review",
    "scoping review": "scoping review",
    "secondary analysis": "secondary analysis",
    "longitudinal": "longitudinal",
    "cross-sectional": "cross-sectional",
    "case study": "case study",
    "field study": "field study",
    "eye-tracking study": "eye-tracking",
    "conjoint analysis": "conjoint",
    "choice experiment": "choice experiment",
    "survey": "survey",
    "experiment": "experimental",
    "simulation": "simulation",
}

STOP_HEADINGS = re.compile(
    r"\b(?:references|bibliography|acknowledg\w*|conflict[s]? of interest|"
    r"competing interests?|declarations?|funding|financial support|"
    r"author contributions?|contributions? of authors?|supplementary|"
    r"appendix|notes|data availability|ethics?)\b", re.I)

AFFILIATION_RX = re.compile(
    r"\b(?:universit|college|institut|school|faculty|department|laborator|"
    r"research center|research centre|hospital|foundation|academy|campus|"
    r"inc\.|llc|gmbh|ltd|co\.,|corporat|@[a-z0-9]|\busa\b|chinese|"
    r"postal|street|avenue|road|zip|orcid)\b", re.I)

# A masthead / running head: the journal name, not the article title.
JOURNALISH = re.compile(
    r"^\s*(?:the\s+)?(?:journal|quarterly|annals|proceedings|transactions|"
    r"international\s+journal|reviews?\s+of|advances\s+in|letters\s+in|"
    r"archives\s+of)\b", re.I)

# Loose, used only to *find* the journal line on page 1.
JOURNAL_WORD_RX = re.compile(
    r"\b(?:journal|review|quarterly|annals|advances|proceedings|transactions|"
    r"science|letters|psychology|marketing|management|studies)\b", re.I)

# Elsevier jams the "References" heading onto the first citation without a
# space ("Referencestrade-o\u00fds"). Split it before heading matching.
# Only "references" gets this treatment: the same rule applied to
# "conclusions" would split the single word "Conclusions" into two.
HEADING_GLUE_RX = re.compile(r"(?i)\b(references)(?=[a-z\u00c0-\u024f])")

# Leading section numbering: "2. Methods", "2.1 Methods", Wiley's "2.2 | Design".
NUMBER_PREFIX_RX = re.compile(r"^\s*\d+(?:\.\d+)*\.?\s*\|?\s*")

# A plausible personal-name line: mostly capitalised tokens or initials.
NAMEISH_RX = re.compile(r"^[A-Z][\w'\-\.]*(?:\s+[A-Z][\w'\-\.]*){0,7}$")

# "Keywords: a, b, c" -- must be a heading-shaped occurrence, not prose.
KEYWORDS_RX = re.compile(
    r"^[ \t]*(?:\d+(?:\.\d+)*\.?\s*)?key\s?words?\s*[:\-–—][ \t]*", re.I | re.M)


def _norm_space(s):
    """Normalise the odd unicode spaces publishers emit and drop control chars."""
    if not s:
        return ""
    for sp in (" ", " ", " ", " ", " ", "⁠",
               " ", " ", " "):
        s = s.replace(sp, " ")
    s = s.replace("­", "")
    s = s.replace("﻿", "").replace("", "")
    s = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", s)
    s = s.replace("ﬁ", "fi").replace("ﬂ", "fl")
    return s


def _fix_wrap(s):
    """Repair hyphenation artefacts left by PDF line breaking ("Front- of-")."""
    if not s:
        return s
    return re.sub(r"(\w)[-‐-―][ \t]+(?=[A-Za-z])", r"\1-", s)


def _clean_ws(s):
    return re.sub(r"[ \t]+", " ", _norm_space(s)).strip()


def _collapse(s, limit=None):
    s = _clean_ws(re.sub(r"\s*\n\s*", " ", s or ""))
    if limit and len(s) > limit:
        s = s[:limit].rsplit(" ", 1)[0] + "…"
    return s


def _group_lines(spans, tol=3.0):
    """
    Collapse spans into visual lines. pypdf emits one span per text-showing
    operator, so a single word is often split across several spans (kerning);
    concatenating them in x-order restores the line exactly. Returns
    [{y, x, size, bold, text}] sorted top-to-bottom, left-to-right.
    """
    lines = []
    for s in sorted(spans, key=lambda s: (-s["y"], s["x"])):
        if lines and abs(lines[-1]["y"] - s["y"]) <= tol:
            ln = lines[-1]
            ln["parts"].append(s)
            ln["x"] = min(ln["x"], s["x"])
            ln["size"] = max(ln["size"], s["size"])
            ln["bold"] = ln["bold"] or s["bold"]
            ln["y"] = max(ln["y"], s["y"])
        else:
            lines.append({"y": s["y"], "x": s["x"], "size": s["size"],
                          "bold": s["bold"], "parts": [s]})
    for ln in lines:
        ln["parts"].sort(key=lambda s: s["x"])
        ln["text"] = _clean_ws("".join(p["text"] for p in ln["parts"]))
        ln.pop("parts")
    lines.sort(key=lambda l: (-l["y"], l["x"]))
    return lines


def _column_split(spans, page_width=None):
    """
    Detect a vertical gutter in a multi-column page.

    Returns (left_spans, right_spans) or (spans, None) when the page looks
    single-column. Without this, a heading in the left column is glued onto
    body text from the right column at the same baseline, which destroys both
    the heading and the line text.
    """
    if len(spans) < 40:
        return spans, None
    width = page_width or 612.0
    xs = sorted(s["x"] for s in spans)
    if not xs:
        return spans, None
    x0, x1 = xs[0], xs[-1]
    if x1 - x0 < width * 0.35:
        return spans, None
    # histogram of span left edges across the printed area
    bins = 40
    hist = [0] * bins
    span = max(x1 - x0, 1e-6)
    for s in spans:
        k = min(bins - 1, int((s["x"] - x0) / span * bins))
        hist[k] += 1
    # only look for a gutter in the middle of the text block
    lo, hi = int(bins * 0.34), int(bins * 0.66)
    run_best, run_len, run_at = 0, 0, None
    for k in range(lo, hi + 1):
        if hist[k] == 0:
            run_len += 1
            if run_len > run_best:
                run_best, run_at = run_len, k - run_len + 1
        else:
            run_len = 0
    if not run_at or run_best < 2:
        return spans, None
    gutter = x0 + (run_at + run_best / 2.0) / bins * span
    left = [s for s in spans if s["x"] < gutter]
    right = [s for s in spans if s["x"] >= gutter]
    if len(left) < 20 or len(right) < 20:
        return spans, None
    return left, right


def _page_lines(spans, page_width=None, allow_split=True):
    """Group one page's spans into lines, handling a two-column layout."""
    left, right = _column_split(spans, page_width) if allow_split else (spans, None)
    out = _group_lines(left)
    for ln in out:
        ln["col"] = 0
    if right is None:
        return out
    for ln in _group_lines(right):
        ln["col"] = 1
        out.append(ln)
    out = _repair_gutter(out, tol=3.0)
    # reading order: whole left column, then whole right column
    out.sort(key=lambda l: (l.get("col", 0), -l["y"], l["x"]))
    return out


def _repair_gutter(lines, tol=3.0):
    """Rejoin a word that the gutter split ("6. Conclusion" | "s")."""
    lefts = [l for l in lines if l.get("col", 0) == 0]
    rights = [l for l in lines if l.get("col", 0) == 1]
    if not lefts or not rights:
        return lines
    merged_right = set()
    for ln in lefts:
        for rt in rights:
            if id(rt) in merged_right or abs(ln["y"] - rt["y"]) > tol:
                continue
            # exactly one of the two halves is a 1-2 char fragment and the other
            # ends in a letter -> they were one word
            if len(ln["text"]) <= 2 and rt["text"] and rt["text"][0].isalpha():
                ln["text"] += rt["text"]
                merged_right.add(id(rt))
                break
            if len(rt["text"]) <= 2 and ln["text"] and ln["text"][-1].isalpha():
                ln["text"] += rt["text"]
                merged_right.add(id(rt))
                break
    return [l for l in lines if id(l) not in merged_right]


def _layout_is_degenerate(lines):
    """
    True when the visitor output cannot be trusted as a layout.

    Some PDFs (image-only scans, or files with an unusual content stream) make
    pypdf emit spans whose glyph scale is 1.0 and whose y positions collapse
    around zero. Plain extract_text() still works on these, so the caller
    falls back to reading order instead of geometry.
    """
    if not lines:
        return True
    tiny = sum(1 for l in lines if l["size"] <= 1.0) / len(lines)
    if tiny > 0.35:
        return True
    p0 = [l for l in lines if l["p"] == 0]
    if p0 and sum(1 for l in p0 if l["y"] <= 0) / len(p0) > 0.5:
        return True
    return False


def _collect_spans(pdf_path, max_pages=MAX_PAGES_FOR_TEXT):
    """
    Return (page_count, lines, page_texts, doc_info).
    Each line: {p, y, x, size, bold, text} -- built from PDF text spans
    (text + glyph scale + bold + position) so that titles, authors and
    section headings can be told apart from body prose by typography rather
    than by guessing from line wording.
    """
    pages, lines, page_texts, info = 0, [], [], {}
    if PdfReader is None:
        return 0, [], [], info

    def read():
        return PdfReader(str(pdf_path), strict=False)

    try:
        pages = len(read().pages)
    except Exception:
        return 0, [], [], info
    try:
        md = read().metadata
        if md:
            for k, v in md.items():
                try:
                    info[str(k)] = str(v)
                except Exception:
                    continue
    except Exception:
        pass

    try:
        rdr = read()
        for pno, page in enumerate(rdr.pages[:max_pages]):
            collected = []
            try:
                pw = float(page.mediabox.width)
                ph = float(page.mediabox.height)
            except Exception:
                pw = ph = None

            def visitor(text, cm, tm, font_dict, font_size, _out=collected):
                if not text or not text.strip():
                    return
                base = ""
                try:
                    base = str((font_dict or {}).get("/BaseFont", ""))
                except Exception:
                    base = ""
                bold = bool(re.search(r"-Bold|-black|Heavy|Semibold", base, re.I))
                italic = bool(re.search(r"-Italic|-Oblique", base, re.I))
                # pypdf reports a useless font_size (always 1.0); the real glyph
                # scale lives in the text matrix, so read it from tm[0] and
                # round it -- tm[0] carries float noise (11.0 vs 10.983) that
                # would otherwise split one font size into a dozen buckets.
                try:
                    size = round(float(tm[0]) * 2) / 2.0
                except Exception:
                    size = 0.0
                if not size or abs(size - 1.0) < 1e-6:
                    try:
                        alt = float(font_size)
                        size = round(alt * 2) / 2.0 if alt and abs(alt - 1.0) > 1e-6 else size
                    except Exception:
                        pass
                try:
                    x, y = round(float(tm[4]), 1), round(float(tm[5]), 1)
                except Exception:
                    x, y = 0.0, 0.0
                _out.append({"p": pno, "size": size, "x": x, "y": y,
                             "text": text, "bold": bold, "italic": italic})

            try:
                page.extract_text(visitor_text=visitor)
            except TypeError:
                page.extract_text(visitor_text=visitor, user_space_units=True)
            except Exception:
                pass
            pglines = _page_lines(collected, pw, allow_split=pno > 0)
            for ln in pglines:
                ln["p"] = pno
            lines.extend(pglines)
            page_texts.append("\n".join(l["text"] for l in pglines))
    except Exception:
        pass
    if _layout_is_degenerate(lines):
        # geometry is unusable: rebuild the text in plain reading order
        info["_layout_degenerate"] = "1"
        try:
            rdr2 = read()
            page_texts = []
            for page in rdr2.pages[:max_pages]:
                try:
                    page_texts.append(page.extract_text() or "")
                except Exception:
                    page_texts.append("")
        except Exception:
            pass
    return pages, lines, page_texts, info


def _body_size(lines):
    """Most common glyph scale by character weight == the body text size."""
    weight = {}
    for s in lines:
        if s["size"] > 0 and 3 < len(s["text"]) < 250:
            weight[s["size"]] = weight.get(s["size"], 0) + len(s["text"])
    if not weight:
        return 10.0
    top = max(weight.values())
    return max((sz for sz, w in weight.items() if w >= top * 0.35), default=10.0)


def _nameish(t):
    """True when a line reads like a personal name rather than prose."""
    t = _clean_ws(t).strip(" ,;")
    if not t or len(t.split()) > 10:
        return False
    words = [w for w in re.split(r"\s+", t) if w]
    if not words:
        return False
    good = sum(1 for w in words
               if w[:1].isupper() or re.fullmatch(r"[a-z]\.?", w)
               or w in {"de", "da", "do", "dos", "van", "von", "der", "den", "del", "la", "le"})
    return good >= max(1, int(0.7 * len(words)))


def _merge_line(lines, joiner=""):
    return _clean_ws(joiner.join(s["text"] for s in lines))


def _title_candidates(page_lines, body):
    """
    Cluster every oversized line on page 1 into vertical blocks and score
    them. Trusting the single largest font is not enough: a journal masthead
    ("Journal of Business Research") is often set *larger* than the article
    title, so candidates are ranked by size but vetoed when they look like a
    journal name rather than prose.
    """
    big = [s for s in page_lines
           if s["size"] >= body * 1.12 and not BOILERPLATE.match(s["text"])
           and len(s["text"]) > 3]
    if not big:
        big = [s for s in page_lines
               if (s["bold"] or s["size"] >= body * 1.02)
               and not BOILERPLATE.match(s["text"])
               and len(s["text"]) > 3]
    if not big:
        return []

    big.sort(key=lambda s: (-s["y"], s["x"]))
    blocks, cur, prev_y, cur_size = [], [], None, None
    for s in big:
        if cur and (abs(prev_y - s["y"]) > TITLE_LINE_GAP
                    or abs(cur_size - s["size"]) > 1.5):
            blocks.append(cur)
            cur = []
        if not cur:
            cur_size = s["size"]
        cur.append(s)
        prev_y = s["y"]
    if cur:
        blocks.append(cur)

    cands = []
    for blk in blocks:
        text = _collapse(" ".join(s["text"] for s in blk), 400)
        text = _fix_wrap(re.sub(r"\s*\d+\s*$", "", text)).strip()
        if len(text) < 12 or BOILERPLATE.match(text):
            continue
        size = max(s["size"] for s in blk)
        words = text.split()
        if JOURNALISH.match(text) or len(words) < 4:
            continue                      # masthead, not a title
        if len(re.findall(r"[a-z]{3,}", text)) < 4:
            continue                      # not prose
        cands.append((size, len(text), blk, text))
    return sorted(cands, key=lambda c: (-c[0], -c[1]))


def _extract_title_and_authors(page_lines, body):
    """
    Title = the best-scoring oversized block on page 1. Authors = the
    name-shaped lines immediately below it.
    """
    if not page_lines:
        return None, []
    cands = _title_candidates(page_lines, body)
    if not cands:
        return None, []

    _, _, block, title = cands[0]
    # the band's bottom edge is where the author/affiliation block begins
    cutoff = min(s["y"] for s in block)

    below = sorted([s for s in page_lines if s["y"] < cutoff - 4],
                   key=lambda s: (-s["y"], s["x"]))
    authors = []
    for s in below:
        t = s["text"]
        if not t or BOILERPLATE.match(t) or len(t) < 3:
            continue
        if AFFILIATION_RX.search(t):
            break
        if re.search(r"\b(?:abstract|highlights?|keywords?|graphical\s+abstract)\b", t, re.I):
            break
        # affiliation superscripts (a, ab, 1*) are set smaller than body text
        if s["size"] < body * 0.92:
            continue
        if re.match(r"^\(?\d+\)?$", t):
            continue
        if s["bold"] and s["size"] > body * 1.2:
            continue
        if len(t) > 160:
            continue
        # Author blocks are name-shaped. Once we have one name, a line that is
        # not name-shaped means the block has ended and the body has started --
        # some layouts put no affiliation or "Abstract" label to stop on.
        if authors and not _nameish(t):
            break
        authors.append(t)
        if len(authors) > 40:
            break
    if not authors:
        return title, []

    joined = " ".join(authors)
    parts = re.split(r"\s*(?:,|;|\band\b|&|\||•)\s*", joined)
    cands = []
    for part in parts:
        part = re.sub(r"[\d\*†‡§¶#~^]+.*$", "", part).strip()
        part = re.sub(r"[‘’“”]", "", part)
        if not (3 <= len(part) <= 60):
            continue
        if not re.search(r"[A-Za-z]{3}", part):
            continue
        if part.isupper():
            continue
        if not re.search(r"[A-Z][a-z]", part):
            continue
        if AFFILIATION_RX.search(part):
            continue
        cands.append(part)
    return title, cands[:25]


def _detect_sections(lines, body):
    """
    Two passes.

    Typography first: a heading is a short line set larger than the body or in
    a bold face.

    Not every publisher cooperates -- Elsevier's production PDFs embed section
    headings in a subset font with no "-Bold" suffix and at body size, so the
    second pass accepts a short standalone line that reads like a heading
    ("5. Discussion", "Method", "Results") even when the font says nothing.
    """
    hits, claimed = [], set()
    for i, s in enumerate(lines):
        t = HEADING_GLUE_RX.sub(r"\1 ", s["text"])
        if not t or len(t) > 80:
            continue
        if not (s["bold"] or s["size"] >= body * 1.03):
            continue
        for name, pat in SECTION_PATTERNS:
            if re.match(pat, t, re.I) or re.match(pat, NUMBER_PREFIX_RX.sub("", t), re.I):
                hits.append((name, s, t))
                claimed.add(i)
                break

    for i, s in enumerate(lines):
        if i in claimed:
            continue
        t = HEADING_GLUE_RX.sub(r"\1 ", s["text"])
        if not t or not (3 <= len(t) <= 60):
            continue
        if t.endswith((".", ",", ";", ":")) and not re.search(r"\d\.$", t):
            continue                      # sentence, not a heading
        if re.search(r"[a-z]\s+[a-z]+\s+[a-z]+", t) and not re.match(r"^\d", t):
            continue                      # lower-case prose
        # strip a run-in page number, e.g. "494. Results" == page 49 + "4. Results"
        stripped = re.sub(r"^\d{1,4}\s+(?=\d+(?:\.\d+)*\.?\s+[A-Z])", "", t, count=1)
        if stripped == t:      # "494. Results" == page 49 + "4. Results"
            stripped = re.sub(r"^\d{1,4}(?=\d+\.\d|\d+\.\s)", "", t, count=1)
        for name, pat in SECTION_PATTERNS:
            if re.match(pat, stripped, re.I) \
               or re.match(pat, NUMBER_PREFIX_RX.sub("", stripped), re.I):
                hits.append((name, s, stripped))
                break
    hits.sort(key=lambda h: (h[1]["p"], -h[1]["y"]))
    return hits


def _first_section_hit(hits, name):
    for n, s, t in hits:
        if n == name:
            return s, t
    return None, None


def _parse_bib_details(text, info):
    out = {"volume": None, "issue": None, "pages": None, "issn": None}
    head = text[:3000] if text else ""
    if not head and info:
        head = " ".join(str(v) for v in info.values())
    if not head:
        return out
    m = re.search(r"\bvol(?:ume|\.)?\s*(\d{1,4})\s*(?:,?\s*(?:no\.|iss\.?|issue)\s*(\d{1,4}))?",
                  head, re.I)
    if m:
        out["volume"], out["issue"] = m.group(1), m.group(2)
    if out["issue"] and not (1 <= int(out["issue"]) <= 99):
        out["issue"] = None
    if not out["volume"]:
        m = re.search(r"\b(\d{1,4})\s*\(\s*(\d{1,4})\s*\)", head)
        if m:
            out["volume"], out["issue"] = m.group(1), m.group(2)
            if out["issue"] and not (1 <= int(out["issue"]) <= 99):
                out["issue"] = None
    def _pages_ok(a, b):
        a, b = int(a), int(b)
        return a < b and b - a <= 2000 and a <= 99999

    for pat in (r"[:.\s]\s*(\d{1,5})\s*[-–—]\s*(\d{1,5})\b",
                r"\b(?:pp?\.?|pages?)\s*(\d{1,5})\s*[-–—]\s*(\d{1,5})"):
        m = re.search(pat, head, re.I)
        if m and _pages_ok(m.group(1), m.group(2)):
            out["pages"] = f"{m.group(1)}-{m.group(2)}"
            break
    m = re.search(r"\bISSN\s*[:.]?\s*(\d{4}-?\d{3}[\dxX])", head, re.I)
    if m:
        out["issn"] = m.group(1)
    return out


def _parse_year(text, info):
    """Prefer an explicit publication/accepted date over the most common year."""
    this_year = datetime.now().year + 1

    def valid(y):
        try:
            y = int(y)
        except Exception:
            return None
        return y if 1900 <= y <= this_year else None

    blob = (text or "")[:8000]
    for rx in [r"(?:published|publication\s+date|published\s+online|first\s+published|"
               r"copyright|©)[^0-9\n]{0,60}((?:19|20)\d{2})",
               r"\breceived\b[^0-9\n]{0,40}((?:19|20)\d{2})",
               r"\baccepted\b[^0-9\n]{0,40}((?:19|20)\d{2})"]:
        m = re.search(rx, blob, re.I)
        if m:
            y = valid(m.group(1))
            if y:
                return y
    years = [valid(y) for y in re.findall(r"\b(19\d{2}|20\d{2})\b", blob)]
    years = [y for y in years if y]
    if years:
        return max(set(years), key=years.count)
    for key in ("creationDate", "modDate", "CreationDate", "ModDate"):
        v = (info or {}).get(key)
        if v:
            m = re.search(r"(19|20)\d{2}", str(v))
            if y := valid(m.group(0)) if m else None:
                return y
    return None


def _between(text, start_pat, end_pats, limit=1600):
    """Slice from the first start-pattern match up to the next heading."""
    m = re.search(start_pat, text, re.I)
    if not m:
        return None
    rest = text[m.end():]
    stop = len(rest)
    for pat in end_pats:
        e = re.search(pat, rest, re.I)
        if e and e.start() < stop:
            stop = e.start()
    chunk = _collapse(rest[:stop], limit)
    return chunk if len(chunk) > 40 else None


def _find_statement(text, labels, limit=800):
    if not text:
        return None
    rx = re.compile("|".join(labels), re.I)
    for m in rx.finditer(text):
        tail = text[m.start():m.start() + limit]
        tail = re.split(r"\b(?:references|bibliography)\b", tail, maxsplit=1, flags=re.I)[0]
        snippet = _collapse(tail, limit)
        if len(snippet) > 40:
            return snippet
    return None


def extract_pdf_metadata(pdf_path, deep=True):
    """
    Research-grade metadata extraction. deep=True reads the whole document and
    derives structured sections, study design, sample size, statistics and the
    standard reporting statements; deep=False keeps a fast shallow pass.
    """
    metadata = {
        "title": None, "authors": [], "author_count": 0,
        "doi": None, "journal": None, "year": None,
        "volume": None, "issue": None, "pages": None, "issn": None,
        "subject": None, "creator": None, "producer": None,
        "abstract": None, "keywords": [], "keyword_count": 0,
        "section_headings": [], "sections_found": [],
        "methodology": None, "findings": None, "conclusions": None,
        "limitations": None, "future_work": None, "implications": None,
        "sample_size": None, "sample_size_label": None, "participants": None,
        "study_design": None, "study_design_label": None,
        "statistical_methods": [], "statistical_method_count": 0,
        "funding": None, "ethics": None, "data_availability": None,
        "conflicts": None, "author_contributions": None,
        "pages": 0, "word_count": 0, "char_count": 0,
        "n_figures": 0, "n_tables": 0, "n_references": 0,
        "language": None, "language_confidence": None,
        "title_source": None, "extraction_ok": False, "extraction_error": None,
    }
    if PdfReader is None:
        metadata["extraction_error"] = "no PDF parser installed"
        return metadata

    max_pages = MAX_PAGES_FOR_TEXT if deep else 6
    try:
        pages, lines, page_texts, info = _collect_spans(pdf_path, max_pages)
    except Exception as e:
        metadata["extraction_error"] = f"read failed: {type(e).__name__}"
        return metadata

    metadata["pages"] = pages
    full_text = "\n".join(page_texts)
    flat = _collapse(full_text)
    metadata["char_count"] = len(full_text)
    metadata["word_count"] = len(re.findall(r"[A-Za-z][A-Za-z'-]+", full_text))
    metadata["extraction_ok"] = bool(flat)
    if not lines:
        metadata["extraction_error"] = metadata["extraction_error"] or "no extractable text"
        return metadata

    body = _body_size(lines)
    metadata["body_font_size"] = round(body, 2)
    info_l = {str(k).lower(): str(v) for k, v in (info or {}).items()}

    # ── identity ────────────────────────────────────────────────────────────
    if info_l.get("title") and len(info_l["title"]) > 8:
        metadata["title"] = _collapse(info_l["title"], 400)
        metadata["title_source"] = "pdf metadata"
    for key, dest in (("subject", "subject"), ("creator", "creator"),
                      ("producer", "producer")):
        if info_l.get(key):
            metadata[dest] = _collapse(info_l[key], 300)

    p1_lines = [s for s in lines if s["p"] == 0]
    t_title, t_authors = _extract_title_and_authors(p1_lines, body)
    if metadata["title"] is None and t_title:
        metadata["title"] = t_title
        metadata["title_source"] = "page 1 layout"
    if not metadata["title"]:
        if info_l.get("_layout_degenerate"):
            # no usable geometry -- read the title off the top of page 1
            first = [c for c in (page_texts[0].split("\n") if page_texts else [])
                     if c.strip() and not BOILERPLATE.match(c.strip())]
            if first:
                metadata["title"] = _collapse(" ".join(first[:2]), 400)
                metadata["title_source"] = "plain text (no usable layout)"
        else:
            cands = [s for s in p1_lines if not BOILERPLATE.match(s["text"])
                     and len(s["text"]) > 20]
            if cands:
                # the masthead ("Journal of Business Research") is set as large
                # as the title on some layouts; prefer a line that reads like
                # prose rather than a journal name
                prose = [s for s in cands
                         if not JOURNALISH.match(s["text"])
                         and not AFFILIATION_RX.search(s["text"])
                         and len(re.findall(r"[a-z]{3,}", s["text"])) >= 4]
                biggest = max(prose or cands, key=lambda s: s["size"])
                metadata["title"] = _collapse(biggest["text"], 400)
                metadata["title_source"] = "largest line on page 1"

    if info_l.get("author") and len(info_l["author"]) > 3:
        parts = re.split(r"\s*(?:;|,|\band\b|&)\s*", _clean_ws(info_l["author"]))
        metadata["authors"] = [p for p in parts if 2 < len(p) < 80][:25]
        metadata["authors_source"] = "pdf metadata"
    if not metadata["authors"] and t_authors:
        metadata["authors"] = t_authors
        metadata["authors_source"] = "page 1 layout"
    metadata.setdefault("authors_source", None)

    doi_rx = re.compile(r"\b(10\.\d{4,9}/[-._;()/:\w\[\]<>]+)")
    for scope in (full_text[:25000], " ".join(info.values()) if info else ""):
        m = doi_rx.search(scope)
        if m:
            candidate = m.group(1)
            # stop before a word glued on by the PDF ("...101181European")
            stop = re.search(r"(?<=[A-Za-z0-9])(?=[A-Z][a-z]{2,})", candidate)
            if stop:
                candidate = candidate[:stop.start()]
            metadata["doi"] = candidate.rstrip(".,);:'\"]>")
            break

    metadata["year"] = _parse_year(full_text, info)
    bib = _parse_bib_details(full_text, info)
    metadata.update(bib)

    jrnl = None
    for ln in (page_texts[0].split("\n") if page_texts else []):
        c = _clean_ws(ln)
        if 6 < len(c) < 100 and JOURNAL_WORD_RX.search(c) \
           and not re.search(r"\bdoi\b|https?://|@|www\.|homepag|/locate/", c, re.I):
            jrnl = c
            break
    metadata["journal"] = jrnl or info_l.get("journal") or None
    # A masthead or running head can be mistaken for the title; if the two
    # match, the journal line is boilerplate and the title is really elsewhere.
    if metadata["title"] and metadata["journal"] \
       and re.sub(r"\W+", "", metadata["title"]).lower() == \
          re.sub(r"\W+", "", metadata["journal"]).lower():
        metadata["title"] = None
        metadata["title_source"] = None

    # ── structured sections ─────────────────────────────────────────────────
    hits = _detect_sections(lines, body)
    ref_pos = None
    if not any(n == "references" for n, _, _ in hits):
        # The heading never survives as its own line (Elsevier glues it onto the
        # first citation), so look for the word itself in the back half.
        for mm in re.finditer(r"(?<![A-Za-z])references", full_text, re.I):
            if mm.start() > 0.45 * len(full_text):
                ref_pos = mm.end()
        if ref_pos is not None:
            hits.append(("references", None, "References"))
    metadata["sections_found"] = sorted({n for n, _, _ in hits},
                                        key=lambda n: SECTION_PRIORITY.index(n)
                                        if n in SECTION_PRIORITY else 99)
    seen_h = set()
    for _, _, t in hits:
        label = re.split(r"\n|\s{2,}[A-Z]", t.strip(), maxsplit=1)[0].strip()
        if label and label not in seen_h:
            seen_h.add(label)
            metadata["section_headings"].append(label[:120])
    metadata["section_headings"] = metadata["section_headings"][:60]

    heading_rx = [r"^\s*\d+(?:\.\d+)*\.?\s+[A-Z][A-Za-z].{0,70}$",
                  r"^\s*(?:abstract|introduction|discussion|conclusions?|references?)\b.{0,70}$"]
    stop_rx = [r"^\s*(?:references?|bibliography)\b",
               r"^\s*(?:\d+(?:\.\d+)*\.?\s*)?(?:conflict[s]? of interest|competing interests?|"
               r"acknowledg\w*|declarations?|funding|financial support|author contributions?|"
               r"contributions? of authors?|supplementary|appendix|data availability|"
               r"ethics? (?:approval|statement)|notes)\b"]

    def sec(start_names, limit=1600):
        for nm in start_names:
            s, _t = _first_section_hit(hits, nm)
            if s:
                # locate this heading's offset inside the flat text
                idx = full_text.find(_t)
                if idx == -1:
                    continue
                tail = full_text[idx:]
                head = len(_t)
                mnum = re.match(r"^\s*(\d+(?:\.\d+)*)", _t)
                cur_num = mnum.group(1) if mnum else ""
                stop = len(tail)
                for pat in heading_rx + stop_rx:
                    for e in re.finditer(pat, tail[head:], re.M):
                        at = head + e.start()
                        if at - head < MIN_SECTION_CHARS:
                            continue          # sub-heading right below
                        sub = re.match(r"^\s*(\d+(?:\.\d+)*)", e.group(0))
                        if cur_num and sub and sub.group(1).startswith(cur_num + "."):
                            continue          # deeper subsection of this one
                        if at < stop:
                            stop = at
                        break
                chunk = _collapse(tail[head:stop], limit)
                if len(chunk) > 40:
                    return chunk
        return None

    metadata["abstract"]     = sec(["abstract"], 2200)
    metadata["methodology"]  = (sec(["methods"], 1600) or sec(["analysis"], 1400)
                                or sec(["materials"], 1100) or sec(["procedure"], 1100))
    metadata["findings"]     = sec(["results"], 1600)
    metadata["discussion"]   = sec(["discussion"], 1400)
    metadata["conclusions"]  = sec(["conclusion"], 1200)
    metadata["limitations"]  = sec(["limitations"], 900)
    metadata["implications"] = sec(["implications"], 900)
    metadata["future_work"]  = sec(["future_work"], 900)
    metadata["participants"] = sec(["participants"], 1200)
    if metadata["findings"] is None and metadata["methodology"]:
        metadata["findings"] = sec(["discussion"], 1200)

    # abstract fallback: prose right before the Keywords/Introduction heading
    if not metadata["abstract"]:
        # On an Elsevier page the first "abstract" is the ARTICLE INFO label and
        # the real abstract follows it, so anchor on the last one on page 1.
        page1 = page_texts[0] if page_texts else ""
        found = list(re.finditer(r"\babstract\b", page1, re.I))
        if found:
            base, anchor = page1, found[-1]
        else:
            found = list(re.finditer(r"\babstract\b", full_text, re.I))
            base, anchor = (full_text, found[0]) if found else (None, None)
        if anchor is not None:
            tail = base[anchor.end():]
            stop = len(tail)
            for pat in [r"\bkey\s?words?\b", r"^\s*1\.?\s*introduction\b",
                        r"\bintroduction\b", STOP_HEADINGS.pattern]:
                e = re.search(pat, tail, re.I | re.M)
                if e and e.start() < stop:
                    stop = e.start()
            chunk = _collapse(tail[:stop], 2200)
            if len(chunk) > 80:
                metadata["abstract"] = chunk

    # keywords
    if info_l.get("keywords"):
        metadata["keywords"] = [k.strip() for k in re.split(r"[;,]", info_l["keywords"])
                                if k.strip()][:40]
    if not metadata["keywords"]:
        m = KEYWORDS_RX.search(full_text)
        if m:
            tail = full_text[m.end():m.end() + 1200]
            tail = re.split(r"\n\s*(?:abstract|introduction|\d+\.?\s*introduction|"
                            r"highlights|1\s*\.?\s*introduction)\b", tail, maxsplit=1,
                            flags=re.I)[0]
            tail = re.sub(r"^[\s:|,\-–—]+", "", tail)
            kws = []
            for chunk in re.split(r"[;\n]|(?<!\d),(?!\d)", tail):
                c = _collapse(chunk, 70)
                if 2 < len(c) < 70 and not re.match(r"^https?://", c, re.I) \
                   and not re.search(r"\b(?:abstract|introduction)\b", c, re.I) \
                   and len(c.split()) <= 4 and not c.endswith(".") \
                   and not re.search(r":\s", c):
                    kws.append(c)
            metadata["keywords"] = kws[:30]
    if metadata["keywords"]:
        seen, uniq = set(), []
        for k in metadata["keywords"]:
            kl = k.lower().strip(" .;:")
            if kl and kl not in seen:
                seen.add(kl)
                uniq.append(k)
        metadata["keywords"] = uniq[:40]
    metadata["keyword_count"] = len(metadata["keywords"])

    # ── study design, sample, statistics ────────────────────────────────────
    design_zone = " ".join(filter(None, [metadata["methodology"] or "",
                                         metadata["participants"] or "",
                                         metadata["abstract"] or "",
                                         flat[:2500]])).lower()
    for label, pat in STUDY_DESIGNS:
        if re.search(pat, design_zone, re.I):
            metadata["study_design"] = label
            metadata["study_design_label"] = STUDY_DESIGN_LABELS.get(label, label)
            break

    stat_zone = " ".join(filter(None, [metadata["methodology"] or "",
                                       metadata["findings"] or "",
                                       metadata["participants"] or ""])).lower()
    found_stats = []
    for sname in STAT_METHODS:
        if sname.lower() in stat_zone and sname not in found_stats:
            found_stats.append(sname)
    metadata["statistical_methods"] = found_stats[:20]
    metadata["statistical_method_count"] = len(found_stats)

    sample_zone = " ".join(filter(None, [metadata["participants"] or "",
                                         metadata["methodology"] or "",
                                         metadata["abstract"] or ""]))
    # The label is the unit noun, so a page can print "1,800 participants"
    # rather than the bare string "n =". A bare n = keeps the number but has
    # no unit to name, hence "reported n".
    for rx, label in [(r"\b[nN]\s*=\s*(\d{1,7})\b", "reported n"),
                      (r"\b(\d{1,7})\s+(participants|respondents|subjects|consumers|"
                       r"students|users|customers|volunteers|households|"
                       r"observations)\b", None),
                      (r"\b(\d{1,7})\s+(trials|runs|sessions|experiments|items|"
                       r"products|brands|profiles|webpages|websites|datasets?)\b", None)]:
        m = re.search(rx, sample_zone, re.I)
        if m:
            n = int(m.group(1))
            if 2 <= n <= 5_000_000:
                metadata["sample_size"] = n
                metadata["sample_size_label"] = (
                    label if label else m.group(2).lower())
                break

    metadata["n_figures"] = len({m for m in re.findall(r"\bfig(?:ure)?s?\.?\s*(\d{1,3})\b",
                                                       full_text, re.I)})
    metadata["n_tables"] = len({m for m in re.findall(r"\btab(?:le)?s?\.?\s*(\d{1,3})\b",
                                                     full_text, re.I)})

    m = re.search(r"^\s*(?:\d+\s*)?references?\s*$", full_text, re.I | re.M)
    ref_line_idx = None
    for nm, sl, st in hits:
        if nm == "references":
            ref_line_idx = lines.index(sl) if sl is not None else None
            break
    if ref_line_idx is not None:
        # reading-order lines after the heading: survives two-column layouts
        tail = "\n".join(l["text"] for l in lines[ref_line_idx + 1:ref_line_idx + 400])
    elif ref_pos is not None:
        tail = full_text[ref_pos:]
    elif m:
        tail = full_text[m.end():]
    else:
        tail = ""
    if tail:
        # Three common reference styles, counted independently and max()'d:
        # numbered [1] / 1. / (1); Harvard "Author, A. 1996. Title"; and
        # APA "(1996)." style year markers.
        numbered = len(re.findall(r"^\s*(?:\[\d{1,3}\]|\(\d{1,3}\)|\d{1,3}[.)])\s+\S", tail, re.M))
        year_start = len(re.findall(
            r"^[A-Z][A-Za-z'’\-]{1,30}[,.\s][^\n]{0,140}?\b(?:19|20)\d{2}\b", tail, re.M))
        by_year = len(re.findall(r"\(\s*(?:19|20)\d{2}[a-z]?\s*\)", tail))
        by_doi = len(set(doi_rx.findall(tail)))
        metadata["n_references"] = max(numbered, year_start, by_year, by_doi)

    metadata["funding"] = _find_statement(full_text,
        [r"funding", r"financial support", r"this work was supported",
         r"grants? (?:from|number)", r"acknowledg\w* of funding",
         r"funded by"])
    metadata["ethics"] = _find_statement(full_text,
        [r"ethic(?:s|al) (?:approval|clearance|committee|statement)",
         r"institutional review board", r"\bIRB\b", r"informed consent",
         r"declaration of helsinki"])
    metadata["data_availability"] = _find_statement(full_text,
        [r"data availability statement", r"data are available", r"data can be",
         r"data will be available", r"open data", r"availability of data"])
    metadata["conflicts"] = _find_statement(full_text,
        [r"conflict(?:s)? of interest", r"competing interests?",
         r"declaration of interest", r"no conflicts? of interest"])
    metadata["author_contributions"] = _find_statement(full_text,
        [r"author contributions?", r"contributions? of authors?", r"credit authorship"])

    # ── language ────────────────────────────────────────────────────────────
    sample = flat[:8000].lower()
    if sample:
        scores = {
            "English": len(re.findall(r"\b(?:the|and|of|to|in|that|is|was|for|with|this|are)\b", sample)),
            "French":  len(re.findall(r"\b(?:le|la|les|des|une|est|dans|pour|que|qui|avec)\b", sample)),
            "German":  len(re.findall(r"\b(?:der|die|das|und|ist|für|mit|nicht|ein|einer)\b", sample)),
            "Spanish": len(re.findall(r"\b(?:el|la|los|las|de|que|para|con|una|por|del)\b", sample)),
            "Italian": len(re.findall(r"\b(?:il|lo|che|di|per|con|una|del|nel|sono)\b", sample)),
        }
        best = max(scores, key=scores.get)
        total = sum(scores.values())
        if total and scores[best] / total > 0.35:
            metadata["language"] = best
            metadata["language_confidence"] = round(scores[best] / total, 3)

    metadata["author_count"] = len(metadata["authors"])
    metadata["has_full_text"] = metadata["word_count"] > 800
    return metadata


# ══════════════════════════════════════════════════════════════════════════════
# SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
DEFAULTS = {
    "stage":        "idle",   # idle | running | stopped | done
    "results":      [],
    "log_lines":    [],
    "completed":    0,
    "total":        0,
    "cur_doi":      "",
    "cur_src":      "",
    "out_dir":      None,
    "zip_bytes":    None,
    "report_bytes": None,
    "failed_bytes": None,
    "pq":           None,
    "stop_event":   None,
    "start_time":   None,
    "all_dois":     [],
    "lit_screen":   {},
    "pending_dois": [],
    # Background metadata extraction running alongside the download
    "meta_watcher": None,
    "meta_results": [],
    "meta_done":    0,
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

try:
    import litcheck_ui
except Exception as _lc_err:            # keep the downloader usable if the
    litcheck_ui = None                    # literature modules fail to import
    LITCHECK_IMPORT_ERROR = _lc_err


# ── DOWNLOADER PAGE ────────────────────────────────────────────────────────────
def _collect_page_text(pdf_path, max_pages=MAX_PAGES_FOR_TEXT):
    """Page-indexed plain text for one PDF.

    The deep paper page needs a page number behind every finding, which a single
    flattened string cannot express. Uses PyMuPDF first for maximum speed and
    fidelity, with fallback to pypdf.
    """
    # 1. Try PyMuPDF
    try:
        import pymupdf
        doc = pymupdf.open(str(pdf_path))
        limit = len(doc) if max_pages is None else min(len(doc), max_pages)
        out = [doc[i].get_text() or "" for i in range(limit)]
        doc.close()
        if any(p.strip() for p in out):
            return out
    except Exception:
        pass

    # 2. Try fitz alias
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        limit = len(doc) if max_pages is None else min(len(doc), max_pages)
        out = [doc[i].get_text() or "" for i in range(limit)]
        doc.close()
        if any(p.strip() for p in out):
            return out
    except Exception:
        pass

    # 3. Fallback to pypdf / PyPDF2
    if PdfReader is not None:
        try:
            rdr = PdfReader(str(pdf_path), strict=False)
            out = []
            for page in rdr.pages[:max_pages]:
                try:
                    out.append(page.extract_text() or "")
                except Exception:
                    out.append("")
            if any(p.strip() for p in out):
                return out
        except Exception:
            pass
    return []


# ── Analysis module wiring ─────────────────────────────────────────────────────
# Publish this script's PDF helpers so the Analysis page can reuse them without
# importing the entry script (which would re-run the whole app).
VA.register(extract_pdf_metadata=extract_pdf_metadata,
            compute_file_hash=compute_file_hash,
            collect_page_text=_collect_page_text)


def render_downloader():
    """PDF downloader page: queue, run controls and live progress."""
    # The Vellum wordmark is rendered once for every page at app level; only
    # this page's own one-liner belongs here.
    st.caption("Upload a `.txt` with one DOI per line, or load a queue from "
               "Literature check. Every available PDF is fetched.")

    # Settings live in the main column, not the sidebar. The sidebar carries the
    # nav, the wordmark, Clear/Exit and the contact block, so the settings were
    # the last thing on screen — and every one of them is disabled while a run is
    # going, which is the only time the page is long enough to need them pinned.
    # The three that matter for any run stay visible; the rest collapse.
    is_running = st.session_state.stage == "running"

    st.markdown("#### Settings")
    col_email, col_delay, col_retry = st.columns(3)
    with col_email:
        email = st.text_input(
            ":material/mail: Email (Unpaywall)", value="your@email.com",
            disabled=is_running,
            help="Unpaywall asks for a real address and is more generous with "
                 "repeat callers. Replace this placeholder before a long run.")
    with col_delay:
        delay = st.slider(":material/schedule: Delay between DOIs (sec)",
                          1.0, 10.0, 3.0, 0.5, disabled=is_running)
    with col_retry:
        retries = st.number_input(":material/refresh: Retry attempts", 0, 5, 1,
                                  disabled=is_running)

    with st.expander(":material/tune: Optional — publisher keys, Wiley access, and direct links",
                     expanded=False):
        opt_key, opt_cookie = st.columns(2)
        with opt_key:
            elsevier_key = st.text_input(
                "🔑 Elsevier / Scopus API key (Free at dev.elsevier.com)", value="", disabled=is_running,
                type="password", placeholder="Paste free key from https://dev.elsevier.com",
                help="Unlocks direct automated PDF download for all ScienceDirect (10.1016) papers without Akamai bot protection.")
        with opt_cookie:
            wiley_cookie = st.text_input(
                "🍪 Wiley cookie (optional)", value="", disabled=is_running, type="password",
                placeholder="I2KBRCK=…; MAID=…",
                help="Sign in at onlinelibrary.wiley.com, open any article, then in DevTools copy the Cookie header.")
        st.caption("Direct PDF links mapping (`DOI = url` or `{doi}` pattern, one per line):")
        links_raw = st.text_area(
            "Links", value="", disabled=is_running,
            label_visibility="collapsed",
            placeholder="10.1111/joss.70003 = https://onlinelibrary.wiley.com/doi/epdf/10.1111/joss.70003")

    # ── File upload & Bibliographic Import ──────────────────────────────────────────
    c_hdr1, c_hdr2 = st.columns([4.2, 1.3], vertical_alignment="center")
    with c_hdr1:
        st.markdown("#### Input Queue & Document Import")
    with c_hdr2:
        if st.button("🔄 Reset Session", key="btn_reset_dl_session_top", width="stretch", help="Reset all downloads, queue, and clear session"):
            st.session_state["pending_dois"] = []
            st.session_state["results"] = []
            st.session_state["log_lines"] = []
            st.session_state["stage"] = "idle"
            st.session_state["completed"] = 0
            st.session_state["total"] = 0
            st.session_state["zip_bytes"] = None
            st.session_state["report_bytes"] = None
            st.session_state["failed_bytes"] = None
            st.success("Downloader session reset!")
            st.rerun()

    c_in1, c_in2 = st.columns([1.1, 0.9])
    with c_in1:
        st.markdown("##### 📝 Paste DOIs or Direct PDF Links")
        raw_text_input = st.text_area(
            "Enter DOIs or direct PDF links (one per line)",
            value="",
            placeholder="10.1016/j.jclepro.2025.147050\nhttps://pdf.sciencedirectassets.com/...main.pdf?...\n10.1111/joss.70003",
            height=135,
            disabled=is_running,
            label_visibility="collapsed",
            help="Supports DOIs (10.xxxx/...), full PDF URLs (e.g. from ScienceDirect/S3), or DOI = URL pairs.",
            key="_main_raw_dois_input"
        )
    with c_in2:
        st.markdown("##### 📁 Upload Search Export or File")
        uploaded = st.file_uploader(
            "Upload DOI list or Search Export (.csv, .ris, .bib, .tsv, .txt)",
            type=["csv", "ris", "bib", "tsv", "txt"],
            disabled=is_running,
            label_visibility="collapsed",
            help="Upload CSV exports from Scopus, PubMed, Web of Science, or RIS/BibTeX/TXT DOI lists."
        )

    dois = []
    pd_ = []
    
    # 1. Parse text area
    if raw_text_input and raw_text_input.strip():
        for line in raw_text_input.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line and "://" in line:
                d_part, u_part = line.split("=", 1)
                d_part, u_part = d_part.strip(), u_part.strip()
                pd_.append({"key": d_part, "doi": d_part, "pdf_url": u_part, "title": ""})
            elif line.startswith("http://") or line.startswith("https://"):
                pd_.append({"key": line, "doi": "", "pdf_url": line, "title": ""})
            elif "10." in line:
                m = re.search(r'\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+', line)
                doi_found = m.group(0).rstrip(".,;") if m else line
                rem_title = line.replace(doi_found, "").strip(" -–—:;,|\t")
                pd_.append({
                    "key": doi_found,
                    "doi": doi_found,
                    "pdf_url": "",
                    "title": rem_title if _is_real_title(rem_title, doi_found) else "",
                })
            else:
                pd_.append({"key": line, "doi": line, "pdf_url": "", "title": ""})

    # 2. Parse uploaded file
    if uploaded:
        import vellum_import
        content_bytes = uploaded.read()
        recs, stats = vellum_import.universal_import_file(content_bytes, uploaded.name)
        for i, r in enumerate(recs):
            k = r.get("doi") or r.get("pdf_url") or f"item-{i}"
            rt = r.get("title") or ""
            pd_.append({
                "key": k,
                "doi": r.get("doi") or "",
                "pdf_url": r.get("pdf_url") or "",
                "title": rt if _is_real_title(rt, k) else "",
            })
        if stats["duplicates_removed"] > 0:
            st.success(f"✅ Loaded **{len(recs)} unique article(s)** from `{uploaded.name}` (filtered {stats['duplicates_removed']} duplicates).")

    # 3. Incorporate canonical project.json download queue & pending queue
    import vellum_workspace as VW
    import vellum_direct_download as VDD
    proj_queue = VW.load_project_data().get("download_queue", [])
    if proj_queue:
        for item in proj_queue:
            if isinstance(item, dict):
                k = item.get("doi") or item.get("title") or "item"
                d_val = item.get("doi") or (str(k).strip() if str(k).strip().startswith("10.") else "")
                t_val = item.get("title") or ""
                pd_.append({
                    "key": str(k).strip(),
                    "doi": d_val,
                    "pdf_url": item.get("pdf_url", ""),
                    "title": t_val if _is_real_title(t_val, d_val) else "",
                })

    if st.session_state.get("pending_dois"):
        for item in st.session_state["pending_dois"]:
            if isinstance(item, dict):
                k = item.get("key") or item.get("doi") or item.get("title") or "item"
                d_val = item.get("doi") or (str(k).strip() if str(k).strip().startswith("10.") else "")
                t_val = item.get("title") or ""
                pd_.append({
                    "key": str(k).strip(),
                    "doi": d_val,
                    "pdf_url": item.get("pdf_url", ""),
                    "title": t_val if _is_real_title(t_val, d_val) else "",
                })
            elif isinstance(item, str) and item.strip():
                s = item.strip()
                pd_.append({
                    "key": s,
                    "doi": s if s.startswith("10.") else "",
                    "pdf_url": s if s.startswith("http") else "",
                    "title": "",
                })

    # Deduplicate pd_ while preserving order (and keeping real titles if one entry has it)
    seen_map = {}
    unique_pd = []
    for p in pd_:
        k = (p.get("doi") or p.get("pdf_url") or p.get("key") or "").strip().lower()
        if not k:
            continue
        if k not in seen_map:
            seen_map[k] = p
            unique_pd.append(p)
        else:
            if not seen_map[k].get("title") and p.get("title"):
                seen_map[k]["title"] = p["title"]
            if not seen_map[k].get("pdf_url") and p.get("pdf_url"):
                seen_map[k]["pdf_url"] = p["pdf_url"]
    pd_ = unique_pd
    st.session_state["pending_dois"] = pd_
    dois = [p["key"] for p in pd_ if p.get("key")]

    if pd_:
        _n_doi = sum(1 for p in pd_ if p.get("doi"))
        _n_url = sum(1 for p in pd_ if p.get("pdf_url"))
        st.info(f"📋 **{len(dois)} item(s) in queue** ({_n_doi} with DOI, {_n_url} with direct PDF link).")
        with st.expander(":material/visibility: Preview queued articles"):
            for p in pd_[:200]:
                t_disp = p.get("title") or _TITLE_CACHE.get((p.get("doi") or "").lower()) or p.get("key")
                st.write(f"**{t_disp}**  ·  `{p.get('doi') or p.get('pdf_url','')}`")
            if len(pd_) > 200:
                st.caption(f"…and {len(pd_)-200} more.")
            if st.button(":material/delete: Clear Queue", key="_clear_curr_queue_btn"):
                st.session_state["pending_dois"] = []
                VDD.clear_download_queue()
                st.rerun()

    st.divider()

    # ── Start / Stop buttons ───────────────────────────────────────────────────────
    can_start = bool(dois) and st.session_state.stage not in ("running",)
    can_stop  = st.session_state.stage == "running"

    col_start, col_stop = st.columns([3, 1])
    with col_start:
        start_clicked = st.button(":material/play_arrow: Start downloading", type="primary",
                                   width="stretch", disabled=not can_start)
    with col_stop:
        stop_clicked = st.button(":material/stop: Stop", width="stretch",
                                  disabled=not can_stop,
                                  help="Stop after current DOI finishes")

    # ── Handle Stop ────────────────────────────────────────────────────────────────
    if stop_clicked and st.session_state.stop_event is not None:
        st.session_state.stop_event.set()
        watcher = st.session_state.get("meta_watcher")
        if watcher is not None:
            watcher.stop()
        st.warning("⏹ Stop requested — finishing current DOI then building report…")

    # ── Handle Start ───────────────────────────────────────────────────────────────
    if start_clicked and dois:
        import vellum_workspace as VW
        out_dir = VW.get_project_dir() / "papers"
        out_dir.mkdir(parents=True, exist_ok=True)
        pq         = queue.Queue()
        stop_event = threading.Event()

        WILEY_COOKIE      = str(wiley_cookie or "").strip()
        ELSEVIER_USER_KEY = str(elsevier_key or "").strip()
        DIRECT_LINKS, DEFAULT_LINKS = parse_direct_links(links_raw)

        # Build url map and hint map for all queued items (only real titles!)
        _hints = {}
        _url_map = {}
        _pend = st.session_state.get("pending_dois") or []
        for p in _pend:
            if isinstance(p, dict):
                pkey = p.get("key") or p.get("doi") or ""
                pdoi = (p.get("doi") or "").strip().lower()
                purl = (p.get("pdf_url") or "").strip()
                ptitle = p.get("title") or ""
                if _is_real_title(ptitle, pdoi or pkey):
                    if pkey:
                        _hints[pkey] = ptitle
                    if pdoi:
                        _hints[pdoi] = ptitle
                if purl:
                    if pkey:
                        DIRECT_LINKS.setdefault(pkey.lower(), []).append(purl)
                        _url_map[pkey] = purl
                    if pdoi:
                        DIRECT_LINKS.setdefault(pdoi, []).append(purl)
                        _url_map[pdoi] = purl

        for k, v in DEFAULTS.items():
            st.session_state[k] = v

        st.session_state.stage      = "running"
        st.session_state.total      = len(dois)
        st.session_state.all_dois   = list(dois)
        st.session_state.out_dir    = str(out_dir)
        st.session_state.pq         = pq
        st.session_state.stop_event = stop_event
        st.session_state.start_time = time.time()

        _email   = str(email)
        _delay   = float(delay)
        _retries = int(retries)

        def worker(dois_list, out_dir, pq, retries, delay, email, stop_event, t0,
                   hints=None, url_map=None):
            from concurrent.futures import ThreadPoolExecutor, as_completed
            hints = hints or {}
            url_map = url_map or {}
            results_map = {}

            # Pre-fetch missing titles concurrently in background so logs & filenames are instant
            missing_title_dois = [
                d for d in dois_list[:60]
                if not _is_real_title(hints.get(d), d) and not d.startswith(("http://", "https://"))
            ]
            if missing_title_dois:
                with ThreadPoolExecutor(max_workers=8) as t_pool:
                    fut_map = {t_pool.submit(fetch_title, d): d for d in missing_title_dois}
                    for fut in as_completed(fut_map):
                        d_k = fut_map[fut]
                        try:
                            t_res = fut.result()
                            if _is_real_title(t_res, d_k):
                                hints[d_k] = t_res
                        except Exception:
                            pass

            for attempt in range(retries + 1):
                if stop_event.is_set(): break
                target = dois_list if attempt == 0 else \
                         [d for d in dois_list if results_map.get(d, {}).get("status") == "failed"]
                if not target: break
                if attempt > 0:
                    pq.put(("retry_banner", attempt, len(target)))

                def _dl_one(d_item):
                    if stop_event.is_set():
                        return None
                    local_scraper = make_scraper()
                    res = download_single_doi(
                        d_item, out_dir, local_scraper, email, pq,
                        title_hint=hints.get(d_item) or hints.get(d_item.lower()),
                        direct_url=url_map.get(d_item) or url_map.get(d_item.lower())
                    )
                    if delay > 0.2:
                        time.sleep(min(delay, 1.5))
                    return d_item, res

                max_w = 3 if len(target) > 1 else 1
                with ThreadPoolExecutor(max_workers=max_w) as pool:
                    futures = [pool.submit(_dl_one, d) for d in target]
                    for fut in as_completed(futures):
                        if stop_event.is_set():
                            break
                        try:
                            out = fut.result()
                            if out:
                                d_item, res = out
                                results_map[d_item] = res
                        except Exception:
                            pass

            results = [results_map[d] for d in dois_list if d in results_map]

            # Always build artifacts (whether done or stopped)
            elapsed = time.time() - t0
            try:
                zb, rb, fb = build_artifacts(out_dir, results, elapsed, email)
            except Exception as e:
                zb, rb, fb = b"", b"", b""

            if stop_event.is_set():
                pq.put(("stopped", results, zb, rb, fb))
            else:
                pq.put(("done", results, zb, rb, fb))

        t = threading.Thread(
            target=worker,
            args=(list(dois), out_dir, pq, _retries, _delay,
                  _email, stop_event, st.session_state.start_time, _hints, _url_map),
            daemon=True
        )
        t.start()

        # Analyse each PDF while it is still downloading instead of making the
        # user wait for a second pass at the end.
        watcher = VA.MetadataWatcher(out_dir, pq, stop_event=stop_event)
        st.session_state.meta_watcher = watcher
        st.session_state.meta_results = []
        st.session_state.meta_done = 0
        watcher.start()
        st.rerun()

    # ── Progress / Results UI ──────────────────────────────────────────────────────
    if st.session_state.stage in ("running", "stopped", "done"):

        # Drain queue (max 100 msgs per rerun)
        if st.session_state.stage == "running" and st.session_state.pq is not None:
            pq = st.session_state.pq
            for _ in range(100):
                try:
                    msg = pq.get_nowait()
                except queue.Empty:
                    break

                kind = msg[0]

                if kind == "trying":
                    _, doi, src = msg
                    st.session_state.cur_doi = doi
                    st.session_state.cur_src = src

                elif kind == "preview":
                    _, doi, src = msg
                    t_lbl = _TITLE_CACHE.get(doi.strip().lower(), "")
                    t_part = f" — {t_lbl[:90]}" if t_lbl else ""
                    st.session_state.log_lines.append(
                        f"<div class='log-warn'>… <b>{doi}</b>{t_part} — {src} returned a "
                        f"1-page preview, trying other sources</div>")

                elif kind == "success":
                    st.session_state.completed = min(
                        st.session_state.completed + 1, st.session_state.total)
                    _, doi, src, title, fname, size_kb = msg
                    disp_title = title if _is_real_title(title, doi) else (_TITLE_CACHE.get(doi.strip().lower()) or fname)
                    st.session_state.log_lines.append(
                        f"<div class='log-ok'>✓ <b>{doi}</b> — "
                        f"{disp_title[:110]} "
                        f"<span style='color:#5a5957'>via {src} ({size_kb:.0f} KB)</span></div>")

                elif kind == "partial":
                    st.session_state.completed = min(
                        st.session_state.completed + 1, st.session_state.total)
                    _, doi, src, title, fname, size_kb = msg
                    disp_title = title if _is_real_title(title, doi) else (_TITLE_CACHE.get(doi.strip().lower()) or fname)
                    st.session_state.log_lines.append(
                        f"<div class='log-skip'>⚠ <b>{doi}</b> — "
                        f"{disp_title[:110]} "
                        f"<span style='color:#5a5957'>only 1 page via {src} "
                        f"({size_kb:.0f} KB) — likely a publisher preview</span></div>")

                elif kind == "skip":
                    st.session_state.completed = min(
                        st.session_state.completed + 1, st.session_state.total)
                    _, doi, title, fname = msg
                    disp_title = title if _is_real_title(title, doi) else (_TITLE_CACHE.get(doi.strip().lower()) or fname)
                    st.session_state.log_lines.append(
                        f"<div class='log-skip'>⏭ <b>{doi}</b> — {disp_title[:110]} <span style='color:#5a5957'>(already cached)</span></div>")

                elif kind == "fail":
                    st.session_state.completed = min(
                        st.session_state.completed + 1, st.session_state.total)
                    _, doi, title = msg
                    disp_title = title if _is_real_title(title, doi) else (_TITLE_CACHE.get(doi.strip().lower()) or fetch_title(doi) or "(no title)")
                    from urllib.parse import quote_plus
                    gs_q = quote_plus(disp_title if _is_real_title(disp_title, doi) else doi)
                    gs_link = f"<a href='https://scholar.google.com/scholar?hl=en&q={gs_q}' target='_blank' style='color:#38bdf8;text-decoration:underline;'>Google Scholar</a>"
                    if doi.startswith("10.1016"):
                        tip = (f" — all automated sources failed (Elsevier bot protection). "
                               f"<a href='https://doi.org/{doi}' target='_blank' style='color:#38bdf8;text-decoration:underline;'>Open ScienceDirect</a> or {gs_link}")
                    else:
                        tip = f" — all sources failed · {gs_link}"
                    st.session_state.log_lines.append(
                        f"<div class='log-fail'>✗ <b>{doi}</b> — "
                        f"{disp_title}{tip}</div>")

                elif kind == "retry_banner":
                    _, attempt, n = msg
                    st.session_state.completed = 0
                    st.session_state.total     = n
                    st.session_state.log_lines.append(
                        f"<div class='log-retry'>🔁 Retry attempt {attempt} "
                        f"— retrying {n} failed DOI(s)…</div>")

                elif kind in ("meta_update", "meta_final"):
                    # Metadata extracted in the background while downloading.
                    _, snapshot = msg
                    st.session_state.meta_results = snapshot
                    st.session_state.meta_done = len(snapshot)
                    if kind == "meta_final":
                        watcher = st.session_state.get("meta_watcher")
                        if watcher is not None and watcher.error:
                            st.session_state.log_lines.append(
                                f"<div class='log-warn'>⚠ Metadata analysis "
                                f"stopped early — {watcher.error}</div>")

                elif kind in ("stopped", "done"):
                    _, results, zb, rb, fb = msg
                    not_started = len(st.session_state.all_dois) - len(results)
                    sl = len([r for r in results if r["status"]=="success"])
                    fl = len([r for r in results if r["status"]=="failed"])

                    # Let the watcher finish the last few files before the run
                    # is declared over, so the analysis page has complete data.
                    watcher = st.session_state.get("meta_watcher")
                    if watcher is not None and watcher.is_alive():
                        watcher.stop()

                    if kind == "stopped":
                        st.session_state.log_lines.append(
                            f"<div class='log-stop'>🛑 STOPPED — "
                            f"✓ {sl} downloaded &nbsp; ✗ {fl} failed &nbsp; "
                            f"⏭ {not_started} not started</div>")
                        st.session_state.stage = "stopped"
                    else:
                        st.session_state.stage = "done"

                    st.session_state.results      = results
                    st.session_state.zip_bytes    = zb
                    st.session_state.report_bytes = rb
                    st.session_state.failed_bytes = fb
                    break

        # ── Status bar ─────────────────────────────────────────────────────────
        total     = max(st.session_state.total, 1)
        completed = st.session_state.completed
        pct       = min(completed / total, 1.0)

        stage = st.session_state.stage
        if stage == "running":
            st.markdown(f"### ⏳ Downloading… **{completed} / {total}** ({pct*100:.0f}%)")
        elif stage == "stopped":
            sl = len([r for r in st.session_state.results if r["status"]=="success"])
            fl = len([r for r in st.session_state.results if r["status"]=="failed"])
            ns = len(st.session_state.all_dois) - len(st.session_state.results)
            st.markdown(f"### 🛑 Stopped &nbsp;·&nbsp; ✓ {sl} downloaded &nbsp; ✗ {fl} failed &nbsp; ⏭ {ns} not started")
        else:
            sl = len([r for r in st.session_state.results if r["status"]=="success"])
            fl = len([r for r in st.session_state.results if r["status"]=="failed"])
            st.markdown(f"### ✅ Done! &nbsp;·&nbsp; ✓ {sl} downloaded &nbsp; ✗ {fl} failed")

        st.progress(pct)

        if stage == "running" and st.session_state.cur_doi:
            st.markdown(
                f"<div style='color:#797876;font-size:0.82rem;margin-top:0.3rem;'>"
                f"🔍 <code>{st.session_state.cur_doi[:60]}</code>"
                f" → trying <i>{st.session_state.cur_src}</i>…</div>",
                unsafe_allow_html=True)

        # Metadata extraction runs alongside the download.
        meta_done = st.session_state.get("meta_done", 0)
        meta_target = len(st.session_state.get("all_dois") or [])
        if stage == "running" and meta_target:
            st.caption(
                f":material/psychology: Metadata extracted for "
                f"{meta_done} of {meta_target} paper(s) in parallel.")
            st.progress(min(meta_done / meta_target, 1.0),
                        text=f"Analysing {meta_done}/{meta_target}")
        elif stage in ("done", "stopped") and meta_done:
            st.caption(
                f":material/check_circle: {meta_done} paper(s) analysed in "
                f"parallel — see the Analysis page for tables and charts.")

        # ── Summary cards ───────────────────────────────────────────────────────
        if stage in ("done","stopped") and st.session_state.results:
            results = st.session_state.results
            sl_list = [r for r in results if r["status"]=="success"]
            fl_list = [r for r in results if r["status"]=="failed"]
            ns_list = len(st.session_state.all_dois) - len(results)
            st.divider()
            c1,c2,c3,c4 = st.columns(4)
            with c1:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-num' style='color:#e0e0e0'>{len(st.session_state.all_dois)}</div>
                    <div class='metric-label'>Total DOIs</div></div>""", unsafe_allow_html=True)
            with c2:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-num' style='color:#6daa45'>{len(sl_list)}</div>
                    <div class='metric-label'>Downloaded</div></div>""", unsafe_allow_html=True)
            with c3:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-num' style='color:#dd6974'>{len(fl_list)}</div>
                    <div class='metric-label'>Failed</div></div>""", unsafe_allow_html=True)
            with c4:
                st.markdown(f"""<div class='metric-card'>
                    <div class='metric-num' style='color:#797876'>{ns_list}</div>
                    <div class='metric-label'>Not Started</div></div>""", unsafe_allow_html=True)

        # ── Log expander ────────────────────────────────────────────────────────
        st.divider()
        with st.expander(":material/description: View detailed log", expanded=(stage in ("stopped","done"))):
            log_html = "".join(st.session_state.log_lines)
            if log_html:
                st.markdown(log_html, unsafe_allow_html=True)
            else:
                st.markdown("<span style='color:#5a5957'>No entries yet…</span>",
                            unsafe_allow_html=True)

        # ── Download buttons ────────────────────────────────────────────────────
        st.divider()
        st.markdown("### Download results")
        is_ready = stage in ("done","stopped")

        c1,c2,c3 = st.columns(3)
        with c1:
            zb = st.session_state.zip_bytes or b"."
            st.download_button(":material/download: All PDFs (ZIP)",
                data=zb, file_name="downloaded_papers.zip",
                mime="application/zip", width="stretch",
                disabled=not is_ready, key="dl_zip")
        with c2:
            rb = st.session_state.report_bytes or b"."
            st.download_button(":material/article: Download report",
                data=rb, file_name="download_report.txt",
                mime="text/plain", width="stretch",
                disabled=not is_ready, key="dl_report")
        with c3:
            fb = st.session_state.failed_bytes or b""
            if is_ready and not fb:
                st.success("🎉 No failures!")
            else:
                st.download_button(":material/error: Failed DOIs (.txt)",
                    data=fb or b".", file_name="failed_to_download.txt",
                    mime="text/plain", width="stretch",
                    disabled=not is_ready, key="dl_failed")

        if stage in ("done", "stopped") and fl_list:
            st.divider()
            st.markdown("#### 🎓 Google Scholar CASA & Direct Link Catcher")
            st.caption(
                "For papers behind institutional/CASA walls (e.g. Emerald `[PDF] emerald.com` on Google Scholar or ScienceDirect), "
                "click **Search Google Scholar `[PDF]`** to click the PDF in your browser, then click **📥 Auto-Import from Downloads/Browser** "
                "(or paste a direct link below) — Vellum will automatically grab the file and rename it to the exact article title."
            )
            import vellum_workspace as VW
            out_p = VW.get_project_dir() / "papers"
            out_p.mkdir(parents=True, exist_ok=True)
            from urllib.parse import quote_plus
            for idx_f, r_fail in enumerate(fl_list[:15]):
                f_doi = r_fail.get("doi") or ""
                f_title = r_fail.get("title") or _TITLE_CACHE.get(f_doi.strip().lower()) or fetch_title(f_doi) or f_doi
                q_sch = quote_plus(f_title if _is_real_title(f_title, f_doi) else f_doi)
                fc1, fc2, fc3 = st.columns([3.4, 1.3, 1.3], vertical_alignment="center")
                with fc1:
                    st.markdown(f"**{f_title}**  \n`{f_doi}`")
                with fc2:
                    st.link_button("🎓 Search Google Scholar [PDF]", f"https://scholar.google.com/scholar?hl=en&q={q_sch}", width="stretch")
                with fc3:
                    if st.button("📥 Auto-Import & Rename", key=f"_auto_imp_{idx_f}_{f_doi}", width="stretch"):
                        target_fname = sanitize_filename(f_title) if _is_real_title(f_title, f_doi) else sanitize_filename(f_doi.replace("/", "_"))
                        target_dest = out_p / target_fname
                        if _scan_browser_sessions_and_downloads(f_doi, target_dest, make_scraper()):
                            r_fail["status"] = "success"
                            r_fail["source"] = "Google Scholar / Browser"
                            r_fail["filename"] = target_fname
                            r_fail["size_kb"] = round(target_dest.stat().st_size / 1024, 1)
                            st.session_state.log_lines.append(
                                f"<div class='log-ok'>✓ <b>{f_doi}</b> — {f_title[:110]} <span style='color:#5a5957'>via Google Scholar / Browser ({r_fail['size_kb']:.0f} KB)</span></div>"
                            )
                            zb_new, rb_new, fb_new = build_artifacts(out_p, st.session_state.results, 1.0, email)
                            st.session_state.zip_bytes = zb_new
                            st.session_state.report_bytes = rb_new
                            st.session_state.failed_bytes = fb_new
                            st.success(f"🎉 Imported & renamed to `{target_fname}`!")
                            st.rerun()
                        else:
                            st.warning("No matching PDF found in `~/Downloads` or active browser tabs yet. Click `Search Google Scholar [PDF]` first to trigger the download in Chrome, then click `Auto-Import & Rename`.")

            qc1, qc2, qc3 = st.columns([3.2, 1.8, 1.0], vertical_alignment="bottom")
            with qc1:
                catch_url = st.text_input("Or paste a direct PDF URL / signed link (`casa_token`, `pdf.sciencedirectassets.com`)", placeholder="https://www.emerald.com/...pdf?casa_token=...", key="_qc_url_input")
            with qc2:
                catch_title = st.text_input("Title or DOI (optional)", placeholder="e.g. 10.1108/apjml-07-2022-0577", key="_qc_title_input")
            with qc3:
                if st.button("⬇️ Download", type="primary", width="stretch", key="_btn_qc_fetch"):
                    if catch_url.strip():
                        import vellum_direct_download as VDD
                        ok, msg, _, local_f = VDD.download_single_paper_direct({
                            "title": catch_title.strip() or "",
                            "doi": catch_title.strip() if catch_title.strip().startswith("10.") else "",
                            "pdf_url": catch_url.strip()
                        })
                        if ok:
                            st.success(f"🎉 Successfully saved: `{local_f.name}`")
                            st.rerun()
                        else:
                            st.error(f"Could not download: {msg}")
                    else:
                        st.warning("Please paste a PDF URL first.")

        # Auto-rerun while running
        if stage == "running":
            time.sleep(0.5)
            st.rerun()

    # Analysis (duplicates, metadata, dashboard) lives on its own page so the
    # downloader stays focused on downloading. See app_pages/analysis.py.


def render_literature():
    """Literature check page (multi-source search + screening)."""
    if litcheck_ui is None:
        st.warning("Literature Check is unavailable because its modules failed "
                   "to import.")
        st.code(str(LITCHECK_IMPORT_ERROR))
        return
    try:
        litcheck_ui.render()
    except Exception as exc:
        st.error(f"Literature Check failed to render: {type(exc).__name__}: {exc}")



# ══════════════════════════════════════════════════════════════════════════════
# UNIFIED WORKFLOW ROUTER & TOP GLASS NAVIGATION
# ══════════════════════════════════════════════════════════════════════════════
import vellum_workspace as VW
import vellum_theme as VT
import vellum_paper_pool as VPP
import vellum_pages as VP

# Clear session support
VB.maybe_clear()

# Every screen is a real Streamlit page with its own URL. That is what makes
# the address bar follow the user, the browser's Back button work, and a
# screen linkable. The navigation widget itself is hidden because the app
# draws its own glass navigation bar; the URL is the part that matters.
_pages = VP.build({"library_downloader": lambda: render_downloader()})
_page = st.navigation(_pages, position="hidden")

if not VW.is_vault_initialized() or st.session_state.get("_show_welcome_hub", False):
    from app_pages import welcome_hub
    welcome_hub.render()
else:
    # Handovers between features: a screen can ask to open another one.
    if st.session_state.pop("_go_download", False):
        VP.go("library_downloader")
    if st.session_state.pop("_go_graph", False):
        VP.go("discover_citation")
    if st.session_state.pop("_go_analysis", False):
        VP.go("evidence_methodology")
    if st.session_state.pop("_go_literature", False):
        VP.go("discover_literature")

    _page.run()


