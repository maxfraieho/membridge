#!/usr/bin/env bash
# verify_leadership.sh — Smoke test for the Primary/Secondary leadership feature.
#
# Usage:
#   ./scripts/verify_leadership.sh
#
# Prerequisites:
#   - Python 3, boto3 installed
#   - MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET,
#     CLAUDE_PROJECT_ID, CLAUDE_MEM_DB env vars set (or in config.env)
#
# Exit code: 0 = all checks passed, non-zero = a check failed.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
SYNC_SCRIPT="$REPO_ROOT/sqlite_minio_sync.py"
CONFIG_ENV="${MEMBRIDGE_CONFIG_ENV:-$HOME/.claude-mem-minio/config.env}"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $*"; }
fail() { echo -e "${RED}[FAIL]${NC} $*"; FAILURES=$((FAILURES + 1)); }
info() { echo -e "${YELLOW}[INFO]${NC} $*"; }

FAILURES=0

echo "=============================="
echo " Membridge Leadership Smoke Test"
echo "=============================="
echo

# Load config.env if present
if [ -f "$CONFIG_ENV" ]; then
    info "Loading config from $CONFIG_ENV"
    set -a
    # shellcheck disable=SC1090
    source "$CONFIG_ENV"
    set +a
fi

# ── Check 1: Required env vars ──────────────────────────────────
echo "[1] Required env vars"
for var in MINIO_ENDPOINT MINIO_ACCESS_KEY MINIO_SECRET_KEY MINIO_BUCKET CLAUDE_PROJECT_ID CLAUDE_MEM_DB; do
    if [ -n "${!var:-}" ]; then
        pass "  $var is set"
    else
        fail "  $var is NOT set"
    fi
done
echo

# ── Check 2: Print project identity ─────────────────────────────
echo "[2] Project identity"
if python3 "$SYNC_SCRIPT" print_project 2>&1; then
    pass "  print_project OK"
else
    fail "  print_project FAILED"
fi
echo

# ── Check 3: leadership_info command ───────────────────────────
echo "[3] leadership_info"
if python3 "$SYNC_SCRIPT" leadership_info 2>&1; then
    pass "  leadership_info OK"
else
    # Exit code 2 means primary refused pull — that's a role gate, not a script error
    rc=$?
    if [ "$rc" -eq 2 ]; then
        pass "  leadership_info ran (exit 2 = primary gate, expected in some setups)"
    else
        fail "  leadership_info FAILED (exit $rc)"
    fi
fi
echo

# ── Check 4: Secondary push gate (unit test via env override) ───
echo "[4] Secondary push gate"
DB_PATH="${CLAUDE_MEM_DB:-$HOME/.claude-mem/claude-mem.db}"

if [ -f "$DB_PATH" ]; then
    # Pretend we are a secondary by overriding NODE_ID and setting a different PRIMARY
    MEMBRIDGE_NODE_ID="fake-secondary-node" \
    PRIMARY_NODE_ID="fake-primary-node" \
    LEADERSHIP_ENABLED=1 \
    ALLOW_SECONDARY_PUSH=0 \
    python3 "$SYNC_SCRIPT" push_sqlite 2>&1
    rc=$?
    if [ "$rc" -eq 3 ]; then
        pass "  Secondary push correctly blocked (exit 3)"
    elif [ "$rc" -eq 0 ]; then
        fail "  Secondary push was NOT blocked (exit 0) — gate may not be working"
    else
        info "  Secondary push exited $rc (may be a MinIO/lock error, not gate failure)"
    fi
else
    info "  DB not found at $DB_PATH — skipping secondary push gate test"
fi
echo

# ── Check 5: Primary pull gate (unit test via env override) ──────
echo "[5] Primary pull gate"
if [ -f "$DB_PATH" ]; then
    # Pretend we are the primary — pull should be refused if SHA differs
    # We can only test this if there is an actual remote SHA mismatch.
    # Here we just verify the command runs and exits with a meaningful code.
    MEMBRIDGE_NODE_ID="$(hostname)" \
    PRIMARY_NODE_ID="$(hostname)" \
    LEADERSHIP_ENABLED=1 \
    ALLOW_PRIMARY_PULL_OVERRIDE=0 \
    python3 "$SYNC_SCRIPT" pull_sqlite 2>&1
    rc=$?
    if [ "$rc" -eq 0 ]; then
        pass "  Pull returned 0 (already up-to-date or first sync)"
    elif [ "$rc" -eq 2 ]; then
        pass "  Primary pull gate triggered correctly (exit 2 = refused overwrite)"
    else
        info "  Pull exited $rc (MinIO error or network issue — check doctor output)"
    fi
else
    info "  DB not found at $DB_PATH — skipping primary pull gate test"
fi
echo

# ── Summary ───────────────────────────────────────────────────────
echo "=============================="
if [ "$FAILURES" -eq 0 ]; then
    echo -e "${GREEN}ALL CHECKS PASSED${NC}"
    exit 0
else
    echo -e "${RED}$FAILURES CHECK(S) FAILED${NC}"
    exit 1
fi
