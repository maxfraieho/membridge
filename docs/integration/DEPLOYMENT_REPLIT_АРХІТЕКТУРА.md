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
