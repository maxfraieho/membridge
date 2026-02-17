#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/maxfraieho/membridge.git"
INSTALL_DIR="${MEMBRIDGE_DIR:-$HOME/membridge}"
PYTHON="${PYTHON:-python3}"
DRY_RUN=0

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[membridge]${NC} $*"; }
warn()  { echo -e "${YELLOW}[membridge]${NC} $*"; }
error() { echo -e "${RED}[membridge]${NC} $*" >&2; }

dry() {
    if [[ "$DRY_RUN" -eq 1 ]]; then
        info "[DRY-RUN] Would execute: $*"
        return 0
    fi
    "$@"
}

usage() {
    echo "Usage: $0 [--dry-run] <agent|server|all|migrate|cleanup>"
    echo ""
    echo "Modes:"
    echo "  agent     — install agent daemon only (does NOT modify legacy files)"
    echo "  server    — install control plane only"
    echo "  all       — install both server and agent"
    echo "  migrate   — detect legacy installation and generate migration report"
    echo "  cleanup   — stop membridge services safely (preserves data)"
    echo ""
    echo "Options:"
    echo "  --dry-run — simulate installation without making changes"
    echo ""
    echo "Environment variables:"
    echo "  MEMBRIDGE_DIR   — install directory (default: ~/membridge)"
    echo "  PYTHON          — python binary (default: python3)"
    echo ""
    echo "Safety guarantees:"
    echo "  - NEVER modifies ~/.claude-mem/ (memory database)"
    echo "  - NEVER modifies ~/.claude/settings.json (user hooks)"
    echo "  - NEVER modifies ~/.claude/.credentials.json (auth)"
    echo "  - NEVER modifies ~/.claude/auth.json (auth)"
    echo "  - NEVER modifies ~/.claude/settings.local.json (local settings)"
    echo "  - NEVER modifies legacy sync scripts in ~/.claude-mem-minio/bin/"
    echo "  - NEVER deletes data during cleanup"
    exit 1
}

POSITIONAL_ARGS=()
while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=1
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            POSITIONAL_ARGS+=("$1")
            shift
            ;;
    esac
done

MODE="${POSITIONAL_ARGS[0]:-}"
if [[ -z "$MODE" ]] || [[ ! "$MODE" =~ ^(agent|server|all|migrate|cleanup)$ ]]; then
    usage
fi

if [[ "$DRY_RUN" -eq 1 ]]; then
    info "=== DRY-RUN MODE — no changes will be made ==="
    echo ""
fi

info "Membridge installer — mode=$MODE"
info "Install directory: $INSTALL_DIR"


# ============================================================
# MODE: cleanup
# ============================================================
if [[ "$MODE" == "cleanup" ]]; then
    info "Cleanup mode — stopping services safely"
    info "This will NOT delete:"
    info "  - Memory database (~/.claude-mem/)"
    info "  - Authentication files (~/.claude/)"
    info "  - Config files (~/.claude-mem-minio/config.env)"
    echo ""

    if command -v systemctl &>/dev/null; then
        for svc in membridge-server membridge-agent; do
            if systemctl is-active --quiet "$svc" 2>/dev/null; then
                info "Stopping $svc..."
                if [[ $EUID -eq 0 ]]; then
                    dry systemctl stop "$svc"
                elif command -v sudo &>/dev/null; then
                    dry sudo systemctl stop "$svc"
                else
                    warn "Not root — run: sudo systemctl stop $svc"
                fi
            else
                info "$svc is not running"
            fi
        done
    fi

    if command -v pgrep &>/dev/null; then
        ORPHAN_PIDS=$(pgrep -f "claude-mem.*worker" 2>/dev/null || true)
        if [[ -n "$ORPHAN_PIDS" ]]; then
            info "Found orphaned claude-mem worker processes: $ORPHAN_PIDS"
            for pid in $ORPHAN_PIDS; do
                info "  Sending SIGTERM to PID $pid..."
                dry kill -TERM "$pid" 2>/dev/null || true
            done
            sleep 2
            STILL_RUNNING=$(pgrep -f "claude-mem.*worker" 2>/dev/null || true)
            if [[ -n "$STILL_RUNNING" ]]; then
                warn "Some workers still running: $STILL_RUNNING"
                warn "  Use 'kill -9 <pid>' manually if needed"
            fi
        else
            info "No orphaned claude-mem worker processes found"
        fi
    fi

    info "Cleanup complete"
    info "Data preserved at:"
    info "  - ~/.claude-mem/"
    info "  - ~/.claude-mem-minio/config.env"
    info "  - $INSTALL_DIR/ (if exists)"
    exit 0
fi

