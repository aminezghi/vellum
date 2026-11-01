"""
vellum_paper_actions.py — Unified 1-click Paper Action Menu across Vellum.

Renders consistent, high-leverage action buttons for any paper:
  [ 🕸️ Citation Graph ] [ ⬇️ Queue PDF ] [ 📄 Appraise ] [ ⭐ Include / Exclude ]
"""

from __future__ import annotations

from typing import Any, Dict, Optional
import streamlit as st

import vellum_workspace


def render_paper_action_bar(
    paper: Dict[str, Any],
    key_prefix: str,
    show_graph: bool = True,
    show_queue: bool = True,
    show_screen: bool = True,
    show_appraise: bool = True,
    show_direct_download: bool = False,
) -> None:
    """
    Render a clean horizontal action bar for a single paper.
    Handles cross-page navigation, queueing, direct download, and screening automatically.
    """
    doi = paper.get("doi") or ""
    title = paper.get("title") or "Untitled Paper"
    target_id = doi if doi.startswith("10.") else title

    actions = []
    if show_graph:
        actions.append("graph")
    if show_direct_download:
        actions.append("download")
    if show_queue:
        actions.append("queue")
    if show_appraise:
        actions.append("appraise")
    if show_screen:
        actions.append("screen")

    if not actions:
        return

    cols = st.columns(len(actions))
    for idx, act in enumerate(actions):
        with cols[idx]:
            if act == "graph":
                if st.button("🕸️ Citation Graph", key=f"{key_prefix}_graph", help="Map upstream foundations and downstream citations", use_container_width=True):
                    st.session_state["_cg_pending_target"] = target_id
                    st.session_state["_go_graph"] = True
                    st.rerun()
            elif act == "download":
                if st.button("⚡ Download PDF", key=f"{key_prefix}_dl_direct", help="Attempt 1-click download directly into your vault", type="primary", use_container_width=True):
                    with st.spinner("Downloading PDF..."):
                        import vellum_direct_download as VDD
                        succ, msg, fallback, path = VDD.download_single_paper_direct(paper)
                        if succ:
                            st.toast(f"✅ Downloaded: {title[:35]}...", icon="📥")
                            st.session_state["_paper_pool_needs_refresh"] = True
                            st.rerun()
                        else:
                            st.error(f"Download blocked: {msg}")
                            if fallback:
                                st.caption(f"[Open browser access]({fallback})")
            elif act == "queue":
                if st.button("⬇️ Queue PDF", key=f"{key_prefix}_queue", help="Add to active project download queue", use_container_width=True):
                    added = VDD.add_to_download_queue(paper)
                    if added:
                        st.toast(f"Added to queue: {title[:40]}...", icon="📥")
                    else:
                        st.toast("Already in download queue", icon="ℹ️")
            elif act == "appraise":
                if st.button("📄 Appraise", key=f"{key_prefix}_appraise", help="Inspect text layer evidence and methodology", use_container_width=True):
                    st.session_state["_analysis_pending_paper"] = target_id
                    st.session_state["_go_analysis"] = True
                    st.rerun()
            elif act == "screen":
                data = vellum_workspace.load_project_data()
                screened = data.get("screened", {})
                current_status = screened.get(target_id, {}).get("status", "undecided")

                if current_status == "included":
                    btn_label = "✅ Included"
                    btn_type = "primary"
                elif current_status == "excluded":
                    btn_label = "❌ Excluded"
                    btn_type = "secondary"
                else:
                    btn_label = "⭐ Include"
                    btn_type = "secondary"

                if st.button(btn_label, key=f"{key_prefix}_screen", type=btn_type, help="Toggle PRISMA systematic review screening", use_container_width=True):
                    if current_status == "included":
                        screened[target_id] = {"status": "excluded"}
                    elif current_status == "excluded":
                        screened.pop(target_id, None)
                    else:
                        screened[target_id] = {"status": "included"}
                    data["screened"] = screened
                    vellum_workspace.save_project_data(data)
                    st.rerun()
