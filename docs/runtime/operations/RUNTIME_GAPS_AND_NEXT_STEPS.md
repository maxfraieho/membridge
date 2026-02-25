---
tags:
  - domain:runtime
  - status:canonical
  - layer:operations
  - authority:production
created: 2026-02-25
updated: 2026-02-25
changelog:
  - 2026-02-25 (rev 3): GAP-7 позначено RESOLVED. Документ переписано українською. Оновлено матрицю.
  - 2026-02-25 (rev 2): GAP-1 and GAP-2 marked RESOLVED (Replit commit 150b491). GAP-7 added.
title: "RUNTIME_GAPS_AND_NEXT_STEPS"
dg-publish: true
---

# BLOOM Runtime — Прогалини та наступні кроки

> Створено: 2026-02-25
> Статус: Canonical
> Layer: Runtime Operations
> Authority: Production Environment
> Scope: Відомі прогалини розгортання та пріоритизований план усунення

---

## Контекст

Цей документ фіксує дельту між **поточним розгорнутим станом** (2026-02-25) та **production-ready станом** BLOOM Runtime.

Базовий стан: [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]]

---

## Критичні прогалини

### GAP-1: Відсутність персистентного сховища — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit commit `150b491`

**Опис рішення:**
- Клас `DatabaseStorage` у `server/storage.ts` (Drizzle ORM + PostgreSQL)
- Замінює `MemStorage` — той самий інтерфейс `IStorage`
- Всі сутності персистовані: tasks, leases, artifacts, results, audit, config

**Деталі:** [[RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]]

---

### GAP-2: Відсутність аутентифікації Runtime API — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit commit `150b491`

**Опис рішення:**
- `server/middleware/runtimeAuth.ts` — заголовок `X-Runtime-API-Key`, timing-safe порівняння
- Застосовано до всіх `/api/runtime/*` маршрутів
- Ключ з env var `RUNTIME_API_KEY`; якщо не встановлено — auth вимкнено (dev mode)
- Незахищені маршрути: `/api/runtime/health`, `/api/runtime/test-connection`

---

### GAP-3: Rate Limiting не налаштований — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit implementation

**Опис рішення:**
- `express-rate-limit` middleware додано до `server/routes.ts`
- Загальний ліміт: 100 req/хв на `/api/runtime/*` і `/api/membridge/*`
- Суворий ліміт: 20 req/хв на `POST /api/runtime/test-connection`
- Стандартні `RateLimit-*` заголовки у відповідях
- JSON повідомлення при перевищенні ліміту

---

### GAP-4: Workers не зареєстровані — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit implementation

**Опис рішення:**
- Додано `POST /api/runtime/workers` — пряма реєстрація worker через Runtime API
- Додано `DELETE /api/runtime/workers/:id` — видалення worker
- Zod-валідація через `registerWorkerSchema` у `shared/schema.ts`
- Upsert семантика: повторний POST оновлює існуючий worker
- Audit log для кожної реєстрації/видалення
- Auto-sync з Membridge `/agents` (кожні 10с) як додаткове джерело workers

**Реєстрація:**

```http
POST /api/runtime/workers
Content-Type: application/json

{
  "name": "worker-01",
  "status": "online",
  "capabilities": {
    "claude_cli": true,
    "max_concurrency": 2,
    "labels": ["production"]
  }
}
```

---

### GAP-5: Відсутність TLS / HTTPS — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit implementation

**Опис рішення:**
- HTTPS redirect middleware у `server/routes.ts`: перевірка `X-Forwarded-Proto` → redirect 301 на HTTPS
- `app.set("trust proxy", 1)` для коректної роботи за reverse proxy
- Активується тільки в `NODE_ENV=production`
- На Replit: TLS забезпечується платформою автоматично (.replit.app домен)
- На Alpine/VPS: certbot + nginx конфігурація (документовано нижче)

**Для self-hosted (Alpine/VPS):**

```nginx
server {
    listen 443 ssl;
    ssl_certificate     /etc/letsencrypt/live/<domain>/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/<domain>/privkey.pem;
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

### GAP-6: Артефакти підключені до MinIO — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit implementation

**Опис рішення:**
- `server/runtime/minioArtifacts.ts` — MinIO клієнт для артефактів
- При `POST .../complete`: якщо MinIO налаштований → upload content до `bloom-artifacts` bucket → зберігає `minio://` URL в `artifact.url`, content=null
- Якщо MinIO не налаштований → graceful fallback на PostgreSQL (content зберігається в таблиці)
- Автоматичне створення bucket якщо не існує
- Функції: `uploadArtifactToMinio()`, `downloadArtifactFromMinio()`, `getMinioArtifactUrl()` (presigned)

**Env vars для MinIO артефактів:**
- `MINIO_ENDPOINT` — хост MinIO (напр. `minio.example.com`)
- `MINIO_PORT` — порт (default: 9000)
- `MINIO_ACCESS_KEY` — access key
- `MINIO_SECRET_KEY` — secret key
- `MINIO_ARTIFACT_BUCKET` — bucket name (default: `bloom-artifacts`)
- `MINIO_USE_SSL` — `true` для HTTPS (default: false)

---

### GAP-7: Membridge Control Plane UI не інтегрований — ✅ ВИРІШЕНО (2026-02-25)

