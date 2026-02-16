#!/bin/bash
# claude-session-cleanup.sh
# Runs on SessionEnd - cleans up background processes when no active sessions remain

LOG_FILE="/home/vokov/claude-cleanup.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') $1" >> "$LOG_FILE"
}

# Count active Claude sessions (processes with TTY, excluding this cleanup script's parent)
count_active_sessions() {
    # Look for 'claude' processes that have a real TTY (pts/*)
    # Exclude processes without TTY (daemon/background processes show ?)
    ps aux | grep -E '^[^ ]+ +[0-9]+ .* pts/[0-9]+ .* claude$' | wc -l
}

# Kill background Claude-related processes
cleanup_background_processes() {
    local killed=0

    # Kill chroma-mcp (vector database - biggest memory consumer)
    if pgrep -f "chroma-mcp" > /dev/null 2>&1; then
        pkill -f "chroma-mcp"
        log "Killed chroma-mcp processes"
        killed=$((killed + 1))
    fi

    # Kill orphaned MCP server processes (not attached to TTY)
    for pid in $(ps aux | grep "mcp-server.cjs" | grep -v pts/ | grep -v grep | awk '{print $2}'); do
        kill "$pid" 2>/dev/null && log "Killed orphaned mcp-server PID $pid"
        killed=$((killed + 1))
    done

    # Kill worker-service daemon (will restart on next session)
    if pgrep -f "worker-service.cjs.*--daemon" > /dev/null 2>&1; then
        pkill -f "worker-service.cjs.*--daemon"
        log "Killed worker-service daemon"
        killed=$((killed + 1))
    fi

    # Kill orphaned uv/uvx processes for chroma
    if pgrep -f "uvx.*chroma" > /dev/null 2>&1; then
        pkill -f "uvx.*chroma"
        log "Killed uvx chroma processes"
        killed=$((killed + 1))
    fi

    # Kill orphaned claude processes (background, no TTY) - with graceful shutdown
    sleep 3  # Give time for other processes to finish
    for pid in $(ps aux | awk '/claude/ && !/pts\// && !/grep/ {print $2}'); do
        # Send SIGTERM first for graceful shutdown
        kill -TERM "$pid" 2>/dev/null
        log "Sent SIGTERM to orphaned claude PID $pid"
        killed=$((killed + 1))
    done

    # Wait for graceful shutdown
    sleep 5

    # Force kill any remaining claude background processes
    for pid in $(ps aux | awk '/claude/ && !/pts\// && !/grep/ {print $2}'); do
        kill -KILL "$pid" 2>/dev/null && log "Force killed claude PID $pid"
    done

    echo "$killed"
}

# Main logic
main() {
    # Wait a moment for session to fully close
    sleep 2

    active=$(count_active_sessions)

    if [[ $active -le 1 ]]; then
        # This is the last session (or already closed)
        log "Last session closing, cleaning up background processes..."
        killed=$(cleanup_background_processes)
        log "Cleanup complete: killed $killed process groups"

        # Report memory after cleanup (LC_ALL=C for locale-independent parsing)
        mem_free=$(LC_ALL=C free -m | awk '/^Mem/ {print $7}')
        log "Available memory after cleanup: ${mem_free}MB"
    else
        log "Session ended but $active other sessions still active, skipping cleanup"
    fi
}

main
exit 0
