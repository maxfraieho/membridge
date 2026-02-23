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
