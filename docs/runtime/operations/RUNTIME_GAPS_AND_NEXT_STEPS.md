---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
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

### GAP-1: Persistence Layer Missing

**Severity:** Critical
**Impact:** All runtime state lost on service restart

**Current state:**
- `MemStorage` class — all data in Node.js process heap
- `Map<string, Task>`, `Map<string, Lease>`, `Map<string, WorkerNode>`, etc.
- No database connection

**What is lost on restart:**
- All queued, running, and completed tasks
- All active leases (in-progress runs interrupted silently)
- All registered worker state
- All artifacts and results
- Audit log history

**What exists but is unused:**
- `drizzle.config.ts` — Drizzle ORM config pointing to PostgreSQL
- `shared/schema.ts` — full PostgreSQL table definitions (`pgTable`) for all entities
- `pg` package in dependencies — PostgreSQL client installed

**Gap:** `DatabaseStorage` class implementing `IStorage` interface — not built.

**Resolution:** Implement `DatabaseStorage` using the existing schema, replace `MemStorage` import in `server/storage.ts`. The `IStorage` interface is fully defined — implementation is a mechanical task.

---

### GAP-2: Runtime API Has No Authentication

**Severity:** Critical (for public exposure)
**Impact:** All `/api/runtime/*` endpoints publicly accessible without credentials

**Current state:**
- No authentication middleware on any route
- Any client with network access can:
  - Read all tasks, leases, audit logs
  - Create tasks and consume worker capacity
  - Modify membridge URL and admin key via `POST /api/runtime/config`
  - Trigger test-connection (consuming rate limits)

**What exists:**
- `passport` + `passport-local` in dependencies
- `express-session` + `memorystore` in dependencies
- `auth.py` exists in `server/` (Python — not the Node.js auth layer)
- User model defined in `shared/schema.ts`

**Gap:** Express middleware chain for authentication not wired to `/api/runtime/*` routes.

**Resolution options (choose one):**
1. **Simple shared secret** — `X-BLOOM-API-KEY` header middleware, key from env var. Minimal implementation, fast.
2. **Session-based auth** — use existing `passport-local` + `express-session` setup. Full login UI.
3. **JWT** — stateless, compatible with worker-to-runtime calls.

Recommended starting point: **option 1** (shared secret) — unblocks production use in hours, not days.

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
- `RuntimeArtifact` stored in `Map<string, RuntimeArtifact>` in `MemStorage`
- MinIO running on `:9000` (separate service, accessible)
- No S3/MinIO client in `server/routes.ts` or `server/storage.ts`
- The existing `sqlite_minio_sync.py` is for memory sync, not for artifact storage

**Resolution:** On artifact creation in `POST .../complete`, upload `artifact.content` to MinIO bucket, store object key in `artifact.url`. This adds durability without requiring `DatabaseStorage` first.

---

## Recommended Next Steps

Priority order based on: unblocking execution > security hardening > observability.

### Priority 1 — Register a Worker (Immediate Unblock)

**Effort:** 1–2 hours operational
**Unlocks:** Steps 4–8 in execution path; full end-to-end test becomes possible

1. Deploy a Claude CLI agent on any machine with network access to `:8000`
2. Configure the agent to register with membridge using `MEMBRIDGE_ADMIN_KEY`
3. Verify: `GET /api/runtime/workers` returns the worker with `status: "online"`
4. Test full pipeline: create task → lease → heartbeat → complete → artifact

This step does not require any code changes.

---

### Priority 2 — Persistence Layer

**Effort:** 1–2 days
**Unlocks:** Survives restarts, enables production reliability

Steps:
1. Provision a PostgreSQL instance (or use SQLite via `better-sqlite3` for local deployment)
2. Run `npm run db:push` — Drizzle will create all tables from `shared/schema.ts`
3. Implement `DatabaseStorage extends IStorage` using `drizzle-orm` queries
4. Replace `export const storage = new MemStorage()` → `new DatabaseStorage()`
5. Add `DATABASE_URL` to `/etc/bloom-runtime.env`

The `IStorage` interface is the contract. All 20+ methods have clear semantics.
The existing `shared/schema.ts` has all tables: `users`, `llm_tasks`, `leases`, `artifacts`, `results`, `audit_logs`.

**Worker state:** workers can remain in-memory (they re-register on heartbeat).
**Config:** persist `runtimeConfig` in a `settings` table or env file (already done via env).

---

### Priority 3 — Auth Hardening

**Effort:** 4–8 hours
**Unlocks:** Safe to expose API beyond trusted network

Minimal viable auth:
1. Add `BLOOM_API_KEY` to `/etc/bloom-runtime.env`
2. Write middleware:
   ```typescript
   app.use('/api/runtime/', (req, res, next) => {
     const key = req.headers['x-bloom-api-key'];
     if (key !== process.env.BLOOM_API_KEY) {
       return res.status(401).json({ error: 'Unauthorized' });
     }
     next();
   });
   ```
3. Wire before route registration in `server/index.ts`

For worker-to-runtime calls (heartbeat, complete), consider a separate `BLOOM_WORKER_KEY` with narrower permissions.

---

### Priority 4 — Observability Improvements

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

| Gap | ID | Severity | Effort | Unblocks |
|-----|----|----------|--------|---------|
| Persistence layer missing | GAP-1 | Critical | 1–2 days | Reliability, production |
| API auth missing | GAP-2 | Critical | 4–8 hours | Security |
| Rate limiting not configured | GAP-3 | High | 15 min | DoS protection |
| Workers not registered | GAP-4 | High | 1–2 hours | Task execution |
| No TLS | GAP-5 | Medium/Critical | 2–4 hours | Public exposure |
| Artifacts not in MinIO | GAP-6 | Medium | 4–8 hours | Artifact durability |

---

## Semantic Relations

**This document depends on:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — actual deployed state baseline
- [[RUNTIME_EXECUTION_PATH_VERIFICATION.md]] — which steps are live vs blocked

**This document is referenced by:**
- [[../../ІНДЕКС.md]] — master index
