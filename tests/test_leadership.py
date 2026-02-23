"""Tests for Primary/Secondary leadership lease role determination."""

import json
import os
import platform
import sqlite3
import time
from unittest.mock import MagicMock

import pytest

# ─────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────

def _make_lease(primary_node_id, ttl_offset=3600):
    """Build a valid, non-expired lease dict."""
    now = int(time.time())
    return {
        "canonical_id": "testcanonical01",
        "primary_node_id": primary_node_id,
        "issued_at": now,
        "expires_at": now + ttl_offset,
        "lease_seconds": ttl_offset,
        "epoch": 1,
        "policy": "primary_authoritative",
        "issued_by": primary_node_id,
    }


def _make_s3_returning_lease(lease: dict):
    """Create a mock S3 client that returns the given lease on get_object."""
    s3 = MagicMock()
    body = MagicMock()
    body.read.return_value = json.dumps(lease).encode()
    s3.get_object.return_value = {"Body": body}
    return s3


def _make_s3_no_lease():
    """Create a mock S3 client that raises on get_object (no lease)."""
    s3 = MagicMock()
    s3.get_object.side_effect = Exception("NoSuchKey")
    return s3


# ─────────────────────────────────────────────────────────────────
# Role decision tests
# ─────────────────────────────────────────────────────────────────

class TestRoleDecision:
    """Unit tests for determine_role() — no real MinIO needed."""

    def test_node_is_primary_when_matching_valid_lease(self, monkeypatch):
        import sqlite_minio_sync as sms
        monkeypatch.setattr(sms, "NODE_ID", "rpi4b")

        lease = _make_lease("rpi4b")
        s3 = _make_s3_returning_lease(lease)

        role, returned_lease, was_created = sms.determine_role(s3, "bucket", "testcanonical01")

        assert role == "primary"
        assert was_created is False
        assert returned_lease["primary_node_id"] == "rpi4b"

    def test_node_is_secondary_when_different_primary_in_lease(self, monkeypatch):
        import sqlite_minio_sync as sms
        monkeypatch.setattr(sms, "NODE_ID", "orangepi")

        lease = _make_lease("rpi4b")
        s3 = _make_s3_returning_lease(lease)

        role, returned_lease, was_created = sms.determine_role(s3, "bucket", "testcanonical01")

        assert role == "secondary"
        assert was_created is False

    def test_no_lease_creates_default_primary_from_env(self, monkeypatch):
        import sqlite_minio_sync as sms
        monkeypatch.setattr(sms, "NODE_ID", "rpi4b")
        monkeypatch.setattr(sms, "PRIMARY_NODE_ID_ENV", "rpi4b")

        s3 = _make_s3_no_lease()
        # write_lease should be called; mock it to return a fake lease
        written = {}

        def fake_write_lease(s3, bucket, canonical_id, primary_node_id, **kwargs):
            lease = _make_lease(primary_node_id)
            written["lease"] = lease
            return lease

        monkeypatch.setattr(sms, "write_lease", fake_write_lease)

        role, returned_lease, was_created = sms.determine_role(s3, "bucket", "testcanonical01")

        assert role == "primary"
        assert was_created is True
        assert written["lease"]["primary_node_id"] == "rpi4b"

    def test_no_lease_creates_secondary_when_env_points_elsewhere(self, monkeypatch):
        import sqlite_minio_sync as sms
        monkeypatch.setattr(sms, "NODE_ID", "orangepi")
        monkeypatch.setattr(sms, "PRIMARY_NODE_ID_ENV", "rpi4b")

        s3 = _make_s3_no_lease()

        def fake_write_lease(s3, bucket, canonical_id, primary_node_id, **kwargs):
            return _make_lease(primary_node_id)

        monkeypatch.setattr(sms, "write_lease", fake_write_lease)

        role, _, was_created = sms.determine_role(s3, "bucket", "testcanonical01")

        assert role == "secondary"
        assert was_created is True

    def test_expired_lease_renewed_when_we_are_configured_primary(self, monkeypatch):
        import sqlite_minio_sync as sms
        monkeypatch.setattr(sms, "NODE_ID", "rpi4b")
        monkeypatch.setattr(sms, "PRIMARY_NODE_ID_ENV", "rpi4b")

        # Expired lease (issued 2h ago, TTL 1h)
        expired_lease = _make_lease("rpi4b", ttl_offset=-3600)
        s3 = _make_s3_returning_lease(expired_lease)

        renewed = {}

        def fake_write_lease(s3, bucket, canonical_id, primary_node_id, epoch=1, **kwargs):
            lease = _make_lease(primary_node_id)
            lease["epoch"] = epoch
            renewed["epoch"] = epoch
            renewed["primary"] = primary_node_id
            return lease

        monkeypatch.setattr(sms, "write_lease", fake_write_lease)

        role, returned_lease, was_created = sms.determine_role(s3, "bucket", "testcanonical01")

        assert role == "primary"
        assert was_created is True
        assert renewed["epoch"] == 2  # incremented from expired lease epoch=1

    def test_expired_lease_returns_secondary_when_not_configured_primary(self, monkeypatch):
        import sqlite_minio_sync as sms
        monkeypatch.setattr(sms, "NODE_ID", "orangepi")
        monkeypatch.setattr(sms, "PRIMARY_NODE_ID_ENV", "")

        expired_lease = _make_lease("rpi4b", ttl_offset=-3600)
        s3 = MagicMock()
        # First get_object returns expired lease; second re-read also returns it (still expired)
        body = MagicMock()
        body.read.return_value = json.dumps(expired_lease).encode()
        s3.get_object.return_value = {"Body": body}

        role, _, was_created = sms.determine_role(s3, "bucket", "testcanonical01")

        assert role == "secondary"
        assert was_created is True  # expired → was_created means recreated/expired path


