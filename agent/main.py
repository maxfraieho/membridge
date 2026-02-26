"""Membridge Agent Daemon v0.4.0 — runs on each machine, executes sync commands.

Supports BLOOM Runtime Control Plane operations:
- Health check with version/OS reporting
- Self-update (git pull + service restart)
- Service restart (systemd/OpenRC)
- Uninstall (stop + cleanup)
- Git repo clone for multi-project management
- Memory sync (push/pull) via hooks
- Auto-registration with BLOOM Runtime on startup
- Heartbeat to Membridge Control Plane
"""

import asyncio
import hashlib
import json
import logging
import os
import platform
import re
import shutil
import signal
import socket
import subprocess
import sys
import time
from contextlib import asynccontextmanager, suppress
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query, Request
from pydantic import BaseModel, Field

from server.auth import AgentAuthMiddleware
from server.logging_config import RequestIDMiddleware, setup_logging

setup_logging("membridge-agent")
logger = logging.getLogger("membridge.agent")

AGENT_VERSION = "0.4.0"
MAX_OUTPUT_LINES = 200

DRYRUN = os.environ.get("MEMBRIDGE_AGENT_DRYRUN", "0") == "1"
HOOKS_BIN = Path(os.environ.get("MEMBRIDGE_HOOKS_BIN", os.path.expanduser("~/.claude-mem-minio/bin")))
CONFIG_ENV = Path(os.environ.get("MEMBRIDGE_CONFIG_ENV", os.path.expanduser("~/.claude-mem-minio/config.env")))
ALLOW_PROCESS_CONTROL = os.environ.get("MEMBRIDGE_ALLOW_PROCESS_CONTROL", "0") == "1"
AGENT_DIR = Path(os.environ.get("MEMBRIDGE_AGENT_DIR", os.path.expanduser("~/membridge")))

