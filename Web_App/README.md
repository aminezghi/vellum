# 🌐 Vellum Web 2.4 — Modern Academic Research Studio (Windows Edition)

> **Author & Lead Architect:** Amine Zouaghi  
> **Tech Stack:** Next.js 16.4 (Turbopack) · React 19 · Tailwind CSS v4 · Dexie.js (IndexedDB) · Lucide Icons · Wispr Flow Aesthetic  
> **Platform:** Windows 10 & Windows 11 (64-bit)  
> **License:** MIT License  

---

## 🌟 Overview

**Vellum Web 2.4** is a 100% free, private, local-first academic research studio and systematic literature review canvas.

It requires **zero account creation, zero cloud dependencies, and zero monthly subscriptions**. All research notebooks, synthesis notes, extracted quotes, and uploaded or fetched PDF binaries are stored directly inside your browser's persistent IndexedDB vault (`dexie.js`).

---

## ✨ Key Features

1. **🔬 250M+ Academic Multi-Source Search**:
   - Query across **OpenAlex**, **arXiv**, **Semantic Scholar**, and **Crossref** in real-time.
   - Advanced Boolean query builder (`AND`, `OR`, `NOT`, exact `"..."` phrase, author, and DOI matching).
   - Custom API tokens modal with 1-click direct links to free provider registration portals.

2. **🔥 Trending Literature Radar**:
   - Live citation momentum tracking across trending research topics (LLM reasoning, oncology, epidemiology, green energy).
   - One-click deep inspection from trends straight into a systematic canvas.

3. **📖 Grounded Tri-Pane Workspace**:
   - **Left Pane:** Systematic paper corpus with instant PDF upload & DOI import.
   - **Center Pane:** Interactive document reader with dual-mode toggle (*Grounded Reader* vs *Interactive PDF*), zoom controls, and verbatim claims extraction.
   - **Right Pane:** Evidence & Synthesis Studio for quote collection, project synthesis markdown notes, and 1-click formatted citation export (BibTeX, RIS, APA).

4. **🎨 Wispr Flow Palette & Dual Reading Modes**:
   - **Linen Day Canvas:** `#ffffeb` warm cream background with `#034f46` signature forest green accents.
   - **Night Obsidian Mode:** `#121413` deep dark mode with high-contrast, eye-friendly typography.
   - Instant anti-flash toggle and persistent theme memory.

5. **🗑️ Workspace Cleaning & Management**:
   - 1-click modal to delete individual notebooks, clean empty review drafts, or reset IndexedDB storage.

---

## 🚀 Quick Start on Windows

### Method 1: Standalone Launcher App (`Vellum_Web_Launcher.exe`)
For a native desktop experience with a dedicated floating launcher GUI:
- Double-click [`Vellum_Web_Launcher.exe`](file:///c:/Users/azoua/Downloads/PDF_Downloader_Dual_Pack/Web_App/Vellum_Web_Launcher.exe) inside `Web_App/` (or run [`2_Launch_Web_App.bat`](file:///c:/Users/azoua/Downloads/PDF_Downloader_Dual_Pack/2_Launch_Web_App.bat) from root).
- **Features:**
  - Automatic background server initialization (no visible black terminal window needed).
  - **"Open in Standalone Desktop Window"**: Opens Vellum Web in a native, chromeless desktop application window (`--app` mode via Edge or Chrome).
  - Diagnostic logs viewer and 1-click server restart/shutdown.

### Method 2: 1-Click Launch via Script
- Double-click [`Launch_Web.bat`](file:///c:/Users/azoua/Downloads/PDF_Downloader_Dual_Pack/Web_App/Launch_Web.bat). It verifies dependencies, starts the dev server, and opens your browser to `http://localhost:3000`.

### Method 3: Command Line
```powershell
npm run dev
# Open in browser: http://localhost:3000
```

---

## 📂 Project Structure

```text
Web_App/
├── Vellum_Web_Launcher.exe            # Windows standalone launcher application
├── Launch_Web.bat                     # Windows 1-click launcher
├── src/
│   ├── app/
│   │   ├── api/
│   │   │   ├── search/route.ts        # Multi-database academic aggregator
│   │   │   ├── trends/route.ts        # Citation momentum radar
│   │   │   └── download-pdf/route.ts  # Multi-tier PDF mirror protocol
│   │   ├── globals.css                # Tailwind CSS v4 & Wispr Flow design tokens
│   │   ├── layout.tsx                 # Root layout, anti-flash script & metadata
│   │   └── page.tsx                   # Main Dashboard & workspace controller
│   ├── components/
│   │   ├── Header.tsx                 # Responsive header with theme toggle & Ctrl+K search
│   │   ├── AcademicSearchHub.tsx      # Advanced literature search & Boolean builder
│   │   ├── TrendingRadar.tsx          # Real-time citation momentum stream
│   │   ├── NotebookWorkspace.tsx      # Grounded Tri-Pane Systematic Review Canvas
│   │   ├── NotebookGrid.tsx           # Wispr Flow elevated card grid
│   │   ├── FeaturedCarousel.tsx       # Curated collections carousel
│   │   ├── TokensModal.tsx            # API key setup with direct provider links
│   │   ├── CleanNotebooksModal.tsx    # Storage clean & wipe dialog
│   │   └── Footer.tsx                 # Detailed authorship & creator credits
│   └── lib/
│       ├── db.ts                      # Client-side IndexedDB schema (Dexie.js)
│       └── pdfDownloader.ts           # Multi-tier binary PDF fetcher
├── package.json                       # Scripts and project dependencies
├── next.config.ts                     # Next.js 16 configuration
└── README.md                          # This manual
```

---

## 👤 Credits & Authorship

- **Author & Creator:** **Amine Zouaghi**  
- **Role:** Lead Architect & Developer of Vellum Web & the PDF Downloader Dual Pack  
- **Purpose:** 100% free, private research tool built for researchers, scholars, and students worldwide.
