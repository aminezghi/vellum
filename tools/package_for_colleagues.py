#!/usr/bin/env python3
"""Build the two shareable ZIP packages for colleagues.

1. Desktop: Vellum_Desktop_Installer_Windows_x64.zip
   - Standalone Windows installer: Vellum-Desktop-V2.1-Setup-x64.exe
   - 1-click launcher: INSTALL_VELLUM_DESKTOP.bat
   - User manuals: README_VELLUM_DESKTOP_V2.1.pdf, README_FOR_COLLEAGUES.pdf
   - Quick instructions: README.txt

2. Web: Vellum_Web_OneClick_Package.zip
   - Self-contained portable Node.js runtime (runtime/node/)
   - Pre-compiled production Next.js app (app/)
   - 1-click launcher: START_VELLUM_WEB.bat
   - 1-click stopper: STOP_VELLUM_WEB.bat
   - User manual: README_FOR_COLLEAGUES.pdf
   - Quick instructions: README.txt
"""

import hashlib
import os
from pathlib import Path
import shutil
import time
import zipfile

REPO_ROOT = Path(__file__).resolve().parent.parent
DIST = REPO_ROOT / "DISTRIBUTABLES"
DIST.mkdir(parents=True, exist_ok=True)

FIXED_DATE = (1980, 1, 1, 0, 0, 0)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def add_file_to_zip(zf: zipfile.ZipFile, arcname: str, src: Path) -> None:
    info = zipfile.ZipInfo(arcname, date_time=FIXED_DATE)
    if src.suffix.lower() in {".png", ".jpg", ".jpeg", ".ico", ".webp", ".pdf", ".zip", ".exe"}:
        info.compress_type = zipfile.ZIP_STORED
    else:
        info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o644 << 16
    zf.writestr(info, src.read_bytes())


def build_desktop_package() -> Path:
    print("[1/2] Building Desktop Installer Package...")
    staging = DIST / "Vellum_Desktop_Installer_Windows_x64"
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True, exist_ok=True)

    # 1. Copy Installer
    installer_src = REPO_ROOT / "Vellum_Desktop" / "Vellum-Desktop-V2.1-Setup-x64.exe"
    if not installer_src.is_file():
        raise FileNotFoundError(f"Missing {installer_src}")
    print(f"  Copying installer: {installer_src.name} ({installer_src.stat().st_size / 1024 / 1024:.1f} MB)")
    shutil.copy2(installer_src, staging / "Vellum-Desktop-V2.1-Setup-x64.exe")

    # 2. Copy PDFs
    print("  Copying PDF manuals...")
    desktop_pdf = REPO_ROOT / "Vellum_Desktop" / "README_VELLUM_DESKTOP_V2.1.pdf"
    colleague_pdf = REPO_ROOT / "README_FOR_COLLEAGUES.pdf"
    if desktop_pdf.is_file():
        shutil.copy2(desktop_pdf, staging / "README_VELLUM_DESKTOP_V2.1.pdf")
    if colleague_pdf.is_file():
        shutil.copy2(colleague_pdf, staging / "README_FOR_COLLEAGUES.pdf")

    # 3. Create 1-click batch launcher
    launcher_bat = (
        "@echo off\r\n"
        "setlocal\r\n"
        "title Vellum Desktop V2.1 by Amine - One-Click Installer\r\n"
        'cd /d "%~dp0"\r\n\r\n'
        "echo =====================================================================\r\n"
        "echo       VELLUM DESKTOP V2.1 by AMINE (FERNLY BOTANICAL BENTO EDITION)\r\n"
        "echo       One-Click Windows Installer - Academic Literature Workbench\r\n"
        "echo =====================================================================\r\n"
        "echo.\r\n"
        "echo [*] Launching Vellum Desktop Installer...\r\n"
        "echo [*] No Python or extra software required.\r\n"
        "echo.\r\n\r\n"
        'if exist "%~dp0Vellum-Desktop-V2.1-Setup-x64.exe" (\r\n'
        '    start "" "%~dp0Vellum-Desktop-V2.1-Setup-x64.exe"\r\n'
        "    echo [OK] Installer started! Follow the setup prompts to install.\r\n"
        '    echo [*] Once installed, launch "Vellum Desktop" from your Desktop or Start Menu.\r\n'
        ") else (\r\n"
        '    echo [ERROR] Installer binary not found: "%~dp0Vellum-Desktop-V2.1-Setup-x64.exe"\r\n'
        "    pause\r\n"
        "    exit /b 1\r\n"
        ")\r\n\r\n"
        "timeout /t 5 >nul\r\n"
        "exit /b 0\r\n"
    )
    (staging / "INSTALL_VELLUM_DESKTOP.bat").write_text(launcher_bat, encoding="utf-8")

    # 4. Create README.txt
    readme_txt = (
        "=====================================================================\n"
        "VELLUM DESKTOP V2.1 by AMINE\n"
        "Academic Research, Systematic Review & Heavy PDF Retrieval Workbench\n"
        "=====================================================================\n\n"
        "HOW TO INSTALL & RUN (One-Click Setup):\n"
        "---------------------------------------------------------------------\n"
        "1. Extract this entire zip folder to a location on your computer.\n"
        "2. Double-click: INSTALL_VELLUM_DESKTOP.bat\n"
        "   (Or double-click: Vellum-Desktop-V2.1-Setup-x64.exe directly)\n"
        "3. Follow the on-screen setup prompts:\n"
        "   * Per-user installation - NO administrator rights required.\n"
        "   * Zero dependencies - NO Python installation required.\n"
        '4. Once installed, launch "Vellum Desktop" from your Desktop shortcut\n'
        "   or Start Menu.\n\n"
        "WHAT IS INCLUDED:\n"
        "---------------------------------------------------------------------\n"
        "* Vellum-Desktop-V2.1-Setup-x64.exe  : Full standalone Windows installer\n"
        "* INSTALL_VELLUM_DESKTOP.bat        : One-click launcher for the installer\n"
        "* README_VELLUM_DESKTOP_V2.1.pdf    : Dedicated desktop guide with illustrations\n"
        "* README_FOR_COLLEAGUES.pdf         : Complete dual-pack technical documentation\n\n"
        "SYSTEM REQUIREMENTS:\n"
        "---------------------------------------------------------------------\n"
        "* Windows 10 (version 1903+) or Windows 11 (64-bit)\n"
        "* 4 GB RAM minimum (8 GB recommended for 10 000+ paper batches)\n"
        "* ~700 MB disk space\n"
        "* Microsoft Edge WebView2 (pre-installed on current Windows 10 & 11)\n\n"
        "PRIVACY & LOCAL STORAGE:\n"
        "---------------------------------------------------------------------\n"
        "* 100% local, zero-telemetry, zero-cloud architecture.\n"
        "* All data is stored privately in %USERPROFILE%\\Vellum_Research_Vault\\.\n"
        "=====================================================================\n"
    )
    (staging / "README.txt").write_text(readme_txt, encoding="utf-8")

    # 5. Zip Desktop package
    out_zip = DIST / "Vellum_Desktop_Installer_Windows_x64.zip"
    print(f"  Zipping package to: {out_zip.name} ...")
    files = sorted(p for p in staging.rglob("*") if p.is_file())
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in files:
            arcname = f"Vellum_Desktop_Installer_Windows_x64/{p.relative_to(staging).as_posix()}"
            add_file_to_zip(zf, arcname, p)

    # Copy to root as well
    root_zip = REPO_ROOT / "Vellum_Desktop_Installer_Windows_x64.zip"
    shutil.copy2(out_zip, root_zip)
    print(f"  [OK] Desktop Package: {out_zip.stat().st_size / 1024 / 1024:.1f} MB (SHA-256: {sha256(out_zip)[:16]}...)")
    return out_zip


