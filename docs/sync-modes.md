# Sync Modes

Membridge supports two sync operations: **pull** and **push**, each with different
behavior depending on the node's **leadership role** (primary or secondary).

---

## Push

**Purpose:** Upload the local SQLite DB snapshot to MinIO (makes it the canonical remote copy).

### Primary push (allowed)

1. Check leadership role → primary ✅
2. Stop worker (for consistent snapshot)
3. `VACUUM INTO` temp snapshot + integrity check
4. Restart worker (independent of upload)
5. Compute SHA256 of snapshot
6. Compare with remote SHA256 (skip if identical)
7. Acquire distributed push lock
8. Upload DB + SHA256 + manifest to MinIO
9. Verify remote SHA256

### Secondary push (blocked)

```
[0/6] Leadership: role=secondary  node=mynode  primary=rpi4b
  SECONDARY: push blocked by default.
  Options:
    - Request promotion: POST /projects/<cid>/leadership/select
    - Override (unsafe): ALLOW_SECONDARY_PUSH=1
```

Exit code 3.

### Env vars affecting push

| Var | Default | Effect |
|-----|---------|--------|
| `ALLOW_SECONDARY_PUSH` | `0` | Allow secondary to push (unsafe) |
| `FORCE_PUSH` | `0` | Override active push lock |
| `LOCK_TTL_SECONDS` | `7200` | Push lock TTL |
| `STALE_LOCK_GRACE_SECONDS` | `60` | Grace period after lock expiry |
| `LEADERSHIP_ENABLED` | `1` | Disable all leadership checks if `0` |

---

## Pull

**Purpose:** Download the canonical DB from MinIO and replace the local copy.

### Secondary pull (allowed, with backup)

1. Check leadership role → secondary ✅
2. Download remote SHA256
3. Compare with local (skip if identical)
4. Download remote DB to temp file
5. Verify SHA256 of download
6. **Safety backup** of current local DB to `~/.claude-mem/backups/pull-overwrite/<ts>/`
7. Stop worker
8. Atomic replace local DB
9. Verify DB integrity + restart worker

### Primary pull (refused if local DB exists)

```
  SHA256 mismatch — pulling remote DB
  [leadership] role=primary  node=rpi4b  primary=rpi4b
  PRIMARY: refusing destructive pull overwrite of local DB.
    local_sha:  abc123...
    remote_sha: def456...
  Primary is the single source of truth — remote drift must be resolved manually.
  Options:
    - Inspect: download remote DB to a temp path and compare
    - Override (unsafe): ALLOW_PRIMARY_PULL_OVERRIDE=1
    - Handover: POST /projects/<cid>/leadership/select
```

Exit code 2.

**Exception:** If the local DB does not yet exist (first-time setup), the primary
can pull freely — there is nothing to protect.

### Env vars affecting pull

| Var | Default | Effect |
|-----|---------|--------|
| `ALLOW_PRIMARY_PULL_OVERRIDE` | `0` | Allow primary to pull-overwrite (unsafe) |
| `PULL_BACKUP_MAX_DAYS` | `14` | Delete backups older than N days |
| `PULL_BACKUP_MAX_COUNT` | `50` | Keep at most N pull backups |
| `MEMBRIDGE_NO_RESTART_WORKER` | `0` | Skip worker restart after pull |
| `LEADERSHIP_ENABLED` | `1` | Disable all leadership checks if `0` |

---

## SAFE-PULL Backups

Before every pull overwrite, the current local DB is backed up to:
```
~/.claude-mem/backups/pull-overwrite/<YYYYMMDD-HHMMSS>/
  claude-mem.db        # full copy of local DB before overwrite
  chroma.sqlite3       # vector DB (if present)
  manifest.json        # metadata: timestamps, SHAs, obs counts, local_ahead flag
```

Backups are retained for `PULL_BACKUP_MAX_DAYS` days and at most `PULL_BACKUP_MAX_COUNT` snapshots.

To restore from backup:
```bash
cp ~/.claude-mem/backups/pull-overwrite/<ts>/claude-mem.db ~/.claude-mem/claude-mem.db
```

---

## Write-Local Policy

Both primary and secondary nodes can write to the local SQLite DB at any time
(the worker and Claude CLI do this). This is intentional — local writes are always
allowed. The leadership gates only control **MinIO sync** (pull/push).

When a secondary has local writes not yet pushed:
- `cm-doctor` will show `local_ahead: YES`
- The secondary cannot push (blocked)
- To preserve secondary-only data: promote secondary to primary first

---

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success (or already up-to-date) |
| 1 | Error (MinIO, DB, config, etc.) |
| 2 | Primary pull refused (role gate) |
| 3 | Secondary push blocked (role gate) |
