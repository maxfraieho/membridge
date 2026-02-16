#!/bin/bash
# ============================================================================
# Claude CLI Optimization Profile for Orange Pi PC2
# Source: Audited from Raspberry Pi 4B (Armbian, 897MB RAM)
# Target: Orange Pi PC2 (with Docker — must not interfere)
#
# Usage:
#   sudo bash optimization-profile-orange.sh apply    # Apply optimizations
#   sudo bash optimization-profile-orange.sh status   # Check current values
#   sudo bash optimization-profile-orange.sh revert   # Revert to defaults
#
# SAFE: Does NOT touch Docker processes, containers, or Docker networking.
# ============================================================================

set -euo pipefail

SCRIPT_NAME="$(basename "$0")"
LOG_FILE="/var/log/claude-optimization.log"

log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') [$SCRIPT_NAME] $1" | tee -a "$LOG_FILE"
}

# ============================================================================
# SECTION 1: Sysctl Memory Tuning
# ============================================================================
# Source values from RPi4 /etc/sysctl.conf:
#   vm.swappiness=10           (default: 60) — reduce swap eagerness, keep Claude in RAM
#   vm.vfs_cache_pressure=100  (default: 100) — balanced inode/dentry cache reclaim
#   vm.dirty_background_ratio=5 (default: 10) — flush dirty pages sooner in background
#   vm.dirty_ratio=10          (default: 20) — limit dirty pages before forced writeback
#   fs.file-max=500000         (default: ~varies) — allow many open files for MCP servers
#   net.core.somaxconn=1024    (default: 4096 on modern kernels) — connection backlog

SYSCTL_CONF="/etc/sysctl.d/90-claude-optimization.conf"

apply_sysctl() {
    log "Applying sysctl memory tuning..."

    cat > "$SYSCTL_CONF" <<'EOF'
# Claude CLI Memory Optimization for Orange Pi
# Applied by optimization-profile-orange.sh

# Reduce swap eagerness — keep Node.js/Bun processes in RAM
vm.swappiness = 10

# Balanced VFS cache reclaim
vm.vfs_cache_pressure = 100

# Flush dirty pages sooner (reduce IO spikes on SD/eMMC)
vm.dirty_background_ratio = 5
vm.dirty_ratio = 10

# Allow many open files (MCP servers, claude-mem workers)
fs.file-max = 500000

# Connection backlog for MCP server sockets
net.core.somaxconn = 1024
EOF

    sysctl --system > /dev/null 2>&1
    log "Sysctl values applied from $SYSCTL_CONF"
}

revert_sysctl() {
    log "Reverting sysctl tuning..."
    rm -f "$SYSCTL_CONF"
    sysctl --system > /dev/null 2>&1
    log "Sysctl reverted (removed $SYSCTL_CONF)"
}

status_sysctl() {
    echo "=== Sysctl Memory Tuning ==="
    for key in vm.swappiness vm.vfs_cache_pressure vm.dirty_background_ratio vm.dirty_ratio fs.file-max net.core.somaxconn; do
        val=$(cat /proc/sys/$(echo "$key" | tr '.' '/') 2>/dev/null || echo "N/A")
        echo "  $key = $val"
    done
    echo "  Config file: $([ -f "$SYSCTL_CONF" ] && echo "EXISTS" || echo "NOT APPLIED")"
}

# ============================================================================
# SECTION 2: Zram Configuration
# ============================================================================
# Source RPi4 config (/etc/default/zramswap):
#   PERCENT=75, ALGO=lzo-rle, PRIORITY=100
#   Actual devices: zram0 (673MB swap, pri 100), zram2 (449MB, pri 5)
#   Plus 2GB swapfile at priority -2 as fallback
#
# For Orange Pi: Configure armbian-zram-config if present,
# otherwise create zram manually.

ZRAM_CONF="/etc/default/zramswap"
ZRAM_ARMBIAN_CONF="/etc/default/armbian-zram-config"