HEARTBEAT_INTERVAL = int(os.environ.get("MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS", "10"))
SERVER_URL = os.environ.get("MEMBRIDGE_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
RUNTIME_URL = os.environ.get("BLOOM_RUNTIME_URL", "").rstrip("/")
RUNTIME_API_KEY = os.environ.get("RUNTIME_API_KEY", "")
NODE_ID = os.environ.get("MEMBRIDGE_NODE_ID", platform.node())
AGENT_PORT = int(os.environ.get("MEMBRIDGE_AGENT_PORT", "8001"))
PROJECTS_FILE = Path(
    os.environ.get("MEMBRIDGE_PROJECTS_FILE", os.path.expanduser("~/.membridge/agent_projects.json"))
)
REPOS_BASE = Path(os.environ.get("MEMBRIDGE_REPOS_BASE", os.path.expanduser("~/projects")))


def _detect_init_system() -> str:
    if shutil.which("systemctl"):
        try:
            r = subprocess.run(["systemctl", "--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return "systemd"
        except Exception:
            pass
    if Path("/sbin/openrc").exists() or shutil.which("rc-service"):
        return "openrc"
    return "unknown"


def _detect_os_info() -> str:
    parts = [platform.node()]
    try:
        with open("/etc/os-release") as f:
            for line in f:
                if line.startswith("PRETTY_NAME="):
                    parts.append(line.split("=", 1)[1].strip().strip('"'))
                    break
    except Exception:
        parts.append(f"{platform.system()} {platform.machine()}")
    return " / ".join(parts)


INIT_SYSTEM = _detect_init_system()
OS_INFO = _detect_os_info()
SERVICE_NAME = os.environ.get("MEMBRIDGE_SERVICE_NAME", "membridge-agent")


def _cid(project_id: str) -> str:
    return hashlib.sha256(project_id.encode()).hexdigest()[:16]


def load_projects() -> dict[str, dict]:
    if not PROJECTS_FILE.exists():
        return {}
    try:
        return json.loads(PROJECTS_FILE.read_text())
    except Exception as e:
        logger.warning("failed to load projects from %s: %s", PROJECTS_FILE, e)
        return {}


def save_projects(projects: dict[str, dict]) -> None:
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(projects, indent=2, default=str))


def upsert_project(project_id: str, canonical_id: Optional[str] = None, meta: Optional[dict] = None) -> dict:
    cid = canonical_id or _cid(project_id)
    projects = load_projects()
    entry = projects.get(cid, {
        "project_id": project_id,
        "canonical_id": cid,
        "created_at": time.time(),
    })
    entry.update({"project_id": project_id, "canonical_id": cid, "last_seen": time.time()})
    if meta:
        for k, v in meta.items():
            if v is not None:
                entry[k] = v
    projects[cid] = entry
    save_projects(projects)
    logger.info("upsert_project: project_id=%s canonical_id=%s", project_id, cid)
    return entry


def _get_ip_addrs() -> list[str]:
    addrs: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addr = info[4][0]
            if addr not in ("127.0.0.1",) and addr not in addrs:
                addrs.append(addr)
    except Exception:
        pass
    try:
        r = subprocess.run(
            ["tailscale", "ip", "--4"],
            capture_output=True, text=True, timeout=2,
        )
        if r.returncode == 0:
            ts_ip = r.stdout.strip()
            if ts_ip and ts_ip not in addrs:
                addrs.append(ts_ip)
    except Exception:
        pass
    return addrs


def _get_git_version() -> Optional[str]:
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True, text=True, timeout=5,
            cwd=str(AGENT_DIR),
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def _get_git_commit() -> Optional[str]:
    try:
        r = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=5,
            cwd=str(AGENT_DIR),
        )
        if r.returncode == 0:
            return r.stdout.strip()
    except Exception:
        pass
    return None


def _run_service_command(action: str) -> dict:
    if INIT_SYSTEM == "systemd":
        cmd = ["sudo", "systemctl", action, SERVICE_NAME]
    elif INIT_SYSTEM == "openrc":
        cmd = ["sudo", "rc-service", SERVICE_NAME, action]
    else:
        return {"ok": False, "error": f"Unknown init system: {INIT_SYSTEM}"}

    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return {
            "ok": r.returncode == 0,
            "command": " ".join(cmd),
            "stdout": r.stdout.strip() if r.stdout else "",
            "stderr": r.stderr.strip() if r.stderr else "",
            "returncode": r.returncode,
        }
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": f"Command timed out: {' '.join(cmd)}"}
    except Exception as e:
        return {"ok": False, "error": str(e)}


async def _register_with_runtime() -> None:
    if not RUNTIME_URL:
        logger.info("BLOOM_RUNTIME_URL not set, skipping runtime registration")
        return

    headers: dict[str, str] = {"Content-Type": "application/json"}
    if RUNTIME_API_KEY:
        headers["X-Runtime-API-Key"] = RUNTIME_API_KEY

    ip_addrs = _get_ip_addrs()
    my_url = f"http://{ip_addrs[0]}:{AGENT_PORT}" if ip_addrs else f"http://{NODE_ID}:{AGENT_PORT}"

    payload = {
        "name": NODE_ID,
        "url": my_url,
        "status": "online",
        "capabilities": {
            "claude_cli": shutil.which("claude") is not None,
            "max_concurrency": 2,
            "labels": [INIT_SYSTEM, platform.machine()],
        },
        "ip_addrs": ip_addrs,
        "agent_version": AGENT_VERSION,
        "os_info": OS_INFO,
        "install_method": os.environ.get("MEMBRIDGE_INSTALL_METHOD", "manual"),
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{RUNTIME_URL}/api/runtime/workers",
                json=payload,
                headers=headers,
            )
            if resp.status_code in (200, 201):
                logger.info("registered with BLOOM Runtime: %s as %s", RUNTIME_URL, NODE_ID)
            else:
                logger.warning("runtime registration returned %d: %s", resp.status_code, resp.text[:200])
    except Exception as e:
        logger.warning("failed to register with BLOOM Runtime: %s", e)


async def _heartbeat_loop() -> None:
    server_key = (
        os.environ.get("MEMBRIDGE_SERVER_ADMIN_KEY")
        or os.environ.get("MEMBRIDGE_ADMIN_KEY", "")
    )
    if not server_key:
        logger.warning(
            "heartbeat disabled: set MEMBRIDGE_SERVER_ADMIN_KEY (or MEMBRIDGE_ADMIN_KEY) "
            "so the agent can authenticate with the control-plane"
        )
        return

    headers = {
        "Content-Type": "application/json",
        "X-MEMBRIDGE-ADMIN": server_key,
    }
    backoff = 0
    node_cid = _cid(NODE_ID)

    logger.info(
        "heartbeat loop started: server=%s interval=%ds node_id=%s",
        SERVER_URL, HEARTBEAT_INTERVAL, NODE_ID,
    )

    while True:
        if backoff:
            await asyncio.sleep(backoff)
            backoff = 0
        else:
            await asyncio.sleep(HEARTBEAT_INTERVAL)

        projects = load_projects()
        ip_addrs = _get_ip_addrs()

        if projects:
            payloads = [
                {
                    "node_id": NODE_ID,
                    "canonical_id": p["canonical_id"],
                    "project_id": p["project_id"],
                    "obs_count": p.get("obs_count"),
                    "db_sha": p.get("db_sha"),
                    "last_seen": p.get("last_seen"),
                    "ip_addrs": ip_addrs,
                    "agent_version": AGENT_VERSION,
                }
                for p in projects.values()
            ]
        else:
            payloads = [{
                "node_id": NODE_ID,
                "canonical_id": node_cid,
                "ip_addrs": ip_addrs,
                "agent_version": AGENT_VERSION,
            }]

        consecutive_fails = 0
        async with httpx.AsyncClient(timeout=10.0) as client:
            for payload in payloads:
                try:
                    resp = await client.post(
                        f"{SERVER_URL}/agent/heartbeat",
                        json=payload,
                        headers=headers,
                    )
                    resp.raise_for_status()
                    data = resp.json()
                    logger.debug(
                        "heartbeat ok: project=%s role=%s",
                        payload.get("project_id", "-"), data.get("role", "?"),
                    )
                except Exception as e:
                    consecutive_fails += 1
                    logger.warning(
                        "heartbeat failed (project=%s): %s",
                        payload.get("project_id", "-"), e,
                    )

        if consecutive_fails:
            backoff = min(60, HEARTBEAT_INTERVAL * (2 ** min(consecutive_fails - 1, 3)))
            logger.info("heartbeat backoff: %ds (%d failures)", backoff, consecutive_fails)


@asynccontextmanager
async def lifespan(app: FastAPI):
    heartbeat_task = asyncio.create_task(_heartbeat_loop())
    registration_task = asyncio.create_task(_register_with_runtime())
    yield
    heartbeat_task.cancel()
    registration_task.cancel()
    with suppress(asyncio.CancelledError):
        await heartbeat_task
    with suppress(asyncio.CancelledError):
        await registration_task


app = FastAPI(
    title="Membridge Agent",
    description="Agent daemon for executing Claude memory sync and fleet management on this machine",
    version=AGENT_VERSION,
    lifespan=lifespan,
)

app.add_middleware(AgentAuthMiddleware)
app.add_middleware(RequestIDMiddleware)


def canonical_id(project_name: str) -> str:
    return hashlib.sha256(project_name.encode()).hexdigest()[:16]


def _tail_lines(text: str, max_lines: int = MAX_OUTPUT_LINES) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text
    return "\n".join([f"... ({len(lines) - max_lines} lines truncated)"] + lines[-max_lines:])


def _load_config_env() -> dict[str, str]:
    env = {}
    if CONFIG_ENV.exists():
        for line in CONFIG_ENV.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


def _build_env(project: str) -> dict[str, str]:
    env = os.environ.copy()
    config = _load_config_env()
    env.update(config)
    env["CLAUDE_PROJECT_ID"] = project
    if "CLAUDE_CANONICAL_PROJECT_ID" in env:
        del env["CLAUDE_CANONICAL_PROJECT_ID"]
    return env


class SyncAction(str, Enum):
    pull = "pull"
    push = "push"
    status = "status"
    doctor = "doctor"


class SyncRequest(BaseModel):
    project: str = Field(..., examples=["garden-seedling"])
    no_restart_worker: bool = Field(default=True, description="Do not restart worker after pull (safe default)")


class SyncResponse(BaseModel):
    ok: bool
    action: str
    project: str
    canonical_id: str
    hostname: str
    detail: str
    dryrun: bool = False
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None


class StatusResponse(BaseModel):
    ok: bool
    project: str
    canonical_id: str
    hostname: str
    detail: str
    dryrun: bool = False
    config_env_exists: bool = False
    hooks_bin_exists: bool = False
    db_exists: bool = False
    db_path: Optional[str] = None


def _find_script(action: SyncAction) -> Path:
    mapping = {
        SyncAction.pull: "claude-mem-pull",
        SyncAction.push: "claude-mem-push",
        SyncAction.status: "claude-mem-status",
        SyncAction.doctor: "claude-mem-doctor",
    }
    return HOOKS_BIN / mapping[action]


def _run_sync(action: SyncAction, project: str, extra_env: dict | None = None) -> SyncResponse:
    hostname = platform.node()
    cid = canonical_id(project)

    if DRYRUN:
        logger.info("[DRYRUN] %s project=%s canonical_id=%s", action.value, project, cid)
        return SyncResponse(
            ok=True,
            action=action.value,
            project=project,
            canonical_id=cid,
            hostname=hostname,
            detail=f"[DRYRUN] Would execute {action.value} for project '{project}' (canonical_id={cid})",
            dryrun=True,
        )

    script = _find_script(action)
    if not script.exists():
        raise HTTPException(
            status_code=500,
            detail=f"Script not found: {script}. Install hooks first: cp hooks/* {HOOKS_BIN}/",
        )
    if not os.access(script, os.X_OK):
        raise HTTPException(
            status_code=500,
            detail=f"Script not executable: {script}. Run: chmod +x {script}",
        )

    env = _build_env(project)
    if extra_env:
        env.update(extra_env)

    logger.info("executing %s project=%s script=%s", action.value, project, script)
    try:
        result = subprocess.run(
            [str(script), "--project", project],
            capture_output=True,
            text=True,
            timeout=120,
            env=env,
        )
        stdout_tail = _tail_lines(result.stdout) if result.stdout else None
        stderr_tail = _tail_lines(result.stderr) if result.stderr else None
        logger.info("%s project=%s rc=%d", action.value, project, result.returncode)
        return SyncResponse(
            ok=result.returncode == 0,
            action=action.value,
            project=project,
            canonical_id=cid,
            hostname=hostname,
            detail=f"{action.value} {'completed' if result.returncode == 0 else 'failed'}",
            stdout=stdout_tail,
            stderr=stderr_tail,
            returncode=result.returncode,
        )
    except subprocess.TimeoutExpired:
        logger.error("%s project=%s timed out", action.value, project)
        return SyncResponse(
            ok=False,
            action=action.value,
            project=project,
            canonical_id=cid,
            hostname=hostname,
            detail=f"{action.value} timed out after 120s",
        )
    except Exception as e:
        logger.exception("failed to execute %s", action.value)
        raise HTTPException(status_code=500, detail=f"Failed to execute {action.value}: {str(e)}")


@app.get("/health")
async def health():
    git_version = _get_git_version()
    git_commit = _get_git_commit()
    disk_usage = None
    try:
        usage = shutil.disk_usage(str(AGENT_DIR))
        disk_usage = {
            "total_gb": round(usage.total / (1024**3), 1),
            "free_gb": round(usage.free / (1024**3), 1),
            "used_pct": round((usage.used / usage.total) * 100, 1),
        }
    except Exception:
        pass

    return {
        "status": "ok",
        "service": "membridge-agent",
        "version": AGENT_VERSION,
        "git_version": git_version,
        "git_commit": git_commit,
        "hostname": platform.node(),
        "node_id": NODE_ID,
        "os_info": OS_INFO,
        "arch": platform.machine(),
        "python": platform.python_version(),
        "init_system": INIT_SYSTEM,
        "dryrun": DRYRUN,
        "allow_process_control": ALLOW_PROCESS_CONTROL,
        "hooks_bin": str(HOOKS_BIN),
        "config_env": str(CONFIG_ENV),
        "agent_dir": str(AGENT_DIR),
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "server_url": SERVER_URL,
        "runtime_url": RUNTIME_URL or None,
        "projects_count": len(load_projects()),
        "uptime_seconds": round(time.time() - _START_TIME, 1),
        "disk": disk_usage,
        "capabilities": {
            "self_update": True,
            "restart": True,
            "uninstall": True,
            "clone": True,
            "sync": True,
            "process_control": ALLOW_PROCESS_CONTROL,
        },
    }


_START_TIME = time.time()


@app.get("/status", response_model=StatusResponse)
async def status(project: str = Query(..., examples=["garden-seedling"])):
    hostname = platform.node()
    cid = canonical_id(project)

    config = _load_config_env()
    db_path = config.get("CLAUDE_MEM_DB", os.path.expanduser("~/.claude-mem/claude-mem.db"))
    db_path = db_path.replace("$HOME", os.path.expanduser("~"))
    db_exists = os.path.exists(db_path)

    if DRYRUN:
        return StatusResponse(
            ok=True, project=project, canonical_id=cid, hostname=hostname,
            detail=f"[DRYRUN] Status for project '{project}'", dryrun=True,
            config_env_exists=CONFIG_ENV.exists(), hooks_bin_exists=HOOKS_BIN.exists(),
            db_exists=db_exists, db_path=db_path,
        )

    if not CONFIG_ENV.exists():
        return StatusResponse(
            ok=False, project=project, canonical_id=cid, hostname=hostname,
            detail=f"config.env not found at {CONFIG_ENV}. Run bootstrap first.",
            config_env_exists=False, hooks_bin_exists=HOOKS_BIN.exists(),
            db_exists=db_exists, db_path=db_path,
        )

    return StatusResponse(
        ok=True, project=project, canonical_id=cid, hostname=hostname,
        detail="Agent ready", config_env_exists=True, hooks_bin_exists=HOOKS_BIN.exists(),
        db_exists=db_exists, db_path=db_path,
    )


class RegisterProjectRequest(BaseModel):
    project_id: str = Field(..., min_length=1, max_length=128, examples=["garden-seedling"])
    canonical_id: Optional[str] = Field(
        default=None,
        description="If omitted, computed as sha256(project_id)[:16]",
    )
    path: Optional[str] = Field(default=None, description="Local filesystem path for this project")
    notes: Optional[str] = Field(default=None, description="Free-form notes")


@app.post("/register_project")
async def register_project(body: RegisterProjectRequest):
    entry = upsert_project(
        project_id=body.project_id,
        canonical_id=body.canonical_id,
        meta={"path": body.path, "notes": body.notes},
    )
    return {
        "ok": True,
        "project_id": entry["project_id"],
        "canonical_id": entry["canonical_id"],
        "projects_count": len(load_projects()),
    }


@app.get("/projects")
async def list_agent_projects():
    return list(load_projects().values())


@app.post("/sync/pull", response_model=SyncResponse)
async def sync_pull(body: SyncRequest):
    extra_env = {}
    if body.no_restart_worker:
        extra_env["MEMBRIDGE_NO_RESTART_WORKER"] = "1"
    return _run_sync(SyncAction.pull, body.project, extra_env=extra_env)


@app.post("/sync/push", response_model=SyncResponse)
async def sync_push(body: SyncRequest):
    return _run_sync(SyncAction.push, body.project)


@app.get("/doctor")
async def doctor(project: str = Query(..., examples=["garden-seedling"])):
    return _run_sync(SyncAction.doctor, project)


@app.post("/pull", response_model=SyncResponse)
async def pull_alias(body: SyncRequest):
    extra_env = {}
    if body.no_restart_worker:
        extra_env["MEMBRIDGE_NO_RESTART_WORKER"] = "1"
    return _run_sync(SyncAction.pull, body.project, extra_env=extra_env)


@app.post("/push", response_model=SyncResponse)
async def push_alias(body: SyncRequest):
    return _run_sync(SyncAction.push, body.project)


class DoctorRequest(BaseModel):
    project: str = Field(..., examples=["garden-seedling"])


@app.post("/doctor", response_model=SyncResponse)
async def doctor_post(body: DoctorRequest):
    return _run_sync(SyncAction.doctor, body.project)


def _require_process_control():
    if not ALLOW_PROCESS_CONTROL:
        raise HTTPException(
            status_code=403,
            detail="Process control is disabled. Set MEMBRIDGE_ALLOW_PROCESS_CONTROL=1 to enable.",
        )


class SelfUpdateRequest(BaseModel):
    repo_url: Optional[str] = Field(default=None, description="Git remote URL (defaults to origin)")
    branch: Optional[str] = Field(default=None, description="Branch to pull (defaults to current)")


@app.post("/self-update")
async def self_update(body: SelfUpdateRequest):
    _require_process_control()
    logger.info("self-update requested")

    if DRYRUN:
        return {"ok": True, "dryrun": True, "detail": "[DRYRUN] Would execute self-update"}

    agent_dir = AGENT_DIR
    if not (agent_dir / ".git").exists():
        raise HTTPException(status_code=500, detail=f"Not a git repo: {agent_dir}")

    steps: list[dict] = []

    try:
        fetch_cmd = ["git", "fetch", "--all"]
        r = subprocess.run(fetch_cmd, capture_output=True, text=True, timeout=60, cwd=str(agent_dir))
        steps.append({"step": "fetch", "ok": r.returncode == 0, "output": r.stdout.strip()})
    except Exception as e:
        steps.append({"step": "fetch", "ok": False, "error": str(e)})

    try:
        if body.branch:
            pull_cmd = ["git", "pull", "origin", body.branch]
        else:
            pull_cmd = ["git", "pull"]
        r = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=120, cwd=str(agent_dir))
        steps.append({
            "step": "pull",
            "ok": r.returncode == 0,
            "output": _tail_lines(r.stdout.strip(), 50),
            "stderr": _tail_lines(r.stderr.strip(), 20) if r.stderr.strip() else None,
        })
        if r.returncode != 0:
            return {"ok": False, "steps": steps, "detail": "git pull failed"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "steps": steps, "detail": "git pull timed out"}

    pip_req = agent_dir / "requirements.txt"
    if pip_req.exists():
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pip", "install", "-r", str(pip_req), "--quiet"],
                capture_output=True, text=True, timeout=120, cwd=str(agent_dir),
            )
            steps.append({"step": "pip_install", "ok": r.returncode == 0})
        except Exception as e:
            steps.append({"step": "pip_install", "ok": False, "error": str(e)})

    new_commit = _get_git_commit()
    steps.append({"step": "new_commit", "commit": new_commit})

    restart_result = _run_service_command("restart")
    steps.append({"step": "restart", **restart_result})

    return {
        "ok": all(s.get("ok", True) for s in steps),
        "version": AGENT_VERSION,
        "new_commit": new_commit,
        "steps": steps,
        "detail": "Self-update completed",
    }


