"""Tests for Membridge API endpoints, auth, schemas, compat layer, and validation."""

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
        assert "allow_process_control" in data

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


class TestAgentAliasEndpoints:
    def test_pull_alias(self, agent_client):
        resp = agent_client.post("/pull", json={"project": "garden-seedling"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["dryrun"] is True
        assert data["project"] == "garden-seedling"

    def test_push_alias(self, agent_client):
        resp = agent_client.post("/push", json={"project": "garden-seedling"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["dryrun"] is True

    def test_doctor_post(self, agent_client):
        resp = agent_client.post("/doctor", json={"project": "garden-seedling"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["dryrun"] is True

    def test_canonical_id_consistency(self, agent_client):
        import hashlib
        project = "garden-seedling"
        expected = hashlib.sha256(project.encode()).hexdigest()[:16]
        resp = agent_client.post("/pull", json={"project": project})
        assert resp.json()["canonical_id"] == expected


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

    def test_combined_agent_pull(self, combined_client):
        resp = combined_client.post("/agent/pull", json={"project": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["dryrun"] is True

    def test_combined_agent_push(self, combined_client):
        resp = combined_client.post("/agent/push", json={"project": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True

    def test_combined_agent_doctor(self, combined_client):
        resp = combined_client.post("/agent/doctor", json={"project": "test"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True


class TestCompatLayer:
    def test_canonical_id(self):
        from membridge.compat.sync_wrapper import canonical_id
        import hashlib
        project = "garden-seedling"
        expected = hashlib.sha256(project.encode()).hexdigest()[:16]
        assert canonical_id(project) == expected

    def test_tail_lines(self):
        from membridge.compat.sync_wrapper import _tail_lines
        short = "line1\nline2\nline3"
        assert _tail_lines(short) == short

        long_text = "\n".join([f"line{i}" for i in range(300)])
        result = _tail_lines(long_text, max_lines=200)
        assert "100 lines truncated" in result

    def test_sync_script_path(self):
        from membridge.compat.sync_wrapper import SYNC_SCRIPT
        assert SYNC_SCRIPT.name == "sqlite_minio_sync.py"

    def test_push_project_returns_dict(self):
        from membridge.compat.sync_wrapper import push_project
        result = push_project("test-project", timeout=5)
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["project"] == "test-project"
        assert result["action"] == "push"
        assert len(result["canonical_id"]) == 16

    def test_pull_project_returns_dict(self):
        from membridge.compat.sync_wrapper import pull_project
        result = pull_project("test-project", timeout=5)
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["project"] == "test-project"
        assert result["action"] == "pull"

    def test_doctor_project_returns_dict(self):
        from membridge.compat.sync_wrapper import doctor_project
        result = doctor_project("test-project", timeout=5)
        assert isinstance(result, dict)
        assert "ok" in result
        assert result["project"] == "test-project"
        assert result["action"] == "doctor"

    def test_protected_user_files_list(self):
        from membridge.compat.sync_wrapper import PROTECTED_USER_FILES
        assert "~/.claude/.credentials.json" in PROTECTED_USER_FILES
        assert "~/.claude/auth.json" in PROTECTED_USER_FILES
        assert "~/.claude/settings.local.json" in PROTECTED_USER_FILES


class TestValidateInstall:
    def test_check_claude_cli(self):
        from membridge.validate_install import check_claude_cli
        result = check_claude_cli()
        assert "name" in result
        assert result["name"] == "claude_cli"
        assert "ok" in result
        assert "detail" in result

    def test_check_sqlite_db(self):
        from membridge.validate_install import check_sqlite_db
        result = check_sqlite_db()
        assert result["name"] == "sqlite_db"
        assert "ok" in result
        assert "path" in result

    def test_check_minio_config(self):
        from membridge.validate_install import check_minio_config
        result = check_minio_config()
        assert result["name"] == "minio_config"
        assert "ok" in result

    def test_validate_install_report(self):
        from membridge.validate_install import validate_install
        report = validate_install()
        assert "hostname" in report
        assert "checks" in report
        assert "overall" in report
        assert len(report["checks"]) == 6
        check_names = [c["name"] for c in report["checks"]]
        assert "claude_cli" in check_names
        assert "claude_mem_plugin" in check_names
        assert "sqlite_db" in check_names
        assert "minio_config" in check_names
        assert "agent_running" in check_names
        assert "server_reachable" in check_names
