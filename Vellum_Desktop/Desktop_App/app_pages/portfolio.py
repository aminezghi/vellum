"""
app_pages/portfolio.py — Researcher Portfolio & CV Generation Engine for Vellum.

Provides genuine extraction, aggregation, bibliometric calculation, and
export of researcher publications and CVs from screened records and local PDFs.
"""

from __future__ import annotations

import html
import json
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

try:
    import streamlit as st
except ImportError:
    st = None

import vellum_analysis as VA
import vellum_workspace as VW


# ── DOI & Metadata Regex Helpers ──────────────────────────────────────────────
DOI_REGEX = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.IGNORECASE)


def _clean_str(val: Any, default: str = "") -> str:
    """Safely coerce any profile or record value to a clean string."""
    if val is None or val is False:
        return default
    s = str(val).strip()
    return s if s else default


def _sanitize_url(url: Any) -> str:
    """
    Sanitize URL ensuring only safe schemes (http, https, mailto) are permitted.
    Rejects javascript:, data:, vbscript:, and other dangerous pseudo-protocols.
    """
    if not url or url is False:
        return ""
    raw = str(url).strip()
    # Strip invisible and control characters
    raw = re.sub(r"[\x00-\x1f\x7f-\x9f]", "", raw)
    lower = raw.lower()
    if lower.startswith(("javascript:", "data:", "vbscript:", "file:")):
        return ""
    if lower.startswith(("http://", "https://", "mailto:")):
        return raw
    # Allow standard domain-like inputs by prefixing https://
    if lower.startswith("www.") or (re.match(r"^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(/.*)?$", raw) and ":" not in raw):
        return f"https://{raw}"
    return ""


def ocr_enrich(folder: str | Path | None, max_files: int = 40, timeout: int = 120) -> int:
    """
    Enrich publication records by reading and extracting metadata from local PDFs.
    Scans the provided directory, extracts text layers or applies OCR fallback,
    and identifies DOIs, titles, and abstracts.
    Stores enriched records in st.session_state['local_pdf_records'].
    Returns the count of successfully processed PDFs.
    """
    if not folder or (isinstance(folder, str) and not folder.strip()):
        return 0

    try:
        folder_path = Path(folder).resolve()
        if not folder_path.exists() or not folder_path.is_dir():
            return 0
        pdf_files = list(folder_path.glob("*.pdf"))[:max_files]
    except (TypeError, ValueError, OSError):
        return 0

    if not pdf_files:
        return 0

    enriched_records = []
    start_time = time.time()

    for pdf in pdf_files:
        if time.time() - start_time > timeout:
            break

        try:
            meta = VA.extract_pdf_metadata(pdf)
            pages = VA.page_text(pdf, max_pages=3)
            joined_text = " ".join(pages)

            # Discover DOI from text if not in metadata
            doi = ""
            doi_match = DOI_REGEX.search(joined_text)
            if doi_match:
                doi = doi_match.group(0).rstrip(".;,")

            title = meta.get("title") or pdf.stem.replace("_", " ")
            abstract = meta.get("abstract") or (joined_text[:500] if joined_text else "")

            rec = {
                "title": title,
                "journal": meta.get("journal") or "Local PDF",
                "cited_by": meta.get("cited_by") or 0,
                "doi": doi,
                "is_oa": True,
                "pdf_url": str(pdf),
                "authors": meta.get("authors") or [],
                "year": meta.get("year"),
                "abstract": abstract,
                "screen": "include",
            }
            enriched_records.append(rec)
        except Exception:
            continue

    if st is not None and hasattr(st, "session_state"):
        existing = st.session_state.get("local_pdf_records", [])
        combined = list(existing) + enriched_records
        # Deduplicate by DOI or title
        seen = set()
        deduped = []
        for r in combined:
            k = (r.get("doi") or r.get("title") or "").strip().lower()
            if k and k not in seen:
                seen.add(k)
                deduped.append(r)
        st.session_state["local_pdf_records"] = deduped

    return len(enriched_records)


