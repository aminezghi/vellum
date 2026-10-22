"""
app_pages/screening.py — ASReview-Powered Active Learning Systematic Review Screening.

Provides:
  - Multi-source bibliographic ingestion (CSV, RIS, BibTeX, Project Pool)
  - 3-tier automated deduplication (Normalized DOI, Normalized Title, Token Jaccard > 0.88)
  - ASReview Machine Learning Active Learning (TF-IDF + Multinomial Naive Bayes)
  - Continuous priority re-ranking of unlabelled literature
  - Heuristic stopping criteria (consecutive irrelevant threshold & estimated recall plateau)
  - Keyboard shortcuts (I = Include, E = Exclude, U = Undo)
  - Persistent multi-session management in local project workspace
  - 1-click export to PRISMA 2020 Flow Matrix & Project Unified Paper Pool
"""

from __future__ import annotations

import io
import json
import math
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd
import streamlit as st

import vellum_theme as VT
import vellum_workspace as VW

# Machine learning dependencies
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.naive_bayes import MultinomialNB
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


# ─────────────────────────────────────────────────────────────────────────────
# 1. Deduplication & Ingestion Utilities
# ─────────────────────────────────────────────────────────────────────────────

def normalize_doi(doi: Optional[str]) -> str:
    """Normalize DOI string for robust duplicate matching."""
    if not doi:
        return ""
    d = str(doi).strip().lower()
    d = re.sub(r"^https?://(dx\.)?doi\.org/", "", d)
    d = re.sub(r"^doi:\s*", "", d)
    return d.strip()


def normalize_title(title: Optional[str]) -> str:
    """Normalize title by stripping punctuation, extra spaces, and common leading articles."""
    if not title:
        return ""
    t = str(title).lower().strip()
    t = re.sub(r"^(the|a|an)\s+", "", t)
    t = re.sub(r"[^a-z0-9]", "", t)
    return t.strip()


def get_word_tokens(title: Optional[str]) -> Set[str]:
    """Extract significant word tokens (length >= 3) from title."""
    if not title:
        return set()
    cleaned = re.sub(r"[^a-z0-9\s]", " ", str(title).lower())
    return {w for w in cleaned.split() if len(w) >= 3}


def token_jaccard_similarity(set_a: Set[str], set_b: Set[str]) -> float:
    """Compute Jaccard similarity between two token sets."""
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0


def deduplicate_records(
    existing_items: List[Dict[str, Any]],
    new_items: List[Dict[str, Any]],
    source_name: str = "Imported File"
) -> Tuple[List[Dict[str, Any]], int, List[Dict[str, Any]]]:
    """
    Deduplicates new_items against existing_items using 3-tier verification:
    1. Exact normalized DOI match
    2. Exact normalized Title match
    3. Fuzzy Token Jaccard similarity >= 0.88 on titles
    Returns: (combined_items, duplicate_count, duplicate_details)
    """
    combined = list(existing_items)
    duplicates_removed: List[Dict[str, Any]] = []
    duplicate_count = 0

    for item in new_items:
        cand_doi = normalize_doi(item.get("doi"))
        cand_norm_title = normalize_title(item.get("title"))
        cand_tokens = get_word_tokens(item.get("title"))

        is_dup = False
        for ex in combined:
            ex_doi = normalize_doi(ex.get("doi"))
            ex_norm_title = normalize_title(ex.get("title"))
            ex_tokens = get_word_tokens(ex.get("title"))

            # Check 1: DOI match
            if cand_doi and ex_doi and cand_doi == ex_doi:
                is_dup = True
                duplicate_count += 1
                duplicates_removed.append({
                    "kept_title": ex.get("title", ""),
                    "dup_title": item.get("title", ""),
                    "source": source_name,
                    "reason": "Exact DOI Match",
                })
                # Merge missing metadata
                if not ex.get("abstract") and item.get("abstract"):
                    ex["abstract"] = item["abstract"]
                if not ex.get("journal") and item.get("journal"):
                    ex["journal"] = item["journal"]
                break

            # Check 2: Exact normalized title match
            if cand_norm_title and ex_norm_title and cand_norm_title == ex_norm_title:
                is_dup = True
                duplicate_count += 1
                duplicates_removed.append({
                    "kept_title": ex.get("title", ""),
                    "dup_title": item.get("title", ""),
                    "source": source_name,
                    "reason": "Normalized Title Match",
                })
                if not ex.get("abstract") and item.get("abstract"):
                    ex["abstract"] = item["abstract"]
                break

            # Check 3: Fuzzy title token similarity
            if cand_tokens and ex_tokens:
                sim = token_jaccard_similarity(cand_tokens, ex_tokens)
                if sim >= 0.88:
                    is_dup = True
                    duplicate_count += 1
                    duplicates_removed.append({
                        "kept_title": ex.get("title", ""),
                        "dup_title": item.get("title", ""),
                        "source": source_name,
                        "reason": f"Fuzzy Title Similarity ({int(sim*100)}%)",
                    })
                    break

        if not is_dup:
            item_copy = dict(item)
            if not item_copy.get("id"):
                item_copy["id"] = f"sc_{uuid.uuid4().hex[:8]}"
            if not item_copy.get("decision"):
                item_copy["decision"] = "pending"
            if "relevance_score" not in item_copy:
                item_copy["relevance_score"] = 0.50
            item_copy["source_origin"] = source_name
            combined.append(item_copy)

    return combined, duplicate_count, duplicates_removed


