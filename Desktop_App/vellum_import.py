"""
Universal Bibliographic File Importer for Vellum.
Author: Amine Zouaghi

Parses exported search results from:
  - Scopus (CSV, RIS)
  - PubMed (CSV, Text format, RIS)
  - Web of Science (CSV, TSV, RIS)
  - Dimensions, Lens, Google Scholar, Covidence, Rayyan (CSV, RIS, BibTeX)
  - Generic CSV / TSV / TXT lists of DOIs and citations

Extracts canonical metadata, normalises DOIs, eliminates duplicates, and builds
ready-to-download queues supporting large datasets (2000+ to 50000+ articles).
"""

from __future__ import annotations

import csv
import io
import re
from typing import Dict, List, Optional, Set, Tuple

DOI_PATTERN = re.compile(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+", re.I)


def norm_doi(d: Optional[str]) -> Optional[str]:
    """Clean and normalise a DOI string."""
    if not d:
        return None
    d = str(d).strip()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d, flags=re.I)
    d = re.sub(r"^doi:\s*", "", d, flags=re.I)
    d = d.lower().strip().rstrip(".;,)\"'>")
    m = DOI_PATTERN.search(d)
    if m:
        return m.group(0).lower().rstrip(".;,)\"'>")
    return d or None


def clean_text(s: Optional[str]) -> Optional[str]:
    if s is None:
        return None
    s = str(s).strip()
    s = re.sub(r"\s+", " ", s)
    return s if s else None


def extract_year(val: Optional[str]) -> Optional[int]:
    if not val:
        return None
    m = re.search(r"\b(19|20)\d{2}\b", str(val))
    return int(m.group(0)) if m else None


def parse_ris_text(content: str, default_source: str = "RIS Import") -> List[Dict]:
    """Parse RIS format lines (TY .. ER)."""
    records = []
    current: Dict = {}
    authors = []
    keywords = []

    for line in content.splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("ER  -") or line == "ER":
            if current:
                current["authors"] = authors
                current["keywords"] = keywords
                records.append(current)
            current = {}
            authors = []
            keywords = []
            continue

        match = re.match(r"^([A-Z0-9]{2})\s*-\s*(.*)$", line)
        if not match:
            continue
        tag, val = match.group(1), match.group(2).strip()
        if not val:
            continue

        if tag == "TY":
            current["type"] = val.lower()
            current["source"] = default_source
        elif tag in ("TI", "T1"):
            current["title"] = (current.get("title", "") + " " + val).strip()
        elif tag in ("AU", "A1"):
            authors.append(val)
        elif tag in ("PY", "Y1"):
            y = extract_year(val)
            if y:
                current["year"] = y
        elif tag in ("DO", "DI"):
            d = norm_doi(val)
            if d:
                current["doi"] = d
        elif tag in ("JO", "JF", "JA", "T2"):
            current["journal"] = val
        elif tag in ("AB", "N2"):
            current["abstract"] = (current.get("abstract", "") + " " + val).strip()
        elif tag in ("KW",):
            keywords.append(val)
        elif tag in ("VL",):
            current["volume"] = val
        elif tag in ("IS",):
            current["issue"] = val
        elif tag in ("SP",):
            current["pages"] = val
        elif tag in ("UR", "LK"):
            if not current.get("landing_url"):
                current["landing_url"] = val
                if not current.get("doi"):
                    m = DOI_PATTERN.search(val)
                    if m:
                        current["doi"] = norm_doi(m.group(0))

    if current:
        current["authors"] = authors
        current["keywords"] = keywords
        records.append(current)

    return records


def parse_bibtex_text(content: str, default_source: str = "BibTeX Import") -> List[Dict]:
    """Parse BibTeX entries."""
    records = []
    entries = re.split(r"@\w+\s*\{", content)
    for entry in entries[1:]:
        rec: Dict = {"source": default_source}
        # extract doi
        m_doi = re.search(r'\bdoi\s*=\s*[\{"\']([^"\'\}]+)[\}"\']', entry, re.I)
        if m_doi:
            rec["doi"] = norm_doi(m_doi.group(1))

        # extract title
        m_title = re.search(r'\btitle\s*=\s*[\{"\']([^"\'\}]+)[\}"\']', entry, re.I)
        if m_title:
            rec["title"] = clean_text(m_title.group(1))

        # extract year
        m_year = re.search(r'\byear\s*=\s*[\{"\']?(\d{4})[\}"\']?', entry, re.I)
        if m_year:
            rec["year"] = int(m_year.group(1))

        # extract authors
        m_auth = re.search(r'\bauthor\s*=\s*[\{"\']([^"\'\}]+)[\}"\']', entry, re.I)
        if m_auth:
            raw_a = m_auth.group(1)
            rec["authors"] = [a.strip() for a in raw_a.split(" and ") if a.strip()]

        # extract journal / booktitle
        m_j = re.search(r'\b(journal|booktitle)\s*=\s*[\{"\']([^"\'\}]+)[\}"\']', entry, re.I)
        if m_j:
            rec["journal"] = clean_text(m_j.group(2))

        # extract abstract
        m_ab = re.search(r'\babstract\s*=\s*[\{"\']([^"\'\}]+)[\}"\']', entry, re.I)
        if m_ab:
            rec["abstract"] = clean_text(m_ab.group(1))

        if rec.get("title") or rec.get("doi"):
            records.append(rec)

    return records