def _gather_records() -> pd.DataFrame:
    """
    Gather publications from the active project workspace and session state.
    Returns a standardized DataFrame of screened/discovered publications.
    """
    project_data = VW.load_project_data()
    search_records = list(project_data.get("search_records", []))

    if st is not None and hasattr(st, "session_state"):
        session_records = st.session_state.get("lit_records") or st.session_state.get("lit_unique") or []
        for r in session_records:
            if isinstance(r, dict):
                search_records.append(r)
        local_records = st.session_state.get("local_pdf_records", [])
        search_records.extend(local_records)

    screened_map = project_data.get("screened", {})
    if st is not None and hasattr(st, "session_state"):
        screened_map.update(st.session_state.get("screened", {}))

    rows = []
    seen = set()

    for p in search_records:
        doi = _clean_str(p.get("doi"))
        title = _clean_str(p.get("title") or p.get("name") or "Untitled")
        key = (doi.lower() if doi else title.lower())
        if not key or key in seen:
            continue
        seen.add(key)

        target_id = doi if (doi and doi.startswith("10.")) else title
        screen_dec = screened_map.get(target_id, {})
        screen_status = screen_dec.get("status") or p.get("screen") or "include"

        authors = p.get("authors") or []
        if isinstance(authors, list):
            auth_str = ", ".join(str(a) for a in authors[:3]) + (" et al." if len(authors) > 3 else "")
        else:
            auth_str = str(authors)

        raw_cites = p.get("cited_by_count") if p.get("cited_by_count") is not None else p.get("cited_by")
        try:
            cites = max(0, int(float(raw_cites))) if raw_cites is not None and not isinstance(raw_cites, bool) else 0
        except (ValueError, TypeError):
            cites = 0

        rows.append({
            "title": title,
            "journal": p.get("journal") or p.get("venue") or "Scholarly Source",
            "cited_by": cites,
            "doi": doi,
            "is_oa": bool(p.get("is_oa") or p.get("pdf_url")),
            "pdf_url": p.get("pdf_url") or "",
            "authors": auth_str,
            "year": p.get("year"),
            "screen": screen_status,
        })

    if not rows:
        return pd.DataFrame(columns=[
            "title", "journal", "cited_by", "doi", "is_oa", "pdf_url", "authors", "year", "screen"
        ])

    return pd.DataFrame(rows)


def _gather_downloads() -> pd.DataFrame:
    """
    Gather publications specifically from downloaded PDFs in the project's papers directory.
    """
    p_dir = VW.get_project_dir()
    papers_dir = p_dir / "papers"
    if not papers_dir.exists():
        return pd.DataFrame(columns=[
            "title", "journal", "cited_by", "doi", "is_oa", "pdf_url", "authors", "year", "screen"
        ])

    pdf_files = list(papers_dir.glob("*.pdf"))
    if not pdf_files:
        return pd.DataFrame(columns=[
            "title", "journal", "cited_by", "doi", "is_oa", "pdf_url", "authors", "year", "screen"
        ])

    project_data = VW.load_project_data()
    search_records = {
        (r.get("doi") or "").lower(): r
        for r in project_data.get("search_records", [])
        if isinstance(r, dict) and r.get("doi")
    }

    rows = []
    for pdf in pdf_files:
        meta = VA.extract_pdf_metadata(pdf)
        doi = meta.get("doi") or ""
        matched = search_records.get(doi.lower()) if doi else None

        title = (matched.get("title") if matched else None) or meta.get("title") or pdf.stem.replace("_", " ")
        venue = (matched.get("journal") or matched.get("venue") if matched else None) or "Local Vault PDF"
        raw_cites = (matched.get("cited_by") if matched else 0) or 0
        try:
            cites = max(0, int(float(raw_cites))) if raw_cites is not None and not isinstance(raw_cites, bool) else 0
        except (ValueError, TypeError):
            cites = 0

        rows.append({
            "title": title,
            "journal": venue,
            "cited_by": cites,
            "doi": doi,
            "is_oa": True,
            "pdf_url": str(pdf),
            "authors": meta.get("authors") or [],
            "year": meta.get("year"),
            "screen": "include",
        })

    return pd.DataFrame(rows)