@app.post("/restart")
async def restart_service():
    _require_process_control()
    logger.info("restart requested")

    if DRYRUN:
        return {"ok": True, "dryrun": True, "detail": "[DRYRUN] Would restart service"}

    result = _run_service_command("restart")

    if not result["ok"] and INIT_SYSTEM == "unknown":
        logger.info("no init system detected, sending SIGHUP to self")
        os.kill(os.getpid(), signal.SIGHUP)
        return {
            "ok": True,
            "method": "sighup",
            "detail": "Sent SIGHUP to self (no init system detected)",
        }

    return {
        "ok": result["ok"],
        "init_system": INIT_SYSTEM,
        "service": SERVICE_NAME,
        "detail": "Service restart " + ("completed" if result["ok"] else "failed"),
        **result,
    }


@app.post("/uninstall")
async def uninstall():
    _require_process_control()
    logger.warning("uninstall requested for node %s", NODE_ID)

    if DRYRUN:
        return {"ok": True, "dryrun": True, "detail": "[DRYRUN] Would uninstall agent"}

    steps: list[dict] = []

    stop_result = _run_service_command("stop")
    steps.append({"step": "stop_service", **stop_result})

    if INIT_SYSTEM == "systemd":
        try:
            r = subprocess.run(
                ["sudo", "systemctl", "disable", SERVICE_NAME],
                capture_output=True, text=True, timeout=15,
            )
            steps.append({"step": "disable_service", "ok": r.returncode == 0})
        except Exception as e:
            steps.append({"step": "disable_service", "ok": False, "error": str(e)})

        unit_file = Path(f"/etc/systemd/system/{SERVICE_NAME}.service")
        if unit_file.exists():
            try:
                unit_file.unlink()
                subprocess.run(["sudo", "systemctl", "daemon-reload"], capture_output=True, timeout=10)
                steps.append({"step": "remove_unit", "ok": True})
            except Exception as e:
                steps.append({"step": "remove_unit", "ok": False, "error": str(e)})
    elif INIT_SYSTEM == "openrc":
        try:
            r = subprocess.run(
                ["sudo", "rc-update", "del", SERVICE_NAME, "default"],
                capture_output=True, text=True, timeout=15,
            )
            steps.append({"step": "disable_service", "ok": r.returncode == 0})
        except Exception as e:
            steps.append({"step": "disable_service", "ok": False, "error": str(e)})

    return {
        "ok": all(s.get("ok", True) for s in steps),
        "node_id": NODE_ID,
        "init_system": INIT_SYSTEM,
        "steps": steps,
        "detail": "Agent uninstalled (service stopped and disabled)",
    }


