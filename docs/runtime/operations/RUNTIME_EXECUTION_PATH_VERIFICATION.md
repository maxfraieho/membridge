---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
changelog:
  - 2026-02-25 (rev 2): Оновлено до поточного стану — PostgreSQL, auth, membridge proxy, UI. Перекладено українською.
title: "RUNTIME_EXECUTION_PATH_VERIFICATION"
dg-publish: true
---

# BLOOM Runtime — Верифікація шляху виконання

> Створено: 2026-02-25
> Статус: Canonical
> Layer: Runtime Operations
> Authority: Production Environment
> Scope: Фактичний верифікований шлях виконання — що працює, що очікує

---

## Огляд

Цей документ простежує повний шлях виконання BLOOM Runtime та позначає кожний сегмент фактичним верифікованим статусом.

**Позначення:**
- ✅ `LIVE` — верифіковано на production
- ⚙️ `РЕАЛІЗОВАНО` — код існує, логіка правильна, але ще не активовано (відсутня передумова)
- ❌ `ВІДСУТНЄ` — ще не побудовано

---

## Повний шлях виконання

```
Запит клієнта
     │
     ▼
 [1] nginx :80  ──────────────────────── ✅ LIVE
     │
     ▼
 [2] bloom-runtime :5000 (Express)  ───── ✅ LIVE
     │
     ├─► X-Runtime-API-Key middleware ─── ✅ LIVE (опціонально через RUNTIME_API_KEY)
     │
     ├─► /api/membridge/* proxy ────────── ✅ LIVE (проксі до Membridge :8000)
     │
     ├─► POST /api/runtime/llm-tasks ──── ✅ LIVE (персистовано в PostgreSQL)
     │
     ▼
 [3] Черга завдань (PostgreSQL) ────────── ✅ LIVE (переживає рестарт)
     │
     ▼
 [4] POST /api/runtime/llm-tasks/:id/lease
     │   Вибір worker (pickWorker) ─────── ✅ LIVE (workers з auto-sync)
     │
     ▼
 [5] Worker auto-sync (інтервал 10с) ──── ✅ LIVE (→ membridge /agents)
     │
     ├─► membridgeFetch з retry ────────── ✅ LIVE (backoff, timeout, tracking)
     │
     ▼
 [6] Membridge control plane :8000 ─────── ✅ LIVE
     │
     ▼
 [7] Worker Node (Claude CLI) ──────────── ⏳ ОЧІКУЄ (потрібна реєстрація)
     │
     ├─► POST .../heartbeat ────────────── ⚙️ РЕАЛІЗОВАНО
     │
     ▼
 [8] Виконання Claude CLI ──────────────── ❌ ВІДСУТНЄ (немає workers)
     │
     ▼
 [9] POST .../complete
     │   Створення артефакту ────────────── ⚙️ РЕАЛІЗОВАНО
     │   Запис результату ───────────────── ⚙️ РЕАЛІЗОВАНО
     │
     ▼
[10] Сховище артефактів (PostgreSQL) ────── ✅ LIVE (персистоване)
     │
     ▼
[11] Audit log (PostgreSQL) ─────────────── ✅ LIVE (персистований)
     │
     ▼
[12] Відповідь клієнту ──────────────────── ✅ LIVE
```

---

## Посегментна верифікація

### [1] nginx → bloom-runtime

**Статус:** ✅ LIVE

```bash
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/
# → 200

curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/api/runtime/stats
# → 200
```

Конфігурація nginx: `/etc/nginx/http.d/bloom-runtime.conf`
Upstream: `server 127.0.0.1:5000; keepalive 32;`
Заголовки: `X-Real-IP`, `X-Forwarded-For`, підтримка WebSocket upgrade.

---

### [2] bloom-runtime Express

**Статус:** ✅ LIVE

```bash
curl -s http://127.0.0.1:5000/api/runtime/health
# → {"status":"ok","service":"bloom-runtime","storage":"postgresql",...}
```

Node.js 23, Express 5. Обслуговує React SPA (`dist/public/`) + API (`/api/runtime/*`, `/api/membridge/*`).

**Аутентифікація:**
- `X-Runtime-API-Key` — для всіх `/api/runtime/*` та `/api/membridge/*`
- Якщо `RUNTIME_API_KEY` не встановлений — auth вимкнений (режим розробки)
- Незахищені: `/api/runtime/health`, `/api/runtime/test-connection`

---

### [3] Створення завдання

**Статус:** ✅ LIVE (PostgreSQL)

`POST /api/runtime/llm-tasks` створює завдання у PostgreSQL.
Валідація через Zod (`insertLLMTaskSchema`).
Завдання створюється зі статусом `queued`, записується в audit log.

---

### [4] Призначення lease та вибір worker

**Статус:** ⚙️ РЕАЛІЗОВАНО — заблоковано відсутністю workers

`POST /api/runtime/llm-tasks/:id/lease` викликає `pickWorker()`:

```
Алгоритм pickWorker():
┌───────────────────────────────────────────┐
│ 1. Фільтр: status="online"               │
│    AND capabilities.claude_cli=true       │
│    AND active_leases < max_concurrency    │
├───────────────────────────────────────────┤
│ 2. Якщо є context_id → sticky routing    │
│    до існуючого worker для цього контексту│
├───────────────────────────────────────────┤
│ 3. Інакше → worker з найбільшою           │
│    вільною ємністю                        │
├───────────────────────────────────────────┤
│ 4. Якщо workers = 0 → return null         │
│    → HTTP 503 "No available worker"       │
└───────────────────────────────────────────┘
```

Вирішиться одразу після першої реєстрації worker.