def _coerce_dataframe(data: Any) -> pd.DataFrame:
    """
    Polymorphically normalize input data into a pd.DataFrame.
    Supports:
      - pd.DataFrame (returned directly without copy)
      - list or tuple of dicts / records
      - dict of column iterables or single-record scalar dict
      - pd.Series
      - None, empty collections, or invalid types (returns empty pd.DataFrame)
    """
    if data is None:
        return pd.DataFrame()
    if isinstance(data, pd.DataFrame):
        return data
    if isinstance(data, (list, tuple)):
        if not data:
            return pd.DataFrame()
        try:
            return pd.DataFrame(list(data))
        except Exception:
            return pd.DataFrame()
    if isinstance(data, dict):
        if not data:
            return pd.DataFrame()
        try:
            if any(isinstance(v, (list, tuple, pd.Series)) for v in data.values()):
                return pd.DataFrame(data)
            return pd.DataFrame([data])
        except Exception:
            return pd.DataFrame()
    if isinstance(data, pd.Series):
        try:
            return data.to_frame().T if any(k in data.index for k in ("title", "doi", "cited_by")) else pd.DataFrame(data)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


def metrics_for(df: Any) -> Dict[str, Any]:
    """
    Calculate genuine bibliometric summary metrics for a publication DataFrame:
      - publications: total count
      - citations: total citation count
      - h_index: Hirsch index
      - journals: count of distinct journals/venues
      - oa_share: percentage of open access publications
    """
    df = _coerce_dataframe(df)
    if df.empty:
        return {
            "publications": 0,
            "citations": 0,
            "h_index": 0,
            "journals": 0,
            "oa_share": 0.0,
        }

    total_pubs = len(df)

    # Citations with non-negative clamping
    cites = []
    if "cited_by" in df.columns:
        for val in df["cited_by"]:
            try:
                if pd.notna(val) and not isinstance(val, bool):
                    cites.append(max(0, int(float(val))))
            except (ValueError, TypeError):
                continue
    total_cites = sum(cites)

    # h-index calculation
    sorted_cites = sorted(cites, reverse=True)
    h_idx = 0
    for i, c in enumerate(sorted_cites):
        if c >= i + 1:
            h_idx = i + 1
        else:
            break

    # Journals / Venues
    venues = set()
    if "journal" in df.columns:
        for j in df["journal"].dropna():
            sj = str(j).strip()
            if sj and sj.lower() not in ("unknown", "n/a", "scholarly source"):
                venues.add(sj)
    journal_count = len(venues)

    # Open Access Share
    oa_count = 0
    if "is_oa" in df.columns:
        for val in df["is_oa"]:
            if val is True or str(val).lower() in ("true", "yes", "1", "open access"):
                oa_count += 1
    oa_share = round((oa_count / total_pubs) * 100, 1) if total_pubs > 0 else 0.0

    return {
        "publications": total_pubs,
        "citations": total_cites,
        "h_index": h_idx,
        "journals": journal_count,
        "oa_share": oa_share,
    }


