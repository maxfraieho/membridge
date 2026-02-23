---
tags:
  - domain:storage
  - status:canonical
  - format:contract
  - feature:storage
created: 2026-02-24
updated: 2026-02-24
tier: 1
title: "Інтеграція: Membridge Control Plane"
dg-publish: true
---

# Інтеграція: Membridge Control Plane

> Created: 2026-02-24
> Author: architect
> Status: canonical
> Мова: Ukrainian (canonical)

---

## 0. Призначення

Визначає архітектурну роль Membridge у системі Garden Bloom як інфраструктурного шару синхронізації пам'яті Claude CLI між вузлами мережі.

Membridge управляє синхронізацією `claude-mem.db` (SQLite) між edge-вузлами (Alpine, RPi, Orange Pi) та об'єктним сховищем MinIO. Він є незалежним від `garden-bloom-memory` git-монорепо — два сховища обслуговують різні шари пам'яті:

| Сховище | Тип пам'яті | Хто пише |
|---------|-------------|---------|
| `claude-mem.db` → MinIO (через Membridge) | Claude CLI session memory | Claude CLI + membridge hooks |
| `garden-bloom-memory` (git) | Agent reasoning memory (Layer 1/2) | Apply Engine via Proposals |

**Аксіома A1:** MinIO є canonical object storage; Membridge є гейткіпером запису до нього для claude-mem.

---

## 1. Компоненти

```
Alpine (192.168.3.184)
├── membridge-server  :8000   ← Control Plane API; leadership registry; Web UI
└── membridge-agent   :8001   ← Local project registry; heartbeat sender

RPi / Orange Pi (edge nodes)
└── membridge-agent   :8001   ← Local sync; heartbeat до Alpine :8000
```

### 1.1 membridge-server (Control Plane)

- FastAPI; порт 8000
- Приймає heartbeats від агентів
- Реєструє проекти та вузли
- Надає leadership API (select primary, view lease)
- Служить Web UI на `/ui` (→ `/static/ui.html`)

### 1.2 membridge-agent (Edge Agent)

- FastAPI; порт 8001
- Зберігає локальний реєстр проектів (`~/.membridge/agent_projects.json`)
- Надсилає heartbeat до control plane кожні `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS` (default: 10s)
- Auth-exempt для localhost; вимагає `X-MEMBRIDGE-AGENT` для remote

---

## 2. Leadership Model (Модель лідерства)

### 2.1 Ролі вузлів

| Роль | Дозволи |
|------|---------|
| **Primary** (Первинний) | Push до MinIO ✅ · Pull → відмовляє якщо є local DB ✅ |
| **Secondary** (Вторинний) | Push → заблоковано за замовчуванням ❌ · Pull (з backup) ✅ |

**Інваріант:** лише один вузол є Primary для кожного проекту в будь-який момент часу.

### 2.2 Leadership Lease (Оренда лідерства)

Зберігається в MinIO: `projects/<canonical_id>/leadership/lease.json`

```json
{
  "canonical_id":     "sha256(project_name)[:16]",
  "primary_node_id":  "alpine",
  "issued_at":        1706000000,
  "expires_at":       1706003600,
  "lease_seconds":    3600,
  "epoch":            3,
  "policy":           "primary_authoritative",
  "issued_by":        "alpine",
  "needs_ui_selection": false
}
```

**Поле `epoch`:** монотонно зростає при кожному поновленні. Запобігає гонці стану між двома вузлами, що одночасно намагаються стати Primary.

### 2.3 Lease State Machine

```
                ┌──────────────┐
                │   ABSENT     │
                └──────┬───────┘
                       │ перший запис
                ┌──────▼───────┐
          ┌─────│    VALID     │─────┐
          │     └──────┬───────┘     │
          │ current    │ expires_at  │ current
          │ node =     │ пройшло     │ node ≠
          │ primary    ▼             │ primary
          │     ┌──────────────┐     │
          │     │   EXPIRED    │     │
          │     └──────┬───────┘     │
          │            │             │
          │   PRIMARY_NODE_ID        │
          │   matches current?       │
          │   YES → renew (epoch+1)  │
          ▼   NO → secondary        ▼
      [Primary]                 [Secondary]
```

