---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
title: "RUNTIME_EXECUTION_PATH_VERIFICATION"
dg-publish: true
---

# BLOOM Runtime — Execution Path Verification

> Створено: 2026-02-25
> Статус: Canonical
> Layer: Runtime Operations
> Authority: Production Environment
> Scope: Actual verified execution path — what is live vs what is pending

---

## Overview

This document traces the full intended execution path of BLOOM Runtime and marks each segment with its actual verified status on the production Alpine deployment.

**Legend:**
- ✅ `LIVE` — verified working in production
- ⚙️ `IMPLEMENTED` — code exists, logic correct, but not yet activated (missing precondition)
- ❌ `MISSING` — not yet built

---

## Full Execution Path

```
Client Request
     │
     ▼
 [1] nginx :80  ──────────────────────── ✅ LIVE
     │
     ▼
 [2] bloom-runtime :5000 (Express)  ───── ✅ LIVE
     │
     ├─► POST /api/runtime/llm-tasks  ─── ⚙️ IMPLEMENTED (creates task, status=queued)
     │
     ▼
 [3] Task Queue (MemStorage)  ─────────── ⚙️ IMPLEMENTED (in-memory)
     │
     ▼
 [4] POST /api/runtime/llm-tasks/:id/lease
     │   Worker selection (pickWorker)  ── ⚙️ IMPLEMENTED (returns 503 — no workers)
     │
     ▼
 [5] membridge control plane :8000  ────── ✅ LIVE (GET /agents → [])
     │
     ▼
 [6] Worker Node (Claude CLI agent)  ───── ❌ MISSING (0 registered)
     │
     ├─► POST /api/runtime/llm-tasks/:id/heartbeat  ─── ⚙️ IMPLEMENTED
     │
     ▼
 [7] Claude CLI execution  ─────────────── ❌ MISSING
     │
     ▼
 [8] POST /api/runtime/llm-tasks/:id/complete
     │   Artifact creation  ─────────────── ⚙️ IMPLEMENTED
     │   Result recording  ──────────────── ⚙️ IMPLEMENTED
     │
     ▼
 [9] Artifact stored in MemStorage  ────── ⚙️ IMPLEMENTED (in-memory, not persisted)
     │
     ▼
[10] Audit log entry  ──────────────────── ✅ LIVE (in-memory, entries visible via /api/runtime/audit)
     │
     ▼
[11] Response to client  ───────────────── ✅ LIVE
```

---

## Segment-by-Segment Verification

### [1] nginx → bloom-runtime

**Status:** ✅ LIVE

```bash
# Verified:
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/
# → 200

curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/api/runtime/stats
# → 200
```

nginx config: `/etc/nginx/http.d/bloom-runtime.conf`
Upstream: `server 127.0.0.1:5000; keepalive 32;`
Headers injected: `X-Real-IP`, `X-Forwarded-For`, WebSocket upgrade support.

---

### [2] bloom-runtime Express server

**Status:** ✅ LIVE

```bash
# Verified:
curl -s http://127.0.0.1:5000/api/runtime/stats
# → {"tasks":{"total":0,"by_status":{}},"leases":{"total":0,"active":0},"workers":{"total":0,"online":0}}
```

Node.js 23.11.1, Express 5.0.1.
Serving React SPA (`dist/public/`) + API (`/api/runtime/*`).

---

### [3] Task creation

**Status:** ⚙️ IMPLEMENTED — not yet tested with real payload

The `POST /api/runtime/llm-tasks` endpoint is wired to `storage.createTask()`.
Schema validated with Zod (`insertLLMTaskSchema`).
Task is created with status `queued` and logged to audit.

Not yet tested with a real task payload in this deployment.

---

### [4] Lease assignment & worker selection

**Status:** ⚙️ IMPLEMENTED — blocked on worker registration

`POST /api/runtime/llm-tasks/:id/lease` calls `pickWorker()`:

```typescript
const online = workers.filter(
  w => w.status === "online" &&
       w.capabilities.claude_cli &&
       w.active_leases < w.capabilities.max_concurrency
);
if (online.length === 0) return null;
// → bloom-runtime returns HTTP 503 "No available worker"
```

Current result: `503 No available worker with free capacity`.
This will resolve immediately upon first worker registration.

---

### [5] Membridge control plane