def to_markdown(prof: Optional[Dict[str, Any]], df: Any) -> str:
    """
    Generate an academic Curriculum Vitae in Markdown format.
    """
    prof = prof or {}
    name = _clean_str(prof.get("name"), "Researcher")
    affiliation = _clean_str(prof.get("affiliation"))
    tagline = _clean_str(prof.get("tagline"))
    email = _clean_str(prof.get("email"))
    orcid = _clean_str(prof.get("orcid"))
    raw_website = _clean_str(prof.get("website"))
    safe_website = _sanitize_url(raw_website)

    lines = [f"# {name}"]
    if tagline:
        lines.append(f"*{tagline}*\n")
    if affiliation:
        lines.append(f"**Affiliation:** {affiliation}")

    contacts = []
    if email:
        contacts.append(f"Email: {email}")
    if orcid:
        clean_orcid = re.sub(r"[^0-9X\-]", "", orcid)
        contacts.append(f"ORCID: [{orcid}](https://orcid.org/{clean_orcid})")
    if safe_website:
        contacts.append(f"Website: [{raw_website}]({safe_website})")
    if contacts:
        lines.append(" | ".join(contacts))

    lines.append("\n---\n")

    # Metrics
    df = _coerce_dataframe(df)
    m = metrics_for(df)
    lines.append("## Bibliometric Overview")
    lines.append(f"- **Total Publications:** {m['publications']}")
    lines.append(f"- **Total Citations:** {m['citations']}")
    lines.append(f"- **h-index:** {m['h_index']}")
    lines.append(f"- **Distinct Venues:** {m['journals']}")
    lines.append(f"- **Open Access Share:** {m['oa_share']}%\n")

    # Publications List
    lines.append("## Selected Publications\n")
    if not df.empty:
        # Sort by citations descending if available
        sorted_df = df.sort_values(by="cited_by", ascending=False) if "cited_by" in df.columns else df
        for idx, row in sorted_df.iterrows():
            title = row.get("title") or "Untitled"
            authors = row.get("authors") or ""
            journal = row.get("journal") or ""
            year = row.get("year") or ""
            doi = row.get("doi") or ""

            raw_cites = row.get("cited_by")
            try:
                cites = max(0, int(float(raw_cites))) if raw_cites is not None and not isinstance(raw_cites, bool) else 0
            except (ValueError, TypeError):
                cites = 0

            pub_line = f"1. **{title}**"
            details = []
            if authors:
                details.append(str(authors))
            if journal:
                details.append(f"*{journal}*")
            if year:
                details.append(f"({year})")
            if doi:
                details.append(f"[DOI: {doi}](https://doi.org/{doi})")
            if cites > 0:
                details.append(f"Citations: {cites}")

            if details:
                pub_line += f"<br>&nbsp;&nbsp;&nbsp;&nbsp;{'; '.join(details)}"
            lines.append(pub_line)
    else:
        lines.append("*No publications recorded yet.*")

    lines.append(f"\n\n*Generated by Vellum Research Workbench on {time.strftime('%Y-%m-%d')}*")
    return "\n".join(lines)


