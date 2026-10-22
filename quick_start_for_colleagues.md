# 🚀 Vellum — Quick Start Guide for Colleagues

> **Author & Lead Architect:** Amine Zouaghi
> **Platform:** Windows 10 / Windows 11 (64-bit)
> **License:** Free & Open-Access Academic Tool (MIT)

Welcome! This package contains **two complementary applications** designed to accelerate
literature review, PDF retrieval, citation tracing, and evidence synthesis. Both run entirely
on your machine — no account, no cloud, no telemetry.

---

## ⚡ 1-Click Launchers (At a Glance)

| What you want to test | File to double-click | Setup required |
| :--- | :--- | :--- |
| **📥 Install Vellum Desktop** | **`Vellum_Desktop\Vellum-Desktop-V2.0-Setup-x64.exe`** | None — standard installer, no admin rights |
| **🖥️ Desktop Workbench** | **`Vellum_Desktop\1_launch_desktop_app.bat`** | None (virtual environment is bundled) |
| **🌐 Web Research Studio (send this one)** | **`Vellum_Web\Vellum_Web_Fernly_SHARE\START_VELLUM_WEB.bat`** | **None** — Node.js is bundled inside the folder |
| **🌐 Web Research Studio (this repository)** | **`Vellum_Web\2_launch_fernly_web_app.bat`** | Node.js 18+ (opens on port 3002) |
| **🚀 Both Together** | **`3_launch_both_apps.bat`** | Launches desktop and web side by side |
| **⚡ Compiled Desktop** | **`Vellum_Desktop\CLICK_TO_RUN_STANDALONE_EXE.bat`** | Prefers the installed copy, falls back to the portable bundle |

The two applications live in **separate, self-contained folders** — `Vellum_Desktop\`
and `Vellum_Web\` — and neither depends on the other.

> **💡 Sharing the web app with someone else?** Send them
> `Vellum_Web\Vellum_Web_Fernly_SHARE.zip`. They unzip it, double-click
> **START_VELLUM_WEB.bat**, and their browser opens on `http://localhost:3002`.
> They do **not** need to install Node.js, Python, or anything else — a
> portable Node.js runtime travels inside the folder.

> **⚠️ First run of the desktop installer:** Windows SmartScreen may say
> *"Windows protected your PC"* because the installer is not code-signed.
> Click **More info → Run anyway**. To confirm the file you received is the
> one that was built, run
> `certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256` and compare it
> with `DISTRIBUTABLES\SHA256SUMS.txt`.

---

## 🖥️ Version 1: Vellum Desktop V2.0 (Fernly Botanical Bento)

**Port:** `http://localhost:8501` · Native window, no browser chrome.

### How to Run
Double-click **`Vellum_Desktop\1_launch_desktop_app.bat`** — or install properly with
**`Vellum_Desktop\Vellum-Desktop-V2.0-Setup-x64.exe`**, which needs no Python at all.
### Key Features to Test
1. **📥 High-Throughput PDF Downloader** — enter DOIs, arXiv IDs or titles, or upload exported
   search files directly. Multi-tier failover resolves open-access PDFs through Unpaywall,
   PubMed Central and arXiv while rejecting paywall HTML traps. **🔄 Reset Session** clears
   the queue and inputs in one click.
2. **📁 Universal Bibliographic File Importer** — upload `.csv`, `.ris`, `.bib`, `.tsv`, or
   `.txt` exported from **Scopus**, **PubMed**, **Web of Science**, Zotero or EndNote.
   Metadata is cleaned, duplicates filtered, DOIs normalised. Click **"Load Unique DOIs into
   PDF Downloader Queue"** or **"Merge into Search Results & Screening"**.
3. **🔍 Ultra-Fast LitCheck** — parallel queries across OpenAlex, arXiv, PubMed and Crossref
   with advanced boolean expressions (`AND`, `OR`, `NOT`). Fuzzy deduplication processes
   3 000+ records in ~1.6 s. Paginated 100-per-page review with **"Include All"**,
   **"Exclude All"** and quick screening filters.
4. **🧪 ASReview Active-Learning Screening** — TF-IDF + Multinomial Naive Bayes re-ranking,
   3-tier deduplication (DOI / title / token Jaccard > 0.88), stopping heuristics at ≥95 %
   estimated recall, and keyboard shortcuts (`I` = Include, `E` = Exclude, `U` = Undo).
5. **🕸️ Connected Papers Force Graph** — D3 physics network with origin halo, citation-weighted
   nodes, year gradient, direct Connected Papers links, and 1-click **"Screen in ASReview"**.
