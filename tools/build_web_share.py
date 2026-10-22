#!/usr/bin/env python3
"""Build the shareable Vellum Web folder for colleagues.

Produces a self-contained folder that runs on a laptop that has *neither*
Node.js nor Python installed:

    Vellum_Web_Fernly_SHARE/
        START_VELLUM_WEB.bat      <- one double-click, browser opens
        STOP_VELLUM_WEB.bat       <- one double-click, server stops
        README.txt                <- plain-text guide (opens in Notepad)
        VERSION.txt               <- version + provenance of this build
        SHA256SUMS.txt            <- integrity manifest, verifiable offline
        runtime/node/             <- portable Node.js (bundled, no install)
        app/                      <- the Next.js production build

Design notes
------------
* The Node runtime is *bundled*, not merely required. The previous launcher
  hard-failed with "[ERROR] Node.js 18+ was not found", which meant the
  colleague had to install a runtime before they could even try the app.

* `next start` is used rather than Next's `output: 'standalone'` bundle.
  On Windows the standalone generator may fall back to a junction point, and
  the Next.js docs state that a junction stores an *absolute* target, which
  makes that particular output not relocatable. A colleague who unzips the
  folder into "C:\\Users\\<them>\\Downloads" must still get a working app, so
  relocatability wins over the smaller footprint.

* Production dependencies are installed with `npm ci --omit=dev`, which
  resolves strictly from the committed package-lock.json. `npm install` would
  be free to move versions and would break reproducibility.

Usage
-----
    python tools/build_web_share.py \\
        --app   Vellum_Web/Web_App_Fernly \\
        --out   Vellum_Web/Vellum_Web_Fernly_SHARE \\
        --node-zip C:\\path\\to\\node-v24.22.1-win-x64.zip
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Build-output directories inside .next/ that are not needed at runtime.
# `cache` and `dev` are the two large ones (50 MB + 118 MB in the last build).
NEXT_BUILD_SKIP = {"cache", "dev", "diagnostics", "trace", "trace-build", "types"}

# node_modules entries that the *server* never loads at runtime.
#
# The client-only packages below are compiled into .next/static at build time
# (Turbopack bundles them into the client chunks), so the copies in
# node_modules are dead weight in the shipped folder. The rest are build-time
# and dev-tooling only. This is verified, not assumed: tools/verify_release.py
# boots the pruned folder and exercises the home page and every API route.
PRUNE_PACKAGES = [
    "lucide-react",       # 34 MB of SVG icons, bundled into the client chunk
    "dexie",              # IndexedDB wrapper, client side only
    "dexie-react-hooks",  # ditto
    "clsx",               # class-name helper, bundled into the client chunk
    "tailwind-merge",     # ditto
    "@types",             # TypeScript declarations, build time only
    "caniuse-lite",       # browserslist database, build time only
    "csstype",            # TypeScript declarations, build time only
]

PRUNE_TREES = [
    "next/dist/docs",            # 3 MB of Markdown shipped inside the package
    "next/dist/bundle-analyzer", # dev tool
    "next/dist/esm",             # ESM build; `next start` uses the CJS build
]


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def human(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.1f} {unit}" if unit != "B" else f"{n} B"
        n /= 1024.0
    return f"{n:.1f} GB"


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_size(path: Path) -> int:
    return sum(p.stat().st_size for p in path.rglob("*") if p.is_file())


def copytree_filtered(src: Path, dst: Path, skip: set[str] | None = None) -> None:
    """Copy a tree, skipping top-level entries whose name is in `skip`."""
    skip = skip or set()
    dst.mkdir(parents=True, exist_ok=True)
    for item in src.iterdir():
        if item.name in skip:
            continue
        target = dst / item.name
        if item.is_dir():
            shutil.copytree(item, target, dirs_exist_ok=True)
        else:
            shutil.copy2(item, target)


def run(cmd: list[str], cwd: Path) -> None:
    # On Windows `npm` is a .cmd shim. CreateProcess only appends .exe, so the
    # bare name would not resolve; shutil.which honours PATHEXT and finds it.
    exe = shutil.which(cmd[0])
    if exe is None:
        raise SystemExit(f"required tool not found on PATH: {cmd[0]}")
    cmd = [exe, *cmd[1:]]
    print(f"    $ {' '.join(cmd)}")
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout[-4000:])
        sys.stderr.write(proc.stderr[-4000:])
        raise SystemExit(f"command failed ({proc.returncode}): {' '.join(cmd)}")


# --------------------------------------------------------------------------
# launcher scripts
# --------------------------------------------------------------------------
START_BAT = r"""@echo off
setlocal enabledelayedexpansion
title Vellum Web - Fernly Botanical Bento Edition
cd /d "%~dp0"

