---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:implementation
created: 2026-02-25
updated: 2026-02-26
changelog:
  - 2026-02-26 (rev 3): Додано NodeManagement.tsx, agent management API, multi-project git API.
  - 2026-02-25 (rev 2): Статус IMPLEMENTED. Повна документація українською.
  - 2026-02-25 (rev 1): Початкова специфікація (англ.)
title: "REPLIT_MEMBRIDGE_UI_INTEGRATION"
dg-publish: true
---

# Інтеграція Membridge Control Plane UI у BLOOM Runtime

> Створено: 2026-02-25
> Статус: **РЕАЛІЗОВАНО**
> Layer: Runtime Operations
> Authority: Implementation Reference
> Scope: Інтеграція Membridge UI у єдиний фронтенд BLOOM Runtime

---

## Зміст

1. [Що це і навіщо](#що-це-і-навіщо)
2. [Архітектура](#архітектура)
3. [Файли проєкту](#файли-проєкту)
4. [Backend: proxy-маршрути](#backend-proxy-маршрути)
5. [Frontend: сторінка Membridge](#frontend-сторінка-membridge)
6. [Навігація](#навігація)
7. [Безпека](#безпека)
8. [Налаштування](#налаштування)
9. [Інструкція з користування](#інструкція-з-користування)
10. [Перевірка працездатності](#перевірка-працездатності)

---

## Що це і навіщо

Membridge Control Plane — це сервіс координації worker-нод, що синхронізують SQLite-пам'ять Claude через MinIO. Раніше для роботи з ним потрібно було:

- відкривати окремий URL (`http://<host>:8000/static/ui.html`)
- вручну вводити admin key кожен раз (зберігався в sessionStorage)
- переключатись між двома інтерфейсами

**Тепер** все інтегровано у єдиний фронтенд BLOOM Runtime. Користувач бачить одну панель з двома вкладками: **Runtime** та **Membridge**. Адмін-ключ інжектується бекендом автоматично.

---

## Архітектура

### Канонічний ланцюг виконання

```
┌─────────────────────────┐
│  React frontend         │  /runtime   — сторінка RuntimeSettings
│  (браузер користувача)  │  /membridge — сторінка MembridgePage
│                         │  /nodes     — сторінка NodeManagement
└────────────┬────────────┘
             │  HTTP запити до /api/membridge/*
             ▼
┌─────────────────────────┐
│  BLOOM Runtime          │  Express 5 backend (:5000)
│  server/routes.ts       │  runtimeAuthMiddleware → перевірка X-Runtime-API-Key
│                         │  membridgeFetch() → інжекція X-MEMBRIDGE-ADMIN
└────────────┬────────────┘
             │  HTTP + заголовок X-MEMBRIDGE-ADMIN (автоматично)
             ▼
┌─────────────────────────┐
│  Membridge Control      │  FastAPI (:8000)
│  Plane                  │  /projects, /agents, /health
└────────────┬────────────┘
             │
             ▼
┌─────────────────────────┐
│  Claude CLI Workers     │  Виконання LLM-завдань
└─────────────────────────┘
```

### Ключові принципи

- **Frontend НІКОЛИ не контактує з Membridge напряму** — всі виклики проксуються через бекенд
- **Admin key не потрапляє у браузер** — інжектується серверним кодом (`membridgeFetch()`)
- **Два шари не змішуються**: Runtime state (PostgreSQL) та Control Plane state (Membridge) — окремі сутності

---

## Файли проєкту

| Файл | Дія | Призначення |
|------|-----|-------------|
| `server/routes.ts` | Змінений | Додані proxy-маршрути `/api/membridge/*`, agent management, multi-project API |
| `client/src/pages/MembridgePage.tsx` | Створений | UI Control Plane: проєкти, лідерство, ноди, промоція, git management |
| `client/src/pages/NodeManagement.tsx` | Створений | Node & Agent Management: fleet overview, agent ops, install script |
| `client/src/App.tsx` | Змінений | Навігаційна панель (Runtime / Membridge / Nodes) + маршрути |
| `shared/schema.ts` | Змінений | Додані `managed_projects`, `project_node_status` таблиці; розширено `workers` |
| `server/storage.ts` | Змінений | Додані CRUD для managed projects, upsert worker з agent_version/os_info |
| `server/runtime/membridgeClient.ts` | Без змін | HTTP-клієнт з retry, backoff, timeout (використовується проксі) |
| `server/middleware/runtimeAuth.ts` | Без змін | Аутентифікація X-Runtime-API-Key |

---

## Backend: proxy-маршрути

Всі маршрути захищені `runtimeAuthMiddleware` і використовують `membridgeFetch()` для інжекції admin key.

### Таблиця маршрутів

| Метод | Шлях у BLOOM Runtime | Проксує до Membridge | Опис |
|-------|---------------------|---------------------|------|
| `GET` | `/api/membridge/health` | `/health` | Перевірка з'єднання |
| `GET` | `/api/membridge/projects` | `/projects` | Список проєктів |
| `GET` | `/api/membridge/projects/:cid/leadership` | `/projects/{cid}/leadership` | Lease лідерства |
| `GET` | `/api/membridge/projects/:cid/nodes` | `/projects/{cid}/nodes` | Список нод проєкту |
| `POST` | `/api/membridge/projects/:cid/leadership/select` | `/projects/{cid}/leadership/select` | Промоція primary-ноди |

### Agent Management маршрути

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/api/runtime/workers/:id/agent-health` | Health check агента (оновлює status + version) |
| `POST` | `/api/runtime/workers/:id/agent-update` | git pull + restart на remote агенті |
| `POST` | `/api/runtime/workers/:id/agent-restart` | Перезапуск systemd-сервісу |
| `POST` | `/api/runtime/workers/:id/agent-uninstall` | Зупинка + видалення агента |
| `GET` | `/api/runtime/agent-install-script` | Генерація bash one-liner (?node_id=, ?server_url=) |

### Multi-Project Git маршрути

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/api/runtime/projects` | Список managed git-проєктів |
| `POST` | `/api/runtime/projects` | Створити проєкт (name, repo_url, target_path) |
| `GET` | `/api/runtime/projects/:id` | Деталі + node statuses |
| `DELETE` | `/api/runtime/projects/:id` | Видалити проєкт |
| `POST` | `/api/runtime/projects/:id/clone` | Клонувати на конкретну ноду |
| `POST` | `/api/runtime/projects/:id/propagate` | Поширити на всі ноди |
| `POST` | `/api/runtime/projects/:id/sync-memory` | Push/pull claude-mem.db |
| `GET` | `/api/runtime/projects/:id/node-status` | Статус клонування по нодах |

### Обробка помилок

- Якщо Membridge **недоступний** → `502 {"error": "fetch failed"}` (нормальна поведінка у Replit)
- Якщо Membridge повертає **4xx** → статус проксується як є
- Якщо Membridge повертає **5xx** → `membridgeFetch()` робить retry (до 3 спроб)

### Audit log

Операція промоції primary записується до audit log:

```
action: "leadership_promote"
entity_type: "membridge_project"
entity_id: <canonical_id>
detail: "Promoted primary to <node_id> for project <cid>"
```

---

## Frontend: сторінка Membridge

### Структура сторінки

```
┌─────────────────────────────────────────────────────────┐
│  BLOOM    [Runtime]  [Membridge]           ← навігація  │
├────────────┬────────────────────────────────────────────┤
│            │                                            │
│  Проєкти   │   Картка лідерства                        │
│            │   ┌──────────────────────────────────┐     │
│  ▸ project │   │ Primary Node: rpi4b              │     │
│  ▸ project │   │ Canonical ID: abc123...          │     │
│            │   │ Epoch: 3    Expires: ...         │     │
│            │   └──────────────────────────────────┘     │
│ (280px)    │                                            │
│            │   Таблиця нод                              │
│            │   ┌──────────────────────────────────┐     │
│            │   │ Node ID │ Role │ Obs │ SHA │ ... │     │
│            │   │─────────│──────│─────│─────│─────│     │
│            │   │ rpi4b   │ prim │ 42  │ abc │ ... │     │
│            │   │ rpi3    │ sec  │ 38  │ def │ ... │     │
│            │   └──────────────────────────────────┘     │
│            │                                            │
│            │   Промоція primary                         │
│            │   ┌──────────────────────────────────┐     │
│            │   │ Node ID: [________]              │     │
│            │   │ Lease:   [3600] сек              │     │
│            │   │ [Promote to Primary]             │     │
│            │   └──────────────────────────────────┘     │
│            │                                            │
└────────────┴────────────────────────────────────────────┘
```

### Компоненти

| Компонент | Дані з | Оновлення |
|-----------|--------|-----------|
| **ProjectList** (ліва панель) | `GET /api/membridge/projects` | Кожні 30 сек |
| **LeadershipCard** | `GET /api/membridge/projects/:cid/leadership` | Кожні 30 сек |
| **NodesTable** | `GET /api/membridge/projects/:cid/nodes` | Кожні 15 сек |
| **PromotePrimaryForm** | `POST /api/membridge/projects/:cid/leadership/select` | На вимогу |

### Поля таблиці нод

| Колонка | Опис |
|---------|------|
| Node ID | Ідентифікатор ноди (hostname або MEMBRIDGE_NODE_ID) |
| Role | `primary` або `secondary` (бейдж) |
| Observations | Кількість спостережень у SQLite-базі |
| DB SHA | SHA256 бази (перші 12 символів) |
| Last Seen | Час останнього heartbeat (відносний: "5s ago") |
| IP Addresses | IP-адреси ноди |

### Картка лідерства

| Поле | Опис |
|------|------|
| Primary Node | Поточна primary-нода |
| Canonical ID | `sha256(project_name)[:16]` |
| Epoch | Монотонно зростаючий лічильник renewal |
| Issued / Expires | Час видачі та закінчення lease |
| Status | `active` або `needs selection` |

---

## Навігація

Верхня панель навігації відображається на всіх сторінках:

```
┌──────────────────────────────────────────────────────┐
│  BLOOM    [Runtime]  [Membridge]  [Nodes]             │
└──────────────────────────────────────────────────────┘
```

| Маршрут | Сторінка | Опис |
|---------|----------|------|
| `/` або `/runtime` | RuntimeSettings | Конфігурація Runtime, Workers, Leases, Tasks |
| `/membridge` | MembridgePage | Control Plane: проєкти, лідерство, ноди, git management |
| `/nodes` | NodeManagement | Fleet overview, agent operations, install script |

Активна вкладка підсвічується.

---

## Безпека

### Що захищено

| Аспект | Механізм |
|--------|----------|
| Доступ до `/api/membridge/*` | `runtimeAuthMiddleware` (X-Runtime-API-Key) |
| Admin key Membridge | Інжектується бекендом через `membridgeFetch()` |
| Audit trail | Операції промоції записуються в PostgreSQL |
| Masking ключів | API повертає `admin_key_masked`, не реальний ключ |

### Що НЕ потрапляє у браузер

- `MEMBRIDGE_ADMIN_KEY`
- `DATABASE_URL`
- `RUNTIME_API_KEY`
- Будь-які серверні секрети

---

## Налаштування

### Крок 1: Змінні середовища

На бекенді мають бути встановлені:

| Змінна | Обов'язкова | Опис |
|--------|-------------|------|
| `DATABASE_URL` | Так | PostgreSQL connection string |
| `MEMBRIDGE_SERVER_URL` | Ні (за замовчуванням `http://127.0.0.1:8000`) | URL Membridge control plane |
| `MEMBRIDGE_ADMIN_KEY` | Ні (якщо Membridge без auth) | Ключ для X-MEMBRIDGE-ADMIN |
| `RUNTIME_API_KEY` | Ні (якщо не встановлено — auth вимкнено) | Ключ для захисту API Runtime |

### Крок 2: Міграція бази

```bash
npm run db:push
```

### Крок 3: Налаштування з'єднання через UI

1. Відкрийте сторінку **Runtime** (вкладка "Membridge Proxy")
2. Введіть URL сервера Membridge (наприклад, `http://192.168.1.10:8000`)
3. Введіть Admin Key (буде збережений на бекенді)
4. Натисніть **Save**, потім **Test Connection**
5. При успішному з'єднанні з'явиться зелене повідомлення

### Крок 4: Перевірка

Перейдіть на вкладку **Membridge**. Якщо Membridge доступний:
- Ліворуч з'явиться список проєктів
- Оберіть проєкт → справа з'явиться інформація про лідерство та ноди

---

## Інструкція з користування

### Перегляд проєктів

1. Натисніть **Membridge** у верхній навігації
2. Зліва побачите список проєктів (автоматично оновлюється кожні 30 сек)
3. Натисніть на проєкт — справа з'явиться деталі

### Перегляд лідерства

Після вибору проєкту:
- **Primary Node** — яка нода є джерелом правди (primary)
- **Epoch** — скільки разів lease було оновлено
- **Expires** — коли закінчується поточний lease
- **Status** — `active` (все добре) або `needs selection` (потрібно обрати primary)

### Перегляд нод

Таблиця показує всі ноди, зареєстровані для проєкту:
- **Role**: `primary` (головна) або `secondary` (вторинна)
- **Observations**: чим більше — тим актуальніша база
- **DB SHA**: для порівняння — чи співпадає база на нодах
- **Last Seen**: якщо давно — нода може бути offline

### Промоція primary

Коли потрібно змінити primary-ноду (наприклад, стара offline):

1. Подивіться таблицю нод — знайдіть потрібний **Node ID**
2. Введіть Node ID у поле "Node ID" у блоці "Promote Primary"
3. За потреби змініть тривалість lease (за замовчуванням 3600 сек = 1 година)
4. Натисніть **Promote to Primary**
5. При успіху з'явиться повідомлення, дані оновляться автоматично

### Моніторинг Runtime

На вкладці **Runtime**:
- **Membridge Proxy** — конфігурація з'єднання, таблиця workers, активні leases
- **Task Queue** — черга завдань, статуси, можливість requeue
- **Overview** — статистика: workers online, active leases, total tasks

---

## Перевірка працездатності

### Smoke tests (curl)

```bash
# Health endpoint
curl -s http://localhost:5000/api/runtime/health
# Очікується: 200 {"status":"ok","service":"bloom-runtime",...}

# Membridge health (через проксі)
curl -s http://localhost:5000/api/membridge/health
# Очікується: 200 (якщо Membridge доступний) або 502 (якщо ні)

# Список проєктів
curl -s http://localhost:5000/api/membridge/projects
# Очікується: JSON-масив проєктів або 502

# Промоція (потребує Membridge)
curl -X POST http://localhost:5000/api/membridge/projects/<cid>/leadership/select \
  -H 'Content-Type: application/json' \
  -d '{"primary_node_id": "node-name", "lease_seconds": 3600}'
```

### Що є нормою у Replit

У середовищі Replit Membridge control plane **не запущений**, тому:
- `GET /api/membridge/*` → `502 {"error": "fetch failed"}` — **це нормально**
- Runtime endpoints (`/api/runtime/*`) працюють повноцінно з PostgreSQL

### Що перевіряти у production

1. `/api/runtime/health` → `200`, `storage: "postgresql"`, `membridge.connected: true`
2. `/api/membridge/projects` → масив проєктів
3. `/api/membridge/projects/<cid>/nodes` → масив нод
4. Сторінка `/membridge` у браузері — проєкти та ноди відображаються
5. Audit log (`/api/runtime/audit`) — записи про дії leadership
6. Сторінка `/nodes` — fleet overview, agent version, status відображаються
7. `/api/runtime/workers` → масив з полями `agent_version`, `os_info`, `install_method`
8. `/api/runtime/agent-install-script` → bash-скрипт з правильним SERVER_URL
9. `/api/runtime/projects` → managed git-проєкти (якщо є)

---

## Семантичні зв'язки

**Цей документ залежить від:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — топологія розгортання
- [[RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]] — стан бекенду

**На цей документ посилаються:**
- [[RUNTIME_GAPS_AND_NEXT_STEPS.md]] — GAP-7 (позначений як RESOLVED)
- [[../../ІНДЕКС.md]] — головний індекс документації