def build_web_package() -> Path:
    print("\n[2/2] Building Web One-Click Share Package...")
    share_dir = REPO_ROOT / "Vellum_Web" / "Vellum_Web_OneClick_Package"
    if not share_dir.is_dir():
        raise FileNotFoundError(f"Missing {share_dir}")

    # Ensure PDF is present
    colleague_pdf = REPO_ROOT / "README_FOR_COLLEAGUES.pdf"
    if colleague_pdf.is_file():
        shutil.copy2(colleague_pdf, share_dir / "README_FOR_COLLEAGUES.pdf")

    out_zip = DIST / "Vellum_Web_OneClick_Package.zip"
    print(f"  Zipping package to: {out_zip.name} (includes portable Node.js runtime) ...")
    files = sorted(p for p in share_dir.rglob("*") if p.is_file())
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
        for p in files:
            arcname = f"Vellum_Web_OneClick_Package/{p.relative_to(share_dir).as_posix()}"
            add_file_to_zip(zf, arcname, p)

    # Copy to root as well
    root_zip = REPO_ROOT / "Vellum_Web_OneClick_Package.zip"
    shutil.copy2(out_zip, root_zip)

    # Also synchronize Vellum_Web_OneClick_Package.zip
    shutil.copy2(out_zip, REPO_ROOT / "Vellum_Web" / "Vellum_Web_OneClick_Package.zip")

    print(f"  [OK] Web Package: {out_zip.stat().st_size / 1024 / 1024:.1f} MB (SHA-256: {sha256(out_zip)[:16]}...)")
    return out_zip


def main():
    t0 = time.time()
    print("=" * 70)
    print("VELLUM SUITE: PACKAGING READY-TO-USE ZIP BUNDLES FOR COLLEAGUES")
    print("=" * 70)

    z1 = build_desktop_package()
    z2 = build_web_package()

    print("\n" + "=" * 70)
    print("PACKAGING COMPLETE!")
    print(f"1. Desktop Package: {z1} ({z1.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"2. Web Package:     {z2} ({z2.stat().st_size / 1024 / 1024:.1f} MB)")
    print(f"Total Time: {time.time() - t0:.1f}s")
    print("=" * 70)


if __name__ == "__main__":
    main()
