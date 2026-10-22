"""Library page: read the PDFs already on this computer.

Separate from the downloader on purpose — this page never touches the network.
It browses a real folder (the system's native chooser where one exists, or the
built-in manual browser), lists the PDFs inside, previews them with the native
PDF viewer, and extracts text, metadata and OCR on demand.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import vellum_analysis as VA  # noqa: E402
import vellum_paths as VP  # noqa: E402


def _pdf_rows(folder):
    """Describe every PDF so the table can show size, pages and title."""
    rows = []
    for p in VA.list_pdfs(folder, recursive=True):
        try:
            size = p.stat().st_size
        except OSError:
            size = 0
        rows.append({
            "name": p.name,
            "path": str(p),
            "size_kb": size / 1024,
            "folder": str(p.parent),
        })
    return pd.DataFrame(rows)


def preview_pdf(path, height=760):
    """Show an interactive PDF reader with continuous scroll, zoom, search and text citation modes."""
    import vellum_pdf_viewer as VPV
    VPV.render_pdf_viewer(path, height=height, key_prefix="lib_pdf_viewer")



def render():
    st.subheader("Library")
    st.caption("Open PDFs you already have on this computer. Nothing here "
               "reaches the network — browsing, preview and text extraction all "
               "run locally.")

    if not VA.is_ready():
        st.warning("PDF extractors are not registered yet — reload the app.")

    # ── Choose a source ─────────────────────────────────────────────────────────
    source = st.segmented_control(
        "Source", ["Browse folders", "Upload files"],
        default="Browse folders", label_visibility="collapsed")

    folder = None
    uploads = []

    if source == "Browse folders":
        import vellum_workspace as VW
        active_papers_dir = str(VW.get_project_dir() / "papers")
        default_folder = st.session_state.get("_unified_corpus_dir") or st.session_state.get("out_dir") or active_papers_dir
        folder = VP.render_folder_picker(
            "Library folder", key="lib_folder",
            default=default_folder, recursive=True)
        if folder and not VP.pdf_count(folder, recursive=True):
            st.info("No PDFs in this folder (searching subfolders too).")
    else:
        uploads = st.file_uploader(
            ":material/upload_file: Upload PDFs", type=["pdf"],
            accept_multiple_files=True,
            help="Uploaded files live in memory for this session only.")
        if not uploads:
            st.info("Upload one or more PDFs to read them here.")
            # st.stop() aborts the whole script in Streamlit 1.64 (it requests a
            # stop rather than raising), which would also skip the app-level
            # signature. These pages are functions, so returning is equivalent.
            return

    # ── Build the file list ─────────────────────────────────────────────────────
    if source == "Browse folders":
        if not folder:
            # st.stop() aborts the whole script in Streamlit 1.64 (it requests a
            # stop rather than raising), which would also skip the app-level
            # signature. These pages are functions, so returning is equivalent.
            return
        paths = [Path(p) for p in VA.list_pdfs(folder, recursive=True)]
        if not paths:
            # st.stop() aborts the whole script in Streamlit 1.64 (it requests a
            # stop rather than raising), which would also skip the app-level
            # signature. These pages are functions, so returning is equivalent.
            return
    else:
        paths = []
        import tempfile
        tmp = Path(tempfile.gettempdir()) / "vellum_uploads"
        tmp.mkdir(parents=True, exist_ok=True)
        for f in uploads:
            target = tmp / f.name
            target.write_bytes(f.getvalue())
            paths.append(target)
        folder = str(tmp)

    total_mb = sum(p.stat().st_size for p in paths if p.exists()) / 1_048_576
    c1, c2, c3 = st.columns(3)
    c1.metric("PDFs", len(paths))
    c2.metric("Size", f"{total_mb:.1f} MB")
    c3.metric("Folder", Path(folder).name or folder)

    # ── Filters ─────────────────────────────────────────────────────────────────
    f1, f2 = st.columns([2, 3])
    with f1:
        needle = st.text_input("Filter by name", placeholder="substring…",
                               label_visibility="collapsed")
    with f2:
        subfolders = sorted({str(p.parent) for p in paths})
        scope = st.selectbox("Folder", ["All folders"] + subfolders,
                             label_visibility="collapsed")

    shown = paths
    if scope != "All folders":
        shown = [p for p in shown if str(p.parent) == scope]
    if needle.strip():
        low = needle.strip().lower()
        shown = [p for p in shown if low in p.name.lower()]

    if not shown:
        st.info("No PDFs match that filter.")
        # st.stop() aborts the whole script in Streamlit 1.64 (it requests a
        # stop rather than raising), which would also skip the app-level
        # signature. These pages are functions, so returning is equivalent.
        return

    # ── File table ──────────────────────────────────────────────────────────────
    df = _pdf_rows(str(folder))
    if scope != "All folders":
        df = df[df["folder"] == scope]
    if needle.strip():
        low = needle.strip().lower()
        df = df[df["name"].str.lower().str.contains(low, regex=False)]

    st.dataframe(
        df.sort_values("name"), width="stretch", hide_index=True, height=280,
        column_config={
            "name": st.column_config.TextColumn("File", width="large"),
            "folder": st.column_config.TextColumn("Folder", width="medium"),
            "size_kb": st.column_config.NumberColumn("KB", format="%.0f"),
        })

    # ── Read one PDF ────────────────────────────────────────────────────────────
    # Options are filenames, not paths: full paths are unreadable in the list and
    # wrap badly. Same-named files in different folders get their folder added.
    labels: dict[str, Path] = {}
    for p in shown:
        name = p.name
        if name in labels:
            name = f"{p.parent.name}/{p.name}"
        labels[name] = p
    picked = st.selectbox("Open a PDF", list(labels), label_visibility="collapsed",
                          key="lib_pick")
    target = labels[picked]

    ACTIONS = (
        ("preview", ":material/visibility: Preview"),
        ("text", ":material/notes: Extract text"),
        ("meta", ":material/psychology: Extract metadata"),
        ("ocr", ":material/scanner: OCR scanned pages"),
    )

    # The chosen action lives in session state rather than a button's return
    # value, because paging through a preview calls st.rerun() and would
    # otherwise discard the flag. It deliberately outlives a change of file:
    # with Preview active, picking another PDF just shows that PDF, which is
    # what a reader expects. One st.click on the table row is not needed.
    action = st.session_state.get("lib_action")

    action_cols = st.columns([1] * len(ACTIONS) + [1])
    for col, (name, label) in zip(action_cols, ACTIONS):
        with col:
            if st.button(label, width="stretch", key=f"lib_do_{name}",
                         type="primary" if action == name else "secondary"):
                st.session_state["lib_action"] = name
                action = name
    with action_cols[-1]:
        if st.button(":material/close: Close", width="stretch",
                     disabled=action is None):
            st.session_state.pop("lib_action", None)
            action = None

    if not action:
        return

    st.divider()
    st.markdown(f"**{target.name}**")

    if action == "preview":
        preview_pdf(target)

    if action == "text":
        import pdf_ocr as O
        with st.status("Reading text…", expanded=False) as status:
            result = O.read_pdf(target)
        status.update(label="Done", state="complete")
        meta = [("Pages", result.pages),
                ("Text-layer pages", result.native_pages),
                ("OCR pages", result.ocr_pages),
                ("Characters", f"{result.chars:,}"),
                ("Engine", result.engine)]
        cols = st.columns(len(meta))
        for col, (label, value) in zip(cols, meta):
            col.metric(label, value if value is not None else "—")
        if result.warnings:
            st.caption(" · ".join(str(w) for w in result.warnings))
        if result.text.strip():
            st.text_area("Extracted text", result.text[:200_000], height=380,
                         disabled=True, label_visibility="collapsed")
            st.download_button(":material/download: Download text",
                               result.text.encode("utf-8"),
                               file_name=f"{target.stem}.txt",
                               mime="text/plain", width="content")
        else:
            st.info("No text found. Try the OCR button — this looks like a scan.")

    if action == "meta":
        with st.status("Extracting metadata…", expanded=False) as status:
            meta = VA.extract_one(target, deep=True) or {}
        status.update(label="Done", state="complete")
        st.session_state["lib_meta"] = meta
        rows = [{"field": k.replace("_", " "),
                 "value": (", ".join(map(str, v)) if isinstance(v, (list, tuple))
                           else ("" if v is None else str(v)))}
                for k, v in meta.items()
                if v not in (None, "", [], {}) and k not in ("path",)]
        st.dataframe(pd.DataFrame(rows), width="stretch", hide_index=True,
                     height=420, column_config={
                         "field": st.column_config.TextColumn("Field", width="small"),
                         "value": st.column_config.TextColumn("Value", width="large")})

    if action == "ocr":
        import pdf_ocr as O
        # Check the engine *before* starting. Force-OCR sends every page down the
        # OCR branch, so with no engine each page is skipped and the result is
        # empty -- the run used to finish reporting "0 pages OCR'd, 0
        # characters" with no explanation, which reads like a broken file rather
        # than a missing capability.
        if not O.ocr_available():
            st.error(
                f"No OCR engine is available on this computer — {O.ocr_backend_name()}.")
            st.markdown(
                "OCR here uses the **macOS Vision** framework, which exists only on "
                "macOS. On Windows and Linux the rest of the app works normally; "
                "only text recovery from scanned pages is unavailable.\n\n"
                "To read a scan on those systems, run OCR beforehand and drop the "
                "resulting searchable PDF into this folder:\n"
                "- **Tesseract** — `ocrmypdf in.pdf out.pdf`\n"
                "- **Windows** — PowerTrix or the free Tesseract installer")
            return
        with st.status("Running OCR on pages without text…",
                       expanded=True) as status:
            result = O.read_pdf(target, force_ocr=True)
        status.update(label="Done", state="complete")
        st.write(f"**{result.ocr_pages}** page(s) OCR'd, "
                 f"**{result.chars:,}** characters, engine **{result.engine}**.")
        if result.text.strip():
            st.text_area("OCR text", result.text[:200_000], height=380,
                         disabled=True, label_visibility="collapsed")
            st.download_button(":material/download: Download OCR text",
                               result.text.encode("utf-8"),
                               file_name=f"{target.stem}_ocr.txt",
                               mime="text/plain", width="content")
        else:
            st.info("OCR produced no text. The pages may be blank or the scan too "
                    "poor to read.")

    # ── Send to the downloader's metadata view ──────────────────────────────────
    if st.session_state.get("lib_meta") and st.session_state["lib_meta"].get("path") == str(target):
        st.divider()
        st.download_button(
            ":material/download: Download metadata row (CSV)",
            VA.meta_frame([st.session_state["lib_meta"]]).to_csv(index=False).encode("utf-8"),
            file_name=f"{target.stem}_metadata.csv", mime="text/csv",
            width="content")