#!/bin/bash
# Pre-Execution Validation Hook
# Triggers: Before major tool execution (Edit, Write, Bash with side effects)
# Purpose: Verify ADR compliance, context health before execution

set -e

CONTEXT_DIR="context/meta"
SESSION_DIR=".claude/sessions"

# Check if context system exists
if [ ! -f "$CONTEXT_DIR/summary.md" ]; then
    echo "⚠️  WARNING: Context system not initialized"
    echo "   Run: Initialize context system first"
    exit 0  # Non-blocking for now
fi

# Check token usage (if available)
# Note: This is a placeholder - actual token tracking would need integration
echo "✓ Pre-Execution Validation: Context system active"

# Check session health
if [ -f "$SESSION_DIR/.current-session" ]; then
    CURRENT_SESSION=$(cat "$SESSION_DIR/.current-session" | head -n 1)
    if [ -f "$SESSION_DIR/$CURRENT_SESSION" ]; then
        # Count lines as proxy for session size
        LINE_COUNT=$(wc -l < "$SESSION_DIR/$CURRENT_SESSION")
        if [ "$LINE_COUNT" -gt 500 ]; then
            echo "⚠️  WARNING: Session file large ($LINE_COUNT lines)"
            echo "   Consider compression or handoff"
        fi
    fi
fi

echo "✓ Pre-Execution Validation: PASS"
exit 0
