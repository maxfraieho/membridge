---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
title: "RUNTIME_BACKEND_IMPLEMENTATION_STATE"
dg-publish: true
---

# BLOOM Runtime — Backend Implementation State

> Created: 2026-02-25
> Status: Canonical
> Layer: Runtime Operations
> Authority: Implementation Reference
> Scope: Backend hardening implementation — persistence, auth, worker sync, proxy client

---

## Overview

This document describes the implementation state of BLOOM Runtime backend hardening, resolving critical gaps identified in [[RUNTIME_GAPS_AND_NEXT_STEPS.md]].

---

## GAP-1 Resolution: Persistent Storage

### Implementation

**Class:** `DatabaseStorage` in `server/storage.ts`
**Driver:** Drizzle ORM + `@neondatabase/serverless` (PostgreSQL)
**Schema:** `shared/schema.ts` — Drizzle `pgTable` definitions for all runtime entities

### Tables Created

| Table | Entity | Key Columns |
|-------|--------|-------------|
| `llm_tasks` | LLMTask | id, context_id, agent_slug, prompt, status, attempts |
| `leases` | Lease | id, task_id, worker_id, expires_at, status, last_heartbeat |
| `workers` | WorkerNode | id, node_id, status, capabilities (JSONB), last_heartbeat |
| `runtime_artifacts` | RuntimeArtifact | id, task_id, type, content, tags (JSONB) |
| `llm_results` | LLMResult | id, task_id, worker_id, status, output, metrics (JSONB) |
| `audit_logs` | AuditLogEntry | id, timestamp, action, entity_type, entity_id, actor, detail |
| `runtime_settings` | RuntimeConfig | key, value (key-value store for config persistence) |
| `users` | User | id, username, password (existing) |

### Key Design Decisions

1. **JSONB for structured fields** — `capabilities`, `policy`, `metrics`, `context_hints`, `ip_addrs`, `tags`, `entity_refs` use PostgreSQL JSONB for flexible schema within typed columns.
2. **Timestamps as bigint** — All timestamps stored as Unix epoch milliseconds (`bigint` mode: "number") for consistency with the existing MemStorage API contract.
3. **Upsert for workers** — `upsertWorker()` uses `ON CONFLICT DO UPDATE` to handle re-registration without duplicates.
4. **Config cache** — `RuntimeConfig` (membridge URL, admin key, connection status) cached in memory and persisted to `runtime_settings` table. Loaded on startup via `init()`.
5. **IStorage interface preserved** — `DatabaseStorage` implements the same `IStorage` interface as `MemStorage`. No route changes required.

### Migration

```bash
npm run db:push
```

Drizzle Kit pushes the schema to PostgreSQL. No manual SQL required.

---

## GAP-2 Resolution: Runtime API Authentication

### Implementation

**File:** `server/middleware/runtimeAuth.ts`
**Header:** `X-Runtime-API-Key`
**Env var:** `RUNTIME_API_KEY`

### Behavior

1. If `RUNTIME_API_KEY` is not set, auth is **disabled** (development mode).
2. If set, all `/api/runtime/*` endpoints require `X-Runtime-API-Key` header.
3. Constant-time comparison using `crypto.timingSafeEqual` to prevent timing attacks.
4. **Unprotected paths:** `/api/runtime/health`, `/api/runtime/test-connection`.

### Deployment

```bash
# Add to /etc/bloom-runtime.env:
RUNTIME_API_KEY=<generate-a-strong-key>
```

---

## Worker Auto-Sync from Membridge

### Implementation

**File:** `server/runtime/workerSync.ts`
**Interval:** Every 10 seconds
**Source:** `GET MEMBRIDGE_SERVER_URL/agents`

### Behavior

1. Fetches agent list from membridge control plane every 10s.
2. For each agent: upserts into local worker registry (PostgreSQL).
3. Updates: status, capabilities, last_heartbeat, IP addresses.
4. Workers missing from membridge response for >60s → marked `offline`.
5. Does NOT modify active leases — lease ownership preserved.
6. Uses hardened `membridgeFetch()` with retry and timeout.
7. Sync failures silently skipped — no crash on membridge downtime.

### Startup

Worker sync starts automatically in `registerRoutes()` via `startWorkerSync()`.

---

## Membridge Proxy Client Hardening

### Implementation

**File:** `server/runtime/membridgeClient.ts`

### Features

