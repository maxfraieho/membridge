---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
changelog:
  - 2026-02-25 (rev 2): Updated — GAP-1 (persistence) and GAP-2 (auth) resolved by Replit commit 150b491
title: "RUNTIME_DEPLOYMENT_STATE_ALPINE"
dg-publish: true
---

# BLOOM Runtime — Deployment State (Alpine Linux)

> Створено: 2026-02-25
> Статус: Canonical
> Layer: Runtime Operations
> Authority: Production Environment
> Scope: Actual deployed runtime state on Alpine Linux server

---

## A. System Topology

```
┌─────────────────────────────────────────────────────────┐
│                   External clients                       │
│              (browser, curl, API consumers)             │
└───────────────────────┬─────────────────────────────────┘
                        │ :80 (HTTP)
                        ▼
┌─────────────────────────────────────────────────────────┐
│                 nginx 1.28.2                            │
│           reverse proxy / default_server                │
│         /etc/nginx/http.d/bloom-runtime.conf            │
└───────────────────────┬─────────────────────────────────┘
                        │ proxy_pass :5000
                        ▼
┌─────────────────────────────────────────────────────────┐
│              bloom-runtime (Node.js 23)                 │
│         Express 5 backend + Vite 7 React frontend       │
│                   :5000 (0.0.0.0)                       │
│           /home/vokov/membridge/dist/index.cjs           │
│                                                         │
│  ┌─────────────────┐   ┌──────────────────────────┐    │
│  │  React 18 SPA   │   │   /api/runtime/*  routes  │    │
│  │  (served from   │   │   (Express 5 handlers)   │    │
│  │   dist/public/) │   │                          │    │
│  └─────────────────┘   └──────────┬───────────────┘    │
│                                   │ membridgeFetch()    │
│  ┌───────────────────────────────────────────────────┐  │
│  │   runtimeAuthMiddleware (X-RUNTIME-API-KEY)       │  │
│  └──────────────────────┬────────────────────────────┘  │
│                         │                               │
│  ┌──────────────────────▼────────────────────────────┐  │
│  │       DatabaseStorage (PostgreSQL via Drizzle)     │  │
│  │  tasks / leases / workers / artifacts / audit      │  │
│  │  runtime_settings (persistent config)              │  │
│  └───────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────┘
                        │ HTTP + X-MEMBRIDGE-ADMIN header
                        ▼ :8000
┌─────────────────────────────────────────────────────────┐
│          membridge control plane v0.3.0                 │
│                  Python / FastAPI                        │
│                   :8000 (0.0.0.0)                       │
│              /agents, /projects, /health                │
└───────────────────────┬─────────────────────────────────┘
                        │ (future: worker registration)
                        ▼
┌─────────────────────────────────────────────────────────┐
│           workers (NOT YET REGISTERED)                  │
│    Claude CLI agents that execute LLM tasks             │
│    Status: 0 workers online                             │
└─────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────┐
│                   MinIO :9000                           │
│            object storage (separate service)            │
│     connected via membridge memory sync (SQLite→S3)     │
└─────────────────────────────────────────────────────────┘
```

### Port Map

| Port | Service | Role | Status |
|------|---------|------|--------|
| 80 | nginx 1.28.2 | Reverse proxy → :5000 | Running |
| 5000 | bloom-runtime | Express API + React SPA | Running |
| 8000 | membridge control plane | Worker registry, agent coordination | Running |
| 8001 | Python (unidentified) | Unknown second Python service | Running |
| 9000 | MinIO | Object storage | Running |
| 22 | sshd | SSH access | Running |

---

## B. Runtime Services

### bloom-runtime (OpenRC)

**Init script:** `/etc/init.d/bloom-runtime`

```ini
command        = /usr/bin/node
command_args   = /home/vokov/membridge/dist/index.cjs
command_user   = vokov:vokov
pidfile        = /run/bloom-runtime.pid
directory      = /home/vokov/membridge
envfile        = /etc/bloom-runtime.env
output_log     = /var/log/bloom-runtime.log
error_log      = /var/log/bloom-runtime-error.log
runlevel       = default
```

**Dependency chain:**
```
need: net
after: firewall
```

**Startup guard:** `start_pre()` перевіряє наявність `dist/index.cjs` перед стартом.

### Environment Variables

Файл: `/etc/bloom-runtime.env` (chmod 600, не в git)