set "NODE=%~dp0runtime\node\node.exe"
set "APPDIR=%~dp0app"
set "PORT=3002"
if not "%VELLUM_PORT%"=="" set "PORT=%VELLUM_PORT%"
set "URL=http://localhost:%PORT%"

cls
echo =====================================================================
echo       VELLUM WEB - FERNLY BOTANICAL BENTO EDITION
echo       Academic Research Studio - local, private, no account needed
echo =====================================================================
echo.

if not exist "%NODE%" (
    echo [ERROR] The bundled Node.js runtime is missing.
    echo         Expected: "%NODE%"
    echo         Please re-extract the complete Vellum_Web folder.
    echo.
    pause
    exit /b 1
)

if not exist "%APPDIR%\.next\BUILD_ID" (
    echo [ERROR] The application build is missing.
    echo         Expected: "%APPDIR%\.next\BUILD_ID"
    echo         Please re-extract the complete Vellum_Web folder.
    echo.
    pause
    exit /b 1
)

rem ---- Is a Vellum session already listening on the port? ----
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $r = Invoke-WebRequest -Uri 'http://localhost:%PORT%' -UseBasicParsing -TimeoutSec 4; if ($r.StatusCode -eq 200 -and $r.Content -match 'Vellum') { exit 0 } } catch {}; exit 1" >nul 2>&1
if %errorlevel%==0 (
    echo [*] Vellum Web is already running on port %PORT%.
    echo     Opening it in your browser...
    start "" "%URL%"
    exit /b 0
)

rem ---- Is the port occupied by something else? ----
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { $c = New-Object Net.Sockets.TcpClient; $c.Connect('127.0.0.1', %PORT%); $c.Close(); exit 0 } catch { exit 1 }" >nul 2>&1
if %errorlevel%==0 (
    echo [ERROR] Port %PORT% is already in use by another program.
    echo         Close that program, or start Vellum on a different port by
    echo         running:  set VELLUM_PORT=3100  then run this file again.
    echo.
    pause
    exit /b 1
)

echo [*] Starting the Vellum Web Studio...
echo [*] Interface: %URL%
echo.
echo     This window is the server. Keep it open while you work.
echo     Close this window (or press Ctrl+C) to stop Vellum.
echo.

rem ---- Open the browser as soon as the server answers ----
start "" /b powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command ^
  "$u='%URL%'; for ($i=0; $i -lt 120; $i++) { try { if ((Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 2).StatusCode -eq 200) { Start-Process $u; break } } catch {}; Start-Sleep -Milliseconds 500 }"

rem ---- Run the server in the foreground so closing this window stops it ----
cd /d "%APPDIR%"
set "PORT=%PORT%"
set "HOSTNAME=127.0.0.1"
set "NODE_ENV=production"
set "NEXT_TELEMETRY_DISABLED=1"
"%NODE%" "%APPDIR%\node_modules\next\dist\bin\next" start -p %PORT%

echo.
echo [INFO] Vellum Web has stopped.
pause
"""

STOP_BAT = r"""@echo off
setlocal enabledelayedexpansion
title Stop Vellum Web
cd /d "%~dp0"

set "PORT=3002"
if not "%VELLUM_PORT%"=="" set "PORT=%VELLUM_PORT%"

echo Stopping the Vellum Web Studio on port %PORT%...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$c = Get-NetTCPConnection -LocalPort %PORT% -State Listen -ErrorAction SilentlyContinue; if ($c) { $c | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue; Write-Output ('  stopped PID ' + $_.OwningProcess) } } else { Write-Output '  nothing was listening on port %PORT%' }"

echo.
echo Done. You can close this window.
timeout /t 3 >nul
"""

README_TXT = """\
VELLUM WEB - FERNLY BOTANICAL BENTO EDITION
Academic Research Studio (Windows)

