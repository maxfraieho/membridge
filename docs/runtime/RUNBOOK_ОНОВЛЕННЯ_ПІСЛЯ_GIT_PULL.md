---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - format:runbook
created: 2026-02-25
updated: 2026-02-26
title: "RUNBOOK_ОНОВЛЕННЯ_ПІСЛЯ_GIT_PULL"
dg-publish: true
---

# Runbook: Оновлення BLOOM Runtime після git pull

> Створено: 2026-02-25 | Оновлено: 2026-02-26
> Статус: Canonical
> Аудиторія: Claude агент на локальному сервері (Alpine Linux)
> Призначення: Prompt-інструкція для автоматичного оновлення, тестування та усунення проблем
> Changelog: 2026-02-26 — додано smoke-тести Node Management, agent health, install script, managed projects

---

## Prompt для Claude агента

Скопіюй цей блок як промт для Claude на локальному сервері:

````
Ти — Claude агент на production-сервері (Alpine Linux).
Репозиторій: /home/vokov/membridge
Сервіс: bloom-runtime (Node.js/Express + React SPA)
Membridge CP: Python/FastAPI на :8000

Щойно виконано `git pull` з оновленнями від Replit. Твоє завдання:

1. ПЕРЕВІРИТИ ПЕРЕДУМОВИ — PostgreSQL повинен працювати локально, DATABASE_URL повинен бути в /etc/bloom-runtime.env
2. ОНОВИТИ СИСТЕМУ — встановити залежності, мігрувати БД, зібрати production bundle
3. ПРОТЕСТУВАТИ — перевірити всі ключові endpoints та UI
4. ПЕРЕВІРИТИ КОНВЕЄР — переконатись що весь pipeline працює
5. УСУНУТИ ПРОБЛЕМИ — якщо щось не працює, виправити та повідомити

ВАЖЛИВО: Нова збірка (починаючи з commit 150b491) вимагає PostgreSQL.
Стара збірка працювала на in-memory storage — нова використовує DatabaseStorage (Drizzle ORM + PostgreSQL).
Якщо DATABASE_URL відсутній в /etc/bloom-runtime.env — сервіс НЕ стартує.
Спочатку виконай "Крок 0: Підготовка PostgreSQL" з runbook.

ІНВАРІАНТИ (НІКОЛИ не порушуй):
- НЕ модифікуй sqlite_minio_sync.py
- НЕ змішуй два шари пам'яті: claude-mem.db (Membridge/MinIO) та DiffMem/git
- НЕ видаляй та не змінюй існуючі рядки /etc/bloom-runtime.env (тільки ДОДАВАЙ нові)
- НЕ видаляй дані з PostgreSQL без явної необхідності
- НЕ показуй значення секретів у виводі
- НЕ використовуй Replit/Neon DATABASE_URL — тільки локальний PostgreSQL

Виконай кроки нижче послідовно. При помилці — зупинись, повідом причину, запропонуй рішення.
Документ: docs/runtime/RUNBOOK_ОНОВЛЕННЯ_ПІСЛЯ_GIT_PULL.md
````

---

## Крок 0: Підготовка PostgreSQL (одноразово, при першому оновленні)

> **Цей крок потрібен ТІЛЬКИ якщо PostgreSQL ще не налаштований на сервері.**
> Попередня збірка (до commit 150b491) працювала на in-memory storage.
> Нова збірка вимагає PostgreSQL — без `DATABASE_URL` сервіс НЕ стартує.

### 0.1 Перевірити чи PostgreSQL вже є

```bash
# Перевірити чи PostgreSQL встановлений
which psql && psql --version

# Перевірити чи сервіс запущений
sudo rc-service postgresql status 2>/dev/null || echo "PostgreSQL не встановлений"

# Перевірити чи DATABASE_URL є в bloom-runtime.env
grep DATABASE_URL /etc/bloom-runtime.env 2>/dev/null || echo "DATABASE_URL ВІДСУТНІЙ"
```

Якщо PostgreSQL запущений і DATABASE_URL є — переходь до Кроку 1.

### 0.2 Встановити PostgreSQL (якщо відсутній)

