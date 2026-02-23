#!/usr/bin/env bash
# verify_claude_mem.sh — Read-only sanity check for claude-mem plugin on Linux
#
# Detects common ARM64 / fresh-install issues:
#   - Missing or stale installed_plugins.json metadata
#   - Missing bun binary
#   - Wrong-architecture bun (Windows PE, x86_64 on ARM64, etc.)
#   - Missing bun-runner.js at the registered plugin path
#
# Exit codes:
#   0  — all checks passed
#   10 — plugin metadata missing or stale (installPath not on disk)
#   11 — bun binary not found
#   12 — bun wrong architecture / suspected Windows PE
#   13 — bun-runner.js missing at registered installPath
#
# Read-only: this script does NOT modify ~/.claude/, ~/.bun/, or any config.
# Safe to run at any time without side effects.

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}OK${NC}    $*"; }
warn() { echo -e "  ${YELLOW}WARN${NC}  $*"; }
fail() { echo -e "  ${RED}FAIL${NC}  $*"; }
hdr()  { echo -e "\n${BOLD}$*${NC}"; }

ISSUES=0
EXIT_CODE=0

# ── helpers ──────────────────────────────────────────────────────────────────

# Extract installPath from installed_plugins.json
# Uses jq if available; falls back to python3; falls back to grep/sed.
_get_install_path() {
    local pj="$HOME/.claude/plugins/installed_plugins.json"
    if command -v jq &>/dev/null; then
        jq -r '.plugins["claude-mem@thedotmack"]?[0]?.installPath // ""' "$pj" 2>/dev/null
    elif command -v python3 &>/dev/null; then
        python3 - "$pj" <<'EOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    entries = d.get("plugins", {}).get("claude-mem@thedotmack", [])
    print(entries[0].get("installPath", "") if entries else "")
except Exception:
    print("")
EOF
    else
        # Last-resort grep — fragile but avoids hard dependency
        grep -o '"installPath"[[:space:]]*:[[:space:]]*"[^"]*"' "$pj" 2>/dev/null \
            | head -1 | sed 's/.*"installPath"[^"]*"//;s/".*//' || true
    fi
}

_get_version() {
    local pj="$HOME/.claude/plugins/installed_plugins.json"
    if command -v jq &>/dev/null; then
        jq -r '.plugins["claude-mem@thedotmack"]?[0]?.version // ""' "$pj" 2>/dev/null
    elif command -v python3 &>/dev/null; then
        python3 - "$pj" <<'EOF'
import json, sys
try:
    d = json.load(open(sys.argv[1]))
    entries = d.get("plugins", {}).get("claude-mem@thedotmack", [])
    print(entries[0].get("version", "") if entries else "")
except Exception:
    print("")
EOF
    else
        grep -o '"version"[[:space:]]*:[[:space:]]*"[^"]*"' "$pj" 2>/dev/null \
            | head -1 | sed 's/.*"version"[^"]*"//;s/".*//' || true
    fi
}

# ── check 1: plugin metadata ──────────────────────────────────────────────────

hdr "1. Plugin metadata (installed_plugins.json)"

PLUGINS_JSON="$HOME/.claude/plugins/installed_plugins.json"

if [[ ! -f "$PLUGINS_JSON" ]]; then
    fail "File not found: $PLUGINS_JSON"
    echo "     → Claude Code has never installed claude-mem on this machine."
    echo "     → Run: /plugin install claude-mem  inside Claude Code CLI"
    EXIT_CODE=10
    ISSUES=$((ISSUES + 1))
