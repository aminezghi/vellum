"""
vellum_paper_pool.py — Master Synchronized Paper Pool with Inline Row Expansion,
Direct PDF Downloading, Queue Drawer, and Citation Export.

Features:
  - Frosted HTML paper card rendering with zero code-block glitches (textwrap.dedent)
  - Inline row expansion for abstract and in-context actions
  - '⚡ Download Now' direct in-place PDF fetching
  - '📥 Add to Queue' with visible top Queue Drawer and '🚀 Download All'
  - 1-Click Export to Zotero (.ris), EndNote (.enw), and BibTeX (.bib)
"""

from __future__ import annotations

import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional
import streamlit as st

import vellum_workspace as VW
import vellum_direct_download as VDD
import vellum_citation_export as VCE
import vellum_pages


def _clean_html(html_str: str) -> str:
    """Normalize HTML to a single line without indentations so Markdown never parses it as code."""
    return " ".join(line.strip() for line in html_str.splitlines() if line.strip())


def render_paper_card(
    paper: Dict[str, Any],
    index: int,
    key_prefix: str = "pool",
) -> None:
    """Renders a single paper card with clean frosted HTML and inline expansion."""
    doi = (paper.get("doi") or "").strip().lower()
    title = paper.get("title") or "Untitled Paper"
    year = paper.get("year") or "N/A"
    venue = paper.get("venue") or paper.get("journal") or "Academic Source"
    citations = paper.get("cited_by_count") or paper.get("cited_by") or 0
    is_oa = paper.get("is_oa") or bool(paper.get("pdf_url"))

    authors = paper.get("authors") or []
    if isinstance(authors, list):
        author_str = ", ".join(str(a) for a in authors[:3]) + (" et al." if len(authors) > 3 else "")
    else:
        author_str = str(authors)

    target_id = doi if (doi and doi.startswith("10.")) else title

    # Load current screening status
    data = VW.load_project_data()
    screened_dict = data.get("screened", {})
    screen_status = screened_dict.get(target_id, {}).get("status", "undecided")

    # Check if PDF already downloaded locally
    p_dir = VW.get_project_dir()
    local_pdf = None
    if doi:
        for p in (p_dir / "papers").glob("*.pdf"):
            if doi.replace("/", "_") in p.name:
                local_pdf = p
                break
    if not local_pdf:
        # Also check by sanitized title
        safe_t = VDD.sanitize_filename(title)
        cand = p_dir / "papers" / safe_t
        if cand.exists():
            local_pdf = cand

    # Badges & Notes Status
    if screen_status == "included":
        screen_badge = "<span class='badge-emerald'>⭐ INCLUDED</span>"
    elif screen_status == "excluded":
        screen_badge = "<span class='badge-amber'>❌ EXCLUDED</span>"
    else:
        screen_badge = "<span class='badge-slate'>⚪ UNDECIDED</span>"

    oa_badge = "<span class='badge-sky'>🔓 OPEN ACCESS</span>" if is_oa else ""
    cite_badge = f"<span class='badge-violet'>📈 {citations:,} Cites</span>" if citations else ""
    pdf_badge = "<span class='badge-emerald'>📄 PDF SAVED</span>" if local_pdf else ""

    p_note_key = doi if (doi and doi.startswith("10.")) else title
    note_info = VW.get_paper_notes(p_note_key)
    note_badge = ""
    if note_info.get("quality"):
        note_badge = f"<span class='badge-amber'>📝 ⭐ {note_info.get('quality')}/5</span>"
    elif note_info.get("notes") or note_info.get("takeaway"):
        note_badge = "<span class='badge-amber'>📝 NOTED</span>"

    import vellum_theme as VT
    dark = VT.is_dark_mode() if hasattr(VT, "is_dark_mode") else True
    if dark:
        card_bg = "rgba(36, 36, 38, 0.70)"
        card_border = "rgba(255, 255, 255, 0.08)"
        card_shadow = "0 2px 8px rgba(0, 0, 0, 0.25)"
        title_color = "#f5f5f7"
        meta_color = "#8e8e93"
        abs_bg = "rgba(0, 0, 0, 0.25)"
        abs_color = "#d1d1d6"
    else:
        card_bg = "#ffffff"
        card_border = "rgba(0, 0, 0, 0.08)"
        card_shadow = "0 1px 3px rgba(0, 0, 0, 0.04)"
        title_color = "#1d1d1f"
        meta_color = "#86868b"
        abs_bg = "rgba(0, 0, 0, 0.03)"
        abs_color = "#3a3a3c"

    # Flattened HTML to prevent any markdown code block formatting
    raw_html = f"""
<div style="background: {card_bg}; border: 1px solid {card_border}; border-radius: 12px; padding: 14px 16px; margin-bottom: 6px; box-shadow: {card_shadow}; backdrop-filter: blur(20px); box-sizing: border-box; overflow: hidden;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 14px; margin-bottom: 6px;">
        <div style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Display', sans-serif; font-size: 1.02rem; font-weight: 700; color: {title_color}; line-height: 1.35; flex: 1; min-width: 200px;">
            {title}
        </div>
        <div style="display: flex; gap: 6px; flex-shrink: 0; flex-wrap: wrap; justify-content: flex-end; max-width: 50%;">
            {screen_badge}
            {note_badge}
            {oa_badge}
            {pdf_badge}
            {cite_badge}
        </div>
    </div>
    <div style="font-family: -apple-system, BlinkMacSystemFont, 'SF Pro Text', sans-serif; font-size: 0.82rem; color: {meta_color}; line-height: 1.4;">
        👥 {author_str or 'Unknown Authors'} &nbsp;•&nbsp; 🏛️ <i>{venue}</i> &nbsp;•&nbsp; 📅 <b>{year}</b>
    </div>
</div>
"""
    st.markdown(_clean_html(raw_html), unsafe_allow_html=True)

    # Inline Expander for Actions, Notes & Abstract
    expander_title = f"🔍 Actions, Notes & Abstract ({doi or 'No DOI'})"
    with st.expander(expander_title, expanded=False):
        if paper.get("abstract"):
            st.markdown(
                f"<div style='font-size: 0.88rem; color: {abs_color}; line-height: 1.6; margin-bottom: 12px; background: {abs_bg}; padding: 12px; border-radius: 8px;'>"
                f"{paper['abstract']}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.caption("No abstract text available for this record.")

        # In-Context Action Row
        c_act1, c_act2, c_act3, c_act4 = st.columns([1.2, 2.0, 1.2, 1.0])

        # 1. Screen Toggle
        with c_act1:
            if screen_status == "included":
                if st.button("❌ Mark Exclude", key=f"{key_prefix}_ex_{index}", width="stretch"):
                    screened_dict[target_id] = {"status": "excluded"}
                    data["screened"] = screened_dict
                    VW.save_project_data(data)
                    st.rerun()
            else:
                if st.button("⭐ Mark Include", key=f"{key_prefix}_inc_{index}", type="primary", width="stretch"):
                    screened_dict[target_id] = {"status": "included"}
                    data["screened"] = screened_dict
                    VW.save_project_data(data)
                    st.rerun()

        # 2. PDF Actions (Direct Download Now vs Queue vs Open)
        with c_act2:
            if local_pdf:
                if st.button("📖 Open Saved PDF", key=f"{key_prefix}_read_{index}", width="stretch", help="Open local PDF in your default PDF reader"):
                    VCE.open_file_or_folder(local_pdf)
            else:
                dl_col1, dl_col2 = st.columns(2)
                with dl_col1:
                    if st.button("⚡ Download Now", key=f"{key_prefix}_dl_now_{index}", type="primary", width="stretch", help="Download PDF immediately into your vault"):
                        with st.spinner("Fetching full-text PDF..."):
                            ok, msg, fallback, path = VDD.download_single_paper_direct(paper)
                            if ok:
                                st.toast(f"✅ {msg}", icon="📄")
                                st.rerun()
                            else:
                                st.error(f"Download failed: {msg}")
                                if fallback:
                                    st.link_button("🌐 Open in Browser", fallback, width="stretch")
                with dl_col2:
                    if st.button("📥 Queue", key=f"{key_prefix}_dl_q_{index}", width="stretch", help="Add to batch download queue"):
                        added = VDD.add_to_download_queue(paper)
                        # Sync with Streamlit downloader pending_dois
                        pend = st.session_state.get("pending_dois", [])
                        k = doi or paper.get("pdf_url") or title
                        q_entry = {
                            "key": str(k).strip(),
                            "doi": doi,
                            "pdf_url": paper.get("pdf_url", ""),
                            "title": title,
                        }
                        if not any((isinstance(x, dict) and x.get("key") == str(k).strip()) or x == str(k).strip() for x in pend):
                            pend.append(q_entry)
                            st.session_state["pending_dois"] = pend
                        if added:
                            st.toast(f"Added to queue: {title[:30]}...", icon="📥")
                        else:
                            st.info("Already in queue")
                        st.rerun()

        # 3. Explore Citation Graph
        with c_act3:
            if st.button("🕸️ Lineage", key=f"{key_prefix}_cg_{index}", width="stretch", help="Explore upstream references & downstream citations"):
                st.session_state["_cg_pending_target"] = doi or title
                vellum_pages.go("discover_citation")

        # 4. Single Paper Citation Export
        with c_act4:
            clean_tag = (doi.replace("/", "_") if doi else "paper_citation")[:35]
            if st.button("📥 Export .ris", key=f"{key_prefix}_exp_{index}", width="stretch", help="Export to Downloads and Citation Manager"):
                ris_single = VCE.export_to_ris([paper])
                fn = f"{clean_tag}.ris"
                vp, dp = VCE.save_citation_export(fn, ris_single)
                st.session_state[f"_{key_prefix}_single_exp"] = str(dp or vp)
                st.toast(f"✅ Saved {fn} to Downloads!", icon="📥")
                st.rerun()

        # 5. Study Notes & Critical Appraisal Drawer
        rating_str = f"⭐ {note_info.get('quality')}/5" if note_info.get("quality") else "Not rated"
        with st.expander(f"📝 Study Notes & Critical Appraisal ({rating_str})", expanded=bool(note_info.get("notes") or note_info.get("takeaway"))):
            n_c1, n_c2 = st.columns([1.5, 3.5])
            with n_c1:
                q_val = st.slider("Quality Score (1-5 ⭐):", 1, 5, int(note_info.get("quality", 3)), key=f"{key_prefix}_q_slider_{index}")
                takeaway_val = st.text_input("Key Takeaway:", value=note_info.get("takeaway", ""), placeholder="Main contribution...", key=f"{key_prefix}_takeaway_{index}")
                limits_val = st.text_input("Methodological Caveats:", value=note_info.get("limitations", ""), placeholder="Risk of bias, sample limits...", key=f"{key_prefix}_limits_{index}")
            with n_c2:
                body_val = st.text_area("Critical Notes & Synthesis Remarks (Markdown supported):", value=note_info.get("notes", ""), height=110, placeholder="Document your study-level appraisal comments here...", key=f"{key_prefix}_body_{index}")
                if st.button("💾 Save Study Notes", key=f"{key_prefix}_save_note_{index}", type="primary"):
                    VW.save_paper_notes(p_note_key, {
                        "quality": q_val,
                        "takeaway": takeaway_val,
                        "limitations": limits_val,
                        "notes": body_val,
                        "title": title,
                        "doi": doi,
                        "year": year,
                        "authors": paper.get("authors", []),
                        "journal": venue,
                    })
                    st.toast(f"Saved notes for '{title[:30]}...'!", icon="✅")
                    st.rerun()

    st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)


