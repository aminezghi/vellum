"""
Literature Check tab — a self-contained Streamlit panel.

`render()` draws the whole tab and is called from the main app so that all the
search state lives here and the downloader tab stays untouched.
"""

from __future__ import annotations

import json
import re
from datetime import datetime

import pandas as pd
import streamlit as st

import litcheck_core as C
import litcheck_sources as S
import vellum_import

DOC_TYPES = ["journal-article", "conference-paper", "book", "book-chapter",
             "dissertation", "review", "preprint", "dataset", "report",
             "posted-content", "software"]

QUERY_SYNTAX = [
    ("OpenAlex / Crossref / CORE / DOAJ / DataCite",
     "space separated terms; `AND` `OR` `NOT` are honoured; `\"exact phrase\"` works"),
    ("PubMed / Europe PMC",
     "field tags like `microplastics[Title/Abstract]`, MeSH terms, `AND`/`OR`"),
    ("arXiv", "plain terms, or `ti:` `au:` `abs:` `cat:` prefixes"),
    ("Scopus", "`TITLE-ABS-KEY(...)`, `AUTHKEY(...)`, `PUBYEAR`, `DOCTYPE(...)`"),
]


def _keys_from_state():
    return {
        "OPENALEX_API_KEY": st.session_state.get("k_openalex", "").strip(),
        "CROSSREF_PLUS_TOKEN": st.session_state.get("k_crossref", "").strip(),
        "ELSEVIER_USER_KEY": st.session_state.get("k_elsevier", "").strip(),
        "NCBI_API_KEY": st.session_state.get("k_ncbi", "").strip(),
        "S2_API_KEY": st.session_state.get("k_s2", "").strip(),
        "DOAJ_API_KEY": st.session_state.get("k_doaj", "").strip(),
        "CORE_API_KEY": st.session_state.get("k_core", "").strip(),
        "WOS_API_TOKEN": st.session_state.get("k_wos", "").strip(),
    }


def _reset_results():
    for k in ("lit_reports", "lit_raw_n", "lit_unique", "lit_audit",
              "lit_conflicts", "lit_query", "lit_filters", "lit_prisma",
              "lit_screen", "lit_records", "lit_queue", "pending_dois"):
        st.session_state.pop(k, None)