else
    ok "File exists: $PLUGINS_JSON"

    INSTALL_PATH="$(_get_install_path)"
    REGISTERED_VER="$(_get_version)"

    if [[ -z "$INSTALL_PATH" ]]; then
        fail "claude-mem@thedotmack not found in plugins registry"
        echo "     → Plugin was never registered. Run: /plugin install claude-mem"
        EXIT_CODE=10
        ISSUES=$((ISSUES + 1))
    else
        echo "     registered version : ${REGISTERED_VER:-<unknown>}"
        echo "     registered path    : $INSTALL_PATH"

        if [[ -d "$INSTALL_PATH" ]]; then
            ok "installPath directory exists"
        else
            fail "installPath directory MISSING: $INSTALL_PATH"
            # Show what's actually in cache
            CACHE_DIR="$HOME/.claude/plugins/cache/thedotmack/claude-mem"
            if [[ -d "$CACHE_DIR" ]]; then
                REAL_VER=$(ls "$CACHE_DIR" 2>/dev/null | sort -V | tail -1)
                echo "     → Cache contains version(s): $(ls "$CACHE_DIR" 2>/dev/null | tr '\n' ' ')"
                if [[ -n "$REAL_VER" ]]; then
                    echo "     → Fix: update installPath in $PLUGINS_JSON"
                    echo "       to: $CACHE_DIR/$REAL_VER"
                    echo "       or: /plugin install claude-mem  (inside Claude Code CLI)"
                fi
            else
                echo "     → Cache directory not found. Run: /plugin install claude-mem"
            fi
            [[ $EXIT_CODE -eq 0 ]] && EXIT_CODE=10
            ISSUES=$((ISSUES + 1))
        fi
    fi
fi

# ── check 2: bun binary ───────────────────────────────────────────────────────

hdr "2. Bun binary"

BUN_PATH=""
if command -v bun &>/dev/null; then
    BUN_PATH="$(command -v bun)"
elif [[ -x "$HOME/.bun/bin/bun" ]]; then
    BUN_PATH="$HOME/.bun/bin/bun"
    # Resolve symlink target for display
    REAL_TARGET="$(readlink -f "$BUN_PATH" 2>/dev/null || echo "$BUN_PATH")"
    echo "     (not in PATH, using $BUN_PATH → $REAL_TARGET)"
fi

if [[ -z "$BUN_PATH" ]]; then
    fail "bun binary not found (checked PATH and ~/.bun/bin/bun)"
    echo "     → Install: curl -fsSL https://bun.sh/install | bash"
    echo "     → Or use the Python-based installer in docs/arm64-claude-mem.md"
    [[ $EXIT_CODE -eq 0 ]] && EXIT_CODE=11
    ISSUES=$((ISSUES + 1))
else
    ok "bun found: $BUN_PATH"

    # ── check 2a: architecture ────────────────────────────────────────────────
    hdr "3. Bun architecture"

    REAL_BUN="$(readlink -f "$BUN_PATH" 2>/dev/null || echo "$BUN_PATH")"
    HOST_ARCH="$(uname -m)"   # aarch64, x86_64, armv7l, …

    # Read ELF magic + machine bytes (first 20 bytes covers e_machine at offset 18)
    BIN_MAGIC=""
    if command -v python3 &>/dev/null; then
        BIN_MAGIC="$(python3 -c "
import sys
try:
    with open('$REAL_BUN','rb') as f:
        hdr = f.read(20)
    magic = hdr[:4].hex()
    # ELF machine field at bytes 18-19 (little-endian)
    if hdr[:4] == b'\x7fELF':
        machine = int.from_bytes(hdr[18:20], 'little')
        # 0x00b7 = AArch64, 0x003e = x86-64, 0x0028 = ARM32
        machines = {0xb7:'aarch64', 0x3e:'x86_64', 0x28:'arm32'}
        print('ELF:' + machines.get(machine, f'unknown(0x{machine:04x})'))
    elif hdr[:2] == b'MZ':
        print('PE:windows')
    else:
        print('unknown:' + magic)
except Exception as e:
    print('read_error:' + str(e))
