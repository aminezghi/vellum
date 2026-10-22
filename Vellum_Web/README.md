# VELLUM WEB — FERNLY BOTANICAL BENTO EDITION
**Local-First Academic Research Studio**
*Author & Lead System Architect: Amine Zouaghi*
*Next.js 16 (Turbopack) / React 19 / Tailwind CSS 4 • Node.js 18+*
*Host & Port: `http://localhost:3002`*

This folder is the **complete, self-contained Vellum Web application**. Nothing in
it depends on the desktop app or on any other folder in the pack.

---

## 📁 What's in this folder

| Item | What it is |
| :--- | :--- |
| `Web_App_Fernly\` | The application: source, dependencies, and the production build output |
| `2_launch_fernly_web_app.bat` | Starts the studio and opens your browser |
| `Vellum_Web_Fernly_Latest_Export.zip` | Lightweight source export (no `node_modules`, no build output) |
| `Web_App_Fernly\README_FOR_COLLEAGUES.md` | The full standalone manual (also as PDF) |

---

## 🚀 Quick Start

Double-click **`2_launch_fernly_web_app.bat`**.

It checks for Node.js, installs dependencies on first run, starts the Next.js 16
dev server and opens:

```
http://localhost:3002
```

> Use `http://localhost:3002`, not `http://127.0.0.1:3002`. Next.js 16's dev
> server treats `127.0.0.1` as a cross-origin dev host and blocks the client
> bundle, which leaves the page stuck on its loading screen.

**Requirements:** Node.js 18 or newer (LTS 20+ recommended).

---

## 🧰 What the studio does

1. **Connected Papers Interactive Citation Graph** — force-directed canvas
   simulation with origin halo rings, citation-scaled nodes and a continuous
   year gradient, plus *Prior Works* / *Derivative Works* lists.
2. **ASReview Machine-Learning Screening** — active-learning ranking with
   TF-IDF vectorisation and Naive Bayes priors, live stopping curves and
   multi-source deduplication.
3. **Visual Boolean Search** — clause-by-clause builder supporting `WHERE`,
   `AND`, `OR`, `NOT` and direct index mapping (`[Title/Abstract]`, `au:`,
   `year:`, `topic:`).
4. **Multi-Tier Batch PDF Downloader** — resolves across Unpaywall, Open Access
   repositories and Semantic Scholar, with paywall-trapping safeguards.
5. **Systematic Notebooks** — local-first synthesis canvas with client-side
   IndexedDB persistence, verbatim claim grounding and citation formatting.

---

## 🔐 Where your data lives

Everything is stored **in your browser**, on this origin only:

| What | Where |
| :--- | :--- |
| Notebooks, sources, notes, screening sessions | IndexedDB `VellumWebDB_fernly` |
| Theme, accent, API tokens, researcher field | `localStorage` keys `vellum:fernly:*` |
| Downloaded PDFs | your browser's download folder |

Nothing is sent anywhere except the scholarly APIs you search (OpenAlex, arXiv,
Crossref, PubMed, Unpaywall, Semantic Scholar). Clearing site data in the
browser clears your library.

The app also migrates any library created by older builds (which shared one
database called `VellumWebDB`) into the namespaced database above, once, leaving
the old copy untouched.

---

## 🧪 Testing & Verification

Run from `Web_App_Fernly\`:

```powershell
npx tsc --noEmit
npx next build
```

| Suite | Result |
| :--- | :--- |
| TypeScript (`tsc --noEmit`) | **0 errors** |
| Production build (`next build`) | **compiled, 0 errors** |

---

## 🏗️ Rebuilding

```powershell
cd Web_App_Fernly
npm install
npx next build
```

A production server can then be started with `npx next start -p 3002`.