# ─────────────────────────────────────────────────────────────────
# Push gate: secondary blocked
# ─────────────────────────────────────────────────────────────────

class TestSecondaryPushBlocked:
    """Verify push_sqlite() exits 3 when role is secondary."""

    def test_secondary_push_exits_3(self, monkeypatch, tmp_path):
        import sqlite_minio_sync as sms

        # Create a minimal fake DB with required tables
        db = tmp_path / "claude-mem.db"
        conn = sqlite3.connect(str(db))
        conn.execute("CREATE TABLE observations (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE session_summaries (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE user_prompts (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        # Set required env vars
        monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
        monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
        monkeypatch.setenv("MINIO_BUCKET", "test-bucket")
        monkeypatch.setenv("CLAUDE_PROJECT_ID", "test-project")
        monkeypatch.setenv("CLAUDE_MEM_DB", str(db))

        monkeypatch.setattr(sms, "NODE_ID", "orangepi")
        monkeypatch.setattr(sms, "LEADERSHIP_ENABLED", True)
        monkeypatch.setattr(sms, "ALLOW_SECONDARY_PUSH", False)

        def mock_determine_role(s3, bucket, canonical_id):
            return "secondary", _make_lease("rpi4b"), False

        monkeypatch.setattr(sms, "determine_role", mock_determine_role)
        monkeypatch.setattr(sms, "get_s3_client", lambda cfg: MagicMock())

        with pytest.raises(SystemExit) as exc:
            sms.push_sqlite()

        assert exc.value.code == 3, f"Expected exit code 3, got {exc.value.code}"

    def test_secondary_push_allowed_with_flag(self, monkeypatch, tmp_path):
        """ALLOW_SECONDARY_PUSH=1 bypasses the gate and proceeds (will fail at upload, that's ok)."""
        import sqlite_minio_sync as sms

        db = tmp_path / "claude-mem.db"
        conn = sqlite3.connect(str(db))
        conn.execute("CREATE TABLE observations (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE session_summaries (id INTEGER PRIMARY KEY)")
        conn.execute("CREATE TABLE user_prompts (id INTEGER PRIMARY KEY)")
        conn.commit()
        conn.close()

        monkeypatch.setenv("MINIO_ENDPOINT", "http://localhost:9000")
        monkeypatch.setenv("MINIO_ACCESS_KEY", "minioadmin")
        monkeypatch.setenv("MINIO_SECRET_KEY", "minioadmin")
        monkeypatch.setenv("MINIO_BUCKET", "test-bucket")
        monkeypatch.setenv("CLAUDE_PROJECT_ID", "test-project")
        monkeypatch.setenv("CLAUDE_MEM_DB", str(db))

        monkeypatch.setattr(sms, "NODE_ID", "orangepi")
        monkeypatch.setattr(sms, "LEADERSHIP_ENABLED", True)
        monkeypatch.setattr(sms, "ALLOW_SECONDARY_PUSH", True)  # override

        def mock_determine_role(s3, bucket, canonical_id):
            return "secondary", _make_lease("rpi4b"), False

        monkeypatch.setattr(sms, "determine_role", mock_determine_role)
        # Return a mock s3 that fails on stop_worker / push (we just want past the gate)
        monkeypatch.setattr(sms, "get_s3_client", lambda cfg: MagicMock())
        monkeypatch.setattr(sms, "stop_worker", lambda: False)
        monkeypatch.setattr(sms, "start_worker", lambda: False)

        # Gate should not block — function should complete without sys.exit(3)
        # (it may succeed with mock data or exit 0; both are fine)
        try:
            sms.push_sqlite()
        except SystemExit as exc:
            assert exc.code != 3, "Gate should not trigger when ALLOW_SECONDARY_PUSH=True"


# ─────────────────────────────────────────────────────────────────
# Leadership API endpoints
# ─────────────────────────────────────────────────────────────────

class TestLeadershipEndpoints:
    """Test control plane leadership endpoints."""

    @pytest.fixture
    def client(self):
        os.environ["MEMBRIDGE_DEV"] = "1"
        from server.main import app, _nodes, _leadership_pref
        _nodes.clear()
        _leadership_pref.clear()
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_heartbeat_registers_node(self, client):
        resp = client.post("/agent/heartbeat", json={
            "node_id": "rpi4b",
            "canonical_id": "abc123",
            "obs_count": 500,
            "db_sha": "deadbeef",
            "ip_addrs": ["192.168.1.10"],
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["canonical_id"] == "abc123"

    def test_list_nodes_empty(self, client):
        resp = client.get("/projects/unknowncid/nodes")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_list_nodes_after_heartbeat(self, client):
        client.post("/agent/heartbeat", json={
            "node_id": "rpi4b",
            "canonical_id": "cid001",
        })
        resp = client.get("/projects/cid001/nodes")
        assert resp.status_code == 200
        nodes = resp.json()
        assert len(nodes) == 1
        assert nodes[0]["node_id"] == "rpi4b"

    def test_get_leadership_no_nodes(self, client):
        resp = client.get("/projects/cid002/leadership")
        assert resp.status_code == 200
        data = resp.json()
        assert data["canonical_id"] == "cid002"
        assert data["node_count"] == 0
        assert data["preferred_primary"] is None

    def test_select_leadership_sets_roles(self, client):
        # Register two nodes
        client.post("/agent/heartbeat", json={"node_id": "rpi4b", "canonical_id": "cid003"})
        client.post("/agent/heartbeat", json={"node_id": "orangepi", "canonical_id": "cid003"})

        # Select primary
        resp = client.post("/projects/cid003/leadership/select", json={
            "primary_node_id": "rpi4b",
            "lease_seconds": 3600,
        })
        assert resp.status_code == 200
        data = resp.json()
        assert data["ok"] is True
        assert data["primary_node_id"] == "rpi4b"

        # Check nodes reflect updated roles
        resp = client.get("/projects/cid003/nodes")
        nodes = {n["node_id"]: n for n in resp.json()}
        assert nodes["rpi4b"]["role"] == "primary"
        assert nodes["orangepi"]["role"] == "secondary"

    def test_heartbeat_role_assigned_from_preference(self, client):
        # Set preference first
        client.post("/projects/cid004/leadership/select", json={"primary_node_id": "rpi4b"})

        # Heartbeat from primary
        resp = client.post("/agent/heartbeat", json={"node_id": "rpi4b", "canonical_id": "cid004"})
        assert resp.json()["role"] == "primary"

        # Heartbeat from secondary
        resp = client.post("/agent/heartbeat", json={"node_id": "orangepi", "canonical_id": "cid004"})
        assert resp.json()["role"] == "secondary"