class CloneRequest(BaseModel):
    repo_url: str = Field(..., description="Git repository URL")
    project_name: str = Field(..., description="Project name for identification")
    target_path: Optional[str] = Field(default=None, description="Target directory (defaults to ~/projects/<name>)")
    branch: Optional[str] = Field(default=None, description="Branch to clone")


@app.post("/clone")
async def clone_repo(body: CloneRequest):
    logger.info("clone requested: repo=%s project=%s", body.repo_url, body.project_name)

    if DRYRUN:
        return {"ok": True, "dryrun": True, "detail": f"[DRYRUN] Would clone {body.repo_url}"}

    if not re.match(r'^[a-zA-Z0-9_.-]+$', body.project_name):
        raise HTTPException(status_code=400, detail="Invalid project name: only alphanumeric, _, -, . allowed")

    if not re.match(r'^(https?://|git@|ssh://)', body.repo_url):
        raise HTTPException(status_code=400, detail="Invalid repo URL: must use https://, git@, or ssh:// scheme")

    if body.target_path:
        target = Path(body.target_path).expanduser().resolve()
        repos_resolved = REPOS_BASE.resolve()
        if not str(target).startswith(str(repos_resolved)):
            raise HTTPException(
                status_code=400,
                detail=f"Target path must be within {repos_resolved}",
            )
    else:
        target = REPOS_BASE / body.project_name

    target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and (target / ".git").exists():
        logger.info("repo already exists at %s, pulling instead", target)
        try:
            r = subprocess.run(
                ["git", "pull"],
                capture_output=True, text=True, timeout=120,
                cwd=str(target),
            )
            upsert_project(
                project_id=body.project_name,
                meta={"path": str(target), "repo_url": body.repo_url},
            )
            return {
                "ok": r.returncode == 0,
                "action": "pull",
                "path": str(target),
                "project_name": body.project_name,
                "stdout": _tail_lines(r.stdout, 30) if r.stdout else None,
                "stderr": _tail_lines(r.stderr, 10) if r.stderr else None,
                "detail": "Existing repo updated via git pull",
            }
        except subprocess.TimeoutExpired:
            raise HTTPException(status_code=504, detail="git pull timed out")
    elif target.exists():
        raise HTTPException(
            status_code=409,
            detail=f"Target path exists but is not a git repo: {target}",
        )

    clone_cmd = ["git", "clone"]
    if body.branch:
        clone_cmd.extend(["--branch", body.branch])
    clone_cmd.extend([body.repo_url, str(target)])

    try:
        r = subprocess.run(
            clone_cmd,
            capture_output=True, text=True, timeout=300,
        )

        if r.returncode == 0:
            upsert_project(
                project_id=body.project_name,
                meta={"path": str(target), "repo_url": body.repo_url},
            )

        return {
            "ok": r.returncode == 0,
            "action": "clone",
            "path": str(target),
            "project_name": body.project_name,
            "stdout": _tail_lines(r.stdout, 30) if r.stdout else None,
            "stderr": _tail_lines(r.stderr, 10) if r.stderr else None,
            "detail": "Cloned" if r.returncode == 0 else f"Clone failed (rc={r.returncode})",
        }
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="git clone timed out after 300s")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Clone failed: {str(e)}")


