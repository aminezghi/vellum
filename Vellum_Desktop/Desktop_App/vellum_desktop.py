#!/usr/bin/env python3
"""
vellum_desktop.py — Native Desktop App Window for Vellum.

Launches Vellum as a true, single-window desktop application powered by
Microsoft Edge WebView2 (pywebview).
  - No browser address bars or tabs
  - Custom dark native frame (1400x900)
  - Automatic background engine lifecycle (closing window terminates server)
  - Automatic fallback to Windows Edge App-Mode if needed
"""

from __future__ import annotations

import atexit
import os
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path
from typing import Optional

APP_NAME = "Vellum by Amine"
DEFAULT_PORT = 8501
HEALTH_TIMEOUT = 45.0  # seconds
SERVER_LOG = Path(tempfile.gettempdir()) / "vellum-desktop-server.log"
APP_LOG = Path(tempfile.gettempdir()) / "vellum-desktop-app.log"


def log_app(msg: str) -> None:
    try:
        with open(APP_LOG, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    except Exception:
        pass


def find_free_port(start: int = DEFAULT_PORT, tries: int = 25) -> int:
    """Find an available TCP port for the local backend."""
    for p in range(start, start + tries):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("127.0.0.1", p))
                return p
            except OSError:
                continue
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def check_server_health(port: int) -> bool:
    """Check if Streamlit HTTP server is responding."""
    try:
        import urllib.request
        url = f"http://127.0.0.1:{port}/_stcore/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=0.8) as resp:
            return resp.status == 200
    except Exception:
        return False


def _terminate_process_tree(proc: subprocess.Popen) -> None:
    """Safely terminate subprocess and all descendants."""
    if proc is None or proc.poll() is not None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=5,
            )
        else:
            proc.terminate()
            proc.wait(timeout=2)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


SERVER_ENV_KEYS = ("VELLUM_SERVER", "VELUM_SERVER")


