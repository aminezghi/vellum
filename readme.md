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

Run the installer in the **`Vellum_Desktop\`** folder:

```
Vellum_Desktop\Vellum-Desktop-V2.0-Setup-x64.exe
```

It installs to `%LOCALAPPDATA%\Programs\Vellum Desktop` — **no administrator rights required**.
You get a Start Menu entry, an optional desktop shortcut, and a proper *Apps & Features*
uninstaller. The installed app needs **no Python**.

> **First run:** the installer is not code-signed, so Windows SmartScreen shows
> *"Windows protected your PC"*. Click **More info → Run anyway**. To confirm the
> file you received is the one that was built, compare
> `certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256` with the hash in
> `DISTRIBUTABLES\SHA256SUMS.txt`.

### Option B — Run straight from source

The repository already ships a ready virtual environment, so the desktop app runs with a
double-click:

```
Vellum_Desktop\1_launch_desktop_app.bat
```

This launches `http://localhost:8501` in your default browser using
`Vellum_Desktop\Desktop_App\.venv`.

### Option C — Send the web studio to a colleague (no install at all)

```
Vellum_Web\Vellum_Web_Fernly_SHARE.zip
```

Unzip it anywhere and double-click **`START_VELLUM_WEB.bat`**. It is fully
self-contained: a portable Node.js runtime is bundled and verified against
`nodejs.org`'s own checksum list, so the colleague needs **no Node.js, no
Python and no admin rights**. The browser opens on `http://localhost:3002`.

### Option D — Run the web studio from this repository

```
Vellum_Web\2_launch_fernly_web_app.bat
```

Opens `http://localhost:3002`. Needs Node.js 18+.

The two applications live in **separate, self-contained folders** — `Vellum_Desktop\`
and `Vellum_Web\` — and neither depends on the other.

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
├── Vellum_Desktop/                        ← APPLICATION 1 (self-contained)
│   ├── Desktop_App/                       ←   source + bundled venv + compiled bundle
│   │   ├── pdf_downloader_app.py          ←   main application
│   │   ├── app_pages/                     ←   the 10 Streamlit pages
│   │   ├── vellum_*.py                    ←   feature modules
│   │   ├── tests/                         ←   pytest suite + page smoke test
│   │   ├── docs/adr/                      ←   architecture decision records
│   │   ├── build_vellum_windows.spec      ←   PyInstaller spec
│   │   ├── installer.iss                  ←   Inno Setup script
│   │   └── dist/Vellum/                   ←   compiled portable bundle
│   ├── Vellum-Desktop-V2.0-Setup-x64.exe  ←   the installer
│   ├── Vellum_Standalone_Windows_x64.zip  ←   portable compiled bundle
│   ├── Vellum_Desktop_V2.0_Botanical_Bento.zip ← source drop for colleagues
│   ├── 1_launch_desktop_app.bat           ←   desktop (from source)
│   ├── CLICK_TO_RUN_VELLUM_DESKTOP.bat    ←   desktop, auto-configuring launcher
│   ├── CLICK_TO_RUN_STANDALONE_EXE.bat    ←   desktop, compiled binary
│   ├── README.md                          ←   desktop manual (this app)
│   └── README_VELLUM_DESKTOP_V2.0.pdf     ←   printable manual
├── Vellum_Web/                            ← APPLICATION 2 (self-contained)
│   ├── Web_App_Fernly/                    ←   source (port 3002)
│   │   ├── src/app, src/components, src/lib
│   │   └── .next/                         ←   production build
│   ├── 2_launch_fernly_web_app.bat        ←   web studio launcher
│   ├── Vellum_Web_Fernly_Latest_Export.zip←   source export
│   ├── Vellum_Web_Fernly_SHARE.zip        ←   ONE-CLICK share folder (portable Node bundled)
│   ├── Vellum_Web_Fernly_SHARE/           ←   the same folder, unpacked
│   ├── README.md                          ←   web manual (this app)
│   └── Web_App_Fernly/README_FOR_COLLEAGUES.md ← full standalone manual
├── 3_launch_both_apps.bat                 ← launches both together
├── tools/                                 ← build + verification scripts
├── BUILDING.md                            ← how the artefacts are built and proved
├── RELEASE_REPORT.md                      ← latest verification results
├── DISTRIBUTABLES/SHA256SUMS.txt           ← hashes of everything shipped
├── readme.md                              ← this file
├── README_FOR_COLLEAGUES.md / .pdf        ← printable manual for the whole pack
├── quick_start_for_colleagues.md
├── glossary.md
└── start_here.txt
```

---

## 🧪 Testing & Verification

Everything in this pack has been exercised end to end — and the checks exercise the
**shipped files**, not just the source.

```powershell
# Full release verification (tests + clean-room install + live API calls)
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" tools\verify_release.py

# Desktop unit suite (64 tests) + in-process smoke test of all 10 pages
cd Vellum_Desktop
Desktop_App\.venv\Scripts\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\tests -v
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
| Installer: silent install → boot → health → uninstall | **passed** |
| Web share folder: relocated → launched → live APIs → stopped | **passed** |

`tools\verify_release.py` writes `RELEASE_REPORT.md` and
`DISTRIBUTABLES\SHA256SUMS.txt`. The same checks run unattended in CI
(`.github\workflows\release.yml`) on every push, so the result does not depend
on the author's machine. See **`BUILDING.md`** for the full release procedure.

---

## 🔐 Verifying what you received

```powershell
certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256
```

Compare with `DISTRIBUTABLES\SHA256SUMS.txt`. The web share folder carries its
own `SHA256SUMS.txt` covering all 8 599 files inside it.

---

## ❓ Troubleshooting

**SmartScreen says "Windows protected your PC"** — the installer is not
code-signed. Click **More info → Run anyway**. To confirm the file is the one
that was built, check its SHA-256 against `DISTRIBUTABLES\SHA256SUMS.txt`.

**`[ERROR] Node.js 18+ was not found`** — you launched the *repository* copy of
the web app (`2_launch_fernly_web_app.bat`), which does need Node.js. If you
are sending the app to a colleague, send `Vellum_Web\Vellum_Web_Fernly_SHARE.zip`
instead: it bundles its own Node.js runtime and needs nothing installed.

**Port already in use (3002 / 8501)** — an earlier session is still running:

```powershell
Get-Process -Name node,Vellum -ErrorAction SilentlyContinue | Stop-Process -Force
```

The share folder also ships `STOP_VELLUM_WEB.bat`, which stops the studio
without hunting for processes.

**Desktop window is blank** — Vellum needs the Microsoft Edge **WebView2 Runtime**. It ships with
Windows 11 and modern Windows 10; if it is missing, install the
[WebView2 Evergreen Runtime](https://developer.microsoft.com/microsoft-edge/webview2/).
Vellum automatically falls back to a standalone Edge/Chrome app window if WebView2 is unavailable.

---

## 👤 Credits

- **Developer & Lead Architect:** Amine Zouaghi
- **Project:** Vellum Academic Literature Suite & PDF Downloader
- **Feedback:** please share suggestions and testing notes directly with Amine.