=====================================================================
HOW TO START (one double-click)
=====================================================================

1. Extract this whole folder somewhere permanent, for example:
       C:\\Vellum_Web

   IMPORTANT - extract the COMPLETE folder. Do not move individual
   files out of it. The application, the Node.js runtime and the
   launcher have to stay next to each other.

2. Double-click:  START_VELLUM_WEB.bat

3. Wait a few seconds. Your browser opens automatically at
   http://localhost:3002

4. Work as usual. Your notebooks and screening sessions are stored in
   your own browser, on your own machine. Nothing is uploaded.

5. To stop Vellum, close the black server window (or press Ctrl+C in
   it). If the window was closed by accident, double-click
   STOP_VELLUM_WEB.bat


=====================================================================
WHAT YOU NEED - AND WHAT YOU DO NOT NEED
=====================================================================

You do NOT need to install anything:
  * No Node.js      (a portable runtime is bundled in runtime\\node)
  * No Python       (not used by the web studio)
  * No internet connection is required to start the app, although the
    live literature search needs one to reach OpenAlex, arXiv, PubMed
    and Crossref.


=====================================================================
IF SOMETHING GOES WRONG
=====================================================================

"Port 3002 is already in use"
  Another program (or an older Vellum) holds the port. Close it, or run
  START_VELLUM_WEB.bat from a command prompt with a different port:

      set VELLUM_PORT=3100
      START_VELLUM_WEB.bat

  Note: the port is also the address the browser uses to store your
  notebooks, so 3002 is the recommended one.

"The bundled Node.js runtime is missing"
  The folder was not extracted completely. Re-extract it.

The page loads but is blank
  Hard-reload with Ctrl+F5. If that does not help, delete the folder
  "C:\\Users\\<you>\\AppData\\Local\\Temp\\next-cache" and start again.

The browser does not open by itself
  Open http://localhost:3002 manually.


=====================================================================
PRIVACY
=====================================================================

Everything runs on your machine. There is no account, no cloud, no
telemetry. Search queries are sent only to the public academic APIs
you are searching, exactly as a browser would.


=====================================================================
CREDITS
=====================================================================

Vellum - Academic Research Suite
Developer & Lead Architect: Amine Zouaghi
License: MIT

