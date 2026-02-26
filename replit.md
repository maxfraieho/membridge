# Membridge

## Overview
Membridge is a distributed control plane designed to synchronize Claude AI memory (claude-mem SQLite databases) across multiple machines using MinIO object storage. Its primary purpose is to provide a robust, scalable, and distributed solution for managing AI memory, ensuring data consistency and availability across a fleet of agents. The project aims to enhance the operational capabilities of AI systems by centralizing memory management and offering advanced features like project management, agent registration, and sync job history tracking.

## User Preferences
I want iterative development.
Ask before making major changes.
Do not make changes to `sqlite_minio_sync.py`.
Do not make changes to the folder `~/.claude-mem/`.
Do not make changes to the file `~/.claude/.credentials.json`.
Do not make changes to the file `~/.claude/auth.json`.
Do not make changes to the file `~/.claude/settings.local.json`.
Do not make changes to the file `~/.claude/settings.json`.
Do not make changes to the file `~/.claude-mem-minio/config.env`.
Do not make changes to the folder `~/.claude-mem-minio/bin/`.

## System Architecture

### Core Components
Membridge operates with a Control Plane (FastAPI server) for managing projects and agents, and an Agent Daemon (FastAPI service) running on each machine to execute sync commands. Authentication is handled via header-based middleware. Sync job history is maintained in an SQLite database. A compatibility layer exists for legacy hook coexistence, and an installation validation CLI ensures proper setup. The core synchronization logic resides in `sqlite_minio_sync.py`, which pushes/pulls SQLite databases to/from MinIO. Systemd service units are provided for deployment.

The BLOOM Runtime extends Membridge with a TypeScript/React layer, offering a comprehensive UI and API for managing AI workflows. It integrates with PostgreSQL for persistent storage and provides functionalities for worker management, LLM task orchestration, lease management, and artifact storage.

### UI/UX Decisions
The BLOOM Runtime frontend provides dedicated pages for Runtime Settings, Membridge Control Plane, and Node Management. The Runtime Settings UI includes a Membridge Proxy tab, Task Queue, and Overview statistics. The Membridge Control Plane UI enables multi-project management (add, clone, propagate, delete), per-node clone status, memory sync (push/pull), leadership selection, and a nodes table. The Node Management page provides fleet overview (total/online/offline stats), per-node agent management (health check, update, restart, uninstall, remove), install script generator, and manual node registration. The navigation features a top bar with Runtime / Membridge / Nodes tabs.

### Technical Implementations
- **API Endpoints:** The Control Plane exposes endpoints for project and agent management, and for triggering sync operations. The Agent provides endpoints for health checks, project status, and executing push/pull/doctor commands. The BLOOM Runtime exposes an Express API for managing LLM tasks, leases, workers, artifacts, and audit logs, along with proxying Membridge Control Plane requests.
- **Authentication:** Header-based authentication (`X-MEMBRIDGE-ADMIN`, `X-MEMBRIDGE-AGENT`) is used for the core Membridge components. The BLOOM Runtime uses an `X-Runtime-API-Key` header with constant-time comparison.
- **Key Concepts:** `canonical_id` is derived from `CLAUDE_PROJECT_ID`. Agents support dry-run modes (`MEMBRIDGE_AGENT_DRYRUN=1`) and safe defaults for process control (`MEMBRIDGE_ALLOW_PROCESS_CONTROL=0`). All hooks support project-aware execution.
- **Installation Modes:** The `install.sh` script supports various modes for agent-only, server-only, or combined installations, including migration and cleanup functionalities.
- **BLOOM Runtime Architecture:** Utilizes Drizzle ORM with PostgreSQL for data persistence. A `DatabaseStorage` implementation handles workers, tasks, leases, artifacts, audit logs, managed projects, and project node statuses. Worker synchronization from Membridge agents is automated. A hardened Membridge client handles communication with the core Membridge control plane, featuring retry, exponential backoff, and timeouts.
- **Multi-Project Git Management:** New PostgreSQL tables `managed_projects` and `project_node_status` track git repos across nodes. API endpoints: `POST /api/runtime/projects` (create), `POST /api/runtime/projects/:id/clone` (clone on primary node via agent API), `POST /api/runtime/projects/:id/propagate` (clone to all other nodes), `POST /api/runtime/projects/:id/sync-memory` (push/pull claude-mem.db per project), `GET /api/runtime/projects/:id/node-status` (per-node clone status). UI: "Add Project" form, clone/propagate buttons, node clone status table, memory push/pull buttons.
- **Runtime Invariants:** Ensures a clear separation of memory layers (Membridge→MinIO for session, DiffMem/git for reasoning). Workers only return results/proposals, never write directly to canonical storage. Lease management includes TTL and task requeuing. Worker routing prioritizes healthy, available workers with context-based stickiness. All runtime state is persisted to PostgreSQL.
- **Rate Limiting:** `express-rate-limit` middleware is applied to all API routes in the BLOOM Runtime.
- **TLS/HTTPS:** Production mode enables HTTPS redirection and trusts proxy headers for reverse proxy deployments.

## External Dependencies

- **MinIO:** Object storage for synchronizing Claude AI memory databases.
- **FastAPI:** Python web framework used for the Control Plane and Agent Daemon.
- **SQLite:** Used for storing sync job history (`server/data/jobs.db`) and Claude AI memory databases (`claude-mem`).
- **PostgreSQL:** Primary database for the BLOOM Runtime, managed via Drizzle ORM.
- **@neondatabase/serverless:** PostgreSQL connection for the BLOOM Runtime.
- **Express:** Node.js web framework used for the BLOOM Runtime API.
- **React:** JavaScript library for building the BLOOM Runtime user interface.
- **TypeScript:** Programming language used for the BLOOM Runtime.
- **Zod:** Validation library for schemas in the BLOOM Runtime.
- **`express-rate-limit`:** Middleware for rate limiting in the BLOOM Runtime.
- **`crypto` module (Node.js):** Used for constant-time comparison in authentication.