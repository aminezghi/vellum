# Building & Releasing Vellum

This document is for whoever maintains this repository next. It describes how
the shipped artefacts are produced and, more importantly, **how to prove they
are correct** — without trusting the person who built them.

---

## 0. The one-paragraph version

Two applications are shipped: a frozen Python desktop app (with a Windows
installer) and a Next.js web studio (with a self-contained one-click folder).
Every artefact is produced by a script in `tools/`, every artefact is hashed,
and a single command — `tools/verify_release.py` — exercises the *shipped
files* the way a colleague would: it installs the installer, boots the
installed binary, relocates the web folder to a random path, and calls the
live APIs. The same checks run unattended in CI on every push.

---

## 1. Prerequisites

| Tool | Version | Used for | How to get it |
| :--- | :--- | :--- | :--- |
| Python | 3.13 | desktop app, build scripts | `winget install Python.Python.3.13` |
| Node.js | 24 LTS | web app build | `winget install OpenJS.NodeJS.LTS` |
| PyInstaller | 6.22 | frozen desktop bundle | already pinned in `requirements.txt` |
| Inno Setup | 6.7 | the `.exe` installer | `winget install JRSoftware.InnoSetup` |
| Node runtime (portable) | v24.22.1 LTS | bundled in the web share folder | `https://nodejs.org/dist/` |

Inno Setup is **not** on `PATH` by default. Its compiler lives at:

```
%LOCALAPPDATA%\Programs\Inno Setup 6\ISCC.exe     (per-user install)
C:\Program Files (x86)\Inno Setup 6\ISCC.exe      (system install)
```

---

## 2. Build everything

```powershell
# from the repository root
$py = "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe"

# 1. desktop: tests first - do not ship a failing build
cd Vellum_Desktop
& Desktop_App\.venv\Scripts\python.exe -m pytest -o pythonpath=Desktop_App Desktop_App\tests -q
& Desktop_App\.venv\Scripts\python.exe Desktop_App\tests\smoke_app_pages.py
cd ..

# 2. desktop: frozen bundle
cd Vellum_Desktop\Desktop_App
& .venv\Scripts\python.exe -m PyInstaller --noconfirm --clean build_vellum_windows.spec
cd ..\..

# 3. desktop: installer
cd Vellum_Desktop\Desktop_App
& "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe" installer.iss
cd ..\..

# 4. web: production build
cd Vellum_Web\Web_App_Fernly
npx tsc --noEmit
npx next build
cd ..\..

# 5. web: self-contained share folder
& $py tools\build_web_share.py --node-zip C:\path\to\node-v24.22.1-win-x64.zip

# 6. all the archives
& $py tools\build_distributables.py
```

