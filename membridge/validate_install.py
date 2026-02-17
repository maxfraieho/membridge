"""Membridge installation validator — CLI and importable module.

Usage:
    python -m membridge.validate_install
    membridge validate-install

Checks:
1. Claude CLI installed
2. claude-mem plugin installed
3. SQLite memory DB exists
4. MinIO accessible (config.env present)
5. Agent running (port 8001)
6. Server reachable (port 8000)

Output: human-readable summary and JSON report.
"""

import hashlib
import json
import os
import platform
import shutil
import sqlite3
import sys
import time
from pathlib import Path


def check_claude_cli() -> dict:
    claude_bin = shutil.which("claude")
    claude_dir = Path(os.path.expanduser("~/.claude"))
    return {
        "name": "claude_cli",
        "ok": claude_bin is not None or claude_dir.exists(),
        "detail": f"binary={claude_bin or 'not found'}, config_dir={'exists' if claude_dir.exists() else 'missing'}",
    }


def check_claude_mem_plugin() -> dict:
    plugin_markers = [
        Path(os.path.expanduser("~/.claude/plugins/marketplaces/thedotmack")),
        Path(os.path.expanduser("~/.claude-mem")),
    ]
    found = [str(p) for p in plugin_markers if p.exists()]
    return {
        "name": "claude_mem_plugin",
        "ok": len(found) > 0,
        "detail": f"found={found}" if found else "claude-mem plugin not detected",
    }


def check_sqlite_db() -> dict:
    db_path = Path(os.path.expanduser("~/.claude-mem/claude-mem.db"))
    config_env = Path(os.environ.get("MEMBRIDGE_CONFIG_ENV", os.path.expanduser("~/.claude-mem-minio/config.env")))
    if config_env.exists():
        for line in config_env.read_text().splitlines():
            if line.strip().startswith("CLAUDE_MEM_DB="):
                custom_path = line.strip().split("=", 1)[1].strip()
                custom_path = custom_path.replace("$HOME", os.path.expanduser("~"))
                db_path = Path(custom_path)
                break

    if not db_path.exists():
        return {
            "name": "sqlite_db",
            "ok": False,
            "detail": f"DB not found at {db_path}",
            "path": str(db_path),
        }

    try:
        conn = sqlite3.connect(str(db_path))
        integrity = conn.execute("PRAGMA integrity_check").fetchone()[0]
        tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
        size = db_path.stat().st_size
        conn.close()
        return {
            "name": "sqlite_db",
            "ok": integrity == "ok",
            "detail": f"size={size} bytes, tables={len(tables)}, integrity={integrity}",
            "path": str(db_path),
            "size": size,
            "tables": len(tables),
            "integrity": integrity,
        }
    except Exception as e:
        return {
            "name": "sqlite_db",
            "ok": False,
            "detail": f"Error reading DB: {e}",
            "path": str(db_path),
        }


def check_minio_config() -> dict:
    config_env = Path(os.environ.get("MEMBRIDGE_CONFIG_ENV", os.path.expanduser("~/.claude-mem-minio/config.env")))
    if not config_env.exists():
        return {
            "name": "minio_config",
            "ok": False,
            "detail": f"config.env not found at {config_env}",
        }

    required_keys = ["MINIO_ENDPOINT", "MINIO_ACCESS_KEY", "MINIO_SECRET_KEY", "MINIO_BUCKET"]
    found_keys = []
    for line in config_env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k = line.split("=", 1)[0].strip()
            if k in required_keys:
                found_keys.append(k)

    missing = [k for k in required_keys if k not in found_keys]
    return {
        "name": "minio_config",
        "ok": len(missing) == 0,
        "detail": f"config={config_env}, missing_keys={missing}" if missing else f"config={config_env}, all keys present",
        "config_path": str(config_env),
        "missing_keys": missing,
    }


def check_agent_running() -> dict:
    try:
        import urllib.request
        agent_port = os.environ.get("MEMBRIDGE_AGENT_PORT", "8001")
        url = f"http://127.0.0.1:{agent_port}/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                "name": "agent_running",
                "ok": data.get("status") == "ok",
                "detail": f"agent v{data.get('version', '?')} on port {agent_port}, dryrun={data.get('dryrun')}",
                "version": data.get("version"),
                "dryrun": data.get("dryrun"),
            }
    except Exception as e:
        return {
            "name": "agent_running",
            "ok": False,
            "detail": f"Agent not reachable: {e}",
        }


def check_server_reachable() -> dict:
    try:
        import urllib.request
        server_port = os.environ.get("MEMBRIDGE_SERVER_PORT", "8000")
        server_host = os.environ.get("MEMBRIDGE_SERVER_HOST", "127.0.0.1")
        url = f"http://{server_host}:{server_port}/health"
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode())
            return {
                "name": "server_reachable",
                "ok": data.get("status") == "ok",
                "detail": f"server v{data.get('version', '?')} on {server_host}:{server_port}",
                "version": data.get("version"),
            }
    except Exception as e:
        return {
            "name": "server_reachable",
            "ok": False,
            "detail": f"Server not reachable: {e}",
        }


def validate_install() -> dict:
    checks = [
        check_claude_cli(),
        check_claude_mem_plugin(),
        check_sqlite_db(),
        check_minio_config(),
        check_agent_running(),
        check_server_reachable(),
    ]

    all_ok = all(c["ok"] for c in checks)

    report = {
        "timestamp": time.time(),
        "hostname": platform.node(),
        "python": sys.version.split()[0],
        "overall": "OK" if all_ok else "ISSUES_FOUND",
        "checks": checks,
    }
    return report


def print_report(report: dict) -> None:
    print("=" * 50)
    print("  Membridge Installation Validation")
    print("=" * 50)
    print(f"  hostname: {report['hostname']}")
    print(f"  python:   {report['python']}")
    print()

    for check in report["checks"]:
        status = "OK" if check["ok"] else "FAIL"
        icon = "+" if check["ok"] else "!"
        print(f"  [{icon}] {check['name']}: {status}")
        print(f"      {check['detail']}")
        print()

    print("=" * 50)
    print(f"  OVERALL: {report['overall']}")
    print("=" * 50)


def main():
    report = validate_install()
    print_report(report)
    print()
    print("--- JSON Report ---")
    print(json.dumps(report, indent=2))
    sys.exit(0 if report["overall"] == "OK" else 1)


if __name__ == "__main__":
    main()