apply_zram() {
    log "Configuring zram..."

    # Check if armbian-zram-config exists (Armbian systems)
    if [ -f "$ZRAM_ARMBIAN_CONF" ]; then
        # Backup original
        [ ! -f "${ZRAM_ARMBIAN_CONF}.bak" ] && cp "$ZRAM_ARMBIAN_CONF" "${ZRAM_ARMBIAN_CONF}.bak"
        log "Armbian zram config found, enabling with ENABLED=true"
        sed -i 's/^ENABLED=.*/ENABLED=true/' "$ZRAM_ARMBIAN_CONF" 2>/dev/null || \
            echo "ENABLED=true" >> "$ZRAM_ARMBIAN_CONF"
    fi

    # Create/update zramswap config
    if [ -f "$ZRAM_CONF" ] || [ ! -f "$ZRAM_ARMBIAN_CONF" ]; then
        [ -f "$ZRAM_CONF" ] && [ ! -f "${ZRAM_CONF}.bak" ] && cp "$ZRAM_CONF" "${ZRAM_CONF}.bak"
        cat > "$ZRAM_CONF" <<'EOF'
# Zram configuration for Claude CLI optimization
# Algorithm: lzo-rle (fast compression, good for ARM)
# 75% of RAM allocated to zram swap
ENABLED=true
PERCENT=75
ALGO=lzo-rle
PRIORITY=100
EOF
        log "Zram config written to $ZRAM_CONF"
    fi

    # Also ensure a swapfile exists as fallback (low priority)
    if [ ! -f /swapfile ]; then
        log "Creating 2GB swapfile as fallback..."
        fallocate -l 2G /swapfile 2>/dev/null || dd if=/dev/zero of=/swapfile bs=1M count=2048 status=progress
        chmod 600 /swapfile
        mkswap /swapfile
        swapon -p -2 /swapfile
        # Add to fstab if not present
        grep -q '/swapfile' /etc/fstab || echo '/swapfile none swap sw,pri=-2 0 0' >> /etc/fstab
        log "Swapfile created and activated"
    else
        log "Swapfile already exists"
    fi

    log "Zram configuration complete. Restart armbian-zram-config or reboot to apply."
}

revert_zram() {
    log "Reverting zram configuration..."
    for conf in "$ZRAM_CONF" "$ZRAM_ARMBIAN_CONF"; do
        if [ -f "${conf}.bak" ]; then
            mv "${conf}.bak" "$conf"
            log "Restored $conf from backup"
        fi
    done
}

status_zram() {
    echo "=== Zram Status ==="
    if command -v zramctl &>/dev/null; then
        zramctl 2>/dev/null || echo "  No zram devices active"
    else
        echo "  zramctl not found, checking /proc/swaps:"
        grep zram /proc/swaps 2>/dev/null || echo "  No zram in swaps"
    fi
    echo "  Swap overview:"
    cat /proc/swaps
}

# ============================================================================
# SECTION 3: Node.js Memory Limit
# ============================================================================
# Source RPi4: NODE_OPTIONS="--max-old-space-size=512" in ~/.bashrc
# This limits Node.js heap to 512MB, preventing OOM on low-RAM systems.
# Claude CLI is a Node.js app — this is critical.

BASHRC_MARKER="# claude-optimization: NODE_OPTIONS"

apply_node_limit() {
    local target_user="${SUDO_USER:-$(whoami)}"
    local target_bashrc="/home/$target_user/.bashrc"

    if [ ! -f "$target_bashrc" ]; then
        log "WARNING: $target_bashrc not found, skipping NODE_OPTIONS"
        return
    fi

    if grep -q "$BASHRC_MARKER" "$target_bashrc"; then
        log "NODE_OPTIONS already configured in $target_bashrc"
        return
    fi

    # Don't duplicate if already set manually
    if grep -q 'NODE_OPTIONS.*max-old-space-size' "$target_bashrc"; then
        log "NODE_OPTIONS already present (manual config) in $target_bashrc"
        return
    fi

    cat >> "$target_bashrc" <<EOF

$BASHRC_MARKER
export NODE_OPTIONS="--max-old-space-size=512"
EOF
    log "Added NODE_OPTIONS to $target_bashrc"
}

revert_node_limit() {
    local target_user="${SUDO_USER:-$(whoami)}"
    local target_bashrc="/home/$target_user/.bashrc"

    if grep -q "$BASHRC_MARKER" "$target_bashrc"; then
        # Remove the marker line and the export line after it
        sed -i "/$BASHRC_MARKER/,+1d" "$target_bashrc"
        # Remove blank line left behind
        sed -i '/^$/N;/^\n$/d' "$target_bashrc"
        log "Removed NODE_OPTIONS from $target_bashrc"
    fi
}

