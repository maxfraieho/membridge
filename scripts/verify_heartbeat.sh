#!/bin/sh
# verify_heartbeat.sh — smoke test for auto-heartbeat + project registration
# Usage: MEMBRIDGE_ADMIN_KEY=<key> sh scripts/verify_heartbeat.sh
set -e

AGENT_URL="${MEMBRIDGE_AGENT_URL:-http://127.0.0.1:8001}"
SERVER_URL="${MEMBRIDGE_SERVER_URL:-http://127.0.0.1:8000}"
ADMIN_KEY="${MEMBRIDGE_ADMIN_KEY:-}"
TEST_PROJECT="${MEMBRIDGE_TEST_PROJECT:-verify-heartbeat-test}"
INTERVAL="${MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS:-10}"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { printf "${GREEN}✓${NC} %s\n" "$*"; }
fail() { printf "${RED}✗${NC} %s\n" "$*"; exit 1; }
info() { printf "${YELLOW}→${NC} %s\n" "$*"; }

# ── 1. Services reachable ─────────────────────────────────────────────────────
info "Checking agent on $AGENT_URL ..."
curl -fsS "$AGENT_URL/health" >/dev/null 2>&1 || fail "Agent not reachable at $AGENT_URL"
pass "Agent is up"

info "Checking server on $SERVER_URL ..."
curl -fsS "$SERVER_URL/health" >/dev/null 2>&1 || fail "Server not reachable at $SERVER_URL"
pass "Server is up"

# ── 2. Register a test project on the agent ───────────────────────────────────
info "Registering test project '$TEST_PROJECT' via /register_project ..."
REG=$(curl -fsS -X POST "$AGENT_URL/register_project" \
  -H "Content-Type: application/json" \
  -d "{\"project_id\":\"$TEST_PROJECT\",\"notes\":\"smoke-test\"}")
echo "$REG" | grep -q '"ok":true' || fail "register_project returned: $REG"
pass "register_project: $REG"

# ── 3. Verify agent local registry ───────────────────────────────────────────
info "Checking agent local projects list ..."
AGENT_PROJECTS=$(curl -fsS "$AGENT_URL/projects")
echo "$AGENT_PROJECTS" | grep -q "$TEST_PROJECT" || \
  fail "Test project not found in agent registry. Got: $AGENT_PROJECTS"
pass "Agent registry contains '$TEST_PROJECT'"

# ── 4. Wait for 2 heartbeat cycles ───────────────────────────────────────────
WAIT=$(( INTERVAL * 2 + 3 ))
info "Waiting ${WAIT}s for 2 heartbeat cycles (interval=${INTERVAL}s) ..."
sleep "$WAIT"

# ── 5. Check project appeared on server ──────────────────────────────────────
if [ -z "$ADMIN_KEY" ]; then
  printf "${YELLOW}⚠${NC}  MEMBRIDGE_ADMIN_KEY not set — skipping server-side check\n"
  printf "   Run: MEMBRIDGE_ADMIN_KEY=<key> sh %s\n" "$0"
else
  info "Checking server projects list ..."
  SERVER_PROJECTS=$(curl -fsS "$SERVER_URL/projects" \
    -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY")
  echo "$SERVER_PROJECTS" | grep -q "$TEST_PROJECT" || \
    fail "Test project not found on server. Got: $SERVER_PROJECTS"
  pass "Server shows '$TEST_PROJECT' (source=heartbeat)"
fi

# ── 6. Agent health shows heartbeat config ───────────────────────────────────
HEALTH=$(curl -fsS "$AGENT_URL/health")
echo "$HEALTH" | grep -q '"heartbeat_interval"' || fail "Agent health missing heartbeat_interval"
pass "Agent health: $(echo "$HEALTH" | tr ',' '\n' | grep -E 'heartbeat_interval|projects_count|server_url' | tr '\n' ' ')"

printf "\n${GREEN}All checks passed.${NC}\n"