**Вирішено у:** Replit implementation

**Опис рішення:**
1. Proxy-маршрути `/api/membridge/*` у `server/routes.ts` через `membridgeFetch()`
2. `MembridgePage.tsx` — список проєктів, лідерство, ноди, промоція primary
3. Навігаційна панель у `App.tsx` з вкладками Runtime / Membridge
4. Admin key інжектується бекендом — фронтенд ніколи не бачить ключ
5. Audit log для операцій промоції

**Деталі:** [[REPLIT_MEMBRIDGE_UI_INTEGRATION.md]]

---

## Рекомендовані наступні кроки

Пріоритет на основі: розблокування виконання > безпека > спостережуваність.

### ~~Пріоритет 1 — Persistence Layer~~ ✅ Виконано (2026-02-25)

Вирішено в Replit commit `150b491`. Див. [[RUNTIME_BACKEND_IMPLEMENTATION_STATE.md]].

---

### ~~Пріоритет 2 — Auth Hardening~~ ✅ Виконано (2026-02-25)

`runtimeAuthMiddleware` через `X-RUNTIME-API-KEY`. Вирішено в Replit commit `150b491`.

---

### ~~Пріоритет 3 — Інтеграція UI Membridge~~ ✅ Виконано (2026-02-25)

Proxy-маршрути, MembridgePage, навігація. Див. [[REPLIT_MEMBRIDGE_UI_INTEGRATION.md]].

---

### Пріоритет 1 — Реєстрація Worker (розблокування виконання)

**Зусилля:** 1–2 години (операційне)
**Розблоковує:** Кроки 4–8 у конвеєрі виконання; повний end-to-end тест

1. Розгорнути Claude CLI агент на будь-якій машині з мережевим доступом до `:8000`
2. Налаштувати реєстрацію агента в Membridge з `MEMBRIDGE_ADMIN_KEY`
3. Перевірити: `GET /api/runtime/workers` повертає worker зі `status: "online"`
4. Тест повного pipeline: create task → lease → heartbeat → complete → artifact

Не потребує змін коду.

---

### Пріоритет 2 — Rate Limiting (GAP-3)

**Зусилля:** 15 хвилин
**Розблоковує:** Захист від DoS

```typescript
import rateLimit from 'express-rate-limit';

const apiLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 100,
  message: { error: 'Too many requests' }
});
app.use('/api/runtime/', apiLimiter);
app.use('/api/membridge/', apiLimiter);
```

`express-rate-limit` вже є в `dependencies`.

---

### Пріоритет 3 — Покращення спостережуваності

**Зусилля:** 1–3 дні
**Розблоковує:** Моніторинг production, реагування на інциденти

Під-задачі (незалежні):

**3a. Ротація логів**
```bash
# /etc/logrotate.d/bloom-runtime
/var/log/bloom-runtime*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    postrotate
        rc-service bloom-runtime restart
    endscript
}
```

**3b. Персистентний audit log до MinIO**
Періодичний flush `auditLogs[]` до MinIO як JSONL файл.

**3c. Endpoint метрик**
Prometheus-сумісний `/metrics` для кількості workers, throughput завдань, тривалості leases.

**3d. TLS (GAP-5)**
HTTPS сертифікат через certbot.

---

## Зведена матриця прогалин

| Прогалина | ID | Серйозність | Статус | Зусилля | Розблоковує |
|-----------|----|-------------|--------|---------|-------------|
| Persistence layer | GAP-1 | Критична | ✅ **ВИРІШЕНО** | — | — |
| API auth | GAP-2 | Критична | ✅ **ВИРІШЕНО** | — | — |
| Rate limiting | GAP-3 | Висока | ✅ **ВИРІШЕНО** | — | — |
| Workers не зареєстровані | GAP-4 | Висока | ✅ **ВИРІШЕНО** | — | — |
| Відсутність TLS | GAP-5 | Середня | ✅ **ВИРІШЕНО** | — | — |
| Артефакти не в MinIO | GAP-6 | Середня | ✅ **ВИРІШЕНО** | — | — |
| Membridge UI не інтегр. | GAP-7 | Середня | ✅ **ВИРІШЕНО** | — | — |

---

## Діаграма пріоритетів

```
                   ┌───────────────────────┐
                   │  BLOOM Runtime        │
                   │  Production Readiness │
                   └───────────┬───────────┘
                               │
          ┌────────────────────┐
          ▼                    │
   ✅ ВСІ ПРОГАЛИНИ ВИРІШЕНО  │
   ┌─────────────────────┐    │
   │ GAP-1 DB             │   │
   │ GAP-2 Auth           │   │
   │ GAP-3 Rate Limiting  │   │
   │ GAP-4 Worker Reg     │   │
   │ GAP-5 TLS/HTTPS      │   │
   │ GAP-6 MinIO Artifacts│   │
   │ GAP-7 UI             │   │
   └─────────────────────┘    │
   Production Ready ──────────┘
```

---

## Семантичні зв'язки

**Цей документ залежить від:**
- [[RUNTIME_DEPLOYMENT_STATE_ALPINE.md]] — базовий стан розгортання
- [[RUNTIME_EXECUTION_PATH_VERIFICATION.md]] — які кроки live vs blocked

**На цей документ посилаються:**
- [[../../ІНДЕКС.md]] — головний індекс
