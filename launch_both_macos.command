#!/bin/bash
# =====================================================================
#       VELLUM BY AMINE - LAUNCHING DESKTOP WORKBENCH + WEB STUDIO (macOS)
#       Desktop: http://localhost:8501   |   Web: http://localhost:3002
# =====================================================================

HERE="$(cd "$(dirname "$0")" && pwd)"

echo "====================================================================="
echo "      VELLUM BY AMINE - LAUNCHING DESKTOP WORKBENCH + WEB STUDIO"
echo "      Desktop: http://localhost:8501   |   Web: http://localhost:3002"
echo "====================================================================="
echo ""

# Launch Desktop in separate background terminal session or process
open -a Terminal "$HERE/launch_desktop_macos.command"

# Launch Web in separate background terminal session or process
open -a Terminal "$HERE/launch_web_macos.command"

echo "[OK] Both applications launched."
echo "     Desktop Workbench : http://localhost:8501"
echo "     Web Studio        : http://localhost:3002"
echo ""
sleep 2
exit 0
