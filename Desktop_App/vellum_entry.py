"""Server entry point: run Streamlit in-process from a frozen bundle.

Imported by vellum_launcher when VELLUM_SERVER=1, and runnable directly
(`python vellum_entry.py`) when working from source.
"""

from __future__ import annotations

import os
import sys


def bundle_dir() -> str:
    """Directory holding pdf_downloader_app.py, .streamlit/ and app_pages/.

    Frozen onefile: PyInstaller unpacks datas into sys._MEIPASS.
    Frozen onedir:  datas land in _internal/ next to the executable.
    macOS .app:     datas land in Contents/Resources.
    Source:         this file's own directory.
    """
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", None)
        if meipass and os.path.isfile(os.path.join(meipass, "pdf_downloader_app.py")):
            return meipass

        exe_dir = os.path.dirname(os.path.abspath(sys.executable))
        candidates = [
            os.path.join(exe_dir, "_internal"),
            os.path.join(os.path.dirname(exe_dir), "Resources"),
            exe_dir,
        ]
        for c in candidates:
            if os.path.isfile(os.path.join(c, "pdf_downloader_app.py")):
                return c
        return exe_dir

    return os.path.dirname(os.path.abspath(__file__))


def run() -> None:
    bd = bundle_dir()
    if bd not in sys.path:
        sys.path.insert(0, bd)

    # Project config (.streamlit/config.toml) is read from the working
    # directory, so start where the bundled config lives.
    try:
        os.chdir(bd)
    except OSError:
        pass

    from streamlit.web import cli as stcli

    port = os.environ.get("STREAMLIT_SERVER_PORT", "8501")
    sys.argv = [
        "streamlit", "run",
        os.path.join(bd, "pdf_downloader_app.py"),
        f"--server.port={port}",
        "--server.address=127.0.0.1",
        "--server.headless=true",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        "--browser.gatherUsageStats=false",
        "--global.developmentMode=false",
    ]
    sys.exit(stcli.main())


if __name__ == "__main__":
    run()
