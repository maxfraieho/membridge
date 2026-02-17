"""Compatibility wrappers that call sqlite_minio_sync.py via subprocess.

These functions allow both legacy hooks and the new agent API to use
the same sync engine without modifying sqlite_minio_sync.py.

Each wrapper:
- Loads config from ~/.claude-mem-minio/config.env (or override)
- Sets CLAUDE_PROJECT_ID to the project name
- Computes canonical_id = sha256(project_name)[:16]
- Calls sqlite_minio_sync.py functions via subprocess
- Returns structured JSON result
"""

import hashlib
import json
import os
import platform
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional


MAX_OUTPUT_LINES = 200

SYNC_SCRIPT = Path(__file__).resolve().parent.parent.parent / "sqlite_minio_sync.py"

DEFAULT_CONFIG_ENV = Path(
    os.environ.get("MEMBRIDGE_CONFIG_ENV", os.path.expanduser("~/.claude-mem-minio/config.env"))
)

PROTECTED_USER_FILES = [
    "~/.claude/.credentials.json",
    "~/.claude/auth.json",
    "~/.claude/settings.local.json",
]


def canonical_id(project_name: str) -> str:
    return hashlib.sha256(project_name.encode()).hexdigest()[:16]


def _load_config_env(config_path: Optional[Path] = None) -> dict[str, str]:
    path = config_path or DEFAULT_CONFIG_ENV
    env = {}
    if path.exists():
        for line in path.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _build_env(project_name: str, config_path: Optional[Path] = None) -> dict[str, str]:
    env = os.environ.copy()
    config = _load_config_env(config_path)
    env.update(config)
    env["CLAUDE_PROJECT_ID"] = project_name
    if "CLAUDE_CANONICAL_PROJECT_ID" in env:
        del env["CLAUDE_CANONICAL_PROJECT_ID"]
    return env


def _tail_lines(text: str, max_lines: int = MAX_OUTPUT_LINES) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join([f"... ({len(lines) - max_lines} lines truncated)"] + lines[-max_lines:])


def _run_sync_subprocess(
    action: str,
    project_name: str,
    extra_env: Optional[dict] = None,
    config_path: Optional[Path] = None,
    timeout: int = 120,
) -> dict:
    cid = canonical_id(project_name)
    hostname = platform.node()
    started_at = time.time()

    if not SYNC_SCRIPT.exists():
        return {
            "ok": False,
            "action": action,
            "project": project_name,
            "canonical_id": cid,
            "hostname": hostname,
            "detail": f"Sync script not found: {SYNC_SCRIPT}",
            "returncode": -1,
            "started_at": started_at,
            "finished_at": time.time(),
        }

    func_map = {
        "push": "push_sqlite",
        "pull": "pull_sqlite",
        "doctor": "doctor",
    }
    func_name = func_map.get(action)
    if not func_name:
        return {
            "ok": False,
            "action": action,
            "project": project_name,
            "canonical_id": cid,
            "hostname": hostname,
            "detail": f"Unknown action: {action}",
            "returncode": -1,
            "started_at": started_at,
            "finished_at": time.time(),
        }

    env = _build_env(project_name, config_path)
    if extra_env:
        env.update(extra_env)

    python = sys.executable
    cmd = [python, "-c", f"import sqlite_minio_sync; sqlite_minio_sync.{func_name}()"]

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
            cwd=str(SYNC_SCRIPT.parent),
        )
        finished_at = time.time()
        stdout = _tail_lines(result.stdout) if result.stdout else None
        stderr = _tail_lines(result.stderr) if result.stderr else None

        return {
            "ok": result.returncode == 0,
            "action": action,
            "project": project_name,
            "canonical_id": cid,
            "hostname": hostname,
            "detail": f"{action} {'completed' if result.returncode == 0 else 'failed'}",
            "stdout": stdout,
            "stderr": stderr,
            "returncode": result.returncode,
            "started_at": started_at,
            "finished_at": finished_at,
        }
    except subprocess.TimeoutExpired:
        return {
            "ok": False,
            "action": action,
            "project": project_name,
            "canonical_id": cid,
            "hostname": hostname,
            "detail": f"{action} timed out after {timeout}s",
            "returncode": -1,
            "started_at": started_at,
            "finished_at": time.time(),
        }
    except Exception as e:
        return {
            "ok": False,
            "action": action,
            "project": project_name,
            "canonical_id": cid,
            "hostname": hostname,
            "detail": f"{action} error: {str(e)}",
            "returncode": -1,
            "started_at": started_at,
            "finished_at": time.time(),
        }


def push_project(
    project_name: str,
    config_path: Optional[Path] = None,
    timeout: int = 120,
) -> dict:
    return _run_sync_subprocess("push", project_name, config_path=config_path, timeout=timeout)


def pull_project(
    project_name: str,
    no_restart_worker: bool = True,
    config_path: Optional[Path] = None,
    timeout: int = 120,
) -> dict:
    extra_env = {}
    if no_restart_worker:
        extra_env["MEMBRIDGE_NO_RESTART_WORKER"] = "1"
    return _run_sync_subprocess("pull", project_name, extra_env=extra_env, config_path=config_path, timeout=timeout)


def doctor_project(
    project_name: str,
    config_path: Optional[Path] = None,
    timeout: int = 120,
) -> dict:
    return _run_sync_subprocess("doctor", project_name, config_path=config_path, timeout=timeout)
