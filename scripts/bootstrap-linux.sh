#!/bin/bash
# bootstrap-linux.sh — Deploy Claude config + MinIO sync from membridge repo
# Source of truth: claude-home/ directory in this repo
# Works on: Raspberry Pi, Orange Pi, Ubuntu, Debian, Alpine, and other Linux distros
# Does NOT touch: auth, tokens, credentials, plugins/cache, databases
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CLAUDE_DIR="$HOME/.claude"
CLAUDE_HOME_SRC="$REPO_DIR/claude-home"
TIMESTAMP="$(date +%Y%m%d-%H%M%S)"
BACKUP_DIR="$CLAUDE_DIR/backup/$TIMESTAMP"

echo "=== Membridge Bootstrap (Linux) ==="
echo "Source:  $CLAUDE_HOME_SRC"
echo "Target:  $CLAUDE_DIR"
echo ""

# Verify source exists
if [ ! -d "$CLAUDE_HOME_SRC" ]; then
    echo "ERROR: Source not found: $CLAUDE_HOME_SRC"
    echo "  Make sure you're running from the membridge repo."
    exit 1
fi

# --- 1. Backup existing safe files ---
echo "--- Backing up existing config to $BACKUP_DIR ---"
mkdir -p "$BACKUP_DIR"

# Backup individual files
for f in CLAUDE.md settings.json mcp.json; do
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

# Backup directories
for d in skills skills-local skills-installer hooks commands; do
    if [ -d "$CLAUDE_DIR/$d" ] && [ "$(ls -A "$CLAUDE_DIR/$d" 2>/dev/null)" ]; then
        mkdir -p "$BACKUP_DIR/$d"
        cp -a "$CLAUDE_DIR/$d/." "$BACKUP_DIR/$d/"
        echo "  Backed up: $d/"
    fi
done

# Backup plugins metadata (not cache)
if [ -d "$CLAUDE_DIR/plugins" ]; then
    mkdir -p "$BACKUP_DIR/plugins"
    for f in installed_plugins.json known_marketplaces.json CLAUDE.md; do
        [ -f "$CLAUDE_DIR/plugins/$f" ] && cp "$CLAUDE_DIR/plugins/$f" "$BACKUP_DIR/plugins/$f"
    done
    echo "  Backed up: plugins/ (metadata only)"
fi

# --- 2. Deploy from claude-home/ ---
echo ""
echo "--- Deploying claude-home/ → ~/.claude/ ---"

# Create target directories
mkdir -p "$CLAUDE_DIR"

# Deploy CLAUDE.md
if [ -f "$CLAUDE_HOME_SRC/CLAUDE.md" ]; then
    cp "$CLAUDE_HOME_SRC/CLAUDE.md" "$CLAUDE_DIR/CLAUDE.md"
    echo "  Deployed: CLAUDE.md"
fi

# Deploy directories
for d in skills skills-local skills-installer hooks commands; do
    if [ -d "$CLAUDE_HOME_SRC/$d" ]; then
        rm -rf "$CLAUDE_DIR/$d"
        cp -a "$CLAUDE_HOME_SRC/$d" "$CLAUDE_DIR/$d"
        echo "  Deployed: $d/"
    fi
done

# Deploy plugins metadata only (NOT cache)
if [ -d "$CLAUDE_HOME_SRC/plugins" ]; then
    mkdir -p "$CLAUDE_DIR/plugins"
    for f in installed_plugins.json known_marketplaces.json CLAUDE.md; do
        if [ -f "$CLAUDE_HOME_SRC/plugins/$f" ]; then
            cp "$CLAUDE_HOME_SRC/plugins/$f" "$CLAUDE_DIR/plugins/$f"
            echo "  Deployed: plugins/$f"
        fi
    done
fi

# --- 3. Deploy settings.json from claude-home/ (if present) ---
if [ -f "$CLAUDE_HOME_SRC/settings.json" ]; then
    cp "$CLAUDE_HOME_SRC/settings.json" "$CLAUDE_DIR/settings.json"
    echo "  Deployed: settings.json (from claude-home/)"
fi

# --- 4. Setup MinIO sync ---
echo ""
echo "--- Setting up MinIO sync ---"

MINIO_DIR="$HOME/.claude-mem-minio"
MINIO_BIN="$MINIO_DIR/bin"
BACKUPS_DIR="$HOME/.claude-mem-backups"

mkdir -p "$MINIO_BIN" "$BACKUPS_DIR"
echo "  Created: $MINIO_DIR/bin/, $BACKUPS_DIR/"

