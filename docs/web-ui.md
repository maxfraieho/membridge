# Membridge Web UI

A minimal single-file web interface for the control-plane, served directly from
FastAPI on port 8000. No build step, no Node.js required.

## Access

```
http://<host>:8000/ui
```

The browser is redirected automatically to `/static/ui.html`.

## Features

| Panel | Endpoint |
|---|---|
| Projects sidebar | `GET /projects` |
| Leadership card | `GET /projects/{cid}/leadership` |
| Nodes table | `GET /projects/{cid}/nodes` |
| Promote primary | `POST /projects/{cid}/leadership/select` |

Auto-refresh every 10 seconds while a project is selected.

## Authentication

All API calls include the `X-MEMBRIDGE-ADMIN` header.
The key is **never** stored on the server side by the UI — it lives only in
`sessionStorage` (cleared when the tab is closed).

1. Open `/ui` in the browser.
2. Paste the value of `MEMBRIDGE_ADMIN_KEY` into the **Admin Key** field.
3. Click **Save** (or **Test** to verify without loading data).

## Architecture

```
FastAPI (port 8000)
  GET  /ui              → 307 → /static/ui.html
  GET  /static/ui.html  → server/static/ui.html  (auth-exempt)
```

Auth middleware exemptions (no `X-MEMBRIDGE-ADMIN` required):

- `/health`, `/docs`, `/openapi.json`, `/redoc`
- `/ui`
- `/static/*`

## Implementation files

| File | Purpose |
|---|---|
| `server/static/ui.html` | Single-file SPA (vanilla HTML + JS + CSS) |
| `server/main.py` | Mounts `StaticFiles` at `/static`, adds `/ui` redirect |
| `server/auth.py` | Auth exemptions for `/ui` and `/static/*` |

## Related

- Interactive API docs: `http://<host>:8000/docs`
- Health endpoint: `http://<host>:8000/health`
