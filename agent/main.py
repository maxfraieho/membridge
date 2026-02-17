"""Membridge Agent Daemon — runs on each machine, executes sync commands."""

import hashlib
import logging
import os
import platform
import subprocess
import time
from enum import Enum
from pathlib import Path
from typing import Optional

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

app = FastAPI(
    title="Membridge Agent",
    description="Agent daemon for executing Claude memory sync on this machine",
    version="0.2.0",
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
    return {
        "status": "ok",
        "service": "membridge-agent",
        "version": "0.2.0",
        "hostname": platform.node(),
        "dryrun": DRYRUN,
        "hooks_bin": str(HOOKS_BIN),
        "config_env": str(CONFIG_ENV),
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
