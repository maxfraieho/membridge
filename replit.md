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

### BLOOM Runtime (TypeScript/React layer)
- **Shared Types** (`shared/schema.ts`) — Drizzle pgTable definitions + TypeScript interfaces for WorkerNode, Lease, LLMTask, LLMResult, RuntimeArtifact, RuntimeConfig, AuditLogEntry + Zod validation schemas
- **Database** (`server/db.ts`) — Drizzle ORM + @neondatabase/serverless PostgreSQL connection
- **Storage** (`server/storage.ts`) — DatabaseStorage (PostgreSQL) implementing IStorage for workers, tasks, leases, artifacts, results, audit logs, runtime config
- **Routes** (`server/routes.ts`) — Express `/api/runtime/*` + `/api/membridge/*` endpoints with auth middleware, worker sync, hardened Membridge proxy client
- **Auth** (`server/middleware/runtimeAuth.ts`) — X-Runtime-API-Key header middleware with constant-time comparison
- **Worker Sync** (`server/runtime/workerSync.ts`) — Auto-sync workers from Membridge /agents every 10s
- **Membridge Client** (`server/runtime/membridgeClient.ts`) — Hardened HTTP client with retry, exponential backoff, timeout, connection tracking
- **Frontend — Runtime** (`client/src/pages/RuntimeSettings.tsx`) — Runtime Settings UI with Membridge Proxy tab, Task Queue, Overview stats
- **Frontend — Membridge** (`client/src/pages/MembridgePage.tsx`) — Control Plane UI: project list, leadership card, nodes table, promote primary
- **Navigation** (`client/src/App.tsx`) — Top nav bar with Runtime / Membridge tabs

### BLOOM Runtime API Endpoints (Express, port 5000)
- `GET /api/runtime/health` — Service health (storage type, uptime, membridge state)
- `GET /api/runtime/config` — Get Membridge proxy config
- `POST /api/runtime/config` — Save proxy config (URL + admin key)
- `POST /api/runtime/test-connection` — Test Membridge /health connectivity
- `GET /api/runtime/workers` — Workers from PostgreSQL (synced from Membridge /agents)
- `GET /api/runtime/workers/:id` — Worker detail with active leases
- `POST /api/runtime/llm-tasks` — Create LLM task
- `GET /api/runtime/llm-tasks` — List tasks (optional ?status= filter)
- `GET /api/runtime/llm-tasks/:id` — Task detail
- `POST /api/runtime/llm-tasks/:id/lease` — Assign task to worker (capability-based routing)
- `POST /api/runtime/llm-tasks/:id/heartbeat` — Renew lease heartbeat
- `POST /api/runtime/llm-tasks/:id/complete` — Submit result + create artifact
- `POST /api/runtime/llm-tasks/:id/requeue` — Requeue failed/dead task
- `GET /api/runtime/leases` — List leases (optional ?status= filter)
- `GET /api/runtime/runs` — Recent task executions
- `GET /api/runtime/artifacts` — Artifacts (optional ?task_id= filter)
- `GET /api/runtime/audit` — Audit log (optional ?limit=)
- `GET /api/runtime/stats` — Dashboard stats (tasks/leases/workers counts)

### Membridge Control Plane Proxy Endpoints (Express, port 5000)
- `GET /api/membridge/health` — Proxy to Membridge /health
- `GET /api/membridge/projects` — List all projects
- `GET /api/membridge/projects/:cid/leadership` — Get leadership lease for project
- `GET /api/membridge/projects/:cid/nodes` — List nodes for project
- `POST /api/membridge/projects/:cid/leadership/select` — Promote node to primary

### Authentication
- Runtime API: `X-Runtime-API-Key` header == `RUNTIME_API_KEY` env var (optional — disabled if not set)
- Membridge proxy: same auth as runtime API, admin key injected by backend via membridgeFetch()
- Unprotected: `/api/runtime/health`, `/api/runtime/test-connection`
- Constant-time comparison via `crypto.timingSafeEqual`

### Key BLOOM Invariants
- Two memory layers NEVER mix: `claude-mem.db` (Membridge→MinIO, session) and `DiffMem/git` (agent reasoning, Proposal/Apply only)
- Workers return results/proposals only — never write directly to canonical storage
- Lease TTL default 300s; stale leases expire and requeue tasks (max 3 attempts → dead)
- Worker routing: healthiest online with free slots + sticky by context_id
- All state persisted to PostgreSQL — survives restart

### Documentation
- `docs/architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md` — Canonical runtime integration spec
- `docs/runtime/operations/RUNTIME_BACKEND_IMPLEMENTATION_STATE.md` — Backend hardening implementation state
- `docs/audit/` — Documentation audit package (rebranding, term matrix, gap analysis)
- `docs/ІНДЕКС.md` — Master documentation index

## Recent Changes
- 2026-02-25: Integrated Membridge Control Plane UI into frontend: /api/membridge/* proxy routes, MembridgePage (projects, leadership, nodes, promote primary), top nav bar
- 2026-02-25: Documentation overhaul: all runtime docs translated to Ukrainian, user guide (ПОСІБНИК_КОРИСТУВАЧА), deployment guide (НАЛАШТУВАННЯ_ТА_РОЗГОРТАННЯ), GAP-7 marked RESOLVED, ІНДЕКС.md updated with new reading routes and guides
- 2026-02-25: Updated REPLIT_MEMBRIDGE_UI_INTEGRATION.md with IMPLEMENTED status
- 2026-02-25: Backend hardening: PostgreSQL persistence (DatabaseStorage), auth middleware, worker auto-sync, hardened membridge client
- 2026-02-25: Added Drizzle pgTable definitions for all runtime entities (llm_tasks, leases, workers, runtime_artifacts, llm_results, audit_logs, runtime_settings)
- 2026-02-25: Added /api/runtime/health endpoint with storage type, uptime, membridge connection state
- 2026-02-25: Added server/middleware/runtimeAuth.ts with X-Runtime-API-Key constant-time auth
- 2026-02-25: Added server/runtime/workerSync.ts — auto-sync workers from membridge every 10s
- 2026-02-25: Added server/runtime/membridgeClient.ts — retry (3x), exponential backoff (500ms×2^n), timeout (10s), connection tracking
- 2026-02-25: Created docs/runtime/operations/RUNTIME_BACKEND_IMPLEMENTATION_STATE.md
- 2026-02-25: BLOOM Runtime integration: shared types, storage, API routes, RuntimeSettings UI, canonical docs
- 2026-02-25: Added /api/runtime/* endpoints with Membridge HTTP proxy, leasing, failover
- 2026-02-25: Created RuntimeSettings page with Proxy, Task Queue, and Overview tabs
- 2026-02-25: Created INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md canonical spec
- 2026-02-25: Created docs/audit/ package (rebranding audit, term matrix, gap analysis)
- 2026-02-25: Created docs/ІНДЕКС.md master index
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
