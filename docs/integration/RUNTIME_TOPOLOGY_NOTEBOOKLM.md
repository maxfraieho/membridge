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
