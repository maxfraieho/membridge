#!/usr/bin/env python3
"""MinIO pull/push sync for claude-mem SQLite DB."""

import hashlib
import json
import os
import platform
import shutil
import signal
import sqlite3
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from urllib.request import urlopen

import boto3
from botocore.config import Config

LOCK_TTL_SECONDS = int(os.getenv("LOCK_TTL_SECONDS", "7200"))
FORCE_PUSH = os.getenv("FORCE_PUSH", "0") == "1"
# Grace period (seconds) after TTL before a foreign lock is stolen.
# Prevents race: holder might still be finishing when TTL just expired.
STALE_LOCK_GRACE_SECONDS = int(os.getenv("STALE_LOCK_GRACE_SECONDS", "60"))
# Pull-overwrite backup retention
PULL_BACKUP_MAX_DAYS = int(os.getenv("PULL_BACKUP_MAX_DAYS", "14"))
PULL_BACKUP_MAX_COUNT = int(os.getenv("PULL_BACKUP_MAX_COUNT", "50"))

# Leadership / Primary-Secondary constants
NODE_ID = os.getenv("MEMBRIDGE_NODE_ID", platform.node())
PRIMARY_NODE_ID_ENV = os.getenv("PRIMARY_NODE_ID", "")
ALLOW_SECONDARY_PUSH = os.getenv("ALLOW_SECONDARY_PUSH", "0") == "1"
ALLOW_PRIMARY_PULL_OVERRIDE = os.getenv("ALLOW_PRIMARY_PULL_OVERRIDE", "0") == "1"
LEADERSHIP_ENABLED = os.getenv("LEADERSHIP_ENABLED", "1") == "1"
LEADERSHIP_LEASE_SECONDS = int(os.getenv("LEADERSHIP_LEASE_SECONDS", "3600"))


def load_config():
    """Load config from environment variables."""
    required = [
        "MINIO_ENDPOINT",
        "MINIO_ACCESS_KEY",
        "MINIO_SECRET_KEY",
        "MINIO_BUCKET",
        "CLAUDE_PROJECT_ID",
        "CLAUDE_MEM_DB",
    ]
    cfg = {}
    for key in required:
        val = os.environ.get(key)
        if not val:
            print(f"ERROR: {key} not set")
            sys.exit(1)
        cfg[key] = val
    cfg["MINIO_REGION"] = os.environ.get("MINIO_REGION", "us-east-1")
    return cfg


NO_RESTART_WORKER = os.getenv("MEMBRIDGE_NO_RESTART_WORKER", "0") == "1"


def resolve_canonical_id(cfg):
    """Return canonical project ID — always sha256(project_name)[:16]."""
    return hashlib.sha256(cfg["CLAUDE_PROJECT_ID"].encode()).hexdigest()[:16]


