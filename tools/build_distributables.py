#!/usr/bin/env python3
"""Regenerate every distributable archive from the current working tree.

The archives in this repository were built by hand and had drifted: they
predated the move into Vellum_Desktop/ and Vellum_Web/, so shipping them next
to a freshly built installer would have handed colleagues a bundle that did
not match the source it claimed to come from.

This script rebuilds all of them from one source of truth - the files git
actually tracks - so the archives can never drift from the tree again.

    Vellum_Standalone_Windows_x64.zip     frozen desktop bundle (portable)
    Vellum_Desktop_V2.1_Botanical_Bento.zip  desktop source drop
    Vellum_Web_Fernly_Latest_Export.zip   web source export
    Vellum_Web_Fernly_SHARE.zip           web one-click share folder

Archive entries are written with a fixed timestamp, so an unchanged tree
produces a byte-identical archive and therefore an identical SHA-256.

Usage:
    python tools/build_distributables.py
    python tools/build_distributables.py --skip-share   # source archives only
"""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# A fixed timestamp keeps the archives reproducible. 1980-01-01 is the
# earliest date the ZIP format can represent.
FIXED_DATE = (1980, 1, 1, 0, 0, 0)

# Paths under Vellum_Desktop/ that never belong in the source drop.
DESKTOP_SOURCE_EXCLUDE = {
    "Vellum_Desktop/Vellum_Desktop_V2.1_Botanical_Bento",  # nested duplicate
    "Vellum_Desktop/Vellum_Standalone_Windows_x64.zip",
    "Vellum_Desktop/Vellum_Desktop_V2.1_Botanical_Bento.zip",
    "Vellum_Desktop/Vellum-Desktop-V2.1-Setup-x64.exe",
}

# The source drop ships only what runs from source. The standalone launcher
# points at dist/Vellum/Vellum.exe, which is not part of a source drop.
DESKTOP_SOURCE_DROP_EXTRA_EXCLUDE = {
    "Vellum_Desktop/CLICK_TO_RUN_STANDALONE_EXE.bat",
}

WEB_SOURCE_EXCLUDE = {
    "Vellum_Web/Vellum_Web_Fernly_Latest_Export.zip",
}


def git_tracked() -> list[str]:
    out = subprocess.run(
        ["git", "ls-files"], cwd=str(REPO_ROOT), capture_output=True, text=True, check=True
    ).stdout
    return [ln.strip() for ln in out.splitlines() if ln.strip()]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add(zf: zipfile.ZipFile, arcname: str, src: Path) -> None:
    """Add a file with a fixed timestamp so the archive is reproducible."""
    info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    # Only already-compressed payloads are stored verbatim. DLLs and .pyd files
    # are *not* in that set: they deflate to roughly half their size, and the
    # bundle is ~450 MB, so storing them uncompressed would nearly double the
    # download a colleague has to pull.
    if src.suffix.lower() in {".png", ".jpg", ".jpeg", ".ico", ".webp", ".pdf"}:
        info.compress_type = zipfile.ZIP_STORED
    zf.writestr(info, src.read_bytes())


def build_source_zip(out: Path, entries: list[tuple[str, Path]]) -> None:
    print(f"  -> {out.name}")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for arcname, src in entries:
            add(zf, arcname, src)
    print(f"     {out.stat().st_size/1024/1024:.1f} MB  sha256={sha256(out)[:32]}")


def build_standalone_zip(out: Path, bundle: Path) -> None:
    print(f"  -> {out.name}")
    files = sorted(p for p in bundle.rglob("*") if p.is_file())
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in files:
            add(zf, p.relative_to(bundle).as_posix(), p)
    print(f"     {out.stat().st_size/1024/1024:.1f} MB  {len(files)} files  "
          f"sha256={sha256(out)[:32]}")


def build_share_zip(out: Path, share: Path) -> None:
    print(f"  -> {out.name}")
    files = sorted(p for p in share.rglob("*") if p.is_file())
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for p in files:
            add(zf, f"{share.name}/{p.relative_to(share).as_posix()}", p)
    print(f"     {out.stat().st_size/1024/1024:.1f} MB  {len(files)} files  "
          f"sha256={sha256(out)[:32]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--skip-share", action="store_true",
                    help="do not archive the web share folder")
    ap.add_argument("--skip-standalone", action="store_true",
                    help="do not archive the frozen desktop bundle")
    args = ap.parse_args()

    tracked = git_tracked()
    print("Vellum distributables")
    print()

    # ---- desktop source drop ------------------------------------------------
    entries = []
    for rel in tracked:
        if rel.startswith("Vellum_Desktop/"):
            if rel in DESKTOP_SOURCE_EXCLUDE or rel in DESKTOP_SOURCE_DROP_EXTRA_EXCLUDE:
                continue
            if any(rel.startswith(ex + "/") for ex in DESKTOP_SOURCE_EXCLUDE):
                continue
            src = REPO_ROOT / rel
            if src.is_file():
                entries.append((rel[len("Vellum_Desktop/"):], src))
    print("Desktop source drop:")
    build_source_zip(REPO_ROOT / "DISTRIBUTABLES" / "Vellum_Desktop_Source_Drop.zip",
                     entries)

    # ---- web source export --------------------------------------------------
    entries = []
    for rel in tracked:
        if rel.startswith("Vellum_Web/Web_App/"):
            if rel in WEB_SOURCE_EXCLUDE:
                continue
            if any(part in {"node_modules", ".next"} for part in rel.split("/")):
                continue
            src = REPO_ROOT / rel
            if src.is_file():
                entries.append((f"Vellum_Web/{rel[len('Vellum_Web/Web_App/'):]}", src))
    print("Web source export:")
    build_source_zip(REPO_ROOT / "DISTRIBUTABLES" / "Vellum_Web_Source_Export.zip", entries)

    # ---- frozen desktop bundle ----------------------------------------------
    bundle = REPO_ROOT / "Vellum_Desktop" / "Desktop_App" / "dist" / "Vellum"
    if not args.skip_standalone:
        if not (bundle / "Vellum.exe").is_file():
            print("  !! frozen bundle missing - run PyInstaller first")
            return 1
        print("Frozen desktop bundle (portable):")
        build_standalone_zip(
            REPO_ROOT / "Vellum_Desktop" / "Vellum_Standalone_Windows_x64.zip", bundle)

    # ---- web share folder ---------------------------------------------------
    share = REPO_ROOT / "Vellum_Web" / "Vellum_Web_Fernly_SHARE"
    if not args.skip_share:
        if not (share / "START_VELLUM_WEB.bat").is_file():
            print("  !! web share folder missing - run tools/build_web_share.py first")
            return 1
        print("Web one-click share folder:")
        build_share_zip(REPO_ROOT / "Vellum_Web" / "Vellum_Web_Fernly_SHARE.zip", share)

    print()
    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
