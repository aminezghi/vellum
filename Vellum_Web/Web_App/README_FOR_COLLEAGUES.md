# 🌿 Vellum Web App
## Dedicated Academic Research Studio — User & Developer Manual

> **Software Version:** 2.1.0  
> **Author & Lead System Architect:** Amine Zouaghi  
> **Target Platform:** Cross-platform (Windows, macOS, Linux)  
> **Runtime Environment:** Next.js 16 (Turbopack) / React 19 / Node.js 18+  
> **Host & Port:** `http://localhost:3002`  
> **License:** 100% Free & Open-Access Academic Tool (MIT License)

---

### 1. Executive Summary

This package is the **dedicated web application of Vellum by Amine**. It provides a unified, local-first web research workstation.

It unites academic tools into a single, cohesive local-first interface:
1. **Connected Papers Interactive Citation Graph**: Force-directed canvas simulation (Coulomb-Hooke physics) showing origin halo rings, citation-scaled nodes, continuous year gradients, and dedicated **Prior Works** / **Derivative Works** exploratory lists.
2. **Machine-Learning Title & Abstract Screening**: Active-learning ranking using TF-IDF vectorization and Naive Bayes probability priors with live stopping curves and multi-source deduplication.
3. **Clause-by-Clause Boolean Search**: Visual clause builder supporting `WHERE`, `AND`, `OR`, `NOT`, and direct index mapping (`[Title/Abstract]`, `au:`, `year:`, `topic:`).
4. **Multi-Tier Batch PDF Downloader**: High-speed binary PDF downloader resolving across Unpaywall, Open Access repositories, and Semantic Scholar with paywall-trapping safeguards.
5. **Grounded Tri-Pane Systematic Notebooks**: Local-first synthesis canvas with client-side IndexedDB persistence, verbatim claim grounding, and citation formatting.

---

### 2. System Requirements & Prerequisites

#### Hardware Requirements
- **CPU:** Dual-Core x86_64 or ARM64 processor (Intel Core i3+, AMD Ryzen, or equivalent).
- **RAM:** 4 GB minimum (8 GB recommended for large candidate screening datasets).
- **Storage:** ~350 MB disk space for the application and dependencies.
- **Display:** 1280 × 800 minimum; 1920 × 1080 (Full HD) recommended for the Tri-Pane Document Reader.

#### Software Prerequisites
- **Operating System:** Windows 10/11, macOS, or Linux.
- **Node.js Runtime:** **Node.js 18.0.0 or higher** (LTS version 20+ strongly recommended) from **[https://nodejs.org](https://nodejs.org)**.
- **Web Browser:** Any modern web browser (Google Chrome, Microsoft Edge, Brave, or Mozilla Firefox).

#### Network & Port Access
- **Local Port:** Permitted local connections on port `3002` (`http://localhost:3002`).
- **Outbound HTTPS (Port 443):** Required to fetch academic metadata from OpenAlex, arXiv, Crossref, and Semantic Scholar APIs.

---

### 3. Quick-Start Guide (How to Run)

1. **Launch the Web App:**
   Double-click `START_VELLUM_WEB.bat` (Windows) or run `npm run dev` in this directory.
2. **Open in Browser:**
   Navigate to `http://localhost:3002`.

---

*Vellum Web — Designed and architected for academic researchers, systematic review teams, and laboratory investigators.*