```bash
# Alpine Linux
sudo apk add postgresql postgresql-client postgresql-contrib

# Ініціалізувати кластер
sudo /etc/init.d/postgresql setup

# Запустити
sudo rc-service postgresql start
sudo rc-update add postgresql default    # автозапуск при boot
```

### 0.3 Створити базу та користувача

```bash
# Створити користувача bloom з паролем
sudo -u postgres createuser -P bloom
# (введіть надійний пароль, запам'ятайте його)

# Створити базу
sudo -u postgres createdb -O bloom bloom_runtime

# Перевірити підключення
psql -U bloom -d bloom_runtime -h 127.0.0.1 -c "SELECT 1"
```

### 0.4 Додати DATABASE_URL в bloom-runtime.env

```bash
# ЗАМІНІТЬ <password> на реальний пароль, створений вище
sudo sh -c 'echo "DATABASE_URL=postgresql://bloom:<password>@127.0.0.1:5432/bloom_runtime" >> /etc/bloom-runtime.env'

# Перевірити
grep DATABASE_URL /etc/bloom-runtime.env
```

### 0.5 Створити таблиці

```bash
cd /home/vokov/membridge
source /etc/bloom-runtime.env
npx drizzle-kit push
```

**Очікуваний результат:**
```
Changes applied successfully
```

Будуть створені таблиці: `llm_tasks`, `leases`, `workers`, `runtime_artifacts`, `llm_results`, `audit_logs`, `runtime_settings`, `users`, `managed_projects`, `project_node_status`.

### 0.6 Перевірити

```bash
source /etc/bloom-runtime.env
psql $DATABASE_URL -c "\dt"
```

Повинні бути видимі всі 10 таблиць.

### Схема підключення (нова vs стара збірка)

```
СТАРА ЗБІРКА (до commit 150b491):
┌──────────────┐
│ bloom-runtime│
│              │ ← MemStorage (в пам'яті)
│ Express :5000│ ← Дані зникають при рестарті
└──────────────┘

НОВА ЗБІРКА (після commit 150b491):
┌──────────────┐      ┌──────────────┐
│ bloom-runtime│      │  PostgreSQL  │
│              │─────▶│  :5432       │
│ Express :5000│      │  bloom_runtime│
└──────────────┘      └──────────────┘
                      ← DatabaseStorage
                      ← Дані переживають рестарт
                      ← DATABASE_URL обов'язковий
```

---

## Крок 1: Підготовка — перевірка стану перед оновленням

```bash
# Перевірити поточний стан сервісу
sudo rc-service bloom-runtime status
sudo rc-service membridge-server status

# Зберегти поточний commit (для можливого rollback)
cd /home/vokov/membridge
PREV_COMMIT=$(git rev-parse HEAD)
echo "Попередній commit: $PREV_COMMIT"

# Перевірити що git pull вже виконано
git log --oneline -3

# Перевірити чи є зміни в package.json (потрібен npm install)
git diff $PREV_COMMIT HEAD --name-only | grep -E 'package\.json|package-lock\.json'

# Перевірити чи є зміни в schema (потрібен db:push)
git diff $PREV_COMMIT HEAD --name-only | grep -E 'shared/schema\.ts|drizzle\.config'

# Перевірити чи є зміни в серверному/клієнтському коді (потрібен rebuild)
git diff $PREV_COMMIT HEAD --name-only | grep -E '\.(ts|tsx|css)$'
```

**Очікуваний результат:**
- Сервіси працюють (started)
- `git pull` завершено
- Відомо які файли змінились

---

## Крок 2: Встановлення залежностей

```bash
cd /home/vokov/membridge

# Встановити/оновити npm пакети
npm install

# Перевірити що встановлення пройшло без помилок
echo "npm install: $?"
```

**Якщо помилка:**
- `ERESOLVE` → спробувати `npm install --legacy-peer-deps`
- `EACCES` → перевірити права на `node_modules/`
- `ENOMEM` → недостатньо пам'яті, закрити непотрібні процеси

---

## Крок 3: Міграція бази даних

```bash
cd /home/vokov/membridge

# Перевірити що DATABASE_URL доступний
# (читається з /etc/bloom-runtime.env або оточення)
source /etc/bloom-runtime.env 2>/dev/null

# Застосувати зміни схеми
npx drizzle-kit push

# Якщо drizzle-kit push відмовляє через деструктивні зміни:
# npx drizzle-kit push --force
# ⚠️ ОБЕРЕЖНО: --force може видалити дані. Спочатку зроби backup:
# pg_dump $DATABASE_URL > /tmp/bloom_backup_$(date +%Y%m%d_%H%M%S).sql
```

**Очікуваний результат:**
- `Changes applied` або `No changes detected`
- Жодних помилок підключення до PostgreSQL

**Якщо помилка:**
- `connection refused` → перевірити що PostgreSQL запущений: `sudo rc-service postgresql status`
- `relation already exists` → нормально, drizzle-kit пропустить
- `column cannot be cast` → потрібен backup + `--force`, або ручна міграція

---

## Крок 4: Збірка production bundle

```bash
cd /home/vokov/membridge

# Зібрати серверний bundle (esbuild) та клієнтський (Vite)
npm run build

# Перевірити що артефакти створені
ls -la dist/index.cjs
ls -la dist/public/assets/index-*.js
ls -la dist/public/assets/index-*.css

echo "Build size: $(du -sh dist/ | cut -f1)"
```

**Очікуваний результат:**
- `dist/index.cjs` — ~900KB+
- `dist/public/assets/index-*.js` — ~250KB+
- `dist/public/assets/index-*.css` — ~60KB+

**Якщо помилка:**
- TypeScript помилка → прочитати помилку, виправити файл, повторити `npm run build`
- `Cannot find module` → `npm install` не завершився коректно, повторити

---

## Крок 5: Перезапуск сервісу

```bash
# Зупинити → запустити (не restart, для чистого старту)
sudo rc-service bloom-runtime stop
sleep 2
sudo rc-service bloom-runtime start

# Перевірити стан
sudo rc-service bloom-runtime status

# Зачекати 5 секунд для ініціалізації
sleep 5

# Перевірити логи на помилки
sudo tail -20 /var/log/bloom-runtime-error.log
sudo tail -10 /var/log/bloom-runtime.log
```

**Очікуваний результат:**
- Статус: `started`
- В логах: `serving on port 5000`
- Без помилок у error.log

**Якщо помилка:**
- `Error: Cannot find module` → збірка не завершилась, повторити крок 4
- `EADDRINUSE` → порт зайнятий: `sudo fuser -k 5000/tcp`, потім знову start
- `database connection failed` → перевірити `DATABASE_URL` у `/etc/bloom-runtime.env`

---

## Крок 6: Smoke-тести — Runtime API

```bash
# 6.1 Health endpoint (без auth)
echo "=== Health ==="
curl -s http://127.0.0.1:5000/api/runtime/health | python3 -m json.tool

# Очікується: {"status":"ok","service":"bloom-runtime","storage":"postgresql",...}
# Перевірити: storage повинен бути "postgresql", НЕ "memory"

# 6.2 Stats (потребує auth якщо RUNTIME_API_KEY встановлений)
echo "=== Stats ==="
curl -s http://127.0.0.1:5000/api/runtime/stats \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool

# Очікується: {"tasks":{"total":...},"leases":{"total":...},"workers":{"total":...}}

# 6.3 Workers
echo "=== Workers ==="
curl -s http://127.0.0.1:5000/api/runtime/workers \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool

# 6.4 Config (перевірити що membridge URL збережений)
echo "=== Config ==="
curl -s http://127.0.0.1:5000/api/runtime/config \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool

# Очікується: membridge_server_url = "http://127.0.0.1:8000"

# 6.5 Audit log (перевірити що персистовані записи не зникли)
echo "=== Audit ==="
curl -s "http://127.0.0.1:5000/api/runtime/audit?limit=5" \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool
```

**Контрольна таблиця:**

| Тест | Очікуваний код | Що перевіряти |
|------|---------------|---------------|
| `/api/runtime/health` | 200 | `storage: "postgresql"`, `membridge.connected` |
| `/api/runtime/stats` | 200 | JSON з counters |
| `/api/runtime/workers` | 200 | Масив (може бути порожній) |
| `/api/runtime/config` | 200 | `membridge_server_url` не порожній |
| `/api/runtime/audit` | 200 | Масив записів (має містити попередні) |

### 6.6 Node Management (НОВЕ)

