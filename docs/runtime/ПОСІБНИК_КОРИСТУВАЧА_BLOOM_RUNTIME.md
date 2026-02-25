---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - format:guide
created: 2026-02-25
updated: 2026-02-25
title: "ПОСІБНИК_КОРИСТУВАЧА_BLOOM_RUNTIME"
dg-publish: true
---

# BLOOM Runtime — Посібник користувача

> Створено: 2026-02-25
> Статус: Canonical
> Мова: Українська (canonical)
> Аудиторія: Оператор, адміністратор, розробник

---

## Зміст

1. [Що таке BLOOM Runtime](#що-таке-bloom-runtime)
2. [Ключові поняття](#ключові-поняття)
3. [Архітектура системи](#архітектура-системи)
4. [Перший запуск](#перший-запуск)
5. [Інтерфейс користувача](#інтерфейс-користувача)
6. [Налаштування Membridge](#налаштування-membridge)
7. [Управління завданнями](#управління-завданнями)
8. [Моніторинг](#моніторинг)
9. [Типові сценарії](#типові-сценарії)
10. [Усунення несправностей](#усунення-несправностей)
11. [Довідка з API](#довідка-з-api)

---

## Що таке BLOOM Runtime

BLOOM Runtime — це платформа оркестрації для AI-агентів, де **людина завжди контролює**. Система:

- Координує виконання LLM-завдань на розподілених worker-нодах
- Синхронізує пам'ять Claude CLI між машинами через MinIO
- Забезпечує audit trail кожної дії
- Пропонує зміни через систему Proposal — людина вирішує

```
┌──────────────────────────────────────────────────────┐
│                  BLOOM Runtime                        │
│                                                      │
│  "AI що пропонує — людина що вирішує"                │
│                                                      │
│  ┌────────┐    ┌──────────┐    ┌──────────────────┐  │
│  │Завдання│───▶│ Lease    │───▶│ Worker (Claude)  │  │
│  │ (Task) │    │(оренда)  │    │ виконує задачу   │  │
│  └────────┘    └──────────┘    └────────┬─────────┘  │
│                                         │            │
│                                    ┌────▼─────┐      │
│                                    │ Результат│      │
│                                    │+Артефакт │      │
│                                    └──────────┘      │
└──────────────────────────────────────────────────────┘
```

---

## Ключові поняття

### Два шари пам'яті (НІКОЛИ не змішуються)

```
┌─────────────────────────────────────────────────────┐
│          ДВА ШАРИ ПАМ'ЯТІ — ІНВАРІАНТ              │
│                                                     │
│  Шар 1: claude-mem.db                               │
│  ├── Тип: SQLite → MinIO (через Membridge)          │
│  ├── Хто пише: Claude CLI + membridge hooks          │
│  └── Призначення: session memory                    │
│                                                     │
│  Шар 2: DiffMem / git                               │
│  ├── Тип: git repo (garden-bloom-memory)            │
│  ├── Хто пише: Apply Engine через Proposals         │
│  └── Призначення: agent reasoning memory            │
│                                                     │
│  ⚠️ Ці два шари НІКОЛИ не змішуються.               │
│  Workers повертають результати/proposals —            │
│  НІКОЛИ не пишуть напряму в canonical storage.       │
└─────────────────────────────────────────────────────┘
```

### Глосарій

| Термін | Пояснення |
|--------|-----------|
| **Task** (Завдання) | Одиниця роботи для LLM: prompt, контекст, параметри |
| **Lease** (Оренда) | Тимчасове призначення завдання worker-ноді (TTL 300с за замовчуванням) |
| **Worker** | Машина з Claude CLI, що виконує завдання |
| **Artifact** (Артефакт) | Результат виконання: код, текст, дані |
| **Primary** | Головна нода для проєкту — може push до MinIO |
| **Secondary** | Вторинна нода — тільки pull з MinIO |
| **canonical_id** | `sha256(project_name)[:16]` — унікальний ідентифікатор проєкту |
| **Epoch** | Лічильник оновлень lease (монотонно зростає) |
| **Heartbeat** | Регулярний сигнал "я живий" від worker |

---

## Архітектура системи

### Загальна топологія

```
┌─────────────────────────────────────────────────────────────┐
│                     Браузер оператора                        │
│              http://host:80 (або :5000)                      │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    nginx (reverse proxy)                      │
│                        порт :80                              │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│               BLOOM Runtime (Node.js / Express)              │
│                        порт :5000                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ React SPA    │  │ /api/runtime │  │ /api/membridge   │   │
│  │ (фронтенд)   │  │ (Runtime API)│  │ (проксі до CP)   │   │
│  └──────────────┘  └──────┬───────┘  └────────┬─────────┘   │
│                           │                    │             │
│         ┌─────────────────┤                    │             │
│         ▼                 ▼                    │             │
│  ┌─────────────┐   ┌─────────────┐             │             │
│  │ Auth        │   │ PostgreSQL  │             │             │
│  │ Middleware  │   │ (сховище)   │             │             │
│  └─────────────┘   └─────────────┘             │             │
└────────────────────────────────────────────────┼─────────────┘
                                                 │
                            ┌────────────────────┘
                            │ HTTP + X-MEMBRIDGE-ADMIN
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Membridge Control Plane (Python / FastAPI)          │
│                        порт :8000                            │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────────────────────┐   │
│  │ /projects│  │ /agents  │  │ leadership (lease.json)  │   │
│  └──────────┘  └──────────┘  └──────────────────────────┘   │
└───────────────────────────┬─────────────────────────────────┘
                            │
               ┌────────────┼────────────┐
               ▼            ▼            ▼
        ┌───────────┐ ┌───────────┐ ┌───────────┐
        │ Worker 1  │ │ Worker 2  │ │ Worker N  │
        │ (Claude)  │ │ (Claude)  │ │ (Claude)  │
        └─────┬─────┘ └─────┬─────┘ └─────┬─────┘
              │              │              │
              └──────────────┼──────────────┘
                             ▼
                    ┌────────────────┐
                    │  MinIO (:9000) │
                    │ (object store) │
                    └────────────────┘
```

### Потік даних

```
                    Створення завдання
                           │
                           ▼
                 ┌─────────────────┐
                 │  Черга (queued)  │ ← PostgreSQL
                 └────────┬────────┘
                          │ pickWorker()
                          ▼
                 ┌─────────────────┐
                 │ Lease (leased)  │ ← TTL 300 секунд
                 └────────┬────────┘
                          │ heartbeat кожні N секунд
                          ▼
                 ┌─────────────────┐
                 │ Виконання       │ ← Claude CLI на worker
                 └────────┬────────┘
                          │
                ┌─────────┼──────────┐
                ▼                    ▼
       ┌────────────┐       ┌────────────┐
       │ Завершено  │       │ Помилка    │
       │ (completed)│       │ (failed)   │
       └────────┬───┘       └─────┬──────┘
                │                 │ attempts < 3?
                ▼                 ▼
         ┌───────────┐     ┌───────────┐
         │ Артефакт  │     │ Requeue   │ ← повторна постановка
         │ + Результ │     │ або Dead  │
         └───────────┘     └───────────┘
```

---

## Перший запуск

### Передумови

| Компонент | Вимога |
|-----------|--------|
| Node.js | >= 18 |
| PostgreSQL | Доступний через `DATABASE_URL` |
| npm | Встановлений |

### Кроки

#### 1. Встановлення залежностей

```bash
npm install
```

#### 2. Міграція бази даних

```bash
npm run db:push
```

Це створить всі необхідні таблиці в PostgreSQL:
- `llm_tasks` — завдання
- `leases` — оренди
- `workers` — worker-ноди
- `runtime_artifacts` — артефакти
- `llm_results` — результати
- `audit_logs` — журнал аудиту
- `runtime_settings` — налаштування

#### 3. Змінні середовища

| Змінна | Обов'язкова | Опис | Приклад |
|--------|-------------|------|---------|
| `DATABASE_URL` | Так | PostgreSQL з'єднання | `postgresql://user:pass@host/db` |
| `MEMBRIDGE_SERVER_URL` | Ні | URL Membridge | `http://127.0.0.1:8000` |
| `MEMBRIDGE_ADMIN_KEY` | Ні | Ключ адміністратора Membridge | `<secret>` |
| `RUNTIME_API_KEY` | Ні | Ключ API Runtime (якщо не встановлений — auth вимкнено) | `<secret>` |
| `SESSION_SECRET` | Так | Секрет сесії | `<secret>` |

#### 4. Запуск

```bash
npm run dev
```

Сервер запуститься на порту `5000`. Відкрийте `http://localhost:5000` у браузері.

---

## Інтерфейс користувача

### Навігація

```
┌────────────────────────────────────────────────────┐
│  BLOOM    [Runtime]  [Membridge]                    │
└────────────────────────────────────────────────────┘
         ▲              ▲
         │              │
         │              └── Membridge Control Plane:
         │                  проєкти, лідерство, ноди
         │
         └── Runtime Settings:
             proxy config, workers, leases, tasks
```

### Вкладка Runtime

Три під-вкладки:

#### Membridge Proxy

- **URL сервера** — адреса Membridge control plane
- **Admin Key** — ключ (маскується при відображенні)
- **Save** — зберегти конфігурацію
- **Test Connection** — перевірити з'єднання
- **Workers** — таблиця зареєстрованих workers
- **Active Leases** — таблиця активних оренд

#### Task Queue

- Список завдань з фільтрацією за статусом
- Можливість requeue невдалих завдань

#### Overview

- Статистика: workers online, active leases, total tasks
- Швидкий огляд стану системи

### Вкладка Membridge

```
┌────────────┬────────────────────────────────────────┐
│            │                                        │
│  ПРОЄКТИ   │   ДЕТАЛІ ПРОЄКТУ                      │
│            │                                        │
│  ▸ proj-1  │   Картка лідерства:                    │
│  ▸ proj-2  │   - Primary Node: rpi4b                │
│            │   - Epoch: 3                           │
│  (автоонов │   - Expires: 2026-02-25 15:00:00       │
│   кожні    │                                        │
│   30 сек)  │   Таблиця нод:                         │
│            │   ┌──────┬──────┬─────┬─────┬─────┐    │
│            │   │ Node │ Role │ Obs │ SHA │ IP  │    │
│            │   ├──────┼──────┼─────┼─────┼─────┤    │
│            │   │ rpi4b│ prim │ 42  │ abc │ ... │    │
│            │   │ rpi3 │ sec  │ 38  │ def │ ... │    │
│            │   └──────┴──────┴─────┴─────┴─────┘    │
│            │                                        │
│            │   Промоція primary:                     │
│            │   Node ID: [________]                   │
│            │   Lease:   [3600] сек                   │
│            │   [Promote to Primary]                  │
│            │                                        │
└────────────┴────────────────────────────────────────┘
```

---

## Налаштування Membridge

### Крок 1: Початкова конфігурація

1. Відкрийте **Runtime** → вкладка **Membridge Proxy**
2. Введіть **Membridge Server URL** (наприклад, `http://192.168.3.184:8000`)
3. Введіть **Admin Key** (буде збережений у PostgreSQL, не на фронтенді)
4. Натисніть **Save**

### Крок 2: Перевірка з'єднання

1. Натисніть **Test Connection**
2. Очікуваний результат:

```
✅ Connected
Service: membridge-control-plane
Version: 0.3.0
Projects: 0
Agents: 0
```

### Крок 3: Перевірка у Membridge

1. Перейдіть на вкладку **Membridge**
2. Якщо з'єднання працює — побачите список проєктів зліва
3. Оберіть проєкт — справа з'являться деталі

### Схема підключення

```
Ваш браузер                    BLOOM Runtime                  Membridge
┌──────────┐   HTTP запит   ┌──────────────┐   HTTP + key   ┌──────────┐
│          │ ──────────────▶│              │ ──────────────▶│          │
│ /api/    │                │ membridgeFetch│                │ /projects│
│ membridge│                │ () додає      │                │ /agents  │
│ /projects│                │ X-MEMBRIDGE-  │                │ /health  │
│          │ ◀──────────────│ ADMIN автом.  │ ◀──────────────│          │
│          │   JSON         │              │   JSON         │          │
└──────────┘                └──────────────┘                └──────────┘

⚠️ Ваш браузер НІКОЛИ не бачить Admin Key.
   Він інжектується серверним кодом автоматично.
```

---

## Управління завданнями

### Життєвий цикл завдання

```
┌─────────┐      ┌─────────┐      ┌─────────┐      ┌───────────┐
│ QUEUED  │─────▶│ LEASED  │─────▶│ RUNNING │─────▶│ COMPLETED │
│(в черзі)│      │(орендов)│      │(викон.) │      │(завершено)│
└─────────┘      └────┬────┘      └────┬────┘      └───────────┘
                      │                │
                      │ TTL expired    │ помилка
                      ▼                ▼
               ┌─────────┐      ┌─────────┐
               │ REQUEUE │      │ FAILED  │
               │(повтор) │      │(невдача)│
               └────┬────┘      └────┬────┘
                    │                │ attempts >= 3
                    │                ▼
                    │          ┌─────────┐
                    └─────────▶│  DEAD   │
                               │(мертве) │
                               └─────────┘
```

### Створення завдання (через API)

```bash
curl -X POST http://localhost:5000/api/runtime/llm-tasks \
  -H 'Content-Type: application/json' \
  -H 'X-Runtime-API-Key: <your-key>' \
  -d '{
    "context_id": "project-context-123",
    "agent_slug": "code-review",
    "prompt": "Review this function for security issues",
    "priority": 5,
    "context_hints": {"file": "src/auth.ts"}
  }'
```

### Перегляд завдань

```bash
curl http://localhost:5000/api/runtime/llm-tasks \
  -H 'X-Runtime-API-Key: <your-key>'

curl http://localhost:5000/api/runtime/llm-tasks?status=queued \
  -H 'X-Runtime-API-Key: <your-key>'
```

### Перегляд артефактів

```bash
curl http://localhost:5000/api/runtime/artifacts?task_id=<task-id> \
  -H 'X-Runtime-API-Key: <your-key>'
```

---

## Моніторинг

### Health endpoint

```bash
curl http://localhost:5000/api/runtime/health
```

Відповідь:

```json
{
  "status": "ok",
  "service": "bloom-runtime",
  "uptime": 3600.5,
  "storage": "postgresql",
  "membridge": {
    "consecutiveFailures": 0,
    "lastSuccess": 1740000000000,
    "lastError": null,
    "connected": true
  }
}
```

### Інтерпретація health

| Поле | Значення | Що робити |
|------|----------|-----------|
| `storage: "postgresql"` | БД працює | Нормально |
| `membridge.connected: true` | Membridge відповідає | Нормально |
| `membridge.connected: false` | Membridge не відповідає | Перевірити Membridge сервер |
| `membridge.consecutiveFailures > 5` | Багато невдалих спроб | Перевірити мережу / Membridge |

### Статистика

```bash
curl http://localhost:5000/api/runtime/stats \
  -H 'X-Runtime-API-Key: <your-key>'
```

```json
{
  "tasks": {"total": 42, "by_status": {"completed": 35, "queued": 5, "failed": 2}},
  "leases": {"total": 50, "active": 3},
  "workers": {"total": 2, "online": 2}
}
```

### Audit log

```bash
curl http://localhost:5000/api/runtime/audit?limit=20 \
  -H 'X-Runtime-API-Key: <your-key>'
```

Кожний запис містить: `timestamp`, `action`, `entity_type`, `entity_id`, `actor`, `detail`.

---

## Типові сценарії

### Сценарій 1: Промоція нового Primary

**Ситуація:** Стара primary-нода offline, потрібно призначити нову.

```
1. Відкрити Membridge → обрати проєкт
2. В таблиці нод знайти ноду з
   найбільшим obs_count та свіжим "Last Seen"
3. Ввести Node ID у "Promote Primary"
4. Натиснути "Promote to Primary"
5. Перевірити: Leadership Card оновилась
```

### Сценарій 2: Перевірка синхронізації нод

**Ситуація:** Потрібно переконатись що ноди мають однакову базу.

```
1. Відкрити Membridge → обрати проєкт
2. В таблиці нод порівняти колонку "DB SHA"
3. Якщо SHA однакові → бази синхронізовані ✅
4. Якщо SHA різні → Secondary pull ще не відбувся
   або Primary push не завершений
```

### Сценарій 3: Requeue невдалого завдання

**Ситуація:** Завдання зависло або worker впав.

```bash
curl -X POST http://localhost:5000/api/runtime/llm-tasks/<task-id>/requeue \
  -H 'X-Runtime-API-Key: <your-key>'
```

Або через UI: Runtime → Task Queue → кнопка Requeue.

### Сценарій 4: Діагностика відключеного Membridge

```
1. Перевірити health:
   curl http://localhost:5000/api/runtime/health
   → membridge.connected: false

2. Перевірити Membridge напряму:
   curl http://127.0.0.1:8000/health
   → Якщо не відповідає — Membridge сервер зупинений

3. Перезапустити Membridge:
   sudo rc-service membridge-server restart

4. Перевірити з'єднання:
   Runtime → Membridge Proxy → Test Connection
```

---

## Усунення несправностей

### Проблема: 502 при зверненні до /api/membridge/*

**Причина:** Membridge control plane недоступний.

**Рішення:**
1. Перевірити що Membridge запущений: `curl http://127.0.0.1:8000/health`
2. Перевірити URL у налаштуваннях: Runtime → Membridge Proxy
3. Перевірити мережу між BLOOM Runtime та Membridge

### Проблема: 503 при створенні lease

**Причина:** Немає доступних workers.

**Рішення:**
1. Зареєструвати worker у Membridge (див. GAP-4)
2. Перевірити стан workers: `GET /api/runtime/workers`
3. Перевірити що worker має `status: "online"` та `capabilities.claude_cli: true`

### Проблема: Lease expire (завдання зависає)

**Причина:** Worker не надіслав heartbeat протягом TTL (300с).

**Рішення:**
1. Stale lease буде автоматично скасований (перевірка кожні 30с)
2. Завдання буде поставлено в чергу повторно (якщо attempts < 3)
3. Після 3 спроб завдання отримає статус `dead`
4. Для ручного requeue: `POST /api/runtime/llm-tasks/:id/requeue`

### Проблема: Workers не з'являються у списку

**Причина:** Auto-sync ще не опитав Membridge.

**Рішення:**
1. Зачекати 10 секунд (інтервал auto-sync)
2. Перевірити `/api/membridge/health` — чи Membridge відповідає
3. Перевірити що worker зареєстрований: `GET /agents` на Membridge (:8000)

---

## Довідка з API

### Runtime API (порт 5000)

| Метод | Шлях | Auth | Опис |
|-------|------|------|------|
| `GET` | `/api/runtime/health` | Ні | Стан сервісу |
| `GET` | `/api/runtime/config` | Так | Конфігурація Membridge proxy |
| `POST` | `/api/runtime/config` | Так | Зберегти конфігурацію |
| `POST` | `/api/runtime/test-connection` | Ні | Тест з'єднання з Membridge |
| `GET` | `/api/runtime/workers` | Так | Список workers |
| `GET` | `/api/runtime/workers/:id` | Так | Деталі worker |
| `POST` | `/api/runtime/llm-tasks` | Так | Створити завдання |
| `GET` | `/api/runtime/llm-tasks` | Так | Список завдань (?status=) |
| `GET` | `/api/runtime/llm-tasks/:id` | Так | Деталі завдання |
| `POST` | `/api/runtime/llm-tasks/:id/lease` | Так | Призначити worker |
| `POST` | `/api/runtime/llm-tasks/:id/heartbeat` | Так | Heartbeat lease |
| `POST` | `/api/runtime/llm-tasks/:id/complete` | Так | Завершити завдання |
| `POST` | `/api/runtime/llm-tasks/:id/requeue` | Так | Повторна постановка |
| `GET` | `/api/runtime/leases` | Так | Список leases (?status=) |
| `GET` | `/api/runtime/runs` | Так | Останні виконання |
| `GET` | `/api/runtime/artifacts` | Так | Артефакти (?task_id=) |
| `GET` | `/api/runtime/audit` | Так | Журнал аудиту (?limit=) |
| `GET` | `/api/runtime/stats` | Так | Статистика dashboard |

### Membridge Proxy API (порт 5000)

| Метод | Шлях | Auth | Опис |
|-------|------|------|------|
| `GET` | `/api/membridge/health` | Так | Стан Membridge |
| `GET` | `/api/membridge/projects` | Так | Список проєктів |
| `GET` | `/api/membridge/projects/:cid/leadership` | Так | Lease лідерства |
| `GET` | `/api/membridge/projects/:cid/nodes` | Так | Ноди проєкту |
| `POST` | `/api/membridge/projects/:cid/leadership/select` | Так | Промоція primary |

### Аутентифікація

```
Заголовок: X-Runtime-API-Key: <значення RUNTIME_API_KEY>

Якщо RUNTIME_API_KEY не встановлений → auth вимкнений (dev mode)
Якщо встановлений → усі маршрути (крім /health, /test-connection) вимагають заголовок
```

---

## Безпека

### Модель безпеки

```
┌─────────────────────────────────────────────────────┐
│                 Межі безпеки                        │
│                                                     │
│  Браузер ───────── /api/runtime/* ─── Auth MW ──┐   │
│                                                  │   │
│  Браузер ───────── /api/membridge/* ─ Auth MW ──┤   │
│                                                  │   │
│                                    PostgreSQL ◄──┘   │
│                                                     │
│  BLOOM Runtime ──── membridgeFetch() ──── Membridge │
│      (серверний код інжектує X-MEMBRIDGE-ADMIN)      │
│                                                     │
│  ⚠️ Фронтенд НІКОЛИ не бачить:                     │
│     - MEMBRIDGE_ADMIN_KEY                           │
│     - DATABASE_URL                                  │
│     - RUNTIME_API_KEY (використовується як заголовок)│
└─────────────────────────────────────────────────────┘
```

### Рекомендації

1. **Завжди встановлюйте `RUNTIME_API_KEY`** у production
2. **Використовуйте HTTPS** (GAP-5) при публічному доступі
3. **Перевіряйте audit log** регулярно: `GET /api/runtime/audit`
4. Зберігайте секрети у `/etc/bloom-runtime.env` (chmod 600)

---

## Семантичні зв'язки

**Цей документ залежить від:**
- [[operations/RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — топологія розгортання
- [[operations/RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]] — деталі реалізації
- [[operations/REPLIT_MEMBRIDGE_UI_INTEGRATION.md]] — інтеграція UI

**На цей документ посилаються:**
- [[../ІНДЕКС.md]] — головний індекс документації
