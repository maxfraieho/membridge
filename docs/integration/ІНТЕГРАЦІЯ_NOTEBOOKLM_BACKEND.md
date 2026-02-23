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
