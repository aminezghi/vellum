# ADR 0002: Deep Modules Over UI-Coupled Extractors

## Context
Originally, PDF metadata extraction (`extract_pdf_metadata`, `compute_file_hash`, `collect_page_text`) resided directly within `pdf_downloader_app.py`. Because `pdf_downloader_app.py` is the top-level Streamlit entry script, importing it from other pages or external test runners executed the full Streamlit UI lifecycle or triggered circular dependency issues. A global `_EXTRACTORS` runtime registry was introduced as a workaround in `vellum_analysis.py`, but this raised runtime errors whenever methods were invoked without a preceding Streamlit initialization.

## Decision
1. **Clean Seams for Business Logic**: Decouple pure computation (PDF text extraction, hashing, lexical scanning, bibliographic parsing) into standalone, headless modules with clear public interfaces (`vellum_analysis.py`, `paper_analysis.py`, `litcheck_core.py`, `citation_core.py`).
2. **Autonomous Fallback**: `vellum_analysis.py` must not depend strictly on registration by `pdf_downloader_app.py`. If invoked headlessly, it must provide built-in fallbacks using standard local PDF engines (`pypdf`, `fitz`, or `pdfplumber`).
3. **Small Public Surface**: UI components call only high-level, leverage-rich functions (e.g., `appraise_paper(path)` or `resolve_seed(query)`), which return clean data dictionaries or dataclasses rather than mutating UI state.

## Consequences
- Every domain function is directly unit-testable without spinning up a Streamlit server.
- Elimination of `RuntimeError: PDF extractor not registered`.
- Simplification of page scripts (`app_pages/analysis.py`, `app_pages/library.py`).
