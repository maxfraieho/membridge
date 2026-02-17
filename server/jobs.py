"""Sync job history stored in a local SQLite database."""

import json
import os
import sqlite3
import time
import uuid
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

DATA_DIR = Path(os.environ.get("MEMBRIDGE_DATA_DIR", os.path.join(os.path.dirname(__file__), "data")))
DB_PATH = DATA_DIR / "jobs.db"


def _get_conn() -> sqlite3.Connection:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id TEXT PRIMARY KEY,
            action TEXT NOT NULL,
            project TEXT NOT NULL,
            agent TEXT,
            canonical_id TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            detail TEXT,
            stdout TEXT,
            stderr TEXT,
            returncode INTEGER,
            dryrun INTEGER DEFAULT 0,
            created_at REAL NOT NULL,
            finished_at REAL,
            request_id TEXT
        )
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_project ON jobs(project)
    """)
    conn.execute("""
        CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at DESC)
    """)
    conn.commit()
    return conn


_conn: Optional[sqlite3.Connection] = None


def get_conn() -> sqlite3.Connection:
    global _conn
    if _conn is None:
        _conn = _get_conn()
    return _conn


class Job(BaseModel):
    id: str
    action: str
    project: str
    agent: Optional[str] = None
    canonical_id: str
    status: str
    detail: Optional[str] = None
    stdout: Optional[str] = None
    stderr: Optional[str] = None
    returncode: Optional[int] = None
    dryrun: bool = False
    created_at: float
    finished_at: Optional[float] = None
    request_id: Optional[str] = None


def create_job(action: str, project: str, canonical_id: str,
               agent: str | None = None, request_id: str | None = None) -> Job:
    job = Job(
        id=uuid.uuid4().hex[:16],
        action=action,
        project=project,
        agent=agent,
        canonical_id=canonical_id,
        status="pending",
        created_at=time.time(),
        request_id=request_id,
    )
    conn = get_conn()
    conn.execute(
        """INSERT INTO jobs (id, action, project, agent, canonical_id, status, created_at, request_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (job.id, job.action, job.project, job.agent, job.canonical_id, job.status, job.created_at, job.request_id),
    )
    conn.commit()
    return job


def finish_job(job_id: str, status: str, detail: str | None = None,
               stdout: str | None = None, stderr: str | None = None,
               returncode: int | None = None, dryrun: bool = False) -> None:
    conn = get_conn()
    conn.execute(
        """UPDATE jobs SET status=?, detail=?, stdout=?, stderr=?, returncode=?, dryrun=?, finished_at=?
           WHERE id=?""",
        (status, detail, stdout, stderr, returncode, int(dryrun), time.time(), job_id),
    )
    conn.commit()


def get_job(job_id: str) -> Job | None:
    conn = get_conn()
    row = conn.execute("SELECT * FROM jobs WHERE id=?", (job_id,)).fetchone()
    if row is None:
        return None
    return _row_to_job(row)


def list_jobs(limit: int = 50, project: str | None = None) -> list[Job]:
    conn = get_conn()
    if project:
        rows = conn.execute(
            "SELECT * FROM jobs WHERE project=? ORDER BY created_at DESC LIMIT ?",
            (project, limit),
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
    return [_row_to_job(r) for r in rows]


def _row_to_job(row: sqlite3.Row) -> Job:
    return Job(
        id=row["id"],
        action=row["action"],
        project=row["project"],
        agent=row["agent"],
        canonical_id=row["canonical_id"],
        status=row["status"],
        detail=row["detail"],
        stdout=row["stdout"],
        stderr=row["stderr"],
        returncode=row["returncode"],
        dryrun=bool(row["dryrun"]),
        created_at=row["created_at"],
        finished_at=row["finished_at"],
        request_id=row["request_id"],
    )
