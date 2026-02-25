# Replit Agent Prompt: Integrate Membridge Control Plane UI

## Context

This is a Node.js + Express 5 + React 18 + Vite + TypeScript monorepo.

### Stack
- Server: `server/routes.ts`, `server/runtime/membridgeClient.ts`
- Frontend: `client/src/`, React + shadcn/ui + TanStack Query + wouter router
- Build output: `dist/public/` (Vite) + `dist/index.cjs` (server)

### Current state

The app running on port 80/5000 has one page: `RuntimeSettings` (route `/`).

There is an external Membridge control plane UI at `http://<host>:8000/static/ui.html`
that requires the user to manually paste an admin key every session (stored in
sessionStorage — lost on tab close). This is inconvenient and unnecessary.

The bloom-runtime server already stores the admin key internally and exposes a
`membridgeFetch(path, options?)` function in `server/runtime/membridgeClient.ts`
that automatically appends `X-MEMBRIDGE-ADMIN` to every outgoing request.
The base URL comes from `storage.getMembridgeUrl()`.

### Goal

Integrate the Membridge control plane functionality directly into the React
frontend at port 80, so the user never needs to enter the admin key manually.

---

## Membridge API (port 8000) — reverse-engineered contract

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/projects` | List all projects |
| GET | `/projects/{cid}/leadership` | Get leadership info for a project |
| GET | `/projects/{cid}/nodes` | List nodes for a project |
| POST | `/projects/{cid}/leadership/select` | Promote a node to primary |

**POST `/leadership/select` body:**
```json
{ "primary_node_id": "string", "lease_seconds": 3600 }
```

**Leadership response shape:**
```json
{ "preferred_primary": "node-id or null", "node_count": 2, "canonical_id": "..." }
```

**Nodes response** — array of:
```json
{
  "node_id": "string",
  "role": "primary" | "secondary" | "unknown",
  "obs_count": 42,
  "db_sha": "abc123...",
  "last_seen": 1700000000,
  "ip_addrs": ["192.168.x.x"]
}
```

**Projects response** — array of:
```json
{ "canonical_id": "string", "name": "string" }
```

---

## Step 1 — Add proxy routes in `server/routes.ts`

After the existing line:
```typescript
app.use("/api/runtime", runtimeAuthMiddleware);
```

Add:
```typescript
app.use("/api/membridge", runtimeAuthMiddleware);
```

Then, before the final `return httpServer;`, add these proxy handlers:

```typescript
// ── Membridge control plane proxy ─────────────────────────────────────────
app.get("/api/membridge/health", async (_req, res) => {
  try {
    const r = await membridgeFetch("/health", { retries: 1 });
    res.status(r.status).json(await r.json());
  } catch (err: any) {
    res.status(502).json({ error: err.message });
  }
});

app.get("/api/membridge/projects", async (_req, res) => {
  try {
    const r = await membridgeFetch("/projects");
    res.status(r.status).json(await r.json());
  } catch (err: any) {
    res.status(502).json({ error: err.message });
  }
});

app.get("/api/membridge/projects/:cid/leadership", async (req, res) => {
  try {
    const r = await membridgeFetch(`/projects/${req.params.cid}/leadership`);
    res.status(r.status).json(await r.json());
  } catch (err: any) {
    res.status(502).json({ error: err.message });
  }
});

app.get("/api/membridge/projects/:cid/nodes", async (req, res) => {
  try {
    const r = await membridgeFetch(`/projects/${req.params.cid}/nodes`);
    res.status(r.status).json(await r.json());
  } catch (err: any) {
    res.status(502).json({ error: err.message });
  }
});

