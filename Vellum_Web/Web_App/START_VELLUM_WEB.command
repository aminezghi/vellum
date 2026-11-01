#!/bin/bash
# =====================================================================
#       VELLUM BY AMINE - WEB STUDIO (macOS)
#       Academic Research Studio - Force Networks - AI Screening
# =====================================================================

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"

echo "====================================================================="
echo "      VELLUM BY AMINE - WEB STUDIO (macOS)"
echo "      Academic Research Studio - Force Networks - AI Screening"
echo "====================================================================="
echo ""

PORT=3002

# Check for bundled portable Node.js runtime first, then system node
if [ -x "$HERE/runtime/node/bin/node" ]; then
    export PATH="$HERE/runtime/node/bin:$PATH"
    echo "[OK] Located bundled portable Node.js runtime ($(node -v))"
elif command -v node >/dev/null 2>&1; then
    echo "[OK] Located system Node.js ($(node -v))"
else
    echo "[ERROR] Node.js 18 or newer was not found on your system."
    echo "Please install Node.js from https://nodejs.org/ or via Homebrew (brew install node)."
    echo ""
    echo "Alternatively, download the pre-packaged Vellum_Web_macOS.zip"
    echo "which bundles its own Node.js runtime and requires nothing installed."
    echo ""
    read -p "Press [Enter] to exit..."
    exit 1
fi

# Determine whether to run production build or dev server
if [ -f "$HERE/.next/BUILD_ID" ]; then
    echo "[*] Starting the production server on http://localhost:$PORT ..."
    (sleep 2 && open "http://localhost:$PORT") &
    if [ -x "$HERE/node_modules/.bin/next" ]; then
        "$HERE/node_modules/.bin/next" start -p "$PORT"
    else
        npx next start -p "$PORT"
    fi
else
    echo "[*] No production build found - starting development server on http://localhost:$PORT ..."
    (sleep 3 && open "http://localhost:$PORT") &
    if [ -x "$HERE/node_modules/.bin/next" ]; then
        "$HERE/node_modules/.bin/next" dev -p "$PORT"
    else
        npx next dev -p "$PORT"
    fi
fi
