# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Vellum (Windows) — high-performance onedir desktop distribution."""

import os
import sys

sys.path.insert(0, os.path.abspath("."))
from vellum_packaging import build_datas

from PyInstaller.utils.hooks import collect_all, copy_metadata


def safe_copy_metadata(pkg):
    try:
        return copy_metadata(pkg)
    except Exception:
        return []


datas, binaries, hiddenimports_collected = collect_all("streamlit")

for pkg in ["pypdf", "pymupdf", "curl_cffi", "DrissionPage", "webview", "clr_loader", "pythonnet", "sklearn", "scipy"]:
    try:
        p_datas, p_binaries, p_hidden = collect_all(pkg)
        datas += p_datas
        binaries += p_binaries
        hiddenimports_collected += p_hidden
        datas += safe_copy_metadata(pkg)
    except Exception as e:
        print(f"collect_all {pkg} warning:", e)

datas += safe_copy_metadata("streamlit")
datas += safe_copy_metadata("requests")
datas += safe_copy_metadata("cloudscraper")
datas += safe_copy_metadata("beautifulsoup4")
datas += safe_copy_metadata("pywebview")
datas += safe_copy_metadata("webview")
datas += safe_copy_metadata("sklearn")
datas += safe_copy_metadata("scipy")
datas += build_datas()

hiddenimports = [
    "streamlit", "streamlit.web", "streamlit.web.cli",
    "streamlit.runtime", "streamlit.runtime.scriptrunner",
    "streamlit.runtime.scriptrunner.magic_funcs",
    "streamlit.runtime.scriptrunner.script_runner",
    "streamlit.runtime.state", "streamlit.runtime.caching",
    "streamlit.runtime.uploaded_file_manager",
    "streamlit.runtime.secrets", "streamlit.runtime.pages_manager",
    "streamlit.elements", "streamlit.components.v1",
    "altair", "narwhals", "narwhals.stable.v1",
    "pandas", "pandas._libs", "numpy", "pyarrow",
    "sklearn", "sklearn.feature_extraction", "sklearn.feature_extraction.text", "sklearn.naive_bayes", "scipy",
    "requests", "bs4", "cloudscraper", "curl_cffi", "curl_cffi.requests", "DrissionPage",
    "urllib3", "certifi", "charset_normalizer",
    "zipfile", "threading", "queue", "pathlib", "tempfile",
    "signal", "io", "importlib", "importlib.metadata",
    "click", "toml", "tomllib", "PIL", "PIL.Image", "PIL.IcoImagePlugin",
    "pystray", "pystray._win32",
    "pydeck", "rich",
    "tkinter", "tkinter.font", "tkinter.ttk", "tkinter.messagebox",
    "subprocess", "webbrowser", "hmac", "hashlib", "uuid", "base64",
    "pypdf", "pymupdf", "fitz",
    "paper_analysis", "pdf_ocr", "vellum_analysis", "vellum_paths",
    "litcheck_core", "litcheck_sources", "litcheck_ui", "researchers_core",
    # Every app_pages module must be listed explicitly. Several are reached
    # through importlib.import_module(), which PyInstaller cannot detect
    # statically, so omitting them ships a frozen app with dead pages.
    "app_pages",
    "app_pages.analysis", "app_pages.citation_graph", "app_pages.export_center",
    "app_pages.help_page", "app_pages.library", "app_pages.notes",
    "app_pages.project_overview", "app_pages.researchers", "app_pages.screening",
    "app_pages.welcome_hub",
    "vellum_entry", "citation_core", "vellum_workspace", "vellum_paper_actions",
    "vellum_theme", "vellum_paper_pool", "vellum_citation_export", "vellum_direct_download",
    "vellum_import", "vellum_pdf_viewer", "vellum_pdf_server",
    "webview", "clr_loader", "pythonnet", "clr",
] + hiddenimports_collected

a = Analysis(
    ["vellum_desktop.py"],
    pathex=["."],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=["."],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="Vellum",
    debug=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="downloader.ico",
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="Vellum",
)
