"""
app_pages/library.py — Consolidated Library Page Shim.

In Vellum V2.1, local PDF browsing and project records have been unified into
vellum_paper_pool.py (Unified Paper Pool). This module delegates cleanly to
the unified paper pool for backwards compatibility.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import vellum_paper_pool as VPP
import vellum_workspace as VW


def render() -> None:
    """Render the Unified Paper Pool for the active project."""
    data = VW.load_project_data()
    papers = data.get("search_records", [])
    VPP.render_paper_pool(papers)