| Feature | Implementation |
|---------|---------------|
| Retry logic | Up to 3 retries (configurable per call) |
| Exponential backoff | 500ms × 2^attempt + 30% jitter |
| Timeout | 10s default per request (AbortController) |
| Connection tracking | Consecutive failure counter, last success/error timestamps |
| 5xx retry | Only retries on HTTP 500+ errors |
| 4xx pass-through | Client errors returned immediately (no retry) |
| State exposure | `getMembridgeClientState()` returns connection health |

### Health Endpoint Integration

`GET /api/runtime/health` includes membridge client state:

```json
{
  "status": "ok",
  "service": "bloom-runtime",
  "uptime": 123.45,
  "storage": "postgresql",
  "membridge": {
    "consecutiveFailures": 0,
    "lastSuccess": 1772042245043,
    "lastError": null,
    "connected": true
  }
}
```

---

## Updated Execution Path

```
Client Request
     │
     ▼
 [1] nginx :80  ──────────────────────── ✅ LIVE
     │
     ▼
 [2] bloom-runtime :5000 (Express)  ───── ✅ LIVE
     │
     ├─► X-Runtime-API-Key middleware ─── ✅ LIVE (optional via RUNTIME_API_KEY)
     │
     ├─► POST /api/runtime/llm-tasks  ─── ✅ LIVE (persisted to PostgreSQL)
     │
     ▼
 [3] Task Queue (PostgreSQL)  ───────── ✅ LIVE (survives restart)
     │
     ▼
 [4] POST /api/runtime/llm-tasks/:id/lease
     │   Worker selection (pickWorker)  ── ✅ LIVE (workers from auto-sync)
     │
     ▼
 [5] Worker auto-sync (10s interval) ── ✅ LIVE (→ membridge /agents)
     │
     ├─► membridgeFetch with retries ── ✅ LIVE (backoff, timeout, tracking)
     │
     ▼
 [6] membridge control plane :8000  ──── ✅ LIVE
     │
     ▼
 [7] Worker Node  ─────────────────── ⏳ WAITING (operational: register agent)
     │
     ▼
 [8] Task completion  ────────────── ✅ LIVE (artifact + result to PostgreSQL)
     │
     ▼
 [9] Artifact storage (PostgreSQL) ── ✅ LIVE (persisted, survives restart)
     │
     ▼
[10] Audit log (PostgreSQL)  ──────── ✅ LIVE (persisted, survives restart)
     │
     ▼
[11] Response to client  ──────────── ✅ LIVE
```

---

## Runtime Readiness Assessment

| Dimension | Previous | Current | Notes |
|-----------|----------|---------|-------|
| Persistence | ❌ In-memory | ✅ PostgreSQL | All entities persisted |
| Auth | ❌ None | ✅ API key | Optional, constant-time |
| Worker discovery | ❌ Manual | ✅ Auto-sync | 10s interval from membridge |
| Proxy reliability | ⚠️ No retry | ✅ Hardened | Retry + backoff + tracking |
| Health endpoint | ❌ Missing | ✅ /api/runtime/health | Includes storage + membridge state |
| Lease lifecycle | ✅ Implemented | ✅ Persisted | TTL, heartbeat, expiry, requeue |
| Audit trail | ⚠️ In-memory | ✅ Persisted | Survives restart |
| Restart resilience | ❌ State lost | ✅ Full recovery | All state in PostgreSQL |

---

## Files Created

| File | Purpose |
|------|---------|
| `server/db.ts` | Drizzle ORM database connection |
| `server/middleware/runtimeAuth.ts` | API key authentication middleware |
| `server/runtime/membridgeClient.ts` | Hardened HTTP client with retry/backoff |
| `server/runtime/workerSync.ts` | Automatic worker discovery from membridge |
| `docs/runtime/operations/RUNTIME_BACKEND_IMPLEMENTATION_STATE.md` | This document |

## Files Modified

| File | Changes |
|------|---------|
| `shared/schema.ts` | Added Drizzle pgTable definitions for all runtime entities |
| `server/storage.ts` | Replaced MemStorage with DatabaseStorage (PostgreSQL) |
| `server/routes.ts` | Integrated auth middleware, worker sync, hardened client, health endpoint |

---

## Deployment Steps

1. Ensure `DATABASE_URL` environment variable is set (PostgreSQL connection string).
2. Run `npm run db:push` to create all tables.
3. Optionally set `RUNTIME_API_KEY` for API authentication.
4. Restart bloom-runtime service.

---

## Semantic Relations

**This document depends on:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — baseline deployment topology
- [[RUNTIME_GAPS_AND_NEXT_STEPS.md]] — gap definitions this resolves

**This document is referenced by:**
- [[../../ІНДЕКС.md]] — master documentation index
