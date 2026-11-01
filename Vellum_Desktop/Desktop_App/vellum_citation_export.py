"""
vellum_citation_export.py — 1-Click Export to Zotero (.ris), EndNote (.enw), and BibTeX (.bib).

Provides compliant citation formats for direct import into:
  - Zotero (via RIS or BibTeX)
  - EndNote (via Tagged ENW or RIS)
  - Mendeley & Paperpile (via RIS or BibTeX)
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import vellum_workspace as VW


def get_user_downloads_dir() -> Path:
    """Return standard user Downloads directory across platforms, supporting VELLUM_DOWNLOADS_DIR override."""
    env_dl = os.environ.get("VELLUM_DOWNLOADS_DIR")
    if env_dl:
        p = Path(env_dl).resolve()
        p.mkdir(parents=True, exist_ok=True)
        return p

    try:
        home = Path.home()
        dl = home / "Downloads"
        if dl.exists():
            return dl
        return home
    except (PermissionError, OSError, RuntimeError):
        pass

    fallback = Path(tempfile.gettempdir()) / "Downloads"
    fallback.mkdir(parents=True, exist_ok=True)
    return fallback


def save_citation_export(
    filename: str,
    content: str,
    project_name: Optional[str] = None,
) -> Tuple[Path, Optional[Path]]:
    """
    Saves citation export to:
      1) <vault>/<project>/exports/<filename>
      2) User's standard Downloads folder (<home>/Downloads/<filename>)
    Catches PermissionError gracefully and falls back to vault exports folder.
    Returns (vault_file_path, downloads_file_path).
    """
    proj_dir = VW.get_project_dir(project_name)
    export_dir = proj_dir / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    vault_path = export_dir / filename
    vault_path.write_text(content, encoding="utf-8", errors="replace")

    dl_path = None
    try:
        user_dl = get_user_downloads_dir()
        if user_dl.exists():
            target_dl = user_dl / filename
            target_dl.write_text(content, encoding="utf-8", errors="replace")
            dl_path = target_dl
    except (PermissionError, OSError):
        # Graceful fallback: downloads folder restricted, vault_path remains canonical
        dl_path = None
    except Exception:
        dl_path = None

    return vault_path, dl_path


def open_file_or_folder(target_path: Path | str) -> bool:
    """Open a file or folder in the OS native file manager or default associated application."""
    try:
        p = Path(target_path).resolve()
        if not p.exists():
            return False
        if sys.platform == "win32":
            if p.is_dir():
                subprocess.Popen(["explorer.exe", str(p)])
            else:
                os.startfile(str(p))
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", str(p)])
            return True
        else:
            subprocess.Popen(["xdg-open", str(p)])
            return True
    except Exception:
        return False


def open_folder_and_select(file_path: Path | str) -> bool:
    """Open folder in Windows Explorer and highlight the file."""
    try:
        p = Path(file_path).resolve()
        if sys.platform == "win32":
            subprocess.Popen(["explorer.exe", f"/select,{str(p)}"])
            return True
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(p)])
            return True
        return open_file_or_folder(p.parent)
    except Exception:
        return False



def _clean_str(val: Any) -> str:
    if val is None:
        return ""
    return str(val).strip()


def export_to_ris(papers: List[Dict[str, Any]]) -> str:
    """
    Generate Research Information Systems (RIS) format.
    Standard for Zotero, Mendeley, and EndNote.
    """
    entries = []
    for p in papers:
        title = _clean_str(p.get("title") or "Untitled")
        year = _clean_str(p.get("year"))
        venue = _clean_str(p.get("journal") or p.get("venue"))
        doi = _clean_str(p.get("doi"))
        abstract = _clean_str(p.get("abstract"))
        url = _clean_str(p.get("pdf_url") or p.get("landing_url") or (f"https://doi.org/{doi}" if doi else ""))

        lines = ["TY  - JOUR"]
        if title:
            lines.append(f"TI  - {title}")

        authors = p.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        for a in authors:
            if a:
                lines.append(f"AU  - {str(a).strip()}")

        if year:
            lines.append(f"PY  - {year}")
        if venue:
            lines.append(f"JO  - {venue}")
            lines.append(f"T2  - {venue}")
        if doi:
            lines.append(f"DO  - {doi}")
        if url:
            lines.append(f"UR  - {url}")
        if abstract:
            lines.append(f"AB  - {abstract}")

        keywords = p.get("keywords") or []
        if isinstance(keywords, list):
            for kw in keywords[:10]:
                if kw:
                    lines.append(f"KW  - {str(kw).strip()}")

        lines.append("ER  - \n")
        entries.append("\n".join(lines))

    return "\n".join(entries)


def export_to_endnote_enw(papers: List[Dict[str, Any]]) -> str:
    """
    Generate EndNote tagged import format (.enw).
    Directly opens in Thomson Reuters / Clarivate EndNote.
    """
    entries = []
    for p in papers:
        title = _clean_str(p.get("title") or "Untitled")
        year = _clean_str(p.get("year"))
        venue = _clean_str(p.get("journal") or p.get("venue"))
        doi = _clean_str(p.get("doi"))
        abstract = _clean_str(p.get("abstract"))
        url = _clean_str(p.get("pdf_url") or p.get("landing_url") or (f"https://doi.org/{doi}" if doi else ""))

        lines = ["%0 Journal Article"]
        if title:
            lines.append(f"%T {title}")

        authors = p.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        for a in authors:
            if a:
                lines.append(f"%A {str(a).strip()}")

        if venue:
            lines.append(f"%J {venue}")
        if year:
            lines.append(f"%D {year}")
        if doi:
            lines.append(f"%R {doi}")
        if url:
            lines.append(f"%U {url}")
        if abstract:
            lines.append(f"%X {abstract}")

        keywords = p.get("keywords") or []
        if isinstance(keywords, list):
            for kw in keywords[:10]:
                if kw:
                    lines.append(f"%K {str(kw).strip()}")

        lines.append("")
        entries.append("\n".join(lines))

    return "\n".join(entries)


def export_to_bibtex(papers: List[Dict[str, Any]]) -> str:
    """Generate standard BibTeX format (.bib)."""
    entries = []
    for idx, p in enumerate(papers):
        title = _clean_str(p.get("title") or "Untitled")
        year = _clean_str(p.get("year") or "nd")
        venue = _clean_str(p.get("journal") or p.get("venue"))
        doi = _clean_str(p.get("doi"))
        url = _clean_str(p.get("pdf_url") or p.get("landing_url") or (f"https://doi.org/{doi}" if doi else ""))

        authors = p.get("authors") or []
        if isinstance(authors, str):
            authors = [authors]
        auth_str = " and ".join(str(a) for a in authors if a) or "Anon"

        first_auth = authors[0] if authors else "Paper"
        last_name = re.sub(r"[^A-Za-z]", "", str(first_auth).split()[-1] if str(first_auth).split() else "Paper")
        cite_key = f"{last_name.lower()}_{year}_{idx+1}"

        fields = [
            ("title", f"{{{title}}}"),
            ("author", f"{{{auth_str}}}"),
            ("year", f"{{{year}}}"),
        ]
        if venue:
            fields.append(("journal", f"{{{venue}}}"))
        if doi:
            fields.append(("doi", f"{{{doi}}}"))
        if url:
            fields.append(("url", f"{{{url}}}"))

        body = ",\n".join(f"  {k} = {v}" for k, v in fields)
        entries.append(f"@article{{{cite_key},\n{body}\n}}")

    return "\n\n".join(entries) + "\n"


def render_export_bar(
    papers: List[Dict[str, Any]],
    key_prefix: str = "exp",
    label_suffix: str = "",
) -> None:
    """
    Renders 1-click citation export buttons for Zotero, EndNote, and BibTeX.
    Directly writes files to ~/Downloads and the Project Vault, provides toast notifications,
    and opens the file in Windows Explorer or default citation software.
    """
    import streamlit as st

    if not papers:
        return

    proj_name = VW.get_active_project_name()

    c1, c2, c3, _ = st.columns([1.6, 1.6, 1.6, 3.2], vertical_alignment="center")

    with c1:
        if st.button(
            f"📥 Zotero (.ris) {label_suffix}".strip(),
            use_container_width=True,
            key=f"{key_prefix}_btn_ris",
            help="Export to Zotero, Mendeley, or Paperpile",
        ):
            ris_text = export_to_ris(papers)
            fn = f"{proj_name}_Zotero.ris"
            vp, dp = save_citation_export(fn, ris_text)
            st.session_state[f"_{key_prefix}_export_info"] = {
                "name": fn,
                "vault_path": str(vp),
                "dl_path": str(dp) if dp else str(vp),
                "type": "Zotero (.ris)",
                "content": ris_text,
            }
            st.toast(f"✅ Exported {len(papers)} paper(s) to {fn}!", icon="📥")
            st.rerun()

    with c2:
        if st.button(
            f"📥 EndNote (.enw) {label_suffix}".strip(),
            use_container_width=True,
            key=f"{key_prefix}_btn_enw",
            help="Direct import into Clarivate EndNote",
        ):
            enw_text = export_to_endnote_enw(papers)
            fn = f"{proj_name}_EndNote.enw"
            vp, dp = save_citation_export(fn, enw_text)
            st.session_state[f"_{key_prefix}_export_info"] = {
                "name": fn,
                "vault_path": str(vp),
                "dl_path": str(dp) if dp else str(vp),
                "type": "EndNote (.enw)",
                "content": enw_text,
            }
            st.toast(f"✅ Exported {len(papers)} paper(s) to {fn}!", icon="📥")
            st.rerun()

    with c3:
        if st.button(
            f"📥 BibTeX (.bib) {label_suffix}".strip(),
            use_container_width=True,
            key=f"{key_prefix}_btn_bib",
            help="Export LaTeX BibTeX bibliography",
        ):
            bib_text = export_to_bibtex(papers)
            fn = f"{proj_name}.bib"
            vp, dp = save_citation_export(fn, bib_text)
            st.session_state[f"_{key_prefix}_export_info"] = {
                "name": fn,
                "vault_path": str(vp),
                "dl_path": str(dp) if dp else str(vp),
                "type": "BibTeX (.bib)",
                "content": bib_text,
            }
            st.toast(f"✅ Exported {len(papers)} paper(s) to {fn}!", icon="📥")
            st.rerun()

    # Success & Action Drawer when an export occurred
    info_key = f"_{key_prefix}_export_info"
    if info_key in st.session_state:
        info = st.session_state[info_key]
        with st.container(border=True):
            s1, s2, s3, s4 = st.columns([3, 1.3, 1.3, 0.6], vertical_alignment="center")
            with s1:
                if info.get("dl_path") and info.get("dl_path") != info.get("vault_path"):
                    st.markdown(
                        f"✅ **Saved `{info['name']}` to your Downloads folder and Project Vault!**"
                    )
                else:
                    st.markdown(
                        f"📁 **Saved `{info['name']}` to Project Vault exports** *(Downloads folder was restricted)*"
                    )
            with s2:
                if st.button("📂 Open in Explorer", key=f"{key_prefix}_open_exp_folder", width="stretch", help="Reveal file in Windows Explorer"):
                    target = info.get("dl_path") or info.get("vault_path")
                    if target:
                        open_folder_and_select(target)
            with s3:
                if st.button("🚀 Open in App", key=f"{key_prefix}_open_exp_app", width="stretch", help="Launch directly in default citation app (Zotero, EndNote, etc.)"):
                    target = info.get("dl_path") or info.get("vault_path")
                    if target:
                        open_file_or_folder(target)
            with s4:
                if st.button("✕", key=f"{key_prefix}_dismiss_exp", width="stretch", help="Dismiss"):
                    del st.session_state[info_key]
                    st.rerun()

            with st.expander("📋 View & Copy Citation Text", expanded=False):
                st.code(info.get("content", ""), language="text")

