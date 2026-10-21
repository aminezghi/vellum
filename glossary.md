# Vellum Domain Glossary

This glossary defines the shared domain vocabulary for **Vellum**, an offline-first academic research workbench. All modules, interfaces, tests, and documentation must adhere to these terms.

---

## 1. Discovery & Search

- **Discovery Record**: A standardized metadata dictionary representing an academic work found across bibliographic sources (OpenAlex, Crossref, Europe PMC, PubMed, arXiv, Semantic Scholar, DataCite, DOAJ, CORE). Contains normalized fields (`doi`, `title`, `authors`, `year`, `abstract`, `pdf_url`, `is_oa`, `sources`).
- **Unified Boolean Query**: An abstract Boolean search expression (`Concept A AND Concept B NOT Concept C`) constructed visually or via raw syntax.
- **Database Query Adapter**: A translator that maps a Unified Boolean Query into the native syntax of a target bibliographic engine (e.g., PubMed MeSH syntax vs. OpenAlex filter syntax vs. Crossref search terms).
- **Hit**: A record reported or returned by an external bibliographic search engine.
- **Deduplication Seam**: The boundary where records from multiple heterogeneous sources are consolidated into canonical records using DOI exact-match and year-constrained title fuzzy matching.
- **PRISMA Accounting**: Tracking flow counts (Identification, Screening, Eligibility, Inclusion) for systematic review compliance.

---

## 2. Citation Networks

- **Seed Paper**: The focal academic work chosen as the starting origin for citation lineage exploration. Identified by DOI, OpenAlex ID (`W...`), or title query.
- **Citation Neighborhood**: The localized graph surrounding a Seed Paper, bounded by a specified depth and node count limit.
- **Upstream Foundations (References)**: Works cited *by* the seed paper. Represent prior art, methodologies, and theoretical foundations.
- **Downstream Derivatives (Citations)**: Works citing *the* seed paper. Represent subsequent applications, extensions, critiques, and follow-ups.
- **Cross-Connection**: A citation link between two non-seed nodes already present in the neighborhood.
- **Graph Node**: A vertex in the citation graph carrying paper metadata (title, year, venue, citation count, OA status, type).
- **Graph Link**: A directed edge `source -> target` representing a bibliographic citation (`cites`).

---

## 3. Collection & Download

- **Download Task**: A queued item consisting of a target paper, resolved PDF URLs (direct OA, Unpaywall, landing page), destination filename, and execution status (`pending`, `downloading`, `completed`, `failed`).
- **PDF Resolution**: The multi-tiered cascade that attempts to discover open-access full-text PDFs:
  1. Direct source URL (e.g., PubMed Central, arXiv).
  2. Unpaywall DOI lookup.
  3. Publisher open-access landing page scraping.
- **Deduplicated Storage**: Local storage in the user's chosen folder ensuring papers are stored with clean, collision-free filenames (`Author_Year_Title.pdf`) and verified by SHA-256 hash.

---

## 4. Appraisal & Evidence Analysis

- **Evidence-Linked Appraisal**: Transparent extraction of methodological characteristics from a PDF where every finding is directly paired with the exact textual snippet and page number where it occurred.
- **Evidence Span**: A verbatim excerpt extracted from a PDF's text layer with page coordinates, verifying a specific methodological assertion.
- **Data Modality**: The physical or empirical nature of the study's data (e.g., Survey, Physiological Measures, Neuroimaging, Transactional Logs, Genomic Sequencing).
- **Measurement Scale**: The statistical nature of the variables (Nominal, Ordinal, Interval, Ratio, Continuous, Categorical).
- **Causality Bound**: Verification of whether causal language ("causes", "leads to", "impacts") is supported by an experimental or longitudinal study design, or if observational claims remain appropriately hedged.
- **Front Matter / Bibliography Zone**: Excluded regions of a PDF (title page, author affiliations, references list) to prevent false-positive method attribution.

---

## 5. Architectural Terms (Codebase Design)

- **Deep Module**: A module with a small, cohesive public interface hiding substantial, robust implementation.
- **Seam**: The public boundary of a module where callers and automated tests interact with it without peering into internals.
- **Adapter**: A component that satisfies an interface at a seam (e.g., `OpenAlexAdapter`, `PubMedAdapter`).
- **Leverage**: Capability provided to callers per unit of interface learned.
- **Locality**: Concentration of bug fixes, optimizations, and invariants within a single module rather than dispersed across UI callers.
- **Staging State**: A temporary session state holding user intent before the corresponding UI widget is instantiated, preventing lifecycle mutation errors.