def render_paper_pool(
    papers: List[Dict[str, Any]],
    key_prefix: str = "pool",
) -> None:
    """Renders the complete paper pool with search filter, queue banner, and 1-click citation export."""
    if not papers:
        st.info("No papers currently in your Project Paper Pool.")
        st.markdown(
            "Use **🔍 Discover** to search OpenAlex, PubMed, and Crossref, or start from the **🏠 Overview** recommendations."
        )
        return

    # 1. Download Queue Banner (if items are in queue)
    queue = VDD.get_download_queue()
    if queue:
        with st.container(border=True):
            qc1, qc2, qc3 = st.columns([3, 1.5, 1], vertical_alignment="center")
            with qc1:
                st.markdown(f"📥 **Download Queue:** `{len(queue)}` papers waiting for batch retrieval")
            with qc2:
                if st.button(f"🚀 Download All in Queue ({len(queue)})", type="primary", width="stretch", key="_pool_dl_all_btn"):
                    prog_bar = st.progress(0, text=f"Downloading {len(queue)} papers...")
                    def _prog(done, total):
                        prog_bar.progress(int((done / max(1, total)) * 100), text=f"Downloaded {done} of {total} papers...")
                    res = VDD.download_all_in_queue(progress_callback=_prog)
                    st.toast(f"Downloaded {res['success']} PDFs! (Remaining: {res['remaining']})", icon="✅")
                    st.rerun()
            with qc3:
                if st.button("🗑️ Clear", width="stretch", key="_pool_clear_q_btn", help="Clear the queue"):
                    VDD.clear_download_queue()
                    st.session_state["pending_dois"] = []
                    st.rerun()

    # 2. Top Action Bar: Search Filter & 1-Click Citation Export (Zotero, EndNote, BibTeX)
    data = VW.load_project_data()
    screened_dict = data.get("screened", {})
    included_papers = [
        p for p in papers
        if screened_dict.get(p.get("doi") if (p.get("doi") and p.get("doi").startswith("10.")) else p.get("title", ""), {}).get("status") == "included"
    ]
    export_target = included_papers if included_papers else papers
    export_label = f"({len(export_target)} Included)" if included_papers else f"({len(papers)} All)"

    st.markdown(f"#### 📚 Project Paper Pool • {len(papers)} Total")

    search_filter = st.text_input(
        "Filter pool",
        placeholder="🔍 Filter by title, author, keyword, or DOI...",
        label_visibility="collapsed",
        key=f"{key_prefix}_filter_input",
    )

    VCE.render_export_bar(export_target, key_prefix=f"{key_prefix}_pool_exp", label_suffix=export_label)

    st.markdown("<hr style='margin: 8px 0 16px 0; border: none; border-bottom: 1px solid rgba(255,255,255,0.06);'>", unsafe_allow_html=True)

    # Filter papers
    filtered = papers
    if search_filter.strip():
        q = search_filter.strip().lower()
        filtered = [
            p for p in papers
            if q in (p.get("title") or "").lower()
            or q in (p.get("doi") or "").lower()
            or any(q in str(a).lower() for a in (p.get("authors") or []))
        ]

    st.caption(f"Showing {len(filtered)} of {len(papers)} papers")

    for idx, p in enumerate(filtered):
        render_paper_card(p, index=idx, key_prefix=key_prefix)