> **Always verify the portable Node runtime against the publisher's checksum
> list before bundling it.** The runtime is a third-party binary that ends up
> on other people's machines:
>
> ```powershell
> $pub = (Invoke-WebRequest https://nodejs.org/dist/v24.22.1/SHASUMS256.txt).Content
> $expected = ($pub -split "`n" | Select-String 'node-v24.22.1-win-x64.zip').ToString().Split()[0]
> $actual = (Get-FileHash node-v24.22.1-win-x64.zip -Algorithm SHA256).Hash
> if ($expected -ne $actual) { throw "Node runtime checksum mismatch - do not ship" }
> ```

---

## 3. Verify everything

```powershell
& "Vellum_Desktop\Desktop_App\.venv\Scripts\python.exe" tools\verify_release.py
```

This writes `RELEASE_REPORT.md` (the full table of results) and
`DISTRIBUTABLES\SHA256SUMS.txt`.

### What it actually does

| Section | Check |
| :--- | :--- |
| **A** | working tree clean · brand assets tracked · `.bat` files have CRLF endings |
| **B** | `pytest Desktop_App/tests` |
| **C** | all 10 Streamlit pages + the main app render (`smoke_app_pages.py`) |
| **D** | `tsc --noEmit` · production build present |
| **E** | **silent install → boot the installed `Vellum.exe` → HTTP 200 → silent uninstall** |
| **F** | **copy the web folder to a random path → launch it → HTTP 200 → live API calls → stop** |
| **G** | SHA-256 manifest of every distributable |

Section F is deliberately paranoid. The launcher deliberately exits early when
it finds a session already listening on the port, so a naive health check
would happily measure *someone else's* server. The harness therefore asserts
the port is free before the launch, captures the launcher's console output,
and confirms the running process's command line points at the relocated copy.

### Why section E matters

The unit suite and the page smoke test both run against **source**. They say
nothing about the frozen bundle, which is what a colleague actually installs.
Section E is the only thing that closes that gap.

---

## 4. How a colleague can verify without trusting us

```powershell
certutil -hashfile Vellum-Desktop-V2.0-Setup-x64.exe SHA256
```

Compare with `DISTRIBUTABLES\SHA256SUMS.txt` (or the `SHA256SUMS.txt` inside
the web share folder). A colleague can do this with nothing but Windows
installed.

### SmartScreen

The installer is **not code-signed** (a signing certificate is not available
for this project), so Windows SmartScreen shows *"Windows protected your
PC"* on first run. This is expected. Tell colleagues to click
**More info → Run anyway**, and explain why: the file is unsigned, not
malicious. The published SHA-256 is the way to make that claim checkable.

---

## 5. CI

`.github/workflows/release.yml` runs on every push and pull request:

- **desktop** — pytest, page smoke test, PyInstaller, Inno Setup, and an
  install → boot → health → uninstall smoke test of the produced installer
- **web** — `npm ci`, `tsc --noEmit`, `eslint`, `next build`, then boots the
  production build and calls the live search API
- **release** — hashes the artefacts and publishes `SHA256SUMS.txt`
- **release-notes** — drafts the notes with the hashes embedded

Nothing is trusted from a developer's machine.

---

## 6. Layout of the shipped artefacts

| Artefact | Audience | Notes |
| :--- | :--- | :--- |
| `Vellum_Desktop\Vellum-Desktop-V2.0-Setup-x64.exe` | colleagues | per-user install, no admin, no Python |
| `Vellum_Desktop\Vellum_Standalone_Windows_x64.zip` | colleagues | portable bundle, unzip and run `Vellum.exe` |
| `Vellum_Desktop\Vellum_Desktop_V2.0_Botanical_Bento.zip` | developers | source drop (no venv, no binaries) |
| `Vellum_Web\Vellum_Web_Fernly_Latest_Export.zip` | developers | web source export |
| `Vellum_Web\Vellum_Web_Fernly_SHARE.zip` | colleagues | **one-click** — portable Node bundled |

---

## 7. Design decisions worth keeping

**The web share folder bundles Node.js instead of requiring it.** The old
launcher hard-failed with *"[ERROR] Node.js 18+ was not found"*, which meant
a colleague had to install a runtime before they could even try the app. The
runtime is now verified against `nodejs.org`'s own `SHASUMS256.txt` and
shipped inside the folder.

**`next start`, not `output: 'standalone'`.** Next's standalone bundle is
smaller, but on Windows the generator may fall back to a junction point, and
the Next.js documentation states that a junction stores an *absolute* target,
making that output not relocatable. A colleague who unzips the folder into
`C:\Users\<them>\Downloads` must still get a working app, so relocatability
wins over the smaller footprint.

**`npm ci --omit=dev`, not `npm install`.** `npm ci` resolves strictly from
the committed `package-lock.json`; `npm install` is free to move versions and
would break reproducibility.

**The build-time-only packages are pruned from the shipped `node_modules`.**
`lucide-react`, `dexie`, `clsx` and friends are compiled into the client
chunks at build time, so the copies in `node_modules` are dead weight
(67 MB). This is verified, not assumed — section F boots the pruned folder
and exercises every route.

**Archives are written with a fixed timestamp.** An unchanged tree produces a
byte-identical archive and therefore an identical SHA-256, so a changed hash
always means changed content.

---

## 8. Known limitations

- The installer is unsigned; SmartScreen will warn on first run.
- The web share folder is ~414 MB unpacked (~100 MB zipped) because it ships a
  complete Node.js runtime and the Next.js server.
- The clean-room test in section E runs on the build machine. A genuinely
  independent check is a Windows Sandbox or a colleague's laptop; the CI
  workflow gets closer by running on a fresh runner.
