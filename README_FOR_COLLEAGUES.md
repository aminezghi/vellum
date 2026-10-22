# 🌿 Vellum Research Suite
## System Documentation & Technical Requirements Manual

> **Document Version:** 4.0 (Consolidated Two-Edition Release)
> **Author & Lead System Architect:** Amine Zouaghi
> **Target OS:** Windows 10 / Windows 11 (64-bit)
> **Distribution Architecture:** Vellum Desktop V2.1 + Vellum Web, Fernly Botanical Bento Edition
> **License:** Free & Open-Access Academic Tool (MIT)

---

### Executive Overview

**Vellum** is an end-to-end academic literature review, citation exploration, and systematic
evidence synthesis suite. It bridges high-throughput local hardware capabilities (direct
multi-tier PDF harvesting, offline deduplication, active-learning screening) with fluid modern
web interfaces (force-directed citation graphs, grounded document readers, and PRISMA
systematic workflows).

The package is partitioned into **two synchronized applications**, each in its own
self-contained folder:

1. **Vellum Desktop V2.1 — Fernly Botanical Bento (`Vellum_Desktop\`)**
   Python 3.13 / Streamlit / PyInstaller native desktop workbench for heavy batch downloads
   (10 000+ DOIs), multi-format import (Scopus, WoS, PubMed, RIS, BibTeX), local vault
   indexing, and PRISMA flow export. Its source lives in `Vellum_Desktop\Desktop_App\`.

2. **Vellum Web — Fernly Botanical Bento (`Vellum_Web\`)**
   Next.js 16 (Turbopack) / React 19 / Tailwind CSS 4 browser studio on port 3002, featuring:
   - **Connected Papers Force-Directed Citation Network** — real-time canvas physics with
     origin halo, citation-weighted sizing, year gradients, and prior/derivative catalogues.
   - **ASReview Machine-Learning Title/Abstract Screening** — active-learning ranking with
     Naive Bayes / TF-IDF priors, stopping criteria, session history, multi-file deduplication.
   - **Clause-by-Clause Boolean Search** — visual query builder with `WHERE`, `AND`, `OR`,
     `NOT`, field-tag compilation, and direct search execution.
   - **Batch Multi-Tier PDF Downloader** — the desktop retrieval engine, ported to the browser
     with client-side blob streaming.
   - **Tri-Pane Grounded Synthesis Workspace** — persistent local-first IndexedDB storage with
     PDF annotation and citation export.

Both applications share the same research workflow and the same local-first promise: no
accounts, no cloud sync, no telemetry, no telemetry endpoints.

---

### System Architecture & Prerequisites

#### 1. Hardware Requirements
- **Processor:** 64-bit dual-core x86_64 or ARM64 (Intel Core i3+, AMD Ryzen, or equivalent).
- **RAM:** 4 GB minimum; 8 GB recommended for 10 000+ paper batch screening.
- **Disk Space:** ~700 MB for the installed desktop app; additional space for stored research
  PDFs and the browser cache for the web studio.
- **Display Resolution:** 1280 × 800 minimum; 1920 × 1080 recommended for the tri-pane view.

#### 2. Software Requirements
- **Operating System:** Windows 10 (version 1903+) or Windows 11 (64-bit).
- **For Vellum Desktop:** **Zero software dependencies.** The installer bundles a
  pre-compiled standalone binary (`Vellum.exe`). No Python installation is needed.
- **For Vellum Web (one-click package):** **Zero software dependencies.** The
  shareable package `Vellum_Web\Vellum_Web_Fernly_SHARE.zip` carries its own
  portable Node.js runtime, verified against `nodejs.org`'s published checksums.
  Unzip it and double-click `START_VELLUM_WEB.bat` — nothing to install.
- **For Vellum Web (running from this repository):** **Node.js 18.0.0 or higher**
  (LTS 20+ recommended) from [https://nodejs.org](https://nodejs.org).
- **Browser:** Any modern Chromium-based browser (Chrome, Edge, Brave) or Firefox.
- **Desktop only:** Microsoft Edge **WebView2 Runtime** for the native window. It ships with
  Windows 11 and current Windows 10; Vellum falls back to a standalone Edge/Chrome app
  window when it is unavailable.
- **SmartScreen:** the desktop installer is not code-signed, so Windows shows
  *"Windows protected your PC"* on first run. Choose **More info → Run anyway**.
  To confirm the file you received is the one that was built, run
  `certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256` and compare it
  with `DISTRIBUTABLES\SHA256SUMS.txt`.

#### 3. Network & Firewall
- Outbound access on ports **80** and **443** (HTTPS) to resolve open-access literature from:
  - `api.openalex.org`
  - `export.arxiv.org`
  - `api.semanticscholar.org`
  - `api.crossref.org`
  - `api.unpaywall.org`
  - `www.ncbi.nlm.nih.gov` (PubMed / PMC)
  - `doi.org`
- Local loopback connections on `127.0.0.1` / `localhost` across ports **3002** (web) and
  **8501** (desktop).

#### 4. Data Locations

| What | Where |
| :--- | :--- |
| Research vault (PDFs, projects) | `%USERPROFILE%\Vellum_Research_Vault\` |
| Workspace configuration | `%USERPROFILE%\.vellum_config.json` |
| Recent-folder list | `%USERPROFILE%\.vellum\recent_dirs.json` |
| Web notebooks & screening sessions | Browser IndexedDB, origin `http://localhost:3002` |

None of these are touched by the uninstaller.

---

### 1-Click Launchers Directory

| Launcher Script | Target Application | Host & Port | Primary Purpose |
| :--- | :--- | :--- | :--- |
| **`Vellum_Desktop\Vellum-Desktop-V2.1-Setup-x64.exe`** | Vellum Desktop installer | — | Installs the desktop app per-user, no admin required |
| **`Vellum_Desktop\1_launch_desktop_app.bat`** | Vellum Desktop Workbench | `http://localhost:8501` | High-volume PDF downloads, RIS/BibTeX import, vault indexing |
| **`Vellum_Web\Vellum_Web_Fernly_SHARE\START_VELLUM_WEB.bat`** | Vellum Web Studio | `http://localhost:3002` | **The package to send to a colleague.** Nothing to install — Node.js is bundled |
| **`Vellum_Web\2_launch_fernly_web_app.bat`** | Vellum Web Studio (from source) | `http://localhost:3002` | Citation graph, AI screening, visual boolean search, notebooks |
| **`3_launch_both_apps.bat`** | Dual Workbench Mode | Ports 8501 & 3002 | Launches desktop and web side by side |
| **`Vellum_Desktop\CLICK_TO_RUN_STANDALONE_EXE.bat`** | Vellum Desktop (compiled) | `http://localhost:8501` | Prefers the installed copy, falls back to the portable bundle |

---

### Step-by-Step User & Colleague Workflow

#### Phase 1 — Exploration via the Connected Papers Network
1. Launch **`Vellum_Web\2_launch_fernly_web_app.bat`** and open the **Connected Papers** tab.
2. Enter a paper title or DOI (or click a seminal preset such as *DeepFruits* or *Transformers*).
3. The interactive canvas maps related literature:
   - **Purple halo ring** — the root origin paper.
   - **Node sizes** — proportional to lifetime citation impact.
   - **Colour spectrum** — publication-year gradient, light sage for early work, deep pine for
     recent breakthroughs.
4. Click **`Prior works`** to inspect the foundational citations that established the domain.
5. Click **`Derivative`** to review subsequent advancements that cited the cluster.
6. Click **`Build graph from this paper`** on any node to re-centre the network.

#### Phase 2 — Systematic Search & Visual Boolean Queries
1. Switch to the **Academic Search** tab.
2. Select your domain (Biomedicine, AI & CS, Economics, Climate, Neuroscience, Physics).
3. Open **`Advanced Search`** and use the **Visual Boolean Builder**:
   - `WHERE` defines the initial core concept.
   - Toggle subsequent connectors between `AND`, `OR`, and `NOT`.
   - Target fields: `Title / Abstract`, `Author`, `Topic / Keyword`, `Publication Year`.
4. Review the real-time **`Live Compiled Query`** and click **`Search Literature`**.
5. On any result card:
   - **`PDF`** — download via the multi-tier unpaywall resolvers.
   - **`Graph`** — jump to its Connected Papers visualisation.
   - **`Add`** — attach it to an active systematic-review notebook.

#### Phase 3 — Active-Learning Title & Abstract Screening (ASReview)
1. Open the **AI Screening** tab.
2. Start a new screening session or resume a saved review.
3. Import candidate records via `.csv`, `.ris`, or `.bib`, or pull them from a notebook.
4. Automatic fuzzy deduplication flags matching titles and DOIs before screening begins.
5. Provide 2–5 seed inclusions (relevant controls) and exclusions (irrelevant controls).
6. Train the active-learning model (TF-IDF vectoriser + Naive Bayes prior ranker).
7. Review records sequentially with hotkeys (`[I]` Include, `[E]` Exclude, `[U]` Uncertain).
   The ranker bubbles the highest-probability relevant papers to the top of the queue.
8. Monitor the real-time **Recall & Stopping Curve** to conclude screening once the relevant
   literature has been exhausted.
9. Export final decisions as PRISMA-compliant CSV or RIS.

#### Phase 4 — High-Throughput PDF Retrieval
- **In the browser:** use the **Batch Downloader** tab on port 3002.
- **For 1 000+ bulk files:** launch **`Vellum_Desktop\1_launch_desktop_app.bat`**, paste the DOI list, set the
  output folder, and run the multi-threaded extraction with automated paywall detection and
  naming conventions.

---

### Testing & Verification

Every component of this pack has been exercised end to end.

```powershell
# Desktop unit suite (64 tests) + in-process smoke test of all 10 pages
cd Vellum_Desktop
Desktop_App\.venv\Scripts\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\tests -v

# Page smoke test alone, with full tracebacks
Desktop_App\.venv\Scripts\python.exe Desktop_App\tests\smoke_app_pages.py

# Web app: type-check + production build
cd ..\Vellum_Web\Web_App_Fernly
npx tsc --noEmit
npx next build
```

| Suite | Result |
| :--- | :--- |
| Desktop unit tests (`Desktop_App/tests`) | **64 passed** |
| Streamlit page smoke test (main app + 10 pages) | **11 / 11 ran clean** |
| Web app production build + TypeScript | **compiled, 0 errors** |
| Frozen `Vellum.exe` server health check | **HTTP 200** |

---

### Troubleshooting & Technical Support

- **Port conflict (`EADDRINUSE`) on 3002 or 8501:**
  ```powershell
  Get-Process -Name node,Vellum -ErrorAction SilentlyContinue | Stop-Process -Force
  ```
  Then re-launch the app.
- **Node.js missing:** install Node.js LTS from [nodejs.org](https://nodejs.org) and tick
  *Add to PATH* during setup.
- **Blank desktop window:** install the
  [WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/).
  Vellum otherwise falls back to a standalone Edge/Chrome app window automatically.
- **Client storage persistence:** web notebooks and screening sessions live in the browser's
  IndexedDB. They remain private to your machine and survive refreshes and browser restarts.
  Use **`Clean Workspace`** on the dashboard to reset local caches.

---

*Compiled for academic collaboration, research laboratories, and systematic review teams.*