status_node_limit() {
    echo "=== Node.js Memory Limit ==="
    echo "  NODE_OPTIONS=${NODE_OPTIONS:-NOT SET}"
    local target_user="${SUDO_USER:-$(whoami)}"
    grep -q 'max-old-space-size' "/home/$target_user/.bashrc" 2>/dev/null && \
        echo "  Configured in ~/.bashrc: YES" || echo "  Configured in ~/.bashrc: NO"
}

# ============================================================================
# SECTION 4: Transparent Hugepages
# ============================================================================
# Source RPi4: always [madvise] never — THP set to "madvise"
# madvise = only use hugepages when app explicitly requests them.
# Good for Node.js — avoids THP overhead for small allocations.

apply_thp() {
    log "Setting THP to madvise..."
    echo madvise > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || \
        log "WARNING: Could not set THP (may not be supported)"

    # Make persistent via systemd tmpfiles
    mkdir -p /etc/tmpfiles.d
    echo 'w /sys/kernel/mm/transparent_hugepage/enabled - - - - madvise' > /etc/tmpfiles.d/claude-thp.conf
    log "THP set to madvise (persistent via tmpfiles.d)"
}

revert_thp() {
    rm -f /etc/tmpfiles.d/claude-thp.conf
    echo always > /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || true
    log "THP reverted to always"
}

status_thp() {
    echo "=== Transparent Hugepages ==="
    echo "  Current: $(cat /sys/kernel/mm/transparent_hugepage/enabled 2>/dev/null || echo 'N/A')"
}

# ============================================================================
# SECTION 5: Open Files Limit
# ============================================================================
# Source RPi4: ulimit -n = 1048576 (very high, likely from systemd default)
# Ensure Claude user has sufficient open files limit.

apply_limits() {
    local target_user="${SUDO_USER:-$(whoami)}"
    local limits_file="/etc/security/limits.d/90-claude.conf"

    cat > "$limits_file" <<EOF
# Claude CLI file descriptor limits
$target_user soft nofile 65536
$target_user hard nofile 131072
EOF
    log "File limits configured in $limits_file"
}

revert_limits() {
    rm -f /etc/security/limits.d/90-claude.conf
    log "Removed Claude file limits"
}

status_limits() {
    echo "=== File Limits ==="
    echo "  Current soft: $(ulimit -Sn)"
    echo "  Current hard: $(ulimit -Hn)"
    [ -f /etc/security/limits.d/90-claude.conf ] && echo "  Config: EXISTS" || echo "  Config: NOT APPLIED"
}

# ============================================================================
# MAIN
# ============================================================================

usage() {
    echo "Usage: sudo $SCRIPT_NAME {apply|status|revert}"
    echo ""
    echo "  apply   - Apply all Claude CLI optimizations"
    echo "  status  - Show current optimization status"
    echo "  revert  - Revert all optimizations to defaults"
    echo ""
    echo "SAFE: Does not affect Docker processes or containers."
}

case "${1:-}" in
    apply)
        log "========== APPLYING OPTIMIZATIONS =========="
        apply_sysctl
        apply_zram
        apply_node_limit
        apply_thp
        apply_limits
        log "========== ALL OPTIMIZATIONS APPLIED =========="
        echo ""
        echo "Done. Reboot recommended to fully activate zram changes."
        echo "Run '$SCRIPT_NAME status' to verify."
        ;;
    status)
        echo "============================================"
        echo "  CLAUDE CLI OPTIMIZATION STATUS"
        echo "============================================"
        echo ""
        status_sysctl
        echo ""
        status_zram
        echo ""
        status_node_limit
        echo ""
        status_thp
        echo ""
        status_limits
        echo ""
        ;;
    revert)
        log "========== REVERTING OPTIMIZATIONS =========="
        revert_sysctl
        revert_zram
        revert_node_limit
        revert_thp
        revert_limits
        log "========== OPTIMIZATIONS REVERTED =========="
        echo "Done. Reboot recommended."
        ;;
    *)
        usage
        exit 1
        ;;
esac
