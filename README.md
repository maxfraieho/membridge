# membridge

Синхронізація SQLite бази [claude-mem](https://github.com/thedotmack/claude-mem) між машинами через MinIO (S3-сумісне сховище).

## Що це робить

- **Push**: VACUUM-копія `claude-mem.db` → SHA256 → завантаження в MinIO
- **Pull**: завантаження з MinIO → верифікація SHA256 → атомарна заміна локальної DB → перезапуск worker
- **Lock**: distributed lock на рівні MinIO (один writer, TTL = 2 години)
- **Hooks**: автоматичний pull при старті сесії Claude CLI, push при завершенні
- **Backup**: автоматична копія DB перед кожним push

## Передумови

- [Claude CLI](https://docs.anthropic.com/en/docs/claude-cli) встановлений
- [claude-mem](https://github.com/thedotmack/claude-mem) плагін встановлений (`claude mcp add ...`)
- Python 3 + pip
- Доступ до MinIO/S3-сумісного endpoint з bucket `claude-memory`

## Розгортання на новій машині

```bash
# 1. Клонувати репо
git clone git@github.com:maxfraieho/membridge.git ~/membridge
cd ~/membridge

# 2. Python venv + boto3
python3 -m venv venv
source venv/bin/activate
pip install boto3

# 3. Створити директорії
mkdir -p ~/.claude-mem-minio/bin ~/.claude-mem-backups

# 4. Конфігурація (секрети — НЕ в git)
cp config.env.example ~/.claude-mem-minio/config.env
nano ~/.claude-mem-minio/config.env   # заповнити реальні ключі MinIO
ln -sf ~/.claude-mem-minio/config.env config.env

# 5. Встановити hook-скрипти
cp hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*

# 6. Claude CLI hooks — додати в ~/.claude/settings.json:
```

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

```bash
# 7. Shell aliases (додати в ~/.bashrc або ~/.zshrc)
cat >> ~/.zshrc << 'ALIASES'

# membridge aliases
alias cm-push="~/.claude-mem-minio/bin/claude-mem-push"
alias cm-pull="~/.claude-mem-minio/bin/claude-mem-pull"
alias cm-status="~/.claude-mem-minio/bin/claude-mem-status"
alias cm-doctor="~/.claude-mem-minio/bin/claude-mem-doctor"
ALIASES
source ~/.zshrc

# 8. Перевірка
~/.claude-mem-minio/bin/claude-mem-doctor

# 9. Перший sync
cm-pull    # якщо DB вже є на MinIO (на іншій машині вже робили push)
# або
cm-push    # якщо ця машина — перша і DB вже є локально
```

## Оновлення існуючої машини

```bash
cd ~/membridge
git pull origin main

# Перевстановити hook-скрипти
cp hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*

# Оновити залежності
source venv/bin/activate
pip install boto3

# Перевірити
cm-doctor
```

**Не чіпати при оновленні:** `~/.claude-mem-minio/config.env`, `~/.claude-mem/claude-mem.db`, `~/.claude/settings.json`.

## Команди

| Команда | Опис |
|---|---|
| `cm-push` | Push локальної DB → MinIO |
| `cm-pull` | Pull MinIO → локальна DB |
| `cm-doctor` | Повна діагностика (MinIO, lock, DB, worker, hooks) |
| `cm-status` | Project identity + статус |

Або напряму через Python:

```bash
source venv/bin/activate && set -a && source config.env && set +a
python sqlite_minio_sync.py push_sqlite
python sqlite_minio_sync.py pull_sqlite
python sqlite_minio_sync.py doctor
python sqlite_minio_sync.py print_project
```

## Порядок роботи з кількома машинами

1. Одночасно активна **тільки одна машина**
2. Перед переходом на іншу — `cm-push` з поточної
3. На новій машині — `cm-pull` (або автоматично через SessionStart hook)
4. Lock захищає від одночасного push (TTL = 2 години)
5. `FORCE_PUSH=1 cm-push` — аварійний override lock

## Структура файлів

```
~/membridge/                         # git repo
  sqlite_minio_sync.py             # основний sync скрипт
  hooks/                           # шаблони hook-скриптів
  config.env.example               # приклад конфігурації
  config.env -> ~/.claude-mem-minio/config.env  # symlink (не в git)
  venv/                            # Python virtualenv (не в git)

~/.claude-mem-minio/               # runtime (не в git)
  config.env                       # секрети MinIO
  bin/                             # робочі hook-скрипти
    claude-mem-hook-pull            # SessionStart hook
    claude-mem-hook-push            # Stop hook (з backup)
    claude-mem-push                 # ручний push
    claude-mem-pull                 # ручний pull
    claude-mem-status               # статус
    claude-mem-doctor               # діагностика
  hook.log                         # лог хуків

~/.claude-mem/claude-mem.db        # master SQLite DB (не в git)
~/.claude-mem-backups/             # автоматичні backups (не в git)
~/.claude/settings.json            # Claude CLI hooks config
```

## Структура в MinIO

```
claude-memory/
  projects/
    6fe2e0f6071ac2bb/              # canonical_project_id = sha256("mem")[:16]
      sqlite/
        claude-mem.db              # SQLite snapshot
        claude-mem.db.sha256       # SHA256 checksum
        manifest.json              # metadata (host, timestamp, counts)
      locks/
        active.lock                # distributed lock
```

## Troubleshooting

**Lock active — не вдається push:**
```
LOCK ACTIVE — held by orangepi for 1234s
```
Дочекайтеся TTL або: `FORCE_PUSH=1 cm-push`

**canonical_id mismatch:** переконайтесь що `CLAUDE_PROJECT_ID=mem` однаковий в `config.env` на всіх машинах.

**Worker locking DB:** скрипт автоматично зупиняє/перезапускає worker. Якщо проблема — `kill $(cat ~/.claude-mem/worker.pid | python3 -c "import sys,json; print(json.load(sys.stdin)['pid'])")`

**MinIO auth errors:** перевірте ключі в `config.env`, існування bucket, правильність endpoint URL.

## Безпека

- **НІКОЛИ** не комітьте `config.env` — містить ключі MinIO
- **НІКОЛИ** не комітьте `*.db` — містить всю пам'ять claude-mem
- `.gitignore` захищає від випадкового коміту
- Same-host lock re-acquisition: повторний push з того ж хоста без FORCE_PUSH

## Performance Optimization

Скрипти оптимізації для ARM-пристроїв з малим обсягом RAM (Raspberry Pi, Orange Pi).

| Файл | Призначення |
|------|-------------|
| `optimization-profile-orange.sh` | sysctl, zram, swap, memory tuning |
| `scripts/claude-cleanup-safe` | Docker-safe cleanup orphan процесів Claude, MCP, bun, chroma |

```bash
# Застосувати оптимізації (потрібен root)
sudo bash optimization-profile-orange.sh apply

# Перевірити статус
sudo bash optimization-profile-orange.sh status

# Відкатити оптимізації
sudo bash optimization-profile-orange.sh revert

# Попередній перегляд процесів (dry run)
scripts/claude-cleanup-safe

# Зупинити orphan процеси (Docker-safe)
scripts/claude-cleanup-safe --kill
```

## Claude Config Sync (no-auth)

Source of truth: Raspberry Pi 3B `~/.claude` (sanitized, no credentials).

The `config/claude/` directory contains portable Claude CLI configuration:
- `settings.json` — hooks for membridge sync (SessionStart pull, Stop push)
- `hooks/` — session cleanup, context drift detection, execution validation

### Deploy on Linux (RPi / Orange Pi / Ubuntu / Debian)

```bash
cd ~/membridge && git pull && bash scripts/bootstrap-linux.sh
```

### Deploy on Alpine x86_64

```bash
cd ~/membridge && git pull && bash scripts/bootstrap-alpine.sh
```

### Deploy on Windows 10

```powershell
cd ~\membridge; git pull
powershell -ExecutionPolicy Bypass -File scripts\bootstrap-windows.ps1
```

**Auth is NOT synced** — tokens and credentials stay local on each machine.

## Full Deployment Guide

For complete step-by-step instructions to reproduce this environment on a new machine — including system prerequisites, Claude CLI installation, claude-mem plugin setup, MinIO sync configuration, hook integration, ARM performance optimization, multi-machine sync model, and recovery procedures — see:

**[DEPLOYMENT.md](DEPLOYMENT.md)**

## Ліцензія

MIT
