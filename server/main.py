"""Membridge Control Plane — FastAPI server for managing projects and agents."""

import hashlib
import logging
import os
import time
from enum import Enum
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel, Field

from server.auth import AdminAuthMiddleware
from server.logging_config import RequestIDMiddleware, setup_logging, request_id_var
from server.jobs import Job, create_job, finish_job, get_job, list_jobs

setup_logging("membridge-server")
logger = logging.getLogger("membridge.server")

app = FastAPI(
    title="Membridge Control Plane",
    description="Centralized API for managing Claude memory sync projects and agents",
    version="0.3.0",
)

app.add_middleware(AdminAuthMiddleware)
app.add_middleware(RequestIDMiddleware)


def canonical_id(project_name: str) -> str:
    return hashlib.sha256(project_name.encode()).hexdigest()[:16]


class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, examples=["garden-seedling"])


class Project(BaseModel):
    name: str
    canonical_id: str
    created_at: float


class AgentCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=128, examples=["orangepipc2"])
    url: str = Field(..., examples=["http://192.168.1.50:8011"])


class AgentStatus(str, Enum):
    unknown = "unknown"
    online = "online"
    offline = "offline"
    syncing = "syncing"
    error = "error"


class Agent(BaseModel):
    name: str
    url: str
    status: AgentStatus = AgentStatus.unknown
    registered_at: float
    last_seen: Optional[float] = None


class SyncRequest(BaseModel):
    project: str = Field(..., examples=["garden-seedling"])
    agent: str = Field(..., examples=["orangepipc2"])


class SyncResponse(BaseModel):
    ok: bool
    project: str
    agent: str
    canonical_id: str
    detail: str
    job_id: Optional[str] = None


_projects: dict[str, Project] = {}
_agents: dict[str, Agent] = {}

# Leadership / node registry (in-memory; populated by heartbeats)
_nodes: dict[str, "NodeRecord"] = {}
_leadership_pref: dict[str, str] = {}  # canonical_id → preferred primary_node_id


class NodeHeartbeat(BaseModel):
    node_id: str
    canonical_id: str
    obs_count: Optional[int] = None
    db_sha: Optional[str] = None
    last_seen: Optional[float] = None
    ip_addrs: list[str] = []


class NodeRecord(BaseModel):
    node_id: str
    canonical_id: str
    role: str = "unknown"
    obs_count: Optional[int] = None
    db_sha: Optional[str] = None
    last_seen: float
    ip_addrs: list[str] = []
    registered_at: float


class LeaseSelectRequest(BaseModel):
    primary_node_id: str
    lease_seconds: Optional[int] = 3600


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "membridge-control-plane",
        "version": "0.3.0",
        "projects": len(_projects),
        "agents": len(_agents),
    }


@app.get("/projects", response_model=list[Project])
async def list_projects_endpoint():
    return list(_projects.values())


@app.post("/projects", response_model=Project, status_code=201)
async def create_project(body: ProjectCreate):
    if body.name in _projects:
        raise HTTPException(status_code=409, detail=f"Project '{body.name}' already exists")
    proj = Project(
        name=body.name,
        canonical_id=canonical_id(body.name),
        created_at=time.time(),
    )
    _projects[body.name] = proj
    logger.info("project created: %s (canonical_id=%s)", body.name, proj.canonical_id)
    return proj


@app.delete("/projects/{name}", status_code=204)
async def delete_project(name: str):
    if name not in _projects:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    del _projects[name]
    logger.info("project deleted: %s", name)


@app.get("/agents", response_model=list[Agent])
async def list_agents_endpoint():
    return list(_agents.values())


@app.post("/agents", response_model=Agent, status_code=201)
async def register_agent(body: AgentCreate):
    if body.name in _agents:
        raise HTTPException(status_code=409, detail=f"Agent '{body.name}' already registered")
    agent = Agent(
        name=body.name,
        url=body.url.rstrip("/"),
        registered_at=time.time(),
    )
    _agents[body.name] = agent
    logger.info("agent registered: %s → %s", body.name, agent.url)
    return agent


@app.delete("/agents/{name}", status_code=204)
async def unregister_agent(name: str):
    if name not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    del _agents[name]
    logger.info("agent unregistered: %s", name)


async def _call_agent(agent: Agent, method: str, path: str, json_body: dict | None = None) -> dict:
    url = f"{agent.url}{path}"
    headers = {}
    agent_key = os.environ.get("MEMBRIDGE_AGENT_KEY", "")
    if agent_key:
        headers["X-MEMBRIDGE-AGENT"] = agent_key
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if method == "GET":
                resp = await client.get(url, headers=headers)
            else:
                resp = await client.post(url, json=json_body, headers=headers)
            resp.raise_for_status()
            agent.last_seen = time.time()
            agent.status = AgentStatus.online
            return resp.json()
        except httpx.ConnectError:
            agent.status = AgentStatus.offline
            raise HTTPException(status_code=502, detail=f"Agent '{agent.name}' unreachable at {agent.url}")
        except httpx.HTTPStatusError as e:
            agent.status = AgentStatus.error
            raise HTTPException(status_code=502, detail=f"Agent error: {e.response.status_code} {e.response.text}")
        except Exception as e:
            agent.status = AgentStatus.error
            raise HTTPException(status_code=502, detail=f"Agent communication error: {str(e)}")


