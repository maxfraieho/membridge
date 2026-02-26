---
tags:
  - domain:frontend
  - status:canonical
  - format:prompt
  - feature:execution
created: 2026-02-25
updated: 2026-02-26
tier: 1
title: "Lovable Initial Instruction — BLOOM Agents & LLM Resources"
---

# Lovable Initial Instruction — BLOOM Agents & LLM Resources

> Автор: Архітектор системи
> Статус: Canonical
> Мова: Українська (канонічна)
> Контекст: Початкова інструкція для Lovable — агенти та доступ до LLM-ресурсів

---

## 0. Контекст системи

**Garden Bloom** — execution platform для AI-агентів, де людина залишається в контролі. Агенти пропонують зміни через Proposal system, власник вирішує що прийняти.

**BLOOM** (Behavioral Logic Orchestration for Order-Made Systems) — runtime-ядро платформи. Відповідає за оркестрацію виконання агентів, ізоляцію контекстів, делегування behavioral logic.

**Ключовий принцип:** AI пропонує — людина вирішує. Кожна мутація — через явну згоду.

---

## 1. Два канали LLM-ресурсів

Агенти системи мають два незалежних шляхи доступу до LLM:

### 1.1 NotebookLM (через NotebookLM.py / FastAPI)

**Роль:** Когнітивне ядро для роботи строго по джерелах.

```
Agent → Mastra Tool → FastAPI (NotebookLM.py) → NotebookLM API
```

**Характеристики:**
- Працює **строго по наданих джерелах** — без галюцинацій
- Пояснює, узагальнює, структурує знання
- Повертає цитати та посилання
- Не приймає архітектурних рішень, не керує процесами

**Застосування:**
- Аналіз документації та знань
- Підготовка summaries з джерел
- Відповіді на питання в межах knowledge base
- Когнітивна обробка зон знань

**Інтеграція у frontend:**
- Агент запускається → крок `query NLM` → FastAPI → NotebookLM
- UI показує результат як артефакт або proposal
- Frontend **ніколи не звертається** до FastAPI/NotebookLM напряму

### 1.2 Membridge (Claude з різних клієнтів)

**Роль:** Розподілений execution fabric для делегування LLM-задач між кількома Claude-акаунтами.

```
BLOOM Runtime API → Membridge Control Plane → Agent Daemons → Claude CLI (різні акаунти)
```

**Характеристики:**
- Кілька машин з окремими Claude-акаунтами (різні API keys / підписки)
- Кожна машина = Worker з Agent Daemon
- Задачі розподіляються між workers через lease-систему
- Результати повертаються як Artifacts — workers **ніколи не пишуть** у canonical storage напряму
- Синхронізація пам'яті (claude-mem.db) через MinIO

**Execution Pipeline:**
1. `POST /api/runtime/llm-tasks` — створити задачу
2. `POST /api/runtime/llm-tasks/:id/lease` — призначити worker (автоматичний routing)
3. Worker виконує задачу через свій Claude CLI
4. `POST /api/runtime/llm-tasks/:id/complete` — worker повертає результат
5. Артефакт зберігається в MinIO (або PostgreSQL як fallback)

**API для frontend (проксі через backend):**

| Endpoint | Метод | Опис |
|----------|-------|------|
| `/api/runtime/workers` | GET | Список workers з статусами |
| `/api/runtime/workers` | POST | Реєстрація нового worker |
| `/api/runtime/workers/:id` | GET | Деталі worker + активні leases |
| `/api/runtime/workers/:id` | DELETE | Видалення worker |
| `/api/runtime/llm-tasks` | GET | Список задач (фільтр `?status=`) |
| `/api/runtime/llm-tasks` | POST | Створити задачу |
| `/api/runtime/llm-tasks/:id` | GET | Деталі задачі |
| `/api/runtime/llm-tasks/:id/lease` | POST | Призначити worker |
| `/api/runtime/llm-tasks/:id/heartbeat` | POST | Оновити heartbeat |
| `/api/runtime/llm-tasks/:id/complete` | POST | Завершити з результатом |
| `/api/runtime/llm-tasks/:id/requeue` | POST | Перезапустити failed/dead |
| `/api/runtime/leases` | GET | Список leases |
| `/api/runtime/artifacts` | GET | Артефакти (фільтр `?task_id=`) |
| `/api/runtime/stats` | GET | Статистика (tasks/leases/workers) |
| `/api/runtime/audit` | GET | Audit log |
| `/api/runtime/health` | GET | Здоров'я сервісу |
| `/api/runtime/workers/:id/agent-health` | GET | Health check агента на ноді |
| `/api/runtime/workers/:id/agent-update` | POST | Оновлення агента (git pull + restart) |
| `/api/runtime/workers/:id/agent-restart` | POST | Перезапуск systemd-сервісу агента |
| `/api/runtime/workers/:id/agent-uninstall` | POST | Видалення агента з ноди |
| `/api/runtime/agent-install-script` | GET | Генерація bash-скрипта інсталяції (?node_id=, ?server_url=) |

