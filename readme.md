# 🍃 Vellum — Academic Research Suite (Windows)

> **Author & Lead Architect:** Amine Zouaghi
> **Edition:** Vellum Desktop V2.0 + Vellum Web — Fernly Botanical Bento
> **Platform:** Windows 10 / Windows 11 (64-bit)
> **License:** Free & Open-Access Academic Tool (MIT)

Vellum is a **local-first** academic research suite for literature discovery, high-throughput
PDF harvesting, active-learning screening, citation-network exploration, and PRISMA-compliant
evidence synthesis. Nothing is uploaded, nothing is tracked, and every byte stays on your machine.

This package contains **two applications** that share the same research workflow but different
strengths: a native desktop workbench for heavy batch work, and a browser studio for visual,
interactive exploration.

---

## 🚀 Install

### Option A — Install Vellum Desktop (recommended)

Run the installer in the **`dist/`** folder:

```
dist\Vellum-Desktop-V2.0-Setup-x64.exe
```

It installs to `%LOCALAPPDATA%\Programs\Vellum Desktop` — **no administrator rights required**.
You get a Start Menu entry, an optional desktop shortcut, and a proper *Apps & Features*
uninstaller. The installed app needs **no Python**.

### Option B — Run straight from source

The repository already ships a ready virtual environment, so the desktop app runs with a
double-click:

```
1_launch_desktop_app.bat
```

This launches `http://localhost:8501` in your default browser using `Desktop_App\.venv`.

---

## 🖥️ Application 1 — Vellum Desktop V2.0 (Fernly Botanical Bento)

**Port:** `http://localhost:8501` · **Engine:** Python 3.13 + Streamlit + PyInstaller

A native single-window workbench (WebView2, no browser chrome) for the heavy lifting:

| Module | What it does |
| :--- | :--- |
| 🧪 **Active-Learning Screening** | ASReview-style ranking (TF-IDF + Naive Bayes), 3-tier deduplication (DOI / Title / token Jaccard > 0.88), stopping heuristics at ≥95 % estimated recall, keyboard shortcuts (`I` / `E` / `U` / `Skip`) |
| 🕸️ **Citation Force Graph** | D3 force-directed network with origin halo, year-gradient colouring, prior/derivative works, direct Connected Papers links |
| 🔍 **LitCheck Multi-Source Search** | Parallel queries across OpenAlex, arXiv, PubMed, Crossref with full boolean syntax; 3 000+ records deduplicated in ~1.6 s |
| 📥 **Batch PDF Harvester** | Multi-tier open-access retrieval (Unpaywall, PubMed Central, arXiv) with paywall-HTML rejection and normalised naming |
| 📥 **Bibliographic Importer** | Scopus, PubMed, Web of Science, Zotero, EndNote — `.csv`, `.ris`, `.bib`, `.tsv` with metadata cleanup and DOI normalisation |
| 📚 **Local PDF Vault** | Index a folder, detect exact and fuzzy duplicates, organise the collection |
| 📊 **PRISMA 2020 Export** | Identified / Deduplicated / Screened / Excluded / Included flow metrics, plus BibTeX, RIS, CSV and APA citation export |

Your work lives in `~\Vellum_Research_Vault\` — outside the install directory, so uninstalling
never touches your data.

**10 pages:** Welcome Hub · Project Overview · Screening · Analysis · Citation Graph ·
Researchers · Library · Notes · Export Center · Help

---

## 🌐 Application 2 — Vellum Web (Fernly Botanical Bento)

**Port:** `http://localhost:3002` · **Engine:** Next.js 16 (Turbopack) + React 19 + Tailwind 4

The browser studio for visual, interactive research:

- **Connected Papers force graph** — canvas physics, citation-weighted nodes, year gradient
- **AI screening workspace** — active-learning ranking with recall/stopping curve and CSV/RIS export
- **Visual Boolean builder** — `WHERE` / `AND` / `OR` / `NOT` with live compiled-query preview
- **Batch downloader** — multi-tier OA resolution with client-side blob streaming
- **Tri-pane grounded workspace** — corpus, document reader (grounded + native PDF), synthesis notes
- **Notebooks** — persisted locally in IndexedDB; no account, no cloud, no telemetry
- **Design switcher** — Apple Fluid ↔ Wispr Flow, plus dark/light modes

> **Why port 3002?** It is the original Fernly origin. Keeping it means any notebooks and
> screening sessions already saved in your browser stay exactly where they are.

---

## 📂 Folder Layout

```
PDF_Downloader_Dual_Pack/
├── dist/
│   └── Vellum-Desktop-V2.0-Setup-x64.exe   ← the installer
├── Desktop_App/                           ← Vellum Desktop V2.0 source
│   ├── pdf_downloader_app.py              ← main application
│   ├── app_pages/                         ← the 10 Streamlit pages
│   ├── vellum_*.py                        ← feature modules
│   ├── tests/                             ← pytest suite + page smoke test
│   ├── docs/adr/                          ← architecture decision records
│   ├── build_vellum_windows.spec          ← PyInstaller spec
│   ├── installer.iss                      ← Inno Setup script
│   └── dist/Vellum/                       ← compiled portable bundle
├── Web_App_Fernly/                        ← Vellum Web source (port 3002)
│   ├── src/app, src/components, src/lib
│   └── .next/                             ← production build
├── 1_launch_desktop_app.bat               ← desktop (from source)
├── 2_launch_fernly_web_app.bat            ← web studio
├── 3_launch_both_apps.bat                 ← both together
├── CLICK_TO_RUN_VELLUM_DESKTOP.bat        ← desktop, auto-configuring launcher
├── CLICK_TO_RUN_STANDALONE_EXE.bat        ← desktop, compiled binary
└── README_FOR_COLLEAGUES.pdf              ← printable manual
```

---

## 🧪 Testing & Verification

Everything in this pack has been exercised end to end.

```powershell
# Desktop unit suite (64 tests) + in-process smoke test of all 10 pages
Desktop_App\.venv\Scripts\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\tests -v

# Page smoke test on its own, with full tracebacks
Desktop_App\.venv\Scripts\python.exe Desktop_App\tests\smoke_app_pages.py

# Web app: type-check + production build
cd Web_App_Fernly; npm run build
```

| Suite | Result |
| :--- | :--- |
| Desktop unit tests (`Desktop_App/tests`) | **64 passed** |
| Streamlit page smoke test (main app + 10 pages) | **11 / 11 ran clean** |
| Web app production build + TypeScript | **compiled, 0 errors** |
| Frozen `Vellum.exe` server health check | **HTTP 200** |

---

## ❓ Troubleshooting

**`[ERROR] Node.js 18+ was not found`** — install Node.js LTS from [nodejs.org](https://nodejs.org)
and tick *Add to PATH* during setup.

**Port already in use (3002 / 8501)** — an earlier session is still running:

```powershell
Get-Process -Name node,Vellum -ErrorAction SilentlyContinue | Stop-Process -Force
```

**Desktop window is blank** — Vellum needs the Microsoft Edge **WebView2 Runtime**. It ships with
Windows 11 and modern Windows 10; if it is missing, install the
[WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/).
Vellum automatically falls back to a standalone Edge/Chrome app window if WebView2 is unavailable.

---

## 👤 Credits

- **Developer & Lead Architect:** Amine Zouaghi
- **Project:** Vellum Academic Literature Suite & PDF Downloader
- **Feedback:** please share suggestions and testing notes directly with Amine.
