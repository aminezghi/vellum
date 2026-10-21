"""Folder selection helpers: a native picker where one exists, plus a manual browser.

Streamlit has no directory-upload widget and no cross-platform folder dialog,
so this offers both routes:

* ``native_folder_dialog`` uses the best chooser the host actually has -- the
  macOS "choose folder" panel via osascript, Tk's own dialog on Windows, and
  ``zenity``/``kdialog`` on Linux. It returns None wherever none is available.
* ``render_folder_picker`` is the portable fallback that always works -- a path
  field, a parent step and the list of subdirectories -- and is what the Browse
  button falls back to.
"""

from __future__ import annotations

import json
import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path

APP_DIR = Path(os.path.expanduser("~/.vellum"))
RECENT_FILE = APP_DIR / "recent_dirs.json"
MAX_RECENT = 12


def is_macos() -> bool:
    return platform.system() == "Darwin"


def native_dialog_backend() -> str:
    """Which folder chooser this machine can offer, or "none".

    Naming the backend matters because the answer reaches the UI: telling a
    Linux user "macOS only" for a button that could have worked was wrong, and
    silently disabling it was worse than saying which chooser is missing.
    """
    if is_macos():
        return "macOS chooser" if shutil.which("osascript") else "none"
    if sys.platform == "win32":
        # Tk ships with python.org installers; distro Pythons often lack it.
        try:
            import tkinter  # noqa: F401
        except Exception:
            return "none"
        return "Windows dialog"
    for tool in ("zenity", "kdialog"):
        if shutil.which(tool):
            return tool
    try:
        import tkinter  # noqa: F401
        return "Tk dialog"
    except Exception:
        return "none"