**Multi-Project Git Management:**

| Endpoint | Метод | Опис |
|----------|-------|------|
| `/api/runtime/projects` | GET | Список managed git-проєктів |
| `/api/runtime/projects` | POST | Створити managed проєкт (name, repo_url, target_path) |
| `/api/runtime/projects/:id` | GET | Деталі проєкту + статус нод |
| `/api/runtime/projects/:id` | DELETE | Видалити managed проєкт |
| `/api/runtime/projects/:id/clone` | POST | Клонувати проєкт на конкретну ноду |
| `/api/runtime/projects/:id/propagate` | POST | Поширити проєкт на всі ноди |
| `/api/runtime/projects/:id/sync-memory` | POST | Push/pull claude-mem.db для проєкту |
| `/api/runtime/projects/:id/node-status` | GET | Статус клонування по нодах |

**Membridge Control Plane (проксі):**

| Endpoint | Метод | Опис |
|----------|-------|------|
| `/api/membridge/health` | GET | Здоров'я Membridge |
| `/api/membridge/projects` | GET | Список проєктів sync |
| `/api/membridge/projects/:cid/leadership` | GET | Leadership lease проєкту |
| `/api/membridge/projects/:cid/nodes` | GET | Ноди проєкту |
| `/api/membridge/projects/:cid/leadership/select` | POST | Промотувати primary |

---

## 2. Два шари пам'яті (КРИТИЧНИЙ ІНВАРІАНТ)

**ЦЕ НАЙВАЖЛИВІШЕ ОБМЕЖЕННЯ.** Два шари пам'яті НІКОЛИ не змішуються:

### Шар A: claude-mem.db (Membridge → MinIO)
- **Що:** SQLite бази пам'яті Claude сесій
- **Синхронізація:** Membridge sync через MinIO (push/pull)
- **Контекст:** Session-level, прив'язана до конкретного Claude CLI
- **Frontend:** НЕ показує вміст бази напряму; показує sync-статус через Membridge UI

### Шар B: DiffMem / git (Agent Reasoning)
- **Що:** Git-based memory для агентного міркування
- **Формат:** Markdown entities у git-репо (entities/people/, entities/projects/, etc.)
- **Операції:** Тільки через Proposal → Apply cycle
- **Frontend:** MemoryPanel.tsx (search, context, add memory)
- **Workers:** Повертають results/proposals — НІКОЛИ не пишуть canonical storage

**UI не повинен:**
- Показувати дані claude-mem.db поряд з DiffMem entities як одну колекцію
- Дозволяти workers писати напряму в knowledge base
- Обходити Proposal lifecycle для будь-яких мутацій

---

## 3. Архітектура з точки зору Frontend

### 3.1 Frontend = проєкція стану

Frontend **відображає** дані, а не є їх джерелом.

| Аспект | Frontend робить | Frontend НЕ робить |
|--------|----------------|-------------------|
| Workers | Показує список, статуси, leases | Не керує workers напряму |
| Tasks | Показує queue, створює tasks через API | Не виконує tasks |
| Artifacts | Відображає результати | Не модифікує artifacts |
| Proposals | Показує, дозволяє approve/reject | Не bypass-ить approval |
| NotebookLM | Показує результати query | Не звертається до NLM напряму |
| Membridge | Показує проєкти, leadership, ноди | Не тримає admin key |

### 3.2 Шлях даних

```
Frontend → API (Express backend, порт 5000) → {PostgreSQL, Membridge, MinIO}
```

Frontend НІКОЛИ не звертається до:
- Membridge Control Plane напряму (тільки через `/api/membridge/*` проксі)
- FastAPI / NotebookLM.py напряму
- MinIO напряму
- Claude CLI / API напряму

### 3.3 Аутентифікація

| Контекст | Механізм |
|----------|----------|
| Frontend → Backend API | `X-Runtime-API-Key` header (опціонально, якщо встановлено) |
| Backend → Membridge | `X-MEMBRIDGE-ADMIN` (інжектується сервером, frontend не бачить) |
| NotebookLM | `Bearer NOTEBOOKLM_SERVICE_TOKEN` (через CF Worker, frontend не бачить) |
| Owner доступ | JWT через Access Gate (master-key) |

---

## 4. UI модулі для LLM-ресурсів

### 4.1 Runtime Dashboard (існує: RuntimeSettings.tsx)

Три вкладки:
- **Overview** — статистика tasks/workers/leases, графіки
- **Task Queue** — список задач, створення нових, requeue
- **Membridge Proxy** — конфігурація URL + admin key, test connection

