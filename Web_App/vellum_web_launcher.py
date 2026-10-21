#!/usr/bin/env python3
"""
Vellum Web Launcher — Standalone Desktop Manager for Vellum Web 2.4.
Author: Amine Zouaghi

Features:
  - Minimalist floating card UI matching Vellum's palette
  - Automatic background Next.js server start (hidden terminal)
  - 1-Click Launch into dedicated Native Desktop App Window (--app mode)
  - Process tree supervisor with clean Node.js / Next.js shutdown
  - Built-in Diagnostic Log Viewer and 1-click Restart
"""

from __future__ import annotations

import atexit
import os
import platform
import shutil
import socket
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

import tkinter as tk
from tkinter import messagebox, font as tkfont

APP_NAME = "Vellum Web"
APP_VERSION = "2.4.0"
DEFAULT_PORT = 3000
SERVER_START_TIMEOUT = 60  # seconds
SERVER_LOG = Path(tempfile.gettempdir()) / "vellum-web-server.log"

# Dark Modern Palette (Wispr Flow / Obsidian)
BG_COLOR = "#0c0e14"        # Outer window dark
CARD_BG = "#151923"         # Floating card surface
CARD_BORDER = "#252c3d"     # Card border
TEXT_MAIN = "#f1f5f9"       # Primary text
TEXT_MUTED = "#8b949e"      # Muted text
ACCENT_GREEN = "#1f8a70"    # Vellum forest green
ACCENT_HOVER = "#23a07a"    # Hover green
BTN_BG = "#212838"          # Secondary button bg
BTN_HOVER = "#2d374d"       # Secondary button hover
BTN_BORDER = "#333d54"      # Button border
STATUS_RUNNING = "#10b981"   # Emerald
STATUS_STARTING = "#f59e0b"  # Amber
STATUS_STOPPED = "#64748b"   # Slate
STATUS_ERROR = "#ef4444"     # Rose


def get_app_directory() -> Path:
    """Get the true application directory whether running as script or frozen binary."""
    if getattr(sys, "frozen", False):
        exe_dir = Path(sys.executable).resolve().parent
        if (exe_dir / "package.json").exists():
            return exe_dir
        if (exe_dir / "Web_App" / "package.json").exists():
            return exe_dir / "Web_App"
        return exe_dir
    script_dir = Path(__file__).resolve().parent
    if (script_dir / "package.json").exists():
        return script_dir
    if (script_dir / "Web_App" / "package.json").exists():
        return script_dir / "Web_App"
    return script_dir


