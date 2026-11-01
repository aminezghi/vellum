"""
tests/conftest.py — Hermetic Test Fixtures for Vellum Desktop.

Automatically redirects all vault directories, config paths, and downloads to isolated
temporary directories for every test, guaranteeing 100% test hermeticity without touching
live user directories (~/Vellum_Research_Vault, ~/.vellum_config.json, ~/Downloads).
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
import pytest

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


@pytest.fixture(autouse=True)
def hermetic_vellum_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """
    Autouse fixture that hermetically isolates all filesystem storage
    to pytest's per-test tmp_path directory.
    """
    vault_dir = tmp_path / "vault"
    vault_dir.mkdir(parents=True, exist_ok=True)
    config_path = tmp_path / "config.json"
    downloads_dir = tmp_path / "downloads"
    downloads_dir.mkdir(parents=True, exist_ok=True)

    monkeypatch.setenv("VELLUM_VAULT_DIR", str(vault_dir))
    monkeypatch.setenv("VELLUM_CONFIG_PATH", str(config_path))
    monkeypatch.setenv("VELLUM_DOWNLOADS_DIR", str(downloads_dir))

    # Safely mock citation exports Downloads directory
    try:
        import vellum_citation_export
        monkeypatch.setattr(vellum_citation_export, "get_user_downloads_dir", lambda: downloads_dir)
    except Exception:
        pass

    # Ensure vellum_workspace reflects isolated paths
    try:
        import vellum_workspace
        vellum_workspace.CONFIG_FILE = config_path
        vellum_workspace.DEFAULT_VAULT_DIR = vault_dir
    except Exception:
        pass

    yield {
        "vault_dir": vault_dir,
        "config_path": config_path,
        "downloads_dir": downloads_dir,
    }
