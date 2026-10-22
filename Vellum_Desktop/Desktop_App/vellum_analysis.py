"""Analysis services shared by the downloader and the Analysis page.

The heavy PDF extractors (``extract_pdf_metadata``, ``compute_file_hash``) live
in the entry script because they carry a large private helper web. Importing
the entry script from a page would re-execute the whole app, so instead the
entry script *registers* its extractors here at start-up and every page uses
them through this module. Registration happens on each run of the entry
script, before ``page.run()``, so the functions are always available.
"""

from __future__ import annotations

import os
import threading
import time
from pathlib import Path

import pandas as pd

import hashlib

# ── Extractor registry ────────────────────────────────────────────────────────
_EXTRACTORS: dict = {}


def register(*, extract_pdf_metadata=None, compute_file_hash=None,
             collect_page_text=None):
    """Publish the entry script's PDF helpers to the page modules."""
    if extract_pdf_metadata is not None:
        _EXTRACTORS["extract_pdf_metadata"] = extract_pdf_metadata
    if compute_file_hash is not None:
        _EXTRACTORS["compute_file_hash"] = compute_file_hash
    if collect_page_text is not None:
        _EXTRACTORS["collect_page_text"] = collect_page_text


def _fallback_compute_file_hash(filepath) -> str:
    """Direct SHA-256 calculation fallback when entry script is not imported."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def _fallback_page_text(pdf_path, max_pages=None) -> list[str]:
    """Direct page text extractor fallback using pymupdf/fitz/pypdf."""
    # 1. Try PyMuPDF
    try:
        import pymupdf
        doc = pymupdf.open(str(pdf_path))
        limit = len(doc) if max_pages is None else min(len(doc), max_pages)
        pages = [doc[i].get_text() or "" for i in range(limit)]
        doc.close()
        if any(p.strip() for p in pages):
            return pages
    except Exception:
        pass

    # 2. Try fitz alias
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        limit = len(doc) if max_pages is None else min(len(doc), max_pages)
        pages = [doc[i].get_text() or "" for i in range(limit)]
        doc.close()
        if any(p.strip() for p in pages):
            return pages
    except Exception:
        pass

    # 3. Try pypdf
    try:
        import pypdf
        reader = pypdf.PdfReader(str(pdf_path))
        limit = len(reader.pages) if max_pages is None else min(len(reader.pages), max_pages)
        pages = [reader.pages[i].extract_text() or "" for i in range(limit)]
        if any(p.strip() for p in pages):
            return pages
    except Exception:
        pass

    return []


def _fallback_extract_pdf_metadata(pdf_path, deep=True) -> dict:
    """Direct PDF metadata extraction fallback when entry script is not imported."""
    p = Path(pdf_path)
    size_kb = round(p.stat().st_size / 1024, 1) if p.exists() else 0.0
    text_pages = _fallback_page_text(pdf_path, max_pages=5)
    first_page = text_pages[0] if text_pages else ""
    return {
        "filename": p.name,
        "path": str(p),
        "size_kb": size_kb,
        "pages": len(_fallback_page_text(pdf_path)),
        "title": p.stem.replace("_", " "),
        "authors": [],
        "year": None,
        "abstract": first_page[:500] if first_page else "",
        "hash": _fallback_compute_file_hash(pdf_path) if p.exists() else "",
    }


def extract_pdf_metadata(pdf_path, deep=True):
    fn = _EXTRACTORS.get("extract_pdf_metadata")
    if fn is not None:
        return fn(pdf_path, deep=deep)
    return _fallback_extract_pdf_metadata(pdf_path, deep=deep)


def compute_file_hash(filepath):
    fn = _EXTRACTORS.get("compute_file_hash")
    if fn is not None:
        return fn(filepath)
    return _fallback_compute_file_hash(filepath)


def page_text(pdf_path, max_pages=None):
    """Page-indexed plain text for one PDF, or [] when unavailable."""
    fn = _EXTRACTORS.get("collect_page_text")
    if fn is not None:
        try:
            if max_pages is None:
                return list(fn(pdf_path) or [])
            return list(fn(pdf_path, max_pages=max_pages) or [])
        except Exception:
            pass
    return _fallback_page_text(pdf_path, max_pages=max_pages)


def is_ready() -> bool:
    return True


# ── Display-safe frames ───────────────────────────────────────────────────────
_META_NUMERIC = ("year", "pages", "size_kb")


def _meta_text(v):
    """Flatten one metadata cell to a display string.

    A cell may legitimately hold a list (authors, keywords), and ``pd.isna``
    returns an *array* for those, so ``v is None or pd.isna(v)`` raises
    "truth value of an array is ambiguous". Handle sequences and scalars
    separately instead.
    """
    if isinstance(v, (list, tuple, set, frozenset)):
        return "; ".join(_meta_text(x) for x in v if x is not None)
    if v is None:
        return ""
    try:
        if not pd.api.types.is_scalar(v):
            return str(v)
        if pd.isna(v):
            return ""
    except (TypeError, ValueError):
        return ""
    return str(v)


def meta_frame(meta_results):
    """Build a display-safe DataFrame from extracted metadata.

    PDF metadata is wildly inconsistent: a year may arrive as 2021, "2022",
    None or "". An object column mixing ints and strings cannot be converted
    by pyarrow, so ``st.dataframe`` raises ``ArrowInvalid`` and the table
    silently disappears. Numeric columns become float (missing -> NaN) and text
    columns str, giving every column one stable dtype.
    """
    df = pd.DataFrame(meta_results or [])
    for col in df.columns:
        if col in _META_NUMERIC:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        else:
            df[col] = df[col].map(_meta_text)
    return df


# ── Filesystem helpers ────────────────────────────────────────────────────────
def list_pdfs(directory, recursive=True):
    """Return sorted PDF paths in *directory* (non-recursive first).

    Matching is on the suffix rather than a ``*.pdf`` glob. The glob is
    case-sensitive on Linux, so a folder of ``PAPER.PDF`` files reported "no
    PDFs here" there while working on macOS and Windows -- the three platforms
    disagreeing about the same folder. ``app_pages/portfolio.py`` already used
    the case-insensitive form; the glob was the outlier.
    """
    if not directory:
        return []
    root = Path(directory).expanduser()
    if not root.exists() or not root.is_dir():
        return []
    top = [p for p in root.glob("*")
           if p.is_file() and p.suffix.lower() == ".pdf"]
    if not recursive:
        return sorted(top, key=lambda p: str(p).lower())
    nested = [p for p in root.rglob("*")
              if p.is_file() and p.suffix.lower() == ".pdf" and p.parent != root]
    return top + sorted(nested, key=lambda p: str(p).lower())


def find_duplicates(directory, recursive=False):
    """Group PDFs by content hash.

    Returns ``(files, duplicates, hash_groups)`` where *duplicates* holds every
    file after the first within each hash group.
    """
    files = []
    for f in list_pdfs(directory, recursive=recursive):
        try:
            h = compute_file_hash(f)
        except Exception:
            h = None
        if h:
            files.append({
                "filename": f.name,
                "path": str(f),
                "hash": h,
                "size_kb": f.stat().st_size / 1024,
            })

    hash_groups: dict = {}
    for item in files:
        hash_groups.setdefault(item["hash"], []).append(item)

    duplicates = []
    for group in hash_groups.values():
        if len(group) > 1:
            duplicates.extend(group[1:])

    return files, duplicates, hash_groups


def extract_one(pdf_path, deep=True):
    """Extract metadata for a single PDF, returning None on failure."""
    p = Path(pdf_path)
    try:
        meta = extract_pdf_metadata(p, deep=deep) or {}
    except Exception as exc:
        meta = {"extraction_ok": False, "extraction_error": f"{type(exc).__name__}: {exc}"}
    if not isinstance(meta, dict):
        meta = {}
    try:
        meta["filename"] = p.name
        meta["size_kb"] = p.stat().st_size / 1024
        meta["path"] = str(p)
    except OSError:
        meta["filename"] = p.name
        meta["path"] = str(p)
    return meta


def extract_all_metadata(directory, recursive=False, deep=True, progress_callback=None):
    """Extract metadata for every PDF in *directory* with optional progress reporting."""
    results = []
    pdfs = list_pdfs(directory, recursive=recursive)
    total = len(pdfs)
    for idx, p in enumerate(pdfs):
        if progress_callback:
            try:
                progress_callback(idx + 1, total, p.name)
            except Exception:
                pass
        meta = extract_one(p, deep=deep)
        if meta:
            results.append(meta)
    return results


# ── Parallel metadata watcher ─────────────────────────────────────────────────
class MetadataWatcher(threading.Thread):
    """Extract metadata from PDFs *while* the downloader is still fetching.

    The download worker already runs in its own thread, so a second thread
    polling the output directory overlaps metadata extraction with network I/O
    instead of making the user wait for a second pass at the end. Progress is
    published on the same queue the UI already drains, so the main script stays
    the only writer of session state.

    Messages posted: ``("meta_update", results)`` after every newly analysed
    file, and ``("meta_final", results)`` once on exit.
    """

    POLL_SECONDS = 1.0

    def __init__(self, directory, pq, stop_event=None, deep=True,
                 recursive=False, poll_seconds=None):
        super().__init__(daemon=True, name="vellum-metadata")
        self.directory = directory
        self.pq = pq
        self.stop_event = stop_event or threading.Event()
        self.deep = deep
        self.recursive = recursive
        if poll_seconds:
            self.POLL_SECONDS = poll_seconds
        self._seen: set = set()
        self._lock = threading.Lock()
        self.results: list = []
        self.error: str | None = None

    def snapshot(self):
        with self._lock:
            return list(self.results)

    def stop(self):
        self.stop_event.set()

    def _pending(self):
        return [p for p in list_pdfs(self.directory, recursive=self.recursive)
                if str(p) not in self._seen]

    def run(self):
        try:
            while not self.stop_event.is_set():
                for path in self._pending():
                    if self.stop_event.is_set():
                        break
                    # A file may still be mid-write; skip until it parses.
                    meta = extract_one(path, deep=self.deep)
                    if not meta or not meta.get("extraction_ok"):
                        try:
                            if path.stat().st_size == 0:
                                continue
                        except OSError:
                            continue
                    with self._lock:
                        self._seen.add(str(path))
                        self.results.append(meta)
                        snapshot = list(self.results)
                    self._put(("meta_update", snapshot))
                self.stop_event.wait(self.POLL_SECONDS)
        except Exception as exc:  # never let the watcher kill the app
            self.error = f"{type(exc).__name__}: {exc}"
        finally:
            self._put(("meta_final", self.snapshot()))

    def _put(self, message):
        if self.pq is None:
            return
        try:
            self.pq.put(message)
        except Exception:
            pass


def previous_run_metadata():
    """Read metadata left by an earlier run so the UI can offer a warm start."""
    cache = Path(
        os.path.expanduser("~/.vellum/meta_cache.json"))
    try:
        if cache.exists():
            return cache.stat().st_mtime
    except OSError:
        pass
    return None


def save_metadata_cache(directory, results):
    """Persist extracted metadata so reopening the app is not instant work."""
    import json
    cache = Path(os.path.expanduser("~/.vellum/meta_cache.json"))
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "directory": str(directory),
            "saved_at": time.time(),
            "results": results,
        }
        cache.write_text(json.dumps(payload, default=str))
        return True
    except Exception:
        return False


def load_metadata_cache(directory):
    """Return cached metadata for *directory*, or None."""
    import json
    cache = Path(os.path.expanduser("~/.vellum/meta_cache.json"))
    try:
        if not cache.exists():
            return None
        payload = json.loads(cache.read_text())
    except Exception:
        return None
    if payload.get("directory") != str(directory):
        return None
    return payload.get("results")