```bash
# Workers з розширеними полями
echo "=== Workers (extended) ==="
curl -s http://127.0.0.1:5000/api/runtime/workers \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -c "
import sys, json
workers = json.load(sys.stdin)
for w in workers:
    print(f'  {w[\"id\"]}: status={w[\"status\"]}, version={w.get(\"agent_version\",\"?\")}, os={w.get(\"os_info\",\"?\")}, method={w.get(\"install_method\",\"?\")}')
"

# Agent health check (якщо worker має URL)
echo "=== Agent Health ==="
WORKER_ID=$(curl -s http://127.0.0.1:5000/api/runtime/workers \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -c "import sys,json; ws=json.load(sys.stdin); print(ws[0]['id'] if ws else '')" 2>/dev/null)

if [ -n "$WORKER_ID" ]; then
    curl -s "http://127.0.0.1:5000/api/runtime/workers/$WORKER_ID/agent-health" \
      -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
      | python3 -m json.tool
fi

# Install script generation
echo "=== Install Script ==="
curl -s "http://127.0.0.1:5000/api/runtime/agent-install-script?node_id=test-node" \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | head -5
echo "..."

# Managed Projects
echo "=== Managed Projects ==="
curl -s http://127.0.0.1:5000/api/runtime/projects \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool
```

**Контрольна таблиця:**

| Тест | Очікуваний код | Що перевіряти |
|------|---------------|---------------|
| Workers (extended) | 200 | `agent_version`, `os_info`, `install_method` поля присутні |
| Agent health | 200 | `reachable: true/false` (залежить від доступності агента) |
| Install script | 200 | Bash-скрипт з правильним SERVER_URL |
| Managed projects | 200 | Масив проєктів (може бути порожній) |

---

## Крок 7: Smoke-тести — Membridge Proxy

```bash
# 7.1 Membridge health через проксі
echo "=== Membridge Health ==="
curl -s http://127.0.0.1:5000/api/membridge/health \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool

# Очікується: 200 з {"status":"ok","service":"membridge-control-plane",...}

# 7.2 Membridge projects
echo "=== Membridge Projects ==="
curl -s http://127.0.0.1:5000/api/membridge/projects \
  -H "X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool

# 7.3 Тест з'єднання
echo "=== Test Connection ==="
curl -s -X POST http://127.0.0.1:5000/api/runtime/test-connection \
  | python3 -m json.tool

# Очікується: {"connected":true,"health":{...}}
```

**Контрольна таблиця:**

| Тест | Очікуваний код | Що перевіряти |
|------|---------------|---------------|
| `/api/membridge/health` | 200 | Membridge відповідає |
| `/api/membridge/projects` | 200 | Масив проєктів |
| `/api/runtime/test-connection` | 200 | `connected: true` |

**Якщо 502:**
- Перевірити Membridge: `curl -s http://127.0.0.1:8000/health`
- Якщо Membridge не відповідає: `sudo rc-service membridge-server restart`
- Якщо URL невірний: оновити через API або UI

---

## Крок 8: Smoke-тести — nginx та фронтенд

```bash
# 8.1 nginx → bloom-runtime
echo "=== nginx proxy ==="
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/
# Очікується: 200

# 8.2 API через nginx
echo "=== nginx → API ==="
curl -s http://127.0.0.1:80/api/runtime/health | python3 -m json.tool
# Очікується: те саме що на :5000

# 8.3 Перевірити що SPA-assets завантажуються
echo "=== SPA assets ==="
curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:80/assets/$(ls dist/public/assets/ | grep '\.js$' | head -1)
# Очікується: 200
```

---

## Крок 9: Тест Python-бекенду (Membridge Control Plane)

```bash
cd /home/vokov/membridge

# 9.1 Запустити pytest
MEMBRIDGE_DEV=1 MEMBRIDGE_AGENT_DRYRUN=1 python -m pytest tests/ -v

# 9.2 Перевірити Membridge endpoints напряму
echo "=== Membridge direct health ==="
curl -s http://127.0.0.1:8000/health | python3 -m json.tool

echo "=== Membridge agents ==="
curl -s http://127.0.0.1:8000/agents \
  -H "X-MEMBRIDGE-ADMIN: $(grep MEMBRIDGE_ADMIN_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)" \
  | python3 -m json.tool
```