### 2.4 Визначення ролі (алгоритм)

```
1. Читати lease.json з MinIO
2. Якщо відсутній → створити (primary = PRIMARY_NODE_ID env або current node)
3. Якщо expired:
   а. Якщо PRIMARY_NODE_ID == NODE_ID → поновити lease (epoch+1)
   б. Інакше → перечитати; якщо ще expired → роль = secondary
4. Якщо valid:
   роль = primary  якщо primary_node_id == NODE_ID
   роль = secondary інакше
```

---

## 3. Push / Pull Protocol (Протокол синхронізації)

### 3.1 Primary Push

```
1. Перевірити роль → primary ✅
2. Зупинити worker (для консистентного snapshot)
3. VACUUM INTO temp + перевірка цілісності
4. Перезапустити worker
5. Обчислити SHA256 snapshot
6. Порівняти з remote SHA256 (пропустити якщо однакові)
7. Отримати distributed push lock
8. Upload DB + SHA256 + manifest до MinIO
9. Верифікувати remote SHA256
```

### 3.2 Secondary Pull

```
1. Перевірити роль → secondary ✅
2. Завантажити remote SHA256
3. Порівняти з local (пропустити якщо однакові)
4. Завантажити remote DB до temp файлу
5. Верифікувати SHA256
6. Safety backup local DB → ~/.claude-mem/backups/pull-overwrite/<ts>/
7. Зупинити worker
8. Атомарна заміна local DB
9. Перевірити цілісність + перезапустити worker
```

### 3.3 Lock Model

| Тип | Шлях у MinIO | TTL | Призначення |
|-----|-------------|-----|-------------|
| Push lock | `projects/<cid>/locks/active.lock` | `LOCK_TTL_SECONDS` (2h) | Заборона паралельних push |
| Leadership lease | `projects/<cid>/leadership/lease.json` | `LEADERSHIP_LEASE_SECONDS` (1h) | Визначення Primary/Secondary |

Push lock та Leadership lease — незалежні механізми.

---

## 4. Artifact Registry (Реєстр артефактів)

Membridge Control Plane веде метаданий реєстр артефактів у MinIO:

```
projects/<canonical_id>/
├── artifacts/
│   └── <artifact_id>.json     ← metadata: type, job_id, created_at, url
├── leadership/
│   ├── lease.json
│   └── audit/<ts>-<node_id>.json
├── locks/
│   └── active.lock
└── db/
    ├── <sha256>.db             ← canonical SQLite snapshot
    └── <sha256>.sha256
```

**Immutability rule:** артефакт після запису до MinIO є immutable. Повторний запис з тим самим `artifact_id` повертає наявний запис без помилки (ідемпотентний).

---

## 5. Control Plane API (Поверхня API)