def check_port_in_use(port: int = DEFAULT_PORT) -> bool:
    """Check if port is already listening."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(("127.0.0.1", port)) == 0


def find_browser_app_executable() -> Optional[str]:
    """Find Microsoft Edge, Google Chrome, or Brave to launch in standalone --app window mode."""
    candidates = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        shutil.which("msedge"),
        shutil.which("chrome"),
        shutil.which("google-chrome"),
        shutil.which("brave"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


class VellumWebLauncher:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.port: int = DEFAULT_PORT
        self.server_proc: Optional[subprocess.Popen] = None
        self.server_ready = threading.Event()
        self.is_starting = False
        self._first_start = True
        self.log_window: Optional[tk.Toplevel] = None
        self.log_text_widget: Optional[tk.Text] = None
        self._icon_photo: Optional[tk.PhotoImage] = None

        self._setup_window()
        self._build_ui()
        self._center_window()

        atexit.register(self._cleanup)

        # Auto-check and auto-start server on application launch
        self.root.after(300, self.start_server)

    def _setup_window(self):
        self.root.title(f"{APP_NAME} Launcher · by Amine Zouaghi")
        self.root.geometry("480x440")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)

        icon_path = self._find_icon()
        if icon_path:
            try:
                if icon_path.suffix.lower() == ".ico":
                    self.root.iconbitmap(str(icon_path))
                else:
                    self._icon_photo = tk.PhotoImage(file=str(icon_path))
                    self.root.iconphoto(True, self._icon_photo)
            except Exception:
                pass

        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _find_icon(self) -> Optional[Path]:
        candidates = []
        if getattr(sys, "frozen", False):
            candidates.append(Path(sys.executable).resolve().parent)
            if hasattr(sys, "_MEIPASS"):
                candidates.append(Path(sys._MEIPASS))
        candidates.append(Path(__file__).resolve().parent)
        candidates.append(get_app_directory())

        for base_dir in candidates:
            for name in ("downloader.ico", "downloader.png"):
                p = base_dir / name
                if p.exists():
                    return p
        return None

    def _center_window(self):
        self.root.update_idletasks()
        w, h = 480, 440
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def _build_ui(self):
        self.card = tk.Frame(
            self.root,
            bg=CARD_BG,
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            padx=24,
            pady=20,
        )
        self.card.pack(fill="both", expand=True, padx=16, pady=16)

        # Header: Icon + Title
        hdr = tk.Frame(self.card, bg=CARD_BG)
        hdr.pack(fill="x", pady=(0, 16))

        logo_lbl = tk.Label(
            hdr,
            text="🔬",
            font=("Segoe UI Emoji", 24),
            bg=CARD_BG,
            fg=TEXT_MAIN,
        )
        logo_lbl.pack(side="left", padx=(0, 10))

        title_frame = tk.Frame(hdr, bg=CARD_BG)
        title_frame.pack(side="left")

        t_lbl = tk.Label(
            title_frame,
            text=f"{APP_NAME} Studio",
            font=("Segoe UI", 14, "bold"),
            fg=TEXT_MAIN,
            bg=CARD_BG,
        )
        t_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            title_frame,
            text="Local-First Literature Review Canvas · by Amine Zouaghi",
            font=("Segoe UI", 8),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        sub_lbl.pack(anchor="w")

        # Status Pill Box
        self.status_box = tk.Frame(
            self.card,
            bg="#1a202c",
            highlightbackground=CARD_BORDER,
            highlightthickness=1,
            padx=12,
            pady=8,
        )
        self.status_box.pack(fill="x", pady=(0, 14))

        self.status_dot = tk.Label(
            self.status_box,
            text="●",
            font=("Segoe UI", 12),
            fg=STATUS_STARTING,
            bg="#1a202c",
        )
        self.status_dot.pack(side="left", padx=(0, 6))

        self.status_text = tk.Label(
            self.status_box,
            text="Checking server…",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_MAIN,
            bg="#1a202c",
        )
        self.status_text.pack(side="left")

        self.url_btn = tk.Label(
            self.status_box,
            text="",
            font=("Segoe UI", 9, "underline"),
            fg="#cef5ca",
            bg="#1a202c",
            cursor="hand2",
        )
        self.url_btn.pack(side="right")
        self.url_btn.bind("<Button-1>", lambda e: self.open_standalone_window())

        # Primary Action Button 1: Launch in Native App Window
        self.app_window_btn = tk.Button(
            self.card,
            text="🖥️  Open in Standalone Desktop Window",
            font=("Segoe UI", 10, "bold"),
            fg="#ffffff",
            bg=ACCENT_GREEN,
            activeforeground="#ffffff",
            activebackground=ACCENT_HOVER,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=9,
            command=self.open_standalone_window,
        )
        self.app_window_btn.pack(fill="x", pady=(0, 8))

        # Action Button 2: Open in Regular Browser Tab
        self.browser_btn = tk.Button(
            self.card,
            text="🌐  Open in Default Browser",
            font=("Segoe UI", 9, "bold"),
            fg=TEXT_MAIN,
            bg=BTN_BG,
            activeforeground=TEXT_MAIN,
            activebackground=BTN_HOVER,
            relief="flat",
            cursor="hand2",
            padx=14,
            pady=7,
            command=self.open_browser,
        )
        self.browser_btn.pack(fill="x", pady=(0, 14))

        # Bottom Controls: Logs, Restart, Start/Stop
        ctrl_frame = tk.Frame(self.card, bg=CARD_BG)
        ctrl_frame.pack(fill="x")

        self.toggle_btn = tk.Button(
            ctrl_frame,
            text="⏹  Stop Server",
            font=("Segoe UI", 8, "bold"),
            fg=TEXT_MAIN,
            bg=BTN_BG,
            activeforeground=TEXT_MAIN,
            activebackground=BTN_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.toggle_server,
        )
        self.toggle_btn.pack(side="left", padx=(0, 6))

        self.restart_btn = tk.Button(
            ctrl_frame,
            text="🔄  Restart",
            font=("Segoe UI", 8),
            fg=TEXT_MAIN,
            bg=BTN_BG,
            activeforeground=TEXT_MAIN,
            activebackground=BTN_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.restart_server,
        )
        self.restart_btn.pack(side="left", padx=(0, 6))

        self.logs_btn = tk.Button(
            ctrl_frame,
            text="📋  View Logs",
            font=("Segoe UI", 8),
            fg=TEXT_MAIN,
            bg=BTN_BG,
            activeforeground=TEXT_MAIN,
            activebackground=BTN_HOVER,
            relief="flat",
            cursor="hand2",
            padx=10,
            pady=4,
            command=self.open_log_viewer,
        )
        self.logs_btn.pack(side="right")

        # Footer Version & Guarantee
        ftr = tk.Frame(self.card, bg=CARD_BG)
        ftr.pack(side="bottom", fill="x", pady=(10, 0))

        ftr_lbl = tk.Label(
            ftr,
            text="Next.js 16.4 Turbopack · 100% Private Client-Side IndexedDB",
            font=("Segoe UI", 7),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        ftr_lbl.pack(side="left")

        ver_lbl = tk.Label(
            ftr,
            text=f"v{APP_VERSION}",
            font=("Segoe UI", 7),
            fg=TEXT_MUTED,
            bg=CARD_BG,
        )
        ver_lbl.pack(side="right")

    # ──────────────────────────────────────────────────────────────────────────
    # Server Lifecycle Management
    def _set_status(self, text: str, dot_color: str, url_text: str = ""):
        self.status_text.config(text=text)
        self.status_dot.config(fg=dot_color)
        self.url_btn.config(text=url_text)

    def _check_health(self, port: int) -> bool:
        url = f"http://127.0.0.1:{port}"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "VellumLauncherCheck/1.0"})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                return response.status in (200, 304, 307, 308)
        except urllib.error.HTTPError:
            return True
        except Exception:
            return False

    def start_server(self):
        if self.is_starting:
            return
        self.is_starting = True
        self.server_ready.clear()
        self._set_status("Starting Next.js Turbopack…", STATUS_STARTING)
        self.app_window_btn.config(state="disabled")
        self.browser_btn.config(state="disabled")
        self.toggle_btn.config(text="⏳ Starting…", state="disabled")

        threading.Thread(target=self._start_thread, daemon=True).start()

    def _start_thread(self):
        # 1. Check if server is already running on port 3000
        if self._check_health(self.port):
            self.server_ready.set()
            self.root.after(0, self._on_server_ready)
            return

        web_dir = get_app_directory()

        # Locate node and npm on Windows
        npm_cmd = shutil.which("npm.cmd") or shutil.which("npm")
        node_cmd = shutil.which("node.exe") or shutil.which("node")

        if not (web_dir / "package.json").exists():
            self.root.after(0, lambda: self._on_launch_error(f"Cannot locate package.json in:\n{web_dir}\n\nPlease ensure Vellum_Web_Launcher.exe is inside the Web_App folder."))
            return

        # Check if node_modules exists; if not, run npm install
        if not (web_dir / "node_modules").exists():
            if not npm_cmd:
                self.root.after(0, lambda: self._on_launch_error("First run requires npm to install dependencies.\nPlease install Node.js from https://nodejs.org/"))
                return
            self.root.after(0, lambda: self._set_status("Installing npm packages…", STATUS_STARTING))
            try:
                subprocess.run(
                    [npm_cmd, "install"],
                    cwd=str(web_dir),
                    shell=True,
                    check=True,
                )
            except Exception as e:
                self.root.after(0, lambda err=e: self._on_launch_error(f"Failed to install npm dependencies: {err}"))
                return

        # Determine best launch command: npm run dev or direct node execution
        next_bin = web_dir / "node_modules" / "next" / "dist" / "bin" / "next"
        if npm_cmd:
            cmd = [npm_cmd, "run", "dev"]
        elif node_cmd and next_bin.exists():
            cmd = [node_cmd, str(next_bin), "dev"]
        else:
            self.root.after(0, lambda: self._on_launch_error("Node.js was not found on your system PATH.\nPlease install Node.js 18+ from https://nodejs.org/"))
            return

        try:
            log_file = open(SERVER_LOG, "w", encoding="utf-8", errors="replace")
        except OSError:
            log_file = None

        try:
            self.server_proc = subprocess.Popen(
                cmd,
                cwd=str(web_dir),
                stdout=log_file if log_file else subprocess.DEVNULL,
                stderr=subprocess.STDOUT if log_file else subprocess.DEVNULL,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                shell=True,
            )
        except Exception as e:
            if log_file:
                log_file.close()
            self.root.after(0, lambda err=e: self._on_launch_error(str(err)))
            return
        finally:
            if log_file:
                log_file.close()

        # Polling loop waiting for HTTP 200
        start_t = time.time()
        while time.time() - start_t < SERVER_START_TIMEOUT:
            if self._check_health(self.port):
                self.server_ready.set()
                self.root.after(0, self._on_server_ready)
                return
            time.sleep(1.0)

        self.root.after(0, lambda: self._on_launch_error("Server start timed out after 60s.\nCheck logs for details."))

    def _on_server_ready(self):
        self.is_starting = False
        url = f"http://localhost:{self.port}"
        self._set_status("Server Active", STATUS_RUNNING, url)
        self.app_window_btn.config(state="normal", bg=ACCENT_GREEN)
        self.browser_btn.config(state="normal")
        self.toggle_btn.config(text="⏹  Stop Server", state="normal")
        if getattr(self, "_first_start", True):
            self._first_start = False
            self.root.after(300, self.open_standalone_window)

    def _on_launch_error(self, message: str):
        self.is_starting = False
        self.server_ready.clear()
        self._set_status("Error Starting", STATUS_ERROR)
        self.app_window_btn.config(state="normal")
        self.browser_btn.config(state="normal")
        self.toggle_btn.config(text="▶  Start Server", state="normal")
        messagebox.showerror("Vellum Web Launch Error", f"{message}\n\nClick 'View Logs' to see diagnostic output.")

    def stop_server(self):
        self._cleanup_process()
        self.server_ready.clear()
        self.is_starting = False
        self._set_status("Server Stopped", STATUS_STOPPED)
        self.app_window_btn.config(state="normal")
        self.browser_btn.config(state="normal")
        self.toggle_btn.config(text="▶  Start Server", state="normal")

    def toggle_server(self):
        if self.server_ready.is_set():
            self.stop_server()
        else:
            self.start_server()

    def restart_server(self):
        self.stop_server()
        self.root.after(1000, self.start_server)

    def open_standalone_window(self):
        """Open in a native chromeless application window with its own frame & taskbar icon."""
        if not self.server_ready.is_set():
            self.start_server()

        url = f"http://localhost:{self.port}"
        browser_exe = find_browser_app_executable()
        if browser_exe:
            try:
                subprocess.Popen([browser_exe, f"--app={url}", "--window-size=1360,860"])
                return
            except Exception:
                pass
        # Fallback to standard browser
        webbrowser.open(url)

    def open_browser(self):
        """Open in standard browser tab."""
        if not self.server_ready.is_set():
            self.start_server()
        url = f"http://localhost:{self.port}"
        webbrowser.open(url)

    def open_log_viewer(self):
        if self.log_window and tk.Toplevel.winfo_exists(self.log_window):
            self.log_window.lift()
            return

        self.log_window = tk.Toplevel(self.root)
        self.log_window.title("Vellum Web — Diagnostic Server Logs")
        self.log_window.geometry("640x420")
        self.log_window.configure(bg=CARD_BG)

        f = tk.Frame(self.log_window, bg=CARD_BG, padx=12, pady=12)
        f.pack(fill="both", expand=True)

        txt = tk.Text(
            f,
            bg="#0c0e14",
            fg="#94a3b8",
            insertbackground="#ffffff",
            font=("Consolas", 8),
            wrap="word",
            relief="flat",
        )
        txt.pack(fill="both", expand=True)

        btn_row = tk.Frame(self.log_window, bg=CARD_BG, padx=12, pady=6)
        btn_row.pack(fill="x")

        def refresh():
            if SERVER_LOG.exists():
                try:
                    with open(SERVER_LOG, "r", encoding="utf-8", errors="replace") as lf:
                        content = lf.read()
                    txt.delete("1.0", "end")
                    txt.insert("end", content)
                    txt.see("end")
                except Exception:
                    pass

        refresh_btn = tk.Button(
            btn_row,
            text="🔄  Refresh Logs",
            font=("Segoe UI", 8),
            fg=TEXT_MAIN,
            bg=BTN_BG,
            relief="flat",
            command=refresh,
        )
        refresh_btn.pack(side="left")

        refresh()

    def _cleanup_process(self):
        if self.server_proc:
            try:
                subprocess.call(["taskkill", "/F", "/T", "/PID", str(self.server_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
            self.server_proc = None

    def _cleanup(self):
        self._cleanup_process()

    def _on_close(self):
        self._cleanup()
        self.root.destroy()


def main():
    root = tk.Tk()
    app = VellumWebLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()