**Що додати/покращити:**
- Task detail view з lease info та artifact
- Lease timeline visualization

### 4.2 Membridge Control Plane (існує: MembridgePage.tsx)

- Список проєктів sync (leadership card, nodes table, promote primary)
- Multi-project git management:
  - **Add Project** форма (name, repo_url, target_path)
  - **Managed Project Cards** з clone/propagate/sync-memory кнопками
  - **Per-node clone status** таблиця
  - **Memory push/pull** для кожного проєкту

**Що додати/покращити:**
- Sync history / job log
- Visual leadership timeline

### 4.3 Node & Agent Management (існує: NodeManagement.tsx)

Маршрут: `/nodes`

Компоненти:
- **Stat Cards** — Total Nodes / Online / Offline+Unknown (автооновлення 15с)
- **Fleet Overview** — таблиця з agent_version, status, URL, IPs, last heartbeat
- **Node Actions** — 5 кнопок на кожну ноду:
  - ♥ Health Check → `GET /api/runtime/workers/:id/agent-health`
  - ↑ Update → `POST /api/runtime/workers/:id/agent-update`
  - ↻ Restart → `POST /api/runtime/workers/:id/agent-restart`
  - ✕ Uninstall → `POST /api/runtime/workers/:id/agent-uninstall`
  - 🗑 Remove → `DELETE /api/runtime/workers/:id`
- **Install Script Card** — генерація curl one-liner (з полями Control Plane URL та Node ID)
- **Register Node Form** — ручна реєстрація (Node ID + Agent URL)

**Дані worker-ноди (розширені):**

```typescript
interface WorkerNode {
  id: string;
  node_id: string;
  url: string;
  status: "online" | "offline" | "syncing" | "error" | "unknown";
  capabilities: { claude_cli: boolean; max_concurrency: number; labels: string[] };
  last_heartbeat: number | null;
  ip_addrs: string[];
  active_leases: number;
  agent_version: string;   // версія агента (наприклад "0.3.1")
  os_info: string;         // hostname або OS info
  install_method: string;  // "script" | "manual" | "unknown"
}
```

### 4.4 Agent Memory Panel (існує: MemoryPanel.tsx)

- Search (BM25 + LLM orchestrated)
- Context assembly (4 depths: basic/wide/deep/temporal)
- Add Memory (process transcript → entities)

**Не чіпати:** Цей компонент вже працює. Зміни тільки через окремий prompt.

### 4.5 Agent Catalog (планується: AgentsPage.tsx)

- Agent cards з name, zone, status badge, order
- Reorder (drag or ↑↓)
- Agent form (name, zone, behavior pseudocode, triggers)
- Agent detail panel

---

## 5. Data Types (TypeScript)

### 5.1 Вже визначені у shared/schema.ts

```typescript
interface WorkerNode {
  id: string;
  node_id: string;
  url: string;
  status: "online" | "offline" | "syncing" | "error" | "unknown";
  capabilities: { claude_cli: boolean; max_concurrency: number; labels: string[] };
  last_heartbeat: number | null;
  ip_addrs: string[];
  active_leases: number;
}

interface LLMTask {
  id: string;
  context_id: string;
  agent_slug: string;
  prompt: string;
  status: "queued" | "leased" | "running" | "completed" | "failed" | "dead";
  created_at: number;
  updated_at: number;
  lease_id: string | null;
  worker_id: string | null;
  attempts: number;
  max_attempts: number;
}

interface Lease {
  id: string;
  task_id: string;
  worker_id: string;
  started_at: number;
  expires_at: number;
  status: "active" | "expired" | "released" | "failed";
  last_heartbeat: number;
}

interface RuntimeArtifact {
  id: string;
  task_id: string;
  type: string;
  url: string | null;      // minio:// URL якщо в MinIO, null якщо в PostgreSQL
  content: string | null;  // вміст якщо в PostgreSQL, null якщо в MinIO
  tags: string[];
}

interface AuditLogEntry {
  id: string;
  timestamp: number;
  action: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  detail: string;
}
```

### 5.2 Для Multi-Project Git Management (визначені у shared/schema.ts)

```typescript
interface ManagedProject {
  id: string;
  name: string;           // regex: ^[a-zA-Z0-9_-]+$
  repo_url: string;       // git URL
  target_path: string;    // шлях на ноді (без "..")
  status: "active" | "archived";
  created_at: number;
  primary_node_id: string | null;
}

interface ProjectNodeCloneStatus {
  id: string;
  project_id: string;
  node_id: string;
  status: "pending" | "cloning" | "cloned" | "failed" | "synced";
  last_clone_at: number | null;
  error: string | null;
}
```

### 5.3 Для Agent Registry (нові)

