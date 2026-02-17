"""Tests for Membridge API endpoints, auth, and schemas."""

import os
import pytest

os.environ["MEMBRIDGE_DEV"] = "1"
os.environ["MEMBRIDGE_AGENT_DRYRUN"] = "1"

from fastapi.testclient import TestClient


@pytest.fixture
def server_client():
    from server.main import app, _projects, _agents
    _projects.clear()
    _agents.clear()
    return TestClient(app)


@pytest.fixture
def agent_client():
    from agent.main import app
    return TestClient(app)


@pytest.fixture
def combined_client():
    from run import app
    return TestClient(app)


class TestServerHealth:
    def test_health(self, server_client):
        resp = server_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["service"] == "membridge-control-plane"
        assert "version" in data


class TestServerAuth:
    def test_auth_disabled_in_dev_mode(self, server_client):
        resp = server_client.get("/projects")
        assert resp.status_code == 200

    def test_auth_required_in_prod(self):
        os.environ.pop("MEMBRIDGE_DEV", None)
        os.environ["MEMBRIDGE_ADMIN_KEY"] = "test-admin-key-123"
        try:
            from server.main import app, _projects, _agents
            _projects.clear()
            _agents.clear()
            client = TestClient(app)
            resp = client.get("/projects")
            assert resp.status_code == 401

            resp = client.get("/projects", headers={"X-MEMBRIDGE-ADMIN": "wrong"})
            assert resp.status_code == 401

            resp = client.get("/projects", headers={"X-MEMBRIDGE-ADMIN": "test-admin-key-123"})
            assert resp.status_code == 200

            resp = client.get("/health")
            assert resp.status_code == 200
        finally:
            os.environ["MEMBRIDGE_DEV"] = "1"
            os.environ.pop("MEMBRIDGE_ADMIN_KEY", None)


class TestProjects:
    def test_create_project(self, server_client):
        resp = server_client.post("/projects", json={"name": "test-project"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "test-project"
        assert len(data["canonical_id"]) == 16
        assert "created_at" in data

    def test_create_duplicate(self, server_client):
        server_client.post("/projects", json={"name": "dup"})
        resp = server_client.post("/projects", json={"name": "dup"})
        assert resp.status_code == 409

    def test_list_projects(self, server_client):
        server_client.post("/projects", json={"name": "p1"})
        server_client.post("/projects", json={"name": "p2"})
        resp = server_client.get("/projects")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    def test_delete_project(self, server_client):
        server_client.post("/projects", json={"name": "del-me"})
        resp = server_client.delete("/projects/del-me")
        assert resp.status_code == 204

    def test_delete_missing(self, server_client):
        resp = server_client.delete("/projects/nonexistent")
        assert resp.status_code == 404


class TestAgents:
    def test_register_agent(self, server_client):
        resp = server_client.post("/agents", json={"name": "a1", "url": "http://localhost:8001"})
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "a1"
        assert data["status"] == "unknown"

    def test_duplicate_agent(self, server_client):
        server_client.post("/agents", json={"name": "a1", "url": "http://localhost:8001"})
        resp = server_client.post("/agents", json={"name": "a1", "url": "http://localhost:8001"})
        assert resp.status_code == 409


class TestAgentDaemon:
    def test_agent_health(self, agent_client):
        resp = agent_client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["dryrun"] is True

    def test_agent_status(self, agent_client):
        resp = agent_client.get("/status", params={"project": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["dryrun"] is True
        assert len(data["canonical_id"]) == 16

    def test_agent_pull_dryrun(self, agent_client):
        resp = agent_client.post("/sync/pull", json={"project": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["dryrun"] is True
        assert "DRYRUN" in data["detail"]

    def test_agent_push_dryrun(self, agent_client):
        resp = agent_client.post("/sync/push", json={"project": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["dryrun"] is True


class TestJobs:
    def test_list_jobs_empty(self, server_client):
        resp = server_client.get("/jobs")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_get_job_missing(self, server_client):
        resp = server_client.get("/jobs/nonexistent")
        assert resp.status_code == 404


class TestCombined:
    def test_combined_health(self, combined_client):
        resp = combined_client.get("/health")
        assert resp.status_code == 200

    def test_combined_agent_health(self, combined_client):
        resp = combined_client.get("/agent/health")
        assert resp.status_code == 200