" 2>/dev/null)"
    fi

    BUN_VERS=""
    BUN_ARCH_RUNTIME=""
    if BUN_OUTPUT="$("$BUN_PATH" --print "process.arch + ':' + process.platform" 2>&1)"; then
        BUN_ARCH_RUNTIME="$BUN_OUTPUT"
        BUN_VERS="$("$BUN_PATH" --version 2>/dev/null || true)"
    fi

    echo "     host arch     : $HOST_ARCH"
    if [[ -n "$BIN_MAGIC" ]]; then
        echo "     binary format : $BIN_MAGIC"
    fi
    if [[ -n "$BUN_ARCH_RUNTIME" ]]; then
        echo "     bun reports   : $BUN_ARCH_RUNTIME  (version: ${BUN_VERS:-?})"
    fi

    ARCH_FAIL=0
    if [[ "$BIN_MAGIC" == "PE:windows" ]]; then
        fail "Windows PE binary — cannot execute on Linux"
        echo "     → The bun npm package ships a Windows stub, not a real runtime."
        echo "     → Fix: curl -fsSL https://bun.sh/install | bash"
        echo "     →      or see docs/arm64-claude-mem.md Symptom B"
        ARCH_FAIL=1
    elif [[ "$BIN_MAGIC" == ELF:* ]]; then
        BIN_ELF_ARCH="${BIN_MAGIC#ELF:}"
        # Map host uname -m → expected ELF arch string
        case "$HOST_ARCH" in
            aarch64|arm64) EXPECTED_ELF="aarch64" ;;
            x86_64|amd64)  EXPECTED_ELF="x86_64"  ;;
            armv7*)        EXPECTED_ELF="arm32"    ;;
            *)             EXPECTED_ELF="$HOST_ARCH" ;;
        esac
        if [[ "$BIN_ELF_ARCH" == "$EXPECTED_ELF" ]]; then
            ok "ELF arch matches host ($BIN_ELF_ARCH)"
        else
            fail "ELF arch mismatch: binary=$BIN_ELF_ARCH, host=$EXPECTED_ELF"
            echo "     → Binary was compiled for a different CPU."
            echo "     → Fix: curl -fsSL https://bun.sh/install | bash"
            ARCH_FAIL=1
        fi
    elif [[ -n "$BUN_ARCH_RUNTIME" ]]; then
        # Couldn't read ELF, fall back to runtime output
        if echo "$BUN_ARCH_RUNTIME" | grep -q "error\|Illegal\|format"; then
            fail "bun runtime error: $BUN_ARCH_RUNTIME"
            ARCH_FAIL=1
        else
            ok "bun runs (runtime: $BUN_ARCH_RUNTIME)"
        fi
    else
        warn "Could not determine binary architecture (python3 not available)"
    fi

    if [[ $ARCH_FAIL -eq 1 ]]; then
        [[ $EXIT_CODE -eq 0 ]] && EXIT_CODE=12
        ISSUES=$((ISSUES + 1))
    fi
fi

# ── check 3 / 4: bun-runner.js ───────────────────────────────────────────────

hdr "4. bun-runner.js"

# Re-read install path (might have been set above or we skip if metadata bad)
if [[ -z "${INSTALL_PATH:-}" ]]; then
    INSTALL_PATH="$(_get_install_path 2>/dev/null || true)"
fi

if [[ -z "$INSTALL_PATH" ]]; then
    warn "Skipping bun-runner.js check — installPath unknown (see check 1)"
else
    RUNNER_JS="$INSTALL_PATH/scripts/bun-runner.js"
    if [[ -f "$RUNNER_JS" ]]; then
        ok "bun-runner.js found: $RUNNER_JS"
    else
        fail "bun-runner.js NOT found: $RUNNER_JS"
        echo "     → installPath exists but scripts/ directory is incomplete."
        echo "     → Run: /plugin install claude-mem  to refresh the plugin cache"
        [[ $EXIT_CODE -eq 0 ]] && EXIT_CODE=13
        ISSUES=$((ISSUES + 1))
    fi
fi

# ── summary ───────────────────────────────────────────────────────────────────

echo ""
echo "──────────────────────────────────────"
if [[ $ISSUES -eq 0 ]]; then
    echo -e "  ${GREEN}${BOLD}All checks passed.${NC}  No claude-mem issues detected."
else
    echo -e "  ${RED}${BOLD}$ISSUES issue(s) found.${NC}  See next steps above."
    echo ""
    echo "  Full fix guide: docs/arm64-claude-mem.md"
fi
echo "──────────────────────────────────────"

exit $EXIT_CODE