```typescript
type AgentStatus = 'active' | 'inactive' | 'draft';

interface AgentDefinition {
  id: string;             // kebab-case
  name: string;
  zone: string;           // folder path, e.g. "exodus.pp.ua/architecture"
  order: number;          // execution sequence
  status: AgentStatus;
  behavior: string;       // pseudocode markdown
  description?: string;
  triggers?: string[];
  created: string;        // ISO date
  updated: string;
}
```

---

## 6. Потік даних: Agent Execution з двома LLM-ресурсами

```
                    ┌─────────────────────┐
                    │     Owner (UI)      │
                    │  Запускає агента    │
                    └─────────┬───────────┘
                              │
                              ▼
                    ┌─────────────────────┐
                    │  Orchestration      │
                    │  (BLOOM Runtime)    │
                    └─────────┬───────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼                               ▼
   ┌────────────────────┐         ┌────────────────────┐
   │  Шлях A: NLM       │         │  Шлях B: Membridge │
   │                    │         │                    │
   │  Agent Tool:       │         │  LLM Task:         │
   │  notebooklm-query  │         │  POST /llm-tasks   │
   │       │            │         │       │            │
   │       ▼            │         │       ▼            │
   │  FastAPI           │         │  Worker Selection  │
   │  (NotebookLM.py)   │         │  (Lease routing)   │
   │       │            │         │       │            │
   │       ▼            │         │       ▼            │
   │  NotebookLM API    │         │  Claude CLI        │
   │  (Google)          │         │  (акаунт worker-а) │
   │       │            │         │       │            │
   │       ▼            │         │       ▼            │
   │  Відповідь з       │         │  Результат         │
   │  цитатами          │         │  (text/json)       │
   └────────┬───────────┘         └────────┬───────────┘
            │                              │
            └──────────────┬───────────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │  Proposal / Artifact│
                 │  → MinIO storage    │
                 └─────────┬───────────┘
                           │
                           ▼
                 ┌─────────────────────┐
                 │  Owner Review (UI)  │
                 │  Approve / Reject   │
                 └─────────────────────┘
```

---

## 7. Rate Limiting

API має rate limiting:

| Група | Ліміт | Endpoints |
|-------|-------|-----------|
| General | 100 req/хв | `/api/runtime/*`, `/api/membridge/*` |
| Strict | 20 req/хв | `POST /api/runtime/test-connection` |

Стандартні `RateLimit-*` заголовки у відповідях. При перевищенні — HTTP 429.

---

## 8. Обмеження для Lovable

### ЗАБОРОНЕНО:
1. Звертатися до Membridge/FastAPI/MinIO/Claude напряму з frontend
2. Зберігати admin key, API keys, tokens у frontend коді
3. Змішувати claude-mem.db та DiffMem дані в одному UI-компоненті
4. Bypass-ити Proposal lifecycle для мутацій
5. Реалізовувати auto-approve у frontend (це серверна логіка)
6. Показувати внутрішній стан Mastra/Orchestration Layer

### ОБОВ'ЯЗКОВО:
1. Всі API запити через backend (порт 5000)
2. Polling для real-time даних (workers: 10с, tasks: 5с)
3. Loading/skeleton states для всіх async операцій
4. Error handling з user-friendly повідомленнями
5. Audit log запис для адмін-операцій (backend робить автоматично)
6. `data-testid` на всіх інтерактивних елементах

---

## 9. Семантичні зв'язки

**Цей документ залежить від:**
- [[BLOOM_IDENTITY_AND_RUNTIME]] — canonical execution identity
- [[КАНОНІЧНА_АРХІТЕКТУРА_ВИКОНАННЯ]] — runtime architecture
- [[КОНТРАКТ_АГЕНТА_V1]] — agent contract
- [[КОНТРАКТИ_API_V1]] — API schemas
- [[LOVABLE_УЗГОДЖЕННЯ_З_АРХІТЕКТУРОЮ_ВИКОНАННЯ]] — frontend contract
- [[BLOOM_AUTH_UI_SPEC]] — auth UI spec
- [[memory/ARCHITECTURE]] — DiffMem memory architecture
- [[memory/API_CONTRACT]] — Memory API spec

**Реалізація:**
- `server/routes.ts` — Runtime API + Membridge proxy + Node Management API
- `server/runtime/membridgeClient.ts` — Membridge HTTP client
- `server/runtime/minioArtifacts.ts` — MinIO artifact storage
- `server/runtime/workerSync.ts` — Worker auto-sync
- `shared/schema.ts` — TypeScript types + Zod schemas
- `client/src/pages/RuntimeSettings.tsx` — Runtime UI
- `client/src/pages/MembridgePage.tsx` — Membridge Control Plane UI + Multi-project git management
- `client/src/pages/NodeManagement.tsx` — Node & Agent fleet management UI
- `client/src/App.tsx` — Навігація: Runtime / Membridge / Nodes