---

### [5] Membridge control plane

**Статус:** ✅ LIVE

```bash
curl -s http://127.0.0.1:8000/health
# → {"status":"ok","service":"membridge-control-plane","version":"0.3.0"}
```

Auto-sync workers з Membridge кожні 10 секунд через `workerSync.ts`.
Поточний стан: `/agents` повертає `[]` — жоден worker не зареєстрований.

---

### [6] Worker Node (Claude CLI агент)

**Статус:** ⏳ ОЧІКУЄ

Жоден агент не зареєстрований у Membridge.

**Що потрібно для розблокування:**

```
Worker реєстрація:
┌─────────────────────────────────────────┐
│ POST /agents                            │
│ X-MEMBRIDGE-ADMIN: <admin-key>          │
│                                         │
│ {                                       │
│   "name": "worker-01",                  │
│   "status": "online",                   │
│   "capabilities": {                     │
│     "claude_cli": true,                 │
│     "max_concurrency": 1                │
│   }                                     │
│ }                                       │
└─────────────────────────────────────────┘
           │
           ▼
GET /api/runtime/workers → [worker-01]
           │
           ▼
POST .../lease → 200 (замість 503)
```

---

### [7–8] Виконання Claude CLI

**Статус:** ❌ ВІДСУТНЄ (немає workers)

Workers викликають Claude CLI з параметрами завдання з lease.
Протокол визначений у:
[[../../architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md]]

---

### [9] Завершення завдання

**Статус:** ⚙️ РЕАЛІЗОВАНО

`POST /api/runtime/llm-tasks/:id/complete`:

```
1. Валідація тіла (Zod: completeTaskSchema)
       │
2. Створення артефакту в PostgreSQL
       │
3. Запис результату (status, output, error_message, metrics)
       │
4. Оновлення статусу завдання → "completed" або "failed"
       │
5. Звільнення lease (status = "released")
       │
6. Запис в audit log
```

---

### [10–11] Сховище артефактів та Audit log

**Статус:** ✅ LIVE (PostgreSQL)

- Артефакти зберігаються в `runtime_artifacts` (PostgreSQL)
- Audit log у `audit_logs` (PostgreSQL)
- Обидва переживають рестарти сервісу
- Запитуються через `GET /api/runtime/artifacts` та `GET /api/runtime/audit`

---

### [12] Відповідь клієнту

**Статус:** ✅ LIVE

Всі API відповіді — JSON. Логування запитів: `METHOD /path STATUS DURATIONms`.

---

## Зведена таблиця

| Крок | Компонент | Статус | Блокер |
|------|-----------|--------|--------|
| 1 | nginx reverse proxy | ✅ LIVE | — |
| 2 | bloom-runtime Express | ✅ LIVE | — |
| 3 | Створення завдання | ✅ LIVE | — |
| 4 | Lease / вибір worker | ⚙️ РЕАЛІЗОВАНО | Немає зареєстрованих workers |
| 5 | Membridge control plane | ✅ LIVE | — |
| 6 | Worker node | ⏳ ОЧІКУЄ | Worker не розгорнутий |
| 7–8 | Виконання Claude CLI | ❌ ВІДСУТНЄ | Worker не розгорнутий |
| 9 | Завершення + артефакт | ⚙️ РЕАЛІЗОВАНО | Worker не розгорнутий |
| 10 | Сховище артефактів | ✅ LIVE | PostgreSQL |
| 11 | Audit log | ✅ LIVE | PostgreSQL |
| 12 | API відповідь | ✅ LIVE | — |

---

## Що розблоковує реєстрація одного worker

```
Реєстрація 1 worker у Membridge
        │
        ▼
┌───────────────────────────────────────┐
│ Одразу активуються:                   │
│                                       │
│  ✅ Крок 4  — Lease assignment        │
│  ✅ Крок 6  — Worker node             │
│  ✅ Кроки 7-8 — Claude CLI виконання  │
│  ✅ Крок 9  — Завершення + артефакт   │
│                                       │
│ Повний end-to-end pipeline:           │
│ create → lease → heartbeat →          │
│ complete → artifact → audit           │
└───────────────────────────────────────┘
```

Весь pipeline повністю реалізований у коді та чекає на цей єдиний операційний крок.

---

## Membridge Proxy (НОВЕ)

Окрім Runtime API, тепер доступні proxy-маршрути до Membridge Control Plane:

| Метод | Шлях | Проксує до | Статус |
|-------|------|-----------|--------|
| `GET` | `/api/membridge/health` | `/health` | ✅ LIVE |
| `GET` | `/api/membridge/projects` | `/projects` | ✅ LIVE |
| `GET` | `/api/membridge/projects/:cid/leadership` | `/projects/{cid}/leadership` | ✅ LIVE |
| `GET` | `/api/membridge/projects/:cid/nodes` | `/projects/{cid}/nodes` | ✅ LIVE |
| `POST` | `/api/membridge/projects/:cid/leadership/select` | `/projects/{cid}/leadership/select` | ✅ LIVE |

Всі маршрути використовують `membridgeFetch()` — admin key інжектується серверним кодом.
Фронтенд: вкладка **Membridge** у навігації.

---

## Семантичні зв'язки

**Цей документ залежить від:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — топологія та стан сервісів
- [[../../architecture/runtime/INTEGRATION_MEMBRIDGE_CLAUDE_CLI_PROXY.md]] — специфікація Claude CLI proxy

**На цей документ посилаються:**
- [[RUNTIME_GAPS_AND_NEXT_STEPS.md]] — прогалини та наступні кроки
- [[../../ІНДЕКС.md]] — головний індекс
