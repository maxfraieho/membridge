# Membridge v0.3.0

Distributed control plane for synchronizing [Claude AI](https://docs.anthropic.com/en/docs/claude-cli) memory databases across multiple machines using MinIO (S3-compatible) object storage.

Membridge replaces manual shell-script sync with a centralized API that coordinates push/pull operations across a fleet of machines — while preserving full backward compatibility with the legacy `claude-mem-minio` hook-based workflow.

## Architecture

Membridge uses a **control plane + agent** model:

- The **control plane** (server) runs on a central host (Replit, VPS, or any always-on machine). It manages projects, agents, and job history.
- An **agent daemon** runs on each machine that has a local Claude memory database. The agent executes sync commands when instructed by the control plane.
- **MinIO** is the shared storage backend. All machines push to and pull from the same bucket.
- The **legacy hook scripts** (`~/.claude-mem-minio/bin/*`) remain fully functional. Membridge does not replace them — it wraps the same sync engine (`sqlite_minio_sync.py`) and adds API-driven orchestration on top.

```
┌─────────────────────────┐     ┌─────────────────────────┐
│  Machine A (Raspberry Pi)│     │  Machine B (Orange Pi)  │
│                         │     │                         │
│  Claude CLI             │     │  Claude CLI             │
│  claude-mem plugin      │     │  claude-mem plugin      │
│  SQLite DB              │     │  SQLite DB              │
│  (~/.claude-mem/        │     │  (~/.claude-mem/        │
│   claude-mem.db)        │     │   claude-mem.db)        │
│                         │     │                         │
│  membridge-agent :8001  │     │  membridge-agent :8001  │
│  legacy hooks (intact)  │     │  legacy hooks (intact)  │
└────────────┬────────────┘     └────────────┬────────────┘
             │                               │
             │  HTTP (pull/push commands)     │
             │                               │
       ┌─────┴───────────────────────────────┴─────┐
       │       Control Plane (Replit or VPS)        │
       │                                           │
       │  membridge-server :8000                   │
       │  REST API                                 │
       │  Job history (SQLite)                     │
       │  Agent registry                           │
       └─────────────────┬─────────────────────────┘
                         │
                         │  S3 API (boto3)
                         │
                   ┌─────┴─────┐
                   │   MinIO   │
                   │  (bucket: │
                   │  claude-  │
                   │  memory)  │
                   └───────────┘
```

**Data flow:** The control plane does **not** touch memory databases or MinIO directly. It sends HTTP commands to agents, and agents execute `sqlite_minio_sync.py` locally. The control plane initiates all connections to agents — agents never call the control plane.

## Installation

### Prerequisites

- Python 3.10+
- [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) installed on each machine
- [claude-mem](https://github.com/thedotmack/claude-mem) plugin installed
- MinIO or S3-compatible endpoint with a bucket (default: `claude-memory`)
- MinIO credentials in `~/.claude-mem-minio/config.env`

### Install agent on a machine

Run this on each machine that has a local Claude memory database:

```bash
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- agent
```

This will:
- Clone the repository to `~/membridge`
- Create a Python virtual environment and install dependencies
- Generate `~/membridge/.env.agent` with placeholder values
- Install and enable the `membridge-agent` systemd service (port 8001)

This will **not** modify:
- `~/.claude-mem/` (memory database)
- `~/.claude/` (CLI config, credentials, auth tokens, settings)
- `~/.claude-mem-minio/config.env` (MinIO credentials)
- `~/.claude-mem-minio/bin/` (legacy hook scripts)

### Install server (control plane)

Run this on the machine that will serve as the control plane:

```bash
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- server
```

This will:
- Clone the repository to `~/membridge`
- Create a Python virtual environment and install dependencies
- Generate `~/membridge/.env.server` with placeholder values
- Install and enable the `membridge-server` systemd service (port 8000)

### Install both (single machine)

```bash
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- all
```

### Dry-run mode

Preview what the installer will do without making any changes:

```bash
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- --dry-run agent
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- --dry-run server
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- --dry-run migrate
```

### Migrate from legacy installation

Detect an existing `claude-mem-minio` installation and generate a migration report without modifying anything:

```bash
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- migrate
```

The report is saved to `~/membridge/migration-report.json` and includes:
- Legacy component detection (Claude CLI, claude-mem plugin, SQLite DB, MinIO config, hook scripts)
- Service status (agent, server)
- List of preserved paths
- Migration safety assessment

### Cleanup (stop services)

Stop membridge services and clean up orphan processes without deleting any data:

```bash
curl -fsSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s -- cleanup
```

This preserves all data at `~/.claude-mem/`, `~/.claude-mem-minio/config.env`, and `~/membridge/`.

## Configuration

### Agent configuration (`~/membridge/.env.agent`)

```env
MEMBRIDGE_AGENT_KEY=<generate-a-strong-random-key>
MEMBRIDGE_ALLOW_PROCESS_CONTROL=0
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `MEMBRIDGE_AGENT_KEY` | Yes | — | Auth key. Must match the `X-MEMBRIDGE-AGENT` header sent by the control plane. |
| `MEMBRIDGE_ALLOW_PROCESS_CONTROL` | No | `0` | When `0`, the agent will never kill processes (safe default). Set to `1` only if you need the agent to restart Claude workers after a pull. |

The agent reads MinIO credentials from `~/.claude-mem-minio/config.env` (the same file used by legacy hooks).

### Server configuration (`~/membridge/.env.server`)

```env
MEMBRIDGE_ADMIN_KEY=<generate-a-strong-random-key>
MEMBRIDGE_HOST=0.0.0.0
MEMBRIDGE_PORT=8000
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `MEMBRIDGE_ADMIN_KEY` | Yes | — | Auth key. Must be sent as `X-MEMBRIDGE-ADMIN` header on all API requests. |
| `MEMBRIDGE_HOST` | No | `0.0.0.0` | Listen address. |
| `MEMBRIDGE_PORT` | No | `8000` | Listen port. |

### Connection model

The control plane initiates all connections to agents. Agents do **not** auto-discover or connect back to the server.

When you register an agent, you provide its URL (e.g., `http://192.168.1.50:8001`). The control plane calls that URL when you trigger a sync operation.

This means:
- The server must be able to reach each agent over the network.
- Agents do not need to know the server's address.
- If agents are behind NAT, you need port forwarding or a VPN.

### MinIO configuration (`~/.claude-mem-minio/config.env`)

This file is shared between legacy hooks and the membridge agent:

```env
MINIO_ENDPOINT=https://your-minio-endpoint.example.com
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
MINIO_BUCKET=claude-memory
MINIO_REGION=us-east-1
CLAUDE_PROJECT_ID=mem
CLAUDE_MEM_DB=$HOME/.claude-mem/claude-mem.db
LOCK_TTL_SECONDS=7200
FORCE_PUSH=0
```

## Usage

All API examples assume the admin key is set in the header. Replace `<ADMIN_KEY>` with your actual key.

### Health check

```bash
# Server (no auth required)
curl http://server:8000/health

# Agent (no auth required)
curl http://machine:8001/health
```

### Register an agent

```bash
curl -X POST http://server:8000/agents \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>" \
  -d '{"name": "rpi4", "url": "http://192.168.1.50:8001"}'
```

### List agents

```bash
curl http://server:8000/agents \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>"
```

### Create a project

```bash
curl -X POST http://server:8000/projects \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>" \
  -d '{"name": "garden-seedling"}'
```

The response includes the `canonical_id` (first 16 hex chars of `sha256(project_name)`), which is the MinIO object key prefix used by the sync engine.

### Trigger sync

Pull the latest memory database from MinIO to a specific machine:

```bash
curl -X POST http://server:8000/sync/pull \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>" \
  -d '{"project": "garden-seedling", "agent": "rpi4"}'
```

Push the local memory database from a specific machine to MinIO:

```bash
curl -X POST http://server:8000/sync/push \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>" \
  -d '{"project": "garden-seedling", "agent": "rpi4"}'
```

### View job history

```bash
# List all jobs
curl http://server:8000/jobs \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>"

# Get specific job
curl http://server:8000/jobs/<JOB_ID> \
  -H "X-MEMBRIDGE-ADMIN: <ADMIN_KEY>"
```

### Direct agent commands

You can also talk to agents directly (useful for debugging). These endpoints require the `X-MEMBRIDGE-AGENT` header:

```bash
# Pull (alias endpoint)
curl -X POST http://machine:8001/pull \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-AGENT: <AGENT_KEY>" \
  -d '{"project": "garden-seedling"}'

# Push (alias endpoint)
curl -X POST http://machine:8001/push \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-AGENT: <AGENT_KEY>" \
  -d '{"project": "garden-seedling"}'

# Diagnostics
curl -X POST http://machine:8001/doctor \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-AGENT: <AGENT_KEY>" \
  -d '{"project": "garden-seedling"}'

# Status (GET)
curl "http://machine:8001/status?project=garden-seedling" \
  -H "X-MEMBRIDGE-AGENT: <AGENT_KEY>"
```

## Authentication

| Component | Header | Env Variable |
|---|---|---|
| Control Plane | `X-MEMBRIDGE-ADMIN` | `MEMBRIDGE_ADMIN_KEY` |
| Agent | `X-MEMBRIDGE-AGENT` | `MEMBRIDGE_AGENT_KEY` |

- `/health` endpoints are always public (no auth required).
- Set `MEMBRIDGE_DEV=1` to disable all authentication (development only).

## Migration Safety Guarantees

Membridge is designed to coexist safely with the legacy `claude-mem-minio` hook-based sync:

1. **`sqlite_minio_sync.py` is never modified.** Both legacy hooks and the membridge agent call the same sync engine. Backward compatibility is guaranteed at the script level.

2. **The memory database is never touched by the installer.** `~/.claude-mem/claude-mem.db` is only read/written by the sync engine during push/pull operations — never during installation or updates.

3. **Legacy hooks remain functional.** The files in `~/.claude-mem-minio/bin/` are never overwritten. Claude CLI hooks configured in `~/.claude/settings.json` continue to work as before.

4. **Authentication and config files are never modified.** `~/.claude/.credentials.json`, `~/.claude/auth.json`, `~/.claude/settings.local.json`, and `~/.claude-mem-minio/config.env` are all protected paths.

5. **The same canonical ID algorithm is used everywhere.** Both legacy hooks and the membridge agent compute `sha256(project_name)[:16]` — there is no ID mismatch between old and new systems.

6. **Process control is disabled by default.** The agent will not kill or restart any processes unless `MEMBRIDGE_ALLOW_PROCESS_CONTROL=1` is explicitly set.

For detailed migration steps, rollback procedures, and compatibility guarantees, see [MIGRATION.md](MIGRATION.md).

## Validate Installation

Run on any machine to check that all components are correctly installed:

```bash
cd ~/membridge
source .venv/bin/activate
python -m membridge.validate_install
```

The validator checks 6 items:

| Check | What it verifies |
|---|---|
| `claude_cli` | Claude CLI binary and `~/.claude/` config directory |
| `claude_mem_plugin` | claude-mem plugin presence |
| `sqlite_db` | Memory database exists and passes integrity check |
| `minio_config` | `config.env` exists with all required keys |
| `agent_running` | Agent daemon responds on port 8001 |
| `server_reachable` | Control plane responds on port 8000 |

Output includes both a human-readable summary and a JSON report. Exit code is `0` if all checks pass, `1` otherwise.

## Troubleshooting

### Agent not starting

```bash
systemctl status membridge-agent
journalctl -u membridge-agent -f
```

### Agent health check

```bash
curl http://localhost:8001/health
```

Expected response:

```json
{
  "status": "ok",
  "service": "membridge-agent",
  "version": "0.3.0",
  "hostname": "rpi4",
  "dryrun": false,
  "allow_process_control": false
}
```

### Server health check

```bash
curl http://localhost:8000/health
```

### Run diagnostics on a machine

```bash
curl -X POST http://localhost:8001/doctor \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-AGENT: <AGENT_KEY>" \
  -d '{"project": "garden-seedling"}'
```

### Common issues

| Symptom | Cause | Fix |
|---|---|---|
| Agent returns `401` | Missing or wrong `X-MEMBRIDGE-AGENT` header | Check `.env.agent` for `MEMBRIDGE_AGENT_KEY` |
| Server returns `401` | Missing or wrong `X-MEMBRIDGE-ADMIN` header | Check `.env.server` for `MEMBRIDGE_ADMIN_KEY` |
| Sync fails with "config.env not found" | MinIO config missing | Create `~/.claude-mem-minio/config.env` from `config.env.example` |
| Agent can't reach MinIO | Network or credentials issue | Run `python -m membridge.validate_install` and check `minio_config` |
| Push fails with lock error | Another machine holds the distributed lock | Wait for TTL (2 hours) or set `FORCE_PUSH=1` in config.env |

## Replit Deployment Notes

Membridge can use Replit as the control plane host. The dev server (`run.py`) mounts both the control plane and an agent (in dry-run mode) on a single port:

- Control plane endpoints: `https://your-app.replit.app/health`, `/projects`, `/agents`, etc.
- Agent endpoints (dev/dry-run): `https://your-app.replit.app/agent/health`, `/agent/pull`, etc.

To deploy the control plane on Replit:

1. Set `MEMBRIDGE_ADMIN_KEY` in the Replit Secrets tab.
2. The dev server starts automatically with `npm run dev` (which runs `run.py`).
3. Register your remote agents using their LAN or public IPs.
4. The Replit instance must be able to reach your agents over the network — if agents are on a private LAN, you need a tunnel or VPN.

In production, set `MEMBRIDGE_DEV=0` so that authentication is enforced on all endpoints except `/health`.

## Development

```bash
# Run in dev mode (auth disabled, agent dry-run)
make dev

# Run server only
make server

# Run agent only
make agent

# Run tests (36 tests)
make test

# Lint
make lint
```

## Legacy Sync Compatibility

The original `claude-mem-minio` hook-based sync continues to work unchanged alongside Membridge.

### Shell aliases

```bash
cm-push    # Push local DB to MinIO
cm-pull    # Pull DB from MinIO
cm-doctor  # Run diagnostics
cm-status  # Show project identity
```

### Claude CLI hooks

Hooks in `~/.claude/settings.json` (SessionStart, Stop) continue to fire the legacy scripts. Membridge does not interfere with or replace this workflow.

### Direct sync engine

```bash
source venv/bin/activate && set -a && source config.env && set +a
python sqlite_minio_sync.py push_sqlite
python sqlite_minio_sync.py pull_sqlite
python sqlite_minio_sync.py doctor
python sqlite_minio_sync.py print_project
```

### Multi-machine sync workflow (legacy)

1. Only one machine is active at a time.
2. Before switching — `cm-push` from the current machine.
3. On the new machine — `cm-pull` (or automatic via SessionStart hook).
4. Lock protects against concurrent push (TTL = 2 hours).
5. `FORCE_PUSH=1 cm-push` — emergency lock override.

### Compatibility layer

The `membridge/compat/` module provides Python wrappers around the same sync engine for use by the agent daemon:

```python
from membridge.compat.sync_wrapper import push_project, pull_project, doctor_project

result = push_project("garden-seedling", timeout=120)
result = pull_project("garden-seedling", timeout=120)
result = doctor_project("garden-seedling", timeout=30)
```

## MinIO Storage Structure

```
claude-memory/
  projects/
    6fe2e0f6071ac2bb/              # canonical_project_id = sha256("mem")[:16]
      sqlite/
        claude-mem.db              # SQLite snapshot
        claude-mem.db.sha256       # SHA256 checksum
        manifest.json              # metadata (host, timestamp, counts)
      locks/
        active.lock                # distributed lock
```

## Project Structure

```
server/main.py              Control plane API (FastAPI)
server/auth.py              Authentication middleware
server/jobs.py              Job history (SQLite)
server/logging_config.py    Structured JSON logging + request_id
agent/main.py               Agent daemon (FastAPI)
run.py                      Combined dev server
membridge/compat/           Legacy compatibility wrappers
membridge/validate_install.py  Installation validator CLI
sqlite_minio_sync.py        Core sync engine (never modified)
hooks/                      Claude CLI hook scripts
deploy/systemd/             Systemd service units
install.sh                  Linux installer (5 modes + --dry-run)
install.ps1                 Windows installer helper
tests/                      Test suite (36 tests)
config.env.example          MinIO config template
DEPLOYMENT.md               Full deployment guide
MIGRATION.md                Migration guide with rollback steps
```

## Full Deployment Guide

For complete step-by-step instructions to reproduce this environment on a new machine — including system prerequisites, Claude CLI installation, claude-mem plugin setup, MinIO sync configuration, hook integration, ARM performance optimization, multi-machine sync model, and recovery procedures — see:

**[DEPLOYMENT.md](DEPLOYMENT.md)**

## License

MIT
