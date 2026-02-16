#!/bin/bash
# bootstrap-linux.sh — Deploy Claude config from membridge repo to ~/.claude
# Works on: Raspberry Pi, Orange Pi, Ubuntu, Debian, and other Linux distros
# Does NOT touch: auth, tokens, credentials, plugins/cache, databases
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$CLAUDE_DIR/backup/$TIMESTAMP"
CONFIG_SRC="$REPO_DIR/config/claude"

echo "=== Claude Config Bootstrap (Linux) ==="
echo "Source:  $CONFIG_SRC"
echo "Target:  $CLAUDE_DIR"

# Verify source exists
if [ ! -d "$CONFIG_SRC" ]; then
    echo "ERROR: Config source not found: $CONFIG_SRC"
    echo "  Make sure you're running from the membridge repo."
    exit 1
fi

# Create ~/.claude if needed
mkdir -p "$CLAUDE_DIR"
mkdir -p "$CLAUDE_DIR/hooks"

# Backup existing safe files (not auth/cache/plugins)
echo ""
echo "--- Backing up existing config to $BACKUP_DIR ---"
mkdir -p "$BACKUP_DIR"

for f in settings.json mcp.json; do
    if [ -f "$CLAUDE_DIR/$f" ]; then
        cp "$CLAUDE_DIR/$f" "$BACKUP_DIR/$f"
        echo "  Backed up: $f"
    fi
done

# Backup MCP configs
for f in "$CLAUDE_DIR"/mcp*.json; do
    [ -f "$f" ] || continue
    cp "$f" "$BACKUP_DIR/"
    echo "  Backed up: $(basename "$f")"
done

# Backup hooks
if [ -d "$CLAUDE_DIR/hooks" ] && [ "$(ls -A "$CLAUDE_DIR/hooks" 2>/dev/null)" ]; then
    mkdir -p "$BACKUP_DIR/hooks"
    cp -a "$CLAUDE_DIR/hooks/." "$BACKUP_DIR/hooks/"
    echo "  Backed up: hooks/"
fi

# Deploy settings.json
echo ""
echo "--- Deploying config ---"
if [ -f "$CONFIG_SRC/settings.json" ]; then
    cp "$CONFIG_SRC/settings.json" "$CLAUDE_DIR/settings.json"
    echo "  Deployed: settings.json"
fi

# Deploy MCP configs
for f in "$CONFIG_SRC"/mcp*.json; do
    [ -f "$f" ] || continue
    cp "$f" "$CLAUDE_DIR/"
    echo "  Deployed: $(basename "$f")"
done

# Deploy hooks
if [ -d "$CONFIG_SRC/hooks" ] && [ "$(ls -A "$CONFIG_SRC/hooks" 2>/dev/null)" ]; then
    for f in "$CONFIG_SRC/hooks/"*; do
        [ -f "$f" ] || continue
        cp "$f" "$CLAUDE_DIR/hooks/"
        chmod +x "$CLAUDE_DIR/hooks/$(basename "$f")"
        echo "  Deployed: hooks/$(basename "$f")"
    done
fi

# Self-check
echo ""
echo "--- Verification ---"
if [ -f "$CLAUDE_DIR/settings.json" ]; then
    python3 -c "import json; json.load(open('$CLAUDE_DIR/settings.json')); print('  settings.json: valid JSON')" 2>/dev/null || \
        echo "  WARNING: settings.json is not valid JSON"
fi

# Check no auth files were touched
for dangerous in .credentials.json auth token credential; do
    if [ -f "$BACKUP_DIR/$dangerous" ] 2>/dev/null; then
        echo "  ERROR: Auth file found in backup — this should not happen"
        exit 1
    fi
done

echo ""
echo "=== SUCCESS ==="
echo "Claude config deployed from membridge."
echo "Auth/tokens remain untouched (local only)."
echo "Backup: $BACKUP_DIR"
