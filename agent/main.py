"""Membridge Agent Daemon — runs on each machine, executes sync commands."""

import asyncio
import hashlib
import json
import logging
import os
import platform
import socket
import subprocess
import time
from contextlib import asynccontextmanager, suppress
from enum import Enum
from pathlib import Path
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from server.auth import AgentAuthMiddleware
from server.logging_config import RequestIDMiddleware, setup_logging

setup_logging("membridge-agent")
logger = logging.getLogger("membridge.agent")

MAX_OUTPUT_LINES = 200

DRYRUN = os.environ.get("MEMBRIDGE_AGENT_DRYRUN", "0") == "1"
HOOKS_BIN = Path(os.environ.get("MEMBRIDGE_HOOKS_BIN", os.path.expanduser("~/.claude-mem-minio/bin")))
CONFIG_ENV = Path(os.environ.get("MEMBRIDGE_CONFIG_ENV", os.path.expanduser("~/.claude-mem-minio/config.env")))
ALLOW_PROCESS_CONTROL = os.environ.get("MEMBRIDGE_ALLOW_PROCESS_CONTROL", "0") == "1"

# ── Heartbeat / auto-registration config ─────────────────────────────────────
HEARTBEAT_INTERVAL = int(os.environ.get("MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS", "10"))
SERVER_URL = os.environ.get("MEMBRIDGE_SERVER_URL", "http://127.0.0.1:8000").rstrip("/")
NODE_ID = os.environ.get("MEMBRIDGE_NODE_ID", platform.node())
PROJECTS_FILE = Path(
    os.environ.get("MEMBRIDGE_PROJECTS_FILE", os.path.expanduser("~/.membridge/agent_projects.json"))
)


# ── Project storage ───────────────────────────────────────────────────────────

def _cid(project_id: str) -> str:
    return hashlib.sha256(project_id.encode()).hexdigest()[:16]


def load_projects() -> dict[str, dict]:
    """Load projects registry from disk. Returns {canonical_id: project_dict}."""
    if not PROJECTS_FILE.exists():
        return {}
    try:
        return json.loads(PROJECTS_FILE.read_text())
    except Exception as e:
        logger.warning("failed to load projects from %s: %s", PROJECTS_FILE, e)
        return {}


def save_projects(projects: dict[str, dict]) -> None:
    """Persist projects registry to disk."""
    PROJECTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROJECTS_FILE.write_text(json.dumps(projects, indent=2, default=str))


def upsert_project(project_id: str, canonical_id: Optional[str] = None, meta: Optional[dict] = None) -> dict:
    """Add or update a project in the local registry. Returns the entry."""
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


# ── IP address collection ─────────────────────────────────────────────────────

def _get_ip_addrs() -> list[str]:
    """Collect LAN and Tailscale IPs, best-effort."""
    addrs: list[str] = []
    try:
        hostname = socket.gethostname()
        for info in socket.getaddrinfo(hostname, None, socket.AF_INET):
            addr = info[4][0]
            if addr not in ("127.0.0.1",) and addr not in addrs:
                addrs.append(addr)
    except Exception:
        pass
    # Tailscale (100.x.y.z) — best-effort
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


# ── Heartbeat loop ────────────────────────────────────────────────────────────

async def _heartbeat_loop() -> None:
    """Background task: send a heartbeat to the control-plane for each known project."""
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
    backoff = 0  # seconds to wait after a failure
    node_cid = _cid(NODE_ID)  # used when no projects registered yet

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

        # Build list of payloads: one per project, or one node-alive if no projects
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
                    "agent_version": "0.3.0",
                }
                for p in projects.values()
            ]
        else:
            # No projects yet — still announce node presence
            payloads = [{
                "node_id": NODE_ID,
                "canonical_id": node_cid,
                "ip_addrs": ip_addrs,
                "agent_version": "0.3.0",
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


# ── FastAPI lifespan ──────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_heartbeat_loop())
    yield
    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


# ── App ───────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Membridge Agent",
    description="Agent daemon for executing Claude memory sync on this machine",
    version="0.3.0",
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


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "membridge-agent",
        "version": "0.3.0",
        "hostname": platform.node(),
        "node_id": NODE_ID,
        "dryrun": DRYRUN,
        "allow_process_control": ALLOW_PROCESS_CONTROL,
        "hooks_bin": str(HOOKS_BIN),
        "config_env": str(CONFIG_ENV),
        "heartbeat_interval": HEARTBEAT_INTERVAL,
        "server_url": SERVER_URL,
        "projects_count": len(load_projects()),
    }


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
    """Register a project in the local agent registry (persisted to disk).

    Callable from localhost without auth key (hooks, scripts).
    canonical_id is auto-computed from project_id if not provided.
    """
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
    """List all projects registered in this agent's local registry."""
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
