"""Membridge Control Plane — FastAPI server for managing projects and agents."""

import hashlib
import logging
import os
import time
from enum import Enum
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException, Query
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
