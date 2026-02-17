# Membridge Migration Guide

## Overview

This document describes how to safely migrate from the legacy `claude-mem-minio` hook-based sync system to the new Membridge Control Plane + Agent architecture.

**Critical principle: Safety over automation.** Production memory must never be lost or overwritten.

---

## Compatibility Guarantees

### What is NEVER modified during migration

| Path | Purpose | Guarantee |
|------|---------|-----------|
| `~/.claude-mem/` | Memory database (claude-mem.db) | Never touched |
| `~/.claude-mem/claude-mem.db` | SQLite memory database | Never modified or deleted |
| `~/.claude/.credentials.json` | Claude CLI auth | Never touched |
| `~/.claude/auth.json` | Claude auth tokens | Never touched |
| `~/.claude/settings.local.json` | Local CLI settings | Never touched |
| `~/.claude/settings.json` | User hooks config | Never modified by installer |
| `~/.claude-mem-minio/config.env` | MinIO credentials | Never modified |
| `~/.claude-mem-minio/bin/` | Legacy sync scripts | Never modified or removed |

### What coexists after migration

After installing the new Membridge agent, you will have **both** systems running:

1. **Legacy hooks** (`~/.claude-mem-minio/bin/claude-mem-push`, `claude-mem-pull`) continue to work unchanged
2. **New agent** (`membridge-agent` on port 8001) provides API-driven sync
3. **Both use the same** `sqlite_minio_sync.py` engine, the same MinIO bucket, and the same canonical ID algorithm

### Sync engine guarantees

The sync engine (`sqlite_minio_sync.py`) is **never modified** during migration:

- Canonical ID = `sha256(project_name)[:16]` (unchanged)
- MinIO object layout: `projects/{canonical_id}/sqlite/` (unchanged)
- Database format: unmodified SQLite (unchanged)
- Default paths: `~/.claude-mem/claude-mem.db` (unchanged)
- Lock format and TTL logic: unchanged

---

## Migration Steps

### Step 1: Run migration detection

```bash
# From any machine with the legacy installation
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s migrate
```

Or for a dry run first:

```bash
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- --dry-run migrate
```

This generates `~/membridge/migration-report.json` describing your legacy installation:
- Claude CLI presence
- claude-mem plugin status
- SQLite database size and table count
- MinIO config status
- Legacy hook locations

### Step 2: Install the agent alongside legacy hooks

```bash
# Install ONLY the agent — does NOT modify legacy files
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s agent
```

This:
- Clones the repo to `~/membridge`
- Creates a Python venv
- Generates `.env.agent`
- Installs systemd service (if available)
- Does **NOT** modify `~/.claude-mem/`, `~/.claude/`, or `~/.claude-mem-minio/`

### Step 3: Configure the agent

```bash
cd ~/membridge

# Set the agent key (from server's .env.server)
nano .env.agent
# Replace REPLACE_WITH_KEY_FROM_SERVER with actual key
```

### Step 4: Validate the installation

```bash
cd ~/membridge
source .venv/bin/activate
python -m membridge.validate_install
```

This checks:
1. Claude CLI installed
2. claude-mem plugin installed
3. SQLite DB exists and is healthy
4. MinIO config present
5. Agent running
6. Server reachable

### Step 5: Install the server (on one machine)

```bash
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s server
```

Then register your agents:

```bash
source ~/membridge/.env.server
curl -X POST http://localhost:8000/agents \
  -H "X-MEMBRIDGE-ADMIN: $MEMBRIDGE_ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"pi3b", "url":"http://192.168.1.50:8001"}'
```

---

## Process Control Safety

By default, the agent **never kills any processes**. The `MEMBRIDGE_ALLOW_PROCESS_CONTROL` flag is set to `0` by default.

| Flag | Behavior |
|------|----------|
| `MEMBRIDGE_ALLOW_PROCESS_CONTROL=0` (default) | Agent never kills worker processes |
| `MEMBRIDGE_ALLOW_PROCESS_CONTROL=1` | Agent may stop/start claude-mem workers during sync |

The sync engine itself (when called via legacy hooks directly) still manages workers as before. Only the agent API respects this flag.

---

## Rollback Steps

If anything goes wrong, you can fully roll back to legacy-only mode:

### Step 1: Stop Membridge services

```bash
# Using the cleanup mode (safe — preserves all data)
cd ~/membridge
bash install.sh cleanup
```

Or manually:

```bash
sudo systemctl stop membridge-agent
sudo systemctl stop membridge-server
sudo systemctl disable membridge-agent
sudo systemctl disable membridge-server
```

### Step 2: Verify legacy hooks still work

```bash
source ~/.claude-mem-minio/config.env
export CLAUDE_PROJECT_ID="your-project-name"
export CLAUDE_MEM_DB="$HOME/.claude-mem/claude-mem.db"

# Test with dry-run style
~/.claude-mem-minio/bin/claude-mem-doctor --project your-project-name
```

### Step 3: Remove systemd units (optional)

```bash
sudo rm /etc/systemd/system/membridge-server.service
sudo rm /etc/systemd/system/membridge-agent.service
sudo systemctl daemon-reload
```

### Step 4: Remove Membridge code (optional)

```bash
# Safe — does NOT touch ~/.claude-mem/ or ~/.claude-mem-minio/
rm -rf ~/membridge
```

**Your memory database, MinIO data, and Claude CLI settings are always preserved.**

---

## Architecture: Coexistence Model

```
                            ┌─────────────────────┐
                            │  MinIO Object Store  │
                            │  (S3-compatible)     │
                            └──────────┬──────────┘
                                       │
                    ┌──────────────────┼──────────────────┐
                    │                  │                   │
           ┌────────┴───────┐  ┌───────┴────────┐  ┌─────┴──────┐
           │ Legacy Hooks   │  │ Compat Layer   │  │ Direct API │
           │ claude-mem-push│  │ push_project() │  │ POST /push │
           │ claude-mem-pull│  │ pull_project() │  │ POST /pull │
           └────────┬───────┘  └───────┬────────┘  └─────┬──────┘
                    │                  │                   │
                    └──────────────────┼───────────────────┘
                                       │
                              ┌────────┴────────┐
                              │  Sync Engine    │
                              │  (unchanged)    │
                              │  sqlite_minio_  │
                              │  sync.py        │
                              └─────────────────┘
```

All three paths (legacy hooks, compat layer, agent API) use the same underlying sync engine. The canonical ID algorithm, MinIO layout, and database format are identical across all paths.

---

## FAQ

**Q: Will installing Membridge break my existing Claude CLI hooks?**
A: No. The installer never modifies `~/.claude/settings.json`. Your existing hooks continue to call the legacy scripts in `~/.claude-mem-minio/bin/`.

**Q: Can I use both legacy hooks and the new agent simultaneously?**
A: Yes. Both use the same sync engine and MinIO layout. Just ensure they don't run simultaneously on the same project (the distributed lock in MinIO prevents data corruption).

**Q: What happens if the agent crashes?**
A: The legacy hooks continue to work independently. The agent crashing has zero impact on legacy sync.

**Q: Does the installer need root access?**
A: Only for installing systemd services. Everything else runs as the current user. If systemd is unavailable, the installer prints instructions for running manually.

**Q: Will my memory database be modified during installation?**
A: No. The installer never reads, writes, or deletes `~/.claude-mem/claude-mem.db`.
