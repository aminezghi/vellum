"""
vellum_pdf_server.py — Local HTTP streaming server for native PDF viewing.

Spins up a lightweight, secure background HTTP daemon on 127.0.0.1 with byte-range
seeking support. Serves PDFs directly to WebView2 / Microsoft Edge native PDF viewer
with zero font distortion and full native controls (search, print, zoom, table of contents).
"""

from __future__ import annotations

import http.server
import os
import re
import socketserver
import threading
import uuid
from pathlib import Path
from typing import Dict, Optional, Tuple
from urllib.parse import unquote

_LOCK = threading.Lock()
_SERVER: Optional[http.server.ThreadingHTTPServer] = None
_SERVER_PORT: Optional[int] = None
_FILE_REGISTRY: Dict[str, Path] = {}
_PATH_TO_TOKEN: Dict[str, str] = {}


class _RangePDFRequestHandler(http.server.BaseHTTPRequestHandler):
    """HTTP handler supporting byte-range requests for smooth PDF streaming."""

    def log_message(self, format: str, *args) -> None:
        """Suppress default console logging to keep stdout clean."""
        pass

    def _resolve_target(self) -> Optional[Tuple[str, Path]]:
        # Format expected: /pdf/<token>/<filename>
        clean_path = unquote(self.path).split("?")[0]
        parts = [p for p in clean_path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "pdf":
            token = parts[1]
            with _LOCK:
                target = _FILE_REGISTRY.get(token)
            if target and target.is_file():
                return token, target
        return None

    def do_HEAD(self) -> None:
        resolved = self._resolve_target()
        if not resolved:
            self.send_error(404, "File not found")
            return
        _, target = resolved
        size = target.stat().st_size
        self.send_response(200)
        self.send_header("Content-Type", "application/pdf")
        self.send_header("Content-Disposition", f'inline; filename="{target.name}"')
        self.send_header("Content-Length", str(size))
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()

    def do_GET(self) -> None:
        resolved = self._resolve_target()
        if not resolved:
            self.send_error(404, "File not found or expired")
            return
        _, target = resolved

        try:
            file_size = target.stat().st_size
            range_header = self.headers.get("Range")

            if range_header:
                m = re.match(r"bytes=(\d+)-(\d*)", range_header)
                if m:
                    start = int(m.group(1))
                    end = int(m.group(2)) if m.group(2) else file_size - 1
                    end = min(end, file_size - 1)
                    if start <= end and start < file_size:
                        length = end - start + 1
                        self.send_response(206, "Partial Content")
                        self.send_header("Content-Type", "application/pdf")
                        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
                        self.send_header("Content-Length", str(length))
                        self.send_header("Content-Disposition", f'inline; filename="{target.name}"')
                        self.send_header("Accept-Ranges", "bytes")
                        self.send_header("Access-Control-Allow-Origin", "*")
                        self.end_headers()

                        with open(target, "rb") as f:
                            f.seek(start)
                            self.wfile.write(f.read(length))
                        return

            # Full file transfer
            self.send_response(200)
            self.send_header("Content-Type", "application/pdf")
            self.send_header("Content-Disposition", f'inline; filename="{target.name}"')
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            with open(target, "rb") as f:
                while chunk := f.read(65536):
                    self.wfile.write(chunk)
        except (ConnectionResetError, BrokenPipeError):
            # Client closed frame or navigated away
            pass
        except Exception as exc:
            try:
                self.send_error(500, f"Error streaming PDF: {exc}")
            except Exception:
                pass


def _ensure_server_started() -> int:
    """Ensure the local daemon HTTP server is running, returning its bound port."""
    global _SERVER, _SERVER_PORT
    with _LOCK:
        if _SERVER is not None and _SERVER_PORT is not None:
            return _SERVER_PORT

        server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _RangePDFRequestHandler)
        _SERVER = server
        _SERVER_PORT = server.server_address[1]

        thread = threading.Thread(
            target=server.serve_forever,
            name="VellumPDFServerThread",
            daemon=True,
        )
        thread.start()
        return _SERVER_PORT


def register_pdf_for_streaming(pdf_path: str | Path) -> str:
    """
    Registers a PDF file for local streaming and returns its local HTTP URL.
    Example: http://127.0.0.1:54321/pdf/a1b2c3d4/paper.pdf
    """
    path = Path(pdf_path).resolve()
    if not path.is_file():
        return ""

    port = _ensure_server_started()
    path_key = str(path).lower()

    with _LOCK:
        token = _PATH_TO_TOKEN.get(path_key)
        if not token or token not in _FILE_REGISTRY:
            token = uuid.uuid4().hex[:12]
            _FILE_REGISTRY[token] = path
            _PATH_TO_TOKEN[path_key] = token

    safe_name = re.sub(r'[^a-zA-Z0-9_\-\.]', '_', path.name)
    return f"http://127.0.0.1:{port}/pdf/{token}/{safe_name}"
