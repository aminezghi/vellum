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
| `Vellum_Web_Fernly_SHARE\` | **The one-click package.** Self-contained: portable Node.js bundled, production build ready. Unzip anywhere and double-click `START_VELLUM_WEB.bat` |
| `Vellum_Web_Fernly_SHARE.zip` | The same folder, zipped — **this is what you send to a colleague** |
| `Web_App_Fernly\` | The application: source, dependencies, and the production build output |
| `2_launch_fernly_web_app.bat` | Starts the studio from source and opens your browser |
| `Vellum_Web_Fernly_Latest_Export.zip` | Lightweight source export (no `node_modules`, no build output) |
| `Web_App_Fernly\README_FOR_COLLEAGUES.md` | The full standalone manual (also as PDF) |

---

## 🚀 Quick Start

### Option A — The one-click package (no installation required)

Double-click **`Vellum_Web_Fernly_SHARE\START_VELLUM_WEB.bat`**.

That folder carries its own portable Node.js runtime, so there is **nothing to
install** — not Node.js, not Python, no admin rights. Extract the whole folder
first (keep the files together), then double-click. The browser opens on:

```
http://localhost:3002
```

Keep the black server window open while you work; close it (or press `Ctrl+C`)
to stop Vellum. `STOP_VELLUM_WEB.bat` stops it without hunting for processes.

> The bundled Node.js runtime (v24 LTS) was verified against `nodejs.org`'s own
> published `SHASUMS256.txt` before being packaged. The folder also contains a
> `SHA256SUMS.txt` covering every file inside it, so a colleague can confirm
> the package was not altered in transit.

### Option B — From source (this repository)

Double-click **`2_launch_fernly_web_app.bat`**.

It checks for Node.js, installs dependencies on first run, starts the Next.js 16
dev server and opens:

```
http://localhost:3002
```

> Use `http://localhost:3002`, not `http://127.0.0.1:3002`. Next.js 16's dev
> server treats `127.0.0.1` as a cross-origin dev host and blocks the client
> bundle, which leaves the page stuck on its loading screen.

**Requirements:** Node.js 18 or newer (LTS 20+ recommended). The one-click
package in Option A needs none of this.

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

## ♿ Accessibility

The studio is built to be usable without a mouse and with a screen reader.

| Area | What it does |
| :--- | :--- |
| **Dialogs** | All seven dialogs are real `role="dialog"` elements with `aria-modal`, an accessible name and description. Focus moves into the dialog when it opens and returns to the trigger when it closes. Tab and Shift+Tab cycle inside the dialog instead of escaping into the page behind it. Escape dismisses it |
| **Live regions** | Search results, the trending feed and the loading states are announced, so a screen-reader user is told when results arrive instead of having to go looking |
| **Focus** | Every focusable element shows a visible focus ring. The app had no `:focus-visible` rule before, which left keyboard users with no way of telling where they were |
| **Reduced motion** | `prefers-reduced-motion` is honoured. The interface uses a lot of movement — hover lifts, fades, a pulsing spinner — which is a problem for people with vestibular sensitivity |
| **Forms** | Every field is associated with its label, and the emoji picker, the destination toggle and the cleaning-scope picker are exposed as radio groups rather than a row of unlabelled buttons |
| **Colour** | The accent colourway is chosen from a listbox whose options have names, not four anonymous colour swatches |

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
| One-click package: relocated to an arbitrary path and launched | **HTTP 200** |
| One-click package: live `/api/search` (OpenAlex) | **real records returned** |
| One-click package: live `/api/trends` (OpenAlex) | **real records returned** |

The last three rows are exercised against the *shipped folder*, not the source.
Run the whole release verification from the repository root:

```powershell
& "..\Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" ..\tools\verify_release.py
```

---

## 🏗️ Rebuilding

```powershell
# source
cd Web_App_Fernly
npm ci
npx next build

# one-click package (from the repository root)
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" tools\build_web_share.py `
    --node-zip C:\path\to\node-v24.22.1-win-x64.zip
```

A production server can then be started with `npx next start -p 3002`, which is
exactly what the packaged `START_VELLUM_WEB.bat` does.
