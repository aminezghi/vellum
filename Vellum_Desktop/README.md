# VELLUM DESKTOP V2.0 — FERNLY BOTANICAL BENTO EDITION
**Academic Literature Suite & Systematic Review Workbench**
*Author: Amine Zouaghi (amine.zouaghi@unipr.it) | University of Parma*
*Local-First • Zero Telemetry • 100% Privacy-Preserving*

This folder is the **complete, self-contained Vellum Desktop application**. Nothing
in it depends on the web app or on any other folder in the pack.

---

## 📁 What's in this folder

| Item | What it is |
| :--- | :--- |
| `Desktop_App\` | The application: source, bundled virtual environment, tests, and the compiled `dist\Vellum\` bundle |
| `1_launch_desktop_app.bat` | Runs the workbench from source (Streamlit) |
| `CLICK_TO_RUN_VELLUM_DESKTOP.bat` | Same, with dependency auto-configuration |
| `CLICK_TO_RUN_STANDALONE_EXE.bat` | Runs the compiled `Vellum.exe` (native WebView2 window) |
| `Vellum-Desktop-V2.0-Setup-x64.exe` | Windows installer (no admin rights, no Python needed) |
| `Vellum_Standalone_Windows_x64.zip` | The portable compiled bundle, ready to unzip anywhere |
| `Vellum_Desktop_V2.0_Botanical_Bento.zip` | Lightweight source drop for colleagues (no venv, no binary) |
| `README_VELLUM_DESKTOP_V2.0.pdf` | The full publication-grade manual |

---

## 🚀 Quick Start (1-Click Run)

### Option A — Install it (recommended)

Double-click **`Vellum-Desktop-V2.0-Setup-x64.exe`**.

- Standard Windows installer, **no administrator rights required**
- Installs to `%LOCALAPPDATA%\Programs\Vellum Desktop`
- Adds a Start Menu entry, an optional desktop shortcut and a proper *Apps & Features*
  uninstaller
- **Zero Python required** — the whole scientific stack is bundled

> **⚠️ "Windows protected your PC" on first run.** The installer is not
> code-signed, so SmartScreen warns. Click **More info → Run anyway**.
> To confirm the file you received is the one that was built, run
> `certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256` and compare it
> with the hash in `..\DISTRIBUTABLES\SHA256SUMS.txt`.

### Option B — Run from source

Double-click **`1_launch_desktop_app.bat`** (or `CLICK_TO_RUN_VELLUM_DESKTOP.bat`).
The launcher detects the bundled virtual environment, verifies the dependencies and
opens:

```
http://localhost:8501
```

### Option C — Compiled bundle, no installer

Double-click **`CLICK_TO_RUN_STANDALONE_EXE.bat`**. It prefers the installed copy and
falls back to the portable build in `Desktop_App\dist\Vellum\Vellum.exe`.

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

Run from this folder:

```powershell
# Unit suite + in-process smoke test of every page
Desktop_App\.venv\Scripts\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\tests -v

# Page smoke test on its own (main app + all 10 pages), with full tracebacks
Desktop_App\.venv\Scripts\python.exe Desktop_App\tests\smoke_app_pages.py
```

| Suite | Result |
| :--- | :--- |
| Unit tests (`Desktop_App/tests`) | **64 passed** |
| Page smoke test (main app + 10 pages) | **11 / 11 ran clean** |
| Installer: silent install → boot installed `Vellum.exe` → health check → silent uninstall | **passed** |

The last row is the one that matters most: the unit suite and the smoke test
both run against **source**, and say nothing about the frozen bundle a
colleague actually installs. The full harness lives in the repository root:

```powershell
& "Desktop_App\.venv\Scripts\python.exe" ..\tools\verify_release.py
```

It installs the produced installer into a temporary directory, boots the
installed binary, checks the health endpoint, then uninstalls and confirms the
directory is gone. The results are written to `..\RELEASE_REPORT.md`.

---

## 🏗️ Rebuilding

```powershell
# 1. Compile the frozen application bundle (must run from Desktop_App)
cd Desktop_App
.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean build_vellum_windows.spec

# 2. Compile the installer
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
```

The installer lands in `Vellum-Desktop-V2.0-Setup-x64.exe`, next to this file.

> The `.iss` script resolves `downloader.ico` and `dist\Vellum\` **relative to
> `Desktop_App\`**. If you move this folder, keep those two paths intact or
> the installer will not compile.

See `..\BUILDING.md` for the complete release procedure, including how the
shareable web package is produced and how every artefact is hashed.

---

## 📁 Where your data lives

| What | Where |
| :--- | :--- |
| Research vault (PDFs, projects) | `%USERPROFILE%\Vellum_Research_Vault\` |
| Workspace configuration | `%USERPROFILE%\.vellum_config.json` |
| Recent-folder list | `%USERPROFILE%\.vellum\recent_dirs.json` |

Uninstalling Vellum leaves all of these untouched.
