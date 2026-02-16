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
        if age < LOCK_TTL_SECONDS and not FORCE_PUSH and not same_host:
            print(f"  LOCK ACTIVE — held by {holder} for {age}s (TTL {LOCK_TTL_SECONDS}s)")
            print(f"  use FORCE_PUSH=1 to override")
            return False
        if same_host:
            print(f"  re-acquiring own lock (holder={holder}, age={age}s)")
        elif FORCE_PUSH:
            print(f"  overriding stale/active lock (age={age}s, FORCE_PUSH=1)")
        else:
            print(f"  lock expired (age={age}s > TTL={LOCK_TTL_SECONDS}s), taking over")

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
    """Start the claude-mem worker."""
    plugin_root = os.path.expanduser(
        "~/.claude/plugins/cache/thedotmack/claude-mem"
    )
    # Find the latest version
    if not os.path.isdir(plugin_root):
        print("  ERROR: plugin root not found")
        return False

    versions = sorted(os.listdir(plugin_root))
    if not versions:
        print("  ERROR: no plugin versions found")
        return False
    version = versions[-1]
    root = os.path.join(plugin_root, version)

    bun_runner = os.path.join(root, "scripts", "bun-runner.js")
    worker_svc = os.path.join(root, "scripts", "worker-service.cjs")

    npm_global_bin = os.path.expanduser("~/npm-global/bin")
    env = os.environ.copy()
    env["PATH"] = f"{npm_global_bin}:{env.get('PATH', '')}"
    env["CLAUDE_PLUGIN_ROOT"] = root

    print(f"  starting worker (plugin v{version})...")
    result = subprocess.run(
        ["node", bun_runner, worker_svc, "start"],
        capture_output=True,
        text=True,
        timeout=30,
        env=env,
    )

    if result.returncode == 0:
        try:
            resp = json.loads(result.stdout.strip())
            if resp.get("status") == "ready":
                print("  worker started successfully")
                return True
        except json.JSONDecodeError:
            pass
        print("  worker started (non-JSON response)")
        return True
    else:
        print(f"  ERROR starting worker: {result.stderr}")
        return False


def pull_sqlite():
    """Pull SQLite DB from MinIO and atomically replace local copy."""
    cfg = load_config()

    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = hashlib.sha256(project_name.encode()).hexdigest()[:16]
    prefix = f"projects/{canonical_id}/sqlite"
    db_path = cfg["CLAUDE_MEM_DB"]

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

    # --- Backup local DB ---
    backup_name = None
    if os.path.exists(db_path):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{db_path}.bak.{ts}"
        print(f"[5/7] Backing up local DB → {backup_name}")
        shutil.copy2(db_path, backup_name)
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

    # --- Restart worker (with sync delay to avoid race) ---
    print()
    time.sleep(1)
    worker_ok = start_worker()
    # Verify DB was not overwritten by worker
    time.sleep(2)
    post_worker_sha = sha256_file(db_path)
    if post_worker_sha != remote_sha:
        print(f"  WARNING: worker may have overwritten DB!")
        print(f"    expected: {remote_sha}")
        print(f"    got:      {post_worker_sha}")
    else:
        print(f"  DB intact after worker start: OK")

    # --- Final report ---
    print()
    print("=" * 40)
    print("SYNC COMPLETE")
    print("=" * 40)
    print(f"  canonical_id:    {canonical_id}")
    print(f"  DB size before:  {db_size_before} bytes")
    print(f"  DB size after:   {db_size_after} bytes")
    print(f"  backup:          {backup_name or 'none'}")
    print(f"  worker restart:  {'OK' if worker_ok else 'FAILED'}")
    print(f"  observations:    {obs_count}")
    print(f"  summaries:       {sess_count}")


def push_sqlite():
    """Push local SQLite DB to MinIO with integrity checks."""
    cfg = load_config()

    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = hashlib.sha256(project_name.encode()).hexdigest()[:16]
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
    canonical_id = hashlib.sha256(project_name.encode()).hexdigest()[:16]
    print(f"project_name: {project_name}")
    print(f"canonical_project_id: {canonical_id}")


def doctor():
    """Run diagnostics on the entire sync system."""
    cfg = load_config()
    project_name = cfg["CLAUDE_PROJECT_ID"]
    canonical_id = hashlib.sha256(project_name.encode()).hexdigest()[:16]
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
    }

    if len(sys.argv) < 2 or sys.argv[1] not in commands:
        print("Usage: sqlite_minio_sync.py <pull_sqlite|push_sqlite|doctor|print_project>")
        sys.exit(1)

    commands[sys.argv[1]]()