6. **📊 Local PDF Vault & Duplicate Detection** — point at a folder of PDFs to extract metadata,
   detect exact and fuzzy duplicates, and organise the collection.
7. **📋 Citation Export** — BibTeX (`.bib`), EndNote/Zotero (`.ris`), CSV and APA, plus
   PRISMA 2020 flow metrics (Identified / Deduplicated / Screened / Excluded / Included).

---

## 🌐 Version 2: Vellum Web (Fernly Botanical Bento)

**Port:** `http://localhost:3002` · Next.js 16 + React 19 + Tailwind 4.

### How to Run
Double-click **`Vellum_Web\2_launch_fernly_web_app.bat`** (this repository copy needs Node.js 18+),
or double-click **`Vellum_Web\Vellum_Web_Fernly_SHARE\START_VELLUM_WEB.bat`** (needs nothing —
Node.js is bundled). Either way the studio opens on `http://localhost:3002`.

### Key Features to Test
1. **🔬 250M+ Academic Multi-Source Search** — OpenAlex, arXiv, Semantic Scholar, Crossref,
   with an **Advanced Search Builder** for boolean expressions and exact `"..."` phrases.
2. **🕸️ Connected Papers Graph** — canvas physics with prior/derivative works catalogues and
   one-click graph re-centring on any node.
3. **🧠 AI Screening Workspace** — active-learning ranking, recall & stopping curve, and
   PRISMA-compliant CSV/RIS export.
4. **📥 Batch Downloader** — multi-tier open-access retrieval with client-side blob streaming.
5. **🎨 Design Switcher** — toggle between **Apple Fluid** (frosted translucent glass,
   Cupertino blue, tactile spring physics) and **Wispr Flow** (calm linen canvas, botanical
   forest tones), plus a dark/light mode switch.
6. **🔑 Custom API Tokens Modal** — rate-limit status and 1-click links to free provider keys
   (OpenAlex, Semantic Scholar, Crossref, PubMed).
7. **📖 Grounded Tri-Pane Workspace** — **left:** paper corpus with DOI fetch and PDF upload;
   **centre:** document reader (grounded reader ↔ native PDF viewer); **right:** evidence &
   synthesis studio for verbatim claims, notes and citation export.
8. **🗑️ Workspace Cleaning** — the **"Clean"** action removes empty review drafts or resets
   local storage.
9. **🔒 100% Client-Side Privacy** — everything is stored in your browser's persistent
   IndexedDB. No accounts, no logins, no cloud tracking.

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q1 — Do I need to install Python for the Desktop App?
**No.** Run `Vellum_Desktop\Vellum-Desktop-V2.0-Setup-x64.exe` and the app works with zero Python. The
in-repository launcher also works because the virtual environment is already bundled.

### Q2 — What do I need to run the Web App?
**Nothing, if you use the share folder.** `Vellum_Web\Vellum_Web_Fernly_SHARE\` bundles a
portable Node.js runtime (verified against `nodejs.org`'s published checksums), so you
just unzip it and double-click `START_VELLUM_WEB.bat`.

If you instead run the repository copy (`Vellum_Web\Web_App_Fernly\`), you need
**Node.js 18+** ([nodejs.org](https://nodejs.org)). Dependencies are already installed in
`Vellum_Web\Web_App_Fernly\node_modules\`.

### Q3 — How do I stop the servers?
Close the desktop window (the background engine terminates with it). For the web app, close the
server window that `START_VELLUM_WEB.bat` opens, or double-click
**`Vellum_Web\Vellum_Web_Fernly_SHARE\STOP_VELLUM_WEB.bat`**. If you launched the repository
copy, you can also run:
```powershell
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Q4 — Where is my data?
`%USERPROFILE%\Vellum_Research_Vault\` for the desktop app, and your browser's IndexedDB for
the web studio. **Uninstalling Vellum never deletes either.**

### Q5 — The desktop window is blank.
Install the [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/).
Vellum automatically falls back to a standalone Edge/Chrome app window if WebView2 is missing.

### Q6 — Windows blocked the installer ("Windows protected your PC").
The installer is not code-signed, so SmartScreen warns on first run. Click
**More info → Run anyway**. Verify the file against `DISTRIBUTABLES\SHA256SUMS.txt`
if you want to be certain it is the one that was built.

---

## 👤 Feedback & Credits

- **Developer & Lead Architect:** **Amine Zouaghi**
- **Project:** Vellum Academic Literature Suite
- **Feedback:** please share suggestions, testing feedback, or feature ideas directly with Amine!
