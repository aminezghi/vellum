"""The page registry for the Vellum desktop app.

Every screen in Vellum is a real Streamlit page with its own URL. That is not
cosmetic:

* the address bar always shows where the user is;
* the browser's Back and Forward buttons work;
* a colleague can be sent a direct link to the exact screen they need;
* the "Researchers" screen - which the manual advertises but which used to be
  unreachable - is finally reachable.

The navigation bar itself stays a 8-segment control over *sections*, and a
section may hold more than one screen. That keeps the information architecture
the users already know while giving each screen its own address.

The renderers are imported lazily. A page whose optional dependency is missing
must not be able to stop the other pages from loading, and importing eleven
modules at start-up would make the app slow for no benefit.
"""

from __future__ import annotations

from typing import Callable, Dict, List, Optional

import streamlit as st

# ── Section definitions ──────────────────────────────────────────────────────
# (section label, [(url_path, page title, icon, renderer)])
#
# The renderer is a zero-argument callable that draws the screen.

def _render_overview() -> None:
    from app_pages import project_overview
    project_overview.render()


def _render_literature() -> None:
    import litcheck_ui
    litcheck_ui.render()


def _render_citation() -> None:
    from app_pages import citation_graph
    citation_graph.render()


def _render_screening() -> None:
    from app_pages import screening
    screening.render()


def _render_paper_pool() -> None:
    import vellum_workspace as VW
    import vellum_paper_pool as VPP
    data = VW.load_project_data()
    VPP.render_paper_pool(data.get("search_records", []))


def _render_methodology() -> None:
    from app_pages import analysis
    analysis.render()


def _render_export() -> None:
    from app_pages import export_center
    export_center.render()


def _render_notes() -> None:
    from app_pages import notes
    notes.render()


def _render_researchers() -> None:
    from app_pages import researchers
    researchers.render()


def _render_guide() -> None:
    from app_pages import help_page
    help_page.render()


SECTIONS: List[dict] = [
    {
        "label": "🏠 Overview",
        "pages": [
            ("overview", "Project Overview", "🏠", _render_overview),
        ],
    },
    {
        "label": "🔍 Discover",
        "pages": [
            ("discover_literature", "Literature Search", "🔍", _render_literature),
            ("discover_citation", "Citation Network", "🕸️", _render_citation),
        ],
    },
    {
        "label": "🧪 Screening",
        "pages": [
            ("screening", "Screening", "🧪", _render_screening),
        ],
    },
    {
        "label": "📚 Library",
        "pages": [
            ("library_pool", "Unified Paper Pool", "📚", _render_paper_pool),
            ("library_downloader", "PDF Downloader", "📥", None),  # supplied by the entrypoint
        ],
    },
    {
        "label": "🔬 Evidence",
        "pages": [
            ("evidence_methodology", "Methodology & Appraisal", "🔬", _render_methodology),
            ("evidence_export", "Export Center", "📦", _render_export),
        ],
    },
    {
        "label": "📝 Notes",
        "pages": [
            ("notes", "Notes", "📝", _render_notes),
        ],
    },
    {
        "label": "🔖 Researchers",
        "pages": [
            ("researchers", "Researchers", "🔖", _render_researchers),
        ],
    },
    {
        "label": "📖 Guide & FAQ",
        "pages": [
            ("guide", "Guide & FAQ", "📖", _render_guide),
        ],
    },
]

# The page that a section opens by default.
DEFAULT_PAGE: Dict[str, str] = {
    section["label"]: section["pages"][0][0] for section in SECTIONS
}

# url_path -> section label
SECTION_OF: Dict[str, str] = {
    page[0]: section["label"]
    for section in SECTIONS
    for page in section["pages"]
}

# url_path -> page title
TITLE_OF: Dict[str, str] = {
    page[0]: page[1]
    for section in SECTIONS
    for page in section["pages"]
}

# The created st.Page objects, filled in by build().
PAGES: Dict[str, "st.Page"] = {}

# The screen the app starts on when nothing else is requested.
HOME = "overview"


def build(overrides: Optional[Dict[str, Callable[[], None]]] = None) -> List["st.Page"]:
    """Create the st.Page objects and return them for st.navigation().

    Parameters
    ----------
    overrides:
        Renderers supplied by the entrypoint for screens whose code lives
        there (the PDF downloader).

    Returns
    -------
    list of st.Page
    """
    import vellum_theme as VT

    overrides = overrides or {}
    pages: List[st.Page] = []
    PAGES.clear()

    for section in SECTIONS:
        for url_path, title, icon, renderer in section["pages"]:
            fn = overrides.get(url_path, renderer)
            if fn is None:
                continue

            def _make(url_path=url_path, fn=fn):
                def _draw() -> None:
                    # The navigation bar is drawn by the page itself so that it
                    # always sits above the content, whichever page is open.
                    VT.render_top_nav(url_path)
                    fn()

                return _draw

            page = st.Page(_make(), title=title, icon=icon, url_path=url_path)
            PAGES[url_path] = page
            pages.append(page)

    return pages


def go(url_path: str) -> None:
    """Navigate to another screen.

    Falls back to the legacy session-state handovers when the page registry
    has not been built yet (for example when a page module is exercised on
    its own by the smoke test).
    """
    page = PAGES.get(url_path)
    if page is not None:
        st.switch_page(page)
        return

    # No registry: fall back to the handover flags the pages have always used.
    section = SECTION_OF.get(url_path, "")
    mapping = {
        "overview": ("overview", None),
        "discover_literature": ("discover", "Literature Search"),
        "discover_citation": ("discover", "Citation Network"),
        "screening": ("screening", None),
        "library_pool": ("library", "Unified Paper Pool"),
        "library_downloader": ("library", "PDF Downloader"),
        "evidence_methodology": ("evidence", "Methodology & Appraisal"),
        "evidence_export": ("evidence", "Export Center"),
        "notes": ("notes", None),
        "researchers": ("researchers", None),
        "guide": ("guide", None),
    }
    tab, sub = mapping.get(url_path, (None, None))
    if tab is None:
        return
    st.session_state["_active_tab"] = tab
    if sub:
        st.session_state[f"_{tab}_subview"] = sub
    st.rerun()


def section_of(url_path: str) -> str:
    """The section label a screen belongs to."""
    return SECTION_OF.get(url_path, "")
