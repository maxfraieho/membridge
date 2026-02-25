# Session: membridge sqlite_minio_sync → Go rewrite
Date: 2026-02-25
From: ARM (Orange Pi / aarch64)
Continue on: x86 Alpine

## Мета
Переписати `sqlite_minio_sync.py` на Go для:
- Мінімального RAM/CPU на ARM
- Статичний нативний бінарник (no Python runtime)
- Alpine-compatible (musl / CGO-free)

## Рішення
**Go** з такими пакетами:
- `github.com/minio/minio-go/v7` — MinIO/S3 SDK (офіційний)
- `modernc.org/sqlite` — pure-Go SQLite, без CGO, cross-compile ready
- stdlib: `crypto/sha256`, `os/signal`, `encoding/json`, `net/http`

## Чому НЕ Codon
Codon дає 0 виграшу для I/O-bound сервісів з boto3/sqlite3 (C extensions)

## Що реалізувати (`cmd/sync/main.go`)

### Env vars (всі з sqlite_minio_sync.py)
```
MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, MINIO_BUCKET
CLAUDE_PROJECT_ID, CLAUDE_MEM_DB, MINIO_REGION (default: us-east-1)
LOCK_TTL_SECONDS (7200), FORCE_PUSH (0), STALE_LOCK_GRACE_SECONDS (60)
PULL_BACKUP_MAX_DAYS (14), PULL_BACKUP_MAX_COUNT (50)
MEMBRIDGE_NODE_ID (hostname), PRIMARY_NODE_ID
ALLOW_SECONDARY_PUSH (0), ALLOW_PRIMARY_PULL_OVERRIDE (0)
LEADERSHIP_ENABLED (1), LEADERSHIP_LEASE_SECONDS (3600)
MEMBRIDGE_NO_RESTART_WORKER (0)
```

### Функції для портування
1. `loadConfig()` — validate required env vars, exit(1) if missing
2. `sha256File(path)` → string
3. `resolveCanonicalID(cfg)` → sha256(project_name)[:16]
4. `newMinioClient(cfg)` → *minio.Client
5. `getLockKey(canonicalID)` → string
6. `getLockStatus(client, cfg)` → (exists bool, lockData LockData, ageSeconds int)
7. `acquireLock(client, cfg)` → bool
8. `releaseLock(client, cfg)`
9. `pushDB(client, cfg)` — SHA256 check, upload, update manifest
10. `pullDB(client, cfg)` — download, backup rotation, replace local
11. `leadershipCheck(client, cfg)` — primary/secondary logic
12. `workerLoop(cfg, cmd string)` — push|pull|sync dispatch
13. `startWorker()` — daemonize, signal handling

### Структура
```
membridge/
  cmd/
    sync/
      main.go        ← точка входу
  internal/
    config/
      config.go      ← loadConfig, env parsing
    lock/
      lock.go        ← distributed lock logic
    storage/
      minio.go       ← MinIO operations
      sqlite.go      ← local SQLite backup/restore
    leadership/
      leadership.go  ← primary/secondary election
```

## Оригінал
`/home/vokov/membridge/sqlite_minio_sync.py` — повний Python код

## Наступні кроки
```bash
cd /home/vokov/membridge
go mod init github.com/vokov/membridge
go get github.com/minio/minio-go/v7
go get modernc.org/sqlite
# потім реалізація пакетів
```

## Build для Alpine (static)
```bash
CGO_ENABLED=0 GOOS=linux GOARCH=amd64 \
  go build -ldflags="-s -w -extldflags=-static" \
  -o dist/membridge-sync ./cmd/sync
```

## claude-mem memory ID
observation #621 (project: membridge)
