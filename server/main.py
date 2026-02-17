"""Membridge Control Plane — FastAPI server for managing projects and agents."""

import hashlib
import time
from enum import Enum
from typing import Optional

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(
    title="Membridge Control Plane",
    description="Centralized API for managing Claude memory sync projects and agents",
    version="0.1.0",
)


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


_projects: dict[str, Project] = {}
_agents: dict[str, Agent] = {}


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "service": "membridge-control-plane",
        "version": "0.1.0",
        "projects": len(_projects),
        "agents": len(_agents),
    }


@app.get("/projects", response_model=list[Project])
async def list_projects():
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
    return proj


@app.delete("/projects/{name}", status_code=204)
async def delete_project(name: str):
    if name not in _projects:
        raise HTTPException(status_code=404, detail=f"Project '{name}' not found")
    del _projects[name]


@app.get("/agents", response_model=list[Agent])
async def list_agents():
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
    return agent


@app.delete("/agents/{name}", status_code=204)
async def unregister_agent(name: str):
    if name not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent '{name}' not found")
    del _agents[name]


async def _call_agent(agent: Agent, method: str, path: str, json_body: dict | None = None) -> dict:
    url = f"{agent.url}{path}"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            if method == "GET":
                resp = await client.get(url)
            else:
                resp = await client.post(url, json=json_body)
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

    agent = _agents[body.agent]
    agent.status = AgentStatus.syncing
    result = await _call_agent(agent, "POST", "/sync/pull", {"project": body.project})
    return SyncResponse(
        ok=result.get("ok", False),
        project=body.project,
        agent=body.agent,
        canonical_id=canonical_id(body.project),
        detail=result.get("detail", "pull completed"),
    )


@app.post("/sync/push", response_model=SyncResponse)
async def sync_push(body: SyncRequest):
    if body.project not in _projects:
        raise HTTPException(status_code=404, detail=f"Project '{body.project}' not found")
    if body.agent not in _agents:
        raise HTTPException(status_code=404, detail=f"Agent '{body.agent}' not found")

    agent = _agents[body.agent]
    agent.status = AgentStatus.syncing
    result = await _call_agent(agent, "POST", "/sync/push", {"project": body.project})
    return SyncResponse(
        ok=result.get("ok", False),
        project=body.project,
        agent=body.agent,
        canonical_id=canonical_id(body.project),
        detail=result.get("detail", "push completed"),
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
