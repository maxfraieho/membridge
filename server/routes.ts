import type { Express } from "express";
import { type Server } from "http";
import rateLimit from "express-rate-limit";
import { storage, DatabaseStorage } from "./storage";
import { membridgeFetch, getMembridgeClientState } from "./runtime/membridgeClient";
import { startWorkerSync } from "./runtime/workerSync";
import { runtimeAuthMiddleware } from "./middleware/runtimeAuth";
import { uploadArtifactToMinio, isMinioConfigured, getMinioArtifactUrl } from "./runtime/minioArtifacts";
import {
  insertLLMTaskSchema,
  completeTaskSchema,
  runtimeConfigSchema,
  registerWorkerSchema,
  createProjectSchema,
  type WorkerNode,
  type TaskStatus,
} from "@shared/schema";

const LEASE_TTL_SECONDS = 300;

async function pickWorker(workers: WorkerNode[], contextId?: string | null): Promise<WorkerNode | null> {
  const online = workers.filter(
    (w) => w.status === "online" && w.capabilities.claude_cli && w.active_leases < w.capabilities.max_concurrency
  );
  if (online.length === 0) return null;

  if (contextId) {
    const activeLeases = await storage.listLeases({ status: "active" });
    const stickyWorkerId = activeLeases.find((l) => l.context_id === contextId)?.worker_id;
    if (stickyWorkerId) {
      const sticky = online.find((w) => w.id === stickyWorkerId);
      if (sticky) return sticky;
    }
  }

  online.sort((a, b) => {
    const freeA = a.capabilities.max_concurrency - a.active_leases;
    const freeB = b.capabilities.max_concurrency - b.active_leases;
    return freeB - freeA;
  });

  return online[0];
}