@app.get("/repos")
async def list_repos():
    repos = []
    if REPOS_BASE.exists():
        for entry in sorted(REPOS_BASE.iterdir()):
            if entry.is_dir() and (entry / ".git").exists():
                try:
                    r = subprocess.run(
                        ["git", "log", "--oneline", "-1"],
                        capture_output=True, text=True, timeout=5,
                        cwd=str(entry),
                    )
                    last_commit = r.stdout.strip() if r.returncode == 0 else None
                except Exception:
                    last_commit = None
                repos.append({
                    "name": entry.name,
                    "path": str(entry),
                    "last_commit": last_commit,
                })
    return repos


@app.get("/system-info")
async def system_info():
    info: dict = {
        "hostname": platform.node(),
        "node_id": NODE_ID,
        "os": OS_INFO,
        "arch": platform.machine(),
        "python": platform.python_version(),
        "init_system": INIT_SYSTEM,
        "agent_version": AGENT_VERSION,
        "agent_dir": str(AGENT_DIR),
        "repos_base": str(REPOS_BASE),
    }

    try:
        r = subprocess.run(["uptime", "-p"], capture_output=True, text=True, timeout=5)
        info["uptime"] = r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        info["uptime"] = None

    try:
        r = subprocess.run(["free", "-m"], capture_output=True, text=True, timeout=5)
        if r.returncode == 0:
            lines = r.stdout.strip().splitlines()
            if len(lines) >= 2:
                parts = lines[1].split()
                info["memory_mb"] = {"total": int(parts[1]), "used": int(parts[2]), "free": int(parts[3])}
    except Exception:
        info["memory_mb"] = None

    try:
        usage = shutil.disk_usage(str(AGENT_DIR))
        info["disk_gb"] = {
            "total": round(usage.total / (1024**3), 1),
            "free": round(usage.free / (1024**3), 1),
        }
    except Exception:
        info["disk_gb"] = None

    try:
        r = subprocess.run(["claude", "--version"], capture_output=True, text=True, timeout=5)
        info["claude_cli"] = r.stdout.strip() if r.returncode == 0 else None
    except Exception:
        info["claude_cli"] = None

    return info


