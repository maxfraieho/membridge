#!/usr/bin/env bash
set -euo pipefail

source /home/vokov/membridge/config.env

EXPECTED_PROJECT="garden-seedling"
EXPECTED_CANON="6fe2e0f6071ac2bb"

if [[ "$CLAUDE_PROJECT_ID" != "$EXPECTED_PROJECT" ]]; then
  echo "Invalid project_id: $CLAUDE_PROJECT_ID"
  exit 1
fi

if [[ "$CLAUDE_CANONICAL_PROJECT_ID" != "$EXPECTED_CANON" ]]; then
  echo "Invalid canonical_project_id: $CLAUDE_CANONICAL_PROJECT_ID"
  exit 2
fi

echo "Environment OK"