---------------------------------------------------------------------
Version: {version}
Built:   {built}
Node.js: {node_version} (bundled, portable)
=====================================================================
"""


# --------------------------------------------------------------------------
# build steps
# --------------------------------------------------------------------------
def stage_app(app_dir: Path, out_app: Path) -> None:
    """Copy the production build and install production dependencies."""
    build_id = app_dir / ".next" / "BUILD_ID"
    if not build_id.is_file():
        raise SystemExit(
            f"no production build found at {build_id}\n"
            "run 'npx next build' in the app directory first"
        )

    print("  staging production build ...")
    copytree_filtered(app_dir / ".next", out_app / ".next", skip=NEXT_BUILD_SKIP)

    print("  copying public assets ...")
    if (app_dir / "public").is_dir():
        shutil.copytree(app_dir / "public", out_app / "public", dirs_exist_ok=True)

    print("  copying package manifests ...")
    for name in ("package.json", "package-lock.json", "next.config.ts"):
        src = app_dir / name
        if src.is_file():
            shutil.copy2(src, out_app / name)

    print("  installing production dependencies (npm ci --omit=dev) ...")
    run(["npm", "ci", "--omit=dev", "--no-audit", "--no-fund"], cwd=out_app)


def prune_runtime(out_app: Path) -> tuple[int, int]:
    """Remove packages the server never loads. Returns (bytes_before, bytes_after)."""
    nm = out_app / "node_modules"
    if not nm.is_dir():
        return 0, 0
    before = sum(p.stat().st_size for p in nm.rglob("*") if p.is_file())
    for name in PRUNE_PACKAGES:
        target = nm / name
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    for tree in PRUNE_TREES:
        target = nm / tree
        if target.exists():
            shutil.rmtree(target, ignore_errors=True)
    after = sum(p.stat().st_size for p in nm.rglob("*") if p.is_file())
    return before, after


def stage_runtime(node_zip: Path, out_runtime: Path) -> str:
    """Extract the portable Node.js runtime. Returns the node version."""
    print("  extracting portable Node.js runtime ...")
    out_runtime.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(node_zip) as zf:
        zf.extractall(out_runtime)

    # The zip contains a top-level "node-vX.Y.Z-win-x64/" folder; flatten it.
    entries = list(out_runtime.iterdir())
    if len(entries) == 1 and entries[0].is_dir():
        inner = entries[0]
        for item in list(inner.iterdir()):
            shutil.move(str(item), str(out_runtime / item.name))
        inner.rmdir()

    node_exe = out_runtime / "node.exe"
    if not node_exe.is_file():
        raise SystemExit(f"node.exe not found after extracting {node_zip}")
    ver = subprocess.run(
        [str(node_exe), "--version"], capture_output=True, text=True
    ).stdout.strip()
    return ver


def write_manifest(out: Path) -> Path:
    """Write SHA256SUMS.txt over every shipped file (except the manifest)."""
    manifest = out / "SHA256SUMS.txt"
    rows = []
    for p in sorted(out.rglob("*")):
        if not p.is_file() or p == manifest:
            continue
        rows.append(f"{sha256(p)}  {p.relative_to(out).as_posix()}")
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return manifest


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--app", default=str(REPO_ROOT / "Vellum_Web" / "Web_App_Fernly"))
    ap.add_argument("--out", default=str(REPO_ROOT / "Vellum_Web" / "Vellum_Web_Fernly_SHARE"))
    ap.add_argument("--node-zip", required=True, help="path to node-vX-win-x64.zip")
    ap.add_argument("--version", default="2.0.0")
    ap.add_argument("--no-prune", action="store_true",
                    help="keep build-time-only packages in node_modules")
    args = ap.parse_args()

    app_dir = Path(args.app).resolve()
    out = Path(args.out).resolve()
    node_zip = Path(args.node_zip).resolve()

    if not node_zip.is_file():
        raise SystemExit(f"node runtime zip not found: {node_zip}")

    t0 = time.time()
    print(f"Vellum Web share build")
    print(f"  source : {app_dir}")
    print(f"  output : {out}")
    print()

    if out.exists():
        print("  removing previous share folder ...")
        shutil.rmtree(out)
    out.mkdir(parents=True)

    out_app = out / "app"
    out_app.mkdir()
    stage_app(app_dir, out_app)

    if not args.no_prune:
        print("  pruning build-time-only packages from node_modules ...")
        before, after = prune_runtime(out_app)
        print(f"    node_modules {human(before)} -> {human(after)} "
              f"(saved {human(before - after)})")

    node_version = stage_runtime(node_zip, out / "runtime" / "node")

    print("  writing launchers and documentation ...")
    (out / "START_VELLUM_WEB.bat").write_text(START_BAT, encoding="utf-8", newline="\r\n")
    (out / "STOP_VELLUM_WEB.bat").write_text(STOP_BAT, encoding="utf-8", newline="\r\n")

    built = time.strftime("%Y-%m-%d %H:%M:%S %Z")
    (out / "README.txt").write_text(
        README_TXT.format(version=args.version, built=built, node_version=node_version),
        encoding="utf-8",
        newline="\r\n",
    )
    (out / "VERSION.txt").write_text(
        "Vellum Web - Fernly Botanical Bento Edition\n"
        f"Version      : {args.version}\n"
        f"Built        : {built}\n"
        f"Node.js      : {node_version} (portable, bundled - no install required)\n"
        f"Next.js      : {json.loads((out_app / 'package.json').read_text())['dependencies']['next']}\n"
        f"Source commit: {os.environ.get('VELLUM_COMMIT', 'n/a')}\n",
        encoding="utf-8",
    )

    print("  writing integrity manifest ...")
    manifest = write_manifest(out)

    total = dir_size(out)
    print()
    print(f"  share folder : {out}")
    print(f"  size         : {human(total)}")
    print(f"  files        : {sum(1 for p in out.rglob('*') if p.is_file())}")
    print(f"  manifest     : {manifest.name} ({sum(1 for _ in manifest.read_text().splitlines())} entries)")
    print(f"  elapsed      : {time.time() - t0:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
