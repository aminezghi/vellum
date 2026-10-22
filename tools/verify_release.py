#!/usr/bin/env python3
"""Release verification harness for the Vellum dual pack.

Everything in this script is an *independent* check: it exercises the shipped
artefacts the way a colleague would, rather than re-reading the source and
re-asserting what the source already claims.

    A  repository hygiene       - can the tree rebuild itself?
    B  desktop unit suite       - pytest over Desktop_App/tests
    C  desktop page smoke       - all 10 Streamlit pages import and render
    D  web static analysis      - tsc --noEmit + production build present
    E  desktop installer        - silent install -> run -> health -> uninstall
    F  web share folder         - relocate -> launch -> health -> page -> APIs
    G  artefacts                - SHA-256 manifest + written release report

Usage:
    python tools/verify_release.py                 # everything
    python tools/verify_release.py --only E,F      # a subset
    python tools/verify_release.py --skip-install  # no clean-room install
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DESKTOP = REPO_ROOT / "Vellum_Desktop"
DESKTOP_APP = DESKTOP / "Desktop_App"
WEB = REPO_ROOT / "Vellum_Web"
WEB_APP = WEB / "Web_App_Fernly"
WEB_SHARE = WEB / "Vellum_Web_Fernly_SHARE"
INSTALLER = DESKTOP / "Vellum-Desktop-V2.1-Setup-x64.exe"

WORK = Path(os.environ.get("TEMP", "/tmp")) / "vellum_verify"

GREEN, RED, YELLOW, DIM, RESET = "\033[32m", "\033[31m", "\033[33m", "\033[2m", "\033[0m"


# --------------------------------------------------------------------------
# result plumbing
# --------------------------------------------------------------------------
@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""
    skipped: bool = False
    duration: float = 0.0


@dataclass
class Report:
    checks: list[Check] = field(default_factory=list)

    def add(self, name: str, ok: bool, detail: str = "", skipped: bool = False, dt: float = 0.0) -> None:
        self.checks.append(Check(name, ok, detail, skipped, dt))

    @property
    def failed(self) -> list[Check]:
        return [c for c in self.checks if not c.ok and not c.skipped]

    @property
    def passed(self) -> list[Check]:
        return [c for c in self.checks if c.ok]


def head(title: str) -> None:
    print(f"\n{title}\n{'-' * len(title)}")


def line(check: Check) -> str:
    if check.skipped:
        return f"  {YELLOW}SKIP{RESET}  {check.name} {DIM}({check.detail}){RESET}"
    if check.ok:
        return f"  {GREEN}PASS{RESET}  {check.name} {DIM}{check.detail}{RESET}"
    return f"  {RED}FAIL{RESET}  {check.name} {RED}{check.detail}{RESET}"


# --------------------------------------------------------------------------
# small utilities
# --------------------------------------------------------------------------
def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def http(url: str, timeout: float = 20.0) -> tuple[int, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "VellumVerify/1.0"})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, ""
    except Exception:
        return 0, ""


def port_free(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("127.0.0.1", port))
            return True
        except OSError:
            return False


def wait_healthy(url: str, timeout: float = 90.0) -> tuple[bool, float]:
    t0 = time.time()
    while time.time() - t0 < timeout:
        status, _ = http(url, timeout=3)
        if status == 200:
            return True, time.time() - t0
        time.sleep(0.4)
    return False, time.time() - t0


def kill_tree(pid: int) -> None:
    subprocess.run(
        ["taskkill", "/F", "/T", "/PID", str(pid)],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def run_cmd(cmd: list[str], cwd: Path | None = None, timeout: int = 1800) -> tuple[int, str]:
    exe = shutil.which(cmd[0]) or cmd[0]
    try:
        p = subprocess.run(
            [exe, *cmd[1:]], cwd=str(cwd) if cwd else None,
            capture_output=True, text=True, timeout=timeout,
        )
        return p.returncode, (p.stdout or "") + (p.stderr or "")
    except subprocess.TimeoutExpired:
        return 124, "TIMEOUT"


# ==========================================================================
# A. repository hygiene
# ==========================================================================
def check_hygiene(rep: Report) -> None:
    head("A. Repository hygiene")

    t = time.time()
    code, out = run_cmd(["git", "status", "--porcelain"], cwd=REPO_ROOT)
    # This harness writes RELEASE_REPORT.md and DISTRIBUTABLES/SHA256SUMS.txt
    # itself, so those two are expected to change between runs and must not
    # count as a dirty tree.
    generated = ("RELEASE_REPORT.md", "DISTRIBUTABLES/")
    dirty = [
        ln for ln in out.splitlines()
        if ln.strip() and not ln.startswith("??")
        and not any(g in ln for g in generated)
    ]
    rep.add("git working tree is clean", code == 0 and not dirty,
            "" if not dirty else f"{len(dirty)} modified file(s): {dirty[:3]}",
            dt=time.time() - t)

    t = time.time()
    code, out = run_cmd(["git", "ls-files"], cwd=REPO_ROOT)
    tracked = set(out.split())
    required = [
        "Vellum_Desktop/Desktop_App/downloader.ico",
        "Vellum_Desktop/Desktop_App/downloader.png",
        "Vellum_Desktop/Desktop_App/assets/icon.ico",
        "Vellum_Web/Web_App_Fernly/src/app/favicon.ico",
        "Vellum_Desktop/Desktop_App/build_vellum_windows.spec",
        "Vellum_Desktop/Desktop_App/installer.iss",
        ".gitattributes",
    ]
    missing = [r for r in required if r not in tracked]
    rep.add("build-critical assets are tracked", not missing,
            "" if not missing else f"missing: {missing}", dt=time.time() - t)

    t = time.time()
    bad = []
    for p in REPO_ROOT.rglob("*.bat"):
        s = str(p)
        if any(x in s for x in ("node_modules", "\\.venv\\", "\\dist\\", "\\build\\")):
            continue
        data = p.read_bytes()
        for i, b in enumerate(data):
            if b == 0x0A and (i == 0 or data[i - 1] != 0x0D):
                bad.append(p.relative_to(REPO_ROOT).as_posix())
                break
    rep.add("Windows launchers use CRLF endings", not bad,
            "" if not bad else f"LF-only: {bad[:4]}", dt=time.time() - t)


# ==========================================================================
# B/C. desktop tests
# ==========================================================================
def check_desktop_tests(rep: Report) -> None:
    head("B. Desktop unit suite")
    py = DESKTOP_APP / ".venv" / "Scripts" / "python.exe"
    if not py.is_file():
        rep.add("desktop unit suite", False, f"no interpreter at {py}")
        return
    t = time.time()
    code, out = run_cmd(
        [str(py), "-m", "pytest", "-o", "pythonpath=Desktop_App", "Desktop_App/tests", "-q"],
        cwd=DESKTOP,
    )
    m = re.search(r"(\d+) passed", out)
    n = m.group(1) if m else "?"
    rep.add("pytest Desktop_App/tests", code == 0, f"{n} passed", dt=time.time() - t)

    head("C. Desktop page smoke test")
    t = time.time()
    code, out = run_cmd([str(py), "Desktop_App/tests/smoke_app_pages.py"], cwd=DESKTOP)
    ok = code == 0 and "all 11 scripts ran clean" in out
    rep.add("all 10 Streamlit pages + main app render", ok,
            "11/11 clean" if ok else out.strip().splitlines()[-1][:120] if out.strip() else "no output",
            dt=time.time() - t)


# ==========================================================================
# D. web static analysis
# ==========================================================================
def check_web_build(rep: Report) -> None:
    head("D. Web app static analysis")
    t = time.time()
    code, out = run_cmd(["npx", "tsc", "--noEmit"], cwd=WEB_APP, timeout=900)
    rep.add("TypeScript type-check (tsc --noEmit)", code == 0,
            "0 errors" if code == 0 else out.strip()[:200], dt=time.time() - t)

    t = time.time()
    build_id = WEB_APP / ".next" / "BUILD_ID"
    has_static = (WEB_APP / ".next" / "static").is_dir()
    has_server = (WEB_APP / ".next" / "server").is_dir()
    rep.add("production build present (.next)", build_id.is_file() and has_static and has_server,
            f"BUILD_ID={build_id.read_text().strip() if build_id.is_file() else 'missing'}",
            dt=time.time() - t)


# ==========================================================================
# E. desktop installer clean-room test
# ==========================================================================
def check_installer(rep: Report, do_install: bool = True) -> None:
    head("E. Desktop installer (clean-room)")

    t = time.time()
    if not INSTALLER.is_file():
        rep.add("installer artefact exists", False, f"missing {INSTALLER}")
        return
    size = INSTALLER.stat().st_size
    digest = sha256(INSTALLER)
    rep.add("installer artefact exists", True, f"{size/1024/1024:.1f} MB  sha256={digest[:16]}...",
            dt=time.time() - t)

    t = time.time()
    code, out = run_cmd(
        ["powershell", "-NoProfile", "-Command",
         f"(Get-AuthenticodeSignature -LiteralPath '{INSTALLER}').Status.ToString()"], timeout=120)
    status = out.strip().splitlines()[-1] if out.strip() else "Unknown"
    rep.add("installer Authenticode status", True,
            f"{status} (unsigned installers trigger SmartScreen on first run)", dt=time.time() - t)

    if not do_install:
        rep.add("clean-room install / launch / uninstall", True, "skipped by request", skipped=True)
        return

    target = WORK / "install"
    if target.exists():
        shutil.rmtree(target, ignore_errors=True)
    target.mkdir(parents=True, exist_ok=True)
    log = WORK / "install.log"

    t = time.time()
    code, out = run_cmd(
        [str(INSTALLER), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
         f"/DIR={target}", f"/LOG={log}"], timeout=900)
    exe = target / "Vellum.exe"
    rep.add("silent install succeeds", code == 0 and exe.is_file(),
            f"exit={code} exe={'present' if exe.is_file() else 'MISSING'}", dt=time.time() - t)

    if not exe.is_file():
        return

    t = time.time()
    port = 8501
    for p in range(8501, 8526):
        if port_free(p):
            port = p
            break
    env = os.environ.copy()
    env["VELLUM_SERVER"] = "1"
    env["STREAMLIT_SERVER_PORT"] = str(port)
    env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
    proc = subprocess.Popen([str(exe)], env=env, cwd=str(target),
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    healthy, waited = wait_healthy(f"http://127.0.0.1:{port}/_stcore/health", timeout=120)
    rep.add("installed Vellum.exe serves /_stcore/health", healthy,
            f"HTTP 200 after {waited:.1f}s on port {port}", dt=time.time() - t)

    if healthy:
        t = time.time()
        status, html = http(f"http://127.0.0.1:{port}/", timeout=30)
        rep.add("installed app serves the UI shell", status == 200 and "streamlit" in html.lower(),
                f"HTTP {status}, {len(html)} bytes", dt=time.time() - t)
    kill_tree(proc.pid)
    time.sleep(1.5)

    # The check above exercises the server path. This one exercises the path a
    # colleague actually takes: double-click the installed Vellum.exe, get the
    # native WebView2 window, and be served by it. The launcher picks its own
    # free port, so every candidate is probed.
    t = time.time()
    gui = subprocess.Popen([str(exe)], cwd=str(target),
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    gui_port, gui_ok = 0, False
    deadline = time.time() + 150
    while time.time() < deadline and not gui_ok:
        for p in range(8501, 8526):
            if http(f"http://127.0.0.1:{p}/_stcore/health", timeout=1)[0] == 200:
                gui_port, gui_ok = p, True
                break
        if gui_ok or gui.poll() is not None:
            break
        time.sleep(0.5)
    rep.add("installed Vellum.exe opens its native window and serves", gui_ok,
            f"native app healthy on port {gui_port}" if gui_ok
            else "no native window came up within 150s", dt=time.time() - t)
    kill_tree(gui.pid)
    time.sleep(1.5)

    t = time.time()
    unins = target / "unins000.exe"
    if unins.is_file():
        code, _ = run_cmd([str(unins), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART"], timeout=600)
        time.sleep(2)
        leftover = target.exists() and any(target.iterdir())
        rep.add("silent uninstall removes the install directory", not leftover,
                f"exit={code}", dt=time.time() - t)
    else:
        rep.add("silent uninstall removes the install directory", False, "unins000.exe missing")


# ==========================================================================
# F. web share folder
# ==========================================================================
def check_web_share(rep: Report, relocate: bool = True) -> None:
    head("F. Web share folder")

    t = time.time()
    required = {
        "START_VELLUM_WEB.bat": WEB_SHARE / "START_VELLUM_WEB.bat",
        "STOP_VELLUM_WEB.bat": WEB_SHARE / "STOP_VELLUM_WEB.bat",
        "README.txt": WEB_SHARE / "README.txt",
        "VERSION.txt": WEB_SHARE / "VERSION.txt",
        "SHA256SUMS.txt": WEB_SHARE / "SHA256SUMS.txt",
        "portable node.exe": WEB_SHARE / "runtime" / "node" / "node.exe",
        "production build": WEB_SHARE / "app" / ".next" / "BUILD_ID",
        "next CLI": WEB_SHARE / "app" / "node_modules" / "next" / "dist" / "bin" / "next",
    }
    missing = [k for k, p in required.items() if not p.exists()]
    rep.add("share folder is complete", not missing,
            "" if not missing else f"missing: {missing}", dt=time.time() - t)
    if missing:
        return

    # --- manifest integrity -------------------------------------------------
    t = time.time()
    bad = []
    for ln in (WEB_SHARE / "SHA256SUMS.txt").read_text(encoding="utf-8").splitlines():
        if not ln.strip():
            continue
        digest, rel = ln.split("  ", 1)
        target = WEB_SHARE / rel
        if not target.is_file() or sha256(target) != digest:
            bad.append(rel)
    rep.add("SHA256SUMS.txt verifies every shipped file", not bad,
            "" if not bad else f"{len(bad)} mismatch(es): {bad[:3]}", dt=time.time() - t)

    # --- relocatability -----------------------------------------------------
    base = WEB_SHARE
    tag = "in place"
    if relocate:
        base = WORK / "relocated" / "Vellum Web (copy)"
        t = time.time()
        if base.exists():
            shutil.rmtree(base, ignore_errors=True)
        base.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(WEB_SHARE, base, symlinks=True)
        rep.add("share folder copies to an arbitrary path", True,
                f"{base}", dt=time.time() - t)
        tag = "relocated"

    # --- launch -------------------------------------------------------------
    port = 3002
    for p in range(3002, 3022):
        if port_free(p):
            port = p
            break

    # Guard against a false positive: if something is already listening, the
    # launcher deliberately exits early ("already running") and the health
    # check would then be measuring somebody else's server, not ours.
    t = time.time()
    pre = http(f"http://localhost:{port}/", timeout=3)
    rep.add(f"port {port} is free before the launch", pre[0] == 0,
            "" if pre[0] == 0 else f"something already answers on {port} (HTTP {pre[0]})",
            dt=time.time() - t)
    if pre[0] != 0:
        return

    env = os.environ.copy()
    env["VELLUM_PORT"] = str(port)
    env.pop("NODE_ENV", None)

    console = WORK / "launcher_console.txt"
    t = time.time()
    with console.open("w", encoding="utf-8", errors="replace") as cf:
        proc = subprocess.Popen(
            ["cmd", "/c", str(base / "START_VELLUM_WEB.bat")],
            cwd=str(base), env=env,
            stdout=cf, stderr=subprocess.STDOUT,
            creationflags=0x08000000,  # CREATE_NO_WINDOW
        )
        healthy, waited = wait_healthy(f"http://localhost:{port}/", timeout=150)
    rep.add(f"launcher starts the studio ({tag})", healthy,
            f"HTTP 200 after {waited:.1f}s on port {port}", dt=time.time() - t)

    # The launcher must have really started a server, not bailed out early
    # because it thought a session was already running.
    ctext = console.read_text(encoding="utf-8", errors="replace") if console.exists() else ""
    rep.add("launcher reported a real startup (not an early exit)",
            "Starting the Vellum Web Studio" in ctext,
            "startup banner present" if "Starting the Vellum Web Studio" in ctext
            else f"console said: {ctext.strip()[:140]!r}")

    # The server that answered must be the relocated copy, not a stray process.
    t = time.time()
    cmdlines = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process -Filter \"Name='node.exe'\" | "
         "Select-Object -ExpandProperty CommandLine"],
        capture_output=True, text=True, timeout=120,
    ).stdout
    served_by_copy = str(base).lower() in cmdlines.lower()
    rep.add("the relocated copy is the one serving", served_by_copy,
            "process command line points at the relocated folder" if served_by_copy
            else "no running node process references the relocated folder")

    if healthy:
        t = time.time()
        status, html = http(f"http://localhost:{port}/", timeout=30)
        rep.add("home page renders with the Vellum identity",
                status == 200 and "Vellum" in html,
                f"HTTP {status}, {len(html)} bytes", dt=time.time() - t)

        t = time.time()
        status, body = http(f"http://localhost:{port}/api/search?q=systematic%20review&sources=openalex&fromYear=2020", timeout=60)
        try:
            data = json.loads(body)
            n = data.get("total", 0)
            ok = status == 200 and isinstance(data.get("results"), list)
            detail = f"HTTP {status}, {n} result(s), sources={data.get('sourcesUsed')}"
            if data.get("errors"):
                detail += f", upstream errors={data['errors']}"
        except Exception as e:
            ok, detail = False, f"HTTP {status}, unparseable body ({e})"
        rep.add("live search API returns real records (OpenAlex)", ok, detail, dt=time.time() - t)

        t = time.time()
        status, body = http(f"http://localhost:{port}/api/trends?domain=ai", timeout=60)
        try:
            data = json.loads(body)
            ok = status == 200 and isinstance(data.get("papers"), list)
            detail = f"HTTP {status}, {len(data.get('papers', []))} trending paper(s)"
        except Exception as e:
            ok, detail = False, f"HTTP {status}, unparseable body ({e})"
        rep.add("trends API returns real records (OpenAlex)", ok, detail, dt=time.time() - t)

        t = time.time()
        status, body = http(f"http://localhost:{port}/api/search?q=", timeout=30)
        try:
            data = json.loads(body)
            ok = status == 200 and data.get("total") == 0
            detail = f"HTTP {status}, empty query handled"
        except Exception:
            ok, detail = False, f"HTTP {status}"
        rep.add("empty query is handled gracefully", ok, detail, dt=time.time() - t)

    kill_tree(proc.pid)
    subprocess.run(["cmd", "/c", str(base / "STOP_VELLUM_WEB.bat")],
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    time.sleep(1.5)
    rep.add("studio stops cleanly on request", port_free(port),
            f"port {port} released")


# ==========================================================================
# H. web accessibility
# ==========================================================================
def check_web_accessibility(rep: Report) -> None:
    """Check that the accessibility work is actually in the shipped build.

    These are machine-checkable claims: they assert on the production build
    that colleagues receive, not on the intention.
    """
    head("H. Web accessibility")

    static = WEB_APP / ".next" / "static"
    if not static.is_dir():
        rep.add("production build available for accessibility scan", False,
                "no .next/static")
        return

    blobs = []
    for p in list(static.rglob("*.js")) + list(static.rglob("*.css")):
        try:
            blobs.append(p.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            pass
    corpus = "\n".join(blobs)

    def has(*markers: str) -> bool:
        return all(m in corpus for m in markers)

    t = time.time()
    rep.add("dialogs expose dialog semantics",
            has('role:"dialog"', "aria-modal"),
            'role="dialog" + aria-modal in the shipped bundle', dt=time.time() - t)

    t = time.time()
    rep.add("dialogs carry an accessible name",
            has("aria-labelledby", "aria-describedby"),
            "aria-labelledby + aria-describedby", dt=time.time() - t)

    t = time.time()
    rep.add("asynchronous results are announced",
            "aria-live" in corpus,
            "aria-live live regions", dt=time.time() - t)

    t = time.time()
    rep.add("keyboard focus is visible",
            ":focus-visible" in corpus,
            ":focus-visible rule", dt=time.time() - t)

    t = time.time()
    rep.add("reduced motion is honoured",
            "prefers-reduced-motion" in corpus,
            "prefers-reduced-motion block", dt=time.time() - t)

    t = time.time()
    rep.add("the accent picker is a named listbox",
            has("aria-haspopup", "listbox"),
            "aria-haspopup=listbox + role=listbox", dt=time.time() - t)

    # Every modal must go through the shared primitive. A bare
    # "fixed inset-0" overlay outside Modal.tsx is a dialog that is not a
    # dialog.
    t = time.time()
    offenders = []
    for p in (WEB_APP / "src" / "components").glob("*.tsx"):
        if p.name == "Modal.tsx":
            continue
        if "fixed inset-0" in p.read_text(encoding="utf-8", errors="replace"):
            offenders.append(p.name)
    rep.add("every modal uses the shared accessible primitive", not offenders,
            "" if not offenders else f"hand-rolled overlays: {offenders}",
            dt=time.time() - t)

    # Focus must not depend on requestAnimationFrame alone. Browsers throttle
    # it in a background or occluded tab, and then the dialog is announced to
    # a screen reader while focus stays on <body>.
    t = time.time()
    modal_src = (WEB_APP / "src" / "components" / "Modal.tsx").read_text(
        encoding="utf-8", errors="replace")
    sync_focus = "focusFirst();" in [ln.strip() for ln in modal_src.splitlines()]
    rep.add("dialog focus is not animation-frame-only", sync_focus,
            "focusFirst() also runs synchronously"
            if sync_focus else
            "focus moves only inside requestAnimationFrame - it will not run "
            "in a background tab",
            dt=time.time() - t)

    # The desktop must not advertise a shortcut it does not implement.
    t = time.time()
    desktop_app = DESKTOP_APP
    py_files = [p for p in desktop_app.rglob("*.py")
                if not any(x in p.parts for x in (".venv", "tests", "build", "dist"))]
    js_files = [p for p in desktop_app.rglob("*.html")
                if "keyboard_component" in p.parts]
    has_handler = any(
        any(k in p.read_text(encoding="utf-8", errors="replace")
            for k in ("addEventListener", "onkeydown", "keydown"))
        for p in js_files
    ) if js_files else False
    rep.add("the desktop keyboard shortcut is actually implemented", has_handler,
            "a keydown listener exists in keyboard_component/"
            if has_handler else "no keydown listener found - the buttons lie",
            dt=time.time() - t)


# ==========================================================================
# G. artefacts
# ==========================================================================
def write_artifacts(rep: Report) -> None:
    head("G. Distributable artefacts")

    out = REPO_ROOT / "DISTRIBUTABLES"
    out.mkdir(exist_ok=True)

    targets = [
        INSTALLER,
        DESKTOP / "Vellum_Standalone_Windows_x64.zip",
        DESKTOP / "Vellum_Desktop_V2.1_Botanical_Bento.zip",
        WEB / "Vellum_Web_Fernly_Latest_Export.zip",
        WEB / "Vellum_Web_Fernly_SHARE.zip",
    ]
    rows = []
    for t in targets:
        if t.is_file():
            rows.append((t.name, t.stat().st_size, sha256(t)))
        else:
            rows.append((t.name, 0, "NOT BUILT"))
    for n, s, h in rows:
        print(f"    {n:<46} {s/1024/1024:9.1f} MB  {h[:32]}")

    (out / "SHA256SUMS.txt").write_text(
        "\n".join(f"{h}  {n}" for n, _, h in rows if h != "NOT BUILT") + "\n", encoding="utf-8"
    )
    print(f"    manifest -> {out / 'SHA256SUMS.txt'}")

    now = time.strftime("%Y-%m-%d %H:%M:%S")
    ok = sum(1 for c in rep.checks if c.ok)
    skipped = sum(1 for c in rep.checks if c.skipped)
    failed = rep.failed

    lines = [
        "# Vellum Release Verification Report",
        "",
        f"- **Generated:** {now}",
        f"- **Commit:** `{os.environ.get('VELLUM_COMMIT', 'unknown')}`",
        f"- **Checks:** {ok} passed, {len(failed)} failed, {skipped} skipped",
        "",
        "| # | Check | Result | Detail |",
        "|---|---|---|---|",
    ]
    for i, c in enumerate(rep.checks, 1):
        result = "SKIP" if c.skipped else ("PASS" if c.ok else "FAIL")
        lines.append(f"| {i} | {c.name} | **{result}** | {c.detail} |")
    lines += ["", "## Distributables", "", "| File | Size | SHA-256 |", "|---|---|---|"]
    for n, s, h in rows:
        lines.append(f"| {n} | {s/1024/1024:.1f} MB | `{h}` |")
    lines += [
        "",
        "## How to re-verify independently",
        "",
        "```powershell",
        "# checksum of a received file (no tooling needed beyond Windows)",
        "certutil -hashfile Vellum-Desktop-V2.1-Setup-x64.exe SHA256",
        "",
        "# full harness on this machine",
        "python tools/verify_release.py",
        "```",
        "",
    ]
    (REPO_ROOT / "RELEASE_REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"    report   -> {REPO_ROOT / 'RELEASE_REPORT.md'}")


# ==========================================================================
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--only", default="", help="comma separated section letters, e.g. E,F")
    ap.add_argument("--skip-install", action="store_true", help="skip the clean-room install test")
    ap.add_argument("--no-relocate", action="store_true", help="test the share folder in place")
    args = ap.parse_args()

    only = {s.strip().upper() for s in args.only.split(",") if s.strip()}
    def want(letter: str) -> bool:
        return not only or letter in only

    WORK.mkdir(parents=True, exist_ok=True)
    rep = Report()

    print("=" * 72)
    print("  VELLUM RELEASE VERIFICATION")
    print("=" * 72)

    t0 = time.time()
    if want("A"):
        check_hygiene(rep)
    if want("B"):
        check_desktop_tests(rep)
    if want("D"):
        check_web_build(rep)
    if want("E"):
        check_installer(rep, do_install=not args.skip_install)
    if want("F"):
        check_web_share(rep, relocate=not args.no_relocate)
    if want("H"):
        check_web_accessibility(rep)
    if want("G"):
        write_artifacts(rep)

    head("Summary")
    for c in rep.checks:
        print(line(c))
    ok = len(rep.passed)
    bad = rep.failed
    skipped = sum(1 for c in rep.checks if c.skipped)
    print()
    print(f"  {ok} passed, {len(bad)} failed, {skipped} skipped  in {time.time()-t0:.1f}s")
    print()
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
