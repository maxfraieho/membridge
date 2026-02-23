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
