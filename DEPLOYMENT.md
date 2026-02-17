# Membridge Deployment Guide

## Quick Start

### Option A: Linux Install Script (recommended)

```bash
# Install both server + agent on one machine
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s all

# Or install just the server (central control plane)
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s server

# Or install just the agent (on each worker machine)
curl -sSL https://raw.githubusercontent.com/maxfraieho/membridge/main/install.sh | bash -s agent
```

The script:
- Clones the repo to `~/membridge`
- Creates a Python venv at `~/membridge/.venv`
- Installs dependencies
- Generates `.env.server` / `.env.agent` with random auth keys
- Installs and starts systemd services (if available)

### Option B: Windows

```powershell
git clone https://github.com/maxfraieho/membridge.git $env:USERPROFILE\membridge
cd $env:USERPROFILE\membridge
powershell -ExecutionPolicy Bypass -File install.ps1 -Mode agent
```

### Option C: Manual

```bash
git clone https://github.com/maxfraieho/membridge.git ~/membridge
cd ~/membridge
python3 -m venv .venv
source .venv/bin/activate
pip install fastapi uvicorn httpx pydantic boto3

# Server
source .env.server
python -m uvicorn server.main:app --host 0.0.0.0 --port 8000

# Agent
source .env.agent
python -m uvicorn agent.main:app --host 0.0.0.0 --port 8001
```

---

## Security Keys

Membridge uses two shared secrets for authentication:

| Key | Header | Purpose |
|-----|--------|---------|
| `MEMBRIDGE_ADMIN_KEY` | `X-MEMBRIDGE-ADMIN` | Admin access to control plane |
| `MEMBRIDGE_AGENT_KEY` | `X-MEMBRIDGE-AGENT` | Agent-to-server authentication |

### Setting up keys

The install script generates random keys automatically. For manual setup:

```bash
# Generate a key
python3 -c "import secrets; print(secrets.token_hex(24))"

# Server (.env.server)
MEMBRIDGE_ADMIN_KEY=<your-admin-key>
MEMBRIDGE_AGENT_KEY=<your-agent-key>

# Agent (.env.agent) — must match server's MEMBRIDGE_AGENT_KEY
MEMBRIDGE_AGENT_KEY=<same-agent-key-as-server>
```

### Dev mode

Set `MEMBRIDGE_DEV=1` to disable authentication entirely (for local development only):

```bash
MEMBRIDGE_DEV=1 python -m uvicorn run:app --host 0.0.0.0 --port 5000 --reload
```

---

## Running Behind a Reverse Proxy

### Nginx example

```nginx
server {
    listen 443 ssl;
    server_name membridge.example.com;

    ssl_certificate     /etc/ssl/certs/membridge.pem;
    ssl_certificate_key /etc/ssl/private/membridge.key;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
```

### Caddy example

```
membridge.example.com {
    reverse_proxy localhost:8000
}
```

Agents should point their URLs to the public endpoint:
```bash
curl -X POST https://membridge.example.com/agents \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"pi-node", "url":"http://192.168.1.50:8001"}'
```

---

## Example: Full Workflow

### 1. Create a project

```bash
curl -X POST http://localhost:8000/projects \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"garden-seedling"}'
```

Response:
```json
{
  "name": "garden-seedling",
  "canonical_id": "aeeafec3a5b5710f",
  "created_at": 1700000000.0
}
```

### 2. Register an agent

```bash
curl -X POST http://localhost:8000/agents \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name":"orangepipc2", "url":"http://192.168.1.50:8001"}'
```

### 3. Check agent status

```bash
curl "http://localhost:8001/status?project=garden-seedling" \
  -H "X-MEMBRIDGE-AGENT: $AGENT_KEY"
```

### 4. Trigger a pull

```bash
curl -X POST http://localhost:8000/sync/pull \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project":"garden-seedling", "agent":"orangepipc2"}'
```

Response:
```json
{
  "ok": true,
  "project": "garden-seedling",
  "agent": "orangepipc2",
  "canonical_id": "aeeafec3a5b5710f",
  "detail": "pull completed",
  "job_id": "abc123def456"
}
```

### 5. Trigger a push

```bash
curl -X POST http://localhost:8000/sync/push \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" \
  -H "Content-Type: application/json" \
  -d '{"project":"garden-seedling", "agent":"orangepipc2"}'
```

### 6. View job history

```bash
# All jobs
curl http://localhost:8000/jobs \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY"

# Filter by project
curl "http://localhost:8000/jobs?project=garden-seedling" \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY"

# Single job detail
curl http://localhost:8000/jobs/abc123def456 \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY"
```

---

## CLI Hook Scripts

### Using `--project`

All hook scripts support `--project <name>` to override the project from config.env:

```bash
# Manual pull for a specific project
claude-mem-pull --project garden-seedling

# Manual push for a specific project
claude-mem-push --project garden-seedling

# Status for a specific project
claude-mem-status --project garden-seedling

# Doctor diagnostics
claude-mem-doctor --project garden-seedling
```

### Using `--no-restart-worker`

By default, pull does NOT restart the claude-mem worker (safe mode). To explicitly control this:

```bash
# Pull without restarting worker (default, same as no flag)
claude-mem-pull --no-restart-worker

# Pull and let it restart worker (remove MEMBRIDGE_NO_RESTART_WORKER)
MEMBRIDGE_NO_RESTART_WORKER=0 claude-mem-pull
```

The SessionStart hook (`claude-mem-hook-pull`) always uses safe mode — the worker starts naturally with the Claude CLI session.

---

## Ports

| Service | Default Port | Environment |
|---------|-------------|-------------|
| Control Plane | 8000 | Production |
| Agent Daemon | 8001 | Production |
| Combined (dev) | 5000 | Development |

---

## Systemd Services

Service units are in `deploy/systemd/`. After installation:

```bash
# Status
sudo systemctl status membridge-server
sudo systemctl status membridge-agent

# Logs
journalctl -u membridge-server -f
journalctl -u membridge-agent -f

# Restart
sudo systemctl restart membridge-server
```

---

## API Reference

### Control Plane (port 8000)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Service health check |
| GET | `/projects` | Admin | List all projects |
| POST | `/projects` | Admin | Create project |
| DELETE | `/projects/{name}` | Admin | Delete project |
| GET | `/agents` | Admin | List all agents |
| POST | `/agents` | Admin | Register agent |
| DELETE | `/agents/{name}` | Admin | Unregister agent |
| POST | `/sync/pull` | Admin | Trigger pull on agent |
| POST | `/sync/push` | Admin | Trigger push on agent |
| GET | `/jobs` | Admin | List job history |
| GET | `/jobs/{id}` | Admin | Get job details |

### Agent Daemon (port 8001)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Agent health check |
| GET | `/status?project=...` | Agent | Project status on this machine |
| POST | `/sync/pull` | Agent | Execute pull |
| POST | `/sync/push` | Agent | Execute push |
| GET | `/doctor?project=...` | Agent | Run diagnostics |
