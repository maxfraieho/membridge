#!/usr/bin/env bash
set -euo pipefail

MEMBRIDGE_DIR="${MEMBRIDGE_DIR:-$HOME/membridge}"

if [[ ! -f "$MEMBRIDGE_DIR/config.env" ]]; then
  echo "ERROR: config.env not found at $MEMBRIDGE_DIR/config.env"
  echo "  Create it: cp $MEMBRIDGE_DIR/config.env.example $MEMBRIDGE_DIR/config.env"
  exit 1
fi

source "$MEMBRIDGE_DIR/config.env"

ERRORS=0

if [[ -z "${CLAUDE_PROJECT_ID:-}" ]]; then
  echo "ERROR: CLAUDE_PROJECT_ID not set in config.env"
  ERRORS=$((ERRORS + 1))
fi

if [[ -z "${MINIO_ENDPOINT:-}" ]]; then
  echo "ERROR: MINIO_ENDPOINT not set in config.env"
  ERRORS=$((ERRORS + 1))
fi

if [[ -z "${MINIO_ACCESS_KEY:-}" ]]; then
  echo "ERROR: MINIO_ACCESS_KEY not set in config.env"
  ERRORS=$((ERRORS + 1))
fi

if [[ -z "${MINIO_SECRET_KEY:-}" ]]; then
  echo "ERROR: MINIO_SECRET_KEY not set in config.env"
  ERRORS=$((ERRORS + 1))
fi

if [[ -z "${MINIO_BUCKET:-}" ]]; then
  echo "ERROR: MINIO_BUCKET not set in config.env"
  ERRORS=$((ERRORS + 1))
fi

if [[ $ERRORS -gt 0 ]]; then
  echo "Validation failed: $ERRORS error(s)"
  exit 1
fi

CANONICAL_ID=$(python3 -c "import hashlib; print(hashlib.sha256('${CLAUDE_PROJECT_ID}'.encode()).hexdigest()[:16])")
echo "Environment OK — project=$CLAUDE_PROJECT_ID canonical_id=$CANONICAL_ID"
