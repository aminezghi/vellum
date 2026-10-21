"""
vellum_pdf_viewer.py — Vellum Interactive PDF Viewer & Citation Assistant.

Provides:
  1. PDF Document: Native Microsoft Edge / Acrobat embedded document reader streamed
     over a high-performance local localhost HTTP endpoint with byte-range support,
     plus a fallback to PyMuPDF razor-sharp continuous high-definition rendering.
  2. Text & Citations Assistant: Page-indexed verbatim text viewer with 1-click
     evidence quote generation and direct insertion into Project Synthesis Notes.
  3. Quick Launch: Open in Windows default app, open publisher DOI, or save copy.
"""

from __future__ import annotations

import base64
from pathlib import Path
from typing import Optional

import streamlit as st
import streamlit.components.v1 as components

import vellum_analysis as VA
import vellum_citation_export as VCE
import vellum_workspace as VW
from vellum_pdf_server import register_pdf_for_streaming


def _get_base64_pdf(pdf_path: Path) -> str:
    """Read PDF file and return base64 encoded string."""
    try:
        with open(pdf_path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    except Exception:
        return ""


def render_pdf_viewer(
    pdf_path: str | Path,
    height: int = 780,
    key_prefix: str = "pdf_viewer",
    show_layout_toggle: bool = False,
    doi: Optional[str] = None,
    title: Optional[str] = None,
):
    """
    Renders an in-place PDF reader:
      - 📄 PDF Document: Full native Edge/Acrobat viewer via local streaming server,
        with optional High-Definition continuous document view.
      - 📝 Text & Citations: Verbatim page text with 1-click quote insertion.
    """
    path = Path(pdf_path)
    if not path.is_file():
        st.warning(f"PDF not found on disk: `{path.name}`")
        return

    # Top Toolbar: Quick actions
    tb_c1, tb_c2, tb_c3 = st.columns([2.5, 1.2, 1.2], vertical_alignment="center")
    with tb_c1:
        st.markdown(f"**📖 `{path.name}`**")
    with tb_c2:
        if st.button(
            "📂 Open in Windows App",
            key=f"{key_prefix}_open_app_btn",
            use_container_width=True,
            help="Open in Adobe Acrobat / Edge / default system viewer",
        ):
            VCE.open_file_or_folder(path)
    with tb_c3:
        if doi and doi.strip().startswith("10."):
            st.link_button("🌐 Publisher (DOI)", f"https://doi.org/{doi.strip()}", use_container_width=True)
        else:
            with open(path, "rb") as f:
                st.download_button(
                    "💾 Save Copy",
                    data=f.read(),
                    file_name=path.name,
                    mime="application/pdf",
                    key=f"{key_prefix}_dl_btn",
                    use_container_width=True,
                )

    # 2 Clean Primary Tabs: Document Viewer vs Text & Citations
    tab_doc, tab_text = st.tabs(["📄 PDF Document", "📝 Text & Citations"])

    with tab_doc:
        _render_document_tab(path, height=height, key_prefix=key_prefix)

    with tab_text:
        _render_text_and_citations(path, key_prefix=key_prefix, title=title, doi=doi)


def _render_document_tab(path: Path, height: int, key_prefix: str):
    """Renders the document using razor-sharp continuous high-definition rendering."""
    pdf_url = register_pdf_for_streaming(path)

    # Clean top toolbar for zoom and full-screen external view
    c_info, c_action = st.columns([3, 1.2], vertical_alignment="center")
    with c_info:
        st.caption("📜 High-definition continuous reading powered by PyMuPDF. Zero browser blocking.")
    with c_action:
        if pdf_url:
            st.link_button("↗️ Full-Screen Window", pdf_url, use_container_width=True, help="Open PDF in a full Microsoft Edge browser tab")

    _render_continuous_mupdf(path, height=height, key_prefix=key_prefix)


@st.cache_data(show_spinner=False, max_entries=128)
def _get_page_image_bytes(path_str: str, page_num: int, dpi: int, mtime: float) -> bytes:
    """Cached high-DPI page rendering with PyMuPDF."""
    try:
        import pymupdf
    except ImportError:
        import fitz as pymupdf
    doc = pymupdf.open(path_str)
    try:
        page = doc[page_num]
        pix = page.get_pixmap(dpi=dpi)
        return pix.tobytes("png")
    finally:
        doc.close()


def _render_continuous_mupdf(path: Path, height: int, key_prefix: str):
    """Renders all PDF pages as a continuous, razor-sharp high-definition image stack."""
    try:
        import pymupdf
    except ImportError:
        try:
            import fitz as pymupdf
        except ImportError:
            st.error("PyMuPDF engine not available.")
            return

    try:
        doc = pymupdf.open(str(path))
    except Exception as exc:
        st.error(f"Could not open PDF with PyMuPDF: {exc}")
        return

    try:
        total = len(doc)
        if total == 0:
            st.warning("This PDF contains no pages.")
            return

        c_info, c_zoom = st.columns([3, 1.2], vertical_alignment="center")
        with c_info:
            st.markdown(f"**Document: {total} page(s)** — Continuous high-definition reading")
        with c_zoom:
            zoom_pct = st.select_slider(
                "Zoom",
                options=[80, 100, 120, 140, 160],
                value=120,
                format_func=lambda z: f"{z}%",
                key=f"{key_prefix}_mupdf_zoom",
            )

        dpi = int(96 * (zoom_pct / 100.0))
        mtime = path.stat().st_mtime

        # Render in a clean scrollable container
        with st.container(height=height):
            for i in range(total):
                img_bytes = _get_page_image_bytes(str(path), i, dpi, mtime)
                st.image(
                    img_bytes,
                    use_container_width=True,
                    caption=f"Page {i + 1} of {total}",
                )
    finally:
        doc.close()


def _render_text_and_citations(
    path: Path, key_prefix: str, title: Optional[str] = None, doi: Optional[str] = None
):
    """Renders page-indexed clean text with 1-click citation quote insertion."""
    pages = VA.page_text(path)
    if not pages:
        st.info("No digital text layer extracted. Use 'Open in Windows App' or '📄 PDF Document' to inspect this paper.")
        return

    n_pages = len(pages)
    col_p, col_filter = st.columns([1.5, 3], vertical_alignment="center")
    with col_p:
        page_idx = st.selectbox(
            "Page:",
            options=list(range(n_pages)),
            format_func=lambda i: f"Page {i + 1} of {n_pages}",
            key=f"{key_prefix}_text_page_sel",
        )
    with col_filter:
        filter_q = st.text_input(
            "Filter page text:",
            placeholder="Search keywords on this page...",
            key=f"{key_prefix}_text_filter",
        )

    page_content = pages[page_idx] if page_idx < n_pages else ""

    if filter_q.strip():
        q = filter_q.strip().lower()
        matching_lines = [l for l in page_content.splitlines() if q in l.lower()]
        display_text = "\n".join(matching_lines) if matching_lines else f"(No matches found for '{filter_q}')"
    else:
        display_text = page_content

    st.text_area(
        f"Verbatim Text — Page {page_idx + 1}:",
        value=display_text,
        height=320,
        key=f"{key_prefix}_page_text_area_{page_idx}",
    )

    # 1-Click Quote to Project Synthesis Notes
    q_col1, q_col2 = st.columns([3, 1.5], vertical_alignment="center")
    with q_col1:
        quote_snippet = st.text_input(
            "Quote to insert into Synthesis Notes:",
            value=display_text[:200].replace("\n", " ") + ("…" if len(display_text) > 200 else ""),
            key=f"{key_prefix}_quote_input",
            placeholder="Type or paste exact sentence to quote...",
        )
    with q_col2:
        if st.button("📝 Insert Quote to Notes", key=f"{key_prefix}_insert_quote_btn", type="primary", use_container_width=True):
            if quote_snippet.strip():
                ref_src = title or path.stem
                cite_line = f"\n> \"{quote_snippet.strip()}\"\n> — *{ref_src}*, Page {page_idx + 1}"
                if doi and doi.startswith("10."):
                    cite_line += f" (https://doi.org/{doi})"
                cite_line += "\n"

                curr_notes = VW.get_project_notes()
                VW.save_project_notes(curr_notes + cite_line)
                st.toast(f"Inserted quote from Page {page_idx + 1} into Project Notes!", icon="✅")
                st.rerun()