# Copy hook scripts to runtime location
cp "$REPO_DIR/hooks/"* "$MINIO_BIN/"
chmod +x "$MINIO_BIN/"*
echo "  Deployed: hooks/* → $MINIO_BIN/"

# Create venv + install boto3
if [ ! -d "$REPO_DIR/venv" ]; then
    echo "  Creating Python venv..."
    python3 -m venv "$REPO_DIR/venv"
fi
echo "  Installing boto3..."
"$REPO_DIR/venv/bin/pip" install -q boto3
echo "  Python venv ready with boto3"

# Create config.env from example if not exists
if [ ! -f "$MINIO_DIR/config.env" ]; then
    cp "$REPO_DIR/config.env.example" "$MINIO_DIR/config.env"
    echo "  Created: $MINIO_DIR/config.env (from example — EDIT THIS)"
else
    echo "  Exists:  $MINIO_DIR/config.env (not overwritten)"
fi

# Create symlink in repo for convenience
if [ ! -e "$REPO_DIR/config.env" ]; then
    ln -sf "$MINIO_DIR/config.env" "$REPO_DIR/config.env"
    echo "  Symlink: config.env → $MINIO_DIR/config.env"
fi

# --- 5. Fix permissions ---
echo ""
echo "--- Fixing permissions ---"

# Make all hooks executable
chmod +x "$MINIO_BIN/"* 2>/dev/null || true
if [ -d "$CLAUDE_DIR/hooks" ]; then
    find "$CLAUDE_DIR/hooks" -type f \( -name "*.sh" -o ! -name "*.*" \) -exec chmod +x {} \; 2>/dev/null || true
fi
echo "  All hooks marked executable"

# --- 6. Verification ---
echo ""
echo "--- Verification ---"

ERRORS=0

# Check settings.json valid JSON
if [ -f "$CLAUDE_DIR/settings.json" ]; then
    if python3 -c "import json; json.load(open('$CLAUDE_DIR/settings.json'))" 2>/dev/null; then
        echo "  OK: settings.json is valid JSON"
    else
        echo "  WARNING: settings.json is not valid JSON"
        ERRORS=$((ERRORS + 1))
    fi
fi

# Check skills present
if [ -d "$CLAUDE_DIR/skills" ] && [ "$(ls -A "$CLAUDE_DIR/skills" 2>/dev/null)" ]; then
    SKILL_COUNT=$(find "$CLAUDE_DIR/skills" -maxdepth 1 -mindepth 1 -type d 2>/dev/null | wc -l)
    echo "  OK: skills/ present ($SKILL_COUNT skills)"
else
    echo "  WARNING: skills/ empty or missing"
    ERRORS=$((ERRORS + 1))
fi

# Check hooks present
if [ -d "$CLAUDE_DIR/hooks" ] && [ "$(ls -A "$CLAUDE_DIR/hooks" 2>/dev/null)" ]; then
    echo "  OK: hooks/ present"
else
    echo "  WARNING: hooks/ empty or missing"
    ERRORS=$((ERRORS + 1))
fi

# Check MinIO hooks present
if [ -f "$MINIO_BIN/claude-mem-hook-pull" ] && [ -f "$MINIO_BIN/claude-mem-hook-push" ]; then
    echo "  OK: MinIO sync hooks present"
else
    echo "  WARNING: MinIO sync hooks missing"
    ERRORS=$((ERRORS + 1))
fi

# Check no auth files were touched
for dangerous in .credentials.json auth.json; do
    if [ -f "$BACKUP_DIR/$dangerous" ] 2>/dev/null; then
        echo "  ERROR: Auth file found in backup — this should not happen"
        ERRORS=$((ERRORS + 1))
    fi
done

# --- Summary ---
echo ""
if [ "$ERRORS" -eq 0 ]; then
    echo "=== SUCCESS ==="
else
    echo "=== COMPLETED WITH $ERRORS WARNING(S) ==="
fi
echo "Claude config deployed from claude-home/"
echo "MinIO sync hooks deployed to $MINIO_BIN/"
echo "Auth/tokens remain untouched (local only)"
echo "Backup: $BACKUP_DIR"
echo ""
echo "--- Next steps ---"
echo "1. Edit MinIO credentials:  nano $MINIO_DIR/config.env"
echo "2. Run diagnostics:         $MINIO_BIN/claude-mem-doctor"
echo "3. First sync:              $MINIO_BIN/claude-mem-pull  (or cm-pull if aliased)"