app.post("/api/membridge/projects/:cid/leadership/select", async (req, res) => {
  try {
    const r = await membridgeFetch(
      `/projects/${req.params.cid}/leadership/select`,
      { method: "POST", body: JSON.stringify(req.body) }
    );
    res.status(r.status).json(await r.json());
  } catch (err: any) {
    res.status(502).json({ error: err.message });
  }
});
```

---

## Step 2 — Create `client/src/pages/MembridgePage.tsx`

Full React page component. Requirements:

### Layout
Two-column, full viewport height (minus nav bar):
- **Left column** (280px, fixed width, scrollable): project list
- **Right column** (flex-1, scrollable): project detail

### Project list (left column)
- Fetched from `GET /api/membridge/projects`
- `refetchInterval: 30000`
- Each item: project name (bold, 13px) + canonical_id below (monospace, 11px, muted)
- Clicking an item selects it → store `selectedCid` + `selectedName` in `useState`
- Active item: blue-left-border highlight (`border-l-2 border-blue-500 bg-slate-800`)
- Loading state: 3 `<Skeleton>` rows
- Error state: red error message

### Project detail (right column)
Shown only when a project is selected. When nothing selected: centered
placeholder with a subtle icon (`⬡` or `Server` from lucide-react) and text
"Select a project from the sidebar".

#### Header area
Project name (font-semibold, 15px) + canonical_id (monospace, muted, 12px) +
a `<Button variant="ghost" size="sm">` with `<RefreshCw>` icon that manually
invalidates all queries for the selected project.

Auto-refresh label: small muted text "auto-refresh 10s" next to the button.

#### Leadership card (`<Card>`)
- Title: "Leadership"
- `useQuery` key: `["/api/membridge/projects", cid, "leadership"]`
- `refetchInterval: 10000`, `enabled: !!selectedCid`
- Display as a 2-column info grid:
  - "Preferred primary" → value in blue bold if set, `—` if null
  - "Node count" → number
  - "canonical_id" → monospace
- Loading: `<Skeleton>` lines. Error: red text.

#### Nodes card (`<Card>`)
- Title: "Nodes" + node count badge
- `useQuery` key: `["/api/membridge/projects", cid, "nodes"]`
- `refetchInterval: 10000`, `enabled: !!selectedCid`
- `<Table>` with columns: Node ID | Role | obs_count | db_sha | Last seen | IPs
- Role badge variants:
  - `primary` → `<Badge>` with blue styling (custom className `bg-blue-900 text-blue-300`)
  - `secondary` → green (`bg-green-900 text-green-300`)
  - `unknown` → gray (default secondary variant)
- db_sha: first 12 chars + "…" (show full in `title` attribute for hover)
- Last seen: relative time helper — `Xs ago` / `Xm ago` / `Xh ago` (from unix timestamp seconds)
- IPs: joined with line breaks
- Empty state: "No heartbeats received yet."
- Loading: skeleton rows. Error: red text.

#### Promote Primary card (`<Card>`)
- Title: "Promote Primary"
- Form layout (flex row, gap-2, align-items end):
  - `<Label>` + `<Input>` for Node ID (placeholder "node-id or hostname", min-width 220px)
  - `<Label>` + `<Input type="number">` for Lease seconds (default `3600`, width ~90px)
  - `<Button>` "Promote" (default variant)
- On submit: `useMutation` → `POST /api/membridge/projects/{cid}/leadership/select`
  with body `{ primary_node_id, lease_seconds }`
- On success: show green `<Alert>` with the `detail` field from response.
  Invalidate leadership + nodes queries.
- On error: show red `<Alert>` with error message.
- Clear alert after 5 seconds or on next submit.

### TypeScript interfaces (define in this file)
```typescript
interface MbProject {
  canonical_id: string;
  name: string;
}

interface MbLeadership {
  preferred_primary: string | null;
  node_count: number;
  canonical_id: string;
}

interface MbNode {
  node_id: string;
  role: "primary" | "secondary" | "unknown";
  obs_count: number | null;
  db_sha: string | null;
  last_seen: number | null;
  ip_addrs: string[];
}
```

### Imports to use
```typescript
import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiRequest } from "@/lib/queryClient";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Skeleton } from "@/components/ui/skeleton";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { RefreshCw, Server } from "lucide-react";
```

---

## Step 3 — Update `client/src/App.tsx`

Add a persistent top navigation bar rendered above `<Router>`. Nav bar spec:

```tsx
// Nav bar — add above <Router /> inside App()
<nav className="bg-slate-900 border-b border-slate-700 px-6 h-12 flex items-center gap-6 flex-shrink-0">
  <span className="font-semibold text-sm text-white">Bloom Runtime</span>
  <div className="flex gap-4 ml-4">
    <NavLink href="/">Runtime</NavLink>
    <NavLink href="/membridge">Membridge</NavLink>
  </div>
</nav>
```

Create a small `NavLink` helper component inside `App.tsx`:
```tsx
function NavLink({ href, children }: { href: string; children: React.ReactNode }) {
  const [isActive] = useRoute(href === "/" ? "/" : href);
  // For "/" route, also highlight when on "/runtime"
  return (
    <Link
      href={href}
      className={`text-sm transition-colors ${
        isActive
          ? "text-white font-medium border-b-2 border-blue-400 pb-0.5"
          : "text-slate-400 hover:text-slate-200"
      }`}
    >
      {children}
    </Link>
  );
}
```

Import `useRoute` and `Link` from `wouter`, and import `MembridgePage`.

Add route in `<Switch>`:
```tsx
<Route path="/membridge" component={MembridgePage} />
```

Wrap the entire app body in a flex-col so nav + content stack properly:
```tsx
<div className="flex flex-col h-screen">
  <nav>...</nav>
  <div className="flex-1 overflow-hidden">
    <Router />
  </div>
</div>
```

---

## Constraints

- Do **NOT** modify any existing routes, components, or page behavior.
- The `RuntimeSettings` page and routes `/` and `/runtime` stay exactly as-is.
- Do **NOT** install new npm packages — all dependencies already exist.
- All shadcn/ui components are under `client/src/components/ui/`.
  Confirmed available: `card`, `table`, `badge`, `button`, `input`, `label`,
  `skeleton`, `alert`.
- TypeScript strict — no `any` in component code (only in catch blocks is fine).
- No changes to `shared/schema.ts` or any other shared files needed.

---

## Verification after implementation

1. `npm run build` must complete with no TypeScript errors.
2. `GET /api/membridge/projects` returns JSON from the membridge server.
3. Opening `/membridge` in the browser shows the project list and detail view.
4. The top nav links switch between Runtime and Membridge pages.
5. No admin key prompt anywhere — it is handled transparently by the server.
