#!/bin/bash
# bootstrap-alpine.sh — Prepare Alpine Linux and deploy Claude config + MinIO sync
# Alpine-specific: installs packages, handles ash/bash, then delegates to bootstrap-linux.sh
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "=== Membridge Bootstrap (Alpine) ==="
echo ""

# --- 1. Verify we're on Alpine ---
if [ ! -f /etc/alpine-release ]; then
    echo "WARNING: Not an Alpine system (/etc/alpine-release missing)"
    echo "  Consider using bootstrap-linux.sh instead."
    echo "  Continuing anyway..."
    echo ""
fi

# --- 2. Install required packages ---
if command -v apk >/dev/null 2>&1; then
    echo "--- Installing Alpine packages ---"
    if [ "$(id -u)" -eq 0 ]; then
        apk add --no-cache bash coreutils git curl python3 py3-pip py3-virtualenv nodejs npm 2>&1 | \
            while IFS= read -r line; do echo "  $line"; done
        echo "  Packages installed"
    else
        echo "  Not root — attempting with sudo..."
        if command -v sudo >/dev/null 2>&1; then
            sudo apk add --no-cache bash coreutils git curl python3 py3-pip py3-virtualenv nodejs npm 2>&1 | \
                while IFS= read -r line; do echo "  $line"; done
            echo "  Packages installed (via sudo)"
        else
            echo "  WARNING: Not root and no sudo. Ensure these packages are installed:"
            echo "    bash coreutils git curl python3 py3-pip py3-virtualenv nodejs npm"
        fi
    fi
else
    echo "  No apk found — skipping package install"
fi

# --- 3. Verify bash is available ---
echo ""
echo "--- Verifying bash ---"
if ! command -v bash >/dev/null 2>&1; then
    echo "ERROR: bash not found. Alpine uses ash by default."
    echo "  Install bash: apk add bash"
    exit 1
fi
echo "  OK: bash available at $(command -v bash)"

# --- 4. Verify key hooks use #!/bin/bash ---
echo ""
echo "--- Checking hook shebangs ---"
HOOKS_DIR="$SCRIPT_DIR/../hooks"
BAD_SHEBANGS=0
if [ -d "$HOOKS_DIR" ]; then
    for f in "$HOOKS_DIR"/*; do
        [ -f "$f" ] || continue
        SHEBANG=$(head -1 "$f")
        if [ "$SHEBANG" != "#!/bin/bash" ]; then
            echo "  WARNING: $(basename "$f") has shebang: $SHEBANG (expected #!/bin/bash)"
            BAD_SHEBANGS=$((BAD_SHEBANGS + 1))
        fi
    done
    if [ "$BAD_SHEBANGS" -eq 0 ]; then
        echo "  OK: all hooks use #!/bin/bash"
    fi
fi

# --- 5. Delegate to the main Linux bootstrap ---
echo ""
echo "--- Delegating to bootstrap-linux.sh ---"
echo ""
exec bash "$SCRIPT_DIR/bootstrap-linux.sh"