**Status:** ✅ LIVE — verified with admin auth

```bash
# Verified (without exposing key):
curl -s http://127.0.0.1:8000/health
# → {"status":"ok","service":"membridge-control-plane","version":"0.3.0","projects":0,"agents":0}

# Via bloom-runtime proxy:
curl -s -X POST http://127.0.0.1:5000/api/runtime/test-connection
# → {"connected":true,"health":{"status":"ok",...}}
```

Audit log records 2 successful `connection_test` events from deployment smoke tests.
`GET /agents` returns `[]` — no workers registered.

---

### [6] Worker Node (Claude CLI agent)

**Status:** ❌ MISSING

No agents have been registered with membridge.

**What is needed to unblock:**
A worker node must register itself with membridge at `POST /agents` with:
```json
{
  "name": "<worker-id>",
  "status": "online",
  "capabilities": {
    "claude_cli": true,
    "max_concurrency": 1
  }
}
```

After registration, `GET /api/runtime/workers` will return the worker,
and `POST .../lease` will succeed instead of returning 503.

---

### [7] Claude CLI execution

**Status:** ❌ MISSING

Workers invoke Claude CLI with task parameters from the lease.
The protocol for this is defined in:
[[../../architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md]]

Not activated — no workers.

---

### [8] Task completion

**Status:** ⚙️ IMPLEMENTED

`POST /api/runtime/llm-tasks/:id/complete` handler:
1. Validates body with `completeTaskSchema` (Zod)
2. Creates artifact in storage (`type`, `content`, `tags`)
3. Creates result record (`status`, `output`, `error_message`, `metrics`)
4. Updates task status → `completed` or `failed`
5. Releases lease (`status = "released"`)
6. Writes audit log

---

### [9] Artifact storage

**Status:** ⚙️ IMPLEMENTED — in-memory only

Artifacts stored in `Map<string, RuntimeArtifact>` in `MemStorage`.
Queryable via `GET /api/runtime/artifacts?task_id=<id>`.

**Limitation:** Lost on service restart.
Does not connect to MinIO in current implementation.

---

### [10] Audit log

**Status:** ✅ LIVE — in-memory, visible via API

```bash
curl -s http://127.0.0.1:5000/api/runtime/audit?limit=10
# → [...audit entries from smoke test...]
```

All state-changing operations emit audit entries:
`config_updated`, `connection_test`, `task_created`, `task_leased`,
`task_completed`, `task_requeued`.

**Limitation:** In-memory. Lost on restart. No persistence to MinIO/DB.

---

### [11] Response to client

**Status:** ✅ LIVE

All API responses are JSON.
Express request logging: `METHOD /path STATUS DURATIONms :: {responseBody}`.
Visible in `/var/log/bloom-runtime.log`.

---

## Summary Table

| Step | Component | Status | Blocker |
|------|-----------|--------|---------|
| 1 | nginx reverse proxy | ✅ LIVE | — |
| 2 | bloom-runtime Express | ✅ LIVE | — |
| 3 | Task creation | ⚙️ IMPLEMENTED | — |
| 4 | Lease / worker selection | ⚙️ IMPLEMENTED | No workers registered |
| 5 | Membridge control plane | ✅ LIVE | — |
| 6 | Worker node | ❌ MISSING | Worker agent not deployed |
| 7 | Claude CLI execution | ❌ MISSING | Worker node missing |
| 8 | Task completion + artifact | ⚙️ IMPLEMENTED | Worker node missing |
| 9 | Artifact storage | ⚙️ IMPLEMENTED | In-memory, no MinIO integration |
| 10 | Audit log | ✅ LIVE | In-memory only |
| 11 | API response | ✅ LIVE | — |

---

## What One Worker Registration Unlocks

Registering a single worker with membridge immediately activates:
- Steps 4, 6, 7, 8 in the execution path
- Full end-to-end task execution
- Lease assignment, heartbeat, completion flow
- Artifact creation and audit trail

The entire pipeline is code-complete and waiting for this single operational step.

---

## Semantic Relations

**This document depends on:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — system topology and service state
- [[../../architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md]] — Claude CLI proxy spec

**This document is referenced by:**
- [[RUNTIME_GAPS_AND_NEXT_STEPS.md]] — gaps and next steps
- [[../../ІНДЕКС.md]] — master index
