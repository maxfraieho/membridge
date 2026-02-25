# Код проєкту: docs
**Згенеровано:** 2026-02-25 19:39:20
**Директорія:** `/home/vokov/projects/mem/docs`
**Формат:** Markdown
---
## Структура проєкту
```
docs/
├── ІНДЕКС.md
├── web-ui.md
├── arm64-claude-mem.md
├── auto-heartbeat.md
├── leadership.md
├── migration.md
├── sync-modes.md
├── runtime/
│   ├── operations/
│   │   ├── RUNTIME_EXECUTION_PATH_VERIFICATION.md
│   │   ├── RUNTIME_DEPLOYMENT_STATE_ALPINE.md
│   │   ├── RUNTIME_GAPS_AND_NEXT_STEPS.md
├── audit/
│   ├── ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md
│   ├── АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md
│   ├── _INDEX.md
│   ├── МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md
├── integration/
│   ├── ІНТЕГРАЦІЯ_MEMBRIDGE.md
│   ├── ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND.md
│   ├── JOB_QUEUE_ТА_ARTIFACT_MODEL.md
│   ├── DEPLOYMENT_REPLIT_АРХІТЕКТУРА.md
│   ├── ІНТЕГРАЦІЯ_MEMORY_BACKEND.md
│   ├── _INDEX.md
│   ├── RUNTIME_TOPOLOGY_NOTEBOOKLM.md
│   ├── ІНТЕГРАЦІЯ_FRONTEND_LOVABLE.md
│   ├── ПЕРСПЕКТИВА_АГЕНТНОЇ_РОЗРОБКИ.md
├── architecture/
│   ├── runtime/
│   │   ├── INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md```
---
### ІНДЕКС.md
**Розмір:** 11,151 байт
```text
---
tags:
  - domain:meta
  - status:canonical
  - format:inventory
created: 2026-02-21
updated: 2026-02-25
title: "ІНДЕКС"
dg-publish: true
---

# Garden Bloom: Documentation Index

> Updated: 2026-02-25
> Language: Ukrainian (canonical)
> Status: Single entry point for all documentation

---

## What is Garden Bloom?

**Garden Bloom** is an execution platform for AI agents where the human remains in control. Agents read knowledge, execute tasks, and **propose** changes through the Proposal system -- the owner decides what to accept. Every mutation requires explicit consent; every step is audit-logged.

In short: **AI that proposes -- human that decides.**

**Architectural root:** [architecture/foundation/АРХІТЕКТУРНИЙ_КОРІНЬ.md](architecture/foundation/АРХІТЕКТУРНИЙ_КОРІНЬ.md) -- axioms, component roles, authority boundaries, canonical flow.

---

## What is BLOOM?

**BLOOM** (Behavioral Logic Orchestration for Order-Made Systems) is the **execution runtime** of Garden Bloom.

BLOOM handles orchestration of the execution pipeline, isolation of execution contexts, delegation of behavioral logic, and memory integration through Membridge.

Reference: [architecture/foundation/BLOOM_RUNTIME_IDENTITY.md](architecture/foundation/BLOOM_RUNTIME_IDENTITY.md)

---

## Documentation Structure

```
docs/
├── ІНДЕКС.md                             <-- this file
│
├── architecture/
│   ├── foundation/                       <-- axiomatic foundation
│   │   ├── АРХІТЕКТУРНИЙ_КОРІНЬ.md       <-- central hub
│   │   └── BLOOM_RUNTIME_IDENTITY.md     <-- BLOOM execution identity
│   │
│   ├── core/                             <-- runtime specs
│   │   ├── _INDEX.md
│   │   ├── КАНОНІЧНА_АРХІТЕКТУРА_ВИКОНАННЯ.md
│   │   ├── КАНОНІЧНА_МОДЕЛЬ_АВТОРИТЕТУ_СХОВИЩА.md
│   │   ├── INBOX_ТА_PROPOSAL_АРХІТЕКТУРА.md
│   │   ├── КОНТРАКТ_АГЕНТА_V1.md
│   │   ├── КАНОНІЧНИЙ_КОНВЕЄР_ВИКОНАННЯ.md
│   │   ├── КАНОНІЧНИЙ_ЦИКЛ_ЗАПУСКУ.md
│   │   └── АБСТРАКЦІЯ_РІВНЯ_ОРКЕСТРАЦІЇ.md
│   │
│   ├── features/                         <-- subsystems and ADRs
│   │   ├── _INDEX.md
│   │   ├── ПАМ_ЯТЬ_АГЕНТА_GIT_DIFFMEM_V1.md
│   │   ├── ВЕРСІОНУВАННЯ_ЛОГІКИ_АГЕНТА_V1.md
│   │   ├── DRAKON_ІНТЕГРАЦІЯ_ТА_МОДЕЛЬ_ВИКОНАННЯ_АГЕНТА.md
│   │   └── ADR_ФЕДЕРАТИВНА_СИСТЕМА_КОМЕНТАРІВ.md
│   │
│   ├── non-functional/                   <-- non-functional requirements
│   │   └── _INDEX.md (+ 6 specs)
│   │
│   ├── governance/                       <-- system evolution governance
│   │   └── _INDEX.md (+ 5 specs)
│   │
│   ├── runtime/                          <-- BLOOM Runtime integration (NEW)
│   │   └── INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md
│
├── runtime/                              <-- Runtime Operations (NEW)
│   └── operations/
│       ├── RUNTIME_DEPLOYMENT_STATE_ALPINE.md    <-- canonical deployed state
│       ├── RUNTIME_EXECUTION_PATH_VERIFICATION.md
│       └── RUNTIME_GAPS_AND_NEXT_STEPS.md
│   │
│   └── historical/                       <-- archive (provenance only)
│
├── integration/                          <-- integration layer
│   ├── _INDEX.md
│   ├── ІНТЕГРАЦІЯ_MEMBRIDGE.md
│   ├── ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND.md
│   ├── ІНТЕГРАЦІЯ_MEMORY_BACKEND.md
│   ├── ІНТЕГРАЦІЯ_FRONTEND_LOVABLE.md
│   ├── RUNTIME_TOPOLOGY_NOTEBOOKLM.md
│   ├── JOB_QUEUE_ТА_ARTIFACT_MODEL.md
│   ├── DEPLOYMENT_REPLIT_АРХІТЕКТУРА.md
│   └── ПЕРСПЕКТИВА_АГЕНТНОЇ_РОЗРОБКИ.md
│
├── audit/                                <-- documentation audit (NEW)
│   ├── _INDEX.md
│   ├── АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md
│   ├── МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md
│   └── ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md
│
├── operations/                           <-- operational directives
│   └── _INDEX.md (+ 5 docs)
│
├── backend/
│   └── _INDEX.md + КОНТРАКТИ_API_V1.md
│
├── frontend/
│   └── _INDEX.md (+ specs, ux-audit, ux-plan)
│
├── manifesto/                            <-- philosophy
│   ├── МАНІФЕСТ.md
│   ├── ФІЛОСОФІЯ_ВСЕ_Є_АГЕНТОМ.md
│   └── ГЛОСАРІЙ.md
│
├── product/
│   ├── СТРАТЕГІЯ_ПРОДУКТУ.md
│   └── МОДЕЛЬ_ДОСТУПУ.md
│
├── memory/                               <-- agent memory subsystem
│   └── README.md + ARCHITECTURE.md + API_CONTRACT.md
│
└── drakon/                               <-- DRAKON integration
    └── _INDEX.md (+ research docs)
```

---

## Reading Routes

### A. New Reader (from scratch)

```
1. manifesto/МАНІФЕСТ.md                                       -- why and what for
2. architecture/foundation/АРХІТЕКТУРНИЙ_КОРІНЬ.md             -- axioms, roles, canonical flow
3. architecture/core/КАНОНІЧНА_АРХІТЕКТУРА_ВИКОНАННЯ.md        -- full architecture
4. architecture/core/КОНТРАКТ_АГЕНТА_V1.md                     -- what is an agent
5. architecture/core/КАНОНІЧНИЙ_КОНВЕЄР_ВИКОНАННЯ.md           -- how a run executes
```

### B. Frontend Developer (Lovable)

```
1. operations/ІНДЕКС_АРХІТЕКТУРИ_ВИКОНАННЯ.md                  -- orientation
2. operations/INBOX_ТА_ЦИКЛ_ЗАПУСКУ_V1.md                      -- lifecycle for UI
3. operations/СИСТЕМА_PROPOSAL_V1.md                           -- Proposal state machine
4. backend/КОНТРАКТИ_API_V1.md                                 -- API schemas
5. frontend/LOVABLE_УЗГОДЖЕННЯ_З_АРХІТЕКТУРОЮ_ВИКОНАННЯ.md     -- architecture contract
```

### C. Backend / Gateway Developer

```
1. architecture/core/КАНОНІЧНА_АРХІТЕКТУРА_ВИКОНАННЯ.md        -- general architecture
2. architecture/core/КАНОНІЧНА_МОДЕЛЬ_АВТОРИТЕТУ_СХОВИЩА.md    -- who writes/reads what
3. backend/КОНТРАКТИ_API_V1.md                                 -- API contracts
4. architecture/non-functional/БЕЗПЕКА_СИСТЕМИ.md              -- security
```

### D. Runtime / Orchestration Developer

```
1. architecture/core/АБСТРАКЦІЯ_РІВНЯ_ОРКЕСТРАЦІЇ.md           -- vendor-agnostic contract
2. architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md -- Claude CLI Proxy spec (NEW)
3. integration/ІНТЕГРАЦІЯ_MEMBRIDGE.md                         -- Membridge Control Plane
4. integration/JOB_QUEUE_ТА_ARTIFACT_MODEL.md                  -- task state machines
5. architecture/core/КАНОНІЧНИЙ_КОНВЕЄР_ВИКОНАННЯ.md           -- pipeline steps
```

### E. Operations Engineer (Alpine deployment)

```
1. runtime/operations/RUNTIME_DEPLOYMENT_STATE_ALPINE.md       -- what is running and where
2. runtime/operations/RUNTIME_EXECUTION_PATH_VERIFICATION.md   -- what works, what doesn't
3. runtime/operations/RUNTIME_GAPS_AND_NEXT_STEPS.md           -- what to fix and in what order
```

### F. Documentation Auditor

```
1. audit/_INDEX.md                                             -- audit package index (NEW)
2. audit/МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md                          -- terminology matrix (NEW)
3. audit/АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md                -- full audit report (NEW)
4. audit/ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md                       -- gaps and plan (NEW)
```

---

## Runtime Integration (NEW)

The BLOOM Runtime delegates LLM execution to Membridge worker nodes. Key documents:

| Document | Purpose |
|----------|---------|
| [architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md](architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md) | Full spec: roles, envelopes, leases, security, worker invocation |
| [integration/ІНТЕГРАЦІЯ_MEMBRIDGE.md](integration/ІНТЕГРАЦІЯ_MEMBRIDGE.md) | Membridge Control Plane contract |
| [integration/JOB_QUEUE_ТА_ARTIFACT_MODEL.md](integration/JOB_QUEUE_ТА_ARTIFACT_MODEL.md) | Task state machines, artifact model |

---

## Runtime Operations (NEW)

Production deployment state, execution path verification, and gap analysis for the Alpine Linux deployment.

| Document | Purpose |
|----------|---------|
| [runtime/operations/RUNTIME_DEPLOYMENT_STATE_ALPINE.md](runtime/operations/RUNTIME_DEPLOYMENT_STATE_ALPINE.md) | Canonical deployment state: topology, services, API, storage, security, readiness |
| [runtime/operations/RUNTIME_EXECUTION_PATH_VERIFICATION.md](runtime/operations/RUNTIME_EXECUTION_PATH_VERIFICATION.md) | Actual execution path: live vs implemented vs missing |
| [runtime/operations/RUNTIME_GAPS_AND_NEXT_STEPS.md](runtime/operations/RUNTIME_GAPS_AND_NEXT_STEPS.md) | Critical gaps (persistence, auth, workers) + prioritized remediation |

---

## Audit Pack (NEW)

Documentation audit results from the BLOOM rebranding:

| Document | Purpose |
|----------|---------|
| [audit/_INDEX.md](audit/_INDEX.md) | Audit package index |
| [audit/АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md](audit/АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md) | Full rebranding audit report |
| [audit/МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md](audit/МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md) | Legacy to canonical term mapping |
| [audit/ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md](audit/ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md) | Documentation gaps and remediation plan |

---

## Membridge Operational Docs

| Document | Purpose |
|----------|---------|
| [leadership.md](leadership.md) | Primary/Secondary model, lease management |
| [auto-heartbeat.md](auto-heartbeat.md) | Heartbeat protocol, auto-registration |
| [web-ui.md](web-ui.md) | Control Plane web interface |
| [sync-modes.md](sync-modes.md) | Push/pull synchronization modes |
| [migration.md](migration.md) | Migration to leadership model |

---

## Semantic Relations

**This document is the master entry point for:**
- All documentation packages listed above

**Depends on:**
- [[architecture/foundation/АРХІТЕКТУРНИЙ_КОРІНЬ.md]] -- Axioms A1-A7
- [[manifesto/ГЛОСАРІЙ.md]] -- Canonical terminology
```
---
### web-ui.md
**Розмір:** 2,321 байт
```text
# Membridge Web UI

A minimal single-file web interface for the control-plane, served directly from
FastAPI on port 8000. No build step, no Node.js required.

## Access

```
http://<host>:8000/ui
```

The browser is redirected automatically to `/static/ui.html`.

## Features

| Panel | Endpoint |
|---|---|
| Projects sidebar | `GET /projects` |
| Leadership card | `GET /projects/{cid}/leadership` |
| Nodes table | `GET /projects/{cid}/nodes` |
| Promote primary | `POST /projects/{cid}/leadership/select` |

Auto-refresh every 10 seconds while a project is selected.

## Auto-population via heartbeat

Projects appear in the sidebar **automatically** once `membridge-agent` is
running and has registered at least one project. No manual API calls needed:

1. Hooks (`claude-mem-hook-pull` / `claude-mem-hook-push`) call
   `POST /register_project` on the local agent when a Claude session starts/stops.
2. The agent's heartbeat loop sends project info to the control-plane every
   `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS` (default: 10 s).
3. The control-plane stores the project in `_heartbeat_projects`.
4. `GET /projects` merges manually-created and heartbeat-discovered projects.

See [docs/auto-heartbeat.md](auto-heartbeat.md) for full details and troubleshooting.

## Authentication

All API calls include the `X-MEMBRIDGE-ADMIN` header.
The key is **never** stored on the server side by the UI — it lives only in
`sessionStorage` (cleared when the tab is closed).

1. Open `/ui` in the browser.
2. Paste the value of `MEMBRIDGE_ADMIN_KEY` into the **Admin Key** field.
3. Click **Save** (or **Test** to verify without loading data).

## Architecture

```
FastAPI (port 8000)
  GET  /ui              → 307 → /static/ui.html
  GET  /static/ui.html  → server/static/ui.html  (auth-exempt)
