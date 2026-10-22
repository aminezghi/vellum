"""Lightweight PDF text extraction with OCR fallback.

Why this exists
---------------
Scanned or image-only PDFs have no text layer, so ``page.get_text()`` returns
nothing and metadata extraction fails silently. This module detects that and
falls back to OCR.

Engine: the macOS Vision framework (via PyObjC). It is genuinely *light*:
no model weights to download, no system packages, no external binaries --
it uses the OCR engine already built into macOS. If Vision is unavailable the
module degrades gracefully and reports why, rather than raising.

Verified behaviour
------------------
* 200 dpi, accurate level: ~0.3-0.7 s per page.
* A text-layer PDF is read natively (no OCR) because OCR actually *degrades*
  quality on clean digital text (ligatures and kerning get mangled).
* A zero-text-layer scan yields full recovered text.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

# ── Optional imports ──────────────────────────────────────────────────────────
try:
    import pymupdf  # PyMuPDF >= 1.24 exposes the modern name
except ImportError:  # pragma: no cover
    try:
        import fitz as pymupdf
    except ImportError:
        pymupdf = None

try:
    import Quartz
    import Vision
    from CoreFoundation import CFDataCreate

    _VISION_OK = True
    _VISION_ERR = ""
except Exception as exc:  # pragma: no cover - depends on host
    _VISION_OK = False
    _VISION_ERR = f"{type(exc).__name__}: {exc}"

# Characters per page below which we assume the page is an image, not text.
CHARS_PER_PAGE_FLOOR = 120
# Confidence floor for keeping an OCR line.
MIN_CONFIDENCE = 0.30


@dataclass
class OCRResult:
    """Outcome of reading one PDF."""

    text: str = ""
    pages: int = 0
    ocr_pages: int = 0
    native_pages: int = 0
    mean_confidence: float = 0.0
    engine: str = "none"
    title: str = ""
    warnings: list = field(default_factory=list)

    @property
    def used_ocr(self) -> bool:
        return self.ocr_pages > 0

    @property
    def chars(self) -> int:
        return len(self.text)


def ocr_available() -> bool:
    """True when a real OCR engine can be used."""
    return _VISION_OK and pymupdf is not None


def ocr_backend_name() -> str:
    if pymupdf is None:
        return "unavailable (PyMuPDF not installed)"
    if not _VISION_OK:
        return f"unavailable ({_VISION_ERR})"
    return "macOS Vision"


def _set(obj, name, *args):
    """pyobjc exposes some setters with a trailing underscore; support both."""
    for candidate in (name + "_", name):
        fn = getattr(obj, candidate, None)
        if fn is not None:
            return fn(*args)
    raise AttributeError(name)


def _vision_lines(png_bytes: bytes, level: int = 1, langs=None):
    """Run Vision OCR on one encoded image.

    Returns [(text, confidence, box_height, box_top), ...]. The geometry is
    kept because bounding-box height is a usable proxy for font size, which is
    how a title is told apart from body text on a scanned page.
    """
    data = CFDataCreate(None, png_bytes, len(png_bytes))
    src = Quartz.CGImageSourceCreateWithData(data, None)
    if src is None:
        return []
    cg = Quartz.CGImageSourceCreateImageAtIndex(src, 0, None)
    if cg is None:
        return []
    req = Vision.VNRecognizeTextRequest.alloc().init()
    _set(req, "setRecognitionLevel", level)
    _set(req, "setUsesLanguageCorrection", True)
    if langs:
        _set(req, "setRecognitionLanguages", list(langs), None)
    handler = Vision.VNImageRequestHandler.alloc().initWithCGImage_orientation_options_(cg, 1, None)
    ok, _err = handler.performRequests_error_([req], None)
    if not ok:
        return []
    out = []
    for obs in req.results() or []:
        cand = obs.topCandidates_(1)
        if not cand:
            continue
        text = cand[0].string()
        conf = float(obs.confidence())
        if not text or conf < MIN_CONFIDENCE:
            continue
        box = obs.boundingBox()
        out.append((text, conf, box.size.height, box.origin.y))
    return out


def _ocr_page(page, dpi: int = 200, level: int = 1, langs=None):
    """Rasterise one page and OCR it -> (text, mean_conf, lines)."""
    # Clamp the raster so a poster-sized page cannot blow up memory.
    zoom = dpi / 72.0
    longest = max(page.rect.width, page.rect.height) or 1.0
    if longest * zoom > 4000:
        zoom = 4000.0 / longest
    pix = page.get_pixmap(matrix=pymupdf.Matrix(zoom, zoom), alpha=False)
    lines = _vision_lines(pix.tobytes("png"), level=level, langs=langs)
    if not lines:
        return "", 0.0, []
    body = "\n".join(t for t, *_ in lines)
    mean_conf = sum(c for _, c, _, _ in lines) / len(lines)
    return body, mean_conf, lines


# ── title detection ──────────────────────────────────────────────────────────
# A paper's title is simply the largest text near the top of page one. Both
# paths below measure that directly: exact point size from the text layer, or
# Vision's bounding-box height when the page has to be OCR'd.

_BOILER = re.compile(
    r"^\s*(©|copyright|all rights reserved|open access|openaccess|"
    r"creative commons|cc[\s/-]*by|license|wiley|elsevier|springer|macmillan|"
    r"taylor\s*&\s*francis|sage|oxford university press|cambridge university press|"
    r"journal|volume|vol\.|issue|issn|isbn|doi|https?://|www\.|"
    r"received|revised|accepted|published|available online|"
    r"research article|article|review|original research|"
    r"abstract|keywords?|introduction|references|appendix|"
    r"page\s*\d+|\d+|[ivxlcdm]+)\b",
    re.I,
)


def _clean_title_lines(candidates):
    """Join a run of same-size lines into one title, in reading order.

    ``candidates`` are (position, size, text) tuples where ``position`` is in
    the same units as ``size`` -- PDF points for a text layer, Vision's
    normalised box coordinates for OCR. Titles wrap onto a second line roughly
    one to two line-heights below the first, so the merge gap is expressed as
    a multiple of the title's own size rather than a fixed constant.
    """
    kept = [c for c in candidates if not _BOILER.match(c[2])]
    if not kept:
        return ""
    kept.sort(key=lambda c: c[0])
    biggest = max(c[1] for c in kept)
    band = [c for c in kept if c[1] >= biggest * 0.86]
    band.sort(key=lambda c: c[0])
    tol = biggest * 2.5
    merged, group = [], [band[0]]
    for prev, cur in zip(band, band[1:]):
        close = abs(cur[0] - prev[0]) <= tol
        same_size = biggest * 0.86 <= cur[1] <= biggest * 1.18
        if close and same_size:
            group.append(cur)
        else:
            merged.append(" ".join(g[2] for g in group))
            group = [cur]
    merged.append(" ".join(g[2] for g in group))
    title = " ".join(merged).strip()
    title = re.sub(r"\s{2,}", " ", title)
    return title.strip(" .,;:")


def title_from_text_layer(page) -> str:
    """Title from real font sizes on a page that has a text layer."""
    try:
        data = page.get_text("dict")
    except Exception:
        return ""
    height = page.rect.height or 1.0
    cands = []
    for block in data.get("blocks", []):
        if block.get("type") != 0:
            continue
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            text = "".join(s.get("text", "") for s in spans).strip()
            if not text:
                continue
            y = line.get("bbox", (0, 0, 0, 0))[1]
            if y > height * 0.55:          # ignore abstract and below
                continue
            cands.append((y, max(s.get("size", 0) for s in spans), text))
    return _clean_title_lines(cands)


def title_from_ocr(lines) -> str:
    """Title from a scanned page, using Vision bounding boxes.

    Box *height* finds the anchor line (the title is set largest), but it
    cannot reliably find the title's second line: Vision measures the glyph
    extent, so a continuation line starting with a lowercase letter comes out
    noticeably shorter and is easily confused with body text. Vertical
    adjacency is the dependable signal instead, so neighbours within about two
    line-heights of the anchor are absorbed, stopping at boilerplate or a gap.
    """
    if not lines:
        return ""
    top_limit = max(l[3] for l in lines) * 0.42
    cands = [l for l in lines if l[3] >= top_limit and not _BOILER.match(l[0])]
    if not cands:
        return ""
    anchor = max(cands, key=lambda l: l[2])
    tol = anchor[2] * 2.5
    floor = anchor[2] * 0.5

    group = [anchor]
    # absorb lines directly below the anchor (title wrapping downwards)
    for cand in sorted((c for c in cands if c[3] < anchor[3]), key=lambda c: -c[3]):
        if group[-1][3] - cand[3] > tol:
            break
        if cand[2] < floor:
            break
        group.append(cand)
    # and directly above it (masthead removed, but be safe)
    for cand in sorted((c for c in cands if c[3] > anchor[3]), key=lambda c: c[3]):
        if cand[3] - group[0][3] > tol:
            break
        if cand[2] < floor:
            break
        group.insert(0, cand)

    return re.sub(r"\s{2,}", " ", " ".join(g[0] for g in group)).strip(" .,;:")


def _needs_ocr(native_text: str) -> bool:
    return len(native_text.strip()) < CHARS_PER_PAGE_FLOOR


def read_pdf(
    path,
    max_pages: int = 40,
    ocr_scanned: bool = True,
    dpi: int = 200,
    fast: bool = False,
    force_ocr: bool = False,
    langs=None,
    progress=None,
) -> OCRResult:
    """Read a PDF, using OCR only for pages that lack a usable text layer.

    Parameters
    ----------
    path : str | Path
        PDF to read.
    max_pages : int
        Safety cap on pages processed.
    ocr_scanned : bool
        When False, image-only pages are reported but not rasterised.
    dpi : int
        Raster resolution for OCR. 200 is a good accuracy/speed balance;
        300 is slower with little gain on clean scans.
    fast : bool
        Use Vision's fast recognition level (0) instead of accurate (1).
    force_ocr : bool
        OCR every page, ignoring its text layer. Some PDFs carry a garbled or
        wrongly-encoded text layer that ``_needs_ocr`` accepts but a human
        cannot read; this bypasses the check and rasterises unconditionally.
    langs : sequence[str] | None
        Restrict recognition languages, e.g. ``["en-GB"]``.
    progress : callable | None
        Called as ``progress(done, total)`` after each page.
    """
    res = OCRResult()
    if pymupdf is None:
        res.warnings.append("PyMuPDF is not installed; cannot read PDF.")
        return res
    if not os.path.exists(path):
        res.warnings.append(f"File not found: {path}")
        return res

    try:
        doc = pymupdf.open(path)
    except Exception as exc:
        res.warnings.append(f"Could not open PDF ({type(exc).__name__}).")
        return res

    if doc.is_encrypted and not doc.authenticate(""):
        res.warnings.append("PDF is password protected.")
        doc.close()
        return res

    try:
        total = min(doc.page_count, max_pages)
        res.pages = doc.page_count
        if doc.page_count > max_pages:
            res.warnings.append(f"Stopped after {max_pages} of {doc.page_count} pages.")

        chunks, confs = [], []
        title = ""
        for i in range(total):
            page = doc[i]
            try:
                native = page.get_text() or ""
            except Exception:
                native = ""

            if not force_ocr and not _needs_ocr(native):
                res.native_pages += 1
                chunks.append(native)
                if i == 0 and not title:
                    title = title_from_text_layer(page)
            else:
                if not ocr_scanned:
                    res.warnings.append(
                        f"Page {i + 1} has no text layer and OCR is disabled."
                    )
                    continue
                if not ocr_available():
                    res.warnings.append(
                        f"Page {i + 1} needs OCR but no engine is available: "
                        f"{ocr_backend_name()}"
                    )
                    continue
                try:
                    body, conf, lines = _ocr_page(
                        page, dpi=dpi, level=0 if fast else 1, langs=langs
                    )
                except Exception as exc:
                    res.warnings.append(f"OCR failed on page {i + 1}: {type(exc).__name__}.")
                    continue
                if body:
                    res.ocr_pages += 1
                    chunks.append(body)
                    if conf:
                        confs.append(conf)
                    if i == 0 and not title:
                        title = title_from_ocr(lines)
            if progress:
                progress(i + 1, total)

        res.text = "\n\n".join(c.strip() for c in chunks if c and c.strip())
        res.mean_confidence = sum(confs) / len(confs) if confs else 0.0
        res.title = title
        res.engine = (
            "macOS Vision" if res.ocr_pages else ("text layer" if res.native_pages else "none")
        )
        if not res.text:
            res.warnings.append("No text could be extracted from this PDF.")
    finally:
        doc.close()
    return res


# ── Convenience helpers used by the app ──────────────────────────────────────

_WS = re.compile(r"[ \t ]+")


def clean_ocr_text(text: str) -> str:
    """Tidy OCR output: collapse runs of spaces and blank-line piles."""
    lines = [_WS.sub(" ", ln).strip() for ln in text.splitlines()]
    out, blank = [], 0
    for ln in lines:
        if ln:
            blank = 0
            out.append(ln)
        else:
            blank += 1
            if blank <= 1:
                out.append("")
    return "\n".join(out).strip()


def guess_doi(text: str) -> str:
    """Pull a DOI out of raw text (first page of a paper usually shows it)."""
    m = re.search(r"\b10\.\d{4,9}/[-._;()/:A-Za-z0-9]+\b", text or "")
    if not m:
        return ""
    return m.group(0).rstrip(".,;)")