def sha256_file(path):
    """Compute SHA256 of a file."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def get_s3_client(cfg):
    """Create boto3 S3 client for MinIO."""
    endpoint = cfg["MINIO_ENDPOINT"]
    return boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=cfg["MINIO_ACCESS_KEY"],
        aws_secret_access_key=cfg["MINIO_SECRET_KEY"],
        region_name=cfg["MINIO_REGION"],
        config=Config(signature_version="s3v4"),
    )


def get_lock_key(canonical_id):
    """Return the S3 key for the distributed lock."""
    return f"projects/{canonical_id}/locks/active.lock"


def get_lock_status(s3, bucket, canonical_id):
    """Check lock status. Returns (exists, lock_data, age_seconds) or (False, None, None)."""
    lock_key = get_lock_key(canonical_id)
    try:
        resp = s3.get_object(Bucket=bucket, Key=lock_key)
        lock_data = json.loads(resp["Body"].read().decode())
        age = int(time.time()) - lock_data.get("timestamp", 0)
        return True, lock_data, age
    except Exception:
        return False, None, None


def acquire_lock(s3, bucket, project_name, canonical_id):
    """Acquire distributed lock. Returns True if acquired, False if blocked."""
    lock_key = get_lock_key(canonical_id)

    # Check existing lock
    exists, lock_data, age = get_lock_status(s3, bucket, canonical_id)
    if exists:
        holder = lock_data.get("hostname", "unknown")
        same_host = holder == platform.node()
        if same_host:
            print(f"  re-acquiring own lock (holder={holder}, age={age}s)")
        elif FORCE_PUSH:
            print(f"  overriding lock (age={age}s, FORCE_PUSH=1)")
        elif age < LOCK_TTL_SECONDS:
            # Lock is active and held by a different host — block.
            print(f"  LOCK ACTIVE — held by {holder} for {age}s (TTL {LOCK_TTL_SECONDS}s)")
            print(f"  use FORCE_PUSH=1 to override")
            return False
        elif age <= LOCK_TTL_SECONDS + STALE_LOCK_GRACE_SECONDS:
            # TTL just expired but still within grace window — be conservative.
            grace_end = LOCK_TTL_SECONDS + STALE_LOCK_GRACE_SECONDS
            print(f"  LOCK RECENTLY EXPIRED (grace) — held by {holder}, age={age}s")
            print(f"  Grace period {STALE_LOCK_GRACE_SECONDS}s not exhausted (limit={grace_end}s), blocking")
            return False
        else:
            # Lock is definitively stale — steal it.
            print(f"  STALE LOCK — held by {holder}, age={age}s > TTL+grace={LOCK_TTL_SECONDS + STALE_LOCK_GRACE_SECONDS}s")
            print(f"  Stealing stale lock")

    # Write new lock
    lock_body = {
        "hostname": platform.node(),
        "timestamp": int(time.time()),
        "project": project_name,
        "canonical_id": canonical_id,
    }
    s3.put_object(
        Bucket=bucket,
        Key=lock_key,
        Body=json.dumps(lock_body, indent=2).encode(),
    )
    print(f"  lock acquired by {platform.node()}")
    return True


def get_worker_pid():
    """Read worker PID from pid file."""
    pid_file = os.path.expanduser("~/.claude-mem/worker.pid")
    if not os.path.exists(pid_file):
        return None
    try:
        with open(pid_file) as f:
            data = json.load(f)
        pid = data.get("pid")
        # Check if process is actually running
        if pid:
            os.kill(pid, 0)
            return pid
    except (json.JSONDecodeError, ProcessLookupError, PermissionError):
        pass
    return None


def stop_worker():
    """Stop the claude-mem worker gracefully."""
    pid = get_worker_pid()
    if pid is None:
        print("  worker not running, skipping stop")
        return False

    print(f"  stopping worker (PID {pid})...")
    try:
        os.kill(pid, signal.SIGTERM)
        # Wait up to 5 seconds for graceful shutdown
        for _ in range(50):
            try:
                os.kill(pid, 0)
                time.sleep(0.1)
            except ProcessLookupError:
                print("  worker stopped")
                return True
        # Force kill if still alive
        print("  worker did not stop gracefully, sending SIGKILL...")
        os.kill(pid, signal.SIGKILL)
        time.sleep(0.5)
        return True
    except ProcessLookupError:
        print("  worker already stopped")
        return True
    except PermissionError:
        print("  ERROR: no permission to stop worker")
        return False


def start_worker():
    """Start the claude-mem worker as a fully-detached daemon.

    Bun crashes with EINVAL (Fix #646) when it inherits pipe fds from the
    Claude Code hook system.  We work around this by:
      1. Spawning worker-service.cjs via setsid so it is a new session leader
         with all stdio redirected to /dev/null — no inherited pipes.
      2. Polling the HTTP health endpoint to confirm readiness instead of
         waiting for the spawned process to exit (it runs as a server).
    """
    plugin_root = os.path.expanduser(
        "~/.claude/plugins/cache/thedotmack/claude-mem/10.3.3"
    )
    worker_service = os.path.join(plugin_root, "scripts", "worker-service.cjs")

    if not os.path.isfile(worker_service):
        print(f"  ERROR: worker-service.cjs not found at {worker_service}")
        return False

    bun = shutil.which("bun") or os.path.expanduser("~/.bun/bin/bun")
    if not os.path.isfile(bun) and not shutil.which("bun"):
        print("  ERROR: bun not found")
        return False

    port = os.environ.get("CLAUDE_MEM_WORKER_PORT", "37777")
    env = os.environ.copy()
    env["CLAUDE_MEM_WORKER_PORT"] = port

    print(f"  starting worker (bun worker-service.cjs --daemon, port {port})...")

    devnull = open(os.devnull, "rb")
    try:
        proc = subprocess.Popen(
            [bun, worker_service, "--daemon"],
            stdin=devnull,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            start_new_session=True,
            env=env,
        )
    finally:
        devnull.close()

    # Poll health endpoint until ready (max 15 s)
    import urllib.request
    url = f"http://127.0.0.1:{port}/api/readiness"
    deadline = time.time() + 15
    while time.time() < deadline:
        time.sleep(0.5)
        try:
            with urllib.request.urlopen(url, timeout=1) as resp:
                if resp.status == 200:
                    print("  worker started successfully")
                    return True
        except Exception:
            pass
        if proc.poll() is not None and proc.returncode not in (0, None):
            print(f"  ERROR starting worker: daemon exited {proc.returncode}")
            return False

    print("  ERROR starting worker: readiness timeout after 15s")
    return False


def get_remote_manifest(s3, bucket, prefix):
    """Download and parse remote manifest.json. Returns dict or None."""
    try:
        resp = s3.get_object(Bucket=bucket, Key=f"{prefix}/manifest.json")
        return json.loads(resp["Body"].read().decode())
    except Exception:
        return None


def get_local_obs_count(db_path):
    """Query local SQLite for observation count (read-only). Returns int or None."""
    if not os.path.exists(db_path):
        return None
    try:
        conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
        count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        conn.close()
        return count
    except Exception:
        return None


def create_pull_safety_backup(db_path, local_sha, remote_sha, local_obs, remote_obs, local_ahead):
    """Create structured backup of local DB before pull overwrite.

    Directory: ~/.claude-mem/backups/pull-overwrite/{YYYYMMDD-HHMMSS}/
    Contents:  claude-mem.db, chroma.sqlite3 (if present), manifest.json

    Returns the backup directory path.
    """
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_base = os.path.expanduser("~/.claude-mem/backups/pull-overwrite")
    backup_dir = os.path.join(backup_base, ts)
    os.makedirs(backup_dir, exist_ok=True)

    # Copy main DB
    db_backup = os.path.join(backup_dir, "claude-mem.db")
    shutil.copy2(db_path, db_backup)

    # Copy vector-db chroma.sqlite3 if it exists
    chroma_path = os.path.expanduser("~/.claude-mem/vector-db/chroma.sqlite3")
    if os.path.exists(chroma_path):
        shutil.copy2(chroma_path, os.path.join(backup_dir, "chroma.sqlite3"))

    # Write manifest so we know what was here and why
    manifest = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "hostname": platform.node(),
        "reason": "pull-overwrite safety backup",
        "local_sha": local_sha,
        "remote_sha": remote_sha,
        "local_obs": local_obs,
        "remote_obs": remote_obs,
        "local_ahead": local_ahead,
        "db_path": db_path,
    }
    with open(os.path.join(backup_dir, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=2)

    return backup_dir


def cleanup_pull_backups(max_days=None, max_count=None):
    """Remove old pull-overwrite backups beyond max_days or max_count.

    Keeps at most `max_count` newest snapshots AND removes anything older
    than `max_days` days.  Runs silently on errors (non-critical path).
    """
    if max_days is None:
        max_days = PULL_BACKUP_MAX_DAYS
    if max_count is None:
        max_count = PULL_BACKUP_MAX_COUNT

    backup_base = os.path.expanduser("~/.claude-mem/backups/pull-overwrite")
    if not os.path.isdir(backup_base):
        return

    # Sorted oldest → newest
    dirs = sorted([
        os.path.join(backup_base, d)
        for d in os.listdir(backup_base)
        if os.path.isdir(os.path.join(backup_base, d))
    ])

    cutoff = time.time() - max_days * 86400
    removed = 0

    # Remove by age (oldest first)
    for d in list(dirs):
        try:
            if os.path.getmtime(d) < cutoff:
                shutil.rmtree(d)
                dirs.remove(d)
                removed += 1
        except Exception:
            pass

    # Remove by count (oldest first if still over limit)
    while len(dirs) > max_count:
        try:
            shutil.rmtree(dirs.pop(0))
            removed += 1
        except Exception:
            break

    if removed:
        print(f"  backup cleanup: removed {removed} old pull-overwrite snapshot(s)")


# ─────────────────────────────────────────────────────────────────
# Leadership / Primary-Secondary lease  (MinIO best-effort, no CAS)
# ─────────────────────────────────────────────────────────────────

def get_lease_key(canonical_id):
    """Return S3 key for the leadership lease."""
    return f"projects/{canonical_id}/leadership/lease.json"


def get_audit_key(canonical_id, node_id):
    """Return S3 key for a leadership audit log entry."""
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    safe_node = node_id.replace("/", "_").replace(":", "_")
    return f"projects/{canonical_id}/leadership/audit/{ts}-{safe_node}.json"


def read_lease(s3, bucket, canonical_id):
    """Read leadership lease from MinIO. Returns dict or None."""
    try:
        resp = s3.get_object(Bucket=bucket, Key=get_lease_key(canonical_id))
        return json.loads(resp["Body"].read().decode())
    except Exception:
        return None


def write_lease(s3, bucket, canonical_id, primary_node_id, lease_seconds=None,
                epoch=1, policy="primary_authoritative", needs_ui_selection=False):
    """Write leadership lease + audit log to MinIO. Returns the lease dict.

    MinIO has no CAS, so this is best-effort. Callers should re-read to verify.
    """
    if lease_seconds is None:
        lease_seconds = LEADERSHIP_LEASE_SECONDS
    now = int(time.time())
    lease = {
        "canonical_id": canonical_id,
        "primary_node_id": primary_node_id,
        "issued_at": now,
        "expires_at": now + lease_seconds,
        "lease_seconds": lease_seconds,
        "epoch": epoch,
        "policy": policy,
        "issued_by": NODE_ID,
    }
    if needs_ui_selection:
        lease["needs_ui_selection"] = True

    s3.put_object(
        Bucket=bucket,
        Key=get_lease_key(canonical_id),
        Body=json.dumps(lease, indent=2).encode(),
    )

    # Audit log (non-critical — failure is silently ignored)
    try:
        audit_entry = {
            **lease,
            "event": "lease_written",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        s3.put_object(
            Bucket=bucket,
            Key=get_audit_key(canonical_id, NODE_ID),
            Body=json.dumps(audit_entry, indent=2).encode(),
        )
    except Exception:
        pass

    return lease


def determine_role(s3, bucket, canonical_id):
    """Determine this node's role as 'primary' or 'secondary'.

    Returns (role, lease, was_created) where:
      role        — 'primary' | 'secondary'
      lease       — current lease dict
      was_created — True if lease was absent/expired and recreated

    Best-effort without CAS: read → maybe write → re-read to verify.
    """
    lease = read_lease(s3, bucket, canonical_id)
    now = int(time.time())

    if lease is None:
        # No lease — bootstrap a default
        primary_node = PRIMARY_NODE_ID_ENV if PRIMARY_NODE_ID_ENV else NODE_ID
        needs_ui = not bool(PRIMARY_NODE_ID_ENV)
        lease = write_lease(
            s3, bucket, canonical_id, primary_node,
            needs_ui_selection=needs_ui,
        )
        print(f"  [leadership] no lease found — created default (primary={primary_node})")
        if needs_ui:
            print("  [leadership] WARNING: needs_ui_selection=true")
            print("    Set PRIMARY_NODE_ID env var or use POST /projects/{}/leadership/select".format(canonical_id))
        role = "primary" if NODE_ID == primary_node else "secondary"
        return role, lease, True

    expires_at = lease.get("expires_at", 0)
    primary_node = lease.get("primary_node_id", "")

    if expires_at < now:
        # Lease expired — try to renew if we are the configured primary
        if PRIMARY_NODE_ID_ENV and PRIMARY_NODE_ID_ENV == NODE_ID:
            old_epoch = lease.get("epoch", 1)
            lease = write_lease(
                s3, bucket, canonical_id, NODE_ID,
                epoch=old_epoch + 1,
            )
            print(f"  [leadership] lease expired — renewed as primary (epoch={lease['epoch']})")
            return "primary", lease, True

        # Not our lease to renew — re-read to see if another node wrote a fresh one
        lease2 = read_lease(s3, bucket, canonical_id)
        if lease2 and lease2.get("expires_at", 0) >= now:
            p2 = lease2.get("primary_node_id", "")
            return ("primary" if NODE_ID == p2 else "secondary"), lease2, False

        # Still expired, not configured as primary → secondary
        return "secondary", lease, True

    role = "primary" if NODE_ID == primary_node else "secondary"
    return role, lease, False


def leadership_info():
    """Print leadership lease and this node's current role."""
    cfg = load_config()
    canonical_id = resolve_canonical_id(cfg)
    s3 = get_s3_client(cfg)
    bucket = cfg["MINIO_BUCKET"]

    print("=== Leadership Lease ===")
    print(f"  node_id:      {NODE_ID}")
    print(f"  canonical_id: {canonical_id}")
    print()

    try:
        role, lease, was_created = determine_role(s3, bucket, canonical_id)
        now_ts = int(time.time())
        expires_at = lease.get("expires_at", 0)
        issued_at = lease.get("issued_at", 0)
        ttl = expires_at - now_ts

        print(f"  role:          {role}")
        print(f"  primary:       {lease.get('primary_node_id', '?')}")
        print(f"  epoch:         {lease.get('epoch', 1)}")
        print(f"  policy:        {lease.get('policy', '?')}")
        print(f"  issued_by:     {lease.get('issued_by', '?')}")
        if issued_at:
            print(f"  issued_at:     {datetime.fromtimestamp(issued_at).isoformat()}")
        print(f"  ttl_remaining: {ttl}s")
        if was_created:
            print()
            print("  NOTE: lease was absent/expired and was recreated.")
        if lease.get("needs_ui_selection"):
            print()
            print("  WARNING: needs_ui_selection=true")
            print("  Confirm the primary node via:")
            print(f"    curl -X POST http://SERVER/projects/{canonical_id}/leadership/select \\")
            print(f"      -H 'Content-Type: application/json' \\")
            print(f"      -d '{{\"primary_node_id\": \"{NODE_ID}\"}}'")
    except Exception as e:
        print(f"  ERROR: {e}")
        sys.exit(1)


def pull_sqlite():
    """Pull SQLite DB from MinIO and atomically replace local copy."""
    cfg = load_config()

    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = resolve_canonical_id(cfg)
    prefix = f"projects/{canonical_id}/sqlite"
    db_path = cfg["CLAUDE_MEM_DB"]

    # Safety-tracking variables (used by local-ahead guard and backup)
    local_sha = None
    local_obs = None
    remote_obs = 0
    local_ahead = False
    backup_dir = None

    print(f"=== claude-mem MinIO pull sync ===")
    print(f"  project:      {project_name}")
    print(f"  canonical_id: {canonical_id}")
    print(f"  prefix:       {prefix}/")
    print(f"  local db:     {db_path}")
    print()

    s3 = get_s3_client(cfg)
    bucket = cfg["MINIO_BUCKET"]

    # --- Download remote SHA256 ---
    print("[1/7] Downloading remote SHA256...")
    sha_key = f"{prefix}/claude-mem.db.sha256"
    try:
        resp = s3.get_object(Bucket=bucket, Key=sha_key)
        remote_sha = resp["Body"].read().decode().strip().split()[0]
        print(f"  remote SHA256: {remote_sha}")
    except s3.exceptions.NoSuchKey:
        print(f"  ERROR: {sha_key} not found in bucket")
        sys.exit(1)

    # --- Compare with local ---
    print("[2/7] Comparing with local DB...")
    db_size_before = 0
    if os.path.exists(db_path):
        local_sha = sha256_file(db_path)
        db_size_before = os.path.getsize(db_path)
        print(f"  local SHA256:  {local_sha}")
        print(f"  local size:    {db_size_before} bytes")
        if local_sha == remote_sha:
            print("  RESULT: already up to date")
            sys.exit(0)
        print("  SHA256 mismatch — pulling remote DB")

        # --- Leadership gate: primary refuses destructive pull overwrite ---
        if LEADERSHIP_ENABLED:
            try:
                role, lease, _ = determine_role(s3, bucket, canonical_id)
                primary_node = lease.get("primary_node_id", "?")
                print(f"  [leadership] role={role}  node={NODE_ID}  primary={primary_node}")
                if role == "primary" and not ALLOW_PRIMARY_PULL_OVERRIDE:
                    print("  PRIMARY: refusing destructive pull overwrite of local DB.")
                    print(f"    local_sha:  {local_sha}")
                    print(f"    remote_sha: {remote_sha}")
                    print("  Primary is the single source of truth — remote drift must be resolved manually.")
                    print("  Options:")
                    print("    - Inspect: download remote DB to a temp path and compare")
                    print("    - Override (unsafe): ALLOW_PRIMARY_PULL_OVERRIDE=1")
                    print(f"    - Handover: POST /projects/{canonical_id}/leadership/select")
                    sys.exit(2)
            except Exception as _e:
                print(f"  [leadership] check failed ({_e}) — proceeding without role enforcement")

        # --- Local-ahead guard: compare observation counts before overwrite ---
        local_obs = get_local_obs_count(db_path)
        remote_manifest = get_remote_manifest(s3, bucket, prefix)
        remote_obs = remote_manifest.get("observations", 0) if remote_manifest else 0
        if local_obs is not None and local_obs > remote_obs:
            local_ahead = True
            print(f"  LOCAL AHEAD SUSPECTED: local={local_obs} obs > remote={remote_obs} obs")
            print(f"  Safety backup will preserve local state before overwrite")
        else:
            print(f"  obs check: local={local_obs} remote={remote_obs}")
    else:
        print("  local DB does not exist — pulling remote")

    # --- Download remote DB to temp file ---
    print("[3/7] Downloading remote DB...")
    db_key = f"{prefix}/claude-mem.db"
    db_dir = os.path.dirname(db_path)
    fd, tmp_path = tempfile.mkstemp(suffix=".db.tmp", dir=db_dir)
    os.close(fd)
    try:
        s3.download_file(bucket, db_key, tmp_path)
        tmp_size = os.path.getsize(tmp_path)
        print(f"  downloaded: {tmp_size} bytes → {tmp_path}")
    except Exception as e:
        os.unlink(tmp_path)
        print(f"  ERROR downloading: {e}")
        sys.exit(1)

    # --- Verify SHA256 ---
    print("[4/7] Verifying SHA256...")
    downloaded_sha = sha256_file(tmp_path)
    if downloaded_sha != remote_sha:
        os.unlink(tmp_path)
        print(f"  ERROR: SHA256 mismatch!")
        print(f"    expected: {remote_sha}")
        print(f"    got:      {downloaded_sha}")
        sys.exit(1)
    print("  SHA256 verified OK")

    # --- Safety backup before overwrite ---
    if os.path.exists(db_path):
        print(f"[5/7] Creating safety backup before overwrite...")
        backup_dir = create_pull_safety_backup(
            db_path, local_sha, remote_sha, local_obs, remote_obs, local_ahead
        )
        print(f"  backup dir: {backup_dir}")
        if local_ahead:
            print(f"  !! LOCAL AHEAD: local data may be newer than remote — backup preserved !!")
    else:
        print("[5/7] No local DB to backup, skipping")

    # --- Stop worker ---
    print("[6/7] Stopping worker for atomic replace...")
    worker_was_running = stop_worker()
    # Small delay to release file locks
    time.sleep(0.5)

    # --- Atomic replace ---
    print("[7/7] Atomic replace...")
    os.replace(tmp_path, db_path)
    db_size_after = os.path.getsize(db_path)
    print(f"  replaced: {db_path}")
    print(f"  new size: {db_size_after} bytes")

    # --- Verify DB integrity ---
    print()
    print("=== Post-replace verification ===")
    try:
        conn = sqlite3.connect(db_path)
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        obs_count = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
        sess_count = conn.execute(
            "SELECT COUNT(*) FROM session_summaries"
        ).fetchone()[0]
        conn.close()
        print(f"  tables:       {len(tables)}")
        print(f"  observations: {obs_count}")
        print(f"  sessions:     {sess_count}")
    except Exception as e:
        print(f"  ERROR verifying DB: {e}")

    # --- Post-replace SHA256 check ---
    final_sha = sha256_file(db_path)
    if final_sha != remote_sha:
        print(f"  WARNING: post-replace SHA256 mismatch!")
        print(f"    expected: {remote_sha}")
        print(f"    got:      {final_sha}")
    else:
        print(f"  SHA256 post-replace: OK")

    # --- Conditionally restart worker ---
    worker_ok = None
    if NO_RESTART_WORKER:
        print()
        print("  --no-restart-worker: skipping worker restart (safe mode)")
        print("  Worker will start automatically with next Claude CLI session.")
    else:
        print()
        time.sleep(1)
        worker_ok = start_worker()
        time.sleep(2)
        post_worker_sha = sha256_file(db_path)
        if post_worker_sha != remote_sha:
            print(f"  WARNING: worker may have overwritten DB!")
            print(f"    expected: {remote_sha}")
            print(f"    got:      {post_worker_sha}")
        else:
            print(f"  DB intact after worker start: OK")

    # --- Cleanup old backups (non-critical, runs silently on errors) ---
    cleanup_pull_backups()

    # --- Final report ---
    print()
    print("=" * 40)
    print("SYNC COMPLETE")
    print("=" * 40)
    print(f"  canonical_id:    {canonical_id}")
    print(f"  DB size before:  {db_size_before} bytes")
    print(f"  DB size after:   {db_size_after} bytes")
    print(f"  backup dir:      {backup_dir or 'none'}")
    if local_ahead:
        print(f"  LOCAL AHEAD:     YES — check backup before discarding!")
    if worker_ok is None:
        print(f"  worker restart:  SKIPPED (safe mode)")
    else:
        print(f"  worker restart:  {'OK' if worker_ok else 'FAILED'}")
    print(f"  observations:    {obs_count}")
    print(f"  summaries:       {sess_count}")


def push_sqlite():
    """Push local SQLite DB to MinIO with integrity checks."""
    cfg = load_config()

    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = resolve_canonical_id(cfg)
    prefix = f"projects/{canonical_id}/sqlite"
    db_path = cfg["CLAUDE_MEM_DB"]

    print("=== claude-mem MinIO push sync ===")
    print(f"  project:      {project_name}")
    print(f"  canonical_id: {canonical_id}")
    print(f"  prefix:       {prefix}/")
    print(f"  local db:     {db_path}")
    print()

    # --- Check local DB exists ---
    if not os.path.exists(db_path):
        print("ERROR: local DB does not exist")
        sys.exit(1)

    s3 = get_s3_client(cfg)
    bucket = cfg["MINIO_BUCKET"]

    # --- Leadership gate: secondary cannot push ---
    if LEADERSHIP_ENABLED:
        try:
            role, lease, _ = determine_role(s3, bucket, canonical_id)
            primary_node = lease.get("primary_node_id", "?")
            print(f"[0/6] Leadership: role={role}  node={NODE_ID}  primary={primary_node}")
            if role == "secondary" and not ALLOW_SECONDARY_PUSH:
                print("  SECONDARY: push blocked by default.")
                print("  Secondary nodes must not push — only the primary is the source of truth.")
                print("  Options:")
                print(f"    - Request promotion: POST /projects/{canonical_id}/leadership/select")
                print("    - Override (unsafe): ALLOW_SECONDARY_PUSH=1")
                sys.exit(3)
            print()
        except Exception as _e:
            print(f"[0/6] Leadership check failed ({_e}) — proceeding without role enforcement")
            print()

    # --- Stop worker for consistent snapshot ---
    print("[1/6] Stopping worker for consistent snapshot...")
    stop_worker()
    time.sleep(0.5)

    # --- VACUUM + integrity check on a snapshot copy ---
    print("[2/6] Creating consistent snapshot...")
    db_dir = os.path.dirname(db_path)
    fd, snap_path = tempfile.mkstemp(suffix=".snap.db", dir=db_dir)
    os.close(fd)
    try:
        conn = sqlite3.connect(db_path)
        # Run integrity check on source
        ic = conn.execute("PRAGMA integrity_check").fetchone()[0]
        if ic != "ok":
            conn.close()
            os.unlink(snap_path)
            print(f"  ERROR: source DB integrity check failed: {ic}")
            start_worker()
            sys.exit(1)

        # VACUUM INTO creates a clean, defragmented copy
        conn.execute(f"VACUUM INTO '{snap_path}'")
        conn.close()
        snap_size = os.path.getsize(snap_path)
        print(f"  snapshot: {snap_size} bytes (VACUUM'd)")

        # Read counts from snapshot
        snap_conn = sqlite3.connect(snap_path)
        obs_count = snap_conn.execute(
            "SELECT COUNT(*) FROM observations"
        ).fetchone()[0]
        sess_count = snap_conn.execute(
            "SELECT COUNT(*) FROM session_summaries"
        ).fetchone()[0]
        prompt_count = snap_conn.execute(
            "SELECT COUNT(*) FROM user_prompts"
        ).fetchone()[0]
        table_count = len(snap_conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall())
        snap_conn.close()
        print(f"  tables:       {table_count}")
        print(f"  observations: {obs_count}")
        print(f"  summaries:    {sess_count}")
        print(f"  prompts:      {prompt_count}")
    except Exception as e:
        if os.path.exists(snap_path):
            os.unlink(snap_path)
        print(f"  ERROR creating snapshot: {e}")
        start_worker()
        sys.exit(1)

    # --- Restart worker early (snapshot is independent now) ---
    print()
    print("[3/6] Restarting worker...")
    time.sleep(1)
    worker_ok = start_worker()

    # --- Compute SHA256 of snapshot ---
    print()
    print("[4/6] Computing SHA256...")
    local_sha = sha256_file(snap_path)
    print(f"  SHA256: {local_sha}")

    # --- Compare with remote ---
    print("[5/6] Comparing with remote...")
    sha_key = f"{prefix}/claude-mem.db.sha256"
    remote_sha = None
    try:
        resp = s3.get_object(Bucket=bucket, Key=sha_key)
        remote_sha = resp["Body"].read().decode().strip().split()[0]
        print(f"  remote SHA256: {remote_sha}")
    except Exception:
        print("  no remote SHA256 found (first push or missing)")

    if remote_sha == local_sha:
        os.unlink(snap_path)
        print("  RESULT: remote already up to date")
        sys.exit(0)

    if remote_sha:
        print("  SHA256 differs — pushing")
        # --- Pull-before-push guard: warn if remote appears ahead ---
        remote_manifest = get_remote_manifest(s3, bucket, prefix)
        if remote_manifest:
            remote_obs_count = remote_manifest.get("observations", 0)
            if remote_obs_count > obs_count:
                print(f"  WARN: remote may be ahead (remote={remote_obs_count} obs vs local={obs_count} obs)")
                print(f"  Consider running pull first to avoid overwriting newer remote data")
    else:
        print("  pushing new snapshot")

    # --- Acquire lock ---
    print()
    print("[6/7] Acquiring lock...")
    if not acquire_lock(s3, bucket, project_name, canonical_id):
        os.unlink(snap_path)
        print("  push aborted — could not acquire lock")
        sys.exit(1)

    # --- Upload ---
    print("[7/7] Uploading to MinIO...")
    db_key = f"{prefix}/claude-mem.db"
    try:
        # Upload DB
        s3.upload_file(snap_path, bucket, db_key)
        print(f"  uploaded: {db_key} ({snap_size} bytes)")

        # Upload SHA256
        sha_content = f"{local_sha}  claude-mem.db\n"
        s3.put_object(
            Bucket=bucket,
            Key=sha_key,
            Body=sha_content.encode(),
        )
        print(f"  uploaded: {sha_key}")

        # Upload manifest
        manifest = {
            "project": project_name,
            "canonical_id": canonical_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source_host": os.uname().nodename,
            "db_size": snap_size,
            "sha256": local_sha,
            "observations": obs_count,
            "session_summaries": sess_count,
            "user_prompts": prompt_count,
            "tables": table_count,
        }
        manifest_key = f"{prefix}/manifest.json"
        s3.put_object(
            Bucket=bucket,
            Key=manifest_key,
            Body=json.dumps(manifest, indent=2).encode(),
        )
        print(f"  uploaded: {manifest_key}")
    except Exception as e:
        print(f"  ERROR uploading: {e}")
        os.unlink(snap_path)
        sys.exit(1)

    # --- Verify remote ---
    print()
    print("=== Post-upload verification ===")
    try:
        resp = s3.get_object(Bucket=bucket, Key=sha_key)
        verify_sha = resp["Body"].read().decode().strip().split()[0]
        if verify_sha == local_sha:
            print("  remote SHA256: OK")
        else:
            print(f"  WARNING: remote SHA256 mismatch after upload!")
            print(f"    expected: {local_sha}")
            print(f"    got:      {verify_sha}")
    except Exception as e:
        print(f"  WARNING: could not verify remote SHA256: {e}")

    # Cleanup snapshot
    os.unlink(snap_path)

    # --- Final report ---
    print()
    print("=" * 40)
    print("PUSH COMPLETE")
    print("=" * 40)
    print(f"  canonical_id:    {canonical_id}")
    print(f"  snapshot size:   {snap_size} bytes")
    print(f"  SHA256:          {local_sha}")
    print(f"  observations:    {obs_count}")
    print(f"  summaries:       {sess_count}")
    print(f"  prompts:         {prompt_count}")
    print(f"  worker restart:  {'OK' if worker_ok else 'FAILED'}")
    print(f"  remote prefix:   {prefix}/")


def print_project():
    """Print project identity info."""
    cfg = load_config()
    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = resolve_canonical_id(cfg)
    print(f"project_name: {project_name}")
    print(f"canonical_project_id: {canonical_id}")


def doctor():
    """Run diagnostics on the entire sync system."""
    cfg = load_config()
    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = resolve_canonical_id(cfg)
    prefix = f"projects/{canonical_id}/sqlite"
    db_path = cfg["CLAUDE_MEM_DB"]
    status = "OK"

    print("=" * 44)
    print("  claude-mem sync — doctor")
    print("=" * 44)
    print()

    # --- 1. Identity ---
    print("[1/5] Project identity")
    print(f"  project_name:         {project_name}")
    print(f"  canonical_project_id: {canonical_id}")
    print(f"  hostname:             {platform.node()}")
    print()

    # --- 2. MinIO connectivity ---
    print("[2/5] MinIO connectivity")
    bucket = cfg["MINIO_BUCKET"]
    try:
        s3 = get_s3_client(cfg)
        s3.head_bucket(Bucket=bucket)
        print(f"  endpoint: {cfg['MINIO_ENDPOINT']}")
        print(f"  bucket:   {bucket} — OK")
    except Exception as e:
        print(f"  endpoint: {cfg['MINIO_ENDPOINT']}")
        print(f"  bucket:   {bucket} — FAIL: {e}")
        status = "ERROR"
        # Can't continue remote checks
        s3 = None

    # Check remote objects
    if s3:
        try:
            resp = s3.head_object(Bucket=bucket, Key=f"{prefix}/claude-mem.db")
            remote_size = resp["ContentLength"]
            print(f"  remote DB: {remote_size} bytes")
        except Exception:
            print(f"  remote DB: not found")

        try:
            resp = s3.get_object(Bucket=bucket, Key=f"{prefix}/claude-mem.db.sha256")
            remote_sha = resp["Body"].read().decode().strip().split()[0]
            print(f"  remote SHA256: {remote_sha[:16]}...")
        except Exception:
            print(f"  remote SHA256: not found")
    print()

    # --- 3. Lock status ---
    print("[3/5] Lock status")
    if s3:
        exists, lock_data, age = get_lock_status(s3, bucket, canonical_id)
        if exists:
            holder = lock_data.get("hostname", "unknown")
            if age < LOCK_TTL_SECONDS:
                print(f"  status:   LOCKED")
                print(f"  holder:   {holder}")
                print(f"  age:      {age}s / {LOCK_TTL_SECONDS}s TTL")
            else:
                print(f"  status:   EXPIRED")
                print(f"  holder:   {holder}")
                print(f"  age:      {age}s (TTL={LOCK_TTL_SECONDS}s)")
        else:
            print(f"  status:   FREE (no lock file)")
    else:
        print(f"  status:   UNKNOWN (MinIO unreachable)")
        status = "ERROR"
    print()

    # --- 4. SQLite health ---
    print("[4/5] SQLite DB health")
    if os.path.exists(db_path):
        db_size = os.path.getsize(db_path)
        print(f"  path: {db_path}")
        print(f"  size: {db_size} bytes")
        try:
            conn = sqlite3.connect(db_path)
            ic = conn.execute("PRAGMA integrity_check").fetchone()[0]
            tables = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'"
            ).fetchall()
            obs = conn.execute("SELECT COUNT(*) FROM observations").fetchone()[0]
            summ = conn.execute("SELECT COUNT(*) FROM session_summaries").fetchone()[0]
            prompts = conn.execute("SELECT COUNT(*) FROM user_prompts").fetchone()[0]
            conn.close()
            print(f"  integrity:    {ic}")
            print(f"  tables:       {len(tables)}")
            print(f"  observations: {obs}")
            print(f"  summaries:    {summ}")
            print(f"  prompts:      {prompts}")
            if ic != "ok":
                status = "ERROR"
        except Exception as e:
            print(f"  ERROR: {e}")
            status = "ERROR"
    else:
        print(f"  path: {db_path} — NOT FOUND")
        status = "ERROR"
    print()

    # --- 5. Worker health ---
    print("[5/5] Worker health")
    pid = get_worker_pid()
    if pid:
        print(f"  PID: {pid}")
    else:
        print(f"  PID: not running")

    try:
        resp = urlopen("http://127.0.0.1:37777/api/health", timeout=5)
        health = json.loads(resp.read().decode())
        print(f"  status:      {health.get('status', '?')}")
        print(f"  version:     {health.get('version', '?')}")
        print(f"  initialized: {health.get('initialized', '?')}")
        print(f"  mcpReady:    {health.get('mcpReady', '?')}")
        if health.get("status") != "ok":
            status = "DEGRADED" if status == "OK" else status
    except Exception as e:
        print(f"  health endpoint: FAIL ({e})")
        status = "DEGRADED" if status == "OK" else status
    print()

    # --- Hooks check ---
    print("[+] Hooks")
    settings_path = os.path.expanduser("~/.claude/settings.json")
    hooks_ok = False
    try:
        with open(settings_path) as f:
            settings = json.load(f)
        hooks = settings.get("hooks", {})
        has_pull = False
        has_push = False
        for h in hooks.get("SessionStart", []):
            for hh in h.get("hooks", []):
                if "hook-pull" in hh.get("command", ""):
                    has_pull = True
        for h in hooks.get("Stop", []):
            for hh in h.get("hooks", []):
                if "hook-push" in hh.get("command", ""):
                    has_push = True
        print(f"  SessionStart pull: {'YES' if has_pull else 'NO'}")
        print(f"  Stop push:         {'YES' if has_push else 'NO'}")
        hooks_ok = has_pull and has_push
    except Exception as e:
        print(f"  ERROR reading settings: {e}")
    print()

    # --- Leadership ---
    print("[+] Leadership")
    if s3:
        try:
            role, lease, was_created = determine_role(s3, bucket, canonical_id)
            primary_node = lease.get("primary_node_id", "?")
            expires_at = lease.get("expires_at", 0)
            ttl = expires_at - int(time.time())
            print(f"  role:     {role}")
            print(f"  node_id:  {NODE_ID}")
            print(f"  primary:  {primary_node}")
            print(f"  epoch:    {lease.get('epoch', 1)}")
            print(f"  ttl:      {ttl}s remaining")
            if was_created:
                print(f"  NOTE:     lease was recreated (was absent/expired)")
            if lease.get("needs_ui_selection"):
                print(f"  WARNING:  needs_ui_selection=true — confirm primary via /leadership/select")
        except Exception as e:
            print(f"  WARNING: leadership check failed: {e}")
    else:
        print("  UNKNOWN (MinIO unreachable)")
    print()

    # --- Final ---
    print("=" * 44)
    if status == "OK" and hooks_ok:
        print("  STATUS: OK — READY FOR PRODUCTION")
    elif status == "OK" and not hooks_ok:
        print("  STATUS: DEGRADED — hooks incomplete")
    else:
        print(f"  STATUS: {status}")
    print("=" * 44)


if __name__ == "__main__":
    commands = {
        "pull_sqlite": pull_sqlite,
        "push_sqlite": push_sqlite,
        "doctor": doctor,
        "print_project": print_project,
        "leadership_info": leadership_info,
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: sqlite_minio_sync.py <pull_sqlite|push_sqlite|doctor|print_project|leadership_info>")
        sys.exit(1)

    commands[sys.argv[1]]()
