# Membridge

## Overview
Membridge is a distributed control plane for synchronizing Claude AI memory (claude-mem SQLite databases) across multiple machines using MinIO object storage.

## Architecture

### Components
- **Control Plane** (`server/main.py`) — FastAPI API for managing projects and agents, port 5000
- **Agent Daemon** (`agent/main.py`) — FastAPI service running on each machine, executes sync commands
- **Sync Engine** (`sqlite_minio_sync.py`) — Core Python script for push/pull SQLite ↔ MinIO
- **Hooks** (`hooks/`) — Bash scripts for Claude CLI lifecycle hooks (SessionStart, Stop)
- **Bootstrap** (`scripts/`) — Deployment scripts for Linux, Alpine, Windows WSL2
- **Config Payload** (`claude-home/`) — Claude CLI configuration (skills, hooks, commands) — NOT runtime

### Running
- Dev mode: `MEMBRIDGE_AGENT_DRYRUN=1 python -m uvicorn run:app --host 0.0.0.0 --port 5000 --reload`
- Control Plane only: `python -m uvicorn server.main:app --host 0.0.0.0 --port 5000`
- Agent only: `MEMBRIDGE_AGENT_DRYRUN=1 python -m uvicorn agent.main:app --host 0.0.0.0 --port 8011`

### API Endpoints

**Control Plane (server/main.py):**
- `GET /health` — Service health
- `GET /projects` / `POST /projects` — List/create projects
- `DELETE /projects/{name}` — Delete project
- `GET /agents` / `POST /agents` — List/register agents
- `DELETE /agents/{name}` — Unregister agent
- `POST /sync/pull` — Trigger pull via agent
- `POST /sync/push` — Trigger push via agent

**Agent (agent/main.py):**
- `GET /health` — Agent health + dry-run status
- `GET /status?project=...` — Project status on this machine
- `POST /sync/pull` — Execute pull (subprocess)
- `POST /sync/push` — Execute push (subprocess)
- `GET /doctor?project=...` — Run diagnostics

### Key Concepts
- `canonical_id` = `sha256(CLAUDE_PROJECT_ID)[:16]` — always computed, never stored separately
- `MEMBRIDGE_AGENT_DRYRUN=1` — agent returns mock responses without executing real scripts
- `MEMBRIDGE_NO_RESTART_WORKER=1` — pull does not restart worker (safe default for hooks)
- All hooks support `--project <name>` parameter for multi-project usage

### Project Structure
```
server/main.py          — FastAPI control plane
agent/main.py           — FastAPI agent daemon
run.py                  — Combined dev server (mounts both)
sqlite_minio_sync.py    — Core sync engine
hooks/                  — CLI hook scripts
scripts/                — Bootstrap/deployment scripts
claude-home/            — Claude CLI config payload
config.env.example      — MinIO config template
validate-env.sh         — Environment validation
```

## Recent Changes
- 2026-02-17: Added Control Plane (server/) and Agent (agent/) FastAPI services
- 2026-02-17: Removed CLAUDE_CANONICAL_PROJECT_ID concept — canonical_id always computed from project name
- 2026-02-17: Fixed pull to not restart worker by default (MEMBRIDGE_NO_RESTART_WORKER=1)
- 2026-02-17: Added --project flag to all hook scripts
- 2026-02-17: Rewrote validate-env.sh to be portable (no hardcoded paths/values)
