# Membridge

## Overview
Membridge is a distributed control plane for synchronizing Claude AI memory (claude-mem SQLite databases) across multiple machines using MinIO object storage.

## Architecture

### Components
- **Control Plane** (`server/main.py`) — FastAPI API for managing projects and agents
- **Agent Daemon** (`agent/main.py`) — FastAPI service running on each machine, executes sync commands
- **Auth** (`server/auth.py`) — Header-based authentication middleware (X-MEMBRIDGE-ADMIN / X-MEMBRIDGE-AGENT)
- **Jobs** (`server/jobs.py`) — Sync job history stored in SQLite (server/data/jobs.db)
- **Logging** (`server/logging_config.py`) — Structured JSON logging with request_id
- **Sync Engine** (`sqlite_minio_sync.py`) — Core Python script for push/pull SQLite to MinIO
- **Hooks** (`hooks/`) — Bash scripts for Claude CLI lifecycle hooks (SessionStart, Stop)
- **Deploy** (`deploy/systemd/`) — Systemd service units for server and agent

### Running
- Dev mode: `make dev` (or `MEMBRIDGE_DEV=1 python -m uvicorn run:app --host 0.0.0.0 --port 5000 --reload`)
- Server only: `make server` (port 8000)
- Agent only: `make agent` (port 8001)
- Tests: `make test`
- Lint: `make lint`

### API Endpoints

**Control Plane (port 8000):**
- `GET /health` — Service health (no auth)
- `GET /projects` / `POST /projects` — List/create projects
- `DELETE /projects/{name}` — Delete project
- `GET /agents` / `POST /agents` — List/register agents
- `DELETE /agents/{name}` — Unregister agent
- `POST /sync/pull` — Trigger pull via agent
- `POST /sync/push` — Trigger push via agent
- `GET /jobs` — List sync job history
- `GET /jobs/{id}` — Get job details

**Agent (port 8001):**
- `GET /health` — Agent health (no auth)
- `GET /status?project=...` — Project status
- `POST /sync/pull` — Execute pull
- `POST /sync/push` — Execute push
- `GET /doctor?project=...` — Run diagnostics

### Authentication
- Control Plane: `X-MEMBRIDGE-ADMIN` header == `MEMBRIDGE_ADMIN_KEY` env var
- Agent: `X-MEMBRIDGE-AGENT` header == `MEMBRIDGE_AGENT_KEY` env var
- `/health` endpoints are always public
- `MEMBRIDGE_DEV=1` disables auth entirely

### Key Concepts
- `canonical_id` = `sha256(CLAUDE_PROJECT_ID)[:16]` — always computed, never stored separately
- `MEMBRIDGE_AGENT_DRYRUN=1` — agent returns mock responses without executing real scripts
- `MEMBRIDGE_NO_RESTART_WORKER=1` — pull does not restart worker (safe default for hooks)
- All hooks support `--project <name>` parameter for multi-project usage
- Agent subprocess stdout/stderr limited to 200 lines in API responses

### Project Structure
```
server/main.py           — FastAPI control plane
server/auth.py           — Authentication middleware
server/jobs.py           — Job history SQLite store
server/logging_config.py — JSON logging + request_id
agent/main.py            — FastAPI agent daemon
run.py                   — Combined dev server (mounts both)
sqlite_minio_sync.py     — Core sync engine
hooks/                   — CLI hook scripts
deploy/systemd/          — Systemd service units
install.sh               — Linux installer (curl | bash)
install.ps1              — Windows installer helper
Makefile                 — dev/test/lint targets
tests/                   — pytest tests
config.env.example       — MinIO config template
validate-env.sh          — Environment validation
DEPLOYMENT.md            — Full deployment documentation
```

## Recent Changes
- 2026-02-17: Release-ready: auth, logging, jobs, install scripts, systemd, tests, docs
- 2026-02-17: Added header-based auth (X-MEMBRIDGE-ADMIN / X-MEMBRIDGE-AGENT)
- 2026-02-17: Added structured JSON logging with request_id middleware
- 2026-02-17: Added job history (SQLite) with GET /jobs and GET /jobs/{id}
- 2026-02-17: Added install.sh (Linux), install.ps1 (Windows), systemd units
- 2026-02-17: Added Makefile with dev/lint/test targets and 18 pytest tests
- 2026-02-17: Agent subprocess output limited to 200 lines, passes --project flag
- 2026-02-17: Updated DEPLOYMENT.md with full documentation