**Очікуваний результат:**
- Всі pytest тести проходять (36 тестів)
- Membridge `/health` повертає 200
- Membridge `/agents` повертає масив агентів

---

## Крок 10: Перевірка конвеєра виконання (End-to-End)

```bash
# Цей крок перевіряє повний pipeline: create → lease → complete
# Працює тільки якщо є зареєстровані workers

AUTH_HEADER="X-Runtime-API-Key: $(grep RUNTIME_API_KEY /etc/bloom-runtime.env 2>/dev/null | cut -d= -f2)"

# 10.1 Створити тестове завдання
echo "=== Create Task ==="
TASK_RESPONSE=$(curl -s -X POST http://127.0.0.1:5000/api/runtime/llm-tasks \
  -H "$AUTH_HEADER" \
  -H "Content-Type: application/json" \
  -d '{
    "context_id": "test-update-verification",
    "agent_slug": "smoke-test",
    "prompt": "Echo test: verify pipeline after git pull update",
    "priority": 1
  }')
echo "$TASK_RESPONSE" | python3 -m json.tool

TASK_ID=$(echo "$TASK_RESPONSE" | python3 -c "import sys,json; print(json.load(sys.stdin)['id'])" 2>/dev/null)
echo "Task ID: $TASK_ID"

if [ -z "$TASK_ID" ]; then
    echo "⚠️ Не вдалось створити завдання. Перевірте логи."
else
    # 10.2 Спробувати lease
    echo "=== Lease Task ==="
    LEASE_RESPONSE=$(curl -s -X POST "http://127.0.0.1:5000/api/runtime/llm-tasks/$TASK_ID/lease" \
      -H "$AUTH_HEADER" \
      -H "Content-Type: application/json")
    echo "$LEASE_RESPONSE" | python3 -m json.tool

    LEASE_STATUS=$(echo "$LEASE_RESPONSE" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('error','ok'))" 2>/dev/null)

    if [ "$LEASE_STATUS" = "No available worker with free capacity" ]; then
        echo "ℹ️ Lease: 503 — немає зареєстрованих workers (очікувана поведінка)"
        echo "   Pipeline до lease працює коректно."
        echo "   Для повного E2E тесту потрібно зареєструвати worker."
    else
        echo "Lease отримано, можна продовжити heartbeat → complete"
    fi

    # 10.3 Перевірити що завдання створилось
    echo "=== Verify Task ==="
    curl -s "http://127.0.0.1:5000/api/runtime/llm-tasks/$TASK_ID" \
      -H "$AUTH_HEADER" | python3 -m json.tool
fi
```

---

## Крок 11: Фінальний звіт

```bash
echo "============================================"
echo "  BLOOM Runtime — Звіт оновлення"
echo "============================================"
echo ""
echo "Дата: $(date)"
echo "Commit: $(cd /home/vokov/membridge && git rev-parse --short HEAD)"
echo "Node.js: $(node --version)"
echo "npm: $(npm --version)"
echo ""

# Health
HEALTH=$(curl -s http://127.0.0.1:5000/api/runtime/health)
echo "Health:"
echo "  Status: $(echo $HEALTH | python3 -c 'import sys,json; print(json.load(sys.stdin)["status"])' 2>/dev/null)"
echo "  Storage: $(echo $HEALTH | python3 -c 'import sys,json; print(json.load(sys.stdin)["storage"])' 2>/dev/null)"
echo "  Membridge connected: $(echo $HEALTH | python3 -c 'import sys,json; print(json.load(sys.stdin).get("membridge",{}).get("connected","unknown"))' 2>/dev/null)"
echo ""

# Services
echo "Services:"
echo "  bloom-runtime: $(sudo rc-service bloom-runtime status 2>&1 | grep -oE 'started|stopped|crashed')"
echo "  membridge-server: $(sudo rc-service membridge-server status 2>&1 | grep -oE 'started|stopped|crashed')"
echo "  nginx: $(sudo rc-service nginx status 2>&1 | grep -oE 'started|stopped|crashed')"
echo "  postgresql: $(sudo rc-service postgresql status 2>&1 | grep -oE 'started|stopped|crashed')"
echo ""

# Build artifacts
echo "Build:"
echo "  Server bundle: $(ls -lh /home/vokov/membridge/dist/index.cjs 2>/dev/null | awk '{print $5}')"
echo "  SPA JS: $(ls -lh /home/vokov/membridge/dist/public/assets/index-*.js 2>/dev/null | awk '{print $5}')"
echo ""

echo "============================================"
echo "  Оновлення завершено"
echo "============================================"
```

