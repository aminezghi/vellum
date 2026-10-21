"""
Analysis & Evidence Hub — Unified Collection Dashboard and Deep Paper Inspection.

Combines:
  1. Collection Dashboard: duplicate scanning, extracted metadata, and publication trends for a folder of PDFs.
  2. Deep Paper Inspection: page-cited verbatim evidence for methods, sample sizes, statistics, rigour, and references.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import paper_analysis as PA  # noqa: E402
import vellum_analysis as VA  # noqa: E402
import vellum_paths as VP  # noqa: E402
import vellum_pdf_viewer as VPV  # noqa: E402

MAX_PAGES = 250
SNIPPET_CHARS = 260
MAX_SEARCH_HITS = 25


# ──────────────────────────────────────────────────────────────────────────────
# Cached Deep Analysis Engine
@st.cache_data(show_spinner=False, max_entries=6)
def _analyse_cached(path_str: str, mtime: float, size: int, deep: bool = True):
    path = Path(path_str)
    meta = VA.extract_one(path, deep=deep) or {}
    pages = VA.page_text(path, max_pages=MAX_PAGES)
    report = PA.analyse(path, meta, pages)
    return {"report": report, "pages": pages, "meta": meta}


def _analysis_for(path: Path, deep: bool = True):
    try:
        stat = path.stat()
        return _analyse_cached(str(path), stat.st_mtime, stat.st_size, deep)
    except Exception as exc:
        st.error(f"Could not analyse this PDF — {type(exc).__name__}: {exc}")
        return None


# ──────────────────────────────────────────────────────────────────────────────
# Main Page Entry Point
def render():
    import vellum_workspace as VW
    import vellum_citation_export as VCE

    st.subheader("Analysis & Evidence Hub")
    st.caption(
        "Gemini Notebook-style research workspace: Unified paper corpus, collection-level synthesis, "
        "and side-by-side deep inspection with verbatim page citations."
    )

    if not VA.is_ready():
        st.warning("PDF extractors are not registered yet — reload the app.")

    # ── 1. Unified Corpus & Source Controller (Single shared upload & folder) ──
    proj_papers = VW.get_project_dir() / "papers"
    proj_papers.mkdir(parents=True, exist_ok=True)
    n_proj_pdfs = len(list(proj_papers.glob("*.pdf")))

    active_folder = st.session_state.get("_unified_corpus_dir") or st.session_state.get("analysis_folder_path") or st.session_state.get("out_dir")
    if not active_folder or not Path(active_folder).is_dir():
        active_folder = str(proj_papers)
    st.session_state["_unified_corpus_dir"] = active_folder
    st.session_state["analysis_folder"] = active_folder
    st.session_state["analysis_folder_path"] = active_folder
    st.session_state["out_dir"] = active_folder

    n_pdfs = VP.pdf_count(active_folder, recursive=True)

    # Glass Corpus Header
    with st.container():
        c_title, c_upload_toggle, c_browse, c_exp = st.columns([2.6, 1.3, 1.2, 1.2], vertical_alignment="center")
        with c_title:
            is_vault = (str(Path(active_folder).resolve()) == str(proj_papers.resolve()))
            badge = "Active Project Vault" if is_vault else "External Folder"
            st.markdown(f"**📚 Corpus:** `{Path(active_folder).name}` &nbsp;·&nbsp; **{n_pdfs} PDFs** &nbsp;·&nbsp; <span class='badge-sky'>{badge}</span>", unsafe_allow_html=True)
            st.caption(f"`{active_folder}`")
        with c_upload_toggle:
            show_upload = st.toggle("📤 Add / Upload", key="_corpus_upload_toggle", help="Drag & drop new PDFs directly into this corpus folder")
        with c_browse:
            if st.button("📂 Change Folder", key="_change_corpus_folder_btn", use_container_width=True, help="Pick a different folder containing PDFs"):
                chosen = VP.native_folder_dialog(default_dir=active_folder)
                if chosen and Path(chosen).is_dir():
                    st.session_state["_unified_corpus_dir"] = chosen
                    st.session_state["analysis_folder"] = chosen
                    st.session_state["analysis_folder_path"] = chosen
                    st.session_state["analysis_folder_pending"] = chosen
                    st.session_state["out_dir"] = chosen
                    st.session_state.pop("meta_results", None)
                    st.session_state.pop("deep_result_path", None)
                    st.session_state.pop("deep_result", None)
                    st.rerun()
        with c_exp:
            if is_vault:
                if st.button("📂 Open Explorer", key="_open_corpus_exp", use_container_width=True):
                    VCE.open_file_or_folder(active_folder)
            else:
                if st.button("📁 Reset to Vault", key="_reset_to_vault_btn", use_container_width=True, help=f"Return to project papers ({n_proj_pdfs} PDFs)"):
                    st.session_state["_unified_corpus_dir"] = str(proj_papers)
                    st.session_state["analysis_folder"] = str(proj_papers)
                    st.session_state["analysis_folder_path"] = str(proj_papers)
                    st.session_state["analysis_folder_pending"] = str(proj_papers)
                    st.session_state["out_dir"] = str(proj_papers)
                    st.session_state.pop("meta_results", None)
                    st.rerun()

        if show_upload:
            uploaded_files = st.file_uploader(
                "Upload research PDFs directly into active corpus:",
                type=["pdf"],
                accept_multiple_files=True,
                key="_corpus_direct_uploader",
                help="Uploaded files will be immediately placed in the active corpus folder and analyzed."
            )
            if uploaded_files:
                saved = 0
                for uf in uploaded_files:
                    dest = Path(active_folder) / uf.name
                    if not dest.exists():
                        dest.write_bytes(uf.getbuffer())
                        saved += 1
                if saved > 0:
                    st.toast(f"Added {saved} PDF(s) to corpus!", icon="✅")
                    st.session_state.pop("meta_results", None)
                    st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

    # Top-level Section Selector
    section_options = ["📊 Collection Dashboard", "🔬 Deep Paper Inspection"]
    active_tab = st.session_state.get("analysis_active_tab")
    if active_tab not in section_options:
        active_tab = "📊 Collection Dashboard"

    tab_choice = st.segmented_control(
        "Analysis Section",
        section_options,
        default=active_tab,
        key="analysis_active_tab_ctrl",
        label_visibility="collapsed",
    )
    if tab_choice:
        st.session_state["analysis_active_tab"] = tab_choice

    curr_tab = st.session_state.get("analysis_active_tab", "📊 Collection Dashboard")
    if curr_tab == "📊 Collection Dashboard":
        _render_collection_dashboard(active_folder)
    else:
        _render_deep_inspection(active_folder)


# ──────────────────────────────────────────────────────────────────────────────
# Tab 1: Collection Dashboard
def _render_collection_dashboard(folder: str):
    import vellum_workspace as VW
    import vellum_citation_export as VCE

    n_pdfs = VP.pdf_count(folder, recursive=True)
    if not n_pdfs:
        st.info("No PDFs found in this folder yet. Use '📤 Add / Upload' above to add papers or choose a folder containing research PDFs.")
        return

    live = st.session_state.get("meta_results") or []
    watcher_running = bool(getattr(st.session_state.get("meta_watcher"), "is_alive", lambda: False)())
    same_folder = live and all(str(Path(r.get("path", "")).parent) == str(Path(folder)) for r in live if r.get("path"))

    view = st.segmented_control(
        "Collection View",
        ["Metadata Table", "Duplicates Scanner", "Publication Trends"],
        default="Metadata Table",
        label_visibility="collapsed",
        key="analysis_subview",
    )

    refresh = st.button("🔄 Re-scan folder", width="content")
    results = list(live) if (same_folder and not refresh) else None

    if results is None:
        cached = None if refresh else VA.load_metadata_cache(folder)
        if cached:
            st.session_state["meta_results"] = cached
            results = cached
            st.caption(f"{len(cached)} records restored from cache.")
        else:
            prog_box = st.container()
            with prog_box:
                p_bar = st.progress(0.0)
                p_text = st.empty()

            def _on_scan_progress(cur, total, name):
                pct = int((cur / max(1, total)) * 100)
                p_bar.progress(cur / max(1, total))
                p_text.markdown(f"⏳ **Loading collection ({pct}%)**: Scanning {cur} of {total} PDFs — `{name}`")

            results = VA.extract_all_metadata(folder, recursive=True, progress_callback=_on_scan_progress)
            VA.save_metadata_cache(folder, results)
            prog_box.empty()

    if not results:
        st.info("No metadata could be extracted from these PDFs.")
        return

    df = VA.meta_frame(results)
    if watcher_running:
        st.info("Downloader is running — metadata appears here automatically as each PDF lands.")

    # 1. Metadata View
    if view == "Metadata Table":
        cols = st.columns(4)
        cols[0].metric("PDFs in folder", len(df))
        cols[1].metric("With a title", int((df.get("title", pd.Series(dtype=str)).astype(str) != "").sum()))
        cols[2].metric("With a DOI", int((df.get("doi", pd.Series(dtype=str)).astype(str) != "").sum()))
        cols[3].metric("With year", int((df.get("year", pd.Series(dtype=str)).astype(str) != "").sum()))

        st.dataframe(
            df[["filename", "title", "authors", "year", "journal", "doi", "pages", "size_kb"]],
            use_container_width=True,
            hide_index=True,
        )

        # 1-Click Drill-down & Multi-Action Bar
        st.markdown("##### 🔬 Selected Study Actions & Deep Inspection")
        st.caption("Select any paper from the collection above to open, read, inspect evidence, or record appraisal notes:")
        valid_paths = [r["path"] for r in results if r.get("path")]
        if valid_paths:
            picked_path = st.selectbox(
                "Select Paper:",
                options=valid_paths,
                format_func=lambda p: Path(p).name,
                key="drilldown_select",
                label_visibility="collapsed",
            )
            # Find matching record
            rec = next((r for r in results if r.get("path") == picked_path), {})
            p_doi = (rec.get("doi") or "").strip()
            p_title = rec.get("title") or Path(picked_path).name

            reader_toggle_key = f"coll_in_place_reader_{picked_path}"
            is_reader_open = st.session_state.get(reader_toggle_key, False)

            act1, act2, act3, act4 = st.columns([1.4, 1.4, 1.3, 1.2])
            with act1:
                if st.button("🔬 Deep Inspect & Read", type="primary", use_container_width=True, help="Switch to Deep Inspection with side-by-side interactive PDF reader"):
                    st.session_state["deep_paper_path"] = picked_path
                    st.session_state["analysis_active_tab"] = "🔬 Deep Paper Inspection"
                    st.session_state["deep_result_path"] = None
                    st.rerun()

            with act2:
                btn_lbl = "📖 Close In-Place Reader" if is_reader_open else "📖 Read PDF In-Place"
                if st.button(btn_lbl, use_container_width=True, help="Toggle interactive PDF reader right here without switching tabs"):
                    st.session_state[reader_toggle_key] = not is_reader_open
                    st.rerun()

            with act3:
                if st.button("📂 Open in Windows App", use_container_width=True, help="Launch PDF in your Windows default PDF viewer (Adobe, Acrobat, Edge)"):
                    VCE.open_file_or_folder(picked_path)

            with act4:
                if p_doi and p_doi.startswith("10."):
                    st.link_button("🌐 Open in Browser", f"https://doi.org/{p_doi}", use_container_width=True, help="Open publisher landing page via DOI")
                else:
                    st.button("🌐 Browser (No DOI)", disabled=True, use_container_width=True)

            # In-Place PDF Reader
            if is_reader_open:
                st.markdown("---")
                VPV.render_pdf_viewer(picked_path, height=680, key_prefix=f"coll_reader_{Path(picked_path).name}", doi=p_doi, title=p_title)
                st.markdown("---")

            # Paper Appraisal & Notes Drawer for the selected paper
            p_key = p_doi if (p_doi and p_doi.startswith("10.")) else p_title
            curr_notes = VW.get_paper_notes(p_key)
            with st.expander(f"📝 Study Notes & Appraisal for: {Path(picked_path).name}", expanded=bool(curr_notes.get("notes") or curr_notes.get("takeaway"))):
                f_c1, f_c2 = st.columns([1.5, 3.5])
                with f_c1:
                    quality = st.slider("Quality Score (1-5 ⭐):", 1, 5, int(curr_notes.get("quality", 3)), key=f"coll_score_{Path(picked_path).name}")
                    takeaway = st.text_input("Key Finding / Takeaway:", value=curr_notes.get("takeaway", ""), placeholder="Main contribution or outcome...", key=f"coll_takeaway_{Path(picked_path).name}")
                    limitations = st.text_input("Methodological Caveats:", value=curr_notes.get("limitations", ""), placeholder="e.g. Small sample size (N=24), no control group...", key=f"coll_limits_{Path(picked_path).name}")
                with f_c2:
                    note_body = st.text_area("Detailed Notes & Critical Comments (Markdown supported):", value=curr_notes.get("notes", ""), height=130, placeholder="Write critical reflections, synthesis notes, or quote page citations...", key=f"coll_notes_{Path(picked_path).name}")
                    if st.button("💾 Save Study Notes", key=f"save_note_btn_{Path(picked_path).name}", type="primary"):
                        VW.save_paper_notes(p_key, {
                            "quality": quality,
                            "takeaway": takeaway,
                            "limitations": limitations,
                            "notes": note_body,
                            "title": p_title,
                            "doi": p_doi,
                            "path": str(picked_path),
                        })
                        st.toast("Saved study notes to Project Vault!", icon="✅")
                        st.rerun()

    # 2. Duplicates Scanner
    elif view == "Duplicates Scanner":
        dups = VA.find_duplicates(results)
        if not dups:
            st.success("✅ No duplicate papers found in this folder.")
        else:
            st.warning(f"⚠️ Found {len(dups)} group(s) of potential duplicates:")
            for i, group in enumerate(dups, 1):
                with st.expander(f"Group {i}: {group.get('reason', 'Matching metadata')}"):
                    for f in group.get("files", []):
                        st.markdown(f"- `{Path(f).name}`")

    # 3. Publication Trends
    elif view == "Publication Trends":
        st.markdown("##### 📈 Publication Year Distribution")
        years = df[df["year"].astype(str).str.isdigit()]["year"].astype(int)
        if not years.empty:
            year_counts = years.value_counts().sort_index()
            st.bar_chart(year_counts)
        else:
            st.info("No publication years available to chart.")

        st.markdown("##### 🏛️ Top Publication Venues")
        journals = df[df["journal"].astype(str).str.strip() != ""]["journal"].value_counts().head(8)
        if not journals.empty:
            st.dataframe(journals, use_container_width=True)


# ──────────────────────────────────────────────────────────────────────────────
# Tab 2: Deep Paper Inspection
def _render_deep_inspection(folder: str):
    st.markdown("#### 🔬 Evidence-Based Deep Analysis")
    st.caption(
        "Extracts verbatim sentences for methodology, sampling, statistics, and rigour. "
        "No AI hallucinations — every claim cites the exact page number."
    )

    pdfs = VA.list_pdfs(folder, recursive=True) if folder else []
    if not pdfs:
        st.info("No PDFs available to inspect in this corpus. Use '📤 Add / Upload' above to add research papers.")
        return

    options = [str(p) for p in pdfs]
    queued = st.session_state.pop("deep_paper_path", None)
    if queued:
        want = str(Path(str(queued)).expanduser())
        match = next((o for o in options if o == want or Path(o).name == Path(want).name), None)
        if match:
            options = [match] + [o for o in options if o != match]

    c_sel, c_back, c_btn = st.columns([3.8, 1.4, 1.2], vertical_alignment="center")
    with c_sel:
        choice_str = st.selectbox(
            "Select Paper to Inspect:",
            options=options,
            format_func=lambda o: Path(o).name,
            key="deep_unified_select",
        )
    with c_back:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        if st.button("📊 Collection View", key="back_to_coll_btn", use_container_width=True, help="Return to collection overview"):
            st.session_state["analysis_active_tab"] = "📊 Collection Dashboard"
            st.rerun()
    with c_btn:
        st.markdown("<div style='height: 28px;'></div>", unsafe_allow_html=True)
        do_analyse = st.button("Analyse 🔬", type="primary", use_container_width=True)

    if not choice_str:
        return

    choice = Path(choice_str)
    if do_analyse or st.session_state.get("deep_result_path") != str(choice):
        with st.spinner("Extracting verbatim evidence from PDF…"):
            st.session_state["deep_result"] = _analysis_for(choice, deep=True)
        st.session_state["deep_result_path"] = str(choice)

    payload = st.session_state.get("deep_result")
    if not payload:
        return

    rep = payload["report"]
    if not rep.get("ok"):
        st.error(f"This PDF could not be read — {rep.get('reason', 'unknown reason')}.")
        return

    ident = rep.get("identity") or {}
    p_doi = (ident.get("doi") or "").strip()
    target_seed = p_doi or ident.get("title")

    meta_bits = []
    if ident.get("year"):
        meta_bits.append(str(ident["year"]))
    if ident.get("journal"):
        meta_bits.append(str(ident["journal"]))
    if p_doi:
        meta_bits.append(f"DOI: {p_doi}")

    st.divider()

    # Layout Mode Selector: Side-by-Side Split View vs Full PDF vs Full Evidence
    view_layout = st.segmented_control(
        "Inspection Layout",
        ["🗗 Side-by-Side (PDF + Evidence)", "📄 Interactive PDF Reader", "🔬 Verbatim Evidence"],
        default="🗗 Side-by-Side (PDF + Evidence)",
        key=f"deep_layout_{choice.name}",
        label_visibility="collapsed",
    )

    if view_layout == "🗗 Side-by-Side (PDF + Evidence)":
        c_left, c_right = st.columns([1.1, 1.25], gap="medium")
        with c_left:
            VPV.render_pdf_viewer(choice, height=820, key_prefix="deep_split_pdf", doi=p_doi, title=ident.get("title"))
        with c_right:
            _render_evidence_details(choice, rep, ident, p_doi, target_seed, payload, meta_bits)
    elif view_layout == "📄 Interactive PDF Reader":
        VPV.render_pdf_viewer(choice, height=860, key_prefix="deep_full_pdf", doi=p_doi, title=ident.get("title"))
    else:
        _render_evidence_details(choice, rep, ident, p_doi, target_seed, payload, meta_bits)


def _render_evidence_details(choice, rep, ident, p_doi, target_seed, payload, meta_bits):
    """Renders the paper header, notes drawer, caveats and evidence tabs."""
    import vellum_workspace as VW
    import vellum_citation_export as VCE

    st.markdown(f"### {ident.get('title') or rep['filename']}")
    if ident.get("authors"):
        st.caption(f"👥 {ident['authors']}")

    c_m, c_g, c_b = st.columns([2.5, 1.2, 1.2], vertical_alignment="center")
    if meta_bits:
        c_m.caption(" · ".join(meta_bits))
    with c_g:
        if target_seed and st.button("🕸️ Graph", key=f"deep_cg_{choice.name}", help="Map citation network for this paper", use_container_width=True):
            st.session_state["_graph_seed_doi"] = target_seed
            st.session_state["_go_graph"] = True
            st.rerun()
    with c_b:
        if p_doi and p_doi.startswith("10."):
            st.link_button("🌐 Browser", f"https://doi.org/{p_doi}", use_container_width=True)
        else:
            if st.button("📂 In App", key=f"deep_open_pdf_{choice.name}", use_container_width=True, help="Launch PDF in your default PDF app"):
                VCE.open_file_or_folder(choice)

    # In-Context Study Notes & Critical Appraisal
    p_key = p_doi if (p_doi and p_doi.startswith("10.")) else (ident.get("title") or choice.name)
    curr_notes = VW.get_paper_notes(p_key)
    rating_lbl = f"⭐ {curr_notes.get('quality')}/5" if curr_notes.get("quality") else "Not rated"
    with st.expander(f"📝 Study Notes & Critical Appraisal ({rating_lbl})", expanded=bool(curr_notes.get("notes") or curr_notes.get("takeaway"))):
        f_c1, f_c2 = st.columns([1.5, 3.5])
        with f_c1:
            quality = st.slider("Quality Score (1-5 ⭐):", 1, 5, int(curr_notes.get("quality", 3)), key=f"deep_score_{choice.name}")
            takeaway = st.text_input("Key Finding / Takeaway:", value=curr_notes.get("takeaway", ""), placeholder="Main contribution...", key=f"deep_takeaway_{choice.name}")
            limitations = st.text_input("Methodological Caveats:", value=curr_notes.get("limitations", ""), placeholder="Caveats or risk of bias...", key=f"deep_limits_{choice.name}")
        with f_c2:
            note_body = st.text_area("Critical Notes / Page Quotations:", value=curr_notes.get("notes", ""), height=120, placeholder="Write evidence synthesis notes...", key=f"deep_notes_{choice.name}")
            if st.button("💾 Save Study Notes", key=f"deep_save_note_btn_{choice.name}", type="primary"):
                VW.save_paper_notes(p_key, {
                    "quality": quality,
                    "takeaway": takeaway,
                    "limitations": limitations,
                    "notes": note_body,
                    "title": ident.get("title") or choice.name,
                    "doi": p_doi,
                    "path": str(choice),
                })
                st.toast("Saved study notes to Project Vault!", icon="✅")
                st.rerun()

    if rep.get("caveats"):
        with st.expander(f"⚠️ Limits of this analysis ({len(rep['caveats'])})", expanded=False):
            for caveat in rep["caveats"]:
                st.warning(caveat)

    # Detailed Sub-tabs
    tabs = st.tabs(["Overview", "Method", "Sampling", "Statistics", "Rigour", "References", "Text Search"])

    with tabs[0]:
        _tab_overview(rep, ident)
    with tabs[1]:
        _tab_method(rep)
    with tabs[2]:
        _tab_sampling(rep)
    with tabs[3]:
        _tab_statistics(rep)
    with tabs[4]:
        _tab_rigour(rep)
    with tabs[5]:
        _tab_references(rep)
    with tabs[6]:
        _tab_search(payload.get("pages", []))


# ── Sub-tab Renderers ─────────────────────────────────────────────────────────
def _render_hits_list(items, title, empty_msg="No occurrences detected."):
    """Renders a list of items where each item is {'label': str, 'hits': [{'page': int, 'text': str}]}."""
    st.markdown(f"##### {title}")
    if not items:
        st.info(empty_msg)
        return
    for item in items:
        if isinstance(item, dict):
            label = item.get("label", "Finding")
            hits = item.get("hits") or []
            if hits:
                for h in hits:
                    page_no = h.get("page", "?")
                    snippet = h.get("text", "").strip()
                    with st.expander(f"📌 {label} (Page {page_no})", expanded=True):
                        st.markdown(f"> *\"{snippet}\"*")
            else:
                snippet = item.get("text") or item.get("snippet", "")
                page_no = item.get("page", "?")
                with st.expander(f"📌 {label} (Page {page_no})", expanded=True):
                    st.markdown(f"> *\"{snippet.strip()}\"*")
        elif isinstance(item, str):
            st.markdown(f"- {item}")


def _tab_overview(rep, ident):
    st.markdown("##### 📋 Document Metrics")
    diag = rep.get("diagnostics") or {}
    data = rep.get("data") or {}
    refs = rep.get("references") or {}

    pages = rep.get("pages_read") or diag.get("pages_read") or rep.get("pages", 0)
    chars = diag.get("characters") or rep.get("chars", 0)
    words = diag.get("words") or 0
    ref_count = refs.get("count") if isinstance(refs, dict) else len(refs)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Pages", pages)
    c2.metric("Characters", f"{chars:,}" if chars else "—")
    c3.metric("Word Count", f"{words:,}" if words else "—")
    c4.metric("References", ref_count)

    # Study scale & sample info if detected
    if data.get("sample_size"):
        st.caption(f"👥 **Estimated Sample Size:** {data['sample_size']} ({data.get('sample_label') or 'participants / observations'})")

    abstract = ident.get("abstract")
    if abstract:
        st.markdown("##### 📖 Abstract")
        st.write(abstract)


def _tab_method(rep):
    method = rep.get("method") or {}
    if not isinstance(method, dict):
        st.info("No methodology data available.")
        return

    st.markdown("##### 🔬 Research Design & Methodology")
    design = method.get("design")
    if design:
        st.success(f"**Identified Study Design:** {design}")

    text = method.get("text")
    if text:
        with st.expander("Verbatim Methodology Section", expanded=False):
            st.write(text)

    # Instruments, Software, Reliability, Bias control
    instruments = method.get("instruments") or []
    software = method.get("software") or []
    reliability = method.get("reliability") or []
    bias = method.get("bias_control") or []

    found_any = False
    if instruments:
        found_any = True
        _render_hits_list(instruments, "Measurement Instruments & Scales")
    if software:
        found_any = True
        _render_hits_list(software, "Software & Computing Tools")
    if reliability:
        found_any = True
        _render_hits_list(reliability, "Reliability & Measurement Validity")
    if bias:
        found_any = True
        _render_hits_list(bias, "Bias Control & Blinding")

    if not found_any and not design and not text:
        st.info("No explicit methodology markers detected in the body text.")


def _tab_sampling(rep):
    st.markdown("##### 👥 Sampling, Participants & Demographics")
    sampling = rep.get("sampling") or {}
    if not isinstance(sampling, dict):
        st.info("No sampling data available.")
        return

    data = rep.get("data") or {}
    if data.get("sample_size"):
        st.success(f"**Sample Size:** {data['sample_size']} ({data.get('sample_label') or 'participants / observations'})")

    part_text = sampling.get("participants_text")
    if part_text:
        with st.expander("Participants Description", expanded=True):
            st.write(part_text)

    strat = sampling.get("strategy") or []
    crit = sampling.get("criteria") or []
    demo = sampling.get("demographics") or []

    found_any = False
    if strat:
        found_any = True
        _render_hits_list(strat, "Sampling Strategy")
    if crit:
        found_any = True
        _render_hits_list(crit, "Eligibility / Inclusion Criteria")
    if demo:
        found_any = True
        _render_hits_list(demo, "Demographics & Socio-economic Attributes")

    if not found_any and not part_text and not data.get("sample_size"):
        st.info("No explicit sample sizes or sampling declarations detected in text.")


def _tab_statistics(rep):
    st.markdown("##### 📐 Statistical Tests, Models & Metrics")
    stats = rep.get("statistics") or {}
    if not isinstance(stats, dict):
        st.info("No statistical analysis data available.")
        return

    # Metrics row
    c1, c2, c3 = st.columns(3)
    c1.metric("P-values Found", stats.get("n_p_values", 0))
    c2.metric("Reports Effect Sizes", "Yes" if stats.get("reports_effect_size") else "No")
    c3.metric("Reports Conf. Intervals", "Yes" if stats.get("reports_ci") else "No")

    named = stats.get("named_methods") or []
    models = stats.get("models") or []
    effects = stats.get("effects") or []
    ci = stats.get("ci") or []

    found_any = False
    if named:
        found_any = True
        _render_hits_list(named, "Named Statistical Tests & Procedures")
    if models:
        found_any = True
        _render_hits_list(models, "Models & Estimators")
    if effects:
        found_any = True
        _render_hits_list(effects, "Reported Effect Sizes")
    if ci:
        found_any = True
        _render_hits_list(ci, "Confidence Intervals")

    if not found_any and stats.get("n_p_values", 0) == 0:
        st.info("No statistical test names or p-value patterns detected in text.")


def _tab_rigour(rep):
    st.markdown("##### 🛡️ Scientific Rigour, Transparency & Caveats")
    rigour = rep.get("rigour") or {}
    if not isinstance(rigour, dict):
        st.info("No rigour data available.")
        return

    # Transparency Statements
    stat_cols = st.columns(4)
    stat_cols[0].metric("Ethics Declared", "Yes" if rigour.get("ethics_found") else "Not found")
    stat_cols[1].metric("Funding Declared", "Yes" if rigour.get("funding_found") else "Not found")
    stat_cols[2].metric("Data Sharing", "Yes" if rigour.get("data_availability_found") else "Not found")
    stat_cols[3].metric("Conflicts Declared", "Yes" if rigour.get("conflicts_found") else "Not found")

    for field, label in [
        ("ethics", "Ethics & IRB Approval"),
        ("funding", "Funding Statement"),
        ("data_availability", "Data Availability Statement"),
        ("conflicts", "Conflicts of Interest"),
        ("limitations", "Author-Stated Limitations"),
    ]:
        val = rigour.get(field)
        if val:
            with st.expander(f"📋 {label}", expanded=False):
                st.write(val)

    validity = rigour.get("validity") or []
    language = rigour.get("language") or []
    guidelines = rigour.get("guidelines") or []

    if validity:
        _render_hits_list(validity, "Methodological Validity Checks")
    if language:
        _render_hits_list(language, "Scientific Language & Causal Wording")
    if guidelines:
        _render_hits_list(guidelines, "Reporting Guidelines (e.g. PRISMA, STROBE)")


def _tab_references(rep):
    st.markdown("##### 📚 Extracted References")
    refs_data = rep.get("references") or {}
    if isinstance(refs_data, dict):
        entries = refs_data.get("entries") or []
        count = refs_data.get("count", len(entries))
        span = refs_data.get("span")
    else:
        entries = list(refs_data)
        count = len(entries)
        span = None

    if not entries:
        st.info("No bibliography list could be separated from the body text.")
        return

    st.caption(f"Extracted **{count}** reference citations" + (f" (covering years {span[0]}–{span[1]})" if span else ""))
    for i, r in enumerate(entries, 1):
        st.markdown(f"**[{i}]** {r}")


def _tab_search(pages):
    st.markdown("##### 🔍 Page-Cited Full-Text Search")
    q = st.text_input("Search for term across all pages:", placeholder="e.g. p < 0.05 or control group")
    if not q:
        return
    q_lower = q.lower()
    hits = []
    for page_idx, page_text in enumerate(pages, 1):
        if q_lower in page_text.lower():
            start = page_text.lower().find(q_lower)
            snippet = page_text[max(0, start - 80) : min(len(page_text), start + 120)]
            hits.append((page_idx, snippet))

    if not hits:
        st.info(f"No occurrences of '{q}' found.")
        return

    st.success(f"Found {len(hits)} occurrence(s):")
    for p_num, snip in hits[:MAX_SEARCH_HITS]:
        st.markdown(f"- **Page {p_num}:** `…{snip.strip()}…`")