### 5.1 Public endpoints (без автентифікації)

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/health` | Service health |
| `GET` | `/ui` | → redirect до `/static/ui.html` |

### 5.2 Admin endpoints (вимагають `X-MEMBRIDGE-ADMIN`)

| Метод | Шлях | Опис |
|-------|------|------|
| `GET` | `/projects` | Список проектів (manual + heartbeat) |
| `GET` | `/projects/<cid>/leadership` | Поточний lease |
| `POST` | `/projects/<cid>/leadership/select` | Вибір Primary вузла |
| `GET` | `/agents` | Список зареєстрованих агентів |
| `POST` | `/agent/heartbeat` | Прийом heartbeat від агента |
| `GET` | `/jobs` | Список Job (статус, тип) |
| `PATCH` | `/jobs/<id>/status` | Оновлення статусу Job |
| `POST` | `/jobs/<id>/requeue` | Повторна постановка DEAD job |

### 5.3 Agent endpoints (порт 8001; `X-MEMBRIDGE-AGENT` для remote)

| Метод | Шлях | Auth | Опис |
|-------|------|------|------|
| `GET` | `/health` | — | Agent health |
| `GET` | `/projects` | — | Local project registry |
| `POST` | `/register_project` | localhost exempt | Реєстрація проекту |

---

## 6. Environment Variables (Override Protocol)

Змінні CLI-середовища перекривають значення з `config.env`. Реалізовано через save/restore pattern у hooks.

| Змінна | Default | Призначення |
|--------|---------|-------------|
| `FORCE_PUSH` | `0` | Примусовий push (обходить stale lock) |
| `ALLOW_SECONDARY_PUSH` | `0` | Дозволити Secondary push (unsafe) |
| `ALLOW_PRIMARY_PULL_OVERRIDE` | `0` | Дозволити Primary pull-overwrite (unsafe) |
| `STALE_LOCK_GRACE_SECONDS` | `60` | Додатковий grace після закінчення TTL lock |
| `LOCK_TTL_SECONDS` | `7200` | TTL push lock |
| `LEADERSHIP_LEASE_SECONDS` | `3600` | TTL leadership lease |
| `LEADERSHIP_ENABLED` | `1` | `0` → вимкнути всі leadership перевірки |

---

## 7. Heartbeat Flow (Потік heartbeat)

```
membridge-agent (port 8001)
        │
        │ кожні HEARTBEAT_INTERVAL_SECONDS (default 10s)
        │ читає ~/.membridge/agent_projects.json
        │
        ▼
POST /agent/heartbeat  →  membridge-server (port 8000)
{
  "node_id":      "alpine",
  "canonical_id": "abc123def456abcd",
  "project_id":   "garden-seedling",
  "ip_addrs":     ["192.168.3.184"],
  "obs_count":    1234,
  "db_sha":       "deadbeef..."
}
        │
        ▼
server: _nodes[] + _heartbeat_projects[] (in-memory)
        │
        ▼
GET /projects → Frontend (Web UI)
```

**Примітка:** `_heartbeat_projects` зберігаються в пам'яті сервера. Після рестарту сервера відновлюються через наступний heartbeat цикл (≤ HEARTBEAT_INTERVAL_SECONDS).

---

## 8. Failure Scenarios та Recovery

| Сценарій | Поведінка | Recovery |
|----------|-----------|----------|
| Primary offline; lease expired | Secondary не може push; needs_ui_selection стає true | Operator: `POST /projects/<cid>/leadership/select` для нового Primary |
| Push lock stuck | Наступний push: steal lock після TTL + grace | `FORCE_PUSH=1 cm-push` або чекати TTL |
| MinIO недоступний | Push → error; pull → error | Всі операції fail-safe; local DB незмінна |
| Secondary local-ahead | Secondary має більше записів ніж remote | Promote Secondary → Primary, потім push |
| Agent reboots | Heartbeat відновлюється автоматично | Нічого не потрібно; cервер оновить стан |
| Server reboot | _heartbeat_projects очищуються | Відновлення через ≤ HEARTBEAT_INTERVAL_SECONDS |

---

## Semantic Relations

**Цей документ є частиною:**
- [[_INDEX]] — Integration Layer, індекс пакету

**Залежить від:**
- [[АРХІТЕКТУРНИЙ_КОРІНЬ]] — A1 (MinIO canonical), A2 (consent-based mutation)
- [[КАНОНІЧНА_МОДЕЛЬ_АВТОРИТЕТУ_СХОВИЩА]] — матриця запису до MinIO

**На цей документ посилаються:**
- [[ІНТЕГРАЦІЯ_MEMORY_BACKEND]] — Membridge vs Memory Backend: два різних сховища
- [[RUNTIME_TOPOLOGY_NOTEBOOKLM]] — Membridge як вузол топології (Alpine :8000/:8001)
- [[JOB_QUEUE_ТА_ARTIFACT_MODEL]] — Artifact Store в MinIO
- [[ІНТЕГРАЦІЯ_FRONTEND_LOVABLE]] — Web UI через Membridge `/ui`
