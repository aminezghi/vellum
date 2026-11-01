# Changelog

All notable changes to the Vellum dual pack are recorded here.
The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and the project uses [Semantic Versioning](https://semver.org/).

---

## [2.1.0] — 2026-10-22

The release that closes the gap between what the documentation promised and
what the software actually did, and that makes both applications usable with
a keyboard and with a screen reader.

### Fixed — the desktop advertised a shortcut that did not exist

The Screening page printed **"Include (I)"**, **"Exclude (E)"**, **"Undo (U)"**
and **"Skip"** on its buttons, and the manual repeated the claim in three
places. **No keyboard handler existed anywhere in the desktop application** —
there was no `keydown` listener, no `addEventListener`, no injected script.
Pressing `I` did nothing.

Global shortcuts now work:

- `I` include · `E` exclude · `U` undo · `S` skip
- They work anywhere on the page, not only when a field has focus.
- They stand down while you are typing in a text field, and while a dialog is
  open.
- `Ctrl`/`Cmd`/`Alt` combinations are left alone, so browser shortcuts still
  work.
- The button and the shortcut call **the same function**, so they cannot
  drift apart again.
- The manual now shows the shortcut on the button *and* in a caption, because
  nobody reads manuals.

### Fixed — the Researchers screen was unreachable

`app_pages/researchers.py` was fully written (324 lines: Semantic Scholar
profiles, ORCID, a shortlist and a CV export) and advertised by the manual,
but nothing in the application ever routed to it. It is now a first-class
screen in the navigation bar.

### Changed — the desktop now has real URLs

Navigation used to live entirely in `st.session_state`, so the address bar
never changed: the browser's Back button did nothing, a reload lost your
place, and a colleague could not be sent a link to a particular screen.

Every screen is now a real Streamlit page with its own address:

| Screen | URL |
| :--- | :--- |
| Project Overview | `/` |
| Literature Search | `/discover_literature` |
| Citation Network | `/discover_citation` |
| Screening | `/screening` |
| Unified Paper Pool | `/library_pool` |
| PDF Downloader | `/library_downloader` |
| Methodology & Appraisal | `/evidence_methodology` |
| Export Center | `/evidence_export` |
| Notes | `/notes` |
| Researchers | `/researchers` |
| Guide & FAQ | `/guide` |

Back and Forward work, and any screen can be linked to.

### Fixed — the web studio had no accessibility semantics at all

The web application contained **zero** ARIA attributes, **zero** roles, no
live regions and no `prefers-reduced-motion` support, across 145 animation
classes and seven dialogs.

- **New `Modal` component** used by all seven dialogs — the four standalone
  `*Modal.tsx` files plus three overlays that had been hand-rolled inline
  inside `ScreeningHub` and `NotebookWorkspace`. The harness caught the
  inline ones; a search for `role="dialog"` would not have, because they had
  no role at all. Each one now has
  `role="dialog"` and `aria-modal="true"`, an accessible name and
  description, focus that moves in on open and returns to the trigger on
  close, a focus trap that keeps Tab inside, and Escape to dismiss.
  Previously the keyboard could tab straight out of a dialog into the page
  behind it, and Escape did nothing.
- **Focus lands inside the dialog even in a background tab.** Focus was
  originally moved on the next animation frame only. Browsers throttle (and
  sometimes skip) `requestAnimationFrame` when a tab is not visible, so in
  exactly that case the dialog was announced to a screen reader while focus
  stayed on `<body>` — the reader had nothing to read. Focus is now moved
  immediately and re-checked on the next frame. Caught by driving a real
  browser: `document.body.style.overflow` was `hidden` (proving the effect
  ran) while `document.activeElement` was still `BODY`.
- **Live regions** announce search results, the trending feed and the loading
  state, so a screen-reader user is told when results arrive.
- **`prefers-reduced-motion`** is honoured: movement, fades and the pulsing
  loading indicator are disabled for users who ask for it.
- **Visible focus**: the app had no `:focus-visible` rule, so a keyboard user
  had no way of telling where they were.
- Form fields are now associated with their labels via `htmlFor`/`id`.

### Fixed — the web studio's lint gate

`npm run lint` failed on 46 errors and 53 warnings, all of them in code that
2.1 had not written. CI ran it as `continue-on-error`, which kept the debt
visible but meant nothing was ever fixed. Both are gone: the tree is at
**0 errors, 0 warnings**, and the lint step is a blocking gate again
(`eslint . --max-warnings 0`).

None of it was silenced with `eslint-disable`. The substantive fixes:

- **27 `no-explicit-any`.** Three routes each declared their own OpenAlex
  types and their own copy of `reconstructAbstract`; they now share
  `src/lib/openalex.ts`. The other registries (Crossref, Unpaywall, Semantic
  Scholar) got the same treatment: the fields we read, described, and nothing
  else. Typing the "add to notebook" flow — `src/lib/paper.ts` — exposed a real
  bug: screening results carry their title under `journal`, but the modal read
  `venue`, so a paper added from screening was saved with **no journal name**.
- **9 `react-hooks/purity`.** `Date.now()` and `Math.random()` were being called
  from render-scope functions to mint ids and timestamps. That work moved to
  module-level functions (`addPaperToNotebook`) and into effect bodies, where
  it belongs.
- **5 `react-hooks/set-state-in-effect`.** Each was a mount-time copy of
  external state into React. They are now lazy initialisers, a child dialog
  that mounts only while open (so its fields are seeded from storage on every
  open with no effect at all), or a promise callback with a cancellation flag.
- **The theme.** Light/dark was held in component state in two places, each
  with its own copy of the same read-localStorage-then-set-three-attributes
  effect. The two copies only ran on mount, so they could disagree — toggling
  in the notebook workspace left the header's switch showing the old value.
  It is now one `useSyncExternalStore` store (`src/lib/theme.ts`) shared by
  both, and the accent picker uses the same store.
- **Dead props and 49 unused imports.** `onAddToNotebook` was declared on the
  Screening and Batch Downloader hubs and never called; the citation graph
  demanded `notebooks` and `onInspectPaper` and used neither. Props that imply
  a capability the UI does not have are worse than no props.

Verified afterwards: `npm run lint` (0/0), `npx tsc --noEmit`, `next build`,
and in the browser — theme and accent shared between header and workspace,
persisted across a reload; tokens saved, cleared and re-seeded; a screening
decision and its undo written to IndexedDB and restored after a tab switch;
a paper added from the in-workspace search with its journal intact; the
Trends → Connected Graph hand-off; and a live `/api/download-pdf` call.

### Fixed - three dialogs kept last time's answers

The lint work asked why several dialogs copied external state into React in an
effect. The answer, in three places, was that they were never unmounted: the
dashboard renders them unconditionally and each one returned `null` *after* its
hooks, so every field survived the close.

- **Save to Research Project.** `newTitle` was seeded once, on the app's first
  render, when `paper` was still `null` — so the new-project title box came up
  **empty** instead of prefilled. Worse, `handleSave` set `isSaving` before
  testing the empty title and then returned, leaving the button stuck on
  "Saving..." with the dialog open and no way out but Cancel. The destination
  notebook id was captured at the same first render, so a project created later
  could leave the select pointing at an id that no longer existed, writing an
  orphaned source. The dialog now mounts only while open (same pattern as the
  tokens dialog), seeds its fields from the current paper and notebook list,
  and disables Save — rather than soft-locking — when the title is blank.
- **Create Research Project.** A cancelled or completed draft came back
  pre-filled, files and emoji included, the next time the dialog opened. It now
  starts blank every time, and a failed write reports itself instead of leaving
  the button on "Creating..." forever.
- **Clean Research Workspace.** After cancelling a wipe, reopening the dialog
  still had `delete` typed into the confirmation box and "Wipe All" selected —
  the destructive button was one stray click away, which defeats the point of
  asking for the word. It now resets on every open.

Checked in the browser: adding a search result created a project whose title was
prefilled from the paper, kept its journal, closed cleanly; clearing the title
left Save disabled with the label intact instead of "Saving..."; a second paper
added to the existing vault landed in the same notebook and the count went
1 → 2; a cancelled project draft reopened blank.


### Changed — the accent picker is one control, not four

The header showed four colour swatches side by side — four extra targets in
the top bar, all encoded in colour alone. They are now behind a single
button that opens a listbox whose options have **names**, not just colours.

### Changed — the repository launcher starts the production server

`2_launch_fernly_web_app.bat` always started the dev server, which recompiles
on navigation and shows a dev overlay. It now prefers `next start` and falls
back to the dev server only when no production build exists. It also had a
batch-parsing bug: a closing parenthesis inside an `echo` line terminated the
`if (...)` block early, so the launcher took the *error* branch even with
Node.js installed. The error paths now use `goto` labels, which no `echo` line
can break.

### Removed — a stale duplicate of the source tree

`Vellum_Desktop/Vellum_Desktop_V2.0_Botanical_Bento/` held a second copy of
the desktop source that had already drifted from the real one in eleven
files. Shipping two copies of the source invites the wrong one being edited.
The canonical source is `Vellum_Desktop/Desktop_App/`; the distributable
source drop is `Vellum_Desktop_V2.1_Botanical_Bento.zip`.

### Changed — release engineering

- Every artefact is now produced by a script in `tools/` and hashed.
- `tools/verify_release.py` runs 36 checks, including a clean-room install of
  the installer (install → boot the installed binary → health check →
  uninstall) and a relocation test of the web package (copy to a random path
  → launch → live API calls → stop).
- Archives are written with a fixed timestamp, so an unchanged tree produces
  an identical SHA-256.
- CI (`.github/workflows/release.yml`) re-runs the desktop suite, the
  PyInstaller build, the Inno Setup build, an installer smoke test, the
  TypeScript check, the production build and a live API call on a clean
  runner.
- The build inputs that the build *consumes* — the application icon, the
  `assets/` tree, the favicon — are tracked again. They were excluded by
  `.gitignore`, so a fresh clone could not build the installer at all.
- `.gitattributes` pins `*.bat` to CRLF, so the Windows launchers behave the
  same whatever the reader's `core.autocrlf` setting is.

### Known limitations

- The installer is not code-signed, so SmartScreen warns on first run. The
  published SHA-256 is the way to verify the file.
- The web studio's "Clean Research Workspace" dialog is fully built and mounted
  but nothing opens it: its `isOpen` state has no setter call anywhere. There is
  therefore no in-app way to wipe the local IndexedDB vault; today it takes
  devtools. Wiring a trigger is a product decision (it is a destructive action),
  so it is left as a known gap rather than added unasked.
- The screening hub's legacy-session migration branch (sessions saved before
  `sessionId` existed) is present but no fixture exercises it.

---

## [2.0.0] — 2026-10-21

The Bento editions.

- **Vellum Desktop V2.0** — Active learning screening, Connected Papers citation graph, multi-source LitCheck, batch PDF downloader, bibliographic importer, local PDF vault and PRISMA 2020 export.
- **Vellum Web** — The same workflow as an interactive browser studio on port 3002, with a tri-pane grounded workspace and IndexedDB persistence.
- The Windows installer, the portable bundle, and the source drops.