class VellumDesktopApp:
    def __init__(self):
        self.port = find_free_port()
        self.server_proc: Optional[subprocess.Popen] = None
        self._stopped = False
        atexit.register(self.shutdown)

    def _find_app_script(self) -> Path:
        """Locate pdf_downloader_app.py in development or frozen bundle."""
        base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
        candidates = [
            base / "pdf_downloader_app.py",
            Path(__file__).resolve().parent / "pdf_downloader_app.py",
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    def start_background_server(self) -> bool:
        """Spawn Streamlit in the background and wait until healthy."""
        app_script = self._find_app_script()
        if not app_script.exists():
            print(f"Error: {app_script} does not exist", file=sys.stderr)
            return False

        if getattr(sys, "frozen", False):
            cmd = [sys.executable]
            cwd = str(app_script.parent)
        else:
            cmd = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(app_script),
                "--global.developmentMode=false",
            ]
            cwd = str(Path(__file__).resolve().parent)

        env = os.environ.copy()
        for k in SERVER_ENV_KEYS:
            env[k] = "1"
        env["STREAMLIT_SERVER_HEADLESS"] = "true"
        env["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"
        env["STREAMLIT_SERVER_PORT"] = str(self.port)
        env["STREAMLIT_SERVER_ADDRESS"] = "127.0.0.1"
        env["VELLUM_DESKTOP_APP"] = "1"
        try:
            import vellum_workspace
            env["VELLUM_VAULT_DIR"] = str(vellum_workspace.get_vault_dir())
            env["VELLUM_ACTIVE_PROJECT"] = str(vellum_workspace.get_active_project_name())
        except Exception as exc:
            log_app(f"Workspace environment discovery notice: {exc}")

        # Redirect background Streamlit standard streams to server log
        try:
            log_file = open(SERVER_LOG, "w", encoding="utf-8", errors="replace")
        except OSError:
            log_file = None

        try:
            self.server_proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                env=env,
                stdout=log_file if log_file else subprocess.DEVNULL,
                stderr=subprocess.STDOUT if log_file else subprocess.DEVNULL,
            )
        except Exception as e:
            print(f"Failed to spawn backend: {e}", file=sys.stderr)
            if log_file:
                log_file.close()
            return False

        # Wait for health endpoint
        t0 = time.time()
        while time.time() - t0 < HEALTH_TIMEOUT:
            if self.server_proc.poll() is not None:
                print("Server exited unexpectedly during startup.", file=sys.stderr)
                return False
            if check_server_health(self.port):
                return True
            time.sleep(0.3)

        print("Timed out waiting for server health.", file=sys.stderr)
        return False

    def shutdown(self) -> None:
        """Shut down the backend server cleanly."""
        if self._stopped:
            return
        self._stopped = True
        if self.server_proc:
            _terminate_process_tree(self.server_proc)
            self.server_proc = None

    def launch(self) -> None:
        """Run the desktop app window."""
        log_app(f"Starting {APP_NAME} engine...")
        ready = self.start_background_server()
        if not ready:
            log_app("Could not start background server. Exiting.")
            sys.exit(1)

        url = f"http://127.0.0.1:{self.port}"
        log_app(f"{APP_NAME} backend ready on {url}. Opening desktop window...")

        try:
            try:
                import pythonnet
                pythonnet.load()
            except Exception as pe:
                log_app(f"pythonnet initialization info: {pe}")

            import webview

            # Crucial for desktop file exports and downloads:
            try:
                webview.settings["ALLOW_DOWNLOADS"] = True
                webview.settings["ALLOW_FILE_URLS"] = True
                webview.settings["OPEN_EXTERNAL_LINKS_IN_BROWSER"] = True
            except Exception:
                pass

            log_app("Creating native WebView2 desktop window...")
            window = webview.create_window(
                title=f"{APP_NAME} — Academic Research Companion",
                url=url,
                width=1400,
                height=900,
                min_size=(1024, 700),
                background_color="#0c0e14",
                text_select=True,
                confirm_close=False,
            )

            log_app("Calling webview.start()...")
            webview.start(debug=False)
            log_app("webview.start() completed cleanly.")
        except Exception as exc:
            log_app(f"WebView2 initialization exception: {exc}. Launching fallback app window...")
            self._fallback_app_mode(url)
        finally:
            log_app("Shutting down Vellum background server...")
            self.shutdown()

    def _fallback_app_mode(self, url: str) -> None:
        """Fallback to Edge/Chrome standalone application window."""
        edge_paths = [
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("ProgramFiles", "")) / "Microsoft/Edge/Application/msedge.exe",
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Edge/Application/msedge.exe",
            Path("/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge"),
        ]
        chrome_paths = [
            Path(os.environ.get("ProgramFiles", "")) / "Google/Chrome/Application/chrome.exe",
            Path(os.environ.get("ProgramFiles(x86)", "")) / "Google/Chrome/Application/chrome.exe",
            Path("/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"),
            Path(os.path.expanduser("~/Applications/Google Chrome.app/Contents/MacOS/Google Chrome")),
            Path("/Applications/Brave Browser.app/Contents/MacOS/Brave Browser"),
        ]

        browser_exe = None
        for p in edge_paths + chrome_paths:
            if p.exists():
                browser_exe = str(p)
                break

        app_dir = Path(tempfile.gettempdir()) / "vellum_desktop_app_profile"
        app_dir.mkdir(parents=True, exist_ok=True)

        if browser_exe:
            try:
                log_app(f"Launching fallback standalone app with {browser_exe}...")
                proc = subprocess.Popen([
                    browser_exe,
                    f"--app={url}",
                    f"--user-data-dir={app_dir}",
                    "--window-size=1400,900",
                    "--disable-features=Translate",
                ])
                # Keep server alive while the app profile is active or server is healthy
                time.sleep(2)
                while check_server_health(self.port):
                    # Check if process is still running or lock exists
                    if proc.poll() is not None:
                        lock = app_dir / "SingletonLock"
                        if not lock.exists():
                            log_app("Fallback browser window was closed.")
                            break
                    time.sleep(1)
            except Exception as e:
                log_app(f"Fallback app mode exception: {e}. Opening default browser...")
                import webbrowser
                webbrowser.open(url)
                try:
                    while check_server_health(self.port):
                        time.sleep(1)
                except (KeyboardInterrupt, SystemExit):
                    pass
        else:
            import webbrowser
            webbrowser.open(url)
            try:
                while check_server_health(self.port):
                    time.sleep(1)
            except (KeyboardInterrupt, SystemExit):
                pass


def main():
    # If spawned as background server process
    if any(os.environ.get(k) == "1" for k in SERVER_ENV_KEYS):
        import vellum_entry
        vellum_entry.run()
        return

    app = VellumDesktopApp()
    app.launch()


if __name__ == "__main__":
    main()
