# VELLUM DESKTOP V2.0 — FERNLY BOTANICAL BENTO EDITION
**Academic Literature Suite & Systematic Review Workbench**  
*Author: Amine Zouaghi (amine.zouaghi@unipr.it) | University of Parma*  
*Local-First • Zero Telemetry • 100% Privacy-Preserving*

---

## 🚀 Quick Start (1-Click Run)

To start Vellum Desktop V2.0 on any Windows computer:
1. Double-click **`CLICK_TO_RUN_VELLUM_DESKTOP.bat`** (or `1_launch_desktop_app.bat`).
2. The launcher will automatically configure Python dependencies and launch the server.
3. Your default web browser will open to:
   ```
   http://localhost:8501
   ```

---

## 📄 Complete Documentation
Please open the included publication-grade PDF manual:
👉 **`README_VELLUM_DESKTOP_V2.0.pdf`**

The PDF contains comprehensive documentation covering:
- **🧪 Module 1: ASReview-Powered Active Learning Screening Hub**
  - 3-tier automated deduplication (DOI, Title, Token Jaccard > 0.88)
  - Continuous priority re-ranking with TF-IDF + Multinomial Naive Bayes
  - Stopping heuristics (consecutive irrelevant records with $\ge 95\%$ estimated recall)
  - Keyboard shortcuts (`I` = Include, `E` = Exclude, `U` = Undo, `Skip`)
  - Multi-session management & 1-click addition to Project Unified Paper Pool
- **🕸️ Module 2: Connected Papers Scholarly Force Graph**
  - D3 force-directed physics graph with seed origin purple halo (`#a855f7`)
  - Temporal color gradient from mint (`#a7d7c5`) to deep pine (`#1b4332`)
  - Direct 1-click Connected Papers link (`https://www.connectedpapers.com/main/{doi}/graph`)
  - 1-click "Screen in ASReview" from any graph node
- **🔍 Module 3: Multi-Database Academic Search & Visual Boolean Builder**
  - Federated searches across OpenAlex, Crossref, arXiv, and PubMed
  - Visual Boolean logic builder (`WHERE`, `AND`, `OR`, `NOT`)
  - Scopus, Web of Science, and RIS/BibTeX import
- **📥 Module 4: Unified Paper Pool & Batch PDF Downloader**
  - Multi-engine Open Access PDF retrieval (Unpaywall, PubMed Central, arXiv)
  - Local vault organization (`~/Vellum_Research_Vault/`)
- **🔬 Module 5: Evidence Synthesis & PRISMA 2020 Compliance**
  - PRISMA 2020 flow metrics export (Identified, Deduplicated, Screened, Excluded, Included)
  - Study design & critical appraisal extraction

---

## 🧪 Testing & Verification
All 64 unit tests pass with a 100% success rate:
```powershell
Desktop_App\.venv\Scripts\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\tests -v
```
*(64 passed in 3.83s)*