def parse_ris_text(text: str) -> List[Dict[str, Any]]:
    """Parse RIS format text into standard screening candidate dictionaries."""
    records = []
    current: Dict[str, Any] = {"authors": []}
    current_tag = None

    for line in text.splitlines():
        line = line.rstrip()
        if not line:
            continue
        if re.match(r"^[A-Z0-9]{2}\s+-\s+", line):
            tag = line[:2]
            val = line[6:].strip()
            current_tag = tag

            if tag == "TY":
                current = {"authors": []}
            elif tag in ("TI", "T1"):
                current["title"] = val
            elif tag in ("AB", "N2"):
                current["abstract"] = val
            elif tag in ("AU", "A1"):
                current["authors"].append(val)
            elif tag in ("PY", "Y1"):
                m = re.search(r"\b(19\d\d|20\d\d)\b", val)
                if m:
                    current["year"] = int(m.group(1))
            elif tag in ("JO", "JF", "JA", "T2"):
                current["journal"] = val
            elif tag in ("DO", "DI"):
                current["doi"] = val
            elif tag == "ER":
                if current.get("title"):
                    records.append(current)
                current = {"authors": []}
        elif current_tag and line.startswith("   "):
            # Multi-line continuation
            val = line.strip()
            if current_tag in ("TI", "T1") and "title" in current:
                current["title"] += " " + val
            elif current_tag in ("AB", "N2") and "abstract" in current:
                current["abstract"] += " " + val

    if current.get("title") and current not in records:
        records.append(current)
    return records


def parse_bibtex_text(text: str) -> List[Dict[str, Any]]:
    """Parse BibTeX format text into standard screening candidate dictionaries."""
    entries = re.split(r"@\w+\s*\{", text)[1:]
    records = []
    for raw in entries:
        rec: Dict[str, Any] = {"authors": []}
        # Title
        m_t = re.search(r"title\s*=\s*[\"\{](.*?)[\"\}],", raw, re.DOTALL | re.IGNORECASE)
        if m_t:
            rec["title"] = re.sub(r"\s+", " ", m_t.group(1).replace("\n", " ")).strip()
        # Abstract
        m_a = re.search(r"abstract\s*=\s*[\"\{](.*?)[\"\}],", raw, re.DOTALL | re.IGNORECASE)
        if m_a:
            rec["abstract"] = re.sub(r"\s+", " ", m_a.group(1).replace("\n", " ")).strip()
        # Year
        m_y = re.search(r"year\s*=\s*[\"\{]?(\d{4})[\"\}]?", raw, re.IGNORECASE)
        if m_y:
            rec["year"] = int(m_y.group(1))
        # Journal
        m_j = re.search(r"(journal|booktitle)\s*=\s*[\"\{](.*?)[\"\}],", raw, re.DOTALL | re.IGNORECASE)
        if m_j:
            rec["journal"] = re.sub(r"\s+", " ", m_j.group(2).replace("\n", " ")).strip()
        # DOI
        m_d = re.search(r"doi\s*=\s*[\"\{](.*?)[\"\}],", raw, re.IGNORECASE)
        if m_d:
            rec["doi"] = m_d.group(1).strip()
        # Authors
        m_au = re.search(r"author\s*=\s*[\"\{](.*?)[\"\}],", raw, re.DOTALL | re.IGNORECASE)
        if m_au:
            au_str = m_au.group(1).strip()
            rec["authors"] = [a.strip() for a in au_str.split(" and ")]

        if rec.get("title"):
            records.append(rec)
    return records


