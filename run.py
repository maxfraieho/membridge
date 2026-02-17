"""Run both Membridge Control Plane and Agent (dry-run) in a single process."""

import asyncio
import os
import uvicorn

os.environ.setdefault("MEMBRIDGE_AGENT_DRYRUN", "1")

from server.main import app as control_plane_app
from agent.main import app as agent_app

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Membridge",
    description="Membridge Control Plane + Agent (dev mode)",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/agent", agent_app)
app.mount("/", control_plane_app)

if __name__ == "__main__":
    uvicorn.run("run:app", host="0.0.0.0", port=5000, reload=True)
