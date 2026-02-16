#!/bin/bash
# bootstrap-alpine.sh — Prepare Alpine Linux and deploy Claude config
# For Alpine x86_64 (e.g., Docker containers, lightweight VMs)
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Claude Config Bootstrap (Alpine) ==="

# Install required packages if running as root or with sudo
if command -v apk >/dev/null 2>&1; then
    echo "--- Installing dependencies ---"
    if [ "$(id -u)" -eq 0 ]; then
        apk add --no-cache bash coreutils util-linux git curl python3 2>/dev/null || true
    else
        echo "  Not root — skipping apk install. Ensure bash, git, curl, python3 are available."
    fi
else
    echo "  Not an Alpine system (no apk). Skipping package install."
fi

# Delegate to the main Linux bootstrap
echo ""
exec bash "$SCRIPT_DIR/bootstrap-linux.sh"
