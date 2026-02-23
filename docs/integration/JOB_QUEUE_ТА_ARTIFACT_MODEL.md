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