export async function registerRoutes(
  httpServer: Server,
  app: Express
): Promise<Server> {

  if (storage instanceof DatabaseStorage) {
    await storage.init();
  }

  const apiLimiter = rateLimit({
    windowMs: 60 * 1000,
    max: 100,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: "Too many requests, please try again later" },
  });

  const strictLimiter = rateLimit({
    windowMs: 60 * 1000,
    max: 20,
    standardHeaders: true,
    legacyHeaders: false,
    message: { error: "Too many requests, please try again later" },
  });

  app.use("/api/runtime", apiLimiter);
  app.use("/api/membridge", apiLimiter);

  app.use("/api/runtime", runtimeAuthMiddleware);

  if (process.env.NODE_ENV === "production") {
    app.use((req, res, next) => {
      if (req.headers["x-forwarded-proto"] === "http") {
        return res.redirect(301, `https://${req.headers.host}${req.originalUrl}`);
      }
      next();
    });
    app.set("trust proxy", 1);
  }

  startWorkerSync();

  setInterval(async () => {
    try {
      const expired = await storage.expireStaleLeases();
      if (expired > 0) {
        console.log(`[runtime] expired ${expired} stale lease(s), requeued tasks`);
      }
    } catch (err) {
      console.error("[runtime] lease expiry error:", err);
    }
  }, 30000);

  app.get("/api/runtime/health", async (_req, res) => {
    const clientState = getMembridgeClientState();
    res.json({
      status: "ok",
      service: "bloom-runtime",
      uptime: process.uptime(),
      storage: "postgresql",
      membridge: clientState,
    });
  });

  app.get("/api/runtime/config", async (_req, res) => {
    const config = await storage.getRuntimeConfig();
    res.json(config);
  });

  app.post("/api/runtime/config", async (req, res) => {
    const parsed = runtimeConfigSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.flatten() });
    }
    const config = await storage.setRuntimeConfig(parsed.data);
    await storage.addAuditLog({
      action: "config_updated",
      entity_type: "runtime_config",
      entity_id: "singleton",
      actor: "admin",
      detail: `Updated membridge URL to ${parsed.data.membridge_server_url}`,
    });
    res.json(config);
  });

  app.post("/api/runtime/test-connection", strictLimiter, async (_req, res) => {
    try {
      const response = await membridgeFetch("/health", { retries: 1 });
      if (!response.ok) {
        storage.setConnectionStatus(false);
        return res.json({ connected: false, error: `HTTP ${response.status}` });
      }
      const data = await response.json();
      storage.setConnectionStatus(true);
      await storage.addAuditLog({
        action: "connection_test",
        entity_type: "runtime_config",
        entity_id: "singleton",
        actor: "admin",
        detail: `Connection OK: ${JSON.stringify(data)}`,
      });
      res.json({ connected: true, health: data });
    } catch (err: any) {
      storage.setConnectionStatus(false);
      res.json({ connected: false, error: err.message || "Connection failed" });
    }
  });

  app.get("/api/runtime/workers", async (_req, res) => {
    try {
      const localWorkers = await storage.listWorkers();
      const merged = new Map<string, WorkerNode>();
      for (const w of localWorkers) {
        merged.set(w.id, { ...w, active_leases: 0 });
      }

      const activeLeases = await storage.listLeases({ status: "active" });
      for (const lease of activeLeases) {
        const worker = merged.get(lease.worker_id);
        if (worker) {
          worker.active_leases += 1;
        }
      }

      res.json(Array.from(merged.values()));
    } catch (err: any) {
      console.error("[workers] list error:", err);
      res.json([]);
    }
  });

  app.get("/api/runtime/workers/:id", async (req, res) => {
    const worker = await storage.getWorker(req.params.id);
    if (!worker) {
      return res.status(404).json({ error: "Worker not found" });
    }
    const leases = await storage.listLeases({ status: "active" });
    const workerLeases = leases.filter((l) => l.worker_id === worker.id);
    res.json({ ...worker, leases: workerLeases });
  });

  app.post("/api/runtime/workers", async (req, res) => {
    const parsed = registerWorkerSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.flatten() });
    }
    const input = parsed.data;
    const now = Date.now();
    const existing = await storage.getWorker(input.name);
    const worker: WorkerNode = {
      id: input.name,
      node_id: input.name,
      url: input.url || existing?.url || "",
      status: input.status || "online",
      capabilities: {
        claude_cli: input.capabilities?.claude_cli ?? true,
        max_concurrency: input.capabilities?.max_concurrency ?? 1,
        labels: input.capabilities?.labels ?? [],
      },
      last_heartbeat: now,
      ip_addrs: input.ip_addrs || [],
      obs_count: existing?.obs_count ?? 0,
      db_sha: existing?.db_sha ?? "",
      registered_at: existing?.registered_at ?? now,
      active_leases: 0,
    };
    const saved = await storage.upsertWorker(worker);
    await storage.addAuditLog({
      action: existing ? "worker_updated" : "worker_registered",
      entity_type: "worker",
      entity_id: saved.id,
      actor: "api",
      detail: `Worker ${saved.id} registered, status=${saved.status}, max_concurrency=${saved.capabilities.max_concurrency}`,
    });
    res.status(existing ? 200 : 201).json(saved);
  });

  app.delete("/api/runtime/workers/:id", async (req, res) => {
    const worker = await storage.getWorker(req.params.id);
    if (!worker) {
      return res.status(404).json({ error: "Worker not found" });
    }
    await storage.removeWorker(req.params.id);
    await storage.addAuditLog({
      action: "worker_removed",
      entity_type: "worker",
      entity_id: req.params.id,
      actor: "admin",
      detail: `Worker ${req.params.id} unregistered`,
    });
    res.json({ removed: true, id: req.params.id });
  });

  app.post("/api/runtime/llm-tasks", async (req, res) => {
    const parsed = insertLLMTaskSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.flatten() });
    }
    const task = await storage.createTask(parsed.data);
    await storage.addAuditLog({
      action: "task_created",
      entity_type: "llm_task",
      entity_id: task.id,
      actor: "api",
      detail: `Task for agent ${task.agent_slug}, context ${task.context_id}`,
    });
    res.status(201).json(task);
  });

  app.get("/api/runtime/llm-tasks", async (req, res) => {
    const status = req.query.status as TaskStatus | undefined;
    const tasks = await storage.listTasks(status ? { status } : undefined);
    res.json(tasks);
  });

  app.get("/api/runtime/llm-tasks/:id", async (req, res) => {
    const task = await storage.getTask(req.params.id);
    if (!task) {
      return res.status(404).json({ error: "Task not found" });
    }
    res.json(task);
  });

  app.post("/api/runtime/llm-tasks/:id/lease", async (req, res) => {
    const task = await storage.getTask(req.params.id);
    if (!task) {
      return res.status(404).json({ error: "Task not found" });
    }
    if (task.status !== "queued") {
      return res.status(409).json({ error: `Task status is '${task.status}', expected 'queued'` });
    }

    const workers = await storage.listWorkers();
    const targetWorkerId = req.body?.worker_id;
    let selectedWorker: WorkerNode | null = null;

    if (targetWorkerId) {
      selectedWorker = workers.find((w) => w.id === targetWorkerId) || null;
    } else {
      const activeLeases = await storage.listLeases({ status: "active" });
      const leaseCounts = new Map<string, number>();
      for (const l of activeLeases) {
        leaseCounts.set(l.worker_id, (leaseCounts.get(l.worker_id) || 0) + 1);
      }
      for (const w of workers) {
        w.active_leases = leaseCounts.get(w.id) || 0;
      }
      selectedWorker = await pickWorker(workers, task.context_id);
    }

    if (!selectedWorker) {
      return res.status(503).json({ error: "No available worker with free capacity" });
    }

    const ttl = req.body?.ttl_seconds || LEASE_TTL_SECONDS;
    const lease = await storage.createLease(task.id, selectedWorker.id, ttl, task.context_id);
    await storage.updateTaskStatus(task.id, "leased", {
      lease_id: lease.id,
      worker_id: selectedWorker.id,
      attempts: task.attempts + 1,
    });

    await storage.addAuditLog({
      action: "task_leased",
      entity_type: "lease",
      entity_id: lease.id,
      actor: "router",
      detail: `Task ${task.id} leased to worker ${selectedWorker.id}, TTL ${ttl}s`,
    });

    res.status(201).json({ lease, worker: selectedWorker });
  });

  app.post("/api/runtime/llm-tasks/:id/heartbeat", async (req, res) => {
    const task = await storage.getTask(req.params.id);
    if (!task || !task.lease_id) {
      return res.status(404).json({ error: "Task or lease not found" });
    }
    const lease = await storage.renewLease(task.lease_id);
    if (!lease) {
      return res.status(404).json({ error: "Lease not found or already expired" });
    }
    await storage.updateTaskStatus(task.id, "running");
    res.json({ lease, expires_at: lease.expires_at });
  });

  app.post("/api/runtime/llm-tasks/:id/complete", async (req, res) => {
    const task = await storage.getTask(req.params.id);
    if (!task) {
      return res.status(404).json({ error: "Task not found" });
    }
    if (task.status !== "leased" && task.status !== "running") {
      return res.status(409).json({ error: `Task status is '${task.status}', expected 'leased' or 'running'` });
    }

    const parsed = completeTaskSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.flatten() });
    }

    const input = parsed.data;
    const now = Date.now();

    let artifactUrl: string | null = null;
    let artifactContent = input.output;

    if (isMinioConfigured() && input.output) {
      try {
        const objectKey = `artifacts/${task.id}/${now}.json`;
        artifactUrl = await uploadArtifactToMinio(objectKey, input.output);
        artifactContent = null;
      } catch (err: any) {
        console.warn("[minio] artifact upload failed, storing in PostgreSQL:", err.message);
      }
    }

    const artifact = await storage.createArtifact({
      task_id: task.id,
      job_id: null,
      type: input.artifact_type,
      created_at: now,
      finalized: true,
      url: artifactUrl,
      entity_refs: [],
      tags: input.artifact_tags,
      content: artifactContent,
    });

    const result = await storage.createResult({
      task_id: task.id,
      worker_id: task.worker_id || "unknown",
      artifact_id: artifact.id,
      status: input.status,
      output: input.output,
      error_message: input.error_message,
      metrics: input.metrics,
      completed_at: now,
    });

    const finalStatus: TaskStatus = input.status === "success" ? "completed" : "failed";
    await storage.updateTaskStatus(task.id, finalStatus);

    if (task.lease_id) {
      await storage.releaseLease(task.lease_id, "released");
    }

    await storage.addAuditLog({
      action: "task_completed",
      entity_type: "llm_task",
      entity_id: task.id,
      actor: task.worker_id || "unknown",
      detail: `Status: ${input.status}, artifact: ${artifact.id}, duration: ${input.metrics.duration_ms}ms`,
    });

    res.json({ task: await storage.getTask(task.id), artifact, result });
  });

  app.get("/api/runtime/leases", async (req, res) => {
    const status = req.query.status as string | undefined;
    const leases = await storage.listLeases(
      status ? { status: status as any } : undefined
    );
    res.json(leases);
  });

  app.get("/api/runtime/runs", async (_req, res) => {
    const tasks = await storage.listTasks();
    const recent = tasks.slice(0, 50);
    res.json(recent);
  });

  app.get("/api/runtime/artifacts", async (req, res) => {
    const taskId = req.query.task_id as string | undefined;
    const artifacts = await storage.listArtifacts(taskId ? { task_id: taskId } : undefined);
    res.json(artifacts);
  });

  app.get("/api/runtime/audit", async (req, res) => {
    const limit = parseInt(req.query.limit as string) || 100;
    const logs = await storage.listAuditLogs(limit);
    res.json(logs);
  });

  app.post("/api/runtime/llm-tasks/:id/requeue", async (req, res) => {
    const task = await storage.getTask(req.params.id);
    if (!task) {
      return res.status(404).json({ error: "Task not found" });
    }
    if (task.status !== "failed" && task.status !== "dead") {
      return res.status(409).json({ error: `Cannot requeue task with status '${task.status}'` });
    }
    await storage.updateTaskStatus(task.id, "queued", {
      lease_id: null,
      worker_id: null,
      attempts: 0,
    });
    await storage.addAuditLog({
      action: "task_requeued",
      entity_type: "llm_task",
      entity_id: task.id,
      actor: "admin",
      detail: `Requeued from ${task.status}`,
    });
    res.json(await storage.getTask(task.id));
  });

  // ─── Membridge Control Plane Proxy ───────────────────────────────
  // All /api/membridge/* routes proxy through membridgeFetch() so the
  // frontend never touches Membridge directly or sees the admin key.

  app.use("/api/membridge", runtimeAuthMiddleware);

  app.get("/api/membridge/health", async (_req, res) => {
    try {
      const response = await membridgeFetch("/health", { retries: 1 });
      const data = await response.json();
      res.json(data);
    } catch (err: any) {
      res.status(502).json({ error: err.message || "Membridge unreachable" });
    }
  });

  app.get("/api/membridge/projects", async (_req, res) => {
    try {
      const response = await membridgeFetch("/projects");
      const data = await response.json();
      res.json(data);
    } catch (err: any) {
      res.status(502).json({ error: err.message || "Membridge unreachable" });
    }
  });

  app.get("/api/membridge/projects/:cid/leadership", async (req, res) => {
    try {
      const response = await membridgeFetch(`/projects/${req.params.cid}/leadership`);
      if (!response.ok) {
        return res.status(response.status).json({ error: `Membridge returned ${response.status}` });
      }
      const data = await response.json();
      res.json(data);
    } catch (err: any) {
      res.status(502).json({ error: err.message || "Membridge unreachable" });
    }
  });

  app.get("/api/membridge/projects/:cid/nodes", async (req, res) => {
    try {
      const response = await membridgeFetch(`/projects/${req.params.cid}/nodes`);
      if (!response.ok) {
        return res.status(response.status).json({ error: `Membridge returned ${response.status}` });
      }
      const data = await response.json();
      res.json(data);
    } catch (err: any) {
      res.status(502).json({ error: err.message || "Membridge unreachable" });
    }
  });

  app.post("/api/membridge/projects/:cid/leadership/select", async (req, res) => {
    try {
      const response = await membridgeFetch(`/projects/${req.params.cid}/leadership/select`, {
        method: "POST",
        body: JSON.stringify(req.body),
      });
      if (!response.ok) {
        const text = await response.text();
        return res.status(response.status).json({ error: text || `Membridge returned ${response.status}` });
      }
      const data = await response.json();
      await storage.addAuditLog({
        action: "leadership_promote",
        entity_type: "membridge_project",
        entity_id: req.params.cid,
        actor: "admin",
        detail: `Promoted primary to ${req.body?.primary_node_id || "unknown"} for project ${req.params.cid}`,
      });
      res.json(data);
    } catch (err: any) {
      res.status(502).json({ error: err.message || "Membridge unreachable" });
    }
  });

  // ─── Multi-Project Git Management ────────────────────────────────

  app.get("/api/runtime/projects", async (_req, res) => {
    const projects = await storage.listManagedProjects();
    res.json(projects);
  });

  app.post("/api/runtime/projects", async (req, res) => {
    const parsed = createProjectSchema.safeParse(req.body);
    if (!parsed.success) {
      return res.status(400).json({ error: parsed.error.flatten() });
    }
    const project = await storage.createManagedProject(parsed.data);
    await storage.addAuditLog({
      action: "project_created",
      entity_type: "managed_project",
      entity_id: project.id,
      actor: "admin",
      detail: `Created project "${project.name}" with repo ${project.repo_url}`,
    });
    res.status(201).json(project);
  });

  app.get("/api/runtime/projects/:id", async (req, res) => {
    const project = await storage.getManagedProject(req.params.id);
    if (!project) {
      return res.status(404).json({ error: "Project not found" });
    }
    const nodeStatuses = await storage.listProjectNodeStatuses(project.id);
    res.json({ ...project, nodes: nodeStatuses });
  });

  app.delete("/api/runtime/projects/:id", async (req, res) => {
    const project = await storage.getManagedProject(req.params.id);
    if (!project) {
      return res.status(404).json({ error: "Project not found" });
    }
    await storage.deleteManagedProject(req.params.id);
    await storage.addAuditLog({
      action: "project_deleted",
      entity_type: "managed_project",
      entity_id: req.params.id,
      actor: "admin",
      detail: `Deleted project "${project.name}"`,
    });
    res.json({ removed: true, id: req.params.id });
  });

  app.post("/api/runtime/projects/:id/clone", async (req, res) => {
    const project = await storage.getManagedProject(req.params.id);
    if (!project) {
      return res.status(404).json({ error: "Project not found" });
    }

    const targetNodeId = req.body?.node_id || project.primary_node_id;
    if (!targetNodeId) {
      return res.status(400).json({ error: "No target node specified. Provide node_id in body or set primary_node_id on project." });
    }

    await storage.updateManagedProjectStatus(project.id, "cloning", {
      primary_node_id: targetNodeId,
      error_message: null,
    });
    await storage.upsertProjectNodeStatus(project.id, targetNodeId, "cloning");

    try {
      const worker = await storage.getWorker(targetNodeId);
      if (!worker || !worker.url) {
        throw new Error(`Worker "${targetNodeId}" not found or has no URL`);
      }

      const agentKey = process.env.MEMBRIDGE_AGENT_KEY || "";
      const cloneResponse = await fetch(`${worker.url}/clone`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-MEMBRIDGE-AGENT": agentKey,
        },
        body: JSON.stringify({
          repo_url: project.repo_url,
          project_name: project.name,
          target_path: project.target_path || undefined,
        }),
        signal: AbortSignal.timeout(60000),
      });

      if (!cloneResponse.ok) {
        const errText = await cloneResponse.text();
        throw new Error(`Agent returned ${cloneResponse.status}: ${errText}`);
      }

      const cloneResult = await cloneResponse.json();
      await storage.updateManagedProjectStatus(project.id, "cloned");
      await storage.upsertProjectNodeStatus(project.id, targetNodeId, "cloned", {
        last_sync_at: Date.now(),
        repo_path: cloneResult.path || project.target_path,
      });

      await storage.addAuditLog({
        action: "project_cloned",
        entity_type: "managed_project",
        entity_id: project.id,
        actor: "admin",
        detail: `Cloned "${project.repo_url}" on node ${targetNodeId}`,
      });

      res.json({ status: "cloned", node: targetNodeId, result: cloneResult });
    } catch (err: any) {
      await storage.updateManagedProjectStatus(project.id, "failed", {
        error_message: err.message,
      });
      await storage.upsertProjectNodeStatus(project.id, targetNodeId, "failed", {
        error_message: err.message,
      });
      res.status(502).json({ error: err.message });
    }
  });

  app.post("/api/runtime/projects/:id/propagate", async (req, res) => {
    const project = await storage.getManagedProject(req.params.id);
    if (!project) {
      return res.status(404).json({ error: "Project not found" });
    }

    const workers = await storage.listWorkers();
    const nodeStatuses = await storage.listProjectNodeStatuses(project.id);
    const clonedNodes = new Set(nodeStatuses.filter(ns => ns.clone_status === "cloned" || ns.clone_status === "synced").map(ns => ns.node_id));

    const targetNodes = workers.filter(w => !clonedNodes.has(w.id) && w.url);
    if (targetNodes.length === 0) {
      return res.json({ status: "nothing_to_propagate", message: "All nodes already have this project" });
    }

    await storage.updateManagedProjectStatus(project.id, "propagating");

    const results: { node_id: string; status: string; error?: string }[] = [];
    const agentKey = process.env.MEMBRIDGE_AGENT_KEY || "";

    for (const worker of targetNodes) {
      await storage.upsertProjectNodeStatus(project.id, worker.id, "cloning");
      try {
        const cloneResponse = await fetch(`${worker.url}/clone`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-MEMBRIDGE-AGENT": agentKey,
          },
          body: JSON.stringify({
            repo_url: project.repo_url,
            project_name: project.name,
            target_path: project.target_path || undefined,
          }),
          signal: AbortSignal.timeout(60000),
        });

        if (!cloneResponse.ok) {
          const errText = await cloneResponse.text();
          throw new Error(`Agent returned ${cloneResponse.status}: ${errText}`);
        }

        const cloneResult = await cloneResponse.json();
        await storage.upsertProjectNodeStatus(project.id, worker.id, "cloned", {
          last_sync_at: Date.now(),
          repo_path: cloneResult.path || project.target_path,
        });
        results.push({ node_id: worker.id, status: "cloned" });
      } catch (err: any) {
        await storage.upsertProjectNodeStatus(project.id, worker.id, "failed", {
          error_message: err.message,
        });
        results.push({ node_id: worker.id, status: "failed", error: err.message });
      }
    }

    const allCloned = results.every(r => r.status === "cloned");
    await storage.updateManagedProjectStatus(project.id, allCloned ? "synced" : "failed");

    await storage.addAuditLog({
      action: "project_propagated",
      entity_type: "managed_project",
      entity_id: project.id,
      actor: "admin",
      detail: `Propagated to ${results.filter(r => r.status === "cloned").length}/${targetNodes.length} nodes`,
    });

    res.json({ status: allCloned ? "synced" : "partial", results });
  });

  app.post("/api/runtime/projects/:id/sync-memory", async (req, res) => {
    const project = await storage.getManagedProject(req.params.id);
    if (!project) {
      return res.status(404).json({ error: "Project not found" });
    }

    const direction = req.body?.direction || "push";
    const targetNodeId = req.body?.node_id || project.primary_node_id;
    if (!targetNodeId) {
      return res.status(400).json({ error: "No target node specified" });
    }

    try {
      const response = await membridgeFetch(`/sync/${direction}`, {
        method: "POST",
        body: JSON.stringify({
          agent_name: targetNodeId,
          project_name: project.name,
        }),
      });
      if (!response.ok) {
        const text = await response.text();
        throw new Error(`Membridge returned ${response.status}: ${text}`);
      }
      const data = await response.json();
      await storage.addAuditLog({
        action: `memory_sync_${direction}`,
        entity_type: "managed_project",
        entity_id: project.id,
        actor: "admin",
        detail: `${direction} memory sync for "${project.name}" via node ${targetNodeId}`,
      });
      res.json({ status: "ok", direction, node: targetNodeId, result: data });
    } catch (err: any) {
      res.status(502).json({ error: err.message });
    }
  });

  app.get("/api/runtime/projects/:id/node-status", async (req, res) => {
    const project = await storage.getManagedProject(req.params.id);
    if (!project) {
      return res.status(404).json({ error: "Project not found" });
    }
    const nodeStatuses = await storage.listProjectNodeStatuses(project.id);
    res.json(nodeStatuses);
  });

  // ─── Runtime Stats ─────────────────────────────────────────────

  app.get("/api/runtime/stats", async (_req, res) => {
    const [tasks, activeLeases, workers] = await Promise.all([
      storage.listTasks(),
      storage.listLeases(),
      storage.listWorkers(),
    ]);

    const tasksByStatus: Record<string, number> = {};
    for (const t of tasks) {
      tasksByStatus[t.status] = (tasksByStatus[t.status] || 0) + 1;
    }

    const activeLeasesCount = activeLeases.filter((l) => l.status === "active").length;
    const onlineWorkers = workers.filter((w) => w.status === "online").length;

    res.json({
      tasks: { total: tasks.length, by_status: tasksByStatus },
      leases: { total: activeLeases.length, active: activeLeasesCount },
      workers: { total: workers.length, online: onlineWorkers },
    });
  });

  return httpServer;
}
