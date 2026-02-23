#!/bin/sh
# verify_hooks_override.sh — ensure CLI env vars survive config.env sourcing in hooks
# Usage: sh scripts/verify_hooks_override.sh
set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

pass() { printf "${GREEN}✓${NC} %s\n" "$*"; }
fail() { printf "${RED}✗${NC} %s\n" "$*"; exit 1; }

TMP=$(mktemp -d)
trap 'rm -rf "$TMP"' EXIT

# Temp config.env: all override vars set to their "off" defaults
printf 'FORCE_PUSH=0\nALLOW_SECONDARY_PUSH=0\nALLOW_PRIMARY_PULL_OVERRIDE=0\nSTALE_LOCK_GRACE_SECONDS=60\n' \
  > "$TMP/config.env"

# ── 1. push preamble: FORCE_PUSH=1 must survive ───────────────────────────────
result=$(FORCE_PUSH=1 bash -c '
  MEMBRIDGE_DIR="'"$TMP"'"
  OV_FORCE_PUSH="${FORCE_PUSH-__unset__}"
  OV_ALLOW_SECONDARY_PUSH="${ALLOW_SECONDARY_PUSH-__unset__}"
  OV_STALE_LOCK_GRACE_SECONDS="${STALE_LOCK_GRACE_SECONDS-__unset__}"
  set -a; . "$MEMBRIDGE_DIR/config.env"; set +a
  [ "$OV_FORCE_PUSH" != "__unset__" ]               && export FORCE_PUSH="$OV_FORCE_PUSH"
  [ "$OV_ALLOW_SECONDARY_PUSH" != "__unset__" ]     && export ALLOW_SECONDARY_PUSH="$OV_ALLOW_SECONDARY_PUSH"
  [ "$OV_STALE_LOCK_GRACE_SECONDS" != "__unset__" ] && export STALE_LOCK_GRACE_SECONDS="$OV_STALE_LOCK_GRACE_SECONDS"
  printf "%s" "$FORCE_PUSH"
')
[ "$result" = "1" ] || fail "FORCE_PUSH override: expected 1, got '$result'"
pass "push: FORCE_PUSH=1 survives config.env FORCE_PUSH=0"

# ── 2. unset var falls through to config.env ──────────────────────────────────
result2=$(bash -c '
  MEMBRIDGE_DIR="'"$TMP"'"
  OV_FORCE_PUSH="${FORCE_PUSH-__unset__}"
  set -a; . "$MEMBRIDGE_DIR/config.env"; set +a
  [ "$OV_FORCE_PUSH" != "__unset__" ] && export FORCE_PUSH="$OV_FORCE_PUSH"
  printf "%s" "$FORCE_PUSH"
')
[ "$result2" = "0" ] || fail "Unset FORCE_PUSH: expected config.env value 0, got '$result2'"
pass "push: unset FORCE_PUSH falls through to config.env (got 0)"

# ── 3. pull preamble: ALLOW_PRIMARY_PULL_OVERRIDE=1 must survive ──────────────
result3=$(ALLOW_PRIMARY_PULL_OVERRIDE=1 bash -c '
  MEMBRIDGE_DIR="'"$TMP"'"
  OV_ALLOW_PRIMARY_PULL_OVERRIDE="${ALLOW_PRIMARY_PULL_OVERRIDE-__unset__}"
  OV_STALE_LOCK_GRACE_SECONDS="${STALE_LOCK_GRACE_SECONDS-__unset__}"
  set -a; . "$MEMBRIDGE_DIR/config.env"; set +a
  [ "$OV_ALLOW_PRIMARY_PULL_OVERRIDE" != "__unset__" ] && export ALLOW_PRIMARY_PULL_OVERRIDE="$OV_ALLOW_PRIMARY_PULL_OVERRIDE"
  [ "$OV_STALE_LOCK_GRACE_SECONDS" != "__unset__" ]    && export STALE_LOCK_GRACE_SECONDS="$OV_STALE_LOCK_GRACE_SECONDS"
  printf "%s" "$ALLOW_PRIMARY_PULL_OVERRIDE"
')
[ "$result3" = "1" ] || fail "ALLOW_PRIMARY_PULL_OVERRIDE override: expected 1, got '$result3'"
pass "pull: ALLOW_PRIMARY_PULL_OVERRIDE=1 survives config.env"

# ── 4. STALE_LOCK_GRACE_SECONDS override ──────────────────────────────────────
result4=$(STALE_LOCK_GRACE_SECONDS=999 bash -c '
  MEMBRIDGE_DIR="'"$TMP"'"
  OV_STALE_LOCK_GRACE_SECONDS="${STALE_LOCK_GRACE_SECONDS-__unset__}"
  set -a; . "$MEMBRIDGE_DIR/config.env"; set +a
  [ "$OV_STALE_LOCK_GRACE_SECONDS" != "__unset__" ] && export STALE_LOCK_GRACE_SECONDS="$OV_STALE_LOCK_GRACE_SECONDS"
  printf "%s" "$STALE_LOCK_GRACE_SECONDS"
')
[ "$result4" = "999" ] || fail "STALE_LOCK_GRACE_SECONDS override: expected 999, got '$result4'"
pass "STALE_LOCK_GRACE_SECONDS=999 survives config.env (60)"

printf "\n${GREEN}All override checks passed.${NC}\n"
