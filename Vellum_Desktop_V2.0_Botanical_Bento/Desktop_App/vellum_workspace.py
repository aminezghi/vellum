"""
vellum_workspace.py — Research Vault and Project Workspace Manager for Vellum.

Provides persistent, local-first multi-project management.
Each project is an isolated folder inside the user's chosen Research Vault:
  <Research_Vault>/
    ├── <Project_A>/
    │   ├── project.json    (Query state, screening decisions, PRISMA counts, graph seeds)
    │   ├── papers/         (Downloaded PDFs for this project)
    │   └── exports/        (Generated BibTeX, CSV, Excel files)
    └── <Project_B>/
        └── ...

Zero telemetry. 100% local filesystem.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

CONFIG_FILE = Path.home() / ".vellum_config.json"
DEFAULT_VAULT_DIR = Path.home() / "Vellum_Research_Vault"


def _sanitize_project_name(name: str) -> str:
    """Sanitize project name to be filesystem safe."""
    s = re.sub(r'[\\/*?:"<>|]', "", name.strip())
    return s.replace(" ", "_") or "Default_Project"


def load_config() -> Dict[str, Any]:
    """Load global Vellum preferences from ~/.vellum_config.json."""
    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "vault_dir": str(DEFAULT_VAULT_DIR),
        "active_project": "Default_Project",
        "vault_initialized": False,
        "recent_vaults": [],
        "user_name": "",
        "research_field": "",
        "research_keywords": "",
    }


def save_config(cfg: Dict[str, Any]) -> None:
    """Save global Vellum preferences to ~/.vellum_config.json."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


def get_user_profile() -> Dict[str, str]:
    """Retrieve the current user profile / research preferences."""
    cfg = load_config()
    return {
        "name": cfg.get("user_name", ""),
        "field": cfg.get("research_field", ""),
        "keywords": cfg.get("research_keywords", ""),
        "theme": cfg.get("theme", "dark"),
    }


def set_user_profile(name: str, field: str, keywords: str, theme: Optional[str] = None) -> None:
    """Persist user profile / research preferences."""
    cfg = load_config()
    cfg["user_name"] = name.strip()
    cfg["research_field"] = field.strip()
    cfg["research_keywords"] = keywords.strip()
    if theme:
        cfg["theme"] = theme.strip()
    save_config(cfg)


def is_user_profile_set() -> bool:
    """Check if the user has completed profile setup."""
    p = get_user_profile()
    return bool(p.get("name") or p.get("field"))


def is_vault_initialized() -> bool:
    """Check if the user has completed initial vault setup."""
    cfg = load_config()
    return bool(cfg.get("vault_initialized", False))


def get_recent_vaults() -> List[str]:
    """Get list of recently opened vault paths."""
    cfg = load_config()
    return cfg.get("recent_vaults", [])


def add_recent_vault(path: str) -> None:
    """Add a path to the recent vaults history."""
    cfg = load_config()
    recent = [p for p in cfg.get("recent_vaults", []) if p != path]
    recent.insert(0, path)
    cfg["recent_vaults"] = recent[:8]
    save_config(cfg)


def get_vault_dir() -> Path:
    """Get the active Research Vault directory, creating it if needed."""
    cfg = load_config()
    v_str = os.environ.get("VELLUM_VAULT_DIR") or cfg.get("vault_dir") or str(DEFAULT_VAULT_DIR)
    p = Path(v_str).resolve()
    p.mkdir(parents=True, exist_ok=True)
    return p


def set_vault_dir(path: Path | str, initialized: bool = True) -> None:
    """Set and persist a new Research Vault directory."""
    p = Path(path).resolve()
    p.mkdir(parents=True, exist_ok=True)
    cfg = load_config()
    cfg["vault_dir"] = str(p)
    cfg["vault_initialized"] = initialized
    save_config(cfg)
    add_recent_vault(str(p))
    os.environ["VELLUM_VAULT_DIR"] = str(p)


def list_projects() -> List[str]:
    """List all project directory names in the current vault."""
    vault = get_vault_dir()
    projects = []
    for entry in vault.iterdir():
        if entry.is_dir() and not entry.name.startswith("."):
            projects.append(entry.name)
    if not projects:
        # Initialize default project if none exists
        create_project("Default_Project")
        projects.append("Default_Project")
    return sorted(projects)


def get_active_project_name() -> str:
    """Get the name of the currently active project."""
    cfg = load_config()
    active = os.environ.get("VELLUM_ACTIVE_PROJECT") or cfg.get("active_project") or "Default_Project"
    projects = list_projects()
    if active not in projects:
        active = projects[0] if projects else "Default_Project"
    return active


