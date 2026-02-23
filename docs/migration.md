# Migration Guide: Upgrading to Primary/Secondary Leadership

This guide covers migrating from pre-leadership Membridge (≤ v0.3.x) to the
Primary/Secondary model introduced in v0.4.0.

---

## What Changed

| Area | Before | After |
|------|--------|-------|
| Push | Any node can push | Only primary can push (secondary blocked) |
| Pull | Any node can pull-overwrite | Primary refuses pull-overwrite; secondary pulls with backup |
| Config | No role concept | `PRIMARY_NODE_ID` env var or lease in MinIO |
| MinIO layout | `projects/<cid>/sqlite/` | + `projects/<cid>/leadership/` |

---

## Migration Steps

### Step 1: Identify your primary node

The primary is the node with the most up-to-date DB (most observations, most recent push).

```bash
# On each node, check obs count:
python3 sqlite_minio_sync.py doctor   # shows [4/5] SQLite DB health → observations
```

### Step 2: Set PRIMARY_NODE_ID on the primary node

```bash
# In ~/.claude-mem-minio/config.env on the primary node:
echo "PRIMARY_NODE_ID=$(hostname)" >> ~/.claude-mem-minio/config.env
```

### Step 3: Bootstrap the leadership lease

```bash
# On the primary node:
python3 sqlite_minio_sync.py leadership_info
```

This creates `projects/<canonical_id>/leadership/lease.json` in MinIO.

### Step 4: Push from primary to establish canonical state

```bash
cm-push   # or: python3 sqlite_minio_sync.py push_sqlite
```

### Step 5: Pull on all secondary nodes

```bash
# On each secondary node:
cm-pull   # or: python3 sqlite_minio_sync.py pull_sqlite
```

The secondary will detect its role automatically (lease exists, its hostname ≠ primary).

### Step 6: Verify

```bash
# On all nodes:
python3 sqlite_minio_sync.py doctor
# Check [+] Leadership section:
#   role:     primary   (or secondary)
#   primary:  rpi4b
#   epoch:    1
```

---

## Rollback (disable leadership gates)

If you need to roll back to the old behavior without role enforcement:

```bash
# In config.env on all nodes:
LEADERSHIP_ENABLED=0
```

This bypasses all role checks. Push and pull work as before v0.4.0.

---

## Backward Compatibility

- `LEADERSHIP_ENABLED=0` fully disables the feature.
- Existing MinIO data (`projects/<cid>/sqlite/`) is untouched.
- The leadership prefix (`projects/<cid>/leadership/`) is new; old clients ignore it.
- Exit codes 2 (primary pull refused) and 3 (secondary push blocked) are new.
  Hook scripts that check `$?` may need updating.

---

## Hook Script Update

If your hooks check exit codes (e.g., `~/.claude-mem-minio/bin/claude-mem-pull`):

```bash
# Before (old):
python3 sqlite_minio_sync.py pull_sqlite || echo "PULL FAILED"

# After (new): handle exit code 2 (primary gate) separately
python3 sqlite_minio_sync.py pull_sqlite
rc=$?
if [ $rc -eq 0 ]; then
  echo "PULL OK"
elif [ $rc -eq 2 ]; then
  echo "PULL SKIPPED: primary node refused overwrite (this is normal)"
else
  echo "PULL FAILED with exit code $rc"
fi
```

Similarly for push (exit code 3 = secondary blocked):

```bash
python3 sqlite_minio_sync.py push_sqlite
rc=$?
if [ $rc -eq 0 ]; then
  echo "PUSH OK"
elif [ $rc -eq 3 ]; then
  echo "PUSH SKIPPED: secondary node blocked (this is normal)"
else
  echo "PUSH FAILED with exit code $rc"
fi
```

---

## Control Plane API (optional)

If you run the Membridge server (`server/main.py`), new endpoints are available:

```bash
# Register heartbeat (from each node's startup hook):
curl -X POST http://SERVER:8000/agent/heartbeat \
  -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"node_id":"rpi4b","canonical_id":"<cid>","obs_count":1234}'

# View all nodes for a project:
curl http://SERVER:8000/projects/<cid>/nodes -H 'X-MEMBRIDGE-ADMIN: <KEY>'

# View leadership state:
curl http://SERVER:8000/projects/<cid>/leadership -H 'X-MEMBRIDGE-ADMIN: <KEY>'

# Set primary (admin action):
curl -X POST http://SERVER:8000/projects/<cid>/leadership/select \
  -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
  -H 'Content-Type: application/json' \
  -d '{"primary_node_id":"rpi4b","lease_seconds":7200}'
```

All leadership endpoints are protected by the same `MEMBRIDGE_ADMIN_KEY` as other
admin endpoints (bypassed in `MEMBRIDGE_DEV=1` mode).

---

## Quickstart for New Deployments

See `docs/leadership.md` for the complete reference.

Short version:

```bash
# 1. Set on primary node in config.env:
PRIMARY_NODE_ID=<hostname>

# 2. Push from primary:
cm-push

# 3. Pull on secondaries (auto-detects secondary role):
cm-pull

# 4. Check everything:
python3 sqlite_minio_sync.py doctor
```
