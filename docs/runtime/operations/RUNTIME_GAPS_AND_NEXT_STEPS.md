---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
changelog:
  - 2026-02-25 (rev 2): GAP-1 and GAP-2 marked RESOLVED (Replit commit 150b491). GAP-7 added (Membridge UI integration).
title: "RUNTIME_GAPS_AND_NEXT_STEPS"
dg-publish: true
---

# BLOOM Runtime — Gaps and Next Steps

> Створено: 2026-02-25
> Статус: Canonical
> Layer: Runtime Operations
> Authority: Production Environment
> Scope: Known gaps in deployed runtime + prioritized remediation plan

---

## Context

This document captures the delta between the **current deployed state** (2026-02-25) and **production-ready state** for BLOOM Runtime on Alpine Linux.

Reference: [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — baseline deployment state.

---

## Critical Gaps

### GAP-1: Persistence Layer Missing — ✅ RESOLVED (2026-02-25)

**Resolved in:** Replit commit `150b491` — "Add persistent storage and authentication to the runtime"

**Resolution summary:**
- `DatabaseStorage` class implemented in `server/storage.ts` using Drizzle ORM + `@neondatabase/serverless`
- Replaces `MemStorage` — same `IStorage` interface, fully compatible
- All entities persisted: tasks, leases, artifacts, results, audit logs, runtime config
- Config (membridge URL, admin key) now persisted to `runtime_settings` table and loaded on startup

**See:** [[RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]] for full implementation detail.

---

### GAP-2: Runtime API Has No Authentication — ✅ RESOLVED (2026-02-25)

**Resolved in:** Replit commit `150b491` — "Add persistent storage and authentication to the runtime"

**Resolution summary:**
- `server/middleware/runtimeAuth.ts` implemented — `X-RUNTIME-API-KEY` header, timing-safe comparison
- Applied to all `/api/runtime/*` routes via `app.use("/api/runtime", runtimeAuthMiddleware)`
- Key read from `RUNTIME_API_KEY` env var; middleware is passthrough if env var unset (dev mode)
- Unprotected paths: `/api/runtime/health`, `/api/runtime/test-connection`

**New env var required:** `RUNTIME_API_KEY` in `/etc/bloom-runtime.env`

---

### GAP-3: Rate Limiting Not Configured

**Severity:** High
**Impact:** API surface exposed to unbounded request rates

**Current state:**
- `express-rate-limit` package is in `dependencies` (installed)
- No `app.use(rateLimit(...))` call in `server/index.ts` or `server/routes.ts`

**Risk:**
- Abuse of `POST /api/runtime/llm-tasks` — queue flooding
- Abuse of `POST /api/runtime/test-connection` — membridge rate limiting triggers
- Denial of service via request volume

**Resolution:**
```typescript
import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 60 * 1000,  // 1 minute
  max: 100,
  message: { error: 'Too many requests' }
});
app.use('/api/runtime/', apiLimiter);
```
Estimated effort: 15 minutes.

---

### GAP-4: Workers Not Registered

**Severity:** High (blocks task execution)
**Impact:** Execution pipeline is implemented but cannot run any tasks

**Current state:**
- `GET /api/runtime/workers` → `[]`
- `POST /api/runtime/llm-tasks/:id/lease` → `503 No available worker`
- membridge `/agents` → `{"agents": []}`
- Full lease/execution pipeline is implemented and waiting

**What is needed:**
Each worker agent must register with membridge control plane:
```http
POST http://127.0.0.1:8000/agents
X-MEMBRIDGE-ADMIN: <admin-key>
Content-Type: application/json

{
  "name": "worker-01",
  "status": "online",
  "capabilities": {
    "claude_cli": true,
    "max_concurrency": 1,
    "labels": ["production"]
  }
}
```

After registration, bloom-runtime's `GET /api/runtime/workers` will return the worker on next poll (the endpoint syncs from membridge `/agents` on every request).

**Resolution:** Deploy and register at least one Claude CLI worker agent. This is an operational step, not a code change.

---

### GAP-5: No TLS / HTTPS

**Severity:** Medium (for internal deployment) / Critical (for public exposure)
**Impact:** All traffic including `X-MEMBRIDGE-ADMIN` key travels in plaintext over HTTP

**Current state:**
- nginx serves plain HTTP on `:80`
- No certificate configured
- localhost-only traffic currently (loopback) — lower risk

**Resolution:**
```nginx
# /etc/nginx/http.d/bloom-runtime.conf additions:
server {
    listen 443 ssl;
    ssl_certificate     /etc/letsencrypt/live/<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;
    # ... proxy config same as :80 ...
}
```
Requires: domain name, `certbot` (`apk add certbot certbot-nginx`).

---

### GAP-6: Artifact Storage Not Connected to MinIO

**Severity:** Medium
**Impact:** Artifacts lost on restart; no durability for LLM outputs

**Current state:**
- `RuntimeArtifact` now stored in PostgreSQL (`runtime_artifacts` table) — content survives restarts
- MinIO running on `:9000` — not yet used for artifact storage
- The existing `sqlite_minio_sync.py` is for memory sync, not for bloom-runtime artifact storage

**Resolution:** On artifact creation in `POST .../complete`, upload `artifact.content` to MinIO bucket, store object key in `artifact.url`. PostgreSQL row stores the reference; MinIO holds the payload.

---

### GAP-7: Membridge Control Plane UI Not Integrated

**Severity:** Medium
**Impact:** User must open a separate URL (`:8000/static/ui.html`) and manually paste the admin key every session (sessionStorage — lost on tab close)

**Current state:**
- External UI at `http://<host>:8000/static/ui.html` — vanilla JS, no auth persistence
- bloom-runtime frontend (`:80`) has no link to Membridge control plane functionality
- Admin key is already stored server-side in `DatabaseStorage` / env — no need for user to enter it

**Resolution:**
1. Add proxy routes `/api/membridge/*` in `server/routes.ts` using existing `membridgeFetch()`
2. Create `MembridgePage.tsx` with projects sidebar + leadership/nodes/promote UI (shadcn/ui)
3. Add top nav bar in `App.tsx` with links to Runtime and Membridge pages

**Spec:** [[REPLIT_MEMBRIDGE_UI_INTEGRATION.md]]
**Status:** Spec written (2026-02-25), pending Replit implementation.

---

## Recommended Next Steps

Priority order based on: unblocking execution > UI integration > security hardening > observability.

### ~~Priority 1 — Persistence Layer~~ ✅ Done (2026-02-25)

Resolved in Replit commit `150b491`. See [[RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]].

---

### ~~Priority 2 — Auth Hardening~~ ✅ Done (2026-02-25)

`runtimeAuthMiddleware` via `X-RUNTIME-API-KEY` header. Resolved in Replit commit `150b491`.

---

### Priority 1 — Register a Worker (Immediate Execution Unblock)

**Effort:** 1–2 hours operational
**Unlocks:** Steps 4–8 in execution path; full end-to-end test becomes possible

1. Deploy a Claude CLI agent on any machine with network access to `:8000`
2. Configure the agent to register with membridge using `MEMBRIDGE_ADMIN_KEY`
3. Verify: `GET /api/runtime/workers` returns the worker with `status: "online"`
4. Test full pipeline: create task → lease → heartbeat → complete → artifact

This step does not require any code changes.

---

### Priority 2 — Integrate Membridge UI into Main Frontend (GAP-7)

**Effort:** 1 day (Replit Agent)
**Unlocks:** Single unified admin UI; no more manual admin key entry

Spec: [[REPLIT_MEMBRIDGE_UI_INTEGRATION.md]]

Deliverables:
- Express proxy routes `/api/membridge/*` using existing `membridgeFetch()`
- `MembridgePage.tsx` — projects sidebar + leadership/nodes/promote detail view
- Top nav bar in `App.tsx` linking Runtime ↔ Membridge pages

**Status:** Spec written, pending Replit implementation.

---

### Priority 4 — Rate Limiting (GAP-3)

**Effort:** 15 minutes
**Unlocks:** DoS protection

```typescript
import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100,
  message: { error: 'Too many requests' }
});
app.use('/api/runtime/', apiLimiter);
app.use('/api/membridge/', apiLimiter);
```

`express-rate-limit` is already in `dependencies`.

---

### Priority 5 — Observability Improvements

**Effort:** 1–3 days
**Unlocks:** Production monitoring, incident response

Sub-tasks (independent, can be done separately):

**4a. Dedicated `/health` endpoint**
```typescript
app.get('/health', (_req, res) => {
  res.json({ status: 'ok', uptime: process.uptime(), storage: 'memory' });
});
```
Currently: `GET /` returns React SPA HTML (HTTP 200 but not a proper health check).

**4b. Log rotation**
```bash
# /etc/logrotate.d/bloom-runtime
/var/log/bloom-runtime*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    postrotate
        rc-service bloom-runtime restart
    endscript
}
```

**4c. Persistent audit log to MinIO**
Flush `auditLogs[]` periodically to MinIO as JSONL file. Low effort, high value.

**4d. Metrics endpoint**
Expose Prometheus-compatible `/metrics` for worker count, task throughput, lease duration.

**4e. TLS**
Add HTTPS certificate via certbot. See GAP-5 above.

---

## Gap Summary Matrix

| Gap | ID | Severity | Status | Effort | Unblocks |
|-----|----|----------|--------|--------|---------|
| Persistence layer | GAP-1 | Critical | ✅ **RESOLVED** 2026-02-25 | — | — |
| API auth | GAP-2 | Critical | ✅ **RESOLVED** 2026-02-25 | — | — |
| Rate limiting | GAP-3 | High | ⏳ Open | 15 min | DoS protection |
| Workers not registered | GAP-4 | High | ⏳ Open | 1–2 hours ops | Task execution |
| No TLS | GAP-5 | Medium/Critical | ⏳ Open | 2–4 hours | Public exposure |
| Artifacts not in MinIO | GAP-6 | Medium | ⏳ Open | 4–8 hours | Artifact durability |
| Membridge UI not integrated | GAP-7 | Medium | ⏳ In progress (Replit) | 1 day | UX: single unified UI |

---

## Semantic Relations

**This document depends on:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — actual deployed state baseline
- [[RUNTIME_EXECUTION_PATH_VERIFICATION.md]] — which steps are live vs blocked

**This document is referenced by:**
- [[../../ІНДЕКС.md]] — master index
