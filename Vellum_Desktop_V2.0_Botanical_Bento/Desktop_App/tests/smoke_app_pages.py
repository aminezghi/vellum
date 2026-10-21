# -*- mode: python ; coding: utf-8 -*-
r"""In-process smoke test for the Vellum Streamlit app and every app_pages module.

Streamlit's AppTest framework executes the real script (not a mock), so an
import error or a top-level exception in any page surfaces here instead of
only appearing when a user opens that page in the browser.

Run:
    .venv\Scripts\python.exe -m pytest -o pythonpath=. tests/smoke_app_pages.py -v

or directly:
    .venv\Scripts\python.exe tests/smoke_app_pages.py
"""

from __future__ import annotations

import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(__file__))
APP_ROOT = os.path.dirname(HERE)
if APP_ROOT not in sys.path:
    sys.path.insert(0, APP_ROOT)

DEFAULT_TIMEOUT = 120


def _app_pages() -> list[str]:
    """Every page module shipped in app_pages/, in sidebar order."""
    pages_dir = os.path.join(APP_ROOT, "app_pages")
    names = []
    for fname in sorted(os.listdir(pages_dir)):
        if not fname.endswith(".py") or fname == "__init__.py":
            continue
        names.append(os.path.join("app_pages", fname))
    return names


def _run(script_path: str):
    """Execute one script under AppTest and return (at, exceptions)."""
    from streamlit.testing.v1 import AppTest

    at = AppTest.from_file(script_path, default_timeout=DEFAULT_TIMEOUT)
    at.run(timeout=DEFAULT_TIMEOUT)
    return at, list(at.exception)


def _describe(script_path: str, exceptions: list) -> str:
    lines = [f"FAIL {script_path}"]
    for exc in exceptions:
        lines.append(f"  {type(exc).__name__}: {exc.value}")
        tb = exc.stack_trace
        if tb:
            lines.append("  --- traceback ---")
            lines.extend("  " + ln for ln in str(tb).splitlines()[-25:])
    return "\n".join(lines)


def main() -> int:
    scripts = [os.path.join(APP_ROOT, "pdf_downloader_app.py")] + [
        os.path.join(APP_ROOT, p) for p in _app_pages()
    ]

    failures: list[str] = []
    for script_path in scripts:
        rel = os.path.relpath(script_path, APP_ROOT)
        try:
            at, exceptions = _run(script_path)
        except Exception:
            failures.append(_describe(rel, [sys.exc_info()[1]]))
            print(f"ERROR {rel}")
            continue

        if exceptions:
            failures.append(_describe(rel, exceptions))
            print(f"FAIL  {rel}  ({len(exceptions)} exception(s))")
        else:
            titles = [t.value for t in at.title]
            print(f"OK    {rel}  titles={titles}")

    print()
    if failures:
        print(f"=== {len(failures)} script(s) failed ===")
        for f in failures:
            print()
            print(f)
        return 1

    print(f"=== all {len(scripts)} scripts ran clean ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
