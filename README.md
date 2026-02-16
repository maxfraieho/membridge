# membridge

Синхронізація SQLite бази [claude-mem](https://github.com/thedotmack/claude-mem) між машинами через MinIO (S3-сумісне сховище).

## Що це робить

- **Push**: створює VACUUM-копію `claude-mem.db`, перевіряє integrity, завантажує в MinIO з SHA256 контрольною сумою
- **Pull**: завантажує DB з MinIO, верифікує SHA256, атомарно замінює локальну копію, перезапускає worker
- **Lock**: distributed lock на рівні MinIO (один writer одночасно, TTL-based)
- **canonical_project_id**: SHA256-хеш від `CLAUDE_PROJECT_ID` — не залежить від абсолютного шляху на файловій системі

## Передумови

- [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) встановлений
- [claude-mem](https://github.com/thedotmack/claude-mem) плагін встановлений (`claude mcp add ...`)
- Python 3 + pip
- Доступ до MinIO/S3-сумісного endpoint з створеним bucket

## Встановлення (нова машина)

```bash
# 1. Клонувати репо
git clone git@github.com:maxfraieho/membridge.git
cd membridge

# 2. Створити virtualenv та встановити залежності
python3 -m venv venv
source venv/bin/activate
pip install boto3

# 3. Створити конфігурацію
cp config.env.example config.env
# Відредагувати config.env — вказати реальні ключі MinIO:
#   MINIO_ENDPOINT=https://your-minio.example.com
#   MINIO_ACCESS_KEY=your-key
#   MINIO_SECRET_KEY=your-secret
#   CLAUDE_MEM_DB=/home/YOUR_USER/.claude-mem/claude-mem.db

# 4. Перевірити конфігурацію
source venv/bin/activate
set -a; source config.env; set +a
python sqlite_minio_sync.py print_project
```

Очікуваний вивід:
```
project_name: mem
canonical_project_id: 21c2e59531c8c9ee
```

> **Важливо**: `canonical_project_id` має бути однаковим на всіх машинах. Він обчислюється як `sha256("mem")[:16]`. Якщо ID не збігається — перевірте `CLAUDE_PROJECT_ID` в `config.env`.

## Налаштування на PRIMARY машині (writer)

PRIMARY — машина, де ведеться основна робота з claude-mem. Вона робить push.

```bash
# Переконатися, що DB існує
ls -la ~/.claude-mem/claude-mem.db
# Типовий розмір: ~2.4MB

# Перший push
source venv/bin/activate
set -a; source config.env; set +a
python sqlite_minio_sync.py push_sqlite
```

## Налаштування на SECONDARY машині (reader/writer)

SECONDARY — додаткова машина, яка синхронізує DB з MinIO перед сесією.

```bash
# 1. Встановити claude-mem плагін (якщо ще не встановлений)
# Дивіться: https://github.com/thedotmack/claude-mem

# 2. Ініціалізувати DB — запустити одну сесію claude, щоб claude-mem створив базу
claude

# 3. Pull з MinIO
source venv/bin/activate
set -a; source config.env; set +a
python sqlite_minio_sync.py pull_sqlite
```

## Встановлення hooks (автоматична синхронізація)

Hooks дозволяють автоматично робити pull при старті сесії та push при завершенні.

### 1. Скопіювати hooks

```bash
mkdir -p ~/.claude-mem-minio/bin
cp hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*
```

Якщо membridge встановлений не в `/home/vokov/projects/mem`, встановіть змінну `MEMBRIDGE_DIR`:

```bash
export MEMBRIDGE_DIR=/path/to/membridge
```

Або відредагуйте дефолтний шлях у кожному hook-скрипті.

### 2. Налаштувати Claude CLI settings

Додати в `~/.claude/settings.json`:

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -lc 'export BUN_INSTALL=\"$HOME/.bun\"; export PATH=\"$BUN_INSTALL/bin:$HOME/npm-global/bin:$PATH\"; ~/.claude-mem-minio/bin/claude-mem-hook-pull'",
            "timeout": 60
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "bash -lc 'export BUN_INSTALL=\"$HOME/.bun\"; export PATH=\"$BUN_INSTALL/bin:$HOME/npm-global/bin:$PATH\"; ~/.claude-mem-minio/bin/claude-mem-hook-push'",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```

### 3. Fail-open поведінка

Hook-скрипти (`hook-pull`, `hook-push`) завжди завершуються з `exit 0`, навіть якщо sync не вдався. Це гарантує, що Claude CLI сесія запуститься/завершиться нормально. Помилки логуються в `~/.claude-mem-minio/hook.log`.

## Команди

| Команда | Опис |
|---|---|
| `python sqlite_minio_sync.py print_project` | Показати project name і canonical_id |
| `python sqlite_minio_sync.py doctor` | Повна діагностика: MinIO, lock, DB, worker, hooks |
| `python sqlite_minio_sync.py pull_sqlite` | Завантажити DB з MinIO → замінити локальну |
| `python sqlite_minio_sync.py push_sqlite` | Створити snapshot → завантажити в MinIO |

Або через wrapper-скрипти з `hooks/`:

```bash
~/.claude-mem-minio/bin/claude-mem-pull
~/.claude-mem-minio/bin/claude-mem-push
~/.claude-mem-minio/bin/claude-mem-doctor
~/.claude-mem-minio/bin/claude-mem-status
```

## Безпека

- **НІКОЛИ** не комітьте `config.env` — він містить ключі MinIO
- **НІКОЛИ** не комітьте `*.db` файли — вони містять всю пам'ять claude-mem
- `.gitignore` вже налаштований для захисту від випадкового коміту
- Lock з TTL (за замовчуванням 7200 секунд / 2 години) — захист від одночасного push з двох машин
- `FORCE_PUSH=1` — для аварійного override lock
- Рекомендується: один активний Claude CLI одночасно (щоб уникнути конфліктів DB)

## Troubleshooting

### Bucket not found

```
ERROR: bucket "claude-memory" not found
```

Створіть bucket в MinIO консолі або через `mc`:
```bash
mc mb myminio/claude-memory
```

### canonical_id mismatch (різний ID на машинах)

Переконайтеся, що `CLAUDE_PROJECT_ID=mem` однаковий в `config.env` на обох машинах. canonical_id обчислюється як:

```python
hashlib.sha256("mem".encode()).hexdigest()[:16]
# → "21c2e59531c8c9ee"
```

### Worker locking DB

Якщо після pull DB повертається до старої версії — worker перезаписує її. Скрипт автоматично зупиняє worker перед заміною та перезапускає після. Якщо проблема зберігається:

```bash
# Зупинити worker вручну
kill $(cat ~/.claude-mem/worker.pid | python3 -c "import sys,json; print(json.load(sys.stdin)['pid'])")
```

### MinIO auth errors

```
ERROR: Access Denied
```

Перевірте:
1. `MINIO_ACCESS_KEY` і `MINIO_SECRET_KEY` в `config.env`
2. Що bucket `claude-memory` існує і доступний для цього користувача
3. Що endpoint URL правильний (https)

### Lock active — не вдається push

```
LOCK ACTIVE — held by orangepi for 1234s
```

Lock тримається іншою машиною. Дочекайтеся TTL або:
```bash
FORCE_PUSH=1 python sqlite_minio_sync.py push_sqlite
```

## Структура в MinIO

```
claude-memory/
  projects/
    21c2e59531c8c9ee/          # canonical_project_id
      sqlite/
        claude-mem.db           # SQLite snapshot (~2.4MB)
        claude-mem.db.sha256    # SHA256 checksum
        manifest.json           # metadata (host, timestamp, counts)
      locks/
        active.lock             # distributed lock file
```

## Performance Optimization

This repository includes performance optimization scripts for low-RAM ARM devices (Raspberry Pi, Orange Pi).

### Files

| File | Purpose |
|------|---------|
| `optimization-profile-orange.sh` | Applies sysctl, zram, swap, and memory tuning |
| `scripts/claude-cleanup-safe` | Docker-safe cleanup of orphan Claude, MCP, bun, and chroma processes |

### Usage

```bash
# Apply system optimizations (requires root)
sudo bash optimization-profile-orange.sh apply

# Check current optimization status
sudo bash optimization-profile-orange.sh status

# Revert all optimizations
sudo bash optimization-profile-orange.sh revert

# Preview process cleanup (dry run)
scripts/claude-cleanup-safe

# Kill orphan processes (Docker-safe)
scripts/claude-cleanup-safe --kill
```

These optimizations significantly improve Claude CLI performance on ARM devices with limited RAM (1-2GB).

## Ліцензія

MIT
