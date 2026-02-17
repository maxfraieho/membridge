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
- **Compat Layer** (`membridge/compat/`) — Wrapper functions for legacy hook coexistence
- **Validate** (`membridge/validate_install.py`) — Installation validation CLI
- **Sync Engine** (`sqlite_minio_sync.py`) — Core Python script for push/pull SQLite to MinIO (NEVER modified)
- **Hooks** (`hooks/`) — Bash scripts for Claude CLI lifecycle hooks (SessionStart, Stop)
- **Deploy** (`deploy/systemd/`) — Systemd service units for server and agent

### Running
- Dev mode: `make dev` (or `MEMBRIDGE_DEV=1 python -m uvicorn run:app --host 0.0.0.0 --port 5000 --reload`)
- Server only: `make server` (port 8000)
- Agent only: `make agent` (port 8001)
- Tests: `make test`
- Lint: `make lint`
- Validate: `python -m membridge.validate_install`

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
- `POST /sync/pull` — Execute pull (legacy path)
- `POST /sync/push` — Execute push (legacy path)
- `POST /pull` — Execute pull (alias)
- `POST /push` — Execute push (alias)
- `POST /doctor` — Run diagnostics (POST)
- `GET /doctor?project=...` — Run diagnostics (GET)

### Authentication
- Control Plane: `X-MEMBRIDGE-ADMIN` header == `MEMBRIDGE_ADMIN_KEY` env var
- Agent: `X-MEMBRIDGE-AGENT` header == `MEMBRIDGE_AGENT_KEY` env var
- `/health` endpoints are always public
- `MEMBRIDGE_DEV=1` disables auth entirely

### Key Concepts
- `canonical_id` = `sha256(CLAUDE_PROJECT_ID)[:16]` — always computed, never stored separately
- `MEMBRIDGE_AGENT_DRYRUN=1` — agent returns mock responses without executing real scripts
- `MEMBRIDGE_NO_RESTART_WORKER=1` — pull does not restart worker (safe default for hooks)
- `MEMBRIDGE_ALLOW_PROCESS_CONTROL=0` — agent never kills processes (safe default)
- All hooks support `--project <name>` parameter for multi-project usage
- Agent subprocess stdout/stderr limited to 200 lines in API responses

### Installation Modes
- `install.sh agent` — install agent only (does NOT modify legacy files)
- `install.sh server` — install server only
- `install.sh all` — install both
- `install.sh migrate` — detect legacy installation, generate migration-report.json
- `install.sh cleanup` — stop services safely (preserves all data)
- `install.sh --dry-run <mode>` — simulate without making changes

### Protected Paths (NEVER modified by installer)
- `~/.claude-mem/` — memory database
- `~/.claude/.credentials.json` — auth
- `~/.claude/auth.json` — auth tokens
- `~/.claude/settings.local.json` — local settings
- `~/.claude/settings.json` — user hooks
- `~/.claude-mem-minio/config.env` — MinIO credentials
- `~/.claude-mem-minio/bin/` — legacy sync scripts

### Project Structure
```
server/main.py            — FastAPI control plane
server/auth.py            — Authentication middleware
server/jobs.py            — Job history SQLite store
server/logging_config.py  — JSON logging + request_id
agent/main.py             — FastAPI agent daemon
run.py                    — Combined dev server (mounts both)
membridge/compat/         — Legacy compatibility layer
membridge/validate_install.py — Installation validator CLI
sqlite_minio_sync.py      — Core sync engine (NEVER modified)
hooks/                    — CLI hook scripts
deploy/systemd/           — Systemd service units
install.sh                — Linux installer (agent/server/migrate/cleanup + --dry-run)
install.ps1               — Windows installer helper
Makefile                  — dev/test/lint targets
tests/                    — pytest tests (36 tests)
config.env.example        — MinIO config template
validate-env.sh           — Environment validation
DEPLOYMENT.md             — Deployment documentation
MIGRATION.md              — Migration guide with rollback steps
```

## Recent Changes
- 2026-02-17: Migration-safe deployment: compat layer, validate-install, installer modes, MIGRATION.md
- 2026-02-17: Added membridge/compat/ with push_project, pull_project, doctor_project wrappers
- 2026-02-17: Added POST /pull, /push, /doctor agent aliases for project-aware execution
- 2026-02-17: Added MEMBRIDGE_ALLOW_PROCESS_CONTROL=0 safe default
- 2026-02-17: Added install.sh modes: migrate, cleanup, --dry-run
- 2026-02-17: Added membridge validate-install CLI (python -m membridge.validate_install)
- 2026-02-17: Updated systemd units with ExecReload and safe update logic
- 2026-02-17: Created MIGRATION.md with migration steps, rollback, compatibility guarantees
- 2026-02-17: Test suite expanded to 36 tests (compat, aliases, validation, combined endpoints)
- 2026-02-17: Version bumped to 0.3.0