| Variable | Purpose | Example value |
|----------|---------|---------------|
| `NODE_ENV` | Runtime mode | `production` |
| `PORT` | Listening port | `5000` |
| `MEMBRIDGE_SERVER_URL` | Membridge control plane URL | `http://127.0.0.1:8000` |
| `MEMBRIDGE_ADMIN_KEY` | Admin auth key for membridge | `<secret, never logged>` |
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host/db` |
| `RUNTIME_API_KEY` | API key for `/api/runtime/*` routes | `<secret>` (optional; if unset, auth skipped) |

**Note:** `MEMBRIDGE_ADMIN_KEY` ніколи не з'являється в логах. API повертає masked версію: `xxxx****xxxx`.

### Working Directory & Paths

| Path | Content |
|------|---------|
| `/home/vokov/membridge/` | Repository root |
| `/home/vokov/membridge/dist/index.cjs` | Production server bundle (esbuild) |
| `/home/vokov/membridge/dist/public/` | React SPA static assets (Vite build) |
| `/etc/bloom-runtime.env` | Production secrets (chmod 600) |
| `/var/log/bloom-runtime.log` | stdout (access, request logs) |
| `/var/log/bloom-runtime-error.log` | stderr (errors, exceptions) |
| `/run/bloom-runtime.pid` | PID file (managed by OpenRC) |

### Build Artifacts

| File | Size | Purpose |
|------|------|---------|
| `dist/index.cjs` | ~922 KB | Server bundle (esbuild, CJS) |
| `dist/public/assets/index-*.js` | ~289 KB (93 KB gzip) | React SPA bundle (Vite) |
| `dist/public/assets/index-*.css` | ~69 KB (11 KB gzip) | Tailwind CSS bundle |

### Operational Commands

```bash
# Manage service
sudo rc-service bloom-runtime start
sudo rc-service bloom-runtime stop
sudo rc-service bloom-runtime restart
sudo rc-service bloom-runtime status

# Rebuild and restart (after code changes)
cd /home/vokov/membridge
npm install
npm run build
sudo rc-service bloom-runtime restart

# Logs
sudo tail -f /var/log/bloom-runtime.log
sudo tail -f /var/log/bloom-runtime-error.log

# nginx
sudo nginx -t && sudo nginx -s reload
```

---

## C. Runtime API State

Base path: `/api/runtime/`
Served by: bloom-runtime on `:5000` (also via nginx on `:80`)
Auth: `X-RUNTIME-API-KEY` header middleware (if `RUNTIME_API_KEY` env var set)

### Endpoints — Full List

| Method | Path | Status | Returns (current state) |
|--------|------|--------|------------------------|
| `GET` | `/api/runtime/config` | ✅ 200 | `{membridge_server_url, admin_key_masked, connected, last_test}` |
| `POST` | `/api/runtime/config` | ✅ 200 | Updated config (Zod-validated body) |
| `POST` | `/api/runtime/test-connection` | ✅ 200 | `{connected: true, health: {...}}` |
| `GET` | `/api/runtime/workers` | ✅ 200 | `[]` — membridge /agents returns empty (0 registered agents) |
| `GET` | `/api/runtime/workers/:id` | ✅ 404 if missing | Worker detail + active leases |
| `POST` | `/api/runtime/llm-tasks` | ✅ 201 | Creates task in queue |
| `GET` | `/api/runtime/llm-tasks` | ✅ 200 | `[]` — no tasks created yet |
| `GET` | `/api/runtime/llm-tasks/:id` | ✅ 404 if missing | Task detail |
| `POST` | `/api/runtime/llm-tasks/:id/lease` | ✅ logic ready | Returns 503 (no workers available) |
| `POST` | `/api/runtime/llm-tasks/:id/heartbeat` | ✅ logic ready | Renews lease TTL |
| `POST` | `/api/runtime/llm-tasks/:id/complete` | ✅ logic ready | Writes artifact + result |
| `POST` | `/api/runtime/llm-tasks/:id/requeue` | ✅ logic ready | Requeues failed/dead tasks |
| `GET` | `/api/runtime/leases` | ✅ 200 | `[]` — no active leases |
| `GET` | `/api/runtime/runs` | ✅ 200 | `[]` — last 50 tasks (empty) |
| `GET` | `/api/runtime/artifacts` | ✅ 200 | `[]` — no artifacts yet |
| `GET` | `/api/runtime/audit` | ✅ 200 | Recent audit log entries |
| `GET` | `/api/runtime/stats` | ✅ 200 | `{tasks:{total:0}, leases:{active:0}, workers:{online:0}}` |

### Why Lists Are Empty

All list endpoints return `[]` for one reason:
**Workers have not been registered** with the membridge control plane.

- `GET /api/runtime/workers` fetches from `membridge:8000/agents` + local storage → 0 agents → empty
- No workers → no lease assignments → no tasks can be executed
- `GET /api/runtime/leases`, `/llm-tasks`, `/runs`, `/artifacts` all empty as a consequence

### Stale Lease Expiry

A background interval runs every **30 seconds**:
```typescript
setInterval(async () => {
  const expired = await storage.expireStaleLeases();
  // requeues tasks with expired leases
}, 30000);
```
Lease TTL default: **300 seconds**.

### Worker Selection Algorithm

When a task requests a lease, `pickWorker()`:
1. Filters workers: `status === "online"` AND `capabilities.claude_cli === true` AND `active_leases < max_concurrency`
2. If `context_id` provided: tries sticky routing to existing worker for that context
3. Otherwise: picks worker with most free capacity (max_concurrency - active_leases)

---

## D. Membridge Integration State

### Connection Status

```json
{
  "connected": true,
  "health": {
    "status": "ok",
    "service": "membridge-control-plane",
    "version": "0.3.0",
    "projects": 0,
    "agents": 0
  }
}
```

Verified via `POST /api/runtime/test-connection` — **2 successful tests** recorded in audit log at deployment time.

### Proxy Mechanism

bloom-runtime → membridge communication uses `membridgeFetch()`:
- Injects `X-MEMBRIDGE-ADMIN` header (from `MEMBRIDGE_ADMIN_KEY` env var)
- Timeout: **10 seconds** per request
- Uses `AbortController` for timeout enforcement
- On timeout/error: connection status set to `false`

### What Is Connected, What Is Not

| Component | State |
|-----------|-------|
| membridge `/health` endpoint | ✅ reachable, responding |
| `X-MEMBRIDGE-ADMIN` auth | ✅ key loaded from env, injected in requests |
| membridge `/agents` endpoint | ✅ reachable, returns empty array |
| Worker agents registered | ❌ 0 agents registered |
| Task execution pipeline | ❌ idle (no workers) |
| Lease assignment | ❌ returns 503 (no workers available) |

### Leasing Protocol (Implemented, Idle)

The full lease lifecycle is implemented:
```
queued → [POST .../lease] → leased → [POST .../heartbeat] → running → [POST .../complete] → completed
                                                                                          ↘ failed
```
Waiting for worker registration to become active.

---

## E. Storage Model

### Current Implementation: DatabaseStorage ✅ (resolved 2026-02-25)

Class: `DatabaseStorage` in `server/storage.ts`
Driver: Drizzle ORM + `@neondatabase/serverless` (PostgreSQL)
Persistence: **full** — all data written to PostgreSQL

```typescript
// All state persists across restarts via PostgreSQL
// Tables: llm_tasks, leases, workers, runtime_artifacts,
//         llm_results, audit_logs, runtime_settings, users
```

### Consequences of PostgreSQL Storage

| Event | Consequence |
|-------|-------------|
| `rc-service bloom-runtime restart` | State **preserved** in PostgreSQL |
| Server crash | State preserved; in-flight runs recovered via lease expiry |
| Node.js OOM | State preserved |
| Machine reboot | Service auto-restarts (OpenRC default), state **intact** |
| `MEMBRIDGE_ADMIN_KEY` update | Persisted in `runtime_settings` table via `POST /api/runtime/config` |

**Operational implication:** bloom-runtime is now **stateful across restarts**. Tasks, leases, audit history, and config survive service restarts.

### Key Design Notes

- Workers remain registered via heartbeat polling — not permanently stored
- `DatabaseStorage.init()` runs on startup to load config from `runtime_settings`
- `upsertWorker()` uses `ON CONFLICT DO UPDATE` to handle re-registration
- Timestamps stored as Unix epoch milliseconds (bigint) for consistency with previous MemStorage API contract

See: [[RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]] — full implementation detail

---

## F. Security State

### Runtime API

| Control | Status | Notes |
|---------|--------|-------|
| Authentication on `/api/runtime/*` | ✅ **present** | `X-RUNTIME-API-KEY` header, timing-safe comparison; skipped if env var unset |
| Authorization / RBAC | ❌ **absent** | No role checks (single key covers all operations) |
| Rate limiting | ❌ **absent** | `express-rate-limit` in deps, not wired |
| Input validation | ✅ Present | Zod schemas on POST bodies |
| Admin key in logs | ✅ Masked | Returns `xxxx****xxxx` in API responses |
| Admin key in git | ✅ Safe | `/etc/bloom-runtime.env` is outside repo |

### Network / Transport

| Control | Status | Notes |
|---------|--------|-------|
| TLS / HTTPS | ❌ **disabled** | nginx serves plain HTTP on :80 |
| nginx ↔ bloom-runtime | HTTP only | localhost proxy, no TLS needed internally |
| bloom-runtime ↔ membridge | HTTP only | loopback `127.0.0.1:8000` |
| CORS | Not configured | Express defaults |

### Secret Management

- `/etc/bloom-runtime.env`: `chmod 600`, owned by root
- `MEMBRIDGE_ADMIN_KEY`: never written to logs; masked in API responses
- No secrets committed to git (`.env.server` is in repo but contains only membridge *server-side* keys, separate from runtime client keys)

---

## G. Membridge Control Plane Proxy (НОВЕ — 2026-02-25)

BLOOM Runtime тепер проксує Membridge Control Plane через `/api/membridge/*`:

```
Браузер                    BLOOM Runtime                  Membridge
┌──────────┐   /api/    ┌──────────────┐   HTTP+key    ┌──────────┐
│          │──membridge──│              │──────────────▶│          │
│ React    │  /*         │ membridgeFetch│               │ :8000    │
│ SPA      │             │ ()            │               │ FastAPI  │
│          │◀────────────│ Admin key     │◀──────────────│          │
│          │  JSON       │ автоматично   │  JSON         │          │
└──────────┘             └──────────────┘               └──────────┘
```

| Метод | Шлях | Проксує до | Статус |
|-------|------|-----------|--------|
| `GET` | `/api/membridge/health` | `/health` | ✅ Працює |
| `GET` | `/api/membridge/projects` | `/projects` | ✅ Працює |
| `GET` | `/api/membridge/projects/:cid/leadership` | `/projects/{cid}/leadership` | ✅ Працює |
| `GET` | `/api/membridge/projects/:cid/nodes` | `/projects/{cid}/nodes` | ✅ Працює |
| `POST` | `/api/membridge/projects/:cid/leadership/select` | `/projects/{cid}/leadership/select` | ✅ Працює |

Фронтенд: вкладка **Membridge** у навігації BLOOM.
Admin key інжектується серверним кодом — фронтенд ніколи не бачить ключ.

---

## H. Оцінка операційної готовності

| Вимір | Оцінка | Опис |
|-----------|-------|-----------|
| **Архітектурна готовність** | 9/10 | Ядро архітектури надійне. Persistence (PostgreSQL), auth, membridgeFetch з retry/backoff, Membridge UI інтегрований. |
| **Готовність виконання** | 4/10 | Pipeline реалізований end-to-end. Заблокований відсутністю workers (0 зареєстрованих). Реєстрація одного worker активує весь pipeline. |
| **Операційна готовність** | 7/10 | Сервіс автозапускається, логи налаштовані, nginx сконфігурований, секрети захищені, стан переживає рестарти. Відсутнє: ротація логів, rate limiting, alerting. |
| **Production готовність** | 7/10 | GAP-1, GAP-2, GAP-7 вирішені. Залишаються: TLS, rate limiting, реєстрація workers. Придатний для внутрішнього production на довіреній мережі. |

---

## Semantic Relations

**This document depends on:**
- [[../../architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md]] — architectural spec for Claude CLI proxy
- [[../../integration/ІНТЕГРАЦІЯ_MEMBRIDGE.md]] — Membridge Control Plane contract

**This document is referenced by:**
- [[RUNTIME_EXECUTION_PATH_VERIFICATION.md]] — actual execution path trace
- [[RUNTIME_GAPS_AND_NEXT_STEPS.md]] — gaps and remediation
- [[../../ІНДЕКС.md]] — master index
