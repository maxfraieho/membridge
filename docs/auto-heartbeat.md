# Auto-Heartbeat & Project Auto-Registration

Membridge agents automatically announce themselves to the control-plane and
register known projects, so the Web UI populates without any manual steps.

## How it works

```
┌──────────────────────┐   POST /agent/heartbeat   ┌──────────────────────┐
│  membridge-agent     │ ──────────────────────────▶│  membridge-server    │
│  (port 8001)         │  {node_id, canonical_id,   │  (port 8000)         │
│                      │   project_id, ip_addrs, …} │                      │
│  every HEARTBEAT_    │                             │  → _nodes[]          │
│  INTERVAL_SECONDS    │                             │  → _heartbeat_       │
│  (default: 10 s)     │                             │    projects[]        │
└──────────────────────┘                             └──────────────────────┘
         ▲
         │ POST /register_project (localhost, no auth)
┌──────────────────────┐
│  hooks               │
│  (claude-mem-hook-   │
│   pull / push)       │
└──────────────────────┘
```

1. Hooks call `POST /register_project` on the local agent — project is persisted
   to `~/.membridge/agent_projects.json`.
2. The heartbeat loop reads that file every tick and sends one heartbeat per
   project to the control-plane.
3. The control-plane stores projects in `_heartbeat_projects` (in-memory).
4. `GET /projects` merges manually-created and heartbeat-discovered projects.
5. The Web UI (`/ui`) auto-populates.

## Environment variables

| Variable | Default | Description |
|---|---|---|
| `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS` | `10` | Seconds between heartbeat ticks |
| `MEMBRIDGE_SERVER_URL` | `http://127.0.0.1:8000` | Control-plane base URL |
| `MEMBRIDGE_NODE_ID` | `platform.node()` | Stable node identifier (hostname) |
| `MEMBRIDGE_SERVER_ADMIN_KEY` | *(falls back to `MEMBRIDGE_ADMIN_KEY`)* | Admin key used to authenticate heartbeats with the server |
| `MEMBRIDGE_PROJECTS_FILE` | `~/.membridge/agent_projects.json` | Path to local project registry |

Set these in `.env.agent` (already loaded by `run-agent.sh`).

## Registering a project manually

```bash
# From any localhost process (hooks, scripts — no key required):
curl -s -X POST http://127.0.0.1:8001/register_project \
  -H "Content-Type: application/json" \
  -d '{"project_id": "garden-seedling"}'

# From a remote host (key required):
curl -s -X POST http://192.168.3.184:8001/register_project \
  -H "Content-Type: application/json" \
  -H "X-MEMBRIDGE-AGENT: $MEMBRIDGE_AGENT_KEY" \
  -d '{"project_id": "garden-seedling", "path": "/home/vokov/projects/garden-seedling"}'
```

## Checking agent status

```bash
curl -s http://127.0.0.1:8001/health | jq .
# → shows: heartbeat_interval, server_url, projects_count

curl -s http://127.0.0.1:8001/projects
# → list of projects in agent's local registry
```

## Checking server state

```bash
ADMIN_KEY="$(grep MEMBRIDGE_ADMIN_KEY ~/.membridge-server.env | cut -d= -f2)"
curl -s http://127.0.0.1:8000/projects \
  -H "X-MEMBRIDGE-ADMIN: $ADMIN_KEY" | jq .
```

## Troubleshooting

**Web UI shows "No projects yet"**

1. Check agent is running: `rc-service membridge-agent status`
2. Check agent health: `curl -s http://127.0.0.1:8001/health`
3. Check `projects_count` in health response — is it > 0?
4. Register a project manually (see above) and wait one heartbeat tick
5. Check server logs: `rc-service membridge-server status` or agent log

**Heartbeat disabled warning in agent logs**

Set `MEMBRIDGE_SERVER_ADMIN_KEY` in `.env.agent`. It is typically the same
value as `MEMBRIDGE_ADMIN_KEY` on the server.

**Stop hook error: "bun-runner.js not found"**

This is a claude-mem plugin issue, not a membridge-agent issue.  Common on
ARM64 machines (Orange Pi, Raspberry Pi) and after plugin upgrades.

Run the read-only verifier to diagnose:

```bash
bash scripts/verify_claude_mem.sh
```

Exit code tells you what's wrong (10 = stale plugin metadata, 11 = bun missing,
12 = wrong bun architecture, 13 = bun-runner.js absent).  Full root-cause
analysis and step-by-step fixes: [`docs/arm64-claude-mem.md`](arm64-claude-mem.md).

**Projects disappear after server restart**

The control-plane stores heartbeat projects in-memory. They reappear after the
next heartbeat cycle (≤ `MEMBRIDGE_HEARTBEAT_INTERVAL_SECONDS`).

## Security notes

- `/register_project` on the agent is **auth-exempt for localhost** connections
  (127.0.0.1 / ::1). Remote calls require `X-MEMBRIDGE-AGENT` header.
- Heartbeats are sent with `X-MEMBRIDGE-ADMIN` — keep `MEMBRIDGE_SERVER_ADMIN_KEY`
  out of version control (use `.env.agent`, already in `.gitignore`).