```

Auth middleware exemptions (no `X-MEMBRIDGE-ADMIN` required):

- `/health`, `/docs`, `/openapi.json`, `/redoc`
- `/ui`
- `/static/*`

## Implementation files

| File | Purpose |
|---|---|
| `server/static/ui.html` | Single-file SPA (vanilla HTML + JS + CSS) |
| `server/main.py` | Mounts `StaticFiles` at `/static`, adds `/ui` redirect |
| `server/auth.py` | Auth exemptions for `/ui` and `/static/*` |

## Related

- Interactive API docs: `http://<host>:8000/docs`
- Health endpoint: `http://<host>:8000/health`
```
---
### arm64-claude-mem.md
**Розмір:** 6,653 байт
```text
# ARM64 claude-mem: Known Issues & Fixes

Reference for deploying `claude-mem` on ARM64 Linux (Orange Pi, Raspberry Pi,
Ampere, etc.).  All issues here are non-fatal from the membridge-agent
perspective — agent heartbeats and project sync continue to work — but they
produce noisy errors in Claude Code CLI Stop hooks.

> **Quick check:** run `scripts/verify_claude_mem.sh` to detect all three
> issues automatically.

---

## Symptom A: "bun-runner.js not found" at Stop hook

### What you see

```
error: non-blocking stop hook failed
  command: node "…/scripts/bun-runner.js" "…/worker-service.cjs" start
  error: No such file or directory
```

### Root cause

`~/.claude/plugins/installed_plugins.json` contains a stale `installPath` or
`version` that no longer matches what is actually present in the plugin cache.

Example of a broken state:

```json
// installed_plugins.json says:
"installPath": "~/.claude/plugins/cache/thedotmack/claude-mem/9.0.5"

// But on disk only this exists:
~/.claude/plugins/cache/thedotmack/claude-mem/10.0.7/
```

Claude Code expands `${CLAUDE_PLUGIN_ROOT}` from `installPath`, so the hook
command resolves to a non-existent path.

### How to verify

```bash
# 1. What does the registry say?
grep -A4 '"version"' ~/.claude/plugins/installed_plugins.json

# 2. What is actually on disk?
ls ~/.claude/plugins/cache/thedotmack/claude-mem/

# 3. Does bun-runner.js exist at the path from the registry?
INSTALL_PATH=$(python3 -c "
import json, os
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
entries = d['plugins'].get('claude-mem@thedotmack', [])
if entries: print(entries[0]['installPath'])
" 2>/dev/null)
ls "${INSTALL_PATH}/scripts/bun-runner.js" 2>/dev/null || echo "NOT FOUND at $INSTALL_PATH"
```

### How to fix

**Option 1 — Reinstall via CLI (recommended)**

```
/plugin install claude-mem
```

This updates `installed_plugins.json` to match the downloaded cache.

**Option 2 — Manual correction (no internet required)**

```bash
# Back up first
cp ~/.claude/plugins/installed_plugins.json \
   ~/.claude/plugins/installed_plugins.json.bak.$(date +%Y%m%d-%H%M%S)

# Find the real version on disk
REAL_VER=$(ls ~/.claude/plugins/cache/thedotmack/claude-mem/ | sort -V | tail -1)
REAL_PATH="$HOME/.claude/plugins/cache/thedotmack/claude-mem/$REAL_VER"

# Edit installed_plugins.json: set installPath → $REAL_PATH and version → $REAL_VER
# (use your preferred editor — jq in-place, sed, or a text editor)
```

After either fix, restart Claude Code CLI and the Stop hook errors will stop.

---

## Symptom B: bun crashes with "Illegal instruction" or "Exec format error"

### What you see

```
/home/user/.bun/bin/bun: Exec format error
# or
bun: Illegal instruction
# or (from bun-runner.js logs)
Failed to start: Process died during startup
```

### Root cause

`~/.bun/bin/bun` is the wrong binary for the current CPU:

| Scenario | What happened |
|---|---|
| Installed `bun` npm package on Windows, then rsynced home dir to ARM64 | `~/.bun/bin/bun` → `…/bun.exe` (Windows PE) |
| Installed bun on x86_64, then migrated to ARM64 host | `~/.bun/bin/bun` is an ELF x86_64 binary |
| Installed bun via npm on Linux | npm only ships the native CLI shim; actual bun runtime is absent |

### How to verify

```bash
# Check what the binary actually is
ls -la ~/.bun/bin/bun            # symlink target?
readelf -h ~/.bun/bin/bun 2>/dev/null | grep -E 'Class|Machine'
# ARM64 correct output:  Machine: AArch64
# x86_64 output:         Machine: Advanced Micro Devices X86-64
# Windows PE: readelf will report "not an ELF file"

# Quick smoke test
~/.bun/bin/bun --version 2>&1   # "1.x.y" is good, error is bad
~/.bun/bin/bun --print "process.arch" 2>&1  # should print "arm64"
```

### How to fix

**Option 1 — Official installer (recommended)**

Requires `unzip` (`apt install unzip` / `apk add unzip`):

```bash
curl -fsSL https://bun.sh/install | bash
```

**Option 2 — Download binary directly (no unzip needed)**

```bash
# Uses Python's built-in zipfile module — no extra tools required
python3 - <<'EOF'
import urllib.request, zipfile, io, os, stat

url = "https://github.com/oven-sh/bun/releases/latest/download/bun-linux-aarch64.zip"
print(f"Downloading {url} ...")
with urllib.request.urlopen(url, timeout=60) as resp:
    data = resp.read()

z = zipfile.ZipFile(io.BytesIO(data))
bun_entry = next(n for n in z.namelist() if n.endswith("/bun") or n == "bun")
dest = os.path.expanduser("~/.bun/bin/bun")
os.makedirs(os.path.dirname(dest), exist_ok=True)
with open(dest, "wb") as f:
    f.write(z.read(bun_entry))
os.chmod(dest, stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH)
print(f"Installed to {dest}")
EOF

~/.bun/bin/bun --version  # verify
```

> **Note for x86_64 ARM emulation users:** replace `bun-linux-aarch64.zip`
> with `bun-linux-x64.zip` if running under QEMU x86_64 emulation.

---

## Quick verification checklist

Run these five commands to confirm a healthy setup:

```bash
# 1. Plugin metadata points to a real directory
python3 -c "
import json, os, sys
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
p = d['plugins'].get('claude-mem@thedotmack', [{}])[0].get('installPath', '')
ok = os.path.isdir(p)
print(('OK' if ok else 'FAIL'), 'installPath:', p)
sys.exit(0 if ok else 1)
"

# 2. bun-runner.js exists at that path
PLUGIN_ROOT=$(python3 -c "
import json, os
d = json.load(open(os.path.expanduser('~/.claude/plugins/installed_plugins.json')))
print(d['plugins'].get('claude-mem@thedotmack', [{}])[0].get('installPath', ''))
" 2>/dev/null)
ls "${PLUGIN_ROOT}/scripts/bun-runner.js" && echo "OK bun-runner.js" || echo "FAIL bun-runner.js missing"

# 3. bun binary is present
BUN=$(command -v bun || echo "$HOME/.bun/bin/bun")
test -x "$BUN" && echo "OK bun found: $BUN" || echo "FAIL bun not found"

# 4. bun is the right architecture
"$BUN" --print "process.arch + ' ' + process.platform" 2>&1

# 5. Worker starts cleanly
node "${PLUGIN_ROOT}/scripts/bun-runner.js" "${PLUGIN_ROOT}/scripts/worker-service.cjs" start 2>&1
```

All five should succeed with no errors. Or just run:

```bash
bash scripts/verify_claude_mem.sh
```

---

## Safety notes

- **Never commit `~/.claude/` contents** — they contain plugin keys and session data.
- **`verify_claude_mem.sh` is read-only** — it only reads and reports, never
  modifies `~/.claude/` or `~/.bun/`.
- Fix scripts above do write to `~/.bun/bin/bun` and
  `~/.claude/plugins/installed_plugins.json` — always back up first.
- Do not include bun binary paths or plugin keys in bug reports or log pastes.
```
---
### auto-heartbeat.md
**Розмір:** 5,043 байт
```text
# Auto-Heartbeat & Project Auto-Registration

Membridge agents automatically announce themselves to the control-plane and
register known projects, so the Web UI populates without any manual steps.

## How it works

```
┌──────────────────────┐   POST /agent/heartbeat   ┌──────────────────────┐
│  membridge-agent     │ ──────────────────────────▶│  membridge-server    │
│  (port 8001)         │  {node_id, canonical_id,   │  (port 8000)         │
│                      │   project_id, ip_addrs, …} │                      │
│  every HEARTBEAT_    │                             │  → _nodes[]          │
│  INTERVAL_SECONDS    │                             │  → _heartbeat_       │
│  (default: 10 s)     │                             │    projects[]        │
└──────────────────────┘                             └──────────────────────┘
         ▲
         │ POST /register_project (localhost, no auth)
┌──────────────────────┐
│  hooks               │
│  (claude-mem-hook-   │
│   pull / push)       │
└──────────────────────┘
```

1. Hooks call `POST /register_project` on the local agent — project is persisted
   to `~/.membridge/agent_projects.json`.
2. The heartbeat loop reads that file every tick and sends one heartbeat per
   project to the control-plane.
3. The control-plane stores projects in `_heartbeat_projects` (in-memory).
4. `GET /projects` merges manually-created and heartbeat-discovered projects.
5. The Web UI (`/ui`) auto-populates.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS` | `10` | Seconds between heartbeat ticks |
| `MEMBRIDGE_SERVER_URL` | `http://127.0.0.1:8000` | Control-plane base URL |
| `MEMBRIDGE_NODE_ID` | `platform.node()` | Stable node identifier (hostname) |
| `MEMBRIDGE_SERVER_ADMIN_KEY` | *(falls back to `MEMBRIDGE_ADMIN_KEY`)* | Admin key used to authenticate heartbeats with the server |
| `MEMBRIDGE_PROJECTS_FILE` | `~/.membridge/agent_projects.json` | Path to local project registry |

Set these in `.env.agent` (already loaded by `run-agent.sh`).

## Registering a project manually

```bash
# From any localhost process (hooks, scripts — no key required):
curl -s -X POST http://127.0.0.1:8001/register_project \
  -H "Content-Type: application/json" \
  -d '{"project_id": "garden-seedling"}'

# From a remote host (key required):
curl -s -X POST http://192.168.3.184:8001/register_project \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-AGENT: $MEMBRIDGE_AGENT_KEY" \
  -d '{"project_id": "garden-seedling", "path": "/home/vokov/projects/garden-seedling"}'
```

## Checking agent status

```bash
curl -s http://127.0.0.1:8001/health | jq .
# → shows: heartbeat_interval, server_url, projects_count

curl -s http://127.0.0.1:8001/projects
# → list of projects in agent's local registry
```

## Checking server state

```bash
ADMIN_KEY="$(grep MEMBRIDGE_ADMIN_KEY ~/.membridge-server.env | cut -d= -f2)"
curl -s http://127.0.0.1:8000/projects \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" | jq .
```

## Troubleshooting

**Web UI shows "No projects yet"**

1. Check agent is running: `rc-service membridge-agent status`
2. Check agent health: `curl -s http://127.0.0.1:8001/health`
3. Check `projects_count` in health response — is it > 0?
4. Register a project manually (see above) and wait one heartbeat tick
5. Check server logs: `rc-service membridge-server status` or agent log

**Heartbeat disabled warning in agent logs**

Set `MEMBRIDGE_SERVER_ADMIN_KEY` in `.env.agent`. It is typically the same
value as `MEMBRIDGE_ADMIN_KEY` on the server.

**Stop hook error: "bun-runner.js not found"**

This is a claude-mem plugin issue, not a membridge-agent issue.  Common on
ARM64 machines (Orange Pi, Raspberry Pi) and after plugin upgrades.

Run the read-only verifier to diagnose:

```bash
bash scripts/verify_claude_mem.sh
```

Exit code tells you what's wrong (10 = stale plugin metadata, 11 = bun missing,
12 = wrong bun architecture, 13 = bun-runner.js absent).  Full root-cause
analysis and step-by-step fixes: [`docs/arm64-claude-mem.md`](arm64-claude-mem.md).

**Projects disappear after server restart**

The control-plane stores heartbeat projects in-memory. They reappear after the
next heartbeat cycle (≤ `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS`).

## Security notes

- `/register_project` on the agent is **auth-exempt for localhost** connections
  (127.0.0.1 / ::1). Remote calls require `X-MEMBRIDGE-AGENT` header.
- Heartbeats are sent with `X-MEMBRIDGE-ADMIN` — keep `MEMBRIDGE_SERVER_ADMIN_KEY`
  out of version control (use `.env.agent`, already in `.gitignore`).
```
---
### leadership.md
**Розмір:** 6,030 байт
```text
# Leadership: Primary / Secondary Model

Membridge implements a **single-source-of-truth** model for multi-node sync.
One node is the **Primary** — it owns the canonical copy of the SQLite DB in MinIO.
All other nodes are **Secondaries**.

---

## Core Policy

| Rule | Primary | Secondary |
|------|---------|-----------|
| Write local SQLite | ✅ allowed | ✅ allowed |
| Push to MinIO | ✅ allowed | ❌ blocked by default |
| Pull from MinIO | ⚠️ refused if local DB exists (see below) | ✅ allowed (with backup) |
| Steal stale push lock | ✅ allowed | ❌ blocked |

### Why Primary Refuses Pull Overwrite

The primary node is the source of truth. If remote SHA differs from local SHA:
- It means a secondary pushed (or a manual write happened).
- Silently overwriting the primary's local DB would destroy canonical data.
- Instead: the drift is logged and a manual resolution is required.

Override for inspection (unsafe): `ALLOW_PRIMARY_PULL_OVERRIDE=1`

### Why Secondary Cannot Push

A secondary may have local writes (write-local is allowed), but pushing would
overwrite the primary's canonical copy. This is blocked by default.

Override (unsafe): `ALLOW_SECONDARY_PUSH=1`

---

## Leadership Lease

Stored at `projects/<canonical_id>/leadership/lease.json` in MinIO.

```json
{
  "canonical_id": "abc123def456abcd",
  "primary_node_id": "rpi4b",
  "issued_at": 1706000000,
  "expires_at": 1706003600,
  "lease_seconds": 3600,
  "epoch": 3,
  "policy": "primary_authoritative",
  "issued_by": "rpi4b",
  "needs_ui_selection": false
}
```

### Fields

| Field | Description |
|-------|-------------|
| `canonical_id` | SHA256(project_name)[:16] |
| `primary_node_id` | Hostname (or `MEMBRIDGE_NODE_ID`) of the primary |
| `issued_at` / `expires_at` | Unix timestamps |
| `lease_seconds` | TTL (default 3600s) |
| `epoch` | Monotonically increasing; increments on each renewal |
| `policy` | Always `primary_authoritative` for now |
| `issued_by` | Node that wrote this lease |
| `needs_ui_selection` | `true` when bootstrapped without `PRIMARY_NODE_ID` set |

### Audit Log

Every lease write appends to:
```
projects/<canonical_id>/leadership/audit/<YYYYMMDDTHHMMSSZ>-<node_id>.json
```

---

## How Role is Determined

1. Read `lease.json` from MinIO.
2. If absent → create default lease (primary = `PRIMARY_NODE_ID` env var or current node).
3. If expired:
   - If `PRIMARY_NODE_ID` matches current node → renew with `epoch+1`.
   - Otherwise → re-read to see if another node already renewed.
   - If still expired → current node is secondary.
4. If valid → role = primary if `primary_node_id == NODE_ID`, else secondary.

**Node ID** = `MEMBRIDGE_NODE_ID` env var, fallback to `platform.node()` (hostname).

---

## How to Select Primary

### Via curl (control plane API)

```bash
# First: find the canonical_id
python3 sqlite_minio_sync.py print_project

# Set primary
curl -X POST http://SERVER:8000/projects/<canonical_id>/leadership/select \
  -H 'Content-Type: application/json' \
  -H 'X-MEMBRIDGE-ADMIN: <ADMIN_KEY>' \
  -d '{"primary_node_id": "rpi4b", "lease_seconds": 7200}'

# View current leadership
curl http://SERVER:8000/projects/<canonical_id>/leadership \
  -H 'X-MEMBRIDGE-ADMIN: <ADMIN_KEY>'
```

### Via env var (persistent)

```bash
# In config.env on the primary node:
PRIMARY_NODE_ID=rpi4b
```

The node will auto-create or renew the lease on each sync operation.

### Via leadership_info command

```bash
python3 sqlite_minio_sync.py leadership_info
```

---

## Heartbeat API

Agents can register themselves with the control plane:

```bash
curl -X POST http://SERVER:8000/agent/heartbeat \
  -H 'Content-Type: application/json' \
  -H 'X-MEMBRIDGE-ADMIN: <ADMIN_KEY>' \
  -d '{
    "node_id": "rpi4b",
    "canonical_id": "abc123def456abcd",
    "obs_count": 1234,
    "db_sha": "deadbeef...",
    "ip_addrs": ["192.168.1.10"]
  }'
```

---

## Failover / Promotion

Membridge MVP uses **manual failover**:

1. Current primary goes offline or becomes stale.
2. Lease expires (default TTL: 3600s).
3. Admin promotes a secondary:
   ```bash
   curl -X POST http://SERVER:8000/projects/<cid>/leadership/select \
     -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
     -d '{"primary_node_id": "new-primary-node"}'
   ```
4. New primary sets `PRIMARY_NODE_ID=new-primary-node` in its `config.env` and runs a push.

---

## Stale Lock vs Stale Lease

| Concept | Path | TTL | Purpose |
|---------|------|-----|---------|
| Push lock | `projects/<cid>/locks/active.lock` | `LOCK_TTL_SECONDS` (2h) | Prevent concurrent pushes |
| Leadership lease | `projects/<cid>/leadership/lease.json` | `LEADERSHIP_LEASE_SECONDS` (1h) | Determine primary/secondary role |

These are independent. A secondary with `ALLOW_SECONDARY_PUSH=1` still needs to acquire the push lock.

---

## Troubleshooting

### "Primary refuses pull overwrite"
The local DB and remote differ. Primary will NOT auto-pull. Options:
- Check which is newer: `cm-doctor` shows obs counts
- If remote is authoritative: `ALLOW_PRIMARY_PULL_OVERRIDE=1 cm-pull`
- If you want the primary to hand off: promote another node

### "Secondary cannot push"
Expected behavior. Either:
- Promote this node: `POST /projects/<cid>/leadership/select`
- Or set `ALLOW_SECONDARY_PUSH=1` (breaks single-source-of-truth guarantee)

### "Lock stuck"
- Check age: `cm-doctor` → `[3/5] Lock status`
- If expired (> TTL + grace): next push will steal it
- Force steal: `FORCE_PUSH=1 cm-push`

### "needs_ui_selection=true in lease"
No `PRIMARY_NODE_ID` was set when the lease was bootstrapped.
Set it explicitly:
```bash
curl -X POST http://SERVER:8000/projects/<cid>/leadership/select \
  -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
  -d '{"primary_node_id": "rpi4b"}'
```

### "Secondary ahead" (secondary has more obs than remote)
Secondary wrote locally but cannot push. Options:
- Promote secondary to primary, then push
- Manually copy the secondary DB to primary, then push from primary
- Accept loss of secondary-only data (do a fresh pull on secondary)
```
---
### migration.md
**Розмір:** 4,520 байт
```text
# Migration Guide: Upgrading to Primary/Secondary Leadership

This guide covers migrating from pre-leadership Membridge (≤ v0.3.x) to the
Primary/Secondary model introduced in v0.4.0.

---

## What Changed

| Area | Before | After |
|------|--------|-------|
| Push | Any node can push | Only primary can push (secondary blocked) |
| Pull | Any node can pull-overwrite | Primary refuses pull-overwrite; secondary pulls with backup |
| Config | No role concept | `PRIMARY_NODE_ID` env var or lease in MinIO |
| MinIO layout | `projects/<cid>/sqlite/` | + `projects/<cid>/leadership/` |

---

## Migration Steps

### Step 1: Identify your primary node

The primary is the node with the most up-to-date DB (most observations, most recent push).

```bash
# On each node, check obs count:
python3 sqlite_minio_sync.py doctor   # shows [4/5] SQLite DB health → observations
```

### Step 2: Set PRIMARY_NODE_ID on the primary node

```bash
# In ~/.claude-mem-minio/config.env on the primary node:
echo "PRIMARY_NODE_ID=$(hostname)" >> ~/.claude-mem-minio/config.env
```

### Step 3: Bootstrap the leadership lease

```bash
# On the primary node:
python3 sqlite_minio_sync.py leadership_info
```

This creates `projects/<canonical_id>/leadership/lease.json` in MinIO.

### Step 4: Push from primary to establish canonical state

```bash
cm-push   # or: python3 sqlite_minio_sync.py push_sqlite
```

### Step 5: Pull on all secondary nodes

```bash
# On each secondary node:
cm-pull   # or: python3 sqlite_minio_sync.py pull_sqlite
```

The secondary will detect its role automatically (lease exists, its hostname ≠ primary).

### Step 6: Verify

```bash
# On all nodes:
python3 sqlite_minio_sync.py doctor
# Check [+] Leadership section:
#   role:     primary   (or secondary)
#   primary:  rpi4b
#   epoch:    1
```

---

## Rollback (disable leadership gates)

If you need to roll back to the old behavior without role enforcement:

```bash
# In config.env on all nodes:
LEADERSHIP_ENABLED=0
```

This bypasses all role checks. Push and pull work as before v0.4.0.

---

## Backward Compatibility

- `LEADERSHIP_ENABLED=0` fully disables the feature.
- Existing MinIO data (`projects/<cid>/sqlite/`) is untouched.
- The leadership prefix (`projects/<cid>/leadership/`) is new; old clients ignore it.
- Exit codes 2 (primary pull refused) and 3 (secondary push blocked) are new.
  Hook scripts that check `$?` may need updating.

---

## Hook Script Update

If your hooks check exit codes (e.g., `~/.claude-mem-minio/bin/claude-mem-pull`):

```bash
# Before (old):
python3 sqlite_minio_sync.py pull_sqlite || echo "PULL FAILED"

# After (new): handle exit code 2 (primary gate) separately
python3 sqlite_minio_sync.py pull_sqlite
rc=$?
if [ $rc -eq 0 ]; then
  echo "PULL OK"
elif [ $rc -eq 2 ]; then
  echo "PULL SKIPPED: primary node refused overwrite (this is normal)"
else
  echo "PULL FAILED with exit code $rc"
fi
```

Similarly for push (exit code 3 = secondary blocked):

```bash
python3 sqlite_minio_sync.py push_sqlite
rc=$?
if [ $rc -eq 0 ]; then
  echo "PUSH OK"
elif [ $rc -eq 3 ]; then
  echo "PUSH SKIPPED: secondary node blocked (this is normal)"
else
  echo "PUSH FAILED with exit code $rc"
fi
```

---

## Control Plane API (optional)

If you run the Membridge server (`server/main.py`), new endpoints are available:

```bash
# Register heartbeat (from each node's startup hook):
curl -X POST http://SERVER:8000/agent/heartbeat \
  -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"node_id":"rpi4b","canonical_id":"<cid>","obs_count":1234}'

# View all nodes for a project:
curl http://SERVER:8000/projects/<cid>/nodes -H 'X-MEMBRIDGE-ADMIN: <KEY>'

# View leadership state:
curl http://SERVER:8000/projects/<cid>/leadership -H 'X-MEMBRIDGE-ADMIN: <KEY>'

# Set primary (admin action):
curl -X POST http://SERVER:8000/projects/<cid>/leadership/select \
  -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"primary_node_id":"rpi4b","lease_seconds":7200}'
```

All leadership endpoints are protected by the same `MEMBRIDGE_ADMIN_KEY` as other
admin endpoints (bypassed in `MEMBRIDGE_DEV=1` mode).

---

## Quickstart for New Deployments

See `docs/leadership.md` for the complete reference.

Short version:

```bash
# 1. Set on primary node in config.env:
PRIMARY_NODE_ID=<hostname>

# 2. Push from primary:
cm-push

# 3. Pull on secondaries (auto-detects secondary role):
cm-pull

# 4. Check everything:
python3 sqlite_minio_sync.py doctor
```
```
---
### sync-modes.md
**Розмір:** 4,201 байт
```text
# Sync Modes

Membridge supports two sync operations: **pull** and **push**, each with different
behavior depending on the node's **leadership role** (primary or secondary).

---

## Push

**Purpose:** Upload the local SQLite DB snapshot to MinIO (makes it the canonical remote copy).

### Primary push (allowed)

1. Check leadership role → primary ✅
2. Stop worker (for consistent snapshot)
3. `VACUUM INTO` temp snapshot + integrity check
4. Restart worker (independent of upload)
5. Compute SHA256 of snapshot
6. Compare with remote SHA256 (skip if identical)
7. Acquire distributed push lock
8. Upload DB + SHA256 + manifest to MinIO
9. Verify remote SHA256

### Secondary push (blocked)

```
[0/6] Leadership: role=secondary  node=mynode  primary=rpi4b
  SECONDARY: push blocked by default.
  Options:
    - Request promotion: POST /projects/<cid>/leadership/select
    - Override (unsafe): ALLOW_SECONDARY_PUSH=1
```

Exit code 3.

### Env vars affecting push

| Var | Default | Effect |
|-----|---------|--------|
| `ALLOW_SECONDARY_PUSH` | `0` | Allow secondary to push (unsafe) |
| `FORCE_PUSH` | `0` | Override active push lock |
| `LOCK_TTL_SECONDS` | `7200` | Push lock TTL |
| `STALE_LOCK_GRACE_SECONDS` | `60` | Grace period after lock expiry |
| `LEADERSHIP_ENABLED` | `1` | Disable all leadership checks if `0` |

---

## Pull

**Purpose:** Download the canonical DB from MinIO and replace the local copy.

### Secondary pull (allowed, with backup)

1. Check leadership role → secondary ✅
2. Download remote SHA256
3. Compare with local (skip if identical)
4. Download remote DB to temp file
5. Verify SHA256 of download
6. **Safety backup** of current local DB to `~/.claude-mem/backups/pull-overwrite/<ts>/`
7. Stop worker
8. Atomic replace local DB
9. Verify DB integrity + restart worker

### Primary pull (refused if local DB exists)

```
  SHA256 mismatch — pulling remote DB
  [leadership] role=primary  node=rpi4b  primary=rpi4b
  PRIMARY: refusing destructive pull overwrite of local DB.
    local_sha:  abc123...
    remote_sha: def456...
  Primary is the single source of truth — remote drift must be resolved manually.
  Options:
    - Inspect: download remote DB to a temp path and compare
    - Override (unsafe): ALLOW_PRIMARY_PULL_OVERRIDE=1
    - Handover: POST /projects/<cid>/leadership/select
```

Exit code 2.

**Exception:** If the local DB does not yet exist (first-time setup), the primary
can pull freely — there is nothing to protect.

### Env vars affecting pull

| Var | Default | Effect |
|-----|---------|--------|
| `ALLOW_PRIMARY_PULL_OVERRIDE` | `0` | Allow primary to pull-overwrite (unsafe) |
| `PULL_BACKUP_MAX_DAYS` | `14` | Delete backups older than N days |
| `PULL_BACKUP_MAX_COUNT` | `50` | Keep at most N pull backups |
| `MEMBRIDGE_NO_RESTART_WORKER` | `0` | Skip worker restart after pull |
| `LEADERSHIP_ENABLED` | `1` | Disable all leadership checks if `0` |

---

## SAFE-PULL Backups

Before every pull overwrite, the current local DB is backed up to:
```
~/.claude-mem/backups/pull-overwrite/<YYYYMMDD-HHMMSS>/
  claude-mem.db        # full copy of local DB before overwrite
  chroma.sqlite3       # vector DB (if present)
  manifest.json        # metadata: timestamps, SHAs, obs counts, local_ahead flag
```

Backups are retained for `PULL_BACKUP_MAX_DAYS` days and at most `PULL_BACKUP_MAX_COUNT` snapshots.

To restore from backup:
```bash
cp ~/.claude-mem/backups/pull-overwrite/<ts>/claude-mem.db ~/.claude-mem/claude-mem.db
```

---

## Write-Local Policy

Both primary and secondary nodes can write to the local SQLite DB at any time
(the worker and Claude CLI do this). This is intentional — local writes are always
allowed. The leadership gates only control **MinIO sync** (pull/push).

When a secondary has local writes not yet pushed:
- `cm-doctor` will show `local_ahead: YES`
- The secondary cannot push (blocked)
- To preserve secondary-only data: promote secondary to primary first

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or already up-to-date) |
| 1 | Error (MinIO, DB, config, etc.) |
| 2 | Primary pull refused (role gate) |
| 3 | Secondary push blocked (role gate) |
```
---
### runtime/operations/RUNTIME_EXECUTION_PATH_VERIFICATION.md
**Розмір:** 8,358 байт
```text
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
```
---
### runtime/operations/RUNTIME_DEPLOYMENT_STATE_ALPINE.md
**Розмір:** 16,709 байт
```text
---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
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
│  ┌────────────────────────────────▼──────────────────┐  │
│  │         MemStorage (in-memory)                    │  │
│  │  tasks / leases / workers / artifacts / audit     │  │
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
Auth: **none** (see Security section)

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

### Current Implementation: MemStorage

Class: `MemStorage` in `server/storage.ts`
Persistence: **none** — all data in Node.js process heap

```typescript
// All state lives here, lost on process exit
private users:     Map<string, User>
private workers:   Map<string, WorkerNode>
private tasks:     Map<string, LLMTask>
private leases:    Map<string, Lease>
private artifacts: Map<string, RuntimeArtifact>
private results:   Map<string, LLMResult>
private auditLogs: AuditLogEntry[]
private runtimeConfig: { membridge_server_url, admin_key, connected, last_test }
```

### Consequences of In-Memory Storage

| Event | Consequence |
|-------|-------------|
| `rc-service bloom-runtime restart` | All tasks, leases, workers, audit logs **lost** |
| Server crash | Same as restart |
| Node.js OOM | Same as restart |
| Machine reboot | Service auto-restarts (OpenRC default), state **lost** |
| `MEMBRIDGE_ADMIN_KEY` reload | Requires restart — config re-read only at startup |

**Operational implication:** bloom-runtime is currently **stateless across restarts**. It cannot replay tasks, recover in-progress runs, or preserve audit history.

### Missing Layer: Persistence

The schema is fully defined (`shared/schema.ts`, Drizzle ORM + `drizzle.config.ts`).
PostgreSQL tables exist as type definitions.
What is missing: a `DatabaseStorage` implementation replacing `MemStorage`.

See: [[RUNTIME_GAPS_AND_NEXT_STEPS.md#persistence-layer]]

---

## F. Security State

### Runtime API

| Control | Status | Notes |
|---------|--------|-------|
| Authentication on `/api/runtime/*` | ❌ **absent** | All endpoints publicly accessible |
| Authorization / RBAC | ❌ **absent** | No role checks |
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

## G. Operational Readiness Assessment

| Dimension | Score | Assessment |
|-----------|-------|-----------|
| **Architecture readiness** | 8/10 | Core architecture sound: Express + Vite + Membridge proxy pattern correct. Lease/task state machines complete. Worker selection with sticky routing implemented. Missing: persistence, auth middleware hooks. |
| **Execution readiness** | 4/10 | Pipeline implemented end-to-end in code, but cannot execute tasks because 0 workers registered. One worker registration makes the entire pipeline operational. |
| **Operational readiness** | 6/10 | Service auto-starts on boot (OpenRC default runlevel), logs in place, nginx proxy configured, env file secured. Missing: log rotation, health check endpoint (only `/` returns 200), alerting. |
| **Production readiness** | 3/10 | Not production-ready as-is. Critical gaps: no persistence (state lost on restart), no auth on API, no TLS, no rate limiting. Suitable for internal/development use behind a trusted network. |

---

## Semantic Relations

**This document depends on:**
- [[../../architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md]] — architectural spec for Claude CLI proxy
- [[../../integration/ІНТЕГРАЦІЯ_MEMBRIDGE.md]] — Membridge Control Plane contract

**This document is referenced by:**
- [[RUNTIME_EXECUTION_PATH_VERIFICATION.md]] — actual execution path trace
- [[RUNTIME_GAPS_AND_NEXT_STEPS.md]] — gaps and remediation
- [[../../ІНДЕКС.md]] — master index
```
---
### runtime/operations/RUNTIME_GAPS_AND_NEXT_STEPS.md
**Розмір:** 10,162 байт
```text
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
```
---
### audit/ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md
**Розмір:** 5,435 байт
```text
---
tags:
  - domain:meta
  - status:canonical
  - format:plan
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Gaps Analysis and Remediation Plan"
dg-publish: true
---

# Gaps Analysis and Remediation Plan

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Language: Ukrainian (canonical)

---

## 0. Purpose

This document identifies documentation gaps discovered during the BLOOM rebranding audit and provides a prioritized remediation plan. Each gap is categorized by severity and assigned a target resolution date.

---

## 1. Gap Inventory

### 1.1 Critical Gaps (P0) -- Resolved

| ID | Gap | Location | Impact | Resolution |
|----|-----|----------|--------|------------|
| G-001 | Runtime integration layer undocumented | `architecture/runtime/` | Workers have no spec to implement against | Created `INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md` |
| G-002 | No audit documentation exists | `audit/` | No traceability for terminology changes | Created audit package (this file + 2 others) |
| G-003 | Master index missing runtime section | `ІНДЕКС.md` | New runtime docs undiscoverable | Updated `ІНДЕКС.md` with runtime + audit sections |

### 1.2 High Priority Gaps (P1) -- Open

| ID | Gap | Location | Impact | Target |
|----|-----|----------|--------|--------|
| G-004 | Tier-2 frontend docs use legacy terminology | `frontend/` | Inconsistent terminology for Lovable developers | Next sprint |
| G-005 | Memory package uses mixed English/Ukrainian | `memory/` | Confusing for new contributors | Next sprint |
| G-006 | Operations docs reference pre-BLOOM state machines | `operations/` | Misalignment with canonical execution pipeline | Next sprint |

### 1.3 Medium Priority Gaps (P2) -- Open

| ID | Gap | Location | Impact | Target |
|----|-----|----------|--------|--------|
| G-007 | No worker implementation guide | `architecture/runtime/` | Workers must reverse-engineer spec from types | Q2 2026 |
| G-008 | DRAKON integration docs reference old agent contract | `drakon/` | Stale references to agent v1.0 (now v1.1) | Q2 2026 |
| G-009 | NotebookLM canonical set does not include runtime | `notebooklm/` | Runtime architecture absent from NLM knowledge | Q2 2026 |
| G-010 | No automated doc linting | CI/CD | Terminology drift detectable only by manual audit | Q3 2026 |

### 1.4 Low Priority Gaps (P3) -- Backlog

| ID | Gap | Location | Impact | Target |
|----|-----|----------|--------|--------|
| G-011 | Wikilinks not standardized (relative vs absolute) | All docs | Some links break in non-Obsidian readers | Backlog |
| G-012 | No documentation changelog | `audit/` | No history of doc mutations | Backlog |
| G-013 | Agent registry docs sparse | `agents/` | Only README exists | Backlog |

---

## 2. Remediation Plan

### Phase 1: Foundation (Completed)

- [x] Create `architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md`
- [x] Create `audit/_INDEX.md`
- [x] Create `audit/АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md`
- [x] Create `audit/МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md`
- [x] Create `audit/ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ.md` (this file)
- [x] Update `ІНДЕКС.md` with runtime and audit sections

### Phase 2: Terminology Alignment (Next Sprint)

- [ ] G-004: Update `frontend/LOVABLE_УЗГОДЖЕННЯ_З_АРХІТЕКТУРОЮ_ВИКОНАННЯ.md` terminology
- [ ] G-004: Update `frontend/ДИРЕКТИВА_УЗГОДЖЕННЯ_FRONTEND_V1.md` terminology
- [ ] G-004: Update `frontend/ПЛАН_МІГРАЦІЇ_FRONTEND_V1.md` terminology
- [ ] G-005: Standardize `memory/` package language to Ukrainian canonical
- [ ] G-006: Update `operations/СИСТЕМА_PROPOSAL_V1.md` state machine references
- [ ] G-006: Update `operations/INBOX_ТА_ЦИКЛ_ЗАПУСКУ_V1.md` execution references

### Phase 3: Extended Coverage (Q2 2026)

- [ ] G-007: Create worker implementation guide with code examples
- [ ] G-008: Update DRAKON docs to reference Agent Contract v1.1
- [ ] G-009: Add runtime docs to NotebookLM canonical set
- [ ] Verify all Tier-1 cross-references resolve correctly

### Phase 4: Automation (Q3 2026)

- [ ] G-010: Implement terminology linter (grep-based CI check)
- [ ] G-011: Standardize wikilink format
- [ ] G-012: Implement documentation changelog tracking
- [ ] G-013: Expand agent registry documentation

---

## 3. Success Criteria

| Metric | Current | Target |
|--------|---------|--------|
| Tier-1 docs using canonical terminology | 95% | 100% |
| Tier-2 docs using canonical terminology | 70% | 90% |
| Documentation gaps (P0/P1) | 0 P0, 3 P1 | 0 P0, 0 P1 |
| Cross-reference integrity | 94% | 100% |
| Runtime layer documentation | Complete | Complete |
| Audit trail documentation | Complete | Complete |

---

## 4. Ownership

| Phase | Owner | Reviewer |
|-------|-------|----------|
| Phase 1 | architect | -- (self-reviewed) |
| Phase 2 | doc-maintainer | architect |
| Phase 3 | implementer + architect | architect |
| Phase 4 | CI/CD engineer | architect |

---

## Semantic Relations

**This document is part of:**
- [[_INDEX]] -- Audit Pack index

**Depends on:**
- [[АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ]] -- Audit findings that inform this plan
- [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]] -- Term mappings used in remediation

**Referenced by:**
- [[ІНДЕКС]] -- Master documentation index
```
---
### audit/АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ.md
**Розмір:** 5,005 байт
```text
---
tags:
  - domain:meta
  - status:canonical
  - format:audit
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Audit: BLOOM Documentation Rebranding"
dg-publish: true
---

# Audit: BLOOM Documentation Rebranding

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Language: Ukrainian (canonical)

---

## 0. Context

Garden Bloom underwent a rebranding to establish **BLOOM** (Behavioral Logic Orchestration for Order-Made Systems) as the canonical name for the execution runtime. This audit documents the terminology alignment process, identifies remaining inconsistencies, and confirms that all canonical documents use standardized terminology.

---

## 1. Audit Methodology

1. Inventory all documentation files across `docs/` hierarchy
2. Identify legacy terminology (pre-BLOOM naming)
3. Map legacy terms to canonical BLOOM equivalents (see [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]])
4. Verify each Tier-1 document uses canonical terms
5. Flag Tier-2 documents that require updates
6. Document gaps in coverage (see [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]])

---

## 2. Scope

### 2.1 Documents audited

| Package | Files | Tier |
|---------|-------|------|
| `architecture/foundation/` | 2 | Tier 1 |
| `architecture/core/` | 8 | Tier 1 |
| `architecture/features/` | 4 | Tier 1 |
| `architecture/non-functional/` | 6 | Tier 1 |
| `architecture/governance/` | 5 | Tier 1/2 |
| `architecture/runtime/` | 1 | Tier 1 (new) |
| `architecture/historical/` | 2 | Archive |
| `operations/` | 5 | Tier 2 |
| `backend/` | 2 | Tier 1 |
| `frontend/` | 6 | Tier 2 |
| `integration/` | 7 | Tier 1 |
| `manifesto/` | 4 | Tier 1 |
| `product/` | 2 | Tier 1 |
| `memory/` | 6 | Tier 2 |
| `drakon/` | 5 | Tier 2 |
| `notebooklm/` | 7 | Tier 2 |
| Root-level docs | 5 | Mixed |

**Total: ~77 files audited**

### 2.2 Exclusions

- `_quarantine/` directory (archived, non-canonical)
- `architecture/historical/` (retained for provenance, not updated)

---

## 3. Findings

### 3.1 Terminology Alignment Status

| Category | Status | Notes |
|----------|--------|-------|
| System name: "Garden Bloom" | Retained | Garden Bloom is the product; BLOOM is the runtime |
| Runtime name: "BLOOM" | Canonical | Defined in `BLOOM_RUNTIME_IDENTITY.md` |
| Agent execution: "Execution Context" | Canonical | Aligned across all core docs |
| Memory: "claude-mem.db" vs "DiffMem" | Canonical | Two-memory axiom consistently applied |
| Orchestration: "Orchestration Layer" | Canonical | Vendor-agnostic abstraction documented |
| Proxy: "Claude CLI Proxy" | Canonical (new) | Documented in `INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md` |

### 3.2 Legacy Terms Found

See [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]] for the complete mapping. Summary:

- 12 legacy terms identified
- 8 terms already replaced in Tier-1 documents
- 4 terms remain in Tier-2 documents (scheduled for update)

### 3.3 Structural Issues

| Issue | Location | Severity | Resolution |
|-------|----------|----------|------------|
| Runtime layer undocumented | `architecture/runtime/` | High | Created `INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md` |
| No audit documentation | `audit/` | Medium | Created this audit package |
| Missing BLOOM identity link in INDEKS | `ІНДЕКС.md` | Low | Updated with runtime section |
| Broken semantic link to АРХІТЕКТУРНИЙ_КОРІНЬ | `integration/_INDEX.md` | Low | Verified as relative path issue |

### 3.4 Cross-Reference Integrity

All `[[wikilink]]` references in Tier-1 documents verified:
- 94% resolve correctly
- 6% use relative paths that work in Obsidian but not in plain Markdown readers
- No broken references to non-existent documents

---

## 4. Recommendations

### 4.1 Immediate (P0)

1. Ensure all new documents use canonical BLOOM terminology from creation
2. Update `docs/ІНДЕКС.md` to include runtime and audit sections

### 4.2 Short-term (P1)

1. Update remaining Tier-2 documents with canonical terminology
2. Add `architecture/runtime/` to the NotebookLM canonical set
3. Standardize wikilink format across all documents

### 4.3 Long-term (P2)

1. Implement automated terminology linting in CI
2. Generate documentation graph from semantic relations
3. Add changelog tracking for Tier-1 document mutations

---

## 5. Audit Trail

| Date | Action | Actor |
|------|--------|-------|
| 2026-02-24 | Initial audit conducted | architect |
| 2026-02-24 | Terminology matrix created | architect |
| 2026-02-24 | Gaps analysis completed | architect |
| 2026-02-24 | Runtime spec created | architect |

---

## Semantic Relations

**This document is part of:**
- [[_INDEX]] -- Audit Pack index

**Depends on:**
- [[manifesto/ГЛОСАРІЙ.md]] -- Canonical glossary
- [[architecture/foundation/BLOOM_RUNTIME_IDENTITY.md]] -- BLOOM identity definition

**Referenced by:**
- [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]] -- Uses findings from this audit
- [[ІНДЕКС]] -- Master documentation index
```
---
### audit/_INDEX.md
**Розмір:** 3,236 байт
```text
---
tags:
  - domain:meta
  - status:canonical
  - format:inventory
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Audit Pack -- Documentation Audit Index"
dg-publish: true
---

# Audit Pack -- Documentation Audit Index

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Language: Ukrainian (canonical)

---

## 0. Purpose

This package contains the results of the BLOOM rebranding documentation audit. It tracks terminology standardization, identifies gaps in documentation coverage, and provides a remediation plan.

All documents in this package use canonical BLOOM terminology as defined in the Glossary (`manifesto/ГЛОСАРІЙ.md`).

---

## 1. Manifest

| Document | Domain | Format | Purpose |
|----------|--------|--------|---------|
| [[АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ]] | `meta` | `audit` | Full audit report: Garden Seedling to BLOOM rebranding |
| [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]] | `meta` | `reference` | Term mapping matrix: old terms to canonical BLOOM terms |
| [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]] | `meta` | `plan` | Documentation gaps identified and remediation plan |

---

## 2. Reading Order

```
1. МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН        -- understand the terminology mapping first
2. АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ -- full audit findings
3. ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ      -- gaps and remediation plan
```

---

## 3. Audit Scope

The audit covers all documentation in the Garden Bloom / BLOOM system:

| Layer | Documents Audited | Status |
|-------|-------------------|--------|
| Foundation (Axioms, Identity) | 2 | Aligned |
| Core Architecture (Execution, Proposals) | 8 | Aligned |
| Features (Memory, Versioning, DRAKON) | 4 | Aligned |
| Non-Functional (Security, Performance) | 6 | Aligned |
| Governance (Multi-agent, Tagging) | 5 | Partially aligned |
| Operations (Proposals, Inbox) | 5 | Partially aligned |
| Frontend | 6 | Requires updates |
| Backend | 2 | Aligned |
| Integration (Membridge, NLM, Memory) | 7 | Aligned |
| Runtime (Claude CLI Proxy) | 1 | New (canonical) |
| Product (Strategy, Access Model) | 2 | Aligned |
| Manifesto (Philosophy, Glossary) | 4 | Aligned |

---

## 4. Key Findings Summary

1. **Terminology inconsistency:** 12 legacy terms identified that require replacement with canonical BLOOM equivalents
2. **Missing documentation:** Runtime integration layer (Claude CLI Proxy) was undocumented -- now covered
3. **Audit trail gaps:** No formal audit documentation existed prior to this package
4. **Cross-reference integrity:** 3 broken semantic links identified and fixed

---

## Semantic Relations

**This document is part of:**
- [[ІНДЕКС]] -- Master documentation index

**Depends on:**
- [[manifesto/ГЛОСАРІЙ.md]] -- Canonical glossary defines authoritative terms
- [[architecture/foundation/АРХІТЕКТУРНИЙ_КОРІНЬ.md]] -- Axioms that govern terminology

**Referenced by:**
- [[АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ]]
- [[МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН]]
- [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]]
```
---
### audit/МАТРИЦЯ_ТЕРМІНІВ_ТА_ЗАМІН.md
**Розмір:** 4,646 байт
```text
---
tags:
  - domain:meta
  - status:canonical
  - format:reference
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Term Matrix: Legacy to Canonical BLOOM Terminology"
dg-publish: true
---

# Term Matrix: Legacy to Canonical BLOOM Terminology

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Language: Ukrainian (canonical)

---

## 0. Purpose

This document provides the authoritative mapping from legacy (pre-BLOOM) terminology to canonical BLOOM terms. All new documentation and updates to existing documentation must use the canonical terms from the right column.

Reference: `manifesto/ГЛОСАРІЙ.md` for full definitions.

---

## 1. System-Level Terms

| Legacy Term | Canonical BLOOM Term | Scope | Notes |
|------------|---------------------|-------|-------|
| Garden Seedling | Garden Bloom | Product name | Garden Bloom is the product; BLOOM is the runtime |
| Runtime / Execution engine | BLOOM Runtime | Execution environment | Behavioral Logic Orchestration for Order-Made Systems |
| Task runner | Orchestration Layer | Vendor-agnostic abstraction | Abstracts Hatchet, Temporal, etc. |
| Job dispatcher | Execution Pipeline | Task lifecycle management | From trigger to terminal state |
| Sync engine | Membridge Control Plane | Memory synchronization | claude-mem.db sync between nodes |

---

## 2. Agent-Related Terms

| Legacy Term | Canonical BLOOM Term | Scope | Notes |
|------------|---------------------|-------|-------|
| Bot / AI worker | Agent | Execution unit | Everything is an Agent |
| Agent config | Agent Definition | Registry entry | Versioned logic definition |
| Agent session | Execution Context | Isolated runtime scope | Activated by master-key |
| Worker process | Worker Node | Edge node running Claude CLI | Membridge agent on port 8001 |

---

## 3. Data & Storage Terms

| Legacy Term | Canonical BLOOM Term | Scope | Notes |
|------------|---------------------|-------|-------|
| Database / DB sync | claude-mem.db | Session memory | SQLite via Membridge to MinIO |
| Agent memory / reasoning | DiffMem (git) | Agent reasoning memory | git-based, Layer 1/2 |
| File storage | MinIO Object Storage | Canonical object store | Axiom A1: MinIO is canonical |
| Output / result | Artifact | Immutable execution output | Registered in Artifact Store |

---

## 4. Execution Flow Terms

| Legacy Term | Canonical BLOOM Term | Scope | Notes |
|------------|---------------------|-------|-------|
| Request / ticket | Proposal | Mutation request | Requires explicit consent |
| Task assignment | Lease | Worker-task binding | TTL + heartbeat lifecycle |
| Health check / ping | Heartbeat | Worker liveness signal | Every 10s default |
| Retry / resubmit | Requeue | Failed task retry | Increment attempts, re-enqueue |
| Proxy call | LLM-Task Delegation | Orchestrator to worker | Never execute LLM directly |

---

## 5. Architecture Terms

| Legacy Term | Canonical BLOOM Term | Scope | Notes |
|------------|---------------------|-------|-------|
| Main node / master | Primary | Leadership role | Single source of truth for sync |
| Replica / follower | Secondary | Non-primary node | Pull-only by default |
| Lock / mutex | Push Lock | Concurrent push prevention | Independent of leadership lease |
| Role assignment | Leadership Lease | Primary/Secondary determination | Stored in MinIO, TTL-based |

---

## 6. Frontend Terms

| Legacy Term | Canonical BLOOM Term | Scope | Notes |
|------------|---------------------|-------|-------|
| Dashboard | BLOOM Runtime UI | Main interface | React/Shadcn-based |
| Settings page | Runtime Settings | Configuration panel | Membridge proxy tab |
| Admin panel | Control Plane UI | Membridge management | vanilla HTML at :8000/ui |

---

## 7. Usage Rules

1. **New documents:** Must use canonical terms exclusively
2. **Existing Tier-1 documents:** Already updated; verify before editing
3. **Existing Tier-2 documents:** Update when editing for other reasons
4. **Code comments:** Prefer canonical terms; legacy acceptable in variable names for backward compatibility
5. **API endpoints:** Use canonical terms in new endpoints; existing endpoints retain names for backward compatibility
6. **User-facing UI:** Always use canonical terms

---

## Semantic Relations

**This document is part of:**
- [[_INDEX]] -- Audit Pack index

**Depends on:**
- [[manifesto/ГЛОСАРІЙ.md]] -- Source of canonical definitions

**Referenced by:**
- [[АУДИТ_ДОКУМЕНТАЦІЇ_BLOOM_РЕБРЕНДИНГ]] -- Uses this matrix for audit
- [[ПРОГАЛИНИ_ТА_ПЛАН_ЗАПОВНЕННЯ]] -- References terms needing update
```
---
### integration/ІНТЕГРАЦІЯ_MEMBRIDGE.md
**Розмір:** 12,545 байт
```text
---
tags:
  - domain:storage
  - status:canonical
  - format:contract
  - feature:storage
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Інтеграція: Membridge Control Plane"
dg-publish: true
---

# Інтеграція: Membridge Control Plane

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає архітектурну роль Membridge у системі Garden Bloom як інфраструктурного шару синхронізації пам'яті Claude CLI між вузлами мережі.

Membridge управляє синхронізацією `claude-mem.db` (SQLite) між edge-вузлами (Alpine, RPi, Orange Pi) та об'єктним сховищем MinIO. Він є незалежним від `garden-bloom-memory` git-монорепо — два сховища обслуговують різні шари пам'яті:

| Сховище | Тип пам'яті | Хто пише |
|---------|-------------|---------|
| `claude-mem.db` → MinIO (через Membridge) | Claude CLI session memory | Claude CLI + membridge hooks |
| `garden-bloom-memory` (git) | Agent reasoning memory (Layer 1/2) | Apply Engine via Proposals |

**Аксіома A1:** MinIO є canonical object storage; Membridge є гейткіпером запису до нього для claude-mem.

---

## 1. Компоненти

```
Alpine (192.168.3.184)
├── membridge-server  :8000   ← Control Plane API; leadership registry; Web UI
└── membridge-agent   :8001   ← Local project registry; heartbeat sender

RPi / Orange Pi (edge nodes)
└── membridge-agent   :8001   ← Local sync; heartbeat до Alpine :8000
```

### 1.1 membridge-server (Control Plane)

- FastAPI; порт 8000
- Приймає heartbeats від агентів
- Реєструє проекти та вузли
- Надає leadership API (select primary, view lease)
- Служить Web UI на `/ui` (→ `/static/ui.html`)

### 1.2 membridge-agent (Edge Agent)

- FastAPI; порт 8001
- Зберігає локальний реєстр проектів (`~/.membridge/agent_projects.json`)
- Надсилає heartbeat до control plane кожні `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS` (default: 10s)
- Auth-exempt для localhost; вимагає `X-MEMBRIDGE-AGENT` для remote

---

## 2. Leadership Model (Модель лідерства)

### 2.1 Ролі вузлів

| Роль | Дозволи |
|------|---------|
| **Primary** (Первинний) | Push до MinIO ✅ · Pull → відмовляє якщо є local DB ✅ |
| **Secondary** (Вторинний) | Push → заблоковано за замовчуванням ❌ · Pull (з backup) ✅ |

**Інваріант:** лише один вузол є Primary для кожного проекту в будь-який момент часу.

### 2.2 Leadership Lease (Оренда лідерства)

Зберігається в MinIO: `projects/<canonical_id>/leadership/lease.json`

```json
{
  "canonical_id":     "sha256(project_name)[:16]",
  "primary_node_id":  "alpine",
  "issued_at":        1706000000,
  "expires_at":       1706003600,
  "lease_seconds":    3600,
  "epoch":            3,
  "policy":           "primary_authoritative",
  "issued_by":        "alpine",
  "needs_ui_selection": false
}
```

**Поле `epoch`:** монотонно зростає при кожному поновленні. Запобігає гонці стану між двома вузлами, що одночасно намагаються стати Primary.

### 2.3 Lease State Machine

```
                ┌──────────────┐
                │   ABSENT     │
                └──────┬───────┘
                       │ перший запис
                ┌──────▼───────┐
          ┌─────│    VALID     │─────┐
          │     └──────┬───────┘     │
          │ current    │ expires_at  │ current
          │ node =     │ пройшло     │ node ≠
          │ primary    ▼             │ primary
          │     ┌──────────────┐     │
          │     │   EXPIRED    │     │
          │     └──────┬───────┘     │
          │            │             │
          │   PRIMARY_NODE_ID        │
          │   matches current?       │
          │   YES → renew (epoch+1)  │
          ▼   NO → secondary        ▼
      [Primary]                 [Secondary]
```

### 2.4 Визначення ролі (алгоритм)

```
1. Читати lease.json з MinIO
2. Якщо відсутній → створити (primary = PRIMARY_NODE_ID env або current node)
3. Якщо expired:
   а. Якщо PRIMARY_NODE_ID == NODE_ID → поновити lease (epoch+1)
   б. Інакше → перечитати; якщо ще expired → роль = secondary
4. Якщо valid:
   роль = primary  якщо primary_node_id == NODE_ID
   роль = secondary інакше
```

---

## 3. Push / Pull Protocol (Протокол синхронізації)

### 3.1 Primary Push

```
1. Перевірити роль → primary ✅
2. Зупинити worker (для консистентного snapshot)
3. VACUUM INTO temp + перевірка цілісності
4. Перезапустити worker
5. Обчислити SHA256 snapshot
6. Порівняти з remote SHA256 (пропустити якщо однакові)
7. Отримати distributed push lock
8. Upload DB + SHA256 + manifest до MinIO
9. Верифікувати remote SHA256
```

### 3.2 Secondary Pull

```
1. Перевірити роль → secondary ✅
2. Завантажити remote SHA256
3. Порівняти з local (пропустити якщо однакові)
4. Завантажити remote DB до temp файлу
5. Верифікувати SHA256
6. Safety backup local DB → ~/.claude-mem/backups/pull-overwrite/<ts>/
7. Зупинити worker
8. Атомарна заміна local DB
9. Перевірити цілісність + перезапустити worker
```

### 3.3 Lock Model

| Тип | Шлях у MinIO | TTL | Призначення |
|-----|-------------|-----|-------------|
| Push lock | `projects/<cid>/locks/active.lock` | `LOCK_TTL_SECONDS` (2h) | Заборона паралельних push |
| Leadership lease | `projects/<cid>/leadership/lease.json` | `LEADERSHIP_LEASE_SECONDS` (1h) | Визначення Primary/Secondary |

Push lock та Leadership lease — незалежні механізми.

---

## 4. Artifact Registry (Реєстр артефактів)

Membridge Control Plane веде метаданий реєстр артефактів у MinIO:

```
projects/<canonical_id>/
├── artifacts/
│   └── <artifact_id>.json     ← metadata: type, job_id, created_at, url
├── leadership/
│   ├── lease.json
│   └── audit/<ts>-<node_id>.json
├── locks/
│   └── active.lock
└── db/
    ├── <sha256>.db             ← canonical SQLite snapshot
    └── <sha256>.sha256
```

**Immutability rule:** артефакт після запису до MinIO є immutable. Повторний запис з тим самим `artifact_id` повертає наявний запис без помилки (ідемпотентний).

---

## 5. Control Plane API (Поверхня API)

### 5.1 Public endpoints (без автентифікації)

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/health` | Service health |
| `GET` | `/ui` | → redirect до `/static/ui.html` |

### 5.2 Admin endpoints (вимагають `X-MEMBRIDGE-ADMIN`)

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/projects` | Список проектів (manual + heartbeat) |
| `GET` | `/projects/<cid>/leadership` | Поточний lease |
| `POST` | `/projects/<cid>/leadership/select` | Вибір Primary вузла |
| `GET` | `/agents` | Список зареєстрованих агентів |
| `POST` | `/agent/heartbeat` | Прийом heartbeat від агента |
| `GET` | `/jobs` | Список Job (статус, тип) |
| `PATCH` | `/jobs/<id>/status` | Оновлення статусу Job |
| `POST` | `/jobs/<id>/requeue` | Повторна постановка DEAD job |

### 5.3 Agent endpoints (порт 8001; `X-MEMBRIDGE-AGENT` для remote)

| Метод | Шлях | Auth | Опис |
|-------|------|------|------|
| `GET` | `/health` | — | Agent health |
| `GET` | `/projects` | — | Local project registry |
| `POST` | `/register_project` | localhost exempt | Реєстрація проекту |

---

## 6. Environment Variables (Override Protocol)

Змінні CLI-середовища перекривають значення з `config.env`. Реалізовано через save/restore pattern у hooks.

| Змінна | Default | Призначення |
|--------|---------|-------------|
| `FORCE_PUSH` | `0` | Примусовий push (обходить stale lock) |
| `ALLOW_SECONDARY_PUSH` | `0` | Дозволити Secondary push (unsafe) |
| `ALLOW_PRIMARY_PULL_OVERRIDE` | `0` | Дозволити Primary pull-overwrite (unsafe) |
| `STALE_LOCK_GRACE_SECONDS` | `60` | Додатковий grace після закінчення TTL lock |
| `LOCK_TTL_SECONDS` | `7200` | TTL push lock |
| `LEADERSHIP_LEASE_SECONDS` | `3600` | TTL leadership lease |
| `LEADERSHIP_ENABLED` | `1` | `0` → вимкнути всі leadership перевірки |

---

## 7. Heartbeat Flow (Потік heartbeat)

```
membridge-agent (port 8001)
        │
        │ кожні HEARTBEAT_INTERVAL_SECONDS (default 10s)
        │ читає ~/.membridge/agent_projects.json
        │
        ▼
POST /agent/heartbeat  →  membridge-server (port 8000)
{
  "node_id":      "alpine",
  "canonical_id": "abc123def456abcd",
  "project_id":   "garden-seedling",
  "ip_addrs":     ["192.168.3.184"],
  "obs_count":    1234,
  "db_sha":       "deadbeef..."
}
        │
        ▼
server: _nodes[] + _heartbeat_projects[] (in-memory)
        │
        ▼
GET /projects → Frontend (Web UI)
```

**Примітка:** `_heartbeat_projects` зберігаються в пам'яті сервера. Після рестарту сервера відновлюються через наступний heartbeat цикл (≤ HEARTBEAT_INTERVAL_SECONDS).

---

## 8. Failure Scenarios та Recovery

| Сценарій | Поведінка | Recovery |
|----------|-----------|----------|
| Primary offline; lease expired | Secondary не може push; needs_ui_selection стає true | Operator: `POST /projects/<cid>/leadership/select` для нового Primary |
| Push lock stuck | Наступний push: steal lock після TTL + grace | `FORCE_PUSH=1 cm-push` або чекати TTL |
| MinIO недоступний | Push → error; pull → error | Всі операції fail-safe; local DB незмінна |
| Secondary local-ahead | Secondary має більше записів ніж remote | Promote Secondary → Primary, потім push |
| Agent reboots | Heartbeat відновлюється автоматично | Нічого не потрібно; cервер оновить стан |
| Server reboot | _heartbeat_projects очищуються | Відновлення через ≤ HEARTBEAT_INTERVAL_SECONDS |

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — A1 (MinIO canonical), A2 (consent-based mutation)
- [[КАНОНІЧНА_МОДЕЛЬ_АВТОРИТЕТУ_СХОВИЩА]] — матриця запису до MinIO

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — Membridge vs Memory Backend: два різних сховища
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — Membridge як вузол топології (Alpine :8000/:8001)
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — Artifact Store в MinIO
- [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] — Web UI через Membridge `/ui`
```
---
### integration/ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND.md
**Розмір:** 13,877 байт
```text
---
tags:
  - domain:api
  - status:canonical
  - format:spec
  - feature:execution
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Інтеграція: NotebookLM Backend"
dg-publish: true
---

# Інтеграція: NotebookLM Backend

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає архітектурну роль, authority boundary, API-контракт та протоколи відновлення NotebookLM Backend — FastAPI-сервісу, розгорнутого на Replit, що виступає єдиним ізольованим проксі до когнітивного рушія NotebookLM у системі Garden Bloom.

NotebookLM Backend є stateless-сервісом. Весь змінний стан зберігається виключно в Job Queue та Artifact Store. Між запитами сервіс не утримує мутабельного стану.

---

## 1. Архітектурна роль

NotebookLM Backend виконує три ролі залежно від типу завдання, отриманого з Job Queue.

### 1.1 Research Worker (Дослідницький Воркер)

Активується на Job типу `RESEARCH`.

- **Вхід:** `{query, context_snapshot, sources[], constraints}`
- **Вихід:** Артефакт типу `RESEARCH_BRIEF`

Послідовність виконання:

```
1. Отримати контекстний пакет від Memory Backend (context assembly)
2. Виконати запит до NotebookLM через ізольований HTTP-виклик
3. Структурувати відповідь з посиланнями на джерела
4. Записати Артефакт до Artifact Store (immutable після commit)
5. Оновити статус Job → COMPLETE; надіслати callback
```

**Інваріант:** сирий LLM-вивід не може бути збережений без структурування.

### 1.2 Brief Generator (Генератор Брифів)

Активується на Job типу `BRIEF`.

- **Вхід:** `{vision_text, entity_refs[], style_guide}`
- **Вихід:** Артефакт типу `BRIEF`

Послідовність виконання:

```
1. Сформувати BM25-запит до Memory Backend за entity_refs
2. Отримати релевантні фрагменти пам'яті Layer 1
3. Побудувати стислий бриф із посиланнями на canonical entities
4. Записати Артефакт; оновити статус Job → COMPLETE
```

### 1.3 Proposal Preprocessor (Препроцесор Пропозицій)

Активується на Job типу `PROPOSAL_PREPROCESS`.

- **Вхід:** `{proposal_draft, context_snapshot, validation_rules[]}`
- **Вихід:** Артефакт типу `PREPROCESSED_PROPOSAL`

Послідовність виконання:

```
1. Зіставити текст draft із відомими сутностями Entity Graph
2. Виявити неповні або суперечливі поля
3. Доповнити Пропозицію посиланнями на релевантні Артефакти
4. Позначити проблеми — НЕ приймати рішень
5. Записати Артефакт; оновити статус Job → COMPLETE
```

---

## 2. Authority Boundary (Межа авторитету)

```
NotebookLM Backend ДОЗВОЛЕНО:
  ✅ GET  /memory/context        — читати Memory Backend (read-only)
  ✅ GET  /artifacts/{id}        — читати Artifact Store
  ✅ POST /artifacts             — записувати нові Артефакти
  ✅ PATCH /jobs/{id}/status     — оновлювати статус Job
  ✅ POST <callback_url>         — надсилати callback результату

NotebookLM Backend ЗАБОРОНЕНО:
  ❌ DELETE /artifacts/{id}      — видаляти Артефакти
  ❌ PUT /memory/*               — писати в Memory Backend напряму
  ❌ POST /leadership/*          — читати або змінювати Leadership Lease
  ❌ S3 MinIO direct write       — писати безпосередньо в об'єктне сховище
  ❌ POST /agents/run            — запускати інші агенти
```

**Аксіома A3:** сервіс є stateless; між запитами не утримує стану виконання.
**Аксіома A5:** усі вхідні запити надходять лише через Gateway (Cloudflare Worker) або Orchestration Layer — не напряму від Frontend.

---

## 3. API Contract (Контракт API)

### 3.1 Вхідний endpoint

```
POST /jobs/process
Authorization: Bearer <NOTEBOOKLM_API_KEY>
Content-Type: application/json

{
  "job_id":   "uuid-v4",
  "job_type": "RESEARCH" | "BRIEF" | "PROPOSAL_PREPROCESS",
  "payload":  { ... job-specific fields ... },
  "context":  {
    "memory_snapshot_url": "https://...",
    "entity_refs": ["entity-slug-1", "entity-slug-2"]
  },
  "callback": "https://membridge.internal/jobs/{job_id}/result"
}
```

| Код | Значення |
|-----|---------|
| 202 | Accepted — `{"accepted":true,"job_id":"...","estimated_seconds":15}` |
| 400 | Bad Request — некоректний payload |
| 422 | Unprocessable Entity — validation error з деталями поля |
| 503 | Service Unavailable — cold start або rate limit |

### 3.2 Вихідний callback

```
POST <callback_url>
Content-Type: application/json

{
  "job_id":       "uuid-v4",
  "status":       "COMPLETE" | "FAILED",
  "artifact_id":  "art-uuid-v4",
  "artifact_url": "https://...",
  "error": {
    "code":    "RATE_LIMIT" | "CONTEXT_TIMEOUT" | "VALIDATION_ERROR",
    "message": "..."
  }
}
```

### 3.3 Health endpoint

```
GET /health
→ {"status":"ok","version":"1.x.x","jobs_processed":N,"uptime_seconds":N}
```

---

## 4. State Machine (Стан завдання NotebookLM)

```
          ┌──────────┐
          │ CREATED  │
          └────┬─────┘
               │ POST /jobs/process (202 Accepted)
          ┌────▼─────┐
          │  QUEUED  │◄─────────────────────────────┐
          └────┬─────┘                              │
               │ worker picks up                    │ retry (exponential backoff)
     ┌─────────▼──────────┐                         │
     │  CONTEXT_ASSEMBLY  │                         │
     └─────────┬──────────┘                         │
               │ memory snapshot ready              │
     ┌─────────▼──────────┐              ┌──────────┴──────────┐
     │  NOTEBOOKLM_CALL   │              │   RETRY_BACKOFF     │
     └─────────┬──────────┘              │   15s → 30s → 60s   │
               │ LLM response received   └──────────▲──────────┘
     ┌─────────▼──────────┐                         │
     │   ARTIFACT_WRITE   │──── error ──────────────┘
     └─────────┬──────────┘
               │ atomic commit (artifact + status)
          ┌────▼─────┐              ┌──────────┐
          │ COMPLETE │              │  FAILED  │──── max retries
          └──────────┘              └────┬─────┘
                                         │
                                    ┌────▼─────┐
                                    │   DEAD   │
                                    └──────────┘
```

**Інваріанти стан-машини:**

- `COMPLETE → *` — заборонений перехід.
- `ARTIFACT_WRITE` є атомарним: або запис Артефакту **і** оновлення статусу виконуються разом, або жодна операція.
- `DEAD` — фінальний стан; автовідновлення відсутнє; вимагає ручного втручання оператора.
- Максимальна кількість спроб retry: 3.

---

## 5. Sequence Diagram: Research Worker

```
Frontend      Gateway      Orch.Layer   NLM Backend   Memory Backend   Artifact Store
   │              │              │            │               │                │
   │──POST /run──►│              │            │               │                │
   │              │──trigger────►│            │               │                │
   │              │              │──POST /jobs/process───────►│                │
   │              │              │            │               │                │
   │              │              │            │──GET /context─►│               │
   │              │              │            │◄── snapshot ───│               │
   │              │              │            │               │                │
   │              │              │            │──NLM query (grounded reasoning) │
   │              │              │            │◄── structured response          │
   │              │              │            │                         ─POST──►│
   │              │              │            │                         ◄─art_id│
   │              │              │◄── callback (COMPLETE, artifact_id) ─────────│
   │              │◄──status─────│            │               │                │
   │◄──display────│              │            │               │                │
```

---

## 6. Failure Scenarios (Сценарії відмов)

| Сценарій | Поведінка | Recovery |
|----------|-----------|----------|
| Replit cold start (> 30s відповіді) | 503 від `/jobs/process` | Job залишається `QUEUED`; retry після backoff |
| NotebookLM rate limit | 429 від NLM API | → `RETRY_BACKOFF`; exponential backoff 15s/30s/60s |
| Context assembly timeout (> 10s) | Memory Backend недоступний | Job → `FAILED`; помилка в артефакті-журналі |
| Artifact write collision | Дублікатний `artifact_id` | Ідемпотентний запис: якщо артефакт з тим самим `job_id` існує — повертається наявний |
| Callback URL недоступний | POST callback → 5xx або timeout | Job-статус синхронізується через polling Orchestration Layer |
| Invalid job payload | 422 | Job → `FAILED` одразу, без retry |
| Replit deployment downtime | Усі job endpoints → 503 | Усі `QUEUED` jobs чекають; оператор перевіряє Deployments dashboard |

---

## 7. Recovery Playbook (Відновлення)

### 7.1 Сервіс не відповідає (503)

```bash
curl -fsS https://<replit-slug>.repl.co/health
# якщо cold start — очікувати 30s, повторити
# якщо постійна помилка — перевірити Replit Deployments dashboard
```

### 7.2 Job завис у QUEUED > 5 хвилин

```bash
curl -X PATCH http://192.168.3.184:8000/jobs/<job_id>/status \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" \
  -d '{"status":"FAILED","reason":"timeout-manual-reset"}'
```

### 7.3 DEAD jobs

```bash
# Переглянути
curl http://192.168.3.184:8000/jobs?status=DEAD \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY"

# Повторно поставити в чергу
curl -X POST http://192.168.3.184:8000/jobs/<job_id>/requeue \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY"
```

---

## 8. Observability (Спостережуваність)

| Метрика | Ендпоінт | Формат |
|---------|----------|--------|
| Service health | `GET /health` | JSON |
| Job metrics | `GET /metrics` | Prometheus text |
| Structured log | Replit console | JSON Lines |
| Artifact stats | `GET /artifacts/stats` | `{"total":N,"by_type":{...}}` |

**Structured log schema:**

```json
{
  "ts":      "2026-02-24T10:00:00Z",
  "level":   "INFO",
  "job_id":  "uuid",
  "phase":   "CONTEXT_ASSEMBLY",
  "node":    "replit",
  "ms":      142
}
```

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — повна специфікація Job та Artifact моделей
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — context assembly API, BM25 query protocol
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — аксіоми A3 (stateless), A5 (Gateway sole entry)

**На цей документ посилаються:**
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — NLM Backend як вузол топології
- [[DEPLOYMENT_REPLIT_АРХІТЕКТУРА]] — деплой цього сервісу
- [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] — відображення результатів
```
---
### integration/JOB_QUEUE_ТА_ARTIFACT_MODEL.md
**Розмір:** 14,795 байт
```text
---
tags:
  - domain:execution
  - status:canonical
  - format:contract
  - feature:execution
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Job Queue та Artifact Model"
dg-publish: true
---

# Job Queue та Artifact Model

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає повну специфікацію Job Queue state machine, NotebookLM Job state machine, Artifact model schema, Authority matrix та модель спостережуваності для Integration Layer системи Garden Bloom.

Цей документ є контрактом між усіма компонентами, що взаємодіють із Job Queue та Artifact Store. Порушення state machine transitions або authority matrix є архітектурним порушенням.

---

## 1. Job Queue: State Machine

### 1.1 Повна стан-машина

```
                         ┌─────────────┐
                         │   PENDING   │◄── Inbox Entry відповідної дії
                         └──────┬──────┘
                                │ Orchestration Layer validation
                         ┌──────▼──────┐
                         │   QUEUED    │◄──────────────────────────────────┐
                         └──────┬──────┘                                   │
                                │ worker picks up (concurrency: max 1/agent)│
                     ┌──────────▼──────────┐                               │
                     │  CONTEXT_ASSEMBLY   │                               │
                     └──────────┬──────────┘                               │
                                │ snapshot ready                           │
                     ┌──────────▼──────────┐                               │
                     │  NOTEBOOKLM_CALL    │                               │
                     └──────────┬──────────┘                               │
                                │ response received                        │
                     ┌──────────▼──────────┐          ┌────────────────────┴──┐
                     │   ARTIFACT_WRITE    │──error──►│    RETRY_BACKOFF      │
                     └──────────┬──────────┘          │    15s → 30s → 60s    │
                                │ atomic commit       └────────────▲──────────┘
                     ┌──────────▼──────────┐                       │
                     │      COMPLETE       │                       │ attempt < 3
                     └─────────────────────┘          ┌────────────┴──────────┐
                                                       │       FAILED          │
                                                       └────────────┬──────────┘
                                                                    │ attempt ≥ 3
                                                       ┌────────────▼──────────┐
                                                       │        DEAD           │
                                                       └───────────────────────┘
```

### 1.2 Transition Table (Таблиця переходів)

| З стану | До стану | Тригер | Хто пише |
|---------|----------|--------|---------|
| `PENDING` | `QUEUED` | Orchestration Layer validation OK | Orchestration Layer |
| `QUEUED` | `CONTEXT_ASSEMBLY` | Worker pickup | Orchestration Layer |
| `CONTEXT_ASSEMBLY` | `NOTEBOOKLM_CALL` | snapshot ready | Orchestration Layer |
| `CONTEXT_ASSEMBLY` | `RETRY_BACKOFF` | Memory Backend timeout | Orchestration Layer |
| `NOTEBOOKLM_CALL` | `ARTIFACT_WRITE` | NLM response OK | Orchestration Layer |
| `NOTEBOOKLM_CALL` | `RETRY_BACKOFF` | 429 / 503 від NLM | Orchestration Layer |
| `ARTIFACT_WRITE` | `COMPLETE` | atomic commit OK | Orchestration Layer |
| `ARTIFACT_WRITE` | `RETRY_BACKOFF` | write error | Orchestration Layer |
| `RETRY_BACKOFF` | `QUEUED` | backoff elapsed; attempt < 3 | Orchestration Layer |
| `RETRY_BACKOFF` | `FAILED` | attempt ≥ 3 | Orchestration Layer |
| `FAILED` | `DEAD` | max retries exceeded | Orchestration Layer |
| `FAILED` | `QUEUED` | manual requeue (operator) | Gateway (Admin) |

**Invariant F1:** `COMPLETE → *` — перехід заборонений. `COMPLETE` є фінальним станом.
**Invariant F2:** `DEAD → *` — автоматичний перехід відсутній; потребує ручного `requeue`.
**Invariant F3:** `ARTIFACT_WRITE` є атомарним: запис артефакту + статус `COMPLETE` виконуються в одній транзакції; часткові записи забороненні.
**Invariant F4:** Лише Orchestration Layer пише `status.json`; Mastra не пише статус.

### 1.3 Job Schema

```json
{
  "job_id":      "uuid-v4",
  "run_id":      "run_2026-02-24_abc123",
  "job_type":    "RESEARCH | BRIEF | PROPOSAL_PREPROCESS",
  "agent_slug":  "architect-guardian",
  "status":      "PENDING | QUEUED | CONTEXT_ASSEMBLY | NOTEBOOKLM_CALL | ARTIFACT_WRITE | COMPLETE | RETRY_BACKOFF | FAILED | DEAD",
  "attempt":     0,
  "max_attempts": 3,
  "payload":     { "...": "..." },
  "context":     {
    "memory_snapshot_url": "https://...",
    "entity_refs":         ["entity-slug"]
  },
  "callback":    "https://membridge.internal/jobs/{job_id}/result",
  "created_at":  "2026-02-24T10:00:00Z",
  "updated_at":  "2026-02-24T10:00:15Z",
  "artifact_id": "art-uuid-v4",
  "error":       null
}
```

---

## 2. NotebookLM Job: State Machine

Детальна стан-машина виконання всередині NLM Backend (підмножина Job Queue states).

```
 NLM Backend отримує POST /jobs/process
           │
    ┌──────▼──────┐
    │   ACCEPTED  │  (202; job зареєстровано у внутрішній черзі NLM Backend)
    └──────┬──────┘
           │ async worker
    ┌──────▼──────┐
    │ FETCHING_   │  завантаження context_snapshot_url
    │  CONTEXT   │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ BUILDING_   │  формування prompt для NLM із контексту + query
    │  PROMPT    │
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  NLM_QUERY  │  HTTP запит до NotebookLM endpoint
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │ STRUCTURING │  парсинг + структурування відповіді NLM
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │  CALLBACK   │  POST <callback_url> із artifact_id
    └──────┬──────┘
           │
    ┌──────▼──────┐
    │    DONE     │  внутрішній стан NLM Backend
    └─────────────┘
```

Будь-який крок може перейти у `ERROR` → NLM Backend надсилає callback із `status: FAILED`.

---

## 3. Artifact Model (Модель артефакту)

### 3.1 Schema

```json
{
  "artifact_id":   "art-uuid-v4",
  "job_id":        "uuid-v4",
  "run_id":        "run_2026-02-24_abc123",
  "type":          "RESEARCH_BRIEF | BRIEF | PREPROCESSED_PROPOSAL",
  "agent_slug":    "architect-guardian",
  "created_at":    "2026-02-24T10:00:00Z",
  "finalized":     true,
  "finalized_at":  "2026-02-24T10:00:20Z",
  "version":       1,
  "url":           "https://<minio>/projects/<cid>/artifacts/<art_id>.json",
  "entity_refs":   ["entity-slug-1", "entity-slug-2"],
  "tags":          ["research", "architecture"],
  "content":       { "...": "artifact-type-specific fields..." },
  "sources":       [
    { "ref": "sources/domain-knowledge.md", "excerpt": "..." }
  ]
}
```

### 3.2 Content Schema за типами

**RESEARCH_BRIEF:**
```json
{
  "title":    "Research Brief: ...",
  "summary":  "Стислий висновок...",
  "sections": [
    { "heading": "...", "body": "...", "sources": ["ref1"] }
  ],
  "conclusions": ["..."],
  "open_questions": ["..."]
}
```

**BRIEF:**
```json
{
  "title":      "...",
  "body":       "Стислий текст...",
  "entity_map": { "entity-slug": "Назва сутності" },
  "word_count": 350
}
```

**PREPROCESSED_PROPOSAL:**
```json
{
  "original":  { "...": "вхідний draft..." },
  "enriched":  { "...": "збагачений draft..." },
  "issues":    [
    { "field": "target", "severity": "warning", "message": "Посилання не резолвиться" }
  ],
  "entity_matches": [{ "text": "...", "entity_id": "...", "confidence": 0.91 }]
}
```

### 3.3 Immutability Rules

- `finalized: true` → артефакт immutable; будь-яке оновлення забороняється.
- Ідемпотентний запис: POST артефакту з наявним `job_id` повертає існуючий артефакт без помилки.
- Видалення артефактів — заборонено для всіх компонентів (окрім системного cleanup після N днів через Admin).

---

## 4. Authority Matrix (Матриця авторитету)

### 4.1 Job Queue

| Компонент | Create | Read | Update Status | Delete |
|-----------|:------:|:----:|:-------------:|:------:|
| Gateway (Owner via Frontend) | ✅ | ✅ | ❌ | ❌ |
| Orchestration Layer | ✅ | ✅ | ✅ | ❌ |
| NLM Backend | ❌ | ✅ (власний job) | ✅ (власний) | ❌ |
| Mastra Runtime | ❌ | ❌ | ❌ | ❌ |
| Membridge Control Plane | ❌ | ✅ (admin) | ✅ (admin) | ❌ |
| Frontend | ❌ | ✅ (read-only) | ❌ | ❌ |

### 4.2 Artifact Store

| Компонент | Write New | Read | Modify | Delete |
|-----------|:---------:|:----:|:------:|:------:|
| NLM Backend | ✅ | ✅ | ❌ | ❌ |
| Orchestration Layer | ❌ | ✅ | ❌ | ❌ |
| Memory Backend | ❌ | ✅ (context) | ❌ | ❌ |
| Membridge Control Plane | Registry metadata | ✅ | ❌ | Admin cleanup |
| Frontend | ❌ | ✅ (read-only) | ❌ | ❌ |
| Gateway | ❌ | ✅ | ❌ | ❌ |

### 4.3 Memory Backend (garden-bloom-memory)

| Компонент | Layer 1 Read | Layer 2 Read | Write (via Proposal) |
|-----------|:-----------:|:-----------:|:-------------------:|
| Orchestration Layer | ✅ | ❌ | Via Gateway |
| Mastra | Via tool | Via explicit tool | Via create-proposal |
| NLM Backend | ✅ (context) | ❌ | ❌ |
| Frontend | ❌ | ❌ | ❌ |
| Apply Engine (Gateway) | ✅ | ✅ | ✅ (git commit) |

---

## 5. Observability Model (Модель спостережуваності)

### 5.1 Audit Log

Кожна write-операція до canonical storage логується Gateway:

```json
{
  "ts":        "2026-02-24T10:00:00Z",
  "event":     "job.status.update",
  "actor":     "orchestration-layer",
  "job_id":    "uuid",
  "from":      "CONTEXT_ASSEMBLY",
  "to":        "NOTEBOOKLM_CALL",
  "node":      "alpine"
}
```

Аудит-лог зберігається в MinIO: `audit/<YYYYMMDD>/<event_id>.json`.

### 5.2 Run Artifacts Structure

```
agents/{slug}/runs/{runId}/
├── status.json          ← canonical run status (writer: Orchestration Layer)
├── manifest.json        ← run metadata (writer: Orchestration Layer)
├── steps/
│   ├── 01-context.json  ← Phase 3: context assembly result
│   ├── 02-execute.json  ← Phase 4: Mastra output
│   └── 03-persist.json  ← Phase 5: proposal write result
└── output/
    └── proposal.json    ← згенерована Пропозиція
```

### 5.3 Metrics

| Метрика | Джерело | SLO |
|---------|---------|-----|
| Job completion rate | Orchestration Layer | > 95% протягом 24h |
| P95 end-to-end run time | status.json timestamps | < 120s |
| P95 context assembly time | step/01-context.json | < 5s |
| P95 NLM call time | step/02-execute.json | < 60s |
| Artifact write latency | step/03-persist.json | < 2s |
| Dead job rate | Job Queue | < 1% протягом 7d |

### 5.4 Alerts

| Умова | Дія |
|-------|-----|
| Job у QUEUED > 5 хвилин | Alert: operator перевіряє NLM Backend health |
| Dead job rate > 1% | Alert: operator перевіряє Orchestration Layer logs |
| Artifact write failure (3 поспіль) | Alert: operator перевіряє MinIO availability |
| Context assembly timeout (3 поспіль) | Alert: operator перевіряє Memory Backend / GitHub |

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — A2 (consent), A3 (stateless execution), A4 (orchestration replaceable)
- [[КАНОНІЧНИЙ_КОНВЕЄР_ВИКОНАННЯ]] — 7 фаз canonical conveyor
- [[КАНОНІЧНИЙ_ЦИКЛ_ЗАПУСКУ]] — run status.json transitions
- [[МОДЕЛЬ_СПОСТЕРЕЖУВАНОСТІ]] — audit log patterns

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — NLM Job state machine деталі
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — Phase 3 / Phase 5 в контексті пам'яті
- [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] — відображення Job states у Frontend
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — data flow через topology
```
---
### integration/DEPLOYMENT_REPLIT_АРХІТЕКТУРА.md
**Розмір:** 11,209 байт
```text
---
tags:
  - domain:arch
  - status:canonical
  - format:guide
  - feature:execution
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Deployment: Replit Архітектура"
dg-publish: true
---

# Deployment: Replit Архітектура

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає архітектуру розгортання NotebookLM Backend на платформі Replit: модель persistence, управління секретами, cold start behavior, CI/CD pipeline та операційні процедури.

**Scope:** лише NotebookLM Backend (FastAPI сервіс). Membridge Control Plane розгортається на Alpine (OpenRC). Memory Backend (Mastra) розгортається як частина Orchestration Layer.

---

## 1. Replit Deployment Model

### 1.1 Тип розгортання

NotebookLM Backend розгортається як **Replit Deployment** (не Repl — не IDE-based ephemeral).

```
Replit Deployment:
  ├── Always-on (не засинає між запитами)
  ├── HTTPS публічний URL: https://<slug>.repl.co
  ├── Окрема від IDE середа виконання
  └── Persistent через Replit Object Storage або external MinIO
```

**Ключова відмінність від Repl:** Deployment продовжує працювати незалежно від стану IDE. Cold start виникає лише при першому старті або після крашу.

### 1.2 Runtime

```
Python 3.11+
FastAPI + Uvicorn
Залежності: requirements.txt або pyproject.toml
Точка входу: uvicorn main:app --host 0.0.0.0 --port 8080
```

### 1.3 Процеси

```
Deployment container:
  PID 1: uvicorn main:app (main HTTP server)
    └── worker threads: asyncio event loop
        ├── /health endpoint
        ├── /jobs/process endpoint (async)
        └── Internal Job Queue (in-memory asyncio Queue)
```

**Invariant:** internal Job Queue є ephemeral — втрачається при рестарті. Persistent state зберігається виключно в MinIO або через callback до Membridge.

---

## 2. Cold Start (Холодний старт)

### 2.1 Cold Start Sequence

```
Container start
  │
  ▼ ~2s
Load environment (Replit Secrets)
  │
  ▼ ~3s
Initialize FastAPI app
  │ load routes, middleware, CORS
  │
  ▼ ~2s
Connect to MinIO (health check)
  │
  ▼ ~1s
Start internal Job Queue worker (asyncio task)
  │
  ▼
Ready: GET /health → {"status":"ok",...}
```

**Типовий cold start:** 8–15 секунд.
**Worst case (після крашу + cold pull):** до 30 секунд.

### 2.2 Cold Start Protection

Orchestration Layer має wait-and-retry при 503 від NLM Backend:

```
POST /jobs/process → 503
  ├── wait 15s
  ├── retry POST /jobs/process
  │   ├── 202 → продовжити
  │   └── 503 → wait 30s → retry (max 3)
  └── після 3 спроб → Job → FAILED
```

**SLO:** cold start ≤ 30s. Якщо сервіс не відповідає > 30s → оператор перевіряє Replit Deployments.

---

## 3. Persistence Model (Модель persistence)

### 3.1 Що є ephemeral

```
/tmp/*                ← ephemeral; очищується при рестарті
Internal Job Queue    ← ephemeral; in-memory asyncio.Queue
Runtime variables     ← ephemeral; завантажуються з Secrets при старті
```

### 3.2 Що є persistent

```
MinIO Object Storage:
  projects/<cid>/artifacts/<art_id>.json   ← Артефакти (immutable)
  audit/<YYYYMMDD>/<event_id>.json         ← Аудит-лог

Replit Key-Value Store (опційно):
  job_state:<job_id>                       ← Проміжний стан Job
  # Використовується лише якщо MinIO недоступний як fallback
```

**Principle:** NLM Backend не має власного persistent storage. Вся persistent інформація зберігається в MinIO або передається через callbacks.

### 3.3 Job Recovery після рестарту

При рестарті Deployment:

```
1. Усі in-progress Jobs втрачаються з internal queue
2. Orchestration Layer виявляє відсутність callback протягом timeout
3. Orchestration Layer → Job: RETRY_BACKOFF → повторний POST /jobs/process
4. NLM Backend отримує job знову як нову задачу (ідемпотентно по job_id)
```

**Ідемпотентність:** якщо NLM Backend отримує `job_id`, що вже має артефакт у MinIO → повертає існуючий артефакт без повторного виконання.

---

## 4. Secrets Management (Управління секретами)

### 4.1 Принципи

- Секрети зберігаються виключно в **Replit Secrets** (encrypted at rest).
- Жоден секрет не потрапляє у VCS, `.replit`, або `requirements.txt`.
- Секрети не логуються (структурований logging фільтрує поля credentials).
- Ротація секретів → оновлення в Replit Secrets + редеплой.

### 4.2 Required Secrets

| Secret Key | Призначення |
|-----------|-------------|
| `NOTEBOOKLM_API_KEY` | Auth для вхідних запитів від Orchestration Layer |
| `MINIO_ENDPOINT` | MinIO endpoint |
| `MINIO_ACCESS_KEY` | MinIO access key |
| `MINIO_SECRET_KEY` | MinIO secret key |
| `MINIO_BUCKET` | MinIO bucket name |
| `MEMBRIDGE_CALLBACK_TOKEN` | Auth для callback до Membridge Control Plane |
| `NOTEBOOKLM_ENDPOINT` | URL когнітивного рушія NotebookLM |

### 4.3 Secret Loading

```python
# main.py — завантаження при старті
import os

MINIO_ENDPOINT     = os.environ["MINIO_ENDPOINT"]      # raises KeyError if missing
MINIO_ACCESS_KEY   = os.environ["MINIO_ACCESS_KEY"]
MINIO_SECRET_KEY   = os.environ["MINIO_SECRET_KEY"]
NLM_API_KEY        = os.environ["NOTEBOOKLM_API_KEY"]

# Startup validation
if not all([MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, NLM_API_KEY]):
    raise RuntimeError("Required secrets missing — check Replit Secrets")
```

Відсутній секрет при старті → RuntimeError → Deployment не стартує → видно у Replit Deployments dashboard.

---

## 5. CI/CD Pipeline

### 5.1 Workflow

```
Developer pushes to main branch (GitHub)
  │
  ▼
GitHub Actions (якщо налаштовано)
  ├── lint (ruff / black)
  ├── type check (mypy)
  └── unit tests (pytest)
  │
  ▼ (після успішного CI)
Replit GitHub Integration
  └── автоматичний редеплой до Replit Deployment
```

**Альтернативний workflow (manual):**
```bash
# Оновити код у Replit IDE → Deploy → Redeploy
```

### 5.2 Deployment Checklist

До деплою нової версії:

- [ ] Всі secrets присутні у Replit Secrets
- [ ] `GET /health` повертає `200` на попередній версії
- [ ] Якщо зміна Job schema → перевірити зворотню сумісність
- [ ] Якщо зміна Artifact schema → версія артефакту оновлена
- [ ] `requirements.txt` актуальний

Після деплою:

```bash
curl -fsS https://<slug>.repl.co/health
# Очікувана відповідь:
# {"status":"ok","version":"1.x.x","jobs_processed":N}
```

### 5.3 Rollback

```
Replit Deployments → History → Select previous version → Redeploy
```

Rollback займає ~15–30s. У цей час сервіс повертає 503.

---

## 6. CORS та Network Policy

```python
# FastAPI CORS configuration
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://<app>.lovable.app",     # Lovable Frontend
        "https://<worker>.workers.dev",  # Cloudflare Worker
    ],
    allow_methods=["GET", "POST", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)
```

**Принципи:**
- Лише явно перелічені origins мають доступ (не wildcard).
- `OPTIONS` preflight — обробляється автоматично middleware.
- Запити з приватного LAN (Alpine) — не потребують CORS (server-to-server).

---

## 7. Monitoring та Health Check

### 7.1 Health Endpoint

```json
GET /health
{
  "status":          "ok",
  "version":         "1.2.0",
  "jobs_processed":  847,
  "uptime_seconds":  3600,
  "queue_depth":     2,
  "minio_connected": true,
  "nlm_connected":   true
}
```

### 7.2 External Health Check

Membridge Control Plane (або Orchestration Layer) може виконувати periodical health check:

```bash
# Cron або Hatchet scheduled task (кожні 60s):
curl -fsS https://<slug>.repl.co/health
# Якщо відповідь != 200 → alert оператору
```

### 7.3 Structured Logging

```json
{
  "ts":      "2026-02-24T10:00:00Z",
  "level":   "INFO | WARNING | ERROR",
  "job_id":  "uuid",
  "phase":   "FETCHING_CONTEXT | NLM_QUERY | CALLBACK",
  "ms":      142,
  "node":    "replit"
}
```

Логи доступні в Replit Deployments → Logs.

---

## 8. Security Boundaries

| Загроза | Захист |
|---------|--------|
| Несанкціонований доступ до `/jobs/process` | `Authorization: Bearer <NOTEBOOKLM_API_KEY>` |
| Витік секретів у logs | Structured logging фільтрує поля `*_KEY`, `*_SECRET`, `token` |
| SSRF через `context.memory_snapshot_url` | URL whitelist validation: дозволено лише довірені origins |
| Payload injection у NLM query | Input sanitization; максимальна довжина payload 50KB |
| DoS через великі payloads | `max_upload_size: 100KB` у FastAPI middleware |
| Replay attacks | `job_id` ідемпотентний; повторний запит повертає наявний результат без повторного виконання |

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — специфікація сервісу, що тут розгортається
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — `replit-nlm` як вузол топології
- [[БЕЗПЕКА_СИСТЕМИ]] — security principles застосовані тут

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — Recovery Playbook посилається на Replit dashboard
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — cold start вплив на Job Queue
```
---
### integration/ІНТЕГРАЦІЯ_MEMORY_BACKEND.md
**Розмір:** 11,962 байт
```text
---
tags:
  - domain:storage
  - status:canonical
  - format:spec
  - feature:memory
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Інтеграція: Memory Backend"
dg-publish: true
---

# Інтеграція: Memory Backend

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає архітектурну роль, структуру сховища, протоколи збирання контексту та межі авторитету Memory Backend у системі Garden Bloom.

Memory Backend складається з двох нерозривно пов'язаних шарів:

- **Mastra Runtime** — stateless-інтерпретатор агентів; читає `_agent.md`, виконує логіку через LLM, повертає Пропозиції.
- **`garden-bloom-memory` git-монорепо** — єдине джерело правди для агентної пам'яті Layer 1 та Layer 2; версійоване, аудитуємо, відновлюване.

**Аксіома A3:** Mastra не утримує стану між запусками — кожен Run є clean start.
**Аксіома A1:** `garden-bloom-memory` є частиною canonical storage; пряме записування в нього поза Proposal lifecycle заборонене (A2).

---

## 1. Структура git-монорепо

```
garden-bloom-memory/
├── memory/
│   └── <agentId>/
│       ├── snapshot.md       ← Layer 1: поточний стан агента   (≤ 2K tokens)
│       ├── facts.md          ← Layer 1: факти та знання         (≤ 8K tokens)
│       ├── open_loops.md     ← Layer 1: відкриті питання        (≤ 2K tokens)
│       ├── decisions.md      ← Layer 2: explicit-only (рішення)
│       ├── changelog.md      ← Layer 2: git-history summary
│       └── runs/
│           └── run_<id>/
│               └── artifacts/
└── logic/
    └── <agentId>/
        ├── current.drakon.json  ← поточна DRAKON-діаграма логіки
        ├── current.pseudo.md    ← поточний псевдокод
        └── versions/
            ├── v1.0/
            └── v1.1/
```

---

## 2. Memory Layer Model (DiffMem)

### 2.1 Layer 1 — Auto-load (≤ 12K tokens сукупно)

Завантажується автоматично перед кожним Run через Orchestration Layer.

| Файл | Призначення | Ліміт |
|------|-------------|-------|
| `snapshot.md` | Поточний стан агента | ≤ 2K tokens |
| `facts.md` | Факти, знання, патерни | ≤ 8K tokens |
| `open_loops.md` | Відкриті питання та залежності | ≤ 2K tokens |

**Hard limit:** сукупний розмір Layer 1 ≤ 12K tokens. Перевищення → автоматичне витіснення надлишку до Layer 2 (Memory Eviction).

### 2.2 Layer 2 — Explicit-only (необмежений)

Завантажується лише за явним запитом агента через інструмент `read-memory(layer=2)`.

| Файл / Директорія | Призначення |
|-------------------|-------------|
| `decisions.md` | Минулі рішення з обґрунтуванням |
| `changelog.md` | Стислий git-лог змін пам'яті |
| `runs/` | Артефакти виконань |

### 2.3 Memory Eviction (Витіснення пам'яті)

```
Layer 1 size > 12K tokens
        │
        ▼
  Identify oldest / least-referenced entries in facts.md
        │
        ▼
  Move evicted entries → decisions.md (Layer 2)
        │
        ▼
  Propose memory-update via Proposal lifecycle
        │
        ▼
  Gateway applies commit to garden-bloom-memory
```

---

## 3. Entity Graph (Граф сутностей)

Entity Graph — це структурована проекція пам'яті агентів у вигляді вузлів (сутностей) та зв'язків між ними.

**Джерела формування:**
- `facts.md` всіх агентів (витягуються іменовані сутності)
- Wiki-посилання `[[...]]` у документах монорепо
- Метадані Пропозицій (поле `entity_refs`)

**Структура вузла:**

```json
{
  "entity_id":    "entity-slug",
  "type":         "agent" | "concept" | "artifact" | "decision",
  "label":        "Human-readable name",
  "refs":         ["source-file-path", ...],
  "last_updated": "2026-02-24T00:00:00Z"
}
```

**Використання:**
- NotebookLM Backend запитує Entity Graph для Proposal Preprocessor
- Brief Generator зіставляє `entity_refs` із графом для збагачення брифу
- Semantic Guard перевіряє консистентність нових Пропозицій відносно графу

---

## 4. BM25 Search (Повнотекстовий пошук)

Memory Backend надає інструмент `search-notes(query, top_k)` на базі BM25-індексу над усім монорепо.

**Індексовані джерела:**
- `memory/<agentId>/snapshot.md`, `facts.md`, `open_loops.md`
- `logic/<agentId>/current.pseudo.md`
- Усі markdown-файли у `sources/` агентів

**Параметри запиту:**

```json
{
  "query":    "рядок природною мовою",
  "top_k":   10,
  "filters": {
    "agent_id": "optional-agent-slug",
    "layer":    1 | 2 | null
  }
}
```

**Відповідь:**

```json
{
  "results": [
    {
      "score":   0.87,
      "file":    "memory/architect-guardian/facts.md",
      "excerpt": "... релевантний фрагмент ...",
      "layer":   1
    }
  ]
}
```

---

## 5. Context Assembly (Збирання контексту)

Context Assembly — процес формування контекстного пакету для агентного Run або для виклику NotebookLM Backend.

```
Orchestration Layer запитує context
         │
         ▼
  ┌──────────────────────────────────────────┐
  │         Context Assembly Protocol        │
  │                                          │
  │  1. GET memory/<agentId>/Layer-1 (git)   │
  │     → snapshot.md + facts.md +           │
  │       open_loops.md                      │
  │                                          │
  │  2. GET agents/<slug>/sources/* (MinIO)  │
  │     → domain-knowledge.md               │
  │       procedures.md                     │
  │                                          │
  │  3. BM25 search (якщо є query_hint)      │
  │     → top-K релевантних фрагментів       │
  │                                          │
  │  4. Перевірка ліміту: ≤ 200K tokens      │
  │     total (context window per agent)     │
  │                                          │
  │  5. Serialize → context_snapshot JSON    │
  └──────────────────────────────────────────┘
         │
         ▼
  Передати до Mastra / NLM Backend
```

**Performance SLO:** P95 context assembly < 5s.

---

## 6. Роль у Canonical Conveyor (Канонічний Конвеєр)

```
Phase 1: TRIGGER         ← Inbox приймає намір
Phase 2: ENQUEUE         ← Orchestration Layer ставить в чергу
Phase 3: LOAD CONTEXT  ◄── Memory Backend: Layer-1 + sources + BM25
Phase 4: EXECUTE         ← Mastra (stateless); інструменти: read-memory, notebooklm-query
Phase 5: PERSIST       ◄── Memory Backend: отримує propose-memory-update
Phase 6: FINALIZE        ← Orchestration Layer; manifest.json
Phase 7: NOTIFY          ← Gateway → Frontend
```

Memory Backend бере участь у Phase 3 (читання) та Phase 5 (пропозиція оновлення).

**Інваріант Phase 5:** оновлення пам'яті — це Пропозиція, що проходить повний Proposal lifecycle. Mastra не пише безпосередньо в монорепо (A2).

---

## 7. Write Protocol (Протокол запису)

```
Mastra генерує memory_update → {file, operation, content}
         │
         ▼
POST /memory/propose  (через Gateway)
         │
         ▼
Gateway → Orchestration Layer → Proposal {status: pending}
         │
         ▼
Owner review (або auto-approve за правилом)
         │
         ▼
Apply Engine → git commit до garden-bloom-memory
```

**Один Proposal Apply = один git commit.** Human може перевірити `git log` для повного аудиту.

---

## 8. API Contract (Контракт API)

| Метод | Шлях | Хто може викликати | Призначення |
|-------|------|--------------------|-------------|
| `GET` | `/memory/context?agent={slug}` | NLM Backend, Orch. Layer | Context assembly (Layer 1) |
| `GET` | `/memory/layer2?agent={slug}` | Mastra tool | Явне завантаження Layer 2 |
| `POST` | `/memory/propose` | Gateway | Пропозиція оновлення пам'яті |
| `GET` | `/memory/search?q={query}` | NLM Backend, Mastra | BM25 пошук |
| `GET` | `/entities/{id}` | NLM Backend | Entity Graph lookup |
| `GET` | `/health` | будь-хто | Service health |

---

## 9. Failure Scenarios та Recovery

| Сценарій | Поведінка | Recovery |
|----------|-----------|----------|
| git-монорепо недоступний | Context Assembly → timeout | Phase 3 повторно через 5s; після 3 спроб Run → `failed` |
| BM25 індекс застарів | Застарілі результати пошуку | Cron-переіндексація кожні 6 годин; або примусово `POST /memory/reindex` |
| Memory Eviction loop | Layer 1 постійно перевищує ліміт | Operator переглядає `facts.md`; архівує застарілі факти вручну через Proposal |
| Proposal Apply conflict | git merge conflict у монорепо | Apply Engine → `failed`; оператор резолвить вручну; Proposal → `retry` |
| Layer 1 corruption | snapshot.md порожній або нечитабельний | Відновлення з `git revert`; або остання версія з `git log` |

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — аксіоми A1 (storage canonical), A2 (consent), A3 (stateless), A7 (bounded memory)
- [[КОНТРАКТ_АГЕНТА_V1]] — визначення Layer 1 / Layer 2 та структури `_agent.md`
- [[ПАМ_ЯТЬ_АГЕНТА_GIT_DIFFMEM_V1]] — DiffMem: канонічна модель агентної пам'яті

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — context assembly для NLM-викликів
- [[ІНТЕГРАЦІЯ_MEMBRIDGE]] — Membridge синхронізує SQLite; Memory Backend керує git-монорепо
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — Phase 3 / Phase 5 Canonical Conveyor
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — Memory Backend як вузол топології
```
---
### integration/_INDEX.md
**Розмір:** 8,712 байт
```text
---
tags:
  - domain:meta
  - status:canonical
  - format:inventory
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Integration Layer — Індекс пакету"
dg-publish: true
---

# Integration Layer — Індекс пакету

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Цей пакет визначає архітектурний шар інтеграції між чотирма компонентами, що розширюють ядро Garden Seedling:

- **NotebookLM Backend** — FastAPI Cognitive Proxy (Replit); інструмент `notebooklm-query`
- **Memory Backend** — Mastra runtime + `garden-bloom-memory` git-монорепо
- **Membridge Control Plane** — інфраструктура синхронізації пам'яті між вузлами
- **Lovable Frontend** — Projection Layer; читає канонічний стан через Gateway

Усі документи цього пакету є Tier-1 canonical і є частиною NotebookLM Canonical Set.

---

## 1. Manifest

| Документ | Домен | Формат | Призначення |
|----------|-------|--------|-------------|
| [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] | `api` | `spec` | FastAPI Cognitive Proxy: ролі, контракт, стан-машина |
| [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] | `storage` | `spec` | Mastra + git memory: Layer 1/2, BM25, context assembly |
| [[ІНТЕГРАЦІЯ_MEMBRIDGE]] | `storage` | `contract` | Leadership, lease, artifact registry, control-plane API |
| [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] | `frontend` | `spec` | Inbox, Proposal lifecycle, Job state machine, Artifact viewer |
| [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] | `arch` | `spec` | Вузли, сервіси, порти, trust boundaries, data flow |
| [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] | `execution` | `contract` | State machines, Artifact model, Authority matrix |
| [[DEPLOYMENT_REPLIT_АРХІТЕКТУРА]] | `arch` | `guide` | Replit deployment: cold start, secrets, persistence, CI/CD |

---

## 2. Позиція в архітектурі Garden Seedling

```
┌─────────────────────────────────────────────────────────┐
│                  Garden Bloom System                    │
│                                                         │
│  ┌──────────────┐   Gateway   ┌────────────────────┐   │
│  │   Lovable    │◄──────────► │  Cloudflare Worker │   │
│  │  Frontend    │  (read-only)│  (write gatekeeper) │   │
│  └──────────────┘             └────────┬───────────┘   │
│                                        │               │
│              ┌─────────────────────────┼─────────────┐  │
│              │     Orchestration Layer │(Hatchet)    │  │
│              └─────────────────────────┬─────────────┘  │
│                         ┌─────────────┴──────────────┐  │
│                         │        Mastra Runtime       │  │
│                         │   ┌─────────┐  ┌────────┐  │  │
│                         │   │NLM Tool │  │Memory  │  │  │
│                         │   │(FastAPI)│  │Tool    │  │  │
│                         │   └────┬────┘  └───┬────┘  │  │
│                         └────────┼───────────┼───────┘  │
│                                  │           │          │
│  ┌───────────────────┐     ┌─────▼──────┐  ┌─▼───────┐ │
│  │  Membridge        │     │ NLM Backend│  │ Memory  │ │
│  │  Control Plane    │     │ (Replit)   │  │ Backend │ │
│  │  Alpine :8000/8001│     └────────────┘  │(Mastra/ │ │
│  └──────────┬────────┘                     │ git)    │ │
│             │                              └────┬────┘ │
│  ┌──────────▼────────────────────────────────▼──┐     │
│  │              MinIO Object Storage             │     │
│  │  (canonical DB · artifacts · agent definitions) │   │
│  └───────────────────────────────────────────────┘    │
└─────────────────────────────────────────────────────────┘
```

---

## 3. Залежності між документами

```
_INDEX
├── RUNTIME_TOPOLOGY_NOTEBOOKLM        ← читати першим
├── JOB_QUEUE_ТА_ARTIFACT_MODEL        ← читати другим
├── ІНТЕГРАЦІЯ_MEMBRIDGE               ← залежить від TOPOLOGY
├── ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND      ← залежить від JOB_QUEUE + MEMBRIDGE
├── ІНТЕГРАЦІЯ_MEMORY_BACKEND          ← залежить від MEMBRIDGE
├── ІНТЕГРАЦІЯ_FRONTEND_LOVABLE        ← залежить від JOB_QUEUE + NLM
└── DEPLOYMENT_REPLIT_АРХІТЕКТУРА      ← залежить від NLM_BACKEND
```

**Порядок читання для нового учасника:**
1. [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — де що запущено
2. [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — як рухається робота
3. [[ІНТЕГРАЦІЯ_MEMBRIDGE]] — як синхронізується пам'ять
4. [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — як обробляються завдання
5. [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — як збирається контекст
6. [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] — як відображається стан
7. [[DEPLOYMENT_REPLIT_АРХІТЕКТУРА]] — як розгортається сервіс

---

## 4. Authority Boundaries пакету

| Компонент | MinIO / git | Artifact Store | Job Queue | Leadership Lease |
|-----------|:-----------:|:--------------:|:---------:|:----------------:|
| NotebookLM Backend | Append | Write (нові артефакти) | Read + Status | — |
| Memory Backend | Write (primary) | Read | — | — |
| Membridge Control Plane | Registry (metadata) | Registry | — | Write |
| Lovable Frontend | — | Read | Write (create) | — |
| Membridge Agent | Read/Write local | — | — | Heartbeat |

**Аксіома A2 (незмінна):** жоден компонент не пише в канонічне сховище поза межами своєї authority boundary.

---

## 5. Versioning Policy

- Версія пакету: `1.0.0` (2026-02-24)
- Оновлення будь-якого документу: оновити `updated:` у frontmatter відповідного файлу.
- Зміна authority boundaries або state machine invariants → мажорна версія всього пакету.
- Публікація у NotebookLM: усі документи з `dg-publish: true`.

---

## Semantic Relations

**Цей документ є частиною:**
- [[ІНДЕКС]] — master entry point Garden Seedling

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — аксіоми A1–A7, що визначають межі всіх інтеграцій
- [[КАНОНІЧНА_МОДЕЛЬ_АВТОРИТЕТУ_СХОВИЩА]] — матриця запису/читання

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]]
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]]
- [[ІНТЕГРАЦІЯ_MEMBRIDGE]]
- [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]]
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]]
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]]
- [[DEPLOYMENT_REPLIT_АРХІТЕКТУРА]]
```
---
### integration/RUNTIME_TOPOLOGY_NOTEBOOKLM.md
**Розмір:** 11,427 байт
```text
---
tags:
  - domain:arch
  - status:canonical
  - format:spec
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Runtime Topology: NotebookLM Integration Layer"
dg-publish: true
---

# Runtime Topology: NotebookLM Integration Layer

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає повну runtime-топологію системи Garden Bloom: вузли, сервіси, порти, мережеві зони, trust boundaries та потік даних між компонентами Integration Layer.

Цей документ є операційною картою системи. Будь-які зміни у топології (нові вузли, зміна портів, зміна trust boundary) вимагають оновлення цього документу.

---

## 1. Node Inventory (Інвентар вузлів)

| Node | Тип | IP / Host | Роль |
|------|-----|-----------|------|
| `alpine` | Control plane (x86_64) | `192.168.3.184` | Membridge Server + Agent; Primary node |
| `rpi` | Edge (ARM64 RPi) | `192.168.3.x` | Membridge Agent; Secondary node |
| `orange` | Edge (ARM64 Orange Pi) | `192.168.3.x` | Membridge Agent; Secondary node |
| `replit-nlm` | Cloud (Replit) | `<slug>.repl.co` | NotebookLM Backend (FastAPI) |
| `cloudflare` | CDN / Edge | global | Gateway (Cloudflare Worker) |
| `lovable` | Cloud SPA | `<app>.lovable.app` | Frontend (React) |
| `minio` | Storage | `<minio-host>` | Object storage (canonical) |
| `github` | Git hosting | `github.com` | `garden-bloom-memory` monorepo |

---

## 2. Service-to-Node Mapping (Сервіси по вузлах)

### 2.1 Alpine (192.168.3.184) — Control Plane

| Сервіс | Порт | Init | Опис |
|--------|------|------|------|
| `membridge-server` | `8000` | OpenRC | Control Plane API + Web UI |
| `membridge-agent` | `8001` | OpenRC | Local agent; heartbeat sender |
| `claude-mem-worker` | `37777` | systemd/rc | Claude CLI memory worker |

### 2.2 RPi / Orange Pi — Edge Nodes

| Сервіс | Порт | Init | Опис |
|--------|------|------|------|
| `membridge-agent` | `8001` | OpenRC | Local agent; secondary sync |
| `claude-mem-worker` | `37777` | systemd/rc | Claude CLI memory worker |

### 2.3 Replit (Cloud)

| Сервіс | Порт | Опис |
|--------|------|------|
| `notebooklm-backend` | `8080` (Replit default) | FastAPI; NLM proxy + Job processor |

### 2.4 Cloudflare (Global Edge)

| Сервіс | Тип | Опис |
|--------|-----|------|
| `cloudflare-worker` | Worker | Gateway: auth, validation, routing |

---

## 3. Port Matrix (Матриця портів)

| Порт | Вузол | Сервіс | Auth | Scope |
|------|-------|--------|------|-------|
| `8000` | Alpine | membridge-server | `X-MEMBRIDGE-ADMIN` | LAN + internal |
| `8001` | Alpine, RPi, Orange | membridge-agent | localhost exempt / `X-MEMBRIDGE-AGENT` | LAN |
| `37777` | Alpine, RPi, Orange | claude-mem-worker | none (localhost only) | localhost |
| `8080` | Replit | NLM Backend | `Bearer <NLM_API_KEY>` | public HTTPS |
| `443` | Cloudflare | Gateway | `Bearer <JWT>` | public HTTPS |

---

## 4. Trust Boundaries (Межі довіри)

```
╔══════════════════════════════════════════════════════════════╗
║  ZONE: Public Internet                                       ║
║                                                              ║
║   [Lovable Frontend]──HTTPS──►[Cloudflare Worker/Gateway]   ║
║                                        │                    ║
║   [Replit NLM Backend]◄──HTTPS─────────┤                    ║
║                                        │                    ║
╠═══════════════════════ZONE: Trusted Cloud═══════════════════╣
║                                        │                    ║
║   Gateway ──────────────────►[MinIO Object Storage]         ║
║   Gateway ──────────────────►[GitHub: garden-bloom-memory]  ║
║   Gateway ──────────────────►[Orchestration Layer: Hatchet] ║
║                                        │                    ║
╠═══════════════════════ZONE: Private LAN (192.168.3.0/24)════╣
║                                        │                    ║
║   [Alpine :8000]◄──────────────────────┘                    ║
║   [Alpine :8001]                                             ║
║   [RPi :8001] ──heartbeat──► [Alpine :8000]                  ║
║   [Orange :8001] ─heartbeat─► [Alpine :8000]                 ║
║                                                              ║
║   All nodes ──MinIO sync──► [MinIO] (S3 over HTTPS)          ║
╚══════════════════════════════════════════════════════════════╝
```

**Правила перетину меж:**

1. Frontend → Gateway: завжди HTTPS + JWT; ніяких прямих з'єднань до LAN.
2. Gateway → MinIO: S3 API over HTTPS; credentials лише у Worker environment vars.
3. LAN nodes → MinIO: S3 over HTTPS; credentials у `config.env` (out of VCS).
4. Replit → Gateway: HTTP callback після Job completion; Bearer token.
5. LAN nodes ↔ між собою: HTTP на приватному діапазоні; `X-MEMBRIDGE-AGENT` auth.

---

## 5. Data Flow Diagram (Потік даних)

### 5.1 Agent Run Flow

```
Owner
  │ POST /agents/{slug}/run
  ▼
Cloudflare Worker (Gateway)
  │ validate JWT
  │ write status: "requested"
  │ trigger Orchestration Layer
  ▼
Orchestration Layer (Hatchet)
  │ GET agents/{slug}/_agent.md ──────────────────► MinIO
  │ GET memory/{agentId}/Layer-1 ─────────────────► GitHub (garden-bloom-memory)
  │ GET agents/{slug}/sources/* ──────────────────► MinIO
  │ update status: "running"
  │
  ▼
Mastra Runtime (stateless)
  │ tool: notebooklm-query(question)
  │   └──────────────────────────────────────────► Replit NLM Backend
  │                                                   │ NLM query
  │                                                   ▼
  │                                                NotebookLM (Google)
  │                                                   │ grounded response
  │                                                   ◄
  │ tool: create-proposal({intent, target, payload})
  │
  ▼
Orchestration Layer
  │ write proposals/*.json ──────────────────────► MinIO
  │ POST /memory/propose ─────────────────────────► Gateway
  │ update status: "completed"
  │ write manifest.json ─────────────────────────► MinIO
  │
  ▼
Gateway notifies
  ▼
Frontend displays result
```

### 5.2 Memory Sync Flow (Membridge)

```
Claude CLI session (Alpine/RPi/Orange)
  │ writes to claude-mem.db (local SQLite)
  │
  ▼ (on session Stop hook)
hooks/claude-mem-hook-push
  │ POST /register_project ──────────────────────► membridge-agent :8001
  │
  ▼
sqlite_minio_sync.py push_sqlite
  │ check leadership (primary?) ─────────────────► MinIO: lease.json
  │ VACUUM INTO snapshot
  │ acquire push lock ────────────────────────────► MinIO: active.lock
  │ upload db + sha256 ───────────────────────────► MinIO: db/<sha256>.db
  │
  ▼ (on session Start hook)
hooks/claude-mem-hook-pull
  │ compare sha256 ───────────────────────────────► MinIO
  │ backup local db
  │ download + replace local db
  │ restart worker :37777
```

### 5.3 Heartbeat Flow

```
membridge-agent :8001 (Alpine/RPi/Orange)
  │ read ~/.membridge/agent_projects.json
  │ every HEARTBEAT_INTERVAL_SECONDS (10s)
  │
  ▼
POST /agent/heartbeat ───────────────────────────► membridge-server :8000 (Alpine)
  {node_id, canonical_id, project_id, ip_addrs}
  │
  ▼
_nodes[] + _heartbeat_projects[] (in-memory)
  │
  ▼
GET /projects ◄───── Web UI (Alpine :8000/ui)
```

---

## 6. Network Zones (Мережеві зони)

| Зона | Компоненти | Протокол | Auth |
|------|-----------|---------|------|
| Public Internet | Lovable, Cloudflare Worker | HTTPS | JWT |
| Trusted Cloud | MinIO, GitHub, Hatchet, Replit | HTTPS/S3 | Bearer / S3 keys |
| Private LAN | Alpine, RPi, Orange | HTTP (LAN) | none / Agent key |
| Localhost | claude-mem-worker, hooks | HTTP 127.0.0.1 | none |

---

## 7. Failure Modes (Топологічний рівень)

| Сценарій | Вплив | Ізоляція |
|----------|-------|----------|
| Alpine offline | Heartbeat зупиняється; Web UI недоступний | RPi/Orange продовжують локальну роботу |
| MinIO недоступний | Push/pull fail; git-монорепо продовжує | Локальні DB незмінні; claude-mem hooks fail-open |
| Replit cold start | Job → QUEUED до ready | Orchestration Layer retry backoff |
| Cloudflare incident | Frontend недоступний | Backend/LAN продовжують незалежно |
| RPi offline | Heartbeat зупиняється для цього вузла | Alpine залишається Primary |
| GitHub недоступний | Context assembly: Layer 1 unavailable | Run → failed; Layer 2 unaffected |

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — A1, A5; визначають топологічні constraints
- [[БЕЗПЕКА_СИСТЕМИ]] — security principles що визначають trust boundary

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — Replit як вузол NLM Backend
- [[ІНТЕГРАЦІЯ_MEMBRIDGE]] — Alpine :8000/:8001 деталі
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — GitHub як вузол garden-bloom-memory
- [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] — Lovable як external projection node
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — data flow в контексті job execution
- [[DEPLOYMENT_REPLIT_АРХІТЕКТУРА]] — деплой на Replit node
```
---
### integration/ІНТЕГРАЦІЯ_FRONTEND_LOVABLE.md
**Розмір:** 11,509 байт
```text
---
tags:
  - domain:frontend
  - status:canonical
  - format:spec
  - feature:proposal
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Інтеграція: Lovable Frontend"
dg-publish: true
---

# Інтеграція: Lovable Frontend

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає роль Lovable Frontend як Projection Layer у системі Garden Bloom, специфікацію його інтеграції з backend через Gateway, та поведінку кожного ключового UI-компонента відносно Proposal lifecycle, Job state machine та Artifact viewer.

**Аксіома A6:** Frontend є виключно Projection Layer. Він читає канонічний стан через Gateway. Frontend не має write authority до canonical storage — усі мутаційні наміри проходять через Inbox → Proposal lifecycle.

---

## 1. Роль у системі

```
Owner
  │ дії (create proposal, approve, view artifacts)
  ▼
Lovable Frontend (React SPA)
  │ тільки читання + Inbox entries
  ▼
Cloudflare Worker (Gateway)
  │ auth · validation · rate-limiting
  ├──► MinIO (canonical state — reads)
  ├──► Orchestration Layer (trigger runs)
  └──► Inbox (write Inbox Entries → Proposals)
```

Frontend ніколи не взаємодіє з Membridge Control Plane, MinIO або Memory Backend напряму. Єдина точка входу — Gateway.

---

## 2. Inbox (Папка вхідних)

Inbox є канонічним входом для всіх намірів власника. Кожна дія у Frontend, що вносить зміни до системи, генерує Inbox Entry.

### 2.1 Inbox Entry Format

```json
{
  "id":     "inbox_2026-02-24_abc123",
  "source": {
    "type":          "ui",
    "identity":      "owner",
    "authenticated": true,
    "timestamp":     "2026-02-24T10:00:00Z"
  },
  "intent": {
    "action":  "propose-edit | propose-artifact | propose-note | propose-tag",
    "target":  "notes/path/to/file",
    "payload": { "...": "..." }
  },
  "metadata": {
    "correlation_id": "run_2026-02-24_...",
    "priority":       "normal | high",
    "ttl_hours":      72
  }
}
```

### 2.2 Джерела Inbox Entry

| Дія у Frontend | action | target |
|----------------|--------|--------|
| Створити нову Пропозицію | `propose-edit` | шлях нотатки |
| Запустити агента вручну | `propose-artifact` | `agents/{slug}` |
| Додати тег до артефакту | `propose-tag` | `artifacts/{id}` |
| Залишити коментар | `propose-note` | довільний шлях |

---

## 3. Proposal Lifecycle (Жмттєвий цикл Пропозиції)

### 3.1 State Machine

```
           ┌──────────┐
           │ PENDING  │◄── створена Orchestration Layer або Gateway
           └────┬─────┘
                │
     ┌──────────┴──────────┐
     │                     │
┌────▼──────┐         ┌────▼──────┐
│ APPROVED  │         │ REJECTED  │
└────┬──────┘         └────┬──────┘
     │                     │
┌────▼──────┐         ┌────▼──────┐
│ APPLYING  │         │ DISCARDED │
└────┬──────┘         └───────────┘
     │
┌────┴──────────┐
│               │
▼               ▼
APPLIED       FAILED
               │
            (retry або
             manual fix)
```

**Також:**
- `PENDING → AUTO_APPROVED` (за правилом auto-approve)
- `PENDING → EXPIRED` (cron TTL check, default 72h)

### 3.2 UI Actions на кожному стані

| Стан | Дії власника у Frontend |
|------|------------------------|
| `PENDING` | Approve · Reject · View details |
| `APPROVED` | View details (read-only; Apply Engine обробляє) |
| `APPLYING` | View details + progress indicator |
| `APPLIED` | View diff · Archive |
| `REJECTED` | View reason · Resubmit (нова Пропозиція) |
| `FAILED` | View error · Retry via API |
| `EXPIRED` | View · Resubmit |

---

## 4. Job State Machine (Стан завдання у Frontend)

Frontend відображає стан Job, отриманий через polling або SSE від Gateway.

```
  CREATED
     │
  QUEUED         ← відображається: "В черзі..."
     │
  CONTEXT_ASSEMBLY  ← "Збирання контексту..."
     │
  NOTEBOOKLM_CALL   ← "Обробка NotebookLM..."
     │
  ARTIFACT_WRITE    ← "Збереження результату..."
     │
  COMPLETE       ← відображається: Artifact Viewer
     │
  (або)
  RETRY_BACKOFF  ← "Повтор через Xs..."
     │
  FAILED         ← відображається: помилка + можливість requeue
     │
  DEAD           ← відображається: "Потребує ручного втручання"
```

**Polling interval:** 2s поки Job у `QUEUED` / `*_ASSEMBLY` / `*_CALL`; 10s для `RETRY_BACKOFF`.

---

## 5. Artifact Viewer (Переглядач артефактів)

Artifact Viewer відображає фіналізовані артефакти. Після переходу Job у `COMPLETE` — автоматичний redirect до відповідного артефакту.

### 5.1 Типи артефактів та їх відображення

| Тип артефакту | Відображення |
|---------------|-------------|
| `RESEARCH_BRIEF` | Структурований звіт із розгортуваними секціями та посиланнями на джерела |
| `BRIEF` | Стислий документ із підсвічуванням entity references |
| `PREPROCESSED_PROPOSAL` | Diff-вигляд: original vs enriched; список помічених проблем |

### 5.2 Artifact metadata schema

```json
{
  "artifact_id":  "art-uuid-v4",
  "job_id":       "uuid-v4",
  "type":         "RESEARCH_BRIEF | BRIEF | PREPROCESSED_PROPOSAL",
  "created_at":   "2026-02-24T10:00:00Z",
  "finalized":    true,
  "url":          "https://...",
  "entity_refs":  ["entity-slug-1"],
  "tags":         ["research", "architecture"]
}
```

**Invariant:** `finalized: true` → артефакт є immutable. Frontend не пропонує редагування фіналізованих артефактів.

---

## 6. API Integration (Інтеграція з Gateway)

### 6.1 Endpoints, які використовує Frontend

| Метод | Шлях | Призначення |
|-------|------|-------------|
| `POST` | `/agents/{slug}/run` | Запуск агента вручну |
| `GET` | `/runs/{runId}/status` | Polling статусу Run |
| `GET` | `/proposals` | Список Пропозицій |
| `GET` | `/proposals/{id}` | Деталі Пропозиції |
| `POST` | `/proposals/{id}/approve` | Схвалення |
| `POST` | `/proposals/{id}/reject` | Відхилення |
| `GET` | `/jobs` | Список Job |
| `GET` | `/jobs/{id}` | Деталі Job |
| `GET` | `/artifacts` | Список артефактів |
| `GET` | `/artifacts/{id}` | Деталі артефакту |
| `POST` | `/inbox` | Надіслати Inbox Entry |

### 6.2 Auth model

Всі запити Frontend → Gateway несуть `Authorization: Bearer <JWT>`.

- JWT видається Gateway при login
- Owner JWT → повний доступ до read + create Inbox Entries + approve/reject Proposals
- Zone Guest JWT → read-only для делегованої зони
- Відсутній JWT → 401

### 6.3 Error handling у Frontend

| HTTP код | Поведінка Frontend |
|----------|--------------------|
| 401 | Redirect до login |
| 403 | Toast: "Недостатньо прав" |
| 404 | Toast: "Не знайдено" |
| 422 | Inline validation error |
| 503 | Toast: "Сервіс тимчасово недоступний; повторіть пізніше" |

---

## 7. Runs Dashboard

Runs Dashboard відображає поточний та архівний стан усіх виконань (Runs) у системі.

```
┌─────────────────────────────────────────────────────┐
│  Runs Dashboard                                     │
│                                                     │
│  [Filter: ALL | RUNNING | COMPLETED | FAILED]       │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Run ID       Agent      Status      Duration  │  │
│  │ run_024...   architect  COMPLETED   34s       │  │
│  │ run_023...   guardian   RUNNING     12s ⟳     │  │
│  │ run_022...   guardian   FAILED      8s  ⚠     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [Click run → Run Detail: phases + artifacts]       │
└─────────────────────────────────────────────────────┘
```

**Backend gap:** статус Run читається з `agents/{slug}/runs/{runId}/status.json` у MinIO через Gateway. Якщо Gateway не повертає Run-список — Runs Dashboard порожній (відомий gap: [[RUNS_DASHBOARD_BACKEND_GAP_V1]]).

---

## 8. Security Boundaries

- Frontend не зберігає секрети локально (не зберігає MinIO credentials, Admin keys).
- JWT зберігається в httpOnly cookie або sessionStorage (не localStorage).
- Frontend не читає `X-MEMBRIDGE-ADMIN` або `X-MEMBRIDGE-AGENT` headers.
- CORS: Gateway дозволяє лише origin Lovable SPA.
- CSP: inline scripts заборонені.

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — A5 (Gateway sole entry point), A6 (Frontend is projection)
- [[КОНТРАКТИ_API_V1]] — визначення Gateway endpoints
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — Job state machine та Artifact model
- [[СИСТЕМА_PROPOSAL_V1]] — Proposal lifecycle у Garden Seedling
- [[INBOX_ТА_ЦИКЛ_ЗАПУСКУ_V1]] — Inbox та Run lifecycle для UI

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — відображення результатів NLM у Frontend
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — Lovable як external projection node
```
---
### integration/ПЕРСПЕКТИВА_АГЕНТНОЇ_РОЗРОБКИ.md
**Розмір:** 18,225 байт
```text
---
tags:
  - domain:arch
  - status:canonical
  - format:spec
  - feature:orchestration
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Перспектива: Комплексна агентна система розробки"
dg-publish: true
---

# Перспектива: Комплексна агентна система розробки

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає стратегічну перспективу еволюції поточної Integration Layer у повноцінну комплексну систему розробки будь-яких програмних рішень на основі агентів, персистентної пам'яті сесій та мультимодального доступу до LLM.

Поточний стан — набір інтегрованих компонентів. Цільовий стан — **Agentic Development Platform**: середовище, де людина-розробник і набір спеціалізованих агентів працюють у спільному контексті, з повною пам'яттю, через уніфікований інтерфейс, на розподіленій інфраструктурі.

---

## 1. Поточний стан системи

```
Claude CLI (сесія)
  ├── Membridge hooks       → синхронізує claude-mem.db між вузлами
  ├── Memory Backend        → git-монорепо Layer 1/2
  ├── NotebookLM Backend    → FastAPI proxy для document-grounded reasoning
  └── Lovable Frontend      → Projection + Proposal lifecycle
```

**Що вже працює:**
- Персистентна пам'ять сесій (claude-mem.db → MinIO через Membridge)
- Синхронізація між вузлами (Alpine/RPi/Orange) з leadership моделлю
- Ізольований проксі до NotebookLM як інструмент агентів
- Proposal lifecycle для consent-based мутацій
- Distributed leadership із lease protocol

**Що потребує доопрацювання:**
- Агенти ще не доступні як MCP-сервери всередині Claude CLI
- Немає уніфікованого LLM routing шару
- Development loop не замкнений: Implementation → Verification → Runtime не автоматизовані
- Немає cross-session entity continuity (кожна сесія стартує майже з нуля)

---

## 2. Цільова архітектура

```
┌─────────────────────────────────────────────────────────────────┐
│                  Agentic Development Platform                   │
│                                                                 │
│  Developer                                                      │
│     │                                                           │
│     ▼                                                           │
│  Claude CLI ◄──── MCP Bus (інструменти) ────────────────────┐  │
│     │                │                                       │  │
│     │         ┌──────┼──────────────────────────┐           │  │
│     │         │      │   MCP Servers (агенти)   │           │  │
│     │         │  [memory-agent]  [notebooklm]   │           │  │
│     │         │  [code-reviewer] [spec-agent]   │           │  │
│     │         │  [test-runner]   [arch-guardian] │           │  │
│     │         └──────────────────────────────────┘           │  │
│     │                                                         │  │
│     ▼                                                         │  │
│  Canonical Conveyor                                           │  │
│  Vision→Modeling→Spec→Impl→Verify→Runtime→Memory→Evolution   │  │
│     │                                                         │  │
│     ▼                                                         │  │
│  ┌─────────────────────────────────────────────────────────┐  │  │
│  │              Unified Memory Layer                       │  │  │
│  │  claude-mem.db (session) ← Membridge → MinIO           │  │  │
│  │  garden-bloom-memory (agent) ← git → Layer 1/2         │  │  │
│  │  Entity Graph (cross-session entities)                 │  │  │
│  └─────────────────────────────────────────────────────────┘  │  │
│                                                               │  │
│  ┌─────────────────────────────────────────────────────────┐  │  │
│  │              LLM Access Layer                           │  │  │
│  │  Direct API  │  NotebookLM Proxy  │  Custom Agents     │◄─┘  │
│  │  (Claude)    │  (grounded docs)   │  (specialized)     │     │
│  └─────────────────────────────────────────────────────────┘     │
└─────────────────────────────────────────────────────────────────┘
```

---

## 3. LLM Access Patterns

Система підтримує три паттерни доступу до LLM, кожен для своєї задачі:

### 3.1 Direct API (Прямий API)

```
Claude CLI → Anthropic API (claude-sonnet / claude-opus)
  └── повний контекст сесії
  └── використання для: reasoning, code generation, planning
```

**Вже доступно.** Поточна основа роботи Claude CLI.

### 3.2 Document-Grounded Proxy (Заземлений проксі)

```
Claude CLI → MCP tool: notebooklm-query(question)
  └── FastAPI NotebookLM Backend (Replit)
      └── NotebookLM (Google) — відповідає виключно з документів
  └── використання для: research, spec grounding, anti-hallucination verification
```

**Частково реалізовано.** Потребує реєстрації як MCP server у `~/.claude/settings.json`.

### 3.3 Спеціалізовані агенти як проксі

```
Claude CLI → MCP tool: agent-proxy(agent_slug, task)
  └── Mastra Agent (Orchestration Layer)
      └── LLM вибирається агентом (Claude / GPT / Gemini / NLM)
  └── використання для: code review, security audit, spec generation,
                        test generation, architecture validation
```

**Потребує реалізації.** Ключова точка розширення системи.

---

## 4. Agent-as-MCP-Proxy: Архітектура

Агенти Garden Seedling можуть бути зареєстровані як MCP servers для Claude CLI. Це перетворює Claude CLI на оркестратор, що делегує спеціалізовані задачі спеціалізованим агентам.

### 4.1 Реєстрація MCP server

```json
// ~/.claude/settings.json (або claude_desktop_config.json)
{
  "mcpServers": {
    "memory-agent": {
      "command": "uvx",
      "args": ["mcp-memory-agent"],
      "env": { "MEMBRIDGE_DIR": "/home/vokov/membridge" }
    },
    "notebooklm": {
      "command": "python",
      "args": ["/home/vokov/membridge/mcp/notebooklm_server.py"],
      "env": { "NLM_API_KEY": "..." }
    },
    "arch-guardian": {
      "command": "python",
      "args": ["/home/vokov/membridge/mcp/agent_proxy_server.py"],
      "env": { "AGENT_SLUG": "architect-guardian" }
    }
  }
}
```

### 4.2 MCP Tool Schema для агента-проксі

```
Tool: agent-run
  Input:  { "agent_slug": str, "task": str, "context_hint": str }
  Output: { "artifact_id": str, "result": str, "proposals": [] }

Tool: memory-read
  Input:  { "query": str, "layer": 1 | 2 }
  Output: { "results": [{ "score": float, "excerpt": str }] }

Tool: notebooklm-query
  Input:  { "question": str, "sources": [] }
  Output: { "answer": str, "citations": [] }

Tool: propose-change
  Input:  { "target": str, "action": str, "payload": {} }
  Output: { "proposal_id": str, "status": "pending" }
```

### 4.3 Приклад: Claude CLI як оркестратор

```
Developer: "Проведи code review модуля sqlite_minio_sync.py і запропонуй покращення"

Claude CLI:
  1. tool: memory-read("sqlite_minio_sync architecture decisions")
     → завантажує контекст із Layer 1
  2. tool: notebooklm-query("best practices for distributed sync")
     → отримує заземлену відповідь із документів
  3. Аналізує код + контекст + grounded knowledge
  4. tool: agent-run("code-reviewer", "review sqlite_minio_sync.py")
     → спеціалізований агент виконує глибокий review
  5. tool: propose-change("sqlite_minio_sync.py", "propose-edit", {...})
     → Пропозиція з конкретними змінами

Результат: структурований code review із посиланнями на джерела,
           entity graph зв'язками та конкретними Пропозиціями
```

---

## 5. Unified Memory Layer (Уніфікований шар пам'яті)

Ключова проблема поточного стану: три ізольованих сховища пам'яті без cross-session continuity.

```
Поточно:
  claude-mem.db ──── Membridge ──── MinIO
  garden-bloom-memory ───────────── GitHub git
  Entity Graph ──────────────────── (немає persistence)

Цільовий стан:
  ┌─────────────────────────────────────────────────────────┐
  │              Unified Memory Router                      │
  │                                                         │
  │  Query: "що я знаю про sqlite_minio_sync leadership?"   │
  │                                                         │
  │  → BM25(claude-mem.db)        → session observations   │
  │  → BM25(garden-bloom-memory)  → agent reasoning        │
  │  → Entity Graph lookup        → entity relationships   │
  │  → Merge + rank → unified context                       │
  └─────────────────────────────────────────────────────────┘
              │
              ▼ єдиний контекстний пакет для Claude / агентів
```

**Інваріант:** Unified Memory Router — read-only. Записує виключно через Proposal lifecycle.

---

## 6. Повний Development Loop

```
┌──────────────────────────────────────────────────────────────────┐
│                    Development Loop v2                           │
│                                                                  │
│  1. VISION         Developer → Inbox → Brief Generator (NLM)    │
│     └─ output: BRIEF artifact                                    │
│                                                                  │
│  2. MODELING       arch-guardian agent → Entity Graph update     │
│     └─ output: PREPROCESSED_PROPOSAL artifact                   │
│                                                                  │
│  3. SPEC           spec-agent (MCP) → markdown spec             │
│     └─ output: SPEC artifact; Proposal pending                  │
│                                                                  │
│  4. IMPLEMENTATION Claude CLI + code-agent (MCP)                │
│     └─ reads: SPEC artifact + memory context                    │
│     └─ output: code changes; propose-edit Proposals             │
│                                                                  │
│  5. VERIFICATION   test-runner (MCP) + security-audit (MCP)     │
│     └─ output: VERIFICATION artifact; issues as Proposals       │
│                                                                  │
│  6. RUNTIME        Membridge deploy + OpenRC restart             │
│     └─ health check; metrics; alerts                            │
│                                                                  │
│  7. MEMORY         memory-agent (MCP) → Layer 1/2 update        │
│     └─ git commit до garden-bloom-memory                        │
│                                                                  │
│  8. EVOLUTION      arch-guardian reviews delta                  │
│     └─ proposes logic-update; optimizer agent                   │
│     └─ цикл повторюється                                        │
└──────────────────────────────────────────────────────────────────┘
```

Кожна фаза виробляє Артефакт. Кожна мутація — Пропозиція. Людина схвалює або відхиляє.

---

## 7. Roadmap: Можливі рішення

### Фаза 1 — MCP Integration (найближча)

| Задача | Рішення | Складність |
|--------|---------|-----------|
| Зареєструвати NotebookLM як MCP server | Python MCP server обгортка навколо FastAPI | Low |
| Зареєструвати memory-read як MCP tool | MCP server читає claude-mem.db + git Layer 1 | Low |
| Unified Memory Router (read-only) | BM25 merge через два сховища | Medium |

### Фаза 2 — Agent Proxies

| Задача | Рішення | Складність |
|--------|---------|-----------|
| agent-proxy MCP server | Generic MCP → Mastra bridge | Medium |
| code-reviewer agent | Mastra + Claude + code analysis tools | Medium |
| spec-agent | Маstra + NotebookLM + DRAKON output | Medium |
| Cross-session entity continuity | Entity Graph з persistence у MinIO | High |

### Фаза 3 — Autonomous Development Loop

| Задача | Рішення | Складність |
|--------|---------|-----------|
| Automated verification pipeline | test-runner agent + CI hooks | High |
| Logic Versioning для агентів | Optimizer agent (вже в Garden Seedling spec) | Medium |
| Multi-LLM routing | LLM Router: Claude / GPT / Gemini за задачею | High |
| Self-improving agents | Optimizer agent → logic-update Proposals | High |

---

## 8. Ключові інваріанти перспективи

**I-P1:** Людина залишається у контурі (Human-in-the-Loop) на всіх фазах, де результат є мутацією canonical storage.

**I-P2:** Кожен LLM-виклик у розробницькому контексті має бути заземленим або явно позначеним як ungrounded (для запобігання галюцинацій у коді).

**I-P3:** MCP servers — це адаптери, не нові сховища. Вся персистентність — через Unified Memory Layer.

**I-P4:** Агентна розробка не замінює розробника; вона підсилює його здатність утримувати складну систему в голові через Unified Memory та автоматизацію рутини.

**I-P5:** Будь-яке програмне рішення може бути розроблено у цьому середовищі, якщо воно описується через Spec artifact та верифікується через Verification artifact.

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — аксіоми A1–A7 визначають границі еволюції
- [[КОНТРАКТ_АГЕНТА_V1]] — MCP servers є реалізацією Agent Contract
- [[АБСТРАКЦІЯ_РІВНЯ_ОРКЕСТРАЦІЇ]] — Orchestration Layer залишається vendor-agnostic
- [[ПАМ_ЯТЬ_АГЕНТА_GIT_DIFFMEM_V1]] — Unified Memory базується на DiffMem

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_NOTEBOOKLM_BACKEND]] — еволюція до MCP server
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — еволюція до Unified Memory Router
- [[ІНТЕГРАЦІЯ_MEMBRIDGE]] — залишається інфраструктурою синхронізації
```
---
### architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md
**Розмір:** 17,754 байт
```text
---
tags:
  - domain:runtime
  - status:canonical
  - format:spec
  - feature:membridge-proxy
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Integration: Membridge Claude CLI Proxy"
dg-publish: true
---

# Integration: Membridge Claude CLI Proxy

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Language: English (canonical)

---

## 0. Purpose

This document specifies how the BLOOM Runtime delegates LLM execution to Membridge worker nodes via the Claude CLI Proxy pattern. It defines the roles, envelope formats, lease lifecycle, security boundaries, worker invocation protocol, and context loading rules.

**Key principle:** The BLOOM Runtime orchestrator never executes LLM prompts directly. Instead, it creates LLM-task envelopes and delegates execution to Membridge workers that run Claude CLI locally.

---

## 1. Roles

### 1.1 BLOOM Runtime (Orchestrator / Proxy)

- Accepts LLM-task requests from the frontend or internal pipeline
- Creates task envelopes with context, policy, and desired format
- Routes tasks to available workers using capability-based selection
- Manages lease lifecycle (create, heartbeat, expire, failover)
- Collects results and creates immutable artifacts
- Never executes Claude CLI directly

### 1.2 Membridge Server (Control Plane)

- Maintains registry of worker nodes via heartbeat protocol
- Provides `/agents` and `/projects` endpoints for worker discovery
- Manages leadership leases for memory sync (independent of task leasing)
- Serves as the source of truth for worker availability

### 1.3 Membridge Worker (Edge Node)

- Runs `membridge-agent` on port 8001
- Executes Claude CLI with the provided prompt and context
- Sends heartbeats to confirm liveness during execution
- Returns structured results (output or error) to the orchestrator
- Never writes directly to canonical storage (MinIO)

### 1.4 Authority Boundaries

| Component | LLM Execution | Task Queue | Artifact Store | Canonical Storage |
|-----------|:---:|:---:|:---:|:---:|
| BLOOM Runtime | Delegates | Read/Write | Write (new) | Read only |
| Membridge Server | None | None | Registry | Metadata only |
| Membridge Worker | Executes | Heartbeat | None | Read (local) |

**Axiom:** Workers never write directly to canonical storage. All mutations flow through the BLOOM Runtime after explicit consent.

---

## 2. LLM-Task Envelope

The task envelope is the unit of work delegated to a worker.

### 2.1 Task Structure

```typescript
interface LLMTask {
  id: string;                   // UUID, generated by orchestrator
  context_id: string;           // Execution context identifier
  agent_slug: string;           // Agent definition to use
  prompt: string;               // The LLM prompt text
  context_hints: string[];      // Files/paths to load as context
  policy: {
    timeout_sec: number;        // Max execution time (1-3600s)
    budget: number;             // Token budget (0 = unlimited)
  };
  desired_format: "json" | "text";  // Expected output format
  status: TaskStatus;           // queued | leased | running | completed | failed | dead
  created_at: number;           // Unix timestamp
  updated_at: number;           // Unix timestamp
  lease_id: string | null;      // Active lease ID
  worker_id: string | null;     // Assigned worker
  attempts: number;             // Current attempt count
  max_attempts: number;         // Max retry attempts (1-10, default: 3)
}
```

### 2.2 Task Status State Machine

```
                    ┌──────────┐
                    │  QUEUED   │
                    └────┬─────┘
                         │ lease assigned
                    ┌────▼─────┐
              ┌─────│  LEASED  │─────┐
              │     └────┬─────┘     │
              │          │ worker    │ lease expired
              │          │ starts   │ (no heartbeat)
              │     ┌────▼─────┐     │
              │     │ RUNNING  │     │
              │     └────┬─────┘     │
              │       ┌──┴──┐        │
              │  ┌────▼┐  ┌▼─────┐   │
              │  │DONE │  │FAILED│   │
              │  └─────┘  └──┬───┘   │
              │              │       │
              │         attempts     │
              │         < max?       │
              │        YES │ NO      │
              │    ┌───▼─┐ │        │
              │    │QUEUED│ ▼        ▼
              │    └─────┘ ┌────────────┐
              └───────────►│    DEAD    │
                           └────────────┘
```

| Transition | Trigger | Action |
|-----------|---------|--------|
| queued → leased | Worker assigned via lease | Set lease_id, worker_id |
| leased → running | Worker confirms execution started | Update status |
| running → completed | Worker submits result (success) | Create artifact |
| running → failed | Worker submits error or timeout | Increment attempts |
| failed → queued | attempts < max_attempts | Re-enqueue for retry |
| failed → dead | attempts >= max_attempts | Terminal state |
| leased → queued | Lease expired (no heartbeat) | Release lease, re-enqueue |

---

## 3. Result Envelope

The result envelope is returned by the worker upon task completion.

```typescript
interface LLMResult {
  id: string;                   // UUID
  task_id: string;              // References the original task
  worker_id: string;            // Worker that executed the task
  artifact_id: string;          // Created artifact ID
  status: "success" | "error";
  output: string | null;        // LLM output (if success)
  error_message: string | null; // Error details (if error)
  metrics: {
    duration_ms: number;        // Execution duration
    tokens_used?: number;       // Token consumption (if available)
  };
  completed_at: number;         // Unix timestamp
}
```

### 3.1 Result Validation

The orchestrator validates results before creating artifacts:
1. `task_id` must reference an existing task in `running` or `leased` status
2. `worker_id` must match the worker assigned via the active lease
3. `metrics.duration_ms` must be non-negative
4. If `status === "success"`, `output` must not be null
5. If `status === "error"`, `error_message` must not be null

---

## 4. Lease Lifecycle

Leases bind a task to a worker for a bounded duration.

### 4.1 Lease Structure

```typescript
interface Lease {
  id: string;                   // UUID
  task_id: string;              // Bound task
  worker_id: string;            // Assigned worker
  started_at: number;           // Unix timestamp
  expires_at: number;           // started_at + ttl_seconds
  ttl_seconds: number;          // Default: policy.timeout_sec + 30
  status: LeaseStatus;          // active | expired | released | failed
  last_heartbeat: number;       // Last heartbeat Unix timestamp
  context_id: string | null;    // For sticky routing
}
```

### 4.2 Lease State Machine

```
  ┌─────────┐
  │  ACTIVE  │◄──── created (task assigned to worker)
  └────┬─────┘
       │
  ┌────┴────────────────────┐
  │                         │
  ▼                         ▼
heartbeat received    no heartbeat within TTL
  │                         │
  ▼                         ▼
[ACTIVE]              ┌──────────┐
(renew)               │ EXPIRED  │
                      └────┬─────┘
                           │
                    task re-enqueued
                    or marked dead
```

| Status | Meaning |
|--------|---------|
| `active` | Worker is executing; heartbeats received |
| `expired` | TTL elapsed without heartbeat; task will be re-enqueued |
| `released` | Worker completed task; lease explicitly released |
| `failed` | Worker reported failure; lease terminated |

### 4.3 Heartbeat Protocol

- Workers send heartbeats every `heartbeat_interval` seconds (recommended: 10s)
- Heartbeat updates `last_heartbeat` and extends lease validity
- If `now > expires_at` and no heartbeat received, lease transitions to `expired`
- Expired leases trigger task failover (re-enqueue if attempts remain)

### 4.4 Failover Flow

```
1. Background reaper checks leases every 15 seconds
2. For each lease where now > expires_at:
   a. Set lease.status = "expired"
   b. If task.attempts < task.max_attempts:
      - Set task.status = "queued"
      - Clear task.lease_id and task.worker_id
      - Increment task.attempts
   c. Else:
      - Set task.status = "dead"
   d. Write audit log entry
```

---

## 5. Security Boundaries

### 5.1 Network Trust Zones

```
┌─────────────────────────────────────────────────┐
│  BLOOM Runtime (Replit)                         │
│  ┌──────────────┐    ┌───────────────────────┐  │
│  │ Express API  │    │ In-Memory Task Store  │  │
│  │ /api/runtime │    │ tasks, leases, audit  │  │
│  └──────┬───────┘    └───────────────────────┘  │
│         │                                        │
│         │ HTTPS + X-MEMBRIDGE-ADMIN              │
└─────────┼────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────┐
│  Membridge Control Plane (Alpine :8000)         │
│  ┌──────────────┐    ┌──────────────────────┐   │
│  │ /agents      │    │ Worker Registry      │   │
│  │ /projects    │    │ (in-memory)          │   │
│  └──────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────┘
          │
          │ Internal network (LAN)
          ▼
┌─────────────────────────────────────────────────┐
│  Membridge Worker (Edge node :8001)             │
│  ┌──────────────┐    ┌──────────────────────┐   │
│  │ Claude CLI   │    │ Local claude-mem.db  │   │
│  │ execution    │    │ (session memory)     │   │
│  └──────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 5.2 Authentication

| Boundary | Mechanism | Header |
|----------|-----------|--------|
| Frontend → BLOOM Runtime | Session-based | Standard HTTP |
| BLOOM Runtime → Membridge Server | Admin key | `X-MEMBRIDGE-ADMIN` |
| Worker → Membridge Server | Admin key | `X-MEMBRIDGE-ADMIN` |
| Local processes → Agent | Exempt | Localhost only |
| Remote → Agent | Agent key | `X-MEMBRIDGE-AGENT` |

### 5.3 Data Isolation

| Data Type | Storage | Who Writes | Who Reads |
|-----------|---------|------------|-----------|
| LLM tasks | BLOOM Runtime (in-memory) | Runtime API | Runtime API, Frontend |
| Leases | BLOOM Runtime (in-memory) | Runtime API | Runtime API, Frontend |
| Artifacts | BLOOM Runtime (in-memory) | Runtime API on completion | Frontend |
| claude-mem.db | MinIO (via Membridge) | Workers via hooks | Workers |
| DiffMem/git | git repository | Apply Engine | Agents |

**Axiom A2 (inherited):** Two memory types (claude-mem.db and DiffMem/git) must never mix. Workers read/write claude-mem.db via Membridge sync. Agent reasoning memory uses git-based DiffMem exclusively.

---

## 6. Worker Claude CLI Invocation

### 6.1 Invocation Flow

When a worker receives a leased task, it executes the following sequence:

```
1. Receive task envelope from orchestrator
2. Validate task fields (agent_slug, prompt, context_hints)
3. Prepare Claude CLI arguments:
   a. Set agent context from agent_slug
   b. Load context files from context_hints
   c. Set output format from desired_format
   d. Set timeout from policy.timeout_sec
4. Execute: claude --agent <agent_slug> --prompt <prompt>
5. Start heartbeat loop (every 10s → POST /heartbeat)
6. Wait for Claude CLI completion or timeout
7. Parse output according to desired_format
8. Submit result envelope to orchestrator
9. Release lease
```

### 6.2 Timeout Handling

- Worker sets a local alarm at `policy.timeout_sec`
- If Claude CLI exceeds timeout, worker kills the process
- Worker submits an error result with `error_message: "timeout exceeded"`
- Lease transitions to `failed`

### 6.3 Error Handling

| Error Type | Worker Action | Orchestrator Action |
|-----------|---------------|---------------------|
| Claude CLI exit code != 0 | Submit error result | Increment attempts, retry or mark dead |
| Network timeout to orchestrator | Retry submission 3x | Lease expires, task re-enqueued |
| Invalid prompt / context | Submit error result | Mark failed immediately |
| Worker crash | No action (dead) | Lease expires via TTL, task re-enqueued |

---

## 7. Context Loading Rules

### 7.1 Context Assembly

The `context_hints` field in the task envelope specifies which files or paths the worker should load as context for the Claude CLI invocation.

| Hint Format | Example | Resolution |
|------------|---------|------------|
| Relative path | `src/agents/writer.md` | Resolve relative to project root |
| Glob pattern | `docs/*.md` | Expand to matching files |
| Agent reference | `@agent/writer` | Load agent definition from registry |
| Memory reference | `@memory/recent` | Load recent DiffMem entries (read-only) |

### 7.2 Context Size Limits

- Maximum total context: determined by `policy.budget` (token limit)
- If context exceeds budget, worker truncates oldest entries first
- Context loading failures are non-fatal: worker proceeds with available context

### 7.3 Context Isolation Rules

1. Workers load context from their local filesystem (synced via Membridge)
2. Workers never access other workers' local state
3. Workers never write to shared context during execution
4. All context mutations happen post-execution through the Proposal system

---

## 8. Capability-Based Routing

### 8.1 Worker Selection Algorithm

When the orchestrator needs to assign a task to a worker:

```
1. Fetch online workers from Membridge (GET /agents + /projects)
2. Filter by capability:
   a. worker.capabilities.claude_cli === true
   b. worker.active_leases < worker.capabilities.max_concurrency
3. Apply sticky routing:
   a. If task.context_id matches a worker's existing lease.context_id
   b. Prefer that worker (reduces context reload overhead)
4. If multiple candidates remain:
   a. Sort by health (most recent heartbeat first)
   b. Sort by load (fewest active leases first)
5. Select top candidate
6. If no candidates: task remains queued
```

### 8.2 Worker Capability Structure

```typescript
interface WorkerCapability {
  claude_cli: boolean;        // Can execute Claude CLI
  max_concurrency: number;    // Max simultaneous tasks
  labels: string[];           // Custom labels (e.g., "gpu", "arm64")
}
```

---

## 9. API Surface (BLOOM Runtime)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/runtime/workers` | List workers (merged from Membridge) |
| `GET` | `/api/runtime/workers/:id` | Worker details + active leases |
| `POST` | `/api/runtime/llm-tasks` | Create new LLM task |
| `POST` | `/api/runtime/llm-tasks/:id/lease` | Assign task to worker (create lease) |
| `POST` | `/api/runtime/llm-tasks/:id/heartbeat` | Worker heartbeat for active lease |
| `POST` | `/api/runtime/llm-tasks/:id/complete` | Submit result + create artifact |
| `GET` | `/api/runtime/leases` | List active leases |
| `GET` | `/api/runtime/runs` | Recent task executions |
| `GET` | `/api/runtime/artifacts` | Artifacts by task_id |
| `GET` | `/api/runtime/config` | Get proxy configuration |
| `POST` | `/api/runtime/config` | Save proxy configuration |
| `POST` | `/api/runtime/test-connection` | Test Membridge connectivity |

---

## Semantic Relations

**This document is part of:**
- [[docs/architecture/runtime/]] -- Runtime architecture package

**Depends on:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] -- Axioms A1-A7, authority boundaries
- [[ІНТЕГРАЦІЯ_MEMBRIDGE]] -- Membridge Control Plane contract
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] -- Task state machines, artifact model
- [[КАНОНІЧНА_МОДЕЛЬ_АВТОРИТЕТУ_СХОВИЩА]] -- Write/read authority matrix

**Referenced by:**
- [[docs/ІНДЕКС.md]] -- Master documentation index
- [[docs/audit/_INDEX.md]] -- Audit documentation package
```
---
## Статистика
- **Оброблено файлів:** 24
- **З них прихованих файлів:** 0
- **Пропущено сервісних файлів:** 0
- **Загальний розмір:** 225,485 байт (220.2 KB)
- **Дата створення:** 2026-02-25 19:39:20