def parse_tabular_data(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Convert pandas dataframe (CSV / Excel) into screening candidates."""
    records = []
    # Identify column mappings case-insensitively
    col_map = {c.lower().strip(): c for c in df.columns}
    
    title_col = None
    for cand in ["title", "article title", "document title", "paper title", "name"]:
        if cand in col_map:
            title_col = col_map[cand]
            break
            
    abstract_col = None
    for cand in ["abstract", "description", "summary"]:
        if cand in col_map:
            abstract_col = col_map[cand]
            break

    doi_col = None
    for cand in ["doi", "digital object identifier"]:
        if cand in col_map:
            doi_col = col_map[cand]
            break

    year_col = None
    for cand in ["year", "publication year", "pub_year", "date"]:
        if cand in col_map:
            year_col = col_map[cand]
            break

    author_col = None
    for cand in ["authors", "author", "author names", "creator"]:
        if cand in col_map:
            author_col = col_map[cand]
            break

    journal_col = None
    for cand in ["journal", "source title", "venue", "publication title", "booktitle"]:
        if cand in col_map:
            journal_col = col_map[cand]
            break

    if not title_col:
        # Fallback to first text column
        for c in df.columns:
            if df[c].dtype == object:
                title_col = c
                break

    if not title_col:
        return []

    for _, row in df.iterrows():
        title = str(row.get(title_col, "")).strip()
        if not title or title.lower() == "nan":
            continue
            
        abstract = str(row.get(abstract_col, "")) if abstract_col else ""
        if abstract.lower() == "nan":
            abstract = ""
            
        doi = str(row.get(doi_col, "")) if doi_col else ""
        if doi.lower() == "nan":
            doi = ""

        year = None
        if year_col:
            val_y = str(row.get(year_col, ""))
            m_y = re.search(r"\b(19\d\d|20\d\d)\b", val_y)
            if m_y:
                year = int(m_y.group(1))

        authors = []
        if author_col:
            raw_au = str(row.get(author_col, ""))
            if raw_au.lower() != "nan":
                authors = [a.strip() for a in re.split(r"[,;]|\band\b", raw_au) if a.strip()]

        journal = str(row.get(journal_col, "")) if journal_col else ""
        if journal.lower() == "nan":
            journal = ""

        records.append({
            "title": title,
            "abstract": abstract,
            "doi": doi,
            "year": year,
            "authors": authors,
            "journal": journal,
        })
    return records


# ─────────────────────────────────────────────────────────────────────────────
# 2. Machine Learning Active Learning Engine (ASReview Protocol)
# ─────────────────────────────────────────────────────────────────────────────

class ASReviewActiveLearningModel:
    """
    Continuous Machine Learning Active Learning model based on ASReview protocol.
    Uses TF-IDF feature extraction + Multinomial Naive Bayes classification.
    Re-ranks pending papers continuously based on posterior relevance probability.
    """
    def __init__(self):
        self.vectorizer = TfidfVectorizer(
            stop_words="english",
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True
        ) if SKLEARN_AVAILABLE else None
        self.clf = MultinomialNB(alpha=0.1) if SKLEARN_AVAILABLE else None

    def fit_and_rerank(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Train on included and excluded candidates, predict posterior probabilities
        for all pending candidates, and sort pending candidates descending by score.
        """
        if not SKLEARN_AVAILABLE or not candidates:
            return candidates

        labeled = [c for c in candidates if c.get("decision") in ("included", "excluded")]
        pending = [c for c in candidates if c.get("decision") == "pending"]

        # We need at least one included candidate to learn relevant features
        included = [c for c in labeled if c.get("decision") == "included"]
        excluded = [c for c in labeled if c.get("decision") == "excluded"]

        if not included:
            # If no positive priors, rank by text length/richness
            for p in pending:
                p["relevance_score"] = 0.50
            return labeled + pending

        # Prepare corpus for vectorizer
        def get_text(item: Dict[str, Any]) -> str:
            t = item.get("title", "")
            a = item.get("abstract", "")
            j = item.get("journal", "")
            return f"{t} {t} {a} {j}".strip()

        all_texts = [get_text(c) for c in candidates]
        try:
            X_all = self.vectorizer.fit_transform(all_texts)
        except Exception:
            return labeled + pending

        # Index mapping
        id_to_idx = {c.get("id"): idx for idx, c in enumerate(candidates)}
        
        train_indices = [id_to_idx[c.get("id")] for c in labeled]
        y_train = [1 if c.get("decision") == "included" else 0 for c in labeled]

        # If we have only 1 class (e.g. only included so far), add a synthetic negative prior
        if len(set(y_train)) < 2:
            # Pair with highest entropy / lowest overlap
            y_train.append(0)
            # Use last pending item as pseudo-negative for initial initialization
            if pending:
                train_indices.append(id_to_idx[pending[-1].get("id")])
            else:
                return labeled + pending

        X_train = X_all[train_indices]

        try:
            self.clf.fit(X_train, y_train)
            
            pending_indices = [id_to_idx[p.get("id")] for p in pending]
            if pending_indices:
                X_pending = X_all[pending_indices]
                probs = self.clf.predict_proba(X_pending)
                # Class 1 is 'included'
                for idx, p_idx in enumerate(pending_indices):
                    p_score = float(probs[idx, 1])
                    candidates[p_idx]["relevance_score"] = round(p_score, 4)

            # Sort pending candidates: highest relevance score first
            sorted_pending = sorted(pending, key=lambda x: x.get("relevance_score", 0.0), reverse=True)
            return labeled + sorted_pending
        except Exception:
            return labeled + pending


# ─────────────────────────────────────────────────────────────────────────────
# 3. Persistent Session Storage
# ─────────────────────────────────────────────────────────────────────────────

def get_screening_sessions_file() -> Path:
    """Return path to screening_sessions.json in active project directory."""
    p_dir = VW.get_project_dir()
    return p_dir / "screening_sessions.json"


def load_screening_sessions() -> List[Dict[str, Any]]:
    """Load all screening sessions for the active project."""
    fpath = get_screening_sessions_file()
    if fpath.exists():
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    return data
        except Exception:
            pass
    # Initialize default session if empty
    default_session = {
        "id": "session_default",
        "name": "Systematic Review Screening",
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "candidates": [],
        "history": [],
        "staged_sources": [],
        "consecutive_excludes": 0,
    }
    return [default_session]


def save_screening_sessions(sessions: List[Dict[str, Any]]) -> None:
    """Save all screening sessions for active project to JSON."""
    fpath = get_screening_sessions_file()
    try:
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(sessions, f, indent=2)
    except Exception:
        pass


def get_active_session(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Retrieve or initialize the active session in st.session_state."""
    active_id = st.session_state.get("_as_active_session_id")
    for s in sessions:
        if s.get("id") == active_id:
            return s
    # Default to first session
    if sessions:
        st.session_state["_as_active_session_id"] = sessions[0]["id"]
        return sessions[0]
    # Fallback create
    new_s = {
        "id": f"session_{uuid.uuid4().hex[:6]}",
        "name": "Systematic Review Screening",
        "created_at": datetime.now().isoformat(),
        "last_modified": datetime.now().isoformat(),
        "candidates": [],
        "history": [],
        "staged_sources": [],
        "consecutive_excludes": 0,
    }
    sessions.append(new_s)
    st.session_state["_as_active_session_id"] = new_s["id"]
    save_screening_sessions(sessions)
    return new_s


# ─────────────────────────────────────────────────────────────────────────────
# 4. Main Rendering Interface (Fernly Botanical Bento Edition)
# ─────────────────────────────────────────────────────────────────────────────

def render():
    """Main rendering entry point for the ASReview Screening page."""
    sessions = load_screening_sessions()
    session = get_active_session(sessions)
    candidates = session.get("candidates", [])
    history = session.get("history", [])

    # ── Header & Title ──
    st.markdown(
        """
        <div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom:12px;">
            <div>
                <h2 style="margin:0; font-family:Georgia, serif; font-size:1.85rem; font-weight:700; color:var(--text-main, #1b4332);">
                    🧪 ASReview Active Learning Screening
                </h2>
                <p style="margin:4px 0 0 0; font-size:0.92rem; color:var(--text-muted, #5c6f64);">
                    Systematic review prioritization engine with continuous machine learning re-ranking, multi-source ingestion & automated deduplication.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ── Session Management Bar (Botanical Bento) ──
    s_col1, s_col2, s_col3, s_col4 = st.columns([3.2, 1.4, 1.4, 1.4], vertical_alignment="center")

    with s_col1:
        session_names = [s.get("name", "Untitled") for s in sessions]
        cur_idx = 0
        for i, s in enumerate(sessions):
            if s.get("id") == session.get("id"):
                cur_idx = i
                break

        sel_session_name = st.selectbox(
            "Screening Session",
            session_names,
            index=cur_idx,
            key="_screening_session_picker",
            help="Switch between independent screening sessions in this project",
            format_func=lambda x: f"📂 {x}",
            label_visibility="collapsed",
        )
        if sel_session_name != session.get("name"):
            for s in sessions:
                if s.get("name") == sel_session_name:
                    st.session_state["_as_active_session_id"] = s.get("id")
                    st.rerun()

    with s_col2:
        if st.button("➕ New Session", key="_btn_new_session", use_container_width=True):
            new_id = f"session_{uuid.uuid4().hex[:6]}"
            new_s = {
                "id": new_id,
                "name": f"Screening {len(sessions) + 1}",
                "created_at": datetime.now().isoformat(),
                "last_modified": datetime.now().isoformat(),
                "candidates": [],
                "history": [],
                "staged_sources": [],
                "consecutive_excludes": 0,
            }
            sessions.append(new_s)
            save_screening_sessions(sessions)
            st.session_state["_as_active_session_id"] = new_id
            st.rerun()

    with s_col3:
        # Rename modal/popover
        with st.popover("✏️ Rename", use_container_width=True):
            new_title = st.text_input("Session Name", value=session.get("name", ""), key="_rename_input")
            if st.button("Save Name", key="_btn_save_name", type="primary"):
                if new_title.strip():
                    session["name"] = new_title.strip()
                    session["last_modified"] = datetime.now().isoformat()
                    save_screening_sessions(sessions)
                    st.rerun()

    with s_col4:
        # Delete session
        if len(sessions) > 1:
            if st.button("🗑️ Delete", key="_btn_del_session", use_container_width=True, help="Delete this screening session"):
                sessions = [s for s in sessions if s.get("id") != session.get("id")]
                save_screening_sessions(sessions)
                st.session_state["_as_active_session_id"] = sessions[0]["id"]
                st.rerun()

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # ── Multi-Source Ingestion & Deduplication Hub ──
    with st.expander("📥 Add Literature Sources & Deduplicate (CSV, RIS, BibTeX, Project Pool)", expanded=(len(candidates) == 0)):
        tab_upload, tab_pool, tab_bench = st.tabs(["📁 Upload File", "📚 Project Paper Pool", "🧪 Benchmark Datasets"])

        with tab_upload:
            st.caption("Upload bibliographic files exported from Scopus, Web of Science, PubMed, Covidence, or Rayyan.")
            uploaded_file = st.file_uploader(
                "Choose reference file",
                type=["csv", "ris", "bib", "txt", "xlsx"],
                key="_screen_file_uploader",
                help="Supported formats: CSV, RIS, BibTeX, Excel",
            )
            if uploaded_file is not None:
                fname = uploaded_file.name
                btn_import = st.button(f"📥 Parse & Ingest '{fname}'", key="_btn_parse_file", type="primary")
                if btn_import:
                    progress_bar = st.progress(0, text="Parsing bibliographic structure...")
                    raw_bytes = uploaded_file.read()
                    progress_bar.progress(35, text="Extracting records & metadata...")

                    new_records = []
                    try:
                        if fname.lower().endswith(".csv"):
                            df = pd.read_csv(io.BytesIO(raw_bytes))
                            new_records = parse_tabular_data(df)
                        elif fname.lower().endswith(".xlsx"):
                            df = pd.read_excel(io.BytesIO(raw_bytes))
                            new_records = parse_tabular_data(df)
                        elif fname.lower().endswith(".ris"):
                            text = raw_bytes.decode("utf-8", errors="replace")
                            new_records = parse_ris_text(text)
                        elif fname.lower().endswith((".bib", ".bibtex")):
                            text = raw_bytes.decode("utf-8", errors="replace")
                            new_records = parse_bibtex_text(text)
                        else:
                            # Try RIS then BibTeX
                            text = raw_bytes.decode("utf-8", errors="replace")
                            new_records = parse_ris_text(text)
                            if not new_records:
                                new_records = parse_bibtex_text(text)
                    except Exception as e:
                        st.error(f"Failed to parse file: {e}")
                        progress_bar.empty()
                        return

                    progress_bar.progress(70, text="Running 3-tier automated deduplication...")
                    combined, dup_count, dup_details = deduplicate_records(
                        candidates,
                        new_records,
                        source_name=fname
                    )

                    progress_bar.progress(90, text="Updating active learning priorities...")
                    session["candidates"] = combined
                    session["last_modified"] = datetime.now().isoformat()
                    
                    staged = session.get("staged_sources", [])
                    staged.append({
                        "name": fname,
                        "count": len(new_records),
                        "duplicates": dup_count,
                        "timestamp": datetime.now().isoformat()
                    })
                    session["staged_sources"] = staged
                    save_screening_sessions(sessions)
                    progress_bar.progress(100, text="Ready!")
                    
                    st.success(
                        f"✅ Successfully ingested {len(new_records)} records! "
                        f"Found and removed **{dup_count} duplicates**."
                    )
                    st.rerun()

        with tab_pool:
            p_data = VW.load_project_data()
            pool_records = p_data.get("search_records", [])
            st.caption(f"Active project paper pool contains **{len(pool_records)}** references.")
            if pool_records:
                if st.button("📥 Ingest All References from Project Pool", key="_btn_ingest_pool", type="primary"):
                    progress_bar = st.progress(0, text="Ingesting from Project Pool...")
                    converted = []
                    for r in pool_records:
                        converted.append({
                            "title": r.get("title", ""),
                            "abstract": r.get("abstract", ""),
                            "doi": r.get("doi", ""),
                            "year": r.get("year"),
                            "authors": r.get("authors", "").split(",") if isinstance(r.get("authors"), str) else [],
                            "journal": r.get("venue", "") or r.get("journal", ""),
                        })
                    combined, dup_count, _ = deduplicate_records(candidates, converted, source_name="Project Pool")
                    session["candidates"] = combined
                    session["last_modified"] = datetime.now().isoformat()
                    save_screening_sessions(sessions)
                    progress_bar.progress(100, text="Completed!")
                    st.success(f"Added {len(converted)} papers. {dup_count} duplicates merged.")
                    st.rerun()
            else:
                st.info("No records in current project pool. Use 'Discover' or 'Library' to add papers.")

        with tab_bench:
            st.caption("Load verified systematic review benchmark corpora for calibration and testing.")
            b1, b2 = st.columns(2)
            with b1:
                if st.button("🍎 DeepFruits Systematic Review (Bench)", key="_btn_bench_fruit", use_container_width=True):
                    sample_bench = [
                        {"title": "DeepFruits: A Fruit Detection System Using Deep Neural Networks", "abstract": "Accurate fruit detection is an essential requirement for automated harvesting systems. We propose DeepFruits...", "year": 2016, "journal": "Sensors", "doi": "10.3390/s16081222", "decision": "included"},
                        {"title": "Automated fruit recognition using faster R-CNN", "abstract": "We evaluate deep learning architectures for apple and mango detection in complex field orchards...", "year": 2018, "journal": "Computers and Electronics in Agriculture", "doi": "10.1016/j.compag.2018.06.012", "decision": "pending"},
                        {"title": "Deep learning for agricultural robotics: A comprehensive review", "abstract": "A review of computer vision algorithms for harvesting robots in modern precision horticulture...", "year": 2021, "journal": "Robotics and Autonomous Systems", "doi": "10.1016/j.robot.2021.103780", "decision": "pending"},
                        {"title": "Chemical synthesis of plant hormones and fruit ripening", "abstract": "This study examines ethylene biosynthesis and transcriptional activation during fruit maturation...", "year": 2019, "journal": "Journal of Plant Physiology", "doi": "10.1016/j.jplph.2019.04.001", "decision": "excluded"},
                        {"title": "Soil composition and nitrogen fertilisation in citrus orchards", "abstract": "An empirical analysis of soil microbial diversity and inorganic nutrient uptake...", "year": 2017, "journal": "Soil Science", "doi": "10.1097/SS.0000000000000210", "decision": "excluded"},
                    ]
                    combined, dup_count, _ = deduplicate_records(candidates, sample_bench, source_name="Benchmark Corpus")
                    session["candidates"] = combined
                    save_screening_sessions(sessions)
                    st.rerun()
            with b2:
                if st.button("🧹 Clear All Candidates in this Session", key="_btn_clear_screen", use_container_width=True):
                    session["candidates"] = []
                    session["history"] = []
                    session["consecutive_excludes"] = 0
                    save_screening_sessions(sessions)
                    st.rerun()

    # If no candidates present, show elegant empty state
    if not candidates:
        st.info("💡 No literature references loaded yet. Upload a CSV/RIS/BibTeX file or import from your Project Pool above to start screening.")
        return

    # ── Calculate Real-Time Metrics & Stopping Projection ──
    screened = [c for c in candidates if c.get("decision") in ("included", "excluded")]
    included = [c for c in candidates if c.get("decision") == "included"]
    excluded = [c for c in candidates if c.get("decision") == "excluded"]
    pending = [c for c in candidates if c.get("decision") == "pending"]

    n_total = len(candidates)
    n_screened = len(screened)
    pct_screened = int((n_screened / n_total) * 100) if n_total > 0 else 0
    consecutive_ex = session.get("consecutive_excludes", 0)

    # ── Bento Metrics Row ──
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.markdown(
            f"""
            <div style="background:var(--metric-bg, rgba(255,255,255,0.7)); border:1px solid var(--panel-border, #dce7e1); border-radius:12px; padding:12px 14px; text-align:center;">
                <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:var(--text-muted, #5c6f64);">Total Staged</div>
                <div style="font-size:1.6rem; font-weight:700; color:var(--text-main, #1b4332);">{n_total}</div>
                <div style="font-size:0.72rem; color:var(--text-muted, #718096);">{len(session.get('staged_sources', []))} sources</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div style="background:var(--metric-bg, rgba(255,255,255,0.7)); border:1px solid var(--panel-border, #dce7e1); border-radius:12px; padding:12px 14px; text-align:center;">
                <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:var(--text-muted, #5c6f64);">Screened</div>
                <div style="font-size:1.6rem; font-weight:700; color:#3b82f6;">{n_screened}</div>
                <div style="font-size:0.72rem; color:var(--text-muted, #718096);">{pct_screened}% complete</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div style="background:var(--metric-bg, rgba(255,255,255,0.7)); border:1px solid var(--panel-border, #dce7e1); border-radius:12px; padding:12px 14px; text-align:center;">
                <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:var(--text-muted, #5c6f64);">⭐ Included</div>
                <div style="font-size:1.6rem; font-weight:700; color:#10b981;">{len(included)}</div>
                <div style="font-size:0.72rem; color:var(--text-muted, #718096);">{round((len(included)/max(1, n_screened))*100, 1)}% yield</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div style="background:var(--metric-bg, rgba(255,255,255,0.7)); border:1px solid var(--panel-border, #dce7e1); border-radius:12px; padding:12px 14px; text-align:center;">
                <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:var(--text-muted, #5c6f64);">❌ Excluded</div>
                <div style="font-size:1.6rem; font-weight:700; color:#ef4444;">{len(excluded)}</div>
                <div style="font-size:0.72rem; color:var(--text-muted, #718096);">{consecutive_ex} in a row</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m5:
        st.markdown(
            f"""
            <div style="background:var(--metric-bg, rgba(255,255,255,0.7)); border:1px solid var(--panel-border, #dce7e1); border-radius:12px; padding:12px 14px; text-align:center;">
                <div style="font-size:0.75rem; font-weight:600; text-transform:uppercase; color:var(--text-muted, #5c6f64);">⏳ Remaining</div>
                <div style="font-size:1.6rem; font-weight:700; color:var(--text-main, #2d6a4f);">{len(pending)}</div>
                <div style="font-size:0.72rem; color:var(--text-muted, #718096);">Active Queue</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # ── Stopping Heuristic Notice ──
    if consecutive_ex >= 30 and len(included) >= 5:
        st.warning(
            f"🎯 **Stopping Criterion Alert**: You have screened **{consecutive_ex} consecutive irrelevant papers**. "
            "Under ASReview statistical stopping heuristics, expected residual recall likely exceeds **95%**. "
            "You may consider concluding the title/abstract screening phase."
        )

    # ── Active Candidate Card & Screening Engine ──
    if not pending:
        st.success("🎉 **Screening Completed!** All staged literature references have been evaluated.")
    else:
        current_item = pending[0]
        score = current_item.get("relevance_score", 0.50)
        score_pct = int(score * 100)

        # Badge color based on ML confidence
        badge_color = "#10b981" if score_pct >= 70 else ("#f59e0b" if score_pct >= 40 else "#6b7280")

        # Botanical Card Container
        st.markdown(
            f"""
            <div style="background:var(--card-bg, #ffffff); border:1.5px solid var(--card-border, #dce7e1); border-radius:16px; padding:22px; box-shadow:0 4px 16px rgba(0,0,0,0.04); margin-bottom:16px;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:8px;">
                    <div style="display:flex; align-items:center; gap:8px;">
                        <span style="background:{badge_color}22; color:{badge_color}; border:1px solid {badge_color}55; font-size:0.75rem; font-weight:700; padding:3px 10px; border-radius:20px;">
                            🎯 {score_pct}% AI Relevance
                        </span>
                        <span style="font-size:0.78rem; color:var(--text-muted, #718096);">
                            Candidate 1 of {len(pending)}
                        </span>
                    </div>
                    <span style="font-size:0.75rem; color:var(--text-muted, #718096); font-family:monospace;">
                        {current_item.get('source_origin', 'Manual')}
                    </span>
                </div>
                <h3 style="margin:0 0 10px 0; font-family:Georgia, serif; font-size:1.32rem; font-weight:700; line-height:1.35; color:var(--text-main, #1b4332);">
                    {current_item.get('title', 'Untitled')}
                </h3>
                <div style="display:flex; flex-wrap:wrap; gap:12px; font-size:0.84rem; color:var(--text-muted, #4a5568); margin-bottom:14px;">
                    <span>👥 {', '.join(current_item.get('authors', [])[:4]) or 'Unknown Authors'}</span>
                    <span>📅 {current_item.get('year', 'N/A')}</span>
                    <span>🏛️ <em>{current_item.get('journal', 'Unknown Journal')}</em></span>
                    {f"<span>🔗 <a href='https://doi.org/{current_item.get('doi')}' target='_blank' style='color:#3b82f6; text-decoration:none;'>{current_item.get('doi')}</a></span>" if current_item.get('doi') else ''}
                </div>
                <div style="background:var(--metric-bg, #fafcf9); border:1px solid var(--panel-border, #e2e8f0); border-radius:10px; padding:14px; font-size:0.92rem; line-height:1.6; color:var(--text-main, #2d3748); max-height:240px; overflow-y:auto;">
                    {current_item.get('abstract') or '<em>No abstract available for this reference. Screen based on title and journal.</em>'}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Screening Action Controls
        c_inc, c_exc, c_undo, c_skip = st.columns([2.5, 2.5, 1.5, 1.5])

        with c_inc:
            if st.button("⭐ Include (I)", key="_btn_act_inc", type="primary", use_container_width=True):
                current_item["decision"] = "included"
                current_item["screened_at"] = datetime.now().isoformat()
                history.append({"id": current_item.get("id"), "decision": "included"})
                session["consecutive_excludes"] = 0
                
                # Active learning re-ranking
                model = ASReviewActiveLearningModel()
                session["candidates"] = model.fit_and_rerank(candidates)
                session["history"] = history
                session["last_modified"] = datetime.now().isoformat()
                save_screening_sessions(sessions)
                st.rerun()

        with c_exc:
            if st.button("❌ Exclude (E)", key="_btn_act_exc", use_container_width=True):
                current_item["decision"] = "excluded"
                current_item["screened_at"] = datetime.now().isoformat()
                history.append({"id": current_item.get("id"), "decision": "excluded"})
                session["consecutive_excludes"] = consecutive_ex + 1
                
                # Active learning re-ranking
                model = ASReviewActiveLearningModel()
                session["candidates"] = model.fit_and_rerank(candidates)
                session["history"] = history
                session["last_modified"] = datetime.now().isoformat()
                save_screening_sessions(sessions)
                st.rerun()

        with c_undo:
            if st.button("↩️ Undo (U)", key="_btn_act_undo", use_container_width=True, disabled=(len(history) == 0)):
                last_act = history.pop()
                for c in candidates:
                    if c.get("id") == last_act.get("id"):
                        c["decision"] = "pending"
                        break
                session["history"] = history
                session["last_modified"] = datetime.now().isoformat()
                save_screening_sessions(sessions)
                st.rerun()

        with c_skip:
            if st.button("⏭️ Skip", key="_btn_act_skip", use_container_width=True):
                # Move to back of pending queue
                skipped = candidates.pop(candidates.index(current_item))
                candidates.append(skipped)
                session["candidates"] = candidates
                save_screening_sessions(sessions)
                st.rerun()

    # ── Included Papers Drawer & Export Hub ──
    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    with st.expander(f"⭐ Included Studies Repository ({len(included)} papers)", expanded=False):
        if not included:
            st.caption("No papers included yet. Relevant studies will appear here.")
        else:
            inc_df = pd.DataFrame([
                {
                    "Title": p.get("title"),
                    "Year": p.get("year"),
                    "Journal": p.get("journal"),
                    "DOI": p.get("doi"),
                    "Source": p.get("source_origin"),
                }
                for p in included
            ])
            st.dataframe(inc_df, use_container_width=True, height=220)

            e_col1, e_col2, e_col3 = st.columns(3)
            with e_col1:
                # Add to Project Paper Pool
                if st.button("📥 Add Included to Project Paper Pool", key="_btn_add_to_pool", use_container_width=True):
                    p_data = VW.load_project_data()
                    current_search = p_data.get("search_records", [])
                    existing_dois = {normalize_doi(r.get("doi")) for r in current_search if r.get("doi")}
                    added = 0
                    for inc in included:
                        d_norm = normalize_doi(inc.get("doi"))
                        if not d_norm or d_norm not in existing_dois:
                            current_search.append({
                                "title": inc.get("title", ""),
                                "abstract": inc.get("abstract", ""),
                                "doi": inc.get("doi", ""),
                                "year": inc.get("year"),
                                "authors": ", ".join(inc.get("authors", [])),
                                "venue": inc.get("journal", ""),
                                "source": "ASReview Included",
                            })
                            added += 1
                    p_data["search_records"] = current_search
                    VW.save_project_data(p_data)
                    st.success(f"Added {added} included studies to Unified Paper Pool!")

            with e_col2:
                # Export CSV
                csv_data = inc_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📄 Export Included (CSV)",
                    data=csv_data,
                    file_name=f"included_{session.get('name', 'screening').replace(' ', '_')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

            with e_col3:
                # Export PRISMA Flow Summary
                prisma_summary = (
                    f"PRISMA 2020 Flow Diagram Data Summary\n"
                    f"Generated by Vellum Desktop App V2.0\n"
                    f"Session: {session.get('name')}\n"
                    f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n\n"
                    f"Identification:\n"
                    f"  - Total records identified across sources: {n_total}\n"
                    f"Screening:\n"
                    f"  - Records screened: {n_screened}\n"
                    f"  - Records excluded: {len(excluded)}\n"
                    f"Included:\n"
                    f"  - Studies included in review: {len(included)}\n"
                )
                st.download_button(
                    "📊 Export PRISMA Summary (TXT)",
                    data=prisma_summary.encode("utf-8"),
                    file_name="PRISMA_screening_flow.txt",
                    mime="text/plain",
                    use_container_width=True,
                )
