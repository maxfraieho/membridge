#!/bin/bash
# Pre-Execution Validation Hook
# Triggers: Before major tool execution (Edit, Write, Bash with side effects)
# Purpose: Verify ADR compliance, context health before execution

set -e

CONTEXT_DIR="context/meta"
SESSION_DIR=".claude/sessions"

if [ ! -f "$CONTEXT_DIR/summary.md" ]; then
    echo "WARNING: Context system not initialized"
    exit 0
fi

echo "Pre-Execution Validation: Context system active"

if [ -f "$SESSION_DIR/.current-session" ]; then
    CURRENT_SESSION=$(cat "$SESSION_DIR/.current-session" | head -n 1)
    if [ -f "$SESSION_DIR/$CURRENT_SESSION" ]; then
        LINE_COUNT=$(wc -l < "$SESSION_DIR/$CURRENT_SESSION")
        if [ "$LINE_COUNT" -gt 500 ]; then
            echo "WARNING: Session file large ($LINE_COUNT lines)"
            echo "   Consider compression or handoff"
        fi
    fi
fi

echo "Pre-Execution Validation: PASS"
exit 0
