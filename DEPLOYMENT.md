# Membridge Deployment Guide

Complete guide for reproducing the Claude CLI + claude-mem + membridge sync environment on a new machine.

**Source of truth:** Raspberry Pi 3B (`~/membridge` repo, `origin/main`).

---

## Table of Contents

1. [System Prerequisites](#1-system-prerequisites)
2. [Install Claude CLI](#2-install-claude-cli)
3. [Install claude-mem Plugin](#3-install-claude-mem-plugin)
4. [Clone membridge](#4-clone-membridge)
5. [Deploy Claude Global Config](#5-deploy-claude-global-config)
6. [Setup MinIO Sync](#6-setup-minio-sync)
7. [Hook Integration](#7-hook-integration)
8. [Performance Optimization (Linux ARM / Low RAM)](#8-performance-optimization-linux-arm--low-ram)
9. [Validation](#9-validation)
10. [Multi-Machine Sync Model](#10-multi-machine-sync-model)
11. [Recovery](#11-recovery)
12. [Updating Environment](#12-updating-environment)
13. [Troubleshooting](#13-troubleshooting)

---

## 1. System Prerequisites

### Supported Platforms

| Architecture | OS | Status |
|---|---|---|
| ARM64 | Armbian, Raspberry Pi OS, Ubuntu 22.04+ | Primary targets |
| x86_64 | Ubuntu 22.04+, Debian 12+ | Supported |
| x86_64 | Alpine Linux | Supported (see bootstrap-alpine.sh) |
| ARM64/x86_64 | macOS 13+ | Supported |
| x86_64 | Windows 10+ WSL2 | Supported |

### Required Packages

#### Debian / Ubuntu / Armbian

```bash
sudo apt update
sudo apt install -y git curl python3 python3-venv nodejs npm
```

#### Alpine Linux

```bash
sudo apk add git curl python3 py3-pip nodejs npm bash
```

#### macOS (Homebrew)

```bash
brew install git curl python3 node npm
```

#### Windows WSL2 (Ubuntu)

```bash
sudo apt update
sudo apt install -y git curl python3 python3-venv nodejs npm
```

### Optional Packages

```bash
# rsync — used by some sync scripts (not strictly required, cp works as fallback)
sudo apt install -y rsync

# Docker — if running containerized services
sudo apt install -y docker.io docker-compose
sudo usermod -aG docker $USER

# zram — compressed swap for low-RAM ARM devices (applied via optimization script)
sudo apt install -y zram-tools
```

### Verify Prerequisites

```bash
git --version        # >= 2.30
curl --version       # any
python3 --version    # >= 3.8
node --version       # >= 18
npm --version        # any
```

---

## 2. Install Claude CLI

### Official Install

```bash
npm install -g @anthropic-ai/claude-code
```

Or via Bun (faster on ARM):

```bash
curl -fsSL https://bun.sh/install | bash
source ~/.bashrc
bun install -g @anthropic-ai/claude-code
```

### Verify

```bash
claude --version
```

### Authenticate

```bash
claude
# Follow the interactive auth flow — this creates ~/.claude/.credentials.json
```

### Verify Directory Created

```bash
ls -la ~/.claude/
# Should contain: .credentials.json, settings.json (possibly empty)
```

> **Note:** Authentication is per-machine and NEVER synced between machines.

---

## 3. Install claude-mem Plugin

### Install from Marketplace

```bash
claude plugin install thedotmack/claude-mem
```

### Verify Plugin Installed

```bash
# Check plugin files exist
ls ~/.claude/plugins/cache/thedotmack/claude-mem/
```

### Verify Worker Starts

Launch Claude CLI and check that claude-mem MCP server starts:

```bash
claude
# Inside session, the claude-mem tools should be available
# Exit and verify:
ls ~/.claude-mem/
```

### Verify Database Created

```bash
ls -la ~/.claude-mem/claude-mem.db
# Should exist after first session with claude-mem active
```

If the DB does not exist yet, it will be created on first claude-mem usage or pulled from MinIO (step 6).

---

## 4. Clone membridge

```bash
git clone git@github.com:maxfraieho/membridge.git ~/membridge
cd ~/membridge
git pull --ff-only
```

### Verify Structure

```bash
ls ~/membridge/
```

Expected:

```
claude-home/                  # Claude CLI global config (source of truth)
  CLAUDE.md                   # Global agent instructions
  skills/                     # Skill definitions (30+ skills)
  skills-local/               # Local/custom skills
  skills-installer/           # Skill installation tooling
  hooks/                      # Hook scripts (UserPromptSubmit, cleanup, etc.)
  commands/                   # Custom slash commands (session-*)
  plugins/                    # Plugin metadata (NOT cache)
hooks/                        # membridge MinIO sync hooks
scripts/
  bootstrap-linux.sh          # Linux/Alpine/Debian deployment (full stack)
  bootstrap-alpine.sh         # Alpine prereqs + delegates to bootstrap-linux.sh
  bootstrap-windows.ps1       # Windows WSL2 deployment
  claude-cleanup-safe         # Docker-safe process cleanup
sqlite_minio_sync.py          # Core MinIO sync engine
optimization-profile-orange.sh # ARM performance tuning
config.env.example            # MinIO config template
```

---

## 5. Deploy Claude Global Config

This step copies safe configuration files from the repo into `~/.claude/`.

### What Gets Synced

| Item | Source | Target |
|---|---|---|
| Global CLAUDE.md | `claude-home/CLAUDE.md` | `~/.claude/CLAUDE.md` |
| Skills | `claude-home/skills/` | `~/.claude/skills/` |
| Local skills | `claude-home/skills-local/` | `~/.claude/skills-local/` |
| Skills installer | `claude-home/skills-installer/` | `~/.claude/skills-installer/` |
| Hooks | `claude-home/hooks/` | `~/.claude/hooks/` |
| Commands | `claude-home/commands/` | `~/.claude/commands/` |
| Plugin metadata | `claude-home/plugins/*.json` | `~/.claude/plugins/*.json` |
| Plugin CLAUDE.md | `claude-home/plugins/CLAUDE.md` | `~/.claude/plugins/CLAUDE.md` |

### What Is NEVER Synced (and Why)

| Item | Reason |
|---|---|
| `.credentials.json` | Contains auth tokens — machine-specific, created during `claude` auth flow |
| `auth.json`, `*token*`, `*credential*` | Authentication secrets — must stay local |
| `plugins/cache/` | Downloaded plugin binaries — architecture-specific, auto-downloaded |
| `cache/` | Runtime cache — ephemeral, machine-specific |
| `history.jsonl` | Conversation history — personal, machine-specific |
| `session-env/` | Active session state — ephemeral |
| `file-history/` | File access tracking — machine-specific |
| `statsig/`, `stats-cache.json` | Telemetry/analytics — machine-specific |
| `projects/` | Per-project config — machine-specific paths |
| `debug/` | Debug logs — ephemeral |

### Automated Deployment (Recommended)

The bootstrap scripts deploy everything from `claude-home/` (single source of truth) plus set up MinIO sync (venv, boto3, hook scripts, config.env).

#### Linux (Raspberry Pi / Orange Pi / Ubuntu / Debian)

```bash
cd ~/membridge && git pull && bash scripts/bootstrap-linux.sh
```

#### Alpine Linux

```bash
cd ~/membridge && git pull && bash scripts/bootstrap-alpine.sh
```

Installs Alpine packages (`bash`, `coreutils`, `git`, `curl`, `python3`, `py3-pip`, `py3-virtualenv`, `nodejs`, `npm`), verifies bash is available (Alpine uses ash by default), then delegates to `bootstrap-linux.sh`.

#### Windows 10+ (via WSL2)

```powershell
cd ~\membridge; git pull
powershell -ExecutionPolicy Bypass -File scripts\bootstrap-windows.ps1
```

Requires WSL2 with a Linux distro. The script:
1. Clones/updates membridge inside WSL2
2. Runs `bootstrap-linux.sh` inside WSL2 (MinIO sync)
3. Deploys config to Windows-native `%USERPROFILE%\.claude\` (CLAUDE.md, skills, commands, hooks)
4. Creates `bin\cm-push.cmd`, `cm-pull.cmd`, `cm-doctor.cmd`, `cm-status.cmd` convenience scripts

### Manual Deployment

If bootstrap scripts don't cover your case:

```bash
# 1. Backup current safe config
TS="$(date +%Y%m%d-%H%M%S)"
BK="$HOME/.claude/backup/membridge-sync-$TS"
mkdir -p "$BK"
for p in CLAUDE.md skills skills-local skills-installer hooks commands plans plugins; do
  [ -e "$HOME/.claude/$p" ] && cp -a "$HOME/.claude/$p" "$BK/" 2>/dev/null || true
done

# 2. Deploy root CLAUDE.md
cp ~/membridge/claude-home/CLAUDE.md ~/.claude/CLAUDE.md

# 3. Deploy directories
for d in skills skills-local skills-installer hooks commands; do
  if [ -d ~/membridge/claude-home/$d ]; then
    rm -rf ~/.claude/$d
    cp -a ~/membridge/claude-home/$d ~/.claude/$d
  fi
done

# 4. Deploy plugins metadata only (NOT cache)
mkdir -p ~/.claude/plugins
for f in installed_plugins.json known_marketplaces.json CLAUDE.md; do
  [ -f ~/membridge/claude-home/plugins/$f ] && \
    cp ~/membridge/claude-home/plugins/$f ~/.claude/plugins/$f
done

# 5. Ensure no cache leaked
rm -rf ~/.claude/plugins/cache ~/.claude/cache 2>/dev/null || true

# 6. Fix hook permissions
chmod -R u+rwX,go-rwx ~/.claude/hooks 2>/dev/null || true
find ~/.claude/hooks -type f -name "*.sh" -exec chmod +x {} \; 2>/dev/null || true
```

### Verify Deployment

```bash
test -f ~/.claude/CLAUDE.md && echo "OK: global CLAUDE.md" || echo "MISSING"
test -d ~/.claude/skills && echo "OK: skills dir" || echo "MISSING"
test -d ~/.claude/hooks && echo "OK: hooks dir" || echo "MISSING"
test -d ~/.claude/commands && echo "OK: commands dir" || echo "MISSING"
test -f ~/.claude/plugins/installed_plugins.json && echo "OK: plugins metadata" || echo "MISSING"

# Verify auth untouched
test -f ~/.claude/.credentials.json && echo "OK: auth still present" || echo "WARNING: auth file missing"
```

---

## 6. Setup MinIO Sync

MinIO provides S3-compatible object storage for syncing the claude-mem SQLite database between machines.

### Create Runtime Directories

```bash
mkdir -p ~/.claude-mem-minio/bin ~/.claude-mem-backups
```

### Configure MinIO Credentials

```bash
cp ~/membridge/config.env.example ~/.claude-mem-minio/config.env
```

Edit `~/.claude-mem-minio/config.env` with your actual credentials:

```bash
nano ~/.claude-mem-minio/config.env
```

#### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `MINIO_ENDPOINT` | MinIO/S3 endpoint URL | `https://minio.example.com` |
| `MINIO_ACCESS_KEY` | Access key ID | (your key) |
| `MINIO_SECRET_KEY` | Secret access key | (your secret) |
| `MINIO_BUCKET` | Bucket name | `claude-memory` |
| `MINIO_REGION` | AWS region | `us-east-1` |
| `CLAUDE_PROJECT_ID` | Project identifier (MUST be identical on all machines) | `mem` |
| `CLAUDE_MEM_DB` | Path to local SQLite DB | `$HOME/.claude-mem/claude-mem.db` |
| `LOCK_TTL_SECONDS` | Distributed lock TTL | `7200` |
| `FORCE_PUSH` | Override lock (emergency only) | `0` |

> **Critical:** `CLAUDE_PROJECT_ID` must be the same value (`mem`) on every machine. This determines the canonical path in MinIO.

### Create Symlink (Repo Convenience)

```bash
ln -sf ~/.claude-mem-minio/config.env ~/membridge/config.env
```

### Install Python Dependencies

```bash
cd ~/membridge
python3 -m venv venv
source venv/bin/activate
pip install boto3
```

### Install Hook Scripts

```bash
cp ~/membridge/hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*
```

### Verify Setup

```bash
~/.claude-mem-minio/bin/claude-mem-doctor
```

Expected output: connection to MinIO succeeds, DB path resolved, project ID matches.

### Shell Aliases (Optional)

Add to `~/.bashrc` or `~/.zshrc`:

```bash
# membridge aliases
alias cm-push="~/.claude-mem-minio/bin/claude-mem-push"
alias cm-pull="~/.claude-mem-minio/bin/claude-mem-pull"
alias cm-status="~/.claude-mem-minio/bin/claude-mem-status"
alias cm-doctor="~/.claude-mem-minio/bin/claude-mem-doctor"
```

### Initial Sync

```bash
# If another machine already has the DB in MinIO:
cm-pull

# If this is the first machine (DB exists locally only):
cm-push
```

---

## 7. Hook Integration

### Lifecycle

Claude CLI fires hooks at specific lifecycle events. Membridge uses two:

```
Session Start                           Session Stop
     │                                       │
     ▼                                       ▼
 SessionStart hook                       Stop hook
     │                                       │
     ▼                                       ▼
 claude-mem-hook-pull                claude-mem-hook-push
     │                                       │
     ▼                                       ▼
 Pull DB from MinIO                  Push DB to MinIO
 Verify SHA256                       VACUUM + SHA256
 Atomic replace local DB             Upload + manifest
 Restart worker if needed            Cleanup orphan processes
```

### How Hooks Are Configured

The hooks are configured in `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude-mem-minio/bin/claude-mem-hook-pull"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "$HOME/.claude-mem-minio/bin/claude-mem-hook-push"
          }
        ]
      }
    ]
  }
}
```

### Fail-Open Design

Both hooks use `exit 0` regardless of success/failure. This means:

- If MinIO is unreachable, the session still starts/stops normally
- Errors are logged to `~/.claude-mem-minio/hook.log`
- The user is never blocked by sync failures

### Verify Hooks Work

```bash
# Check settings.json is valid
python3 -c "import json; json.load(open('$HOME/.claude/settings.json')); print('OK')"

# Manual test pull
~/.claude-mem-minio/bin/claude-mem-hook-pull
cat ~/.claude-mem-minio/hook.log | tail -5

# Manual test push
~/.claude-mem-minio/bin/claude-mem-hook-push
cat ~/.claude-mem-minio/hook.log | tail -5
```

### Additional Hooks (from claude-home)

The `~/.claude/hooks/` directory also contains:

| Hook | Purpose |
|---|---|
| `UserPromptSubmit` | Runs on each user prompt submission |
| `claude-session-cleanup.sh` | Cleans up session state |
| `context-drift-detection.sh` | Detects context window degradation |
| `pre-execution-validation.sh` | Validates before tool execution |
| `post-execution-verification.sh` | Verifies after tool execution |
| `unified-skill-hook.sh` | Skill loading/routing |

---

## 8. Performance Optimization (Linux ARM / Low RAM)

For ARM devices with <= 2GB RAM (Raspberry Pi 3B/4B, Orange Pi PC2).

### Apply Optimizations

```bash
sudo bash ~/membridge/optimization-profile-orange.sh apply
```

### What It Does

#### sysctl Tuning

| Parameter | Value | Purpose |
|---|---|---|
| `vm.swappiness` | 10 | Reduce swap eagerness, keep Claude in RAM |
| `vm.vfs_cache_pressure` | 100 | Balanced inode/dentry cache reclaim |
| `vm.dirty_background_ratio` | 5 | Flush dirty pages sooner |
| `vm.dirty_ratio` | 10 | Limit dirty pages before forced writeback |
| `fs.file-max` | 500000 | Allow many open files for MCP servers |

#### zram (Compressed Swap)

Creates compressed swap in RAM. On 1GB devices, effectively doubles usable memory for compressible data (Node.js heap, Python objects).

#### NODE_OPTIONS

Sets `--max-old-space-size` to limit Node.js heap, preventing OOM kills on low-RAM devices.

### Check Status

```bash
sudo bash ~/membridge/optimization-profile-orange.sh status
```

### Revert

```bash
sudo bash ~/membridge/optimization-profile-orange.sh revert
```

### Docker-Safe Process Cleanup

For cleaning up orphan Claude/MCP/Bun processes without touching Docker:

```bash
# Dry run (show what would be killed)
~/membridge/scripts/claude-cleanup-safe

# Actually kill orphans
~/membridge/scripts/claude-cleanup-safe --kill

# Force kill (SIGTERM + SIGKILL fallback)
~/membridge/scripts/claude-cleanup-safe --force
```

This script explicitly preserves: `dockerd`, `containerd`, `docker-proxy`, and any Docker-related node processes.

---

## 9. Validation

Run these checks after completing deployment:

### 1. Claude CLI Starts

```bash
claude --version
```

### 2. Skills Load

```bash
# Start Claude and verify skills are listed
claude
# Type: /help — should show custom commands (session-start, session-end, etc.)
```

### 3. Hooks Run

```bash
# Check hook log after starting a session
cat ~/.claude-mem-minio/hook.log | tail -10
```

### 4. Memory Sync Works

```bash
cm-doctor
cm-status
```

### 5. Global CLAUDE.md Active

```bash
# Inside a Claude session, the agent should follow the "Working with Q" protocol
# Verify by observing DOING/EXPECT/RESULT format in responses
```

### 6. Canonical Project ID Matches

```bash
# Must output the same ID on all machines
source ~/membridge/venv/bin/activate
set -a && source ~/.claude-mem-minio/config.env && set +a
python3 ~/membridge/sqlite_minio_sync.py print_project
```

The canonical project ID is derived from `sha256("mem")[:16]` = `6fe2e0f6071ac2bb`.

---

## 10. Multi-Machine Sync Model

### Architecture

```
┌─────────────────┐
│   MinIO (S3)    │  ← Single source of truth for claude-mem DB
│  claude-memory/ │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌────────┐ ┌────────┐
│ RPi 3B │ │OPi PC2 │  ← Mirrors (only one active at a time)
│(source)│ │(mirror)│
└────────┘ └────────┘
```

**Raspberry Pi 3B** is the source of truth for:
- `~/membridge` git repository (canonical config)
- MinIO server (hosts the S3-compatible storage)

**Other machines** are mirrors that:
- Clone `~/membridge` from GitHub
- Pull/push claude-mem DB via MinIO

### Safe Workflow

```
Machine A (finishing work):
  1. Session ends → Stop hook fires → cm-push (automatic)
  2. DB uploaded to MinIO with SHA256 + manifest

Machine B (starting work):
  1. git pull ~/membridge (get latest config)
  2. Session starts → SessionStart hook fires → cm-pull (automatic)
  3. DB downloaded from MinIO, verified, atomically replaced
```

### Rules

1. **Only one machine active at a time** — concurrent writes are not supported
2. Before switching machines: ensure the previous session ended (push completed)
3. `CLAUDE_PROJECT_ID=mem` must be identical on all machines
4. Lock system prevents concurrent pushes (TTL = 2 hours)
5. Emergency override: `FORCE_PUSH=1 cm-push`

### Lock System

MinIO-based distributed lock prevents concurrent writes:

```
claude-memory/projects/6fe2e0f6071ac2bb/locks/active.lock
```

- Lock is acquired on push, released after upload
- TTL = 2 hours (auto-expires if machine crashes)
- Same-host can re-acquire its own lock
- `FORCE_PUSH=1` overrides any lock (use with caution)

---

## 11. Recovery

### Restore from Backup

Automatic backups are created before each sync:

```bash
# List available backups
ls ~/.claude/backup/
ls ~/.claude-mem-backups/

# Restore Claude config from backup
cp -a ~/.claude/backup/<timestamp>/CLAUDE.md ~/.claude/CLAUDE.md
cp -a ~/.claude/backup/<timestamp>/skills/ ~/.claude/skills/
# etc.

# Restore claude-mem DB from backup
cp ~/.claude-mem-backups/<backup-file>.db ~/.claude-mem/claude-mem.db
```

### Restore from membridge Repo

If `~/.claude` is damaged, rebuild from repo:

```bash
cd ~/membridge && git pull

# Re-deploy all safe config
bash scripts/bootstrap-linux.sh

# Re-deploy claude-home content
for d in skills skills-local skills-installer hooks commands; do
  rm -rf ~/.claude/$d
  cp -a ~/membridge/claude-home/$d ~/.claude/$d
done
cp ~/membridge/claude-home/CLAUDE.md ~/.claude/CLAUDE.md
```

### Restore from MinIO (claude-mem DB)

```bash
cm-pull
# This downloads the latest DB from MinIO and replaces local copy
```

### Full Rebuild of ~/.claude

If `~/.claude` is completely lost:

```bash
# 1. Re-authenticate (creates ~/.claude/ and .credentials.json)
claude

# 2. Re-install claude-mem plugin
claude plugin install thedotmack/claude-mem

# 3. Deploy config from membridge
cd ~/membridge && bash scripts/bootstrap-linux.sh

# 4. Deploy claude-home content
cp ~/membridge/claude-home/CLAUDE.md ~/.claude/CLAUDE.md
for d in skills skills-local skills-installer hooks commands; do
  [ -d ~/membridge/claude-home/$d ] && cp -a ~/membridge/claude-home/$d ~/.claude/$d
done
mkdir -p ~/.claude/plugins
for f in installed_plugins.json known_marketplaces.json CLAUDE.md; do
  [ -f ~/membridge/claude-home/plugins/$f ] && cp ~/membridge/claude-home/plugins/$f ~/.claude/plugins/$f
done

# 5. Pull DB from MinIO
cm-pull

# 6. Verify
cm-doctor
```

---

## 12. Updating Environment

When the source of truth (RPi) pushes new config to `origin/main`:

```bash
# 1. Pull latest repo
cd ~/membridge
git fetch origin
git pull --ff-only

# 2. Re-deploy Claude global config
cp ~/membridge/claude-home/CLAUDE.md ~/.claude/CLAUDE.md

for d in skills skills-local skills-installer hooks commands; do
  if [ -d ~/membridge/claude-home/$d ]; then
    rm -rf ~/.claude/$d
    cp -a ~/membridge/claude-home/$d ~/.claude/$d
  fi
done

for f in installed_plugins.json known_marketplaces.json CLAUDE.md; do
  [ -f ~/membridge/claude-home/plugins/$f ] && \
    cp ~/membridge/claude-home/plugins/$f ~/.claude/plugins/$f
done

# 3. Update hook scripts
cp ~/membridge/hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*

# 4. Update Python dependencies
source ~/membridge/venv/bin/activate
pip install --upgrade boto3

# 5. Restart Claude CLI session
# Exit current session and start a new one
```

**Do NOT overwrite during update:** `~/.claude-mem-minio/config.env`, `~/.claude-mem/claude-mem.db`, `~/.claude/.credentials.json`, `~/.claude/settings.json` (if locally customized).

---

## 13. Troubleshooting

### Lock Active — Cannot Push

```
LOCK ACTIVE — held by orangepi for 1234s
```

Wait for TTL to expire, or force override:

```bash
FORCE_PUSH=1 cm-push
```

### canonical_id Mismatch

Ensure `CLAUDE_PROJECT_ID=mem` is identical in `config.env` on all machines. The canonical ID `6fe2e0f6071ac2bb` = `sha256("mem")[:16]`.

### Worker Locking DB

The sync script automatically stops/restarts the claude-mem worker. If issues persist:

```bash
# Find and kill worker
cat ~/.claude-mem/worker.pid | python3 -c "import sys,json; print(json.load(sys.stdin)['pid'])" | xargs kill
```

### MinIO Auth Errors

```bash
# Verify config
cat ~/.claude-mem-minio/config.env  # check credentials (don't share!)

# Test connectivity
cm-doctor
```

### rsync Not Installed

Not all systems have rsync. Use `cp -a` as fallback (the manual deployment steps above use `cp`).

### settings.json Invalid

```bash
python3 -c "import json; json.load(open('$HOME/.claude/settings.json')); print('OK')"
# If this fails, restore from backup or re-run bootstrap:
# bash ~/membridge/scripts/bootstrap-linux.sh
```

### Skills Not Loading

```bash
# Verify skills directory exists and has content
ls ~/.claude/skills/ | head -5

# Verify permissions
ls -la ~/.claude/skills/
```

### Hooks Not Firing

```bash
# Check settings.json has hooks configured
python3 -c "
import json
s = json.load(open('$HOME/.claude/settings.json'))
print('SessionStart hooks:', 'SessionStart' in s.get('hooks', {}))
print('Stop hooks:', 'Stop' in s.get('hooks', {}))
"

# Check hook log
tail -20 ~/.claude-mem-minio/hook.log
```

### OOM on ARM Devices

```bash
# Apply performance optimizations
sudo bash ~/membridge/optimization-profile-orange.sh apply

# Check memory
free -h

# Clean up orphan processes
~/membridge/scripts/claude-cleanup-safe --kill
```

---

## Quick Reference

| Task | Command |
|---|---|
| Full deploy (Linux) | `cd ~/membridge && git pull && bash scripts/bootstrap-linux.sh` |
| Sync config from repo | See [Section 5](#5-deploy-claude-global-config) manual steps |
| Push DB to MinIO | `cm-push` |
| Pull DB from MinIO | `cm-pull` |
| Diagnostics | `cm-doctor` |
| Status | `cm-status` |
| Apply ARM optimizations | `sudo bash ~/membridge/optimization-profile-orange.sh apply` |
| Cleanup orphan processes | `~/membridge/scripts/claude-cleanup-safe --kill` |
| Update from repo | See [Section 12](#12-updating-environment) |

---

*Generated from membridge repo — source of truth: Raspberry Pi 3B, `origin/main`.*
