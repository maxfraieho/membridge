#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/maxfraieho/membridge.git"
INSTALL_DIR="${MEMBRIDGE_DIR:-$HOME/membridge}"
PYTHON="${PYTHON:-python3}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[membridge]${NC} $*"; }
warn()  { echo -e "${YELLOW}[membridge]${NC} $*"; }
error() { echo -e "${RED}[membridge]${NC} $*" >&2; }

usage() {
    echo "Usage: $0 <agent|server|all>"
    echo ""
    echo "  agent   — install agent daemon only"
    echo "  server  — install control plane only"
    echo "  all     — install both"
    echo ""
    echo "Environment variables:"
    echo "  MEMBRIDGE_DIR   — install directory (default: ~/membridge)"
    echo "  PYTHON          — python binary (default: python3)"
    exit 1
}

MODE="${1:-}"
if [[ -z "$MODE" ]] || [[ "$MODE" != "agent" && "$MODE" != "server" && "$MODE" != "all" ]]; then
    usage
fi

info "Membridge installer — mode=$MODE"
info "Install directory: $INSTALL_DIR"

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
if [[ -d "$INSTALL_DIR/.git" ]]; then
    info "Updating existing installation..."
    git -C "$INSTALL_DIR" pull --ff-only || {
        warn "git pull failed — continuing with existing code"
    }
else
    info "Cloning membridge..."
    git clone "$REPO_URL" "$INSTALL_DIR"
fi

cd "$INSTALL_DIR"

# --- Create venv ---
if [[ ! -d ".venv" ]]; then
    info "Creating Python venv..."
    "$PYTHON" -m venv .venv
fi
source .venv/bin/activate
info "Installing Python dependencies..."
pip install --quiet --upgrade pip
pip install --quiet fastapi uvicorn httpx pydantic boto3

# --- Generate env files ---
generate_key() {
    python3 -c "import secrets; print(secrets.token_hex(24))"
}

if [[ "$MODE" == "server" || "$MODE" == "all" ]]; then
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

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
    if [[ ! -f ".env.agent" ]]; then
        cat > .env.agent <<EOF
MEMBRIDGE_AGENT_KEY=REPLACE_WITH_KEY_FROM_SERVER
MEMBRIDGE_AGENT_DRYRUN=0
MEMBRIDGE_HOOKS_BIN=$INSTALL_DIR/hooks
MEMBRIDGE_CONFIG_ENV=$HOME/.claude-mem-minio/config.env
EOF
        info "Created .env.agent"
        warn "  Edit .env.agent and set MEMBRIDGE_AGENT_KEY from server's .env.server"
    else
        info ".env.agent already exists — skipping"
    fi
fi

# --- Make hooks executable ---
if [[ -d "hooks" ]]; then
    chmod +x hooks/* 2>/dev/null || true
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

    sed -e "s|%h|$user_home|g" -e "s|%i|$(whoami)|g" "$svc_source" > /tmp/${svc_name}.service

    if command -v systemctl &>/dev/null; then
        if [[ $EUID -eq 0 ]]; then
            cp /tmp/${svc_name}.service "$svc_dest"
            systemctl daemon-reload
            systemctl enable "$svc_name"
            systemctl restart "$svc_name"
            info "Systemd: $svc_name enabled and started"
        else
            if command -v sudo &>/dev/null; then
                sudo cp /tmp/${svc_name}.service "$svc_dest"
                sudo systemctl daemon-reload
                sudo systemctl enable "$svc_name"
                sudo systemctl restart "$svc_name"
                info "Systemd: $svc_name enabled and started (via sudo)"
            else
                warn "Not root and no sudo — copy manually:"
                warn "  sudo cp /tmp/${svc_name}.service $svc_dest"
                warn "  sudo systemctl daemon-reload && sudo systemctl enable --now $svc_name"
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
    rm -f /tmp/${svc_name}.service
}

if [[ "$MODE" == "server" || "$MODE" == "all" ]]; then
    install_systemd_unit "membridge-server"
fi

if [[ "$MODE" == "agent" || "$MODE" == "all" ]]; then
    install_systemd_unit "membridge-agent"
fi

# --- Summary ---
echo ""
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