def parse_tabular_data(
    file_bytes: bytes,
    filename: str,
    delimiter: Optional[str] = None
) -> List[Dict]:
    """Parse CSV, TSV, or comma-separated exports from Scopus, PubMed, WoS, etc."""
    # Attempt multiple encodings
    text = None
    for enc in ("utf-8-sig", "utf-8", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    if not text:
        text = file_bytes.decode("utf-8", errors="ignore")

    records = []
    # Detect delimiter if not given
    if not delimiter:
        first_few_lines = "\n".join(text.splitlines()[:5])
        if "\t" in first_few_lines:
            delimiter = "\t"
        elif ";" in first_few_lines and "," not in first_few_lines:
            delimiter = ";"
        else:
            delimiter = ","

    f = io.StringIO(text)
    reader = csv.DictReader(f, delimiter=delimiter)
    if not reader.fieldnames:
        return []

    # Map column names case-insensitively
    headers_lower = {h.strip().lower(): h for h in reader.fieldnames if h}

    def get_val(row: Dict, *candidates: str) -> Optional[str]:
        for c in candidates:
            cl = c.lower()
            if cl in headers_lower:
                v = row.get(headers_lower[cl])
                if v and str(v).strip():
                    return str(v).strip()
        # Substring search as fallback
        for cl, orig in headers_lower.items():
            for c in candidates:
                if c.lower() in cl:
                    v = row.get(orig)
                    if v and str(v).strip():
                        return str(v).strip()
        return None

    # Detect known source profile
    src_label = "CSV Import"
    if "pubmed id" in headers_lower or "pmid" in headers_lower:
        src_label = "PubMed (CSV)"
    elif "art. no." in headers_lower or "eid" in headers_lower or "authors with affiliations" in headers_lower:
        src_label = "Scopus (CSV)"
    elif "times cited, all databases" in headers_lower or "ut (unique wos id)" in headers_lower:
        src_label = "Web of Science (CSV)"

    for row in reader:
        rec: Dict = {"source": src_label}

        # 1. DOI
        raw_doi = get_val(row, "doi", "digital object identifier", "article doi", "document doi")
        if not raw_doi:
            # Check link or url
            raw_url = get_val(row, "link", "url", "electronic link")
            if raw_url:
                m = DOI_PATTERN.search(raw_url)
                if m:
                    raw_doi = m.group(0)
        rec["doi"] = norm_doi(raw_doi)

        # 2. Title
        title = get_val(row, "title", "article title", "document title", "publication title")
        rec["title"] = clean_text(title)

        # 3. Year
        year_str = get_val(row, "year", "publication year", "pub year", "py", "date", "createdate")
        rec["year"] = extract_year(year_str)

        # 4. Authors
        auth_str = get_val(row, "authors", "author", "author(s)", "first author")
        if auth_str:
            # Split common formats (semicolons, commas, or 'and')
            if ";" in auth_str:
                auths = [a.strip() for a in auth_str.split(";") if a.strip()]
            elif " and " in auth_str:
                auths = [a.strip() for a in auth_str.split(" and ") if a.strip()]
            else:
                auths = [auth_str.strip()]
            rec["authors"] = auths
        else:
            rec["authors"] = []

        # 5. Journal / Source title
        j_str = get_val(row, "source title", "journal", "journal/book", "publication title", "venue", "booktitle")
        rec["journal"] = clean_text(j_str)

        # 6. Abstract
        ab_str = get_val(row, "abstract", "abstract text", "summary")
        rec["abstract"] = clean_text(ab_str)

        # 7. Citations count
        cit_str = get_val(row, "cited by", "citations", "times cited", "cited by count")
        if cit_str:
            try:
                rec["cited_by"] = int(re.sub(r"[^\d]", "", cit_str))
            except ValueError:
                rec["cited_by"] = None

        # 8. Identifiers: PMID, PMCID, arXiv
        pmid = get_val(row, "pmid", "pubmed id")
        if pmid:
            rec["pmid"] = re.sub(r"[^\d]", "", pmid)
        pmcid = get_val(row, "pmcid", "pmc id")
        if pmcid:
            rec["pmcid"] = pmcid

        if rec.get("title") or rec.get("doi"):
            records.append(rec)

    return records


def parse_raw_text_list(content: str) -> List[Dict]:
    """Parse plain text containing a list of DOIs, URLs, or citations."""
    records = []
    lines = content.splitlines()
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        m = DOI_PATTERN.search(line)
        if m:
            d = norm_doi(m.group(0))
            rem = line.replace(m.group(0), "").strip(" -–—:;,|\t")
            records.append({
                "doi": d,
                "title": rem if len(rem) > 10 else "",
                "source": "Text List",
                "authors": [],
            })
        elif line.startswith("http://") or line.startswith("https://"):
            records.append({
                "doi": None,
                "title": line,
                "pdf_url": line if line.lower().endswith(".pdf") else None,
                "landing_url": line,
                "source": "URL List",
                "authors": [],
            })
    return records


def universal_import_file(
    file_bytes: bytes,
    filename: str
) -> Tuple[List[Dict], Dict[str, int]]:
    """
    Main entry point: imports records from any supported file format.
    Returns (records, stats).
    """
    fn_lower = filename.lower()
    records: List[Dict] = []

    # Detect format by extension or content
    if fn_lower.endswith(".ris"):
        text = file_bytes.decode("utf-8", errors="ignore")
        records = parse_ris_text(text, default_source=f"RIS ({filename})")
    elif fn_lower.endswith(".bib") or fn_lower.endswith(".bibtex"):
        text = file_bytes.decode("utf-8", errors="ignore")
        records = parse_bibtex_text(text, default_source=f"BibTeX ({filename})")
    elif fn_lower.endswith(".tsv"):
        records = parse_tabular_data(file_bytes, filename, delimiter="\t")
    elif fn_lower.endswith(".csv"):
        records = parse_tabular_data(file_bytes, filename, delimiter=",")
    else:
        # Check if text looks like RIS
        sample = file_bytes[:1000].decode("utf-8", errors="ignore")
        if re.search(r"^[A-Z0-9]{2}\s*-\s*", sample, re.M):
            records = parse_ris_text(file_bytes.decode("utf-8", errors="ignore"), default_source=f"RIS ({filename})")
        elif "@" in sample and "{" in sample:
            records = parse_bibtex_text(file_bytes.decode("utf-8", errors="ignore"), default_source=f"BibTeX ({filename})")
        elif "\t" in sample or "," in sample:
            records = parse_tabular_data(file_bytes, filename)
        else:
            records = parse_raw_text_list(file_bytes.decode("utf-8", errors="ignore"))

    # Convert records into canonical format
    canonical_list = []
    seen_dois: Set[str] = set()
    seen_titles: Set[str] = set()
    dup_count = 0

    for r in records:
        d = norm_doi(r.get("doi"))
        t = clean_text(r.get("title"))
        t_key = re.sub(r"[^a-z0-9]", "", (t or "").lower())

        is_dup = False
        if d:
            if d in seen_dois:
                is_dup = True
            else:
                seen_dois.add(d)

        if not is_dup and len(t_key) > 15:
            if t_key in seen_titles:
                is_dup = True
            else:
                seen_titles.add(t_key)

        if is_dup:
            dup_count += 1
            continue

        canonical: Dict = {
            "doi": d,
            "title": t or "",
            "authors": r.get("authors") or [],
            "author_count": len(r.get("authors") or []),
            "year": r.get("year"),
            "publication_date": str(r.get("year")) if r.get("year") else None,
            "epub_date": None,
            "journal": r.get("journal"),
            "abstract": r.get("abstract"),
            "keywords": r.get("keywords") or [],
            "type": r.get("type", "journal-article"),
            "language": r.get("language", "English"),
            "issn": [],
            "volume": r.get("volume"),
            "issue": r.get("issue"),
            "pages": r.get("pages"),
            "cited_by": r.get("cited_by", 0),
            "is_oa": r.get("is_oa", False),
            "oa_status": r.get("oa_status"),
            "pdf_url": r.get("pdf_url"),
            "landing_url": r.get("landing_url") or (f"https://doi.org/{d}" if d else None),
            "pmid": r.get("pmid"),
            "pmcid": r.get("pmcid"),
            "arxiv_id": r.get("arxiv_id"),
            "openalex_id": None,
            "source": r.get("source", "File Import"),
            "sources": [r.get("source", "File Import")],
            "source_count": 1,
            "match_method": "",
            "screen_status": "",
            "screen_reason": "",
            "pdf_ready": bool(r.get("pdf_url")),
            "notes": "",
        }
        canonical_list.append(canonical)

    stats = {
        "total_parsed": len(records),
        "duplicates_removed": dup_count,
        "unique_records": len(canonical_list),
        "with_doi": len([c for c in canonical_list if c["doi"]]),
    }
    return canonical_list, stats
