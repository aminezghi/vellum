# ADR 0001: Local-First Zero-Telemetry Architecture

## Context
Vellum is designed for researchers, academics, clinicians, and investigative scholars who frequently handle pre-publication manuscripts, sensitive clinical data, or competitive patent research. Cloud-hosted research tools or services that send user queries or document contents to centralized telemetry backends represent an unacceptable privacy leak.

## Decision
1. **Zero External Document Transfer**: All PDF parsing, metadata extraction, regex lexicons, section attribution, and text mining execute strictly on the user's local machine via Python standard libraries and local C-extensions (`pypdf`, `fitz`, `pdfplumber`).
2. **Opt-in Public API Lookups Only**: The only network requests made by Vellum are directly initiated by the user to public academic metadata APIs (OpenAlex, Crossref, Europe PMC, PubMed, arXiv, Semantic Scholar, DataCite, DOAJ, CORE, Unpaywall).
3. **No Analytics or Telemetry**: No tracking cookies, Google Analytics, telemetry pingbacks, or third-party phone-home calls are permitted anywhere in Vellum.

## Consequences
- Total privacy and compliance with institutional ethics boards and GDPR/HIPAA.
- Offline functionality for library management and paper analysis once documents are downloaded.
- Requires local CPU/RAM for PDF text mining.
