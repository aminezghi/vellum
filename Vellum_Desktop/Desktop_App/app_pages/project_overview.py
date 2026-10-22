"""
project_overview.py — Streamlined Project Mission Control & Systematic Review Dashboard.

Minimalist single-focus layout:
  - Personalized Greeting (User Name & Research Discipline)
  - 4 Frosted Glass Metric Cards (Discovered, Screened, Downloaded, Appraised)
  - Fast Workflow Quick-Launch row
  - Direct 1-Click Export to Zotero (.ris) & EndNote (.enw)
  - Visible Download Queue Bar with '🚀 Download All in Queue'
  - Active Paper Stream with live suggested papers (with Refresh button) or screened pool
  - Advanced Project Scope & Criteria tucked cleanly into an expandable drawer
"""

from __future__ import annotations

import random
import textwrap
from typing import Any, Dict, List
import streamlit as st

import vellum_workspace as VW
import vellum_paper_pool as VPP
import vellum_direct_download as VDD
import vellum_citation_export as VCE
import vellum_pages

SEMINAL_FALLBACKS: List[Dict[str, Any]] = [
    {
        "title": "Attention Is All You Need",
        "doi": "10.48550/arxiv.1706.03762",
        "year": 2017,
        "authors": ["Ashish Vaswani", "Noam Shazeer", "Niki Parmar", "Jakob Uszkoreit"],
        "venue": "Advances in Neural Information Processing Systems",
        "cited_by": 135000,
        "is_oa": True,
        "pdf_url": "https://arxiv.org/pdf/1706.03762.pdf",
        "abstract": "The dominant sequence transduction models are based on complex recurrent or convolutional neural networks. We propose the Transformer, a model architecture eschewing recurrence and relying entirely on an attention mechanism to draw global dependencies between input and output.",
    },
    {
        "title": "Deep learning",
        "doi": "10.1038/nature14539",
        "year": 2015,
        "authors": ["Yann LeCun", "Yoshua Bengio", "Geoffrey Hinton"],
        "venue": "Nature",
        "cited_by": 65000,
        "is_oa": True,
        "pdf_url": "https://www.nature.com/articles/nature14539.pdf",
        "abstract": "Deep learning allows computational models that are composed of multiple processing layers to learn representations of data with multiple levels of abstraction. These methods have dramatically improved the state-of-the-art in speech recognition, visual object recognition and many other domains.",
    },
    {
        "title": "Hallmarks of Cancer: The Next Generation",
        "doi": "10.1016/j.cell.2011.02.013",
        "year": 2011,
        "authors": ["Douglas Hanahan", "Robert A. Weinberg"],
        "venue": "Cell",
        "cited_by": 58000,
        "is_oa": True,
        "pdf_url": "",
        "abstract": "The hallmarks of cancer comprise six biological capabilities acquired during the multistep development of human tumors. We propose an updated conceptual framework incorporating genomic instability, tumor-promoting inflammation, and reprogramming of energy metabolism.",
    },
    {
        "title": "Highly accurate protein structure prediction with AlphaFold",
        "doi": "10.1038/s41586-021-03819-2",
        "year": 2021,
        "authors": ["John Jumper", "Richard Evans", "Alexander Pritzel", "Demis Hassabis"],
        "venue": "Nature",
        "cited_by": 28000,
        "is_oa": True,
        "pdf_url": "https://www.nature.com/articles/s41586-021-03819-2.pdf",
        "abstract": "Proteins are essential to life, and understanding their structure can facilitate a mechanistic understanding of their function. We demonstrate a computational method that can regularly predict protein structures with atomic accuracy even in cases in which no similar structure is known.",
    },
    {
        "title": "The PRISMA 2020 statement: an updated guideline for reporting systematic reviews",
        "doi": "10.1136/bmj.n71",
        "year": 2021,
        "authors": ["Matthew J. Page", "Joanne E. McKenzie", "Patrick M. Bossuyt", "David Moher"],
        "venue": "BMJ",
        "cited_by": 26000,
        "is_oa": True,
        "pdf_url": "https://www.bmj.com/content/bmj/372/bmj.n71.full.pdf",
        "abstract": "The Preferred Reporting Items for Systematic Reviews and Meta-Analyses (PRISMA) 2020 statement provides updated reporting guidance for systematic reviews that reflects advances in methods to identify, select, appraise, and synthesise studies.",
    },
]


def _clean_html(html_str: str) -> str:
    """Normalize HTML to a single line without indentations so Markdown never parses it as code."""
    return " ".join(line.strip() for line in html_str.splitlines() if line.strip())