def to_html(prof: Optional[Dict[str, Any]], df: Any) -> str:
    """
    Generate a standalone HTML Curriculum Vitae document.
    """
    prof = prof or {}
    name_val = prof.get("name")
    name = html.escape(str(name_val if name_val not in (None, False, "") else "Researcher"))

    affil_val = prof.get("affiliation")
    affiliation = html.escape(str(affil_val if affil_val not in (None, False) else ""))

    tagline_val = prof.get("tagline")
    tagline = html.escape(str(tagline_val if tagline_val not in (None, False) else ""))

    email_val = prof.get("email")
    email = html.escape(str(email_val if email_val not in (None, False) else ""))

    orcid_val = prof.get("orcid")
    orcid = html.escape(str(orcid_val if orcid_val not in (None, False) else ""))

    raw_website = str(prof.get("website") if prof.get("website") not in (None, False) else "").strip()
    safe_website = _sanitize_url(raw_website)
    website = html.escape(safe_website)

    df = _coerce_dataframe(df)
    m = metrics_for(df)

    rows_html = []
    if not df.empty:
        sorted_df = df.sort_values(by="cited_by", ascending=False) if "cited_by" in df.columns else df
        for _, row in sorted_df.iterrows():
            title = html.escape(str(row.get("title") or "Untitled"))
            authors = html.escape(str(row.get("authors") or ""))
            journal = html.escape(str(row.get("journal") or ""))
            year = html.escape(str(row.get("year") or ""))
            doi = str(row.get("doi") or "").strip()

            raw_cites = row.get("cited_by")
            if raw_cites is None or (isinstance(raw_cites, float) and pd.isna(raw_cites)) or raw_cites == "":
                cites = "0"
            else:
                try:
                    if isinstance(raw_cites, bool):
                        cites = "0"
                    else:
                        cites = str(max(0, int(float(raw_cites))))
                except (ValueError, TypeError):
                    cites = html.escape(str(raw_cites))

            doi_link = f"<a href='https://doi.org/{html.escape(doi)}' target='_blank'>doi:{html.escape(doi)}</a>" if doi else ""

            rows_html.append(f"""
            <tr class="pub-row">
                <td class="pub-title">
                    <strong>{title}</strong>
                    <div class="pub-meta">{authors} &bull; <em>{journal}</em> ({year})</div>
                </td>
                <td class="pub-doi">{doi_link}</td>
                <td class="pub-cites">{cites}</td>
            </tr>
            """)

    pubs_body = "\n".join(rows_html) if rows_html else "<tr><td colspan='3'>No publications recorded yet.</td></tr>"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{name} &mdash; Curriculum Vitae</title>
    <style>
        :root {{
            --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
            --bg-color: #fbfbfa;
            --card-bg: #ffffff;
            --text-color: #1a1a1a;
            --muted-color: #666666;
            --accent-color: #0071e3;
            --border-color: #e5e5e0;
        }}
        body {{
            font-family: var(--font-family);
            background: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            padding: 40px 20px;
            line-height: 1.5;
        }}
        .container {{
            max-width: 860px;
            margin: 0 auto;
            background: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 48px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.04);
        }}
        header {{
            border-bottom: 2px solid var(--border-color);
            padding-bottom: 24px;
            margin-bottom: 32px;
        }}
        h1 {{
            margin: 0 0 8px 0;
            font-size: 2.2rem;
            font-weight: 700;
        }}
        .tagline {{
            font-size: 1.1rem;
            color: var(--muted-color);
            margin-bottom: 12px;
            font-style: italic;
        }}
        .contacts {{
            font-size: 0.95rem;
            color: var(--muted-color);
        }}
        .contacts a {{
            color: var(--accent-color);
            text-decoration: none;
        }}
        .metrics-grid {{
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 16px;
            margin-bottom: 36px;
        }}
        .metric-card {{
            background: var(--bg-color);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
            text-align: center;
        }}
        .metric-value {{
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--accent-color);
        }}
        .metric-label {{
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted-color);
            margin-top: 4px;
        }}
        h2 {{
            font-size: 1.4rem;
            border-bottom: 1px solid var(--border-color);
            padding-bottom: 8px;
            margin-top: 32px;
            margin-bottom: 16px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
        }}
        th {{
            text-align: left;
            padding: 10px 12px;
            border-bottom: 2px solid var(--border-color);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: var(--muted-color);
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid var(--border-color);
            vertical-align: top;
        }}
        .pub-meta {{
            font-size: 0.85rem;
            color: var(--muted-color);
            margin-top: 4px;
        }}
        .pub-cites {{
            text-align: right;
            font-weight: 600;
        }}
        footer {{
            margin-top: 48px;
            text-align: center;
            font-size: 0.85rem;
            color: var(--muted-color);
        }}
        @media print {{
            body {{ background: #fff; padding: 0; }}
            .container {{ border: none; box-shadow: none; padding: 0; }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>{name}</h1>
            {f'<div class="tagline">{tagline}</div>' if tagline else ''}
            {f'<div><strong>Affiliation:</strong> {affiliation}</div>' if affiliation else ''}
            <div class="contacts">
                {" &bull; ".join([c for c in [f"Email: {email}" if email else "", f"ORCID: <a href='https://orcid.org/{orcid}'>{orcid}</a>" if orcid else "", f"Website: <a href='{website}'>{website}</a>" if website else ""] if c])}
            </div>
        </header>

        <section>
            <h2>Bibliometric Overview</h2>
            <div class="metrics-grid">
                <div class="metric-card">
                    <div class="metric-value">{m['publications']}</div>
                    <div class="metric-label">Publications</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{m['citations']}</div>
                    <div class="metric-label">Citations</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{m['h_index']}</div>
                    <div class="metric-label">h-index</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{m['journals']}</div>
                    <div class="metric-label">Journals</div>
                </div>
                <div class="metric-card">
                    <div class="metric-value">{m['oa_share']}%</div>
                    <div class="metric-label">Open Access</div>
                </div>
            </div>
        </section>

        <section>
            <h2>Publications</h2>
            <table>
                <thead>
                    <tr>
                        <th style="width: 65%;">Title & Venue</th>
                        <th style="width: 25%;">Identifier</th>
                        <th style="width: 10%; text-align: right;">Cites</th>
                    </tr>
                </thead>
                <tbody>
                    {pubs_body}
                </tbody>
            </table>
        </section>

        <footer>
            Generated by Vellum Research Workbench &bull; {time.strftime('%B %d, %Y')}
        </footer>
    </div>
</body>
</html>
"""


def render() -> None:
    """Render the standalone portfolio / CV page."""
    if st is None:
        return
    from app_pages import researchers
    email = st.session_state.get("lit_email") or None
    researchers._render_cv(email)