def render():
    col_t1, col_t2 = st.columns([4.2, 1.3], vertical_alignment="center")
    with col_t1:
        st.markdown("### 🔎 Literature Check — Multi-Source Search & File Import")
        st.caption("Build queries across 10+ databases, or upload exports from Scopus/PubMed. High-throughput deduplication supports 2,000+ to 50,000+ papers.")
    with col_t2:
        if st.button("🔄 Reset Session", key="lit_reset_session_top_btn", width="stretch", help="Wipe all queries, search results, and uploaded screening records"):
            _reset_results()
            st.success("Session reset!")
            st.rerun()

    # ── 0. File Import Section (Scopus, PubMed, WoS, CSV, RIS, BibTeX) ──────
    with st.expander("📁 Import External Search File (Scopus, PubMed, WoS, CSV, RIS, BibTeX)", expanded=False):
        st.caption("Upload bibliography files exported from **Scopus**, **PubMed**, **Web of Science**, **Dimensions**, or reference managers. Duplicates are filtered automatically, and DOIs can be sent directly to the download queue.")
        up_files = st.file_uploader(
            "Upload files (.csv, .ris, .bib, .tsv, .txt)",
            type=["csv", "ris", "bib", "tsv", "txt"],
            accept_multiple_files=True,
            key="lit_external_file_uploader",
            help="Supports Scopus CSV, PubMed CSV/PMID text, WoS CSV/TSV, and universal RIS/BibTeX."
        )
        if up_files:
            all_imported = []
            tot_p = 0
            tot_d = 0
            for uf in up_files:
                recs, stats = vellum_import.universal_import_file(uf.read(), uf.name)
                tot_p += stats["total_parsed"]
                tot_d += stats["duplicates_removed"]
                all_imported.extend(recs)

            if len(all_imported) > 1:
                uniq_imp, _, _ = C.deduplicate(all_imported)
            else:
                uniq_imp = all_imported

            doi_cnt = sum(1 for r in uniq_imp if r.get("doi"))
            st.success(f"✅ Extracted **{len(uniq_imp)} unique articles** ({doi_cnt} with verified DOIs) from {len(up_files)} file(s). **{tot_d} duplicate(s)** removed.")

            c_act1, c_act2 = st.columns(2)
            with c_act1:
                if st.button("📥 Load Unique DOIs into PDF Downloader Queue", type="primary", key="btn_send_imp_to_dl", width="stretch"):
                    payload = []
                    for i, q in enumerate(uniq_imp):
                        key = q.get("doi") or (q.get("pdf_url") or f"item-{i}")
                        payload.append({"key": key, "doi": q.get("doi") or "", "pdf_url": q.get("pdf_url") or "", "title": q.get("title") or key})
                    st.session_state["pending_dois"] = payload
                    st.session_state["_go_download"] = True
                    st.rerun()
            with c_act2:
                if st.button("📊 Merge into Search Results & Screening", key="btn_merge_imp_lit", width="stretch"):
                    existing = st.session_state.get("lit_unique", [])
                    combined = list(existing) + uniq_imp
                    merged, audit, conf = C.deduplicate(combined)
                    st.session_state["lit_unique"] = merged
                    st.session_state["lit_raw_n"] = (st.session_state.get("lit_raw_n", 0) + len(uniq_imp))
                    st.session_state["lit_audit"] = audit
                    st.session_state["lit_conflicts"] = conf
                    st.session_state["lit_reports"] = st.session_state.get("lit_reports", []) + [
                        {"source": "file_import", "label": "External File Import", "n": len(uniq_imp), "reported": tot_p, "status": "ok", "elapsed": 0.1}
                    ]
                    st.session_state["lit_prisma"] = C.prisma(
                        st.session_state["lit_reports"], merged, len(merged), 0, C.build_queue(merged))
                    st.success(f"Merged {len(uniq_imp)} articles into your screening table!")
                    st.rerun()

    keys = _keys_from_state()
    runnable, blocked = S.available_sources(keys)
    runnable_ids = [s["id"] for s in runnable]
    st.session_state.setdefault("lit_sources", [
        "openalex", "crossref", "europepmc", "pubmed", "arxiv",
        "semantic_scholar", "datacite", "doaj", "core"])

    # ── 1. Top Search Bar ───────────────────────────────────────────────────
    current_q = st.session_state.get("lit_query", "")
    col_q, col_btn = st.columns([5, 1.4], vertical_alignment="bottom")
    with col_q:
        new_q = st.text_input(
            "Search literature",
            value=current_q,
            placeholder="Search keywords, topics, DOI, or e.g. \"machine learning\" AND (biomedical OR clinical)...",
            label_visibility="collapsed",
            key="_top_lit_search_input",
            help="Unified query across all selected databases. Use uppercase AND, OR, NOT for boolean logic."
        )
    if new_q != current_q:
        if current_q:
            _reset_results()
        st.session_state["lit_query"] = new_q
        current_q = new_q

    with col_btn:
        active_sources = [s for s in st.session_state.lit_sources if s in runnable_ids]
        run_search_btn = st.button(
            "🚀 Search Literature",
            type="primary",
            use_container_width=True,
            disabled=not bool(current_q.strip() and active_sources),
            key="lit_top_search_run_btn",
        )

    # ── Advanced Query Builder & Syntax Help Drawer ──────────────────────────
    with st.expander("🧩 Visual Boolean Builder & Query Syntax", expanded=False):
        mode = st.radio(
            "Query Mode",
            ["🧩 Visual Boolean Builder", "✍️ Advanced Raw Query"],
            horizontal=True,
            label_visibility="collapsed",
            key="lit_query_mode",
        )
        if mode == "🧩 Visual Boolean Builder":
            if "lit_clauses" not in st.session_state:
                st.session_state["lit_clauses"] = [
                    {"field": "All fields", "term": "", "connector": "AND"},
                    {"field": "Title / Abstract", "term": "", "connector": "AND"},
                ]
            clauses = st.session_state["lit_clauses"]
            st.caption("Combine concepts using boolean logic. Quotes are added automatically around multi-word terms.")
            for idx, c in enumerate(clauses):
                col_conn, col_field, col_term, col_del = st.columns([1.2, 2.2, 4.5, 0.6])
                with col_conn:
                    if idx == 0:
                        st.markdown("<div style='padding-top:8px; font-weight:600; color:#8b949e;'>WHERE</div>", unsafe_allow_html=True)
                    else:
                        c["connector"] = st.selectbox(
                            f"Conn {idx}",
                            ["AND", "OR", "NOT"],
                            index=["AND", "OR", "NOT"].index(c.get("connector", "AND")),
                            key=f"clause_conn_{idx}",
                            label_visibility="collapsed",
                        )
                with col_field:
                    field_opts = ["All fields", "Title / Abstract", "Author", "Topic / Keyword", "Publication Year"]
                    cur_f = c.get("field", "All fields")
                    c["field"] = st.selectbox(
                        f"Field {idx}",
                        field_opts,
                        index=field_opts.index(cur_f) if cur_f in field_opts else 0,
                        key=f"clause_field_{idx}",
                        label_visibility="collapsed",
                    )
                with col_term:
                    c["term"] = st.text_input(
                        f"Term {idx}",
                        value=c.get("term", ""),
                        placeholder=f"e.g. {'microplastics' if idx == 0 else 'marine ecology'}",
                        key=f"clause_term_{idx}",
                        label_visibility="collapsed",
                    )
                with col_del:
                    if len(clauses) > 1:
                        if st.button("✕", key=f"del_clause_{idx}", help="Remove clause"):
                            clauses.pop(idx)
                            st.session_state["lit_clauses"] = clauses
                            st.rerun()

            c_add, c_clear = st.columns([2, 5])
            if c_add.button("➕ Add Clause", key="btn_add_clause"):
                clauses.append({"field": "All fields", "term": "", "connector": "AND"})
                st.session_state["lit_clauses"] = clauses
                st.rerun()

            compiled_parts = []
            for i, c in enumerate(clauses):
                term = (c.get("term") or "").strip()
                if not term:
                    continue
                if " " in term and not (term.startswith('"') and term.endswith('"')):
                    quoted_term = f'"{term}"'
                else:
                    quoted_term = term

                field = c.get("field", "All fields")
                if field == "Title / Abstract":
                    segment = f'{quoted_term}[Title/Abstract]'
                elif field == "Author":
                    segment = f'au:{quoted_term}'
                elif field == "Publication Year":
                    segment = f'year:{quoted_term}'
                else:
                    segment = quoted_term

                if i == 0:
                    compiled_parts.append(segment)
                else:
                    compiled_parts.append(f"{c.get('connector', 'AND')} {segment}")

            compiled_str = " ".join(compiled_parts)
            if compiled_str:
                col_comp_txt, col_comp_btn = st.columns([4, 1.5], vertical_alignment="center")
                with col_comp_txt:
                    st.info(f"**Compiled Query:** `{compiled_str}`")
                with col_comp_btn:
                    if st.button("Apply to Search Bar", key="btn_apply_compiled_q", type="secondary", use_container_width=True):
                        st.session_state["lit_query"] = compiled_str
                        st.rerun()
        else:
            raw_q = st.text_area(
                "Raw Query Editor",
                value=st.session_state.get("lit_query", ""),
                placeholder="\"machine learning\" AND (biomedical OR clinical) NOT review",
                height=80,
                help="One query is sent to every selected source. Each database applies its own syntax.",
                key="_lit_raw_query_area"
            )
            if raw_q != st.session_state.get("lit_query", ""):
                if st.button("Apply Raw Query to Search Bar", key="btn_apply_raw_q"):
                    st.session_state["lit_query"] = raw_q
                    st.rerun()

            if raw_q:
                warnings = []
                if raw_q.count('"') % 2 != 0:
                    warnings.append("⚠️ Unmatched double quote (`\"`) detected.")
                if raw_q.count("(") != raw_q.count(")"):
                    warnings.append(f"⚠️ Unbalanced parentheses: {raw_q.count('(')} open vs {raw_q.count(')')} closed.")
                has_lower_booleans = bool(re.search(r"\b(and|or|not)\b", raw_q))
                if has_lower_booleans:
                    warnings.append("💡 Lowercase boolean operators detected (`and`, `or`, `not`). Academic APIs require uppercase `AND`, `OR`, `NOT`.")

                if warnings:
                    for w in warnings:
                        st.caption(w)
                    if has_lower_booleans:
                        if st.button("✨ Auto-Capitalize Boolean Operators", key="fix_booleans_btn"):
                            fixed = re.sub(r"\band\b", "AND", raw_q)
                            fixed = re.sub(r"\bor\b", "OR", fixed)
                            fixed = re.sub(r"\bnot\b", "NOT", fixed)
                            st.session_state["lit_query"] = fixed
                            st.rerun()

        with st.expander("Per-database query syntax & translation", expanded=False):
            for name, syn in QUERY_SYNTAX:
                st.markdown(f"- **{name}** — {syn}")

    # ── Databases Drawer (Full Width) ───────────────────────────────────────
    with st.expander(f"🌐 Databases & API Keys ({len(active_sources)} selected)", expanded=False):
        chosen = st.multiselect(
            "Databases to search",
            options=runnable_ids,
            default=[s for s in st.session_state.lit_sources if s in runnable_ids],
            format_func=lambda i: S.SOURCE_BY_ID[i]["label"],
            help="All selected sources are queried in parallel.",
            key="lit_sources_multiselect"
        )
        st.session_state["lit_sources"] = chosen
        with st.expander("Database specialties"):
            for s in S.SOURCE_REGISTRY:
                mark = "✅" if s["id"] in runnable_ids else "🔑"
                st.markdown(f"- {mark} **{s['label']}** — {s['note']}")
        if blocked:
            st.warning("Skipped (needs a key): " +
                       ", ".join(f"{s['label']} ({s['reason']})" for s in blocked))

        with st.expander("API keys (optional except where noted)"):
            c1, c2 = st.columns(2)
            st.session_state["k_openalex"] = c1.text_input(
                "OpenAlex API key", type="password", placeholder="optional",
                help="Free, from openalex.org. Raises rate limits 10×.")
            st.session_state["k_crossref"] = c2.text_input(
                "Crossref Plus token", type="password", placeholder="optional")
            st.session_state["k_elsevier"] = c1.text_input(
                "Elsevier / Scopus API key", type="password", placeholder="required for Scopus")
            st.session_state["k_ncbi"] = c2.text_input(
                "NCBI API key", type="password", placeholder="optional",
                help="Free from ncbi.nlm.nih.gov. 3→10 requests/sec.")
            st.session_state["k_s2"] = c1.text_input(
                "Semantic Scholar API key", type="password", placeholder="strongly recommended",
                help="The keyless pool rate-limits hard (HTTP 429).")
            st.session_state["k_doaj"] = c2.text_input(
                "DOAJ API key", type="password", placeholder="optional")
            st.session_state["k_core"] = c1.text_input(
                "CORE API key", type="password", placeholder="optional")
            st.session_state["k_wos"] = c2.text_input(
                "Web of Science token", type="password", placeholder="subscription required")
            if st.session_state.get("k_elsevier"):
                st.caption("Your Scopus key is reused by the downloader tab — "
                           "paste it there too to raise the article entitlement.")
        keys = _keys_from_state()

    # ── Filters Drawer (Full Width) ──────────────────────────────────────────
    with st.expander("🎯 Search Filters & Limits", expanded=False):
        f = st.session_state.get("lit_filters", {})
        c_y1, c_y2, c_max, c_cit = st.columns([1, 1, 1.2, 1])
        with c_y1:
            y_from = st.number_input("From year", 1900, 2100,
                                    int(f.get("year_from") or 2015), step=1)
        with c_y2:
            y_to = st.number_input("To year", 1900, 2100,
                                  int(f.get("year_to") or datetime.now().year), step=1)
        if y_from > y_to:
            y_from, y_to = y_to, y_from
        with c_max:
            max_records = st.number_input(
                "Max per source (supports 2000+)", 10, 10000,
                int(f.get("max_records") or 1000), step=50,
                help="Maximum records to retrieve per database. Set higher for comprehensive searches (e.g. 2000-5000)."
            )
        with c_cit:
            min_cit = st.number_input("Min citations", 0, 100000,
                                      int(f.get("min_citations") or 0), step=5)

        types = st.multiselect("Publication types", DOC_TYPES,
                               default=f.get("doc_types") or [])
        d1, d2 = st.columns(2)
        oa_only = d1.checkbox("Open access only", value=bool(f.get("oa_only")))
        has_ft = d2.checkbox("Has full-text PDF link", value=bool(f.get("has_fulltext")))
        filters = {
            "year_from": int(y_from), "year_to": int(y_to),
            "max_records": int(max_records), "doc_types": types or None,
            "oa_only": oa_only, "has_fulltext": has_ft,
            "min_citations": int(min_cit) or None,
        }
        st.session_state["lit_filters"] = filters

    email = st.session_state.get("lit_email",
                                 st.session_state.get("unpaywall_email", ""))

    query_to_run = (st.session_state.get("lit_query") or "").strip()
    sources_to_run = [s for s in st.session_state.get("lit_sources", []) if s in runnable_ids]
    filters_to_run = st.session_state.get("lit_filters", {})

    if run_search_btn and query_to_run and sources_to_run:
        bar = st.progress(0.0, text="Starting…")
        done = []

        def on_progress(info, total):
            done.append(info)
            bar.progress(min(1.0, len(done) / max(1, len(sources_to_run))),
                         text=f"{info['label']}: {info['n']} records "
                              f"({total} total)")

        with st.spinner("Querying databases in parallel…"):
            recs, reports = S.run_search(sources_to_run, query_to_run, filters_to_run, keys,
                                         email, workers=min(6, len(sources_to_run)),
                                         progress=on_progress)
        bar.empty()
        uniq, audit, conf = C.deduplicate(recs)
        st.session_state["lit_reports"] = reports
        st.session_state["lit_raw_n"] = len(recs)
        st.session_state["lit_unique"] = uniq
        st.session_state["lit_audit"] = audit
        st.session_state["lit_conflicts"] = conf
        st.session_state["lit_prisma"] = C.prisma(
            reports, uniq, len(uniq), 0, C.build_queue(uniq))
        st.rerun()

    reports = st.session_state.get("lit_reports")
    if not reports:
        st.markdown(
            "<div style='text-align: center; padding: 40px 20px; color: #888; font-size: 0.95rem;'>"
            "Enter your research query above and click <b>🚀 Search Literature</b> to scan databases in parallel."
            "</div>",
            unsafe_allow_html=True
        )
        return

    # ── 5. per-source report ────────────────────────────────────────────────
    with st.expander("📗 What each database returned", expanded=True):
        rows = []
        for r in reports:
            rows.append({
                "database": r.get("label"),
                "retrieved": r.get("n", 0),
                "reported hits": r.get("reported"),
                "capped": "⚠️ yes" if r.get("truncated") else "",
                "filtered out": r.get("year_filtered_out", ""),
                "seconds": r.get("elapsed"),
                "status": r.get("status") or "ok",
                "ignored filters": ", ".join(r.get("ignored") or []),
            })
        st.dataframe(pd.DataFrame(rows), use_container_width=True,
                     hide_index=True)
        st.caption("`reported hits` is the database's own count; `retrieved` is "
                   "what was actually downloaded. A ⚠️ means the source capped "
                   "the result set, so the search is not exhaustive for it.")

    # ── 6. results ──────────────────────────────────────────────────────────
    uniq = st.session_state["lit_unique"]
    audit = st.session_state.get("lit_audit") or []
    conf = st.session_state.get("lit_conflicts") or []

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Records retrieved", st.session_state.get("lit_raw_n", 0))
    m2.metric("After deduplication", len(uniq))
    m3.metric("Found in >1 database", sum(1 for r in uniq if r["source_count"] > 1))
    m4.metric("With a direct PDF link",
              sum(1 for r in uniq if r.get("pdf_url")))

    rows = C.apply_filters(uniq, filters)
    st.markdown(f"**{len(rows)} records** after refinement.")
    if len(rows) != len(uniq):
        with st.expander("Refine further"):
            e1, e2, e3 = st.columns(3)
            journal = e1.text_input("Journal contains")
            author = e2.text_input("Author contains")
            title = e3.text_input("Title contains")
            rows = C.apply_filters(rows, {
                "year_from": filters["year_from"], "year_to": filters["year_to"],
                "oa_only": filters["oa_only"], "has_fulltext": filters["has_fulltext"],
                "min_citations": filters["min_citations"],
                "journal_contains": journal, "author_contains": author,
                "title_contains": title})
            st.caption(f"{len(rows)} records match.")

    screen = st.session_state.setdefault("lit_screen", {})

    # Bulk screening toolbar
    c_bulk1, c_bulk2, c_bulk3, c_bulk4 = st.columns([1.5, 1.5, 1.5, 3.5])
    with c_bulk1:
        if st.button("✅ Include All", key="btn_include_all_records", help="Mark all records as included for download"):
            for r in rows:
                k = r.get("doi") or r.get("title") or ""
                if k:
                    screen[k] = "include"
            st.session_state["lit_screen"] = screen
            st.rerun()
    with c_bulk2:
        if st.button("❌ Exclude All", key="btn_exclude_all_records", help="Mark all records as excluded"):
            for r in rows:
                k = r.get("doi") or r.get("title") or ""
                if k:
                    screen[k] = "exclude"
            st.session_state["lit_screen"] = screen
            st.rerun()
    with c_bulk3:
        if st.button("🔄 Clear Choices", key="btn_clear_screen_choices", help="Reset all screening decisions"):
            st.session_state["lit_screen"] = {}
            st.rerun()

    # Pagination controls for high volume (2,000+ articles)
    total_records = len(rows)
    PAGE_SIZE = 100
    total_pages = max(1, (total_records + PAGE_SIZE - 1) // PAGE_SIZE)
    if total_pages > 1:
        pg_c1, pg_c2, pg_c3 = st.columns([2.5, 2.0, 2.5], vertical_alignment="center")
        with pg_c1:
            st.caption(f"Showing page items (Page size: {PAGE_SIZE})")
        with pg_c2:
            cur_page = st.number_input("Page", min_value=1, max_value=total_pages, value=1, step=1, key="lit_res_page_num")
        with pg_c3:
            st.caption(f"Showing {(cur_page-1)*PAGE_SIZE + 1}–{min(cur_page*PAGE_SIZE, total_records)} of {total_records} records")
        start_idx = (cur_page - 1) * PAGE_SIZE
        end_idx = min(cur_page * PAGE_SIZE, total_records)
        display_rows = rows[start_idx:end_idx]
    else:
        display_rows = rows

    df = pd.DataFrame([{**C.to_row(r), "screen": screen.get(r.get("doi") or r["title"], "")}
                       for r in display_rows])
    show = ["screen", "title", "authors", "year", "journal", "doi", "cited_by",
            "sources", "source_count", "pdf_url", "oa_status", "is_oa"]
    edited = st.data_editor(
        df[[c for c in show if c in df.columns]],
        use_container_width=True, hide_index=True, height=min(500, 45 + len(display_rows)*35),
        column_config={
            "screen": st.column_config.SelectboxColumn(
                "Screen", options=["", "include", "exclude"], width="small",
                help="Your screening decision, saved with the project."),
            "title": st.column_config.TextColumn("Title", width="large"),
            "authors": st.column_config.TextColumn("Authors", width="medium"),
            "doi": st.column_config.TextColumn("DOI", width="medium"),
            "cited_by": st.column_config.NumberColumn("Cited", format="%d"),
            "source_count": st.column_config.NumberColumn("Srcs", format="%d"),
        },
        disabled=[c for c in df.columns if c != "screen" and c in show],
        key=f"lit_editor_page_{st.session_state.get('lit_res_page_num', 1)}")

    # persist screening decisions for current page
    key_of_display = [(r.get("doi") or r.get("title") or "", r) for r in display_rows]
    for (k, _r), val in zip(key_of_display, edited["screen"].tolist()):
        if k:
            screen[k] = val
    st.session_state["lit_screen"] = screen
    st.session_state["lit_records"] = [C.to_row(r) for r in rows]

    key_of_all = [(r.get("doi") or r.get("title") or "", r) for r in rows]
    included = [r for (k, r) in key_of_all if screen.get(k) == "include"]
    excluded_n = sum(1 for k, _ in key_of_all if screen.get(k) == "exclude")
    undecided = len(rows) - len(included) - excluded_n
    queue_rows = included if included else rows
    queue = C.build_queue(queue_rows)

    st.caption(f"Screening: **{len(included)} included** · **{excluded_n} excluded** · "
               f"**{undecided} undecided**. Sending undecided rows when nothing is marked included.")

    # ── 7. handoff to the downloader ────────────────────────────────────────
    st.markdown("#### ⬇️ Download queue")
    qc1, qc2 = st.columns([3, 1])
    qc1.metric("Articles ready to download", len(queue))
    n_doi = sum(1 for q in queue if q["doi"])
    n_url = len(queue) - n_doi
    if st.button("📥 Load into the downloader tab", type="primary",
                 use_container_width=True):
        payload = []
        for i, q in enumerate(queue):
            # A record with no DOI still needs a stable key; the downloader
            # pins that key to the record's PDF url.
            key = q["doi"] or (q["pdf_url"] or f"item-{i}")
            payload.append({"key": key, "doi": q["doi"],
                            "pdf_url": q["pdf_url"], "title": q["title"]})
        st.session_state["pending_dois"] = payload
        st.session_state["lit_queue"] = queue
        st.session_state["_go_download"] = True
        st.rerun()

    # ── 7.5. Explore in Citation Graph ──────────────────────────────────────
    cg_candidates = [r for r in queue_rows if r.get("doi")]
    if cg_candidates:
        st.markdown("#### 🕸️ Citation Graph Explorer")
        st.caption("Map the citation network of any discovered paper to find derivative works and prior foundations.")
        cg_col1, cg_col2 = st.columns([3, 1])

        def _paper_label(doi_str):
            for r in cg_candidates:
                if r.get("doi") == doi_str:
                    t = str(r.get("title") or "Untitled")[:65]
                    y = r.get("year") or "N/A"
                    return f"({y}) {t}… [{doi_str}]"
            return str(doi_str)

        cg_doi = cg_col1.selectbox(
            "Select paper to explore:",
            options=[r["doi"] for r in cg_candidates],
            format_func=_paper_label,
            key="lit_cg_pick",
            label_visibility="collapsed",
        )
        if cg_col2.button("🕸️ View in Graph", width="stretch"):
            st.session_state["_graph_seed_doi"] = cg_doi
            st.session_state["_cg_pending_target"] = cg_doi
            st.session_state["_go_graph"] = True
            st.rerun()

    # Auto-sync active search and screening to Research Vault active project
    try:
        import vellum_workspace as VW
        p_data = VW.load_project_data()
        p_data["search_records"] = rows[:500]
        p_data["screened"] = {
            k: {"status": screen.get(k, "undecided")} for k, _ in key_of if k
        }
        VW.save_project_data(p_data)
    except Exception:
        pass

    # ── 8. PRISMA ───────────────────────────────────────────────────────────
    pr = C.prisma(st.session_state["lit_reports"], uniq, len(included),
                  excluded_n, queue)
    st.session_state["lit_prisma"] = pr
    with st.expander("📊 PRISMA 2020 flow", expanded=False):
        st.markdown(
            f"- Records identified by all databases (as reported): **{pr['identified']:,}**\n"
            f"- Records actually retrieved: **{pr['retrieved']:,}**\n"
            f"- Duplicates removed: **{pr['duplicates_removed']:,}**\n"
            f"- Records after deduplication: **{pr['after_dedup']:,}**\n"
            f"- Records screened: **{pr['screened']:,}**\n"
            f"- Excluded at screening: **{pr['excluded_at_screening']:,}**\n"
            f"- Studies included: **{pr['included']:,}**\n"
            f"- In PDF download queue: **{pr['pdf_queue']:,}**")
        st.dataframe(pd.DataFrame(pr["per_source"]), use_container_width=True,
                     hide_index=True)

    # ── 9. exports ──────────────────────────────────────────────────────────
    with st.expander("💾 Export", expanded=False):
        proj = st.text_input("Project name", value=st.session_state.get("lit_project", ""))
        st.session_state["lit_project"] = proj
        e1, e2, e3 = st.columns(3)
        e1.download_button("⬇️ All records (CSV)", C.export_csv(queue_rows),
                           file_name=f"{proj or 'search'}_records.csv",
                           mime="text/csv", use_container_width=True)
        e2.download_button("⬇️ Download queue (CSV)", C.export_csv(queue_rows),
                           file_name=f"{proj or 'search'}_queue.csv",
                           mime="text/csv", use_container_width=True)
        e3.download_button("⬇️ PRISMA counts (CSV)", C.export_prisma_csv(pr),
                           file_name=f"{proj or 'search'}_prisma.csv",
                           mime="text/csv", use_container_width=True)
        f1, f2, f3 = st.columns(3)
        f1.download_button("⬇️ BibTeX", C.export_bibtex(queue_rows),
                           file_name=f"{proj or 'search'}.bib",
                           mime="application/x-bibtex", use_container_width=True)
        f2.download_button("⬇️ RIS", C.export_ris(queue_rows),
                           file_name=f"{proj or 'search'}.ris",
                           mime="application/x-research-info-systems",
                           use_container_width=True)
        f3.download_button("⬇️ Duplicate audit (CSV)", C.export_duplicates(audit),
                           file_name=f"{proj or 'search'}_duplicates.csv",
                           mime="text/csv", use_container_width=True)
        if st.button("💾 Save project", use_container_width=True):
            path = C.save_project(proj or "untitled", {
                "query": query, "filters": filters, "sources": chosen,
                "records": queue_rows, "audit": audit, "conflicts": conf,
                "prisma": pr, "screen": screen,
                "saved": datetime.now().isoformat(timespec="seconds")})
            st.success(f"Saved to {path}")

    if conf:
        with st.expander(f"⚠️ {len(conf)} same-titled pairs were NOT merged",
                         expanded=False):
            st.caption("These share a title but have different DOIs or years, "
                       "so they are probably different works. Check them by hand.")
            st.dataframe(pd.DataFrame(conf), use_container_width=True,
                         hide_index=True)

    if audit:
        with st.expander(f"🔗 Deduplication audit ({len(audit)} merges)",
                         expanded=False):
            st.dataframe(pd.DataFrame(audit), use_container_width=True,
                         hide_index=True)

    # ── 10. snowballing ─────────────────────────────────────────────────────
    with st.expander("🌱 Citation snowballing (backward)", expanded=False):
        st.caption("Pick well-cited DOIs from the results and fetch the works "
                   "that cite them, via OpenAlex.")
        seeds = C.seed_dois(rows, limit=10)
        if not seeds:
            st.info("No DOIs available to snowball from.")
        else:
            pick = st.multiselect("Seed DOIs", seeds, default=seeds[:3],
                                  format_func=lambda d: d)
            if st.button("Fetch citing works") and pick:
                with st.spinner("Following citations…"):
                    found = []
                    for d in pick:
                        found.extend(C.cited_by_doi(d, email=email,
                                                    key=keys.get("OPENALEX_API_KEY")))
                st.session_state["lit_snowball"] = found
                st.success(f"{len(found)} citing works found — merge them into "
                           f"the pool with *Run search* or export separately.")
                if found:
                    st.download_button("⬇️ Snowballed works (CSV)",
                                       C.export_csv([{"doi": w.get("doi"),
                                                      "title": w.get("title"),
                                                      "year": w.get("publication_year"),
                                                      "cited_by": w.get("cited_by_count"),
                                                      "authors": "; ".join(
                                                          (a.get("author") or {}).get("display_name", "")
                                                          for a in (w.get("authorships") or [])),
                                                      "sources": ["openalex"],
                                                      "match_method": "snowball"} for w in found]),
                                       file_name=f"{proj or 'search'}_snowball.csv",
                                       mime="text/csv")