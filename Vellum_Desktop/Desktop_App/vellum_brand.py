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

APP_NAME = "Vellum by Amine"
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
<div class="header-row" style="display:flex;align-items:center;gap:12px;">
  <div style="width:36px;height:36px;background:#0B0F19;border-radius:10px;border:1px solid rgba(16,185,129,0.3);display:flex;align-items:center;justify-content:center;overflow:hidden;flex-shrink:0;">
    <svg width="22" height="22" viewBox="0 0 512 512" fill="none" xmlns="http://www.w3.org/2000/svg">
      <polygon points="112,96 186,96 256,358 206,445 112,96" fill="#10B981" />
      <polygon points="400,96 326,96 256,358 306,445 400,96" fill="#059669" />
      <polygon points="256,176 326,96 256,358 186,96" fill="#34D399" />
    </svg>
  </div>
  <div>
    <span class="header-title">{APP_NAME}</span>
    <span class="header-byline">{BYLINE}</span>
  </div>
</div>""",
        unsafe_allow_html=True,
    )




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
