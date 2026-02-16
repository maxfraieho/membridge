#!/bin/bash
# Context Drift Detection Hook
# Triggers: Periodically (every N actions)
# Purpose: Detect context degradation signals

set -e

SESSION_DIR=".claude/sessions"
CONTEXT_DIR="context/meta"

# Check if current session exists
if [ ! -f "$SESSION_DIR/.current-session" ]; then
    echo "No active session"
    exit 0
fi

CURRENT_SESSION=$(cat "$SESSION_DIR/.current-session" | head -n 1)
SESSION_FILE="$SESSION_DIR/$CURRENT_SESSION"

if [ ! -f "$SESSION_FILE" ]; then
    echo "WARNING: Session file not found: $CURRENT_SESSION"
    exit 0
fi

# Calculate session age (days since creation)
if [[ "$OSTYPE" == "darwin"* ]]; then
    FILE_AGE_DAYS=$(( ( $(date +%s) - $(stat -f%B "$SESSION_FILE") ) / 86400 ))
else
    FILE_AGE_DAYS=$(( ( $(date +%s) - $(stat -c%Y "$SESSION_FILE") ) / 86400 ))
fi

# Warning thresholds
if [ "$FILE_AGE_DAYS" -gt 5 ]; then
    echo "CRITICAL: Session age > 5 days ($FILE_AGE_DAYS days)"
    echo "   Mandatory handoff recommended"
elif [ "$FILE_AGE_DAYS" -gt 3 ]; then
    echo "WARNING: Session age > 3 days ($FILE_AGE_DAYS days)"
    echo "   Consider compression or handoff"
else
    echo "Context Health: Session age OK ($FILE_AGE_DAYS days)"
fi

# Check file size
FILE_SIZE=$(wc -l < "$SESSION_FILE")
if [ "$FILE_SIZE" -gt 1000 ]; then
    echo "WARNING: Session file very large ($FILE_SIZE lines)"
elif [ "$FILE_SIZE" -gt 500 ]; then
    echo "INFO: Session file growing ($FILE_SIZE lines)"
fi

exit 0
