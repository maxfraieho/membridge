# Leadership: Primary / Secondary Model

Membridge implements a **single-source-of-truth** model for multi-node sync.
One node is the **Primary** — it owns the canonical copy of the SQLite DB in MinIO.
All other nodes are **Secondaries**.

---

## Core Policy

| Rule | Primary | Secondary |
|------|---------|-----------|
| Write local SQLite | ✅ allowed | ✅ allowed |
| Push to MinIO | ✅ allowed | ❌ blocked by default |
| Pull from MinIO | ⚠️ refused if local DB exists (see below) | ✅ allowed (with backup) |
| Steal stale push lock | ✅ allowed | ❌ blocked |

### Why Primary Refuses Pull Overwrite

The primary node is the source of truth. If remote SHA differs from local SHA:
- It means a secondary pushed (or a manual write happened).
- Silently overwriting the primary's local DB would destroy canonical data.
- Instead: the drift is logged and a manual resolution is required.

Override for inspection (unsafe): `ALLOW_PRIMARY_PULL_OVERRIDE=1`

### Why Secondary Cannot Push

A secondary may have local writes (write-local is allowed), but pushing would
overwrite the primary's canonical copy. This is blocked by default.

Override (unsafe): `ALLOW_SECONDARY_PUSH=1`

---

## Leadership Lease

Stored at `projects/<canonical_id>/leadership/lease.json` in MinIO.

```json
{
  "canonical_id": "abc123def456abcd",
  "primary_node_id": "rpi4b",
  "issued_at": 1706000000,
  "expires_at": 1706003600,
  "lease_seconds": 3600,
  "epoch": 3,
  "policy": "primary_authoritative",
  "issued_by": "rpi4b",
  "needs_ui_selection": false
}
```

### Fields

| Field | Description |
|-------|-------------|
| `canonical_id` | SHA256(project_name)[:16] |
| `primary_node_id` | Hostname (or `MEMBRIDGE_NODE_ID`) of the primary |
| `issued_at` / `expires_at` | Unix timestamps |
| `lease_seconds` | TTL (default 3600s) |
| `epoch` | Monotonically increasing; increments on each renewal |
| `policy` | Always `primary_authoritative` for now |
| `issued_by` | Node that wrote this lease |
| `needs_ui_selection` | `true` when bootstrapped without `PRIMARY_NODE_ID` set |

### Audit Log

Every lease write appends to:
```
projects/<canonical_id>/leadership/audit/<YYYYMMDDTHHMMSSZ>-<node_id>.json
```

---

## How Role is Determined

1. Read `lease.json` from MinIO.
2. If absent → create default lease (primary = `PRIMARY_NODE_ID` env var or current node).
3. If expired:
   - If `PRIMARY_NODE_ID` matches current node → renew with `epoch+1`.
   - Otherwise → re-read to see if another node already renewed.
   - If still expired → current node is secondary.
4. If valid → role = primary if `primary_node_id == NODE_ID`, else secondary.

**Node ID** = `MEMBRIDGE_NODE_ID` env var, fallback to `platform.node()` (hostname).

---

## How to Select Primary

### Via curl (control plane API)

```bash
# First: find the canonical_id
python3 sqlite_minio_sync.py print_project

# Set primary
curl -X POST http://SERVER:8000/projects/<canonical_id>/leadership/select \
  -H 'Content-Type: application/json' \
  -H 'X-MEMBRIDGE-ADMIN: <ADMIN_KEY>' \
  -d '{"primary_node_id": "rpi4b", "lease_seconds": 7200}'

# View current leadership
curl http://SERVER:8000/projects/<canonical_id>/leadership \
  -H 'X-MEMBRIDGE-ADMIN: <ADMIN_KEY>'
```

### Via env var (persistent)

```bash
# In config.env on the primary node:
PRIMARY_NODE_ID=rpi4b
```

The node will auto-create or renew the lease on each sync operation.

### Via leadership_info command

```bash
python3 sqlite_minio_sync.py leadership_info
```

---

## Heartbeat API

Agents can register themselves with the control plane:

```bash
curl -X POST http://SERVER:8000/agent/heartbeat \
  -H 'Content-Type: application/json' \
  -H 'X-MEMBRIDGE-ADMIN: <ADMIN_KEY>' \
  -d '{
    "node_id": "rpi4b",
    "canonical_id": "abc123def456abcd",
    "obs_count": 1234,
    "db_sha": "deadbeef...",
    "ip_addrs": ["192.168.1.10"]
  }'
```

---

## Failover / Promotion

Membridge MVP uses **manual failover**:

1. Current primary goes offline or becomes stale.
2. Lease expires (default TTL: 3600s).
3. Admin promotes a secondary:
   ```bash
   curl -X POST http://SERVER:8000/projects/<cid>/leadership/select \
     -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
     -d '{"primary_node_id": "new-primary-node"}'
   ```
4. New primary sets `PRIMARY_NODE_ID=new-primary-node` in its `config.env` and runs a push.

---

## Stale Lock vs Stale Lease

| Concept | Path | TTL | Purpose |
|---------|------|-----|---------|
| Push lock | `projects/<cid>/locks/active.lock` | `LOCK_TTL_SECONDS` (2h) | Prevent concurrent pushes |
| Leadership lease | `projects/<cid>/leadership/lease.json` | `LEADERSHIP_LEASE_SECONDS` (1h) | Determine primary/secondary role |

These are independent. A secondary with `ALLOW_SECONDARY_PUSH=1` still needs to acquire the push lock.

---

## Troubleshooting

### "Primary refuses pull overwrite"
The local DB and remote differ. Primary will NOT auto-pull. Options:
- Check which is newer: `cm-doctor` shows obs counts
- If remote is authoritative: `ALLOW_PRIMARY_PULL_OVERRIDE=1 cm-pull`
- If you want the primary to hand off: promote another node

### "Secondary cannot push"
Expected behavior. Either:
- Promote this node: `POST /projects/<cid>/leadership/select`
- Or set `ALLOW_SECONDARY_PUSH=1` (breaks single-source-of-truth guarantee)

### "Lock stuck"
- Check age: `cm-doctor` → `[3/5] Lock status`
- If expired (> TTL + grace): next push will steal it
- Force steal: `FORCE_PUSH=1 cm-push`

### "needs_ui_selection=true in lease"
No `PRIMARY_NODE_ID` was set when the lease was bootstrapped.
Set it explicitly:
```bash
curl -X POST http://SERVER:8000/projects/<cid>/leadership/select \
  -H 'X-MEMBRIDGE-ADMIN: <KEY>' \
  -d '{"primary_node_id": "rpi4b"}'
```

### "Secondary ahead" (secondary has more obs than remote)
Secondary wrote locally but cannot push. Options:
- Promote secondary to primary, then push
- Manually copy the secondary DB to primary, then push from primary
- Accept loss of secondary-only data (do a fresh pull on secondary)