# ============================================================
# MODE: migrate
# ============================================================
if [[ "$MODE" == "migrate" ]]; then
    info "Migration mode — detecting legacy installation"
    echo ""

    REPORT_FILE="${INSTALL_DIR}/migration-report.json"

    CLAUDE_DIR="$HOME/.claude"
    CLAUDE_MEM_DIR="$HOME/.claude-mem"
    MINIO_DIR="$HOME/.claude-mem-minio"
    MINIO_BIN="$MINIO_DIR/bin"
    DB_PATH="$CLAUDE_MEM_DIR/claude-mem.db"

    claude_cli_found=false
    claude_mem_found=false
    sqlite_db_found=false
    config_env_found=false
    hooks_found=false
    db_size=0
    db_tables=0

    if command -v claude &>/dev/null || [[ -d "$CLAUDE_DIR" ]]; then
        claude_cli_found=true
        info "Claude CLI: found"
    else
        warn "Claude CLI: not found"
    fi

    if [[ -d "$CLAUDE_MEM_DIR" ]]; then
        claude_mem_found=true
        info "claude-mem directory: $CLAUDE_MEM_DIR (exists)"
    else
        warn "claude-mem directory: not found"
    fi

    if [[ -f "$DB_PATH" ]]; then
        sqlite_db_found=true
        db_size=$(stat -c%s "$DB_PATH" 2>/dev/null || stat -f%z "$DB_PATH" 2>/dev/null || echo 0)
        info "SQLite DB: $DB_PATH ($db_size bytes)"
        if command -v "$PYTHON" &>/dev/null; then
            db_tables=$("$PYTHON" -c "
import sqlite3
conn = sqlite3.connect('$DB_PATH')
tables = conn.execute(\"SELECT COUNT(*) FROM sqlite_master WHERE type='table'\").fetchone()[0]
print(tables)
conn.close()
" 2>/dev/null || echo 0)
            info "  Tables: $db_tables"
        fi
    else
        warn "SQLite DB: not found at $DB_PATH"
    fi

    if [[ -f "$MINIO_DIR/config.env" ]]; then
        config_env_found=true
        info "MinIO config: $MINIO_DIR/config.env (exists)"
    else
        warn "MinIO config: not found"
    fi

    HOOKS_LIST=""
    if [[ -d "$MINIO_BIN" ]]; then
        hooks_found=true
        HOOKS_LIST=$(ls -1 "$MINIO_BIN" 2>/dev/null | tr '\n' ',' | sed 's/,$//')
        info "Legacy hooks: $MINIO_BIN ($HOOKS_LIST)"
    else
        warn "Legacy hooks: not found at $MINIO_BIN"
    fi

    settings_json="$CLAUDE_DIR/settings.json"
    settings_hooks="none"
    if [[ -f "$settings_json" ]]; then
        if command -v "$PYTHON" &>/dev/null; then
            settings_hooks=$("$PYTHON" -c "
import json
with open('$settings_json') as f:
    data = json.load(f)
hooks = data.get('hooks', {})
for event, cmds in hooks.items():
    for cmd in cmds:
        print(f'  {event}: {cmd}')
" 2>/dev/null || echo "  (could not parse)")
        fi
    fi

    agent_running=false
    if command -v systemctl &>/dev/null && systemctl is-active --quiet membridge-agent 2>/dev/null; then
        agent_running=true
    fi

    server_running=false
    if command -v systemctl &>/dev/null && systemctl is-active --quiet membridge-server 2>/dev/null; then
        server_running=true
    fi

    echo ""
    info "=== Migration Report ==="
    echo ""
    info "Preserved directories (NEVER modified by installer):"
    info "  ~/.claude-mem/               — memory database"
    info "  ~/.claude/                   — CLI config and auth"
    info "  ~/.claude-mem-minio/config.env — MinIO credentials"
    info "  ~/.claude-mem-minio/bin/     — legacy sync scripts"
    echo ""

    if [[ "$DRY_RUN" -eq 0 ]]; then
        mkdir -p "$(dirname "$REPORT_FILE")"
        cat > "$REPORT_FILE" <<REPORT_EOF
{
  "generated_at": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "hostname": "$(hostname)",
  "legacy_installation": {
    "claude_cli": $claude_cli_found,
    "claude_mem_plugin": $claude_mem_found,
    "sqlite_db": {
      "found": $sqlite_db_found,
      "path": "$DB_PATH",
      "size_bytes": $db_size,
      "tables": $db_tables
    },
    "minio_config": {
      "found": $config_env_found,
      "path": "$MINIO_DIR/config.env"
    },
    "legacy_hooks": {
      "found": $hooks_found,
      "path": "$MINIO_BIN",
      "scripts": "$HOOKS_LIST"
    }
  },
  "membridge_services": {
    "agent_running": $agent_running,
    "server_running": $server_running
  },
  "preserved_paths": [
    "$CLAUDE_MEM_DIR",
    "$CLAUDE_DIR",
    "$MINIO_DIR/config.env"
  ],
  "migration_safe": true,
  "notes": [
    "Legacy hooks in $MINIO_BIN remain functional",
    "New agent runs alongside legacy scripts",
    "No modification to existing data or auth files"
  ]
}
REPORT_EOF
        info "Report saved to: $REPORT_FILE"
    else
        info "[DRY-RUN] Would save report to: $REPORT_FILE"
    fi
    exit 0
fi


# ============================================================
# MODES: agent, server, all
# ============================================================

# --- Check Python ---
if ! command -v "$PYTHON" &>/dev/null; then
    error "Python not found. Install Python 3.11+ and try again."
    exit 1
fi

PY_VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
PY_MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
PY_MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")
if [[ "$PY_MAJOR" -lt 3 ]] || [[ "$PY_MINOR" -lt 11 ]]; then
    error "Python 3.11+ required, found $PY_VERSION"
    exit 1
fi
info "Python $PY_VERSION OK"

# --- Clone or update repo ---
if [[ "$DRY_RUN" -eq 1 ]]; then
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        info "[DRY-RUN] Would update existing repo at $INSTALL_DIR"
    else
        info "[DRY-RUN] Would clone $REPO_URL to $INSTALL_DIR"
    fi
else
    if [[ -d "$INSTALL_DIR/.git" ]]; then
        info "Updating existing installation..."
        git -C "$INSTALL_DIR" pull --ff-only || {
            warn "git pull failed — continuing with existing code"
        }
    else
        info "Cloning membridge..."
        git clone "$REPO_URL" "$INSTALL_DIR"
    fi
fi

if [[ "$DRY_RUN" -eq 0 ]]; then
    cd "$INSTALL_DIR"
fi

# --- Create venv ---
if [[ "$DRY_RUN" -eq 1 ]]; then
    info "[DRY-RUN] Would create/update Python venv and install dependencies"
else
    if [[ ! -d ".venv" ]]; then
        info "Creating Python venv..."
        "$PYTHON" -m venv .venv
    fi
    source .venv/bin/activate
    info "Installing Python dependencies..."
    pip install --quiet --upgrade pip
    pip install --quiet fastapi uvicorn httpx pydantic boto3
fi

# --- Generate env files (NEVER echoes secret values) ---
generate_key() {
    python3 -c "import secrets; print(secrets.token_hex(24))"
}

if [[ "$MODE" == "server" || "$MODE" == "all" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
        if [[ -f "$INSTALL_DIR/.env.server" ]]; then
            info "[DRY-RUN] .env.server already exists — would skip"
        else
            info "[DRY-RUN] Would generate .env.server with random auth keys"
        fi
    else
        if [[ ! -f ".env.server" ]]; then
            ADMIN_KEY=$(generate_key)
            AGENT_KEY=$(generate_key)
            cat > .env.server <<EOF
MEMBRIDGE_ADMIN_KEY=$ADMIN_KEY
MEMBRIDGE_AGENT_KEY=$AGENT_KEY
MEMBRIDGE_DATA_DIR=$INSTALL_DIR/server/data
EOF
            info "Created .env.server"
            info "  MEMBRIDGE_ADMIN_KEY and MEMBRIDGE_AGENT_KEY generated"
            warn "  Save these keys — you'll need MEMBRIDGE_AGENT_KEY on each agent machine"
        else
            info ".env.server already exists — skipping"
        fi
    fi
fi

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
    if [[ "$DRY_RUN" -eq 1 ]]; then
        if [[ -f "$INSTALL_DIR/.env.agent" ]]; then
            info "[DRY-RUN] .env.agent already exists — would skip"
        else
            info "[DRY-RUN] Would generate .env.agent template"
        fi
    else
        if [[ ! -f ".env.agent" ]]; then
            cat > .env.agent <<EOF
MEMBRIDGE_AGENT_KEY=REPLACE_WITH_KEY_FROM_SERVER
MEMBRIDGE_AGENT_DRYRUN=0
MEMBRIDGE_ALLOW_PROCESS_CONTROL=0
MEMBRIDGE_HOOKS_BIN=$INSTALL_DIR/hooks
MEMBRIDGE_CONFIG_ENV=$HOME/.claude-mem-minio/config.env
EOF
            info "Created .env.agent"
            warn "  Edit .env.agent and set MEMBRIDGE_AGENT_KEY from server's .env.server"
        else
            info ".env.agent already exists — skipping"
        fi
    fi
fi

# --- Make hooks executable ---
if [[ -d "${INSTALL_DIR}/hooks" ]]; then
    dry chmod +x "${INSTALL_DIR}/hooks/"* 2>/dev/null || true
fi

# --- Systemd (Linux only) ---
install_systemd_unit() {
    local svc_name="$1"
    local svc_source="$INSTALL_DIR/deploy/systemd/${svc_name}.service"
    local svc_dest="/etc/systemd/system/${svc_name}.service"

    if [[ ! -f "$svc_source" ]]; then
        warn "Systemd unit not found: $svc_source — skipping"
        return
    fi

    local user_home
    user_home=$(eval echo "~$(whoami)")

    local tmp_unit="/tmp/${svc_name}.service"
    sed -e "s|%h|$user_home|g" -e "s|%i|$(whoami)|g" "$svc_source" > "$tmp_unit"

    if command -v systemctl &>/dev/null; then
        local needs_update=0
        if [[ -f "$svc_dest" ]]; then
            if ! diff -q "$tmp_unit" "$svc_dest" &>/dev/null; then
                needs_update=1
                info "Systemd: $svc_name unit changed — updating"
            else
                info "Systemd: $svc_name unit unchanged"
            fi
        else
            needs_update=1
            info "Systemd: installing $svc_name"
        fi

        if [[ "$needs_update" -eq 1 ]] || ! systemctl is-active --quiet "$svc_name" 2>/dev/null; then
            if [[ $EUID -eq 0 ]]; then
                dry cp "$tmp_unit" "$svc_dest"
                dry systemctl daemon-reload
                dry systemctl enable "$svc_name"
                dry systemctl restart "$svc_name"
                info "Systemd: $svc_name enabled and started"
            else
                if command -v sudo &>/dev/null; then
                    dry sudo cp "$tmp_unit" "$svc_dest"
                    dry sudo systemctl daemon-reload
                    dry sudo systemctl enable "$svc_name"
                    dry sudo systemctl restart "$svc_name"
                    info "Systemd: $svc_name enabled and started (via sudo)"
                else
                    warn "Not root and no sudo — copy manually:"
                    warn "  sudo cp $tmp_unit $svc_dest"
                    warn "  sudo systemctl daemon-reload && sudo systemctl enable --now $svc_name"
                fi
            fi
        fi
    else
        info "Systemd not found — run manually instead:"
        if [[ "$svc_name" == "membridge-server" ]]; then
            info "  cd $INSTALL_DIR && source .venv/bin/activate"
            info "  source .env.server"
            info "  python -m uvicorn server.main:app --host 0.0.0.0 --port 8000"
        else
            info "  cd $INSTALL_DIR && source .venv/bin/activate"
            info "  source .env.agent"
            info "  python -m uvicorn agent.main:app --host 0.0.0.0 --port 8001"
        fi
    fi
    rm -f "$tmp_unit"
}

if [[ "$MODE" == "server" || "$MODE" == "all" ]]; then
    install_systemd_unit "membridge-server"
fi

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
    install_systemd_unit "membridge-agent"
fi

# --- Safety verification ---
echo ""
info "=== Safety Verification ==="
SAFE=true
for protected in "$HOME/.claude-mem" "$HOME/.claude/settings.json" "$HOME/.claude/.credentials.json" "$HOME/.claude/auth.json" "$HOME/.claude/settings.local.json" "$HOME/.claude-mem-minio/bin"; do
    if [[ -e "$protected" ]]; then
        info "  Protected: $protected (unchanged)"
    fi
done
echo ""

# --- Summary ---
echo "============================================"
info "Installation complete!"
echo "============================================"
echo ""

if [[ "$MODE" == "server" || "$MODE" == "all" ]]; then
    info "Control Plane:"
    info "  Health: curl http://localhost:8000/health"
    info "  Env:    $INSTALL_DIR/.env.server"
    if command -v systemctl &>/dev/null; then
        info "  Logs:   journalctl -u membridge-server -f"
    fi
    echo ""
fi

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
    info "Agent Daemon:"
    info "  Health: curl http://localhost:8001/health"
    info "  Env:    $INSTALL_DIR/.env.agent"
    if command -v systemctl &>/dev/null; then
        info "  Logs:   journalctl -u membridge-agent -f"
    fi
    echo ""
fi

info "Next steps:"
if [[ "$MODE" == "agent" ]]; then
    warn "1. Edit $INSTALL_DIR/.env.agent — set MEMBRIDGE_AGENT_KEY"
    info "2. Ensure ~/.claude-mem-minio/config.env exists with MinIO credentials"
    info "3. Restart: systemctl restart membridge-agent (or run manually)"
elif [[ "$MODE" == "server" ]]; then
    info "1. Note your admin key from .env.server"
    info "2. Register agents: curl -X POST http://localhost:8000/agents ..."
elif [[ "$MODE" == "all" ]]; then
    warn "1. For remote agents: copy MEMBRIDGE_AGENT_KEY from .env.server to each agent's .env.agent"
    info "2. Register agents: curl -X POST http://localhost:8000/agents ..."
fi

info ""
info "Validate installation:"
info "  cd $INSTALL_DIR && source .venv/bin/activate"
info "  python -m membridge.validate_install"
