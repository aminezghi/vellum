"""Shared branding: the header shown on every page and the sidebar credit.

Kept separate from the entry script so the app-level markup lives in one place
and every page inherits it, rather than each page repeating the same header and
drifting apart over time.
"""

from __future__ import annotations

import os
import signal
import threading
import time

import streamlit as st

APP_NAME = "Vellum"
BYLINE = "Academic research companion"
AUTHOR = "Amine Zouaghi"
EMAIL = "amine.zouaghi@unipr.it"
LINKEDIN = "https://www.linkedin.com/in/zouaghi-amine/"
YEAR = "2026"

CLEAR_FLAG = "_vellum_clear_pending"
ARMED_KEY = "_vellum_clear_armed"
FLASH_KEY = "_vellum_flash"
EXIT_ARMED_KEY = "_vellum_exit_armed"
EXIT_FLAG = "_vellum_exit_pending"


def header():
    """Wordmark at the top of every page, above the page's own title."""
    st.markdown(
        f"""
<div class="header-row">
  <span class="header-title">{APP_NAME}</span>
  <span class="header-byline">{BYLINE}</span>
</div>""",
        unsafe_allow_html=True,
    )


def workspace_header():
    """Render the active Research Vault and Project Switcher at the top of the sidebar."""
    try:
        import vellum_workspace as VW
        vault = VW.get_vault_dir()
        projects = VW.list_projects()
        active = VW.get_active_project_name()
        idx = projects.index(active) if active in projects else 0

        with st.sidebar:
            st.markdown(
                f"""
                <div style='padding:10px 12px; background:rgba(255,255,255,0.03); border-radius:8px; border:1px solid rgba(255,255,255,0.08); margin-bottom:10px;'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size:0.75rem; text-transform:uppercase; letter-spacing:0.06em; color:#a1a1aa; font-weight:600;'>📁 Research Vault</span>
                        <span style='font-size:0.75rem; color:#71717a;'>{len(projects)} projects</span>
                    </div>
                    <div style='font-size:0.85rem; color:#f4f4f5; font-weight:500; text-overflow:ellipsis; overflow:hidden; white-space:nowrap; margin-top:2px;' title='{str(vault)}'>{vault.name}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            sel = st.selectbox(
                "Active Project",
                projects,
                index=idx,
                label_visibility="collapsed",
                key="_vw_active_project_sel",
            )
            if sel != active:
                VW.set_active_project(sel)
                st.rerun()

            stats = VW.get_project_stats()
            st.caption(
                f"📊 **{stats['search_records']}** searched · **{stats['included']}** included · **{stats['pdfs']}** PDFs"
            )

            vh_c1, vh_c2 = st.columns([1, 1])
            with vh_c1:
                if st.button("➕ Project", key="_vw_new_p_toggle", width="stretch", help="Create new project"):
                    st.session_state["_show_new_proj_dialog"] = not st.session_state.get("_show_new_proj_dialog", False)
                    st.rerun()
            with vh_c2:
                if st.button("⚙️ Vaults", key="_vw_manage_vaults_btn", width="stretch", help="Switch or create Research Vault"):
                    st.session_state["_show_welcome_hub"] = True
                    st.rerun()

            if st.session_state.get("_show_new_proj_dialog", False):
                with st.container():
                    new_p = st.text_input("New Project Name", key="_vw_new_p_name", placeholder="e.g. Oncology_2026")
                    if st.button("Confirm Create", key="_vw_create_btn", width="stretch", type="primary"):
                        if new_p.strip():
                            VW.create_project(new_p.strip())
                            VW.set_active_project(new_p.strip())
                            st.session_state["_show_new_proj_dialog"] = False
                            st.rerun()
            st.divider()
    except Exception:
        pass


def maybe_clear():
    """Honour a pending session reset.

    Must run before any widget is created. Streamlit refuses writes to a
    session_state key that a widget owns, so wiping the state mid-render would
    fail on every widget still alive; instead the button only raises a flag and
    this clears on the fresh run, ahead of the first widget.
    """
    if st.session_state.pop(CLEAR_FLAG, False):
        st.session_state.clear()
        # Also clear persisted recent folders so the folder pickers start blank.
        try:
            import vellum_paths as VP
            VP.clear_recent()
        except Exception:
            pass
        st.session_state[FLASH_KEY] = (
            "Session cleared. Downloads, screening, folders and the shortlist "
            "are back to their defaults.")


def clear_button():
    """Two-step 'clear session' control, so it cannot be hit by accident."""
    armed = st.session_state.get(ARMED_KEY, False)
    if st.button(
            ":material/delete_sweep: Confirm clear" if armed
            else ":material/mop: Clear session",
            width="stretch", type="secondary" if armed else "tertiary",
            help=("Click again to wipe this session's data"
                  if armed else
                  "Empty this session: queue, screening, folders, shortlist. "
                  "The app keeps running.")):
        if armed:
            st.session_state.pop(ARMED_KEY, None)
            st.session_state[CLEAR_FLAG] = True
            st.rerun()
        else:
            st.session_state[ARMED_KEY] = True
            st.rerun()


def _terminate_self():
    """Signal this Streamlit process to stop.

    Runs on a timer thread rather than inline so the farewell message already
    rendered reaches the browser before the server disappears; killing the
    process mid-script would leave the tab on a bare connection error.

    SIGTERM first, so the server unwinds and releases its port. The hard exit is
    a fallback for the case where the handler never fires, otherwise a broken
    signal would leave the button looking like it did nothing.
    """
    pid = os.getpid()

    def _die():
        time.sleep(1.0)
        try:
            os.kill(pid, signal.SIGTERM)
        except Exception:
            pass
        time.sleep(2.5)
        os._exit(0)

    threading.Thread(target=_die, daemon=True).start()


def exit_button():
    """Two-step control that shuts the whole app down, not just the session.

    Closing the browser tab leaves the server running in the background, still
    holding the port. This stops the process itself, so the app is really gone.
    """
    if st.session_state.pop(EXIT_FLAG, False):
        _terminate_self()
        st.info("Shutting down. You can close this tab.",
                icon=":material/power_settings_new:")
        st.caption("Restart with `python3 -m streamlit run pdf_downloader_app.py`.")
        return

    armed = st.session_state.get(EXIT_ARMED_KEY, False)
    if st.button(
            ":material/power_settings_new: Confirm exit" if armed
            else ":material/power_settings_new: Exit app",
            width="stretch", type="secondary" if armed else "tertiary",
            help=("Click again to stop the app and release the port"
                  if armed else
                  "Stop the app completely. Any running download is "
                  "interrupted; saved files are kept.")):
        if armed:
            st.session_state.pop(EXIT_ARMED_KEY, None)
            st.session_state[EXIT_FLAG] = True
            # Stop the download worker first so it is not killed mid-write.
            # It is a daemon thread, so the process exit would reap it anyway.
            stop_event = st.session_state.get("stop_event")
            if stop_event is not None:
                try:
                    stop_event.set()
                except Exception:
                    pass
            st.rerun()
        else:
            st.session_state[EXIT_ARMED_KEY] = True
            st.rerun()


def sidebar_brand():
    """App name and copyright at the foot of the sidebar, on every page.

    Rendered after the active page so it lands below the navigation and any
    per-page sidebar controls rather than competing with them.
    """
    with st.sidebar:
        flash = st.session_state.pop(FLASH_KEY, None)
        if flash:
            st.success(flash, icon=":material/check_circle:")
        clear_button()
        exit_button()
        st.markdown(
            f"""
<div class="brand-block">
  <div class="brand-name">{APP_NAME}</div>
  <div class="brand-byline">{BYLINE}</div>
  <div class="brand-copy">&copy; {YEAR} {AUTHOR}</div>
</div>""",
            unsafe_allow_html=True,
        )
        st.markdown(
            f"""
<div class="brand-contact">
  <a href="mailto:{EMAIL}">{EMAIL}</a><span class="sep">&middot;</span>
  <a href="{LINKEDIN}" target="_blank" rel="noopener noreferrer">LinkedIn</a>
</div>""",
            unsafe_allow_html=True,
        )