@app.post("/sync/pull", response_model=SyncResponse)
async def sync_pull(body: SyncRequest):
    if body.project not in _projects:
        raise HTTPException(status_code=404, detail=f"Project '{body.project}' not found")
    if body.agent not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent '{body.agent}' not found")

    cid = canonical_id(body.project)
    job = create_job("pull", body.project, cid, agent=body.agent, request_id=request_id_var.get("-"))
    agent = _agents[body.agent]
    agent.status = AgentStatus.syncing
    try:
        result = await _call_agent(agent, "POST", "/sync/pull", {"project": body.project})
        finish_job(job.id, "completed" if result.get("ok") else "failed",
                   detail=result.get("detail"), stdout=result.get("stdout"),
                   stderr=result.get("stderr"), returncode=result.get("returncode"),
                   dryrun=result.get("dryrun", False))
        return SyncResponse(ok=result.get("ok", False), project=body.project, agent=body.agent,
                            canonical_id=cid, detail=result.get("detail", "pull completed"), job_id=job.id)
    except Exception as e:
        finish_job(job.id, "error", detail=str(e))
        raise


@app.post("/sync/push", response_model=SyncResponse)
async def sync_push(body: SyncRequest):
    if body.project not in _projects:
        raise HTTPException(status_code=404, detail=f"Project '{body.project}' not found")
    if body.agent not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent '{body.agent}' not found")

    cid = canonical_id(body.project)
    job = create_job("push", body.project, cid, agent=body.agent, request_id=request_id_var.get("-"))
    agent = _agents[body.agent]
    agent.status = AgentStatus.syncing
    try:
        result = await _call_agent(agent, "POST", "/sync/push", {"project": body.project})
        finish_job(job.id, "completed" if result.get("ok") else "failed",
                   detail=result.get("detail"), stdout=result.get("stdout"),
                   stderr=result.get("stderr"), returncode=result.get("returncode"),
                   dryrun=result.get("dryrun", False))
        return SyncResponse(ok=result.get("ok", False), project=body.project, agent=body.agent,
                            canonical_id=cid, detail=result.get("detail", "push completed"), job_id=job.id)
    except Exception as e:
        finish_job(job.id, "error", detail=str(e))
        raise


@app.get("/jobs", response_model=list[Job])
async def list_jobs_endpoint(limit: int = Query(default=50, le=200), project: Optional[str] = None):
    return list_jobs(limit=limit, project=project)


@app.get("/jobs/{job_id}", response_model=Job)
async def get_job_endpoint(job_id: str):
    job = get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return job


@app.post("/agent/heartbeat")
async def agent_heartbeat(body: NodeHeartbeat):
    """Register a node heartbeat. Returns the node's current role."""
    now = time.time()
    key = f"{body.canonical_id}:{body.node_id}"
    pref_primary = _leadership_pref.get(body.canonical_id, "")
    role = "unknown"
    if pref_primary:
        role = "primary" if body.node_id == pref_primary else "secondary"
    existing = _nodes.get(key)
    _nodes[key] = NodeRecord(
        node_id=body.node_id,
        canonical_id=body.canonical_id,
        role=role,
        obs_count=body.obs_count,
        db_sha=body.db_sha,
        last_seen=body.last_seen or now,
        ip_addrs=body.ip_addrs,
        registered_at=existing.registered_at if existing else now,
    )
    logger.info(
        "heartbeat: node=%s canonical_id=%s role=%s obs=%s",
        body.node_id, body.canonical_id, role, body.obs_count,
    )
    return {"ok": True, "role": role, "canonical_id": body.canonical_id}


@app.get("/projects/{cid}/nodes", response_model=list[NodeRecord])
async def list_nodes(cid: str):
    """List all nodes that have sent heartbeats for this canonical_id."""
    return [n for n in _nodes.values() if n.canonical_id == cid]


@app.get("/projects/{cid}/leadership")
async def get_leadership(cid: str):
    """Get current leadership state for a project (from heartbeat registry)."""
    nodes = [n for n in _nodes.values() if n.canonical_id == cid]
    pref = _leadership_pref.get(cid)
    return {
        "canonical_id": cid,
        "preferred_primary": pref,
        "node_count": len(nodes),
        "nodes": [n.model_dump() for n in nodes],
    }


@app.post("/projects/{cid}/leadership/select")
async def select_leadership(cid: str, body: LeaseSelectRequest):
    """Set the preferred primary node for a project.

    ADMIN_KEY protected (via AdminAuthMiddleware).
    Stores the preference in-memory; nodes adopt roles on next heartbeat/sync.
    For MinIO lease persistence, nodes read this via heartbeat and write locally.
    """
    _leadership_pref[cid] = body.primary_node_id
    # Update cached roles in node registry
    for node in _nodes.values():
        if node.canonical_id == cid:
            node.role = "primary" if node.node_id == body.primary_node_id else "secondary"
    logger.info(
        "leadership select: canonical_id=%s primary=%s lease_seconds=%s",
        cid, body.primary_node_id, body.lease_seconds,
    )
    return {
        "ok": True,
        "canonical_id": cid,
        "primary_node_id": body.primary_node_id,
        "lease_seconds": body.lease_seconds,
        "detail": (
            f"Leadership preference set: primary={body.primary_node_id}. "
            "Nodes will adopt roles on next heartbeat or sync operation. "
            "To persist to MinIO: run `sqlite_minio_sync.py leadership_info` on the primary node "
            f"with PRIMARY_NODE_ID={body.primary_node_id}."
        ),
    }


@app.get("/ui", include_in_schema=False)
async def ui_redirect():
    """Redirect browser to the web UI."""
    return RedirectResponse(url="/static/ui.html")


_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)
app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