def set_active_project(name: str) -> None:
    """Switch active project name."""
    s_name = _sanitize_project_name(name)
    cfg = load_config()
    cfg["active_project"] = s_name
    save_config(cfg)
    os.environ["VELLUM_ACTIVE_PROJECT"] = s_name


def get_project_dir(name: Optional[str] = None) -> Path:
    """Get directory for a project, creating standard subdirectories."""
    p_name = name or get_active_project_name()
    p_dir = get_vault_dir() / _sanitize_project_name(p_name)
    (p_dir / "papers").mkdir(parents=True, exist_ok=True)
    (p_dir / "exports").mkdir(parents=True, exist_ok=True)
    return p_dir


def create_project(name: str) -> Path:
    """Create a new project folder inside the vault."""
    p_name = _sanitize_project_name(name)
    p_dir = get_project_dir(p_name)
    meta_file = p_dir / "project.json"
    if not meta_file.exists():
        initial_state = {
            "name": p_name,
            "created_at": None,
            "query": "",
            "search_records": [],
            "screened": {},
            "citation_graph_seeds": [],
            "download_queue": [],
            "notes": "",
        }
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(initial_state, f, indent=2)
    return p_dir


def load_project_data(name: Optional[str] = None) -> Dict[str, Any]:
    """Load project.json metadata for the active or named project."""
    p_dir = get_project_dir(name)
    meta_file = p_dir / "project.json"
    if meta_file.exists():
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "name": p_dir.name,
        "search_records": [],
        "screened": {},
        "citation_graph_seeds": [],
        "download_queue": [],
        "notes": "",
    }


def save_project_data(data: Dict[str, Any], name: Optional[str] = None) -> None:
    """Persist project.json metadata."""
    p_dir = get_project_dir(name)
    meta_file = p_dir / "project.json"
    try:
        with open(meta_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def get_project_stats(name: Optional[str] = None) -> Dict[str, int]:
    """Compute live stats for a project (PDFs on disk, screened counts, searched counts, notes)."""
    p_dir = get_project_dir(name)
    pdf_count = len(list((p_dir / "papers").glob("*.pdf")))
    data = load_project_data(name)
    search_count = len(data.get("search_records", []))
    screened_dict = data.get("screened", {})
    included_count = sum(1 for v in screened_dict.values() if v.get("status") == "included")
    appraisals_count = len(data.get("appraisals", {}))
    paper_notes = data.get("paper_notes", {})
    noted_count = len(paper_notes)
    return {
        "pdfs": pdf_count,
        "search_records": search_count,
        "included": included_count,
        "appraisals": appraisals_count,
        "noted": noted_count,
    }


def get_project_notes(name: Optional[str] = None) -> str:
    """Retrieve overall project synthesis / diary notes."""
    data = load_project_data(name)
    return data.get("project_notes") or data.get("notes") or ""


def save_project_notes(notes: str, name: Optional[str] = None) -> None:
    """Save overall project synthesis / diary notes to project.json and a standalone .md file."""
    data = load_project_data(name)
    data["project_notes"] = notes
    data["notes"] = notes
    save_project_data(data, name)

    # Also persist to human-readable synthesis_notes.md in project dir
    try:
        p_dir = get_project_dir(name)
        (p_dir / "synthesis_notes.md").write_text(notes, encoding="utf-8", errors="replace")
    except Exception:
        pass


def get_paper_notes(paper_key: str, name: Optional[str] = None) -> Dict[str, Any]:
    """Retrieve appraisal notes and comments for a specific paper."""
    data = load_project_data(name)
    notes_map = data.get("paper_notes", {})
    clean_k = str(paper_key).strip().lower()
    return notes_map.get(clean_k, {})


def save_paper_notes(
    paper_key: str,
    note_data: Dict[str, Any],
    name: Optional[str] = None,
) -> None:
    """Persist appraisal notes, ratings, and comments for a specific paper."""
    data = load_project_data(name)
    if "paper_notes" not in data:
        data["paper_notes"] = {}
    clean_k = str(paper_key).strip().lower()
    existing = data["paper_notes"].get(clean_k, {})
    existing.update(note_data)
    data["paper_notes"][clean_k] = existing
    save_project_data(data, name)


def get_all_paper_notes(name: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """Retrieve all study-specific appraisal notes for the project."""
    data = load_project_data(name)
    return data.get("paper_notes", {})

