# 🚀 Vellum — Quick Start Guide for Colleagues

> **Author & Lead Architect:** Amine Zouaghi  
> **Platform:** Windows 10 / Windows 11 (64-bit)  
> **License:** Free & Open-Access Academic Tool (MIT)  

Welcome! This package contains **two complementary applications** designed to accelerate literature review, PDF retrieval, citation tracing, and evidence synthesis. Both run entirely on your machine — no account, no cloud, no telemetry.

---

## ⚡ 1-Click Launchers (At a Glance)

| What you want to test | File to double-click | Setup required |
| :--- | :--- | :--- |
| **🖥️ Desktop Workbench** | **`launch_desktop.bat`** (or `Vellum_Desktop\launch_desktop_app.bat`) | None (virtual environment is bundled) |
| **🌐 Web Research Studio** | **`launch_web.bat`** (or `Vellum_Web\launch_web_app.bat`) | Node.js 18+ (opens on port 3002) |
| **🚀 Both Together** | **`launch_both.bat`** | Launches desktop and web side by side |
| **📥 Install Desktop App** | **`Vellum-Desktop-Setup-x64.exe`** (from Releases) | None — standard installer, no admin rights |

The two applications live in **separate, self-contained folders** — `Vellum_Desktop\` and `Vellum_Web\` — and neither depends on the other.

> **💡 Sharing with someone else?** Send them the pre-built packages from [GitHub Releases](https://github.com/aminezghi/vellum/releases/latest).

> **⚠️ First run of the desktop installer:** Windows SmartScreen may say *"Windows protected your PC"* because the installer is not code-signed. Click **More info → Run anyway**. To confirm the file integrity, check `DISTRIBUTABLES\SHA256SUMS.txt`.

---

## 🖥️ Version 1: Vellum Desktop Workbench

**Port:** `http://localhost:8501` · Native window, no browser chrome.

### How to Run
Double-click **`launch_desktop.bat`** or **`Vellum_Desktop\launch_desktop_app.bat`**.

### Key Features to Test
1. **📥 High-Throughput PDF Downloader** — enter DOIs, arXiv IDs or titles, or upload exported search files directly. Multi-tier failover resolves open-access PDFs through Unpaywall, PubMed Central and arXiv while rejecting paywall HTML traps. **🔄 Reset Session** clears the queue and inputs in one click.
2. **📁 Universal Bibliographic File Importer** — upload `.csv`, `.ris`, `.bib`, `.tsv`, or `.txt` exported from **Scopus**, **PubMed**, **Web of Science**, Zotero or EndNote. Metadata is cleaned, duplicates filtered, DOIs normalised. Click **"Load Unique DOIs into PDF Downloader Queue"** or **"Merge into Search Results & Screening"**.
3. **🔍 Ultra-Fast LitCheck** — parallel queries across OpenAlex, arXiv, PubMed and Crossref with advanced boolean expressions (`AND`, `OR`, `NOT`). Fuzzy deduplication processes 3 000+ records in ~1.6 s. Paginated 100-per-page review with **"Include All"**, **"Exclude All"** and quick screening filters.
4. **🧪 Active-Learning Screening** — TF-IDF + Multinomial Naive Bayes re-ranking, 3-tier deduplication (DOI / title / token Jaccard > 0.88), stopping heuristics at ≥95 % estimated recall, and keyboard shortcuts (`I` = Include, `E` = Exclude, `U` = Undo).
5. **🕸️ Connected Papers Force Graph** — D3 physics network with origin halo, citation-weighted nodes, year gradient, direct Connected Papers links, and 1-click **"Screen in Screening Hub"**.
6. **📊 Local PDF Vault & Duplicate Detection** — point at a folder of PDFs to extract metadata, detect exact and fuzzy duplicates, and organise the collection.
7. **📋 Citation Export** — BibTeX (`.bib`), EndNote/Zotero (`.ris`), CSV and APA, plus PRISMA 2020 flow metrics (Identified / Deduplicated / Screened / Excluded / Included).

---

## 🌐 Version 2: Vellum Web Studio

**Port:** `http://localhost:3002` · Next.js 16 + React 19 + Tailwind 4.

### How to Run
Double-click **`launch_web.bat`** or **`Vellum_Web\launch_web_app.bat`**. The studio opens on `http://localhost:3002`.

### Key Features to Test
1. **🔬 250M+ Academic Multi-Source Search** — OpenAlex, arXiv, Semantic Scholar, Crossref, with an **Advanced Search Builder** for boolean expressions and exact `"..."` phrases.
2. **🕸️ Connected Papers Graph** — canvas physics with prior/derivative works catalogues and one-click graph re-centring on any node.
3. **🧠 AI Screening Workspace** — active-learning ranking, recall & stopping curve, and PRISMA-compliant CSV/RIS export.
4. **📥 Batch Downloader** — multi-tier open-access retrieval with client-side blob streaming.
5. **🎨 Design & Palettes** — fluid translucent glass styling, high-contrast dark/light mode, and curated accent palettes.
6. **🔑 Custom API Tokens Modal** — rate-limit status and 1-click links to free provider keys (OpenAlex, Semantic Scholar, Crossref, PubMed).
7. **📖 Grounded Tri-Pane Workspace** — **left:** paper corpus with DOI fetch and PDF upload; **centre:** document reader (grounded reader ↔ native PDF viewer); **right:** evidence & synthesis studio for verbatim claims, notes and citation export.
8. **🗑️ Workspace Cleaning** — the **"Clean"** action removes empty review drafts or resets local storage.
9. **🔒 100% Client-Side Privacy** — everything is stored in your browser's persistent IndexedDB. No accounts, no logins, no cloud tracking.

---

## ❓ Frequently Asked Questions & Troubleshooting

### Q1 — Do I need to install Python for the Desktop App?
**No.** The repository includes a pre-configured environment in `Vellum_Desktop\Desktop_App\.venv\`.

### Q2 — What do I need to run the Web App?
**Node.js 18+** ([nodejs.org](https://nodejs.org)). Dependencies are installed in `Vellum_Web\Web_App\node_modules\`.

### Q3 — How do I stop the servers?
Close the desktop terminal/window. For the web app, press `Ctrl + C` in the web terminal window, or run:
```powershell
Get-Process -Name node -ErrorAction SilentlyContinue | Stop-Process -Force
```

### Q4 — Where is my data?
`%USERPROFILE%\Vellum_Research_Vault\` for the desktop app, and your browser's IndexedDB for the web studio.

### Q5 — The desktop window is blank.
Install the [Microsoft Edge WebView2 Runtime](https://developer.microsoft.com/microsoft-edge/webview2/). Vellum automatically falls back to a standalone Edge/Chrome app window if WebView2 is missing.

---

## 👤 Feedback & Credits

- **Developer & Lead Architect:** **Amine Zouaghi**
- **Project:** Vellum Academic Literature Suite
- **Feedback:** please share suggestions, testing feedback, or feature ideas directly with Amine!
