# -*- mode: python ; coding: utf-8 -*-
"""Data files that the frozen Vellum.app must ship.

Kept in one module because the .spec and the runtime both need the same list.
"""

import os

# Modules the app imports by bare name (sys.path has the bundle directory).
MODULES = [
    "pdf_downloader_app.py",
    "vellum_analysis.py",
    "vellum_brand.py",
    "vellum_paths.py",
    "paper_analysis.py",
    "pdf_ocr.py",
    "litcheck_core.py",
    "litcheck_sources.py",
    "litcheck_ui.py",
    "researchers_core.py",
    "vellum_entry.py",
    "citation_core.py",
    "vellum_workspace.py",
    "vellum_paper_actions.py",
    "vellum_desktop.py",
    "vellum_theme.py",
    "vellum_paper_pool.py",
    "vellum_citation_export.py",
    "vellum_direct_download.py",
    "vellum_import.py",
    "vellum_pdf_viewer.py",
    "vellum_pdf_server.py",
]

# Directories whose contents are needed at runtime.
TREES = ["app_pages", "assets"]

# Streamlit reads project config from <cwd>/.streamlit/, and the server child
# process starts in the bundle directory – so ship the theme with it.
CONFIG = [(".streamlit/config.toml", ".streamlit")]

# Icons: .icns for the .app bundle, .png for PhotoImage fallback, .ico for Windows.
ICONS = ["downloader.icns", "downloader.png", "downloader.ico"]


def build_datas(here=None):
    """Build the datas list, skipping anything absent from this checkout."""
    here = here or os.path.abspath(os.getcwd())
    out = []
    for name in MODULES + ICONS:
        if os.path.isfile(os.path.join(here, name)):
            out.append((name, "."))
    for src, dest in CONFIG:
        if os.path.isfile(os.path.join(here, src)):
            out.append((src, dest))
    for tree in TREES:
        if os.path.isdir(os.path.join(here, tree)):
            out.append((tree, tree))
    return out