SESSIONS_DIR = Path(os.environ.get("MEMBRIDGE_SESSIONS_DIR", os.path.expanduser("~/.membridge/sessions")))
SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_file(context_id: str) -> Path:
    safe_id = re.sub(r'[^a-zA-Z0-9_.-]', '_', context_id)
    return SESSIONS_DIR / f"{safe_id}.json"


def _load_session(context_id: str) -> dict:
    sf = _session_file(context_id)
    if sf.exists():
        try:
            return json.loads(sf.read_text())
        except Exception:
            pass
    return {"context_id": context_id, "messages": [], "created_at": time.time()}


def _save_session(context_id: str, session: dict) -> None:
    sf = _session_file(context_id)
    sf.write_text(json.dumps(session, indent=2, default=str))


class ExecuteTaskRequest(BaseModel):
    task_id: str = Field(..., description="BLOOM Runtime task ID")
    prompt: str = Field(..., description="The prompt/instruction for Claude CLI")
    context_id: str = Field(..., description="Context ID for session persistence")
    agent_slug: str = Field(default="default", description="Agent persona/slug")
    desired_format: str = Field(default="text", description="Output format: text or json")
    context_hints: list[str] = Field(default_factory=list, description="Context hints for the prompt")
    policy: dict = Field(default_factory=lambda: {"timeout_sec": 120, "budget": 0})
    runtime_url: Optional[str] = Field(default=None, description="BLOOM Runtime URL for callbacks")


