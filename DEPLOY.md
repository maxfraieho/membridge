# Розгортання membridge

## Нова машина з нуля

```bash
# 1. Клонувати репо
git clone git@github.com:maxfraieho/membridge.git ~/projects/mem
cd ~/projects/mem

# 2. Python venv + boto3
python3 -m venv venv
source venv/bin/activate
pip install boto3

# 3. Конфігурація (секрети — НЕ в git)
mkdir -p ~/.claude-mem-minio/bin
cp config.env.example ~/.claude-mem-minio/config.env
nano ~/.claude-mem-minio/config.env   # заповнити реальні ключі MinIO
ln -sf ~/.claude-mem-minio/config.env config.env

# 4. Встановити hook-скрипти
cp hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*

# 5. Claude CLI hooks
# Додати в ~/.claude/settings.json:
cat <<'EOF'
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/USER/.claude-mem-minio/bin/claude-mem-hook-pull"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/home/USER/.claude-mem-minio/bin/claude-mem-hook-push"
          }
        ]
      }
    ]
  }
}
EOF
# Замінити USER на свого користувача

# 6. Перевірка
~/.claude-mem-minio/bin/claude-mem-doctor

# 7. Перший sync (pull з MinIO або push локальної DB)
~/.claude-mem-minio/bin/claude-mem-pull   # якщо DB вже є на MinIO
# або
~/.claude-mem-minio/bin/claude-mem-push   # якщо ця машина — master
```

## Оновлення існуючої машини (deploy нових фіч)

Коли в репо з'являються нові зміни (новий sync скрипт, нові hooks, тощо):

```bash
cd ~/projects/mem

# 1. Підтягнути зміни
git pull origin main

# 2. Оновити залежності (якщо змінились)
source venv/bin/activate
pip install -r requirements.txt 2>/dev/null || pip install boto3

# 3. Перевстановити hook-скрипти (вони живуть у ~/.claude-mem-minio/bin/)
cp hooks/* ~/.claude-mem-minio/bin/
chmod +x ~/.claude-mem-minio/bin/*

# 4. Перевірити що все працює
~/.claude-mem-minio/bin/claude-mem-doctor

# 5. Тестовий push/pull
~/.claude-mem-minio/bin/claude-mem-push
~/.claude-mem-minio/bin/claude-mem-status
```

**Що НЕ треба робити при оновленні:**
- Не чіпати `~/.claude-mem-minio/config.env` (секрети лишаються)
- Не чіпати `~/.claude-mem/claude-mem.db` (master DB лишається)
- Не змінювати `~/.claude/settings.json` (якщо hooks вже налаштовані)

## Production hardening (що вже зроблено)

### Автоматичний backup перед push

Hook-push створює копію DB перед кожним push:

```
~/.claude-mem-backups/claude-mem-YYYYMMDD-HHMMSS.db
```

Очищення старих backups (ручне, за потреби):

```bash
# Видалити backups старше 30 днів
find ~/.claude-mem-backups -name "*.db" -mtime +30 -delete
```

### Shell aliases

В `~/.bashrc` додані alias-команди:

```bash
cm-push        # Push local DB -> MinIO
cm-pull        # Pull MinIO -> local DB
cm-status      # Project identity + doctor
cm-doctor      # Повна діагностика
```

Після додавання: `source ~/.bashrc`

### Same-host lock re-acquisition

Lock system дозволяє повторний push з того ж хоста без FORCE_PUSH.
Це критично для послідовних сесій з інтервалом менше TTL (2 години).

## Структура файлів

```
~/projects/mem/                     # git repo (код)
  sqlite_minio_sync.py             # основний sync скрипт
  hooks/                           # шаблони hook-скриптів
  config.env -> ~/.claude-mem-minio/config.env  # symlink
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

~/.claude-mem/                     # claude-mem data (не в git)
  claude-mem.db                    # master SQLite DB

~/.claude-mem-backups/             # автоматичні backups (не в git)

~/.claude/settings.json            # Claude CLI hooks config
```

## Порядок роботи з двома машинами

1. Одночасно активна **тільки одна машина**
2. Перед переходом на іншу машину — `cm-push` з поточної
3. На новій машині — `cm-pull` (або автоматично через SessionStart hook)
4. Lock захищає від випадкового одночасного push (TTL = 2 години)
5. `FORCE_PUSH=1 cm-push` — для аварійного override
