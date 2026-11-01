#!/bin/bash
# =====================================================================
#       VELLUM BY AMINE - DESKTOP WORKBENCH (macOS)
#       Active Learning Screening + Citation Exploration + Batch Harvester
# =====================================================================

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo "====================================================================="
echo "      VELLUM BY AMINE - DESKTOP WORKBENCH (macOS)"
echo "      Active Learning Screening + Citation Exploration + Batch Harvester"
echo "====================================================================="
echo ""

# 1. Prefer native standalone app bundle if present
if [ -d "$HERE/Desktop_App/dist/Vellum.app" ]; then
    echo "[OK] Found native standalone Vellum.app bundle. Launching..."
    open "$HERE/Desktop_App/dist/Vellum.app"
    exit 0
elif [ -d "$HERE/Vellum.app" ]; then
    echo "[OK] Found native standalone Vellum.app bundle. Launching..."
    open "$HERE/Vellum.app"
    exit 0
fi

# 2. Source mode: locate Python environment
PY_BIN=""

if [ -f "$HERE/Desktop_App/.venv/bin/python" ]; then
    PY_BIN="$HERE/Desktop_App/.venv/bin/python"
    echo "[OK] Located dedicated Desktop_App virtualenv (.venv)"
elif [ -f "$HERE/.venv/bin/python" ]; then
    PY_BIN="$HERE/.venv/bin/python"
    echo "[OK] Located root virtualenv (.venv)"
elif command -v python3 >/dev/null 2>&1; then
    PY_BIN="$(command -v python3)"
    echo "[OK] Using system python3: $PY_BIN"
fi

if [ -z "$PY_BIN" ]; then
    echo "[ERROR] Python 3 was not found on your system!"
    echo "Please install Python 3 from https://www.python.org/downloads/ or via Homebrew (brew install python)."
    read -p "Press [Enter] to exit..."
    exit 1
fi

cd "$HERE/Desktop_App"
echo "[*] Target Directory: $HERE/Desktop_App"
echo "[*] Starting Vellum Desktop on http://localhost:8501 ..."
echo ""

"$PY_BIN" -m streamlit run pdf_downloader_app.py --browser.serverAddress localhost --server.port 8501