@app.post("/execute-task")
async def execute_task(body: ExecuteTaskRequest):
    logger.info("execute-task: task_id=%s context_id=%s agent_slug=%s", body.task_id, body.context_id, body.agent_slug)

    if not shutil.which("claude"):
        raise HTTPException(status_code=503, detail="Claude CLI is not installed on this node")

    if DRYRUN:
        return {
            "ok": True,
            "dryrun": True,
            "task_id": body.task_id,
            "detail": f"[DRYRUN] Would execute Claude CLI for task {body.task_id}",
        }

    session = _load_session(body.context_id)
    timeout = body.policy.get("timeout_sec", 120)

    cmd = ["claude", "--print"]

    if body.desired_format == "json":
        cmd.extend(["--output-format", "json"])

    if body.context_hints:
        hints_text = "\n".join(f"- {h}" for h in body.context_hints)
        full_prompt = f"Context:\n{hints_text}\n\n{body.prompt}"
    else:
        full_prompt = body.prompt

    if session["messages"]:
        recent = session["messages"][-10:]
        history = "\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content'][:500]}"
            for m in recent
        )
        full_prompt = f"Previous conversation context:\n{history}\n\n---\n\nCurrent request:\n{full_prompt}"

    cmd.extend(["-p", full_prompt])

    env = os.environ.copy()
    if body.agent_slug and body.agent_slug != "default":
        env["CLAUDE_PROJECT_ID"] = body.agent_slug

    start_time = time.time()

    runtime_url = body.runtime_url or RUNTIME_URL
    runtime_key = RUNTIME_API_KEY

    async def _send_heartbeat():
        if not runtime_url:
            return
        try:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if runtime_key:
                headers["X-Runtime-API-Key"] = runtime_key
            async with httpx.AsyncClient(timeout=5.0) as client:
                await client.post(
                    f"{runtime_url}/api/runtime/llm-tasks/{body.task_id}/heartbeat",
                    headers=headers,
                )
        except Exception as e:
            logger.debug("heartbeat for task %s failed: %s", body.task_id, e)

    async def _complete_task(status: str, output: str | None, error_message: str | None, duration_ms: int, tokens: int | None = None):
        if not runtime_url:
            return
        try:
            headers: dict[str, str] = {"Content-Type": "application/json"}
            if runtime_key:
                headers["X-Runtime-API-Key"] = runtime_key
            payload = {
                "status": status,
                "output": output,
                "error_message": error_message,
                "metrics": {"duration_ms": duration_ms, "tokens_used": tokens},
            }
            async with httpx.AsyncClient(timeout=30.0) as client:
                await client.post(
                    f"{runtime_url}/api/runtime/llm-tasks/{body.task_id}/complete",
                    json=payload,
                    headers=headers,
                )
                logger.info("task %s completed callback sent: %s", body.task_id, status)
        except Exception as e:
            logger.warning("complete callback for task %s failed: %s", body.task_id, e)

    try:
        await _send_heartbeat()

        loop = asyncio.get_event_loop()
        result = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    env=env,
                    cwd=str(AGENT_DIR),
                ),
            ),
            timeout=timeout + 10,
        )

        duration_ms = int((time.time() - start_time) * 1000)
        output = result.stdout.strip() if result.stdout else ""
        stderr = result.stderr.strip() if result.stderr else ""

        session["messages"].append({"role": "user", "content": body.prompt, "ts": time.time()})
        if output:
            session["messages"].append({"role": "assistant", "content": output[:2000], "ts": time.time()})
        session["last_used"] = time.time()
        session["total_tasks"] = session.get("total_tasks", 0) + 1
        _save_session(body.context_id, session)

        if result.returncode == 0:
            await _complete_task("success", output, None, duration_ms)
            return {
                "ok": True,
                "task_id": body.task_id,
                "output": _tail_lines(output, MAX_OUTPUT_LINES),
                "duration_ms": duration_ms,
                "returncode": result.returncode,
                "context_id": body.context_id,
                "session_messages": len(session["messages"]),
                "detail": "Claude CLI execution completed",
            }
        else:
            error_msg = stderr or f"Claude CLI returned exit code {result.returncode}"
            await _complete_task("error", None, error_msg, duration_ms)
            return {
                "ok": False,
                "task_id": body.task_id,
                "error": error_msg,
                "stdout": _tail_lines(output, 50) if output else None,
                "stderr": _tail_lines(stderr, 50),
                "duration_ms": duration_ms,
                "returncode": result.returncode,
                "detail": "Claude CLI execution failed",
            }

    except (asyncio.TimeoutError, subprocess.TimeoutExpired):
        duration_ms = int((time.time() - start_time) * 1000)
        await _complete_task("error", None, f"Timed out after {timeout}s", duration_ms)
        return {
            "ok": False,
            "task_id": body.task_id,
            "error": f"Claude CLI timed out after {timeout}s",
            "duration_ms": duration_ms,
            "detail": "Execution timed out",
        }
    except Exception as e:
        duration_ms = int((time.time() - start_time) * 1000)
        error_msg = str(e)
        await _complete_task("error", None, error_msg, duration_ms)
        logger.exception("execute-task failed: task_id=%s", body.task_id)
        raise HTTPException(status_code=500, detail=f"Execution failed: {error_msg}")


@app.get("/sessions")
async def list_sessions():
    sessions = []
    if SESSIONS_DIR.exists():
        for f in sorted(SESSIONS_DIR.iterdir()):
            if f.suffix == ".json":
                try:
                    data = json.loads(f.read_text())
                    sessions.append({
                        "context_id": data.get("context_id", f.stem),
                        "messages_count": len(data.get("messages", [])),
                        "total_tasks": data.get("total_tasks", 0),
                        "created_at": data.get("created_at"),
                        "last_used": data.get("last_used"),
                    })
                except Exception:
                    pass
    return sessions


@app.get("/sessions/{context_id}")
async def get_session(context_id: str):
    session = _load_session(context_id)
    if not session.get("messages"):
        raise HTTPException(status_code=404, detail=f"Session not found: {context_id}")
    return session


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=AGENT_PORT)