def _fetch_tailored_suggestions(field: str, keywords: str) -> List[Dict[str, Any]]:
    """Fetch 3-5 open-access papers from OpenAlex matching user's field and keywords."""
    query = f"{field} {keywords}".strip() or "Systematic review methodology"
    try:
        import litcheck_sources as ls
        results, _ = ls.search_openalex(query=query, per_source=5, max_records=5, oa_only=True)
        if results:
            return results
    except Exception:
        pass
    sample_size = min(3, len(SEMINAL_FALLBACKS))
    return random.sample(SEMINAL_FALLBACKS, sample_size)


def render() -> None:
    data = VW.load_project_data()
    stats = VW.get_project_stats()
    proj_name = VW.get_active_project_name()

    profile = VW.get_user_profile()
    user_name = profile.get("name") or "Researcher"
    user_field = profile.get("field") or "Scientific Research"
    user_keywords = profile.get("keywords") or ""

    # 1. Header Banner
    header_html = f"""
<div class="glass-panel" style="margin-bottom: 16px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
            <div style="font-size: 0.76rem; text-transform: uppercase; letter-spacing: 0.08em; color: var(--apple-blue, #0071e3); font-weight: 700; margin-bottom: 2px;">
                MISSION CONTROL • SYSTEMATIC REVIEW
            </div>
            <h1 style="margin: 0; font-size: 2.1rem; font-weight: 800; color: var(--text-main, #1d1d1f); letter-spacing: -0.025em; line-height: 1.2;">
                {proj_name}
            </h1>
            <div style="margin-top: 6px; font-size: 0.95rem; color: var(--text-muted, #86868b);">
                👋 Welcome back, <b style="color: var(--text-main, #1d1d1f);">{user_name}</b>! Exploring <span class="badge-sky">{user_field}</span>
            </div>
        </div>
        <div style="text-align: right;">
            <span class="badge-emerald" style="font-size: 0.82rem; padding: 4px 12px;">🟢 Live Project Vault</span>
        </div>
    </div>
</div>
"""
    st.markdown(_clean_html(header_html), unsafe_allow_html=True)

    # 2. 4 Metric Cards
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(
            f"""<div class="glass-metric">
                <div class="glass-metric-num" style="color: var(--apple-blue, #0071e3);">{stats.get('search_records', 0):,}</div>
                <div class="glass-metric-label">Discovered Papers</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c2:
        st.markdown(
            f"""<div class="glass-metric">
                <div class="glass-metric-num" style="color: var(--apple-emerald, #34c759);">{stats.get('included', 0):,}</div>
                <div class="glass-metric-label">Included / Screened</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c3:
        st.markdown(
            f"""<div class="glass-metric">
                <div class="glass-metric-num" style="color: var(--apple-purple, #af52de);">{stats.get('pdfs', 0):,}</div>
                <div class="glass-metric-label">Saved PDF Full-Texts</div>
            </div>""",
            unsafe_allow_html=True,
        )
    with c4:
        st.markdown(
            f"""<div class="glass-metric">
                <div class="glass-metric-num" style="color: var(--apple-amber, #ff9f0a);">{stats.get('appraisals', 0):,}</div>
                <div class="glass-metric-label">Appraisals Completed</div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # 3. Fast Workflow Quick-Launch Row
    lp1, lp2, lp3, lp4 = st.columns(4)
    with lp1:
        if st.button("🔍 Search Literature", width="stretch", help="Run multi-source queries across OpenAlex, PubMed, Crossref"):
            vellum_pages.go("discover_literature")
    with lp2:
        if st.button("🕸️ Citation Lineage", width="stretch", help="Explore upstream references & downstream citations"):
            if not st.session_state.get("_cg_pending_target"):
                pool_papers = data.get("search_records", [])
                if pool_papers:
                    p_seed = pool_papers[-1]
                    st.session_state["_cg_pending_target"] = p_seed.get("doi") or p_seed.get("title")
                elif "_suggested_feed" in st.session_state and st.session_state["_suggested_feed"]:
                    sug_list = st.session_state["_suggested_feed"]
                    sug_idx = st.session_state.get("_suggested_idx", 0)
                    p_sug = sug_list[sug_idx % len(sug_list)]
                    st.session_state["_cg_pending_target"] = p_sug.get("doi") or p_sug.get("title")
            vellum_pages.go("discover_citation")
    with lp3:
        if st.button("📚 Unified Paper Pool", width="stretch", help="Screen and manage all papers"):
            vellum_pages.go("library_pool")
    with lp4:
        if st.button("📥 PDF Downloader", width="stretch", help="Batch download queue and folder management"):
            vellum_pages.go("library_downloader")

    # 4. Advanced Scope & Criteria Drawer (Collapsed by default for a clean single-focus interface)
    with st.expander("⚙️ Advanced Project Scope & Inclusion Criteria", expanded=False):
        current_topic = data.get("topic") or ""
        new_topic = st.text_area(
            "Research Question / Topic Scope",
            value=current_topic,
            placeholder=f"e.g. Investigation of {user_field} methods in...",
            height=70,
            key="_overview_topic_input",
        )

        current_criteria = data.get("inclusion_criteria") or ""
        new_criteria = st.text_area(
            "Inclusion & Exclusion Criteria",
            value=current_criteria,
            placeholder="Include: Peer-reviewed studies 2020-2026, empirical data.\nExclude: Non-English, opinion articles.",
            height=90,
            key="_overview_criteria_input",
        )

        if st.button("💾 Save Scope & Criteria", width="stretch"):
            data["topic"] = new_topic
            data["inclusion_criteria"] = new_criteria
            VW.save_project_data(data)
            st.toast("Research criteria saved to Vault!", icon="✅")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)

    # 5. Visible Download Queue Banner (when items are queued)
    queue = VDD.get_download_queue()
    if queue:
        with st.container(border=True):
            qc1, qc2, qc3 = st.columns([3, 1.5, 1], vertical_alignment="center")
            with qc1:
                st.markdown(f"📥 **Download Queue:** `{len(queue)}` papers waiting for batch download")
            with qc2:
                if st.button(f"🚀 Download All in Queue ({len(queue)})", type="primary", width="stretch", key="_ovw_dl_all_btn"):
                    with st.spinner(f"Downloading {len(queue)} papers..."):
                        res = VDD.download_all_in_queue()
                        st.toast(f"Downloaded {res['success']} PDFs! (Remaining: {res['remaining']})", icon="✅")
                        st.rerun()
            with qc3:
                if st.button("🗑️ Clear", width="stretch", key="_ovw_clear_q_btn", help="Clear queue"):
                    VDD.clear_download_queue()
                    st.session_state["pending_dois"] = []
                    st.rerun()

    # 6. Active Paper Stream / Suggested Feed
    papers = data.get("search_records", [])

    if papers:
        # Header with 1-Click Citation Export
        st.markdown(f"#### 📑 Active Paper Stream • {len(papers)} Total")

        screened_dict = data.get("screened", {})
        included_papers = [
            p for p in papers
            if screened_dict.get(p.get("doi") if (p.get("doi") and p.get("doi").startswith("10.")) else p.get("title", ""), {}).get("status") == "included"
        ]
        export_target = included_papers if included_papers else papers
        export_label = f"({len(export_target)} Included)" if included_papers else f"({len(papers)} All)"

        VCE.render_export_bar(export_target, key_prefix="_ovw_pool_exp", label_suffix=export_label)

        st.caption(f"Showing latest {min(len(papers), 6)} papers in your project pool:")
        for idx, p in enumerate(reversed(papers[-6:])):
            VPP.render_paper_card(p, index=idx, key_prefix="ovw_pool")

        if len(papers) > 6:
            if st.button(f"View all {len(papers)} papers in Paper Pool ➔", width="stretch"):
                vellum_pages.go("library_pool")

    else:
        # Project is Empty -> Show Clean Single-Paper Spotlight Feed
        if "_suggested_feed" not in st.session_state or not st.session_state["_suggested_feed"]:
            st.session_state["_suggested_feed"] = _fetch_tailored_suggestions(user_field, user_keywords)
        if "_suggested_idx" not in st.session_state:
            st.session_state["_suggested_idx"] = 0

        suggested_list = st.session_state["_suggested_feed"]
        if not suggested_list:
            suggested_list = SEMINAL_FALLBACKS

        # Clamp/cycle index
        curr_idx = st.session_state["_suggested_idx"] % len(suggested_list)
        p_sug = suggested_list[curr_idx]

        sug_hdr_c1, sug_hdr_c2 = st.columns([3, 1], vertical_alignment="center")
        with sug_hdr_c1:
            st.markdown(
                f"""
                <div style="font-size: 1.15rem; font-weight: 700; color: var(--apple-blue, #0071e3);">
                    🌟 Suggested Paper Spotlight • {user_field}
                </div>
                <div style="font-size: 0.82rem; color: var(--text-muted, #86868b); margin-top: 2px;">
                    Hand-picked seminal work tailored to your profile. Click Refresh to explore another paper:
                </div>
                """,
                unsafe_allow_html=True,
            )
        with sug_hdr_c2:
            if st.button("🔄 Suggest Another Paper", width="stretch", key="_refresh_sug_btn", help="Cycle to next suggested paper"):
                # Advance index, and if at end, re-fetch
                st.session_state["_suggested_idx"] = st.session_state.get("_suggested_idx", 0) + 1
                if st.session_state["_suggested_idx"] >= len(suggested_list):
                    fresh = _fetch_tailored_suggestions(user_field, user_keywords)
                    seen_titles = {x.get("title") for x in suggested_list}
                    for f in fresh:
                        if f.get("title") not in seen_titles:
                            suggested_list.append(f)
                    st.session_state["_suggested_feed"] = suggested_list
                st.rerun()

        st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)

        # Single Card Spotlight
        with st.container(border=True):
            s_title = p_sug.get("title") or "Untitled Paper"
            s_year = p_sug.get("year") or "N/A"
            s_venue = p_sug.get("journal") or p_sug.get("venue") or "Academic Source"
            s_cites = p_sug.get("cited_by") or p_sug.get("cited_by_count") or 0
            s_abstract = p_sug.get("abstract") or "No abstract summary available."
            s_doi = (p_sug.get("doi") or "").strip().lower()
            s_authors = p_sug.get("authors") or []
            if isinstance(s_authors, list):
                author_preview = ", ".join(str(a) for a in s_authors[:3]) + (" et al." if len(s_authors) > 3 else "")
            else:
                author_preview = str(s_authors)

            card_box = f"""
<div style="margin-bottom: 8px;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 4px;">
        <div style="font-size: 1.05rem; font-weight: 700; color: var(--text-main, #1d1d1f); line-height: 1.35; flex: 1;">
            {s_title}
        </div>
        <div style="display: flex; gap: 6px; flex-shrink: 0;">
            <span class="badge-sky">🔓 OPEN ACCESS</span>
            <span class="badge-violet">📈 {s_cites:,} Cites</span>
        </div>
    </div>
    <div style="font-size: 0.83rem; color: var(--text-muted, #86868b); margin-top: 3px;">
        👥 <b>{author_preview or 'Featured Authors'}</b> &nbsp;•&nbsp; 🏛️ <i>{s_venue}</i> &nbsp;•&nbsp; 📅 <b>{s_year}</b>
    </div>
    <div style="font-size: 0.86rem; color: var(--text-main, #1d1d1f); line-height: 1.5; margin-top: 10px; background: rgba(125,125,125,0.08); padding: 10px 14px; border-radius: 8px; border-left: 3px solid var(--apple-blue, #0071e3);">
        {s_abstract[:360]}{"..." if len(s_abstract) > 360 else ""}
    </div>
</div>
"""
            st.markdown(_clean_html(card_box), unsafe_allow_html=True)

            act_c1, act_c2, act_c3, act_c4 = st.columns([1.5, 1.4, 1.1, 1.2])

            with act_c1:
                if st.button("➕ Add to Pool & Screen ⭐", key="_sug_spotlight_add", type="primary", width="stretch"):
                    plist = data.get("search_records", [])
                    plist.append(p_sug)
                    data["search_records"] = plist
                    target_key = s_doi if (s_doi and s_doi.startswith("10.")) else s_title
                    screened = data.get("screened", {})
                    screened[target_key] = {"status": "included"}
                    data["screened"] = screened
                    VW.save_project_data(data)
                    st.toast(f"Added to Project Pool!", icon="✅")
                    st.rerun()

            with act_c2:
                if st.button("⚡ Download PDF Now", key="_sug_spotlight_dl", width="stretch", help="Download PDF directly into your Vault"):
                    with st.spinner("Fetching full-text PDF..."):
                        # Add to pool first if not present
                        plist = data.get("search_records", [])
                        if not any(x.get("title") == s_title for x in plist):
                            plist.append(p_sug)
                            data["search_records"] = plist
                            VW.save_project_data(data)
                        ok, msg, fallback_url, dest_path = VDD.download_single_paper_direct(p_sug)
                        if ok:
                            st.toast(f"✅ {msg}", icon="📄")
                            st.rerun()
                        else:
                            st.error(f"Download failed: {msg}")
                            if fallback_url:
                                st.link_button("🌐 Open PDF in Browser", fallback_url, width="stretch")

            with act_c3:
                if st.button("📥 Add to Queue", key="_sug_spotlight_queue", width="stretch", help="Queue paper for batch download"):
                    added = VDD.add_to_download_queue(p_sug)
                    pend = st.session_state.get("pending_dois", [])
                    k = s_doi or s_title
                    q_item = {
                        "key": str(k).strip(),
                        "doi": s_doi,
                        "pdf_url": p_sug.get("pdf_url", ""),
                        "title": s_title,
                    }
                    if not any((isinstance(x, dict) and x.get("key") == str(k).strip()) or x == str(k).strip() for x in pend):
                        pend.append(q_item)
                        st.session_state["pending_dois"] = pend
                    if added:
                        st.toast(f"Added to Queue: {s_title[:30]}...", icon="📥")
                    else:
                        st.info("Already in download queue")
                    st.rerun()

            with act_c4:
                if st.button("🕸️ Citation Lineage", key="_sug_spotlight_lineage", width="stretch"):
                    st.session_state["_cg_pending_target"] = s_doi or s_title
                    vellum_pages.go("discover_citation")