def native_folder_dialog(prompt="Select a folder", default_dir=None):
    """Open the host's folder chooser. Returns a path, or None if cancelled.

    Blocks until the user picks, so only call it from a button handler.
    """
    backend = native_dialog_backend()
    if backend == "none":
        return None

    if backend == "macOS chooser":
        # The prompt is interpolated into AppleScript source, so a quote in it
        # would end the string early.
        safe = prompt.replace("\\", "\\\\").replace('"', '\\"')
        script = f'POSIX path of (choose folder with prompt "{safe}")'
        argv = ["osascript", "-e", script]
    elif backend == "Windows dialog":
        # 1. Try PowerShell WinForms FolderBrowserDialog (runs in STA subprocess, works across threads & PyInstaller)
        try:
            safe_p = prompt.replace("'", "''")
            init_cmd = ""
            if default_dir and Path(default_dir).is_dir():
                safe_def = str(Path(default_dir).resolve()).replace("'", "''")
                init_cmd = f"$f.SelectedPath = '{safe_def}'; "
            ps_cmd = (
                "$ErrorActionPreference = 'Stop'; "
                "[System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms') | Out-Null; "
                "$top = New-Object System.Windows.Forms.Form; "
                "$top.TopMost = $true; "
                "$f = New-Object System.Windows.Forms.FolderBrowserDialog; "
                f"$f.Description = '{safe_p}'; "
                f"{init_cmd}"
                "$f.ShowNewFolderButton = $true; "
                "if ($f.ShowDialog($top) -eq [System.Windows.Forms.DialogResult]::OK) { [Console]::WriteLine($f.SelectedPath) }; "
                "$top.Dispose()"
            )
            res = subprocess.run(
                ["powershell", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
                capture_output=True,
                text=True,
                timeout=60,
            )
            out = res.stdout.strip()
            if out and Path(out).is_dir():
                return out
        except Exception:
            pass

        # 2. Fallback to Tkinter
        try:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            root.attributes("-topmost", True)
            init_dir = str(default_dir) if (default_dir and Path(default_dir).is_dir()) else None
            chosen = filedialog.askdirectory(title=prompt, initialdir=init_dir, mustexist=True)
            root.destroy()
            return chosen or None
        except Exception:
            return None
    else:
        if backend == "zenity":
            argv = ["zenity", "--file-selection", "--directory",
                    f"--title={prompt}"]
        elif backend == "kdialog":
            argv = ["kdialog", "--getexistingdirectory", os.path.expanduser("~"),
                    "--title", prompt]
        else:
            try:
                import tkinter as tk
                from tkinter import filedialog
                root = tk.Tk()
                root.withdraw()
                root.attributes("-topmost", True)
                chosen = filedialog.askdirectory(title=prompt, mustexist=True)
                root.destroy()
                return chosen or None
            except Exception:
                return None

    try:
        out = subprocess.run(argv, capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        return None
    except Exception:
        return None
    if out.returncode != 0:
        # A non-zero status is a cancel for all three of these tools.
        return None
    return (out.stdout or "").strip() or None


def default_roots():
    """Sensible starting places, most likely first."""
    home = Path.home()
    candidates = [
        home / "Desktop",
        home / "Documents",
        home / "Downloads",
        home / "Library" / "Containers" / "com.apple.mail" / "Downloads",
        home,
        Path("/Volumes"),
    ]
    seen, out = set(), []
    for c in candidates:
        s = str(c)
        if s not in seen and Path(s).is_dir():
            seen.add(s)
            out.append(s)
    return out


def load_recent():
    try:
        if RECENT_FILE.exists():
            data = json.loads(RECENT_FILE.read_text())
            if isinstance(data, list):
                return [p for p in data if Path(p).is_dir()]
    except Exception:
        pass
    return []


def remember(path):
    if not path:
        return
    try:
        path = str(Path(path).expanduser())
        if not Path(path).is_dir():
            return
        recent = [p for p in load_recent() if p != path]
        recent.insert(0, path)
        APP_DIR.mkdir(parents=True, exist_ok=True)
        RECENT_FILE.write_text(json.dumps(recent[:MAX_RECENT], indent=1))
    except Exception:
        pass


def clear_recent():
    """Wipe the persisted recent-folders list."""
    try:
        if RECENT_FILE.exists():
            RECENT_FILE.unlink()
    except Exception:
        pass


def subdirs(path):
    """Immediate subdirectories, hidden entries excluded, sorted."""
    try:
        p = Path(path).expanduser()
        if not p.is_dir():
            return []
        out = []
        for child in p.iterdir():
            if not child.is_dir() or child.name.startswith("."):
                continue
            try:
                if child.is_symlink() and not child.resolve().is_dir():
                    continue
            except OSError:
                continue
            out.append(child)
        return sorted(out, key=lambda c: c.name.lower())
    except (PermissionError, OSError):
        return []


def pdf_count(path, recursive=False):
    try:
        root = Path(path).expanduser()
        pat = "**/*" if recursive else "*"
        # Suffix match, not a "*.pdf" glob: the glob misses PAPER.PDF on a
        # case-sensitive filesystem. See vellum_analysis.list_pdfs.
        return sum(1 for p in root.glob(pat)
                   if p.is_file() and p.suffix.lower() == ".pdf")
    except Exception:
        return 0


def _parent_of(path_text):
    """The folder one level up, or None at the filesystem root / if invalid."""
    text = (path_text or "").strip()
    if not text:
        return None
    try:
        p = Path(text).expanduser()
        if not p.is_dir() or p == Path(p.anchor):
            return None
        return p.parent
    except (OSError, ValueError):
        return None


def render_folder_picker(label="Folder", key="folder_picker", default=None,
                         recursive=False, show_pdfs=True):
    """Portable folder chooser. Returns the selected path or None."""
    import streamlit as st

    state_key = f"{key}_path"
    pending_key = f"{key}_pending"

    # Streamlit forbids writing to a session_state key that is already bound to
    # an instantiated widget, and the path field below owns ``state_key``. Any
    # navigation requested by a button therefore queues the new path in
    # ``pending_key`` and applies it here, before the field is created.
    pending = st.session_state.pop(pending_key, None)
    if pending is not None:
        st.session_state[state_key] = pending

    # No default folder — user must choose.
    if state_key not in st.session_state:
        st.session_state[state_key] = default or ""

    st.markdown(f"**{label}**")
    col_a, col_up, col_b = st.columns([5, 2, 2])
    with col_a:
        typed = st.text_input(
            "Path", key=state_key, label_visibility="collapsed",
            help="Type or paste an absolute folder path.")

    # Icon first, label second, `secondary`, stretch: the same shape as Browse
    # beside it, so the two read as one control pair. "arrow_upward" is the real
    # Material icon name; Streamlit renders an unknown name as literal text,
    # which is what turned this into a button reading "arrow_up Downloads".
    up_target = _parent_of(typed)
    up_name = (up_target.name or str(up_target)) if up_target else None
    with col_up:
        if st.button(f":material/arrow_upward: {up_name}" if up_name
                     else ":material/arrow_upward: Up", key=f"{key}_up",
                     width="stretch", disabled=up_target is None,
                     type="secondary",
                     help=(f"Go up to {up_target}"
                           if up_target else "Already at the top level")):
            st.session_state[pending_key] = str(up_target)
            st.rerun()

    backend = native_dialog_backend()
    with col_b:
        opened = st.button(":material/folder_open: Browse", key=f"{key}_native",
                           width="stretch", disabled=(backend == "none"),
                           type="secondary",
                           help=(f"Open the {backend}"
                                 if backend != "none" else
                                 "No native folder chooser on this system — "
                                 "type the path instead"))
    if opened:
        chosen = native_folder_dialog(f"Select {label.lower()}")
        if chosen:
            remember(chosen)
            st.session_state[pending_key] = chosen
            st.rerun()
        else:
            # Cancelling must not look like a failure: leave the field alone and
            # rerun so the page returns to its previous state.
            st.rerun()

    current = (st.session_state.get(state_key) or "").strip()
    valid = bool(current) and Path(current).expanduser().is_dir()

    if not valid:
        st.caption("Enter or browse for an existing folder.")
        if current:
            st.warning(f"`{current}` is not a folder.")
        return None

    remember(current)
    p = Path(current).expanduser()

    # Breadcrumb: every ancestor, newest last. The root is found by asking each
    # ancestor for its parent rather than comparing against "/", which is only
    # the root on POSIX -- on Windows "C:\" has parent "C:\" too, so a string
    # comparison never matched and the trail ended in an empty segment.
    crumbs = []
    node = p
    while True:
        parent = node.parent
        if parent == node:
            break
        crumbs.append(node)
        node = parent
    crumbs = list(reversed(crumbs))[-4:]
    trail = " › ".join("Home" if c == Path.home() else (c.name or str(c))
                       for c in crumbs)
    if p not in crumbs:
        trail = (trail + " › " + (p.name or str(p))) if trail else str(p)
    st.caption(f"`{trail}`")

    children = subdirs(p)
    if children:
        st.caption(f"{len(children)} subfolder(s)")
        labels = {f"{c.name}  ·  {pdf_count(c, recursive)}": c for c in children}
        chosen_label = st.selectbox(
            "Subfolder", list(labels), key=f"{key}_sub",
            label_visibility="collapsed")
        enter = st.button(":material/subdirectory_arrow_right: Open", key=f"{key}_go",
                          width="stretch")
        if enter:
            st.session_state[pending_key] = str(labels[chosen_label])
            st.rerun()
    else:
        st.caption("No subfolders here.")

    if show_pdfs:
        n = pdf_count(p, recursive)
        st.caption(f"**{n}** PDF file(s) here"
                   + (" (including subfolders)" if recursive else ""))

    return str(p)