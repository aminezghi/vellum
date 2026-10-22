"""
app_pages/notes.py — Research Notes & Synthesis Hub for Vellum.

Provides unified, connected note-taking for systematic reviews:
  Tab 1: 📔 Project Synthesis Diary (Overall review findings, protocol, methodology notes)
  Tab 2: 📑 All Paper Appraisal Notes (Aggregated, searchable study-level notes & ratings)
"""

from __future__ import annotations

import csv
import io
from pathlib import Path
from typing import Any, Dict, List
import streamlit as st

import vellum_workspace as VW
import vellum_citation_export as VCE
import vellum_pages


def _clean_html(html_str: str) -> str:
    """Normalize HTML to a single line without indentations so Markdown never parses it as code."""
    return " ".join(line.strip() for line in html_str.splitlines() if line.strip())


def render() -> None:
    data = VW.load_project_data()
    proj_name = VW.get_active_project_name()
    papers = data.get("search_records", [])
    paper_notes = data.get("paper_notes", {})
    screened_dict = data.get("screened", {})

    # 1. Header Banner
    header_html = f"""
<div class="glass-panel" style="margin-bottom: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
            <div style="font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--apple-blue, #0071e3); font-weight: 700; margin-bottom: 2px;">
                SYNTHESIS & APPRAISAL • RESEARCH NOTES
            </div>
            <div style="font-size: 1.35rem; font-weight: 800; color: var(--text-main, #1d1d1f);">
                📝 Research Notes & Synthesis Hub
            </div>
            <div style="font-size: 0.85rem; color: var(--text-muted, #86868b); margin-top: 3px;">
                Project: <b style="color: var(--text-main, #1d1d1f);">{proj_name}</b> &nbsp;•&nbsp; 
                <span style="color: var(--apple-blue, #0071e3); font-weight: 600;">{len(paper_notes)}</span> studies appraised with notes
            </div>
        </div>
        <div style="display: flex; gap: 8px;">
            <span class="badge-sky">📝 {len(paper_notes)} Noted</span>
            <span class="badge-emerald">⭐ {sum(1 for v in screened_dict.values() if v.get('status') == 'included')} Included</span>
        </div>
    </div>
</div>
"""
    st.markdown(_clean_html(header_html), unsafe_allow_html=True)

    tab_diary, tab_studies = st.tabs(["📔 Project Synthesis Diary", "📑 All Paper Appraisal Notes"])

    # ──────────────────────────────────────────────────────────────────────────
    # Tab 1: Project Synthesis Diary
    # ──────────────────────────────────────────────────────────────────────────
    with tab_diary:
        current_notes = VW.get_project_notes()

        # Toolbar & Citation Inserter
        tb_col1, tb_col2 = st.columns([3.5, 1.5], vertical_alignment="bottom")
        with tb_col1:
            if papers:
                cite_opts = {
                    (p.get("doi") or p.get("title") or f"paper_{i}"): f"{p.get('title', 'Untitled')[:60]} ({p.get('year', 'N/A')})"
                    for i, p in enumerate(papers)
                }
                selected_seed = st.selectbox(
                    "Insert Citation into Diary:",
                    options=list(cite_opts.keys()),
                    format_func=lambda k: cite_opts.get(k, k),
                    key="_notes_cite_picker",
                )
                if st.button("➕ Insert Citation Reference", key="_notes_insert_cite_btn"):
                    matched_p = next((p for p in papers if (p.get("doi") or p.get("title")) == selected_seed), {})
                    auth = (matched_p.get("authors") or ["Author"])[0] if matched_p.get("authors") else "Study"
                    if isinstance(auth, str) and " " in auth:
                        auth = auth.split()[-1]
                    cite_tag = f"\n\n> **Reference:** [@{auth}{matched_p.get('year', '')}: *{matched_p.get('title')}* (DOI: {matched_p.get('doi', 'N/A')})]\n"
                    st.session_state["_diary_text_area"] = current_notes + cite_tag
                    VW.save_project_notes(current_notes + cite_tag)
                    st.toast("Citation reference inserted!", icon="📎")
                    st.rerun()

        diary_val = st.text_area(
            "Review Synthesis Draft & Methodology Diary (Markdown supported):",
            value=st.session_state.get("_diary_text_area", current_notes),
            height=320,
            placeholder="Write your systematic review synthesis, thematic summary, inclusion justification, or research journal here...",
            key="_diary_editor_field",
        )

        b_c1, b_c2, b_c3, b_c4 = st.columns([1.5, 1.5, 1.5, 1.5])
        with b_c1:
            if st.button("💾 Save Synthesis Diary", type="primary", width="stretch", key="_save_diary_btn"):
                VW.save_project_notes(diary_val)
                st.session_state["_diary_text_area"] = diary_val
                st.toast("Synthesis Diary saved to Project Vault!", icon="✅")

        with b_c2:
            st.download_button(
                "📥 Export (.md)",
                data=diary_val,
                file_name=f"{proj_name}_Synthesis_Notes.md",
                mime="text/markdown",
                width="stretch",
                key="_exp_diary_md",
                help="Export synthesis draft as Markdown file",
            )

        with b_c3:
            p_dir = VW.get_project_dir()
            notes_file = p_dir / "synthesis_notes.md"
            if st.button("📂 Show File in Explorer", width="stretch", key="_open_diary_dir"):
                if notes_file.exists():
                    VCE.open_folder_and_select(notes_file)
                else:
                    VCE.open_file_or_folder(p_dir)

        with b_c4:
            if st.button("🔄 Reload from Vault", width="stretch", key="_reload_diary_btn"):
                st.session_state["_diary_text_area"] = VW.get_project_notes()
                st.rerun()

        with st.expander("👁️ Live Markdown Preview", expanded=False):
            if diary_val.strip():
                st.markdown(diary_val)
            else:
                st.caption("Diary is currently empty. Write above to see the formatted preview.")

    # ──────────────────────────────────────────────────────────────────────────
    # Tab 2: All Paper Appraisal Notes
    # ──────────────────────────────────────────────────────────────────────────
    with tab_studies:
        # Build unified list of papers that have records or notes
        all_studies = []
        seen_keys = set()

        for p in papers:
            k = p.get("doi") if (p.get("doi") and p.get("doi").startswith("10.")) else p.get("title", "")
            if not k:
                continue
            clean_k = str(k).strip().lower()
            seen_keys.add(clean_k)
            n_data = paper_notes.get(clean_k, {})
            all_studies.append({
                "key": clean_k,
                "title": p.get("title") or "Untitled Study",
                "authors": p.get("authors") or [],
                "year": p.get("year") or "N/A",
                "venue": p.get("journal") or p.get("venue") or "Academic Source",
                "doi": p.get("doi") or "",
                "pdf_url": p.get("pdf_url") or "",
                "quality": n_data.get("quality", 0),
                "takeaway": n_data.get("takeaway", ""),
                "limitations": n_data.get("limitations", ""),
                "notes": n_data.get("notes", ""),
                "is_included": screened_dict.get(k, {}).get("status") == "included",
            })

        # Also add any paper_notes entries that might not be in search_records
        for k, n_data in paper_notes.items():
            clean_k = str(k).strip().lower()
            if clean_k not in seen_keys:
                all_studies.append({
                    "key": clean_k,
                    "title": n_data.get("title") or clean_k,
                    "authors": n_data.get("authors") or [],
                    "year": n_data.get("year") or "N/A",
                    "venue": n_data.get("journal") or "Project Study",
                    "doi": n_data.get("doi") or (clean_k if clean_k.startswith("10.") else ""),
                    "pdf_url": n_data.get("path") or "",
                    "quality": n_data.get("quality", 0),
                    "takeaway": n_data.get("takeaway", ""),
                    "limitations": n_data.get("limitations", ""),
                    "notes": n_data.get("notes", ""),
                    "is_included": screened_dict.get(clean_k, {}).get("status") == "included",
                })

        if not all_studies:
            st.info("No studies found in this project. Discovered papers in your Paper Pool or Collection Dashboard will appear here.")
            return

        # Filters Row
        flt_c1, flt_c2, flt_c3 = st.columns([3, 1.5, 1.5])
        with flt_c1:
            q_search = st.text_input(
                "Filter study notes:",
                placeholder="🔍 Search by study title, author, keyword, or note contents...",
                key="_study_notes_search_input",
                label_visibility="collapsed",
            )
        with flt_c2:
            view_filter = st.selectbox(
                "Filter By:",
                options=["All Studies", "Only With Notes / Ratings", "Only Included Studies"],
                key="_study_notes_filter_sel",
                label_visibility="collapsed",
            )
        with flt_c3:
            sort_by = st.selectbox(
                "Sort By:",
                options=["Quality Rating (Highest)", "Year (Newest)", "Title (A-Z)"],
                key="_study_notes_sort_sel",
                label_visibility="collapsed",
            )

        filtered = all_studies
        if view_filter == "Only With Notes / Ratings":
            filtered = [s for s in filtered if s["quality"] > 0 or s["notes"] or s["takeaway"]]
        elif view_filter == "Only Included Studies":
            filtered = [s for s in filtered if s["is_included"]]

        if q_search.strip():
            w = q_search.strip().lower()
            filtered = [
                s for s in filtered
                if w in s["title"].lower()
                or w in s["notes"].lower()
                or w in s["takeaway"].lower()
                or w in s["limitations"].lower()
                or any(w in str(a).lower() for a in s["authors"])
            ]

        # Sorting
        if sort_by == "Quality Rating (Highest)":
            filtered = sorted(filtered, key=lambda s: s["quality"], reverse=True)
        elif sort_by == "Year (Newest)":
            def _safe_year(val):
                try:
                    return int(val)
                except Exception:
                    return 0
            filtered = sorted(filtered, key=lambda s: _safe_year(s["year"]), reverse=True)
        elif sort_by == "Title (A-Z)":
            filtered = sorted(filtered, key=lambda s: s["title"].lower())

        st.caption(f"Showing {len(filtered)} of {len(all_studies)} studies:")

        # Study Note Cards
        for idx, s in enumerate(filtered):
            with st.container(border=True):
                # Header row
                c_title, c_badge = st.columns([4, 1.5], vertical_alignment="top")
                with c_title:
                    st.markdown(f"**{s['title']}**")
                    auth_str = ", ".join(str(a) for a in s["authors"][:3]) + (" et al." if len(s["authors"]) > 3 else "")
                    st.caption(f"👥 {auth_str or 'Authors not listed'} · 🏛️ *{s['venue']}* · 📅 **{s['year']}**")
                with c_badge:
                    rating_stars = "⭐" * s["quality"] if s["quality"] else "⚪ Not rated"
                    st.markdown(
                        f"""<div style="text-align: right;">
                            <span class="badge-amber">{rating_stars}</span>
                            {'<span class="badge-emerald">⭐ INCLUDED</span>' if s['is_included'] else ''}
                        </div>""",
                        unsafe_allow_html=True,
                    )

                # Key Takeaway & Limitations Highlights
                if s["takeaway"]:
                    st.markdown(
                        f"<div style='border-left: 3px solid var(--apple-blue, #0071e3); background: rgba(0, 113, 227, 0.08); padding: 8px 14px; border-radius: 8px; font-size: 0.88rem; margin: 6px 0;'>"
                        f"💡 <b>Key Finding:</b> {s['takeaway']}</div>",
                        unsafe_allow_html=True,
                    )
                if s["limitations"]:
                    st.markdown(
                        f"<div style='border-left: 3px solid var(--apple-amber, #ff9f0a); background: rgba(255, 159, 10, 0.08); padding: 8px 14px; border-radius: 8px; font-size: 0.88rem; margin: 6px 0;'>"
                        f"⚠️ <b>Limitations / Caveats:</b> {s['limitations']}</div>",
                        unsafe_allow_html=True,
                    )

                if s["notes"]:
                    with st.expander("📖 View Full Appraisal Notes", expanded=True):
                        st.markdown(s["notes"])

                # In-line Editor & Quick Action row
                with st.expander("✏️ Edit Notes & Critical Appraisal", expanded=False):
                    e_c1, e_c2 = st.columns([1.5, 3.5])
                    with e_c1:
                        new_q = st.slider("Quality Score (1-5 ⭐):", 1, 5, max(1, s["quality"] or 3), key=f"_edit_q_{s['key']}_{idx}")
                        new_takeaway = st.text_input("Key Takeaway:", value=s["takeaway"], key=f"_edit_takeaway_{s['key']}_{idx}")
                        new_limits = st.text_input("Methodological Caveats:", value=s["limitations"], key=f"_edit_limits_{s['key']}_{idx}")
                    with e_c2:
                        new_body = st.text_area("Appraisal Comments & Page Citations:", value=s["notes"], height=110, key=f"_edit_notes_{s['key']}_{idx}")
                        if st.button("💾 Save Study Notes", key=f"_save_study_note_{s['key']}_{idx}", type="primary"):
                            VW.save_paper_notes(s["key"], {
                                "quality": new_q,
                                "takeaway": new_takeaway,
                                "limitations": new_limits,
                                "notes": new_body,
                                "title": s["title"],
                                "doi": s["doi"],
                                "year": s["year"],
                                "authors": s["authors"],
                                "journal": s["venue"],
                            })
                            st.toast(f"Saved notes for '{s['title'][:30]}...'!", icon="✅")
                            st.rerun()

                # Action Links
                l_c1, l_c2, l_c3 = st.columns([1.5, 1.5, 3])
                with l_c1:
                    if s["doi"] and s["doi"].startswith("10."):
                        st.link_button("🌐 Open DOI in Browser", f"https://doi.org/{s['doi']}", width="stretch")
                    elif s["pdf_url"] and s["pdf_url"].startswith("http"):
                        st.link_button("🌐 Open Link in Browser", s["pdf_url"], width="stretch")
                with l_c2:
                    if st.button("🔬 Inspect Evidence", key=f"_insp_from_notes_{idx}", width="stretch"):
                        vellum_pages.go("evidence_methodology")

        # Export All Notes Bar
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
        st.markdown("##### 📥 Export All Study Notes")
        exp_c1, exp_c2 = st.columns(2)
        with exp_c1:
            # Generate CSV
            csv_buf = io.StringIO()
            writer = csv.writer(csv_buf)
            writer.writerow(["Title", "Year", "Journal", "DOI", "Quality_Rating", "Key_Takeaway", "Limitations", "Notes", "Included"])
            for s in all_studies:
                writer.writerow([
                    s["title"], s["year"], s["venue"], s["doi"], s["quality"], s["takeaway"], s["limitations"], s["notes"], s["is_included"]
                ])
            st.download_button(
                "📥 Export All Notes to CSV (.csv)",
                data=csv_buf.getvalue(),
                file_name=f"{proj_name}_Study_Notes.csv",
                mime="text/csv",
                width="stretch",
                key="_exp_notes_csv_btn",
            )
        with exp_c2:
            # Generate Markdown Summary
            md_lines = [f"# Study Notes & Critical Appraisal: {proj_name}\n\n"]
            for s in all_studies:
                md_lines.append(f"## {s['title']} ({s['year']})\n")
                md_lines.append(f"- **DOI:** {s['doi']}\n")
                md_lines.append(f"- **Quality Rating:** {'⭐' * s['quality'] if s['quality'] else 'Not rated'}\n")
                if s["takeaway"]:
                    md_lines.append(f"- **Key Finding:** {s['takeaway']}\n")
                if s["limitations"]:
                    md_lines.append(f"- **Limitations:** {s['limitations']}\n")
                if s["notes"]:
                    md_lines.append(f"\n### Notes:\n{s['notes']}\n")
                md_lines.append("\n---\n\n")
            st.download_button(
                "📥 Export All Notes to Markdown (.md)",
                data="".join(md_lines),
                file_name=f"{proj_name}_Appraisal_Summary.md",
                mime="text/markdown",
                width="stretch",
                key="_exp_notes_md_btn",
            )