---

## Rollback (якщо щось пішло не так)

```bash
cd /home/vokov/membridge

# Повернутись до попереднього commit
git checkout $PREV_COMMIT -- .
# або
git reset --hard $PREV_COMMIT

# Перебудувати та перезапустити
npm install
npm run build
sudo rc-service bloom-runtime restart

# Перевірити
curl -s http://127.0.0.1:5000/api/runtime/health
```

Якщо потрібно відкатити міграцію БД:

```bash
# Відновити з backup
psql $DATABASE_URL < /tmp/bloom_backup_<дата>.sql
```

---

## Типові проблеми після git pull

### Проблема: `Cannot find module 'xxx'`

```bash
# Новий пакет додано в package.json але не встановлено
npm install
npm run build
sudo rc-service bloom-runtime restart
```

### Проблема: `column "xxx" does not exist`

```bash
# Схема змінилась, потрібна міграція
source /etc/bloom-runtime.env
npx drizzle-kit push
sudo rc-service bloom-runtime restart
```

### Проблема: `ECONNREFUSED 127.0.0.1:5432`

```bash
# PostgreSQL не запущений
sudo rc-service postgresql start
sudo rc-service bloom-runtime restart
```

### Проблема: `502 Bad Gateway` від nginx

```bash
# bloom-runtime не запустився або впав
sudo rc-service bloom-runtime status
sudo tail -50 /var/log/bloom-runtime-error.log

# Перезапустити
sudo rc-service bloom-runtime restart
```

### Проблема: Membridge proxy повертає 502

```bash
# Membridge CP не запущений
sudo rc-service membridge-server status
sudo rc-service membridge-server restart

# Або URL невірний — перевірити config
curl -s http://127.0.0.1:5000/api/runtime/config \
  -H "X-Runtime-API-Key: <key>" | python3 -m json.tool
```

### Проблема: `storage: "memory"` замість `"postgresql"`

```bash
# DATABASE_URL не встановлений або невірний
grep DATABASE_URL /etc/bloom-runtime.env

# Перевірити підключення
psql $(grep DATABASE_URL /etc/bloom-runtime.env | cut -d= -f2-) -c "SELECT 1"

# Якщо таблиць немає:
source /etc/bloom-runtime.env
npx drizzle-kit push
sudo rc-service bloom-runtime restart
```

### Проблема: Auth помилка 401 на API

```bash
# RUNTIME_API_KEY не збігається
grep RUNTIME_API_KEY /etc/bloom-runtime.env

# Тест без auth (health не вимагає)
curl -s http://127.0.0.1:5000/api/runtime/health

# Якщо RUNTIME_API_KEY не потрібен — видалити рядок з bloom-runtime.env
# та перезапустити сервіс
```

---

## Чеклист (скорочена версія)

```
□ git pull виконано
□ npm install — без помилок
□ npx drizzle-kit push — schema up to date
□ npm run build — bundle створено
□ rc-service bloom-runtime restart — started
□ /api/runtime/health → 200, storage: "postgresql"
□ /api/runtime/stats → 200
□ /api/membridge/health → 200
□ /api/runtime/test-connection → connected: true
□ nginx :80 → 200
□ pytest tests/ → all pass
□ Фронтенд завантажується в браузері
□ Вкладки Runtime та Membridge працюють
```

---

## Семантичні зв'язки

**Цей документ залежить від:**
- [[operations/RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — топологія, сервіси, шляхи
- [[НАЛАШТУВАННЯ_ТА_РОЗГОРТАННЯ.md]] — повна інструкція з налаштування
- [[ПОСІБНИК_КОРИСТУВАЧА_BLOOM_RUNTIME.md]] — посібник з використання UI

**На цей документ посилаються:**
- [[../ІНДЕКС.md]] — головний індекс документації
