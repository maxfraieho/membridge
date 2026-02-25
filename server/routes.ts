import type { Express } from "express";
import { createServer, type Server } from "http";
import { storage } from "./storage";
import {
  insertLLMTaskSchema,
  completeTaskSchema,
  runtimeConfigSchema,
  type WorkerNode,
  type TaskStatus,
} from "@shared/schema";

const LEASE_TTL_SECONDS = 300;
const MEMBRIDGE_TIMEOUT_MS = 10000;

async function membridgeFetch(path: string, options?: RequestInit): Promise<Response> {
  const baseUrl = storage.getMembridgeUrl();
  const adminKey = storage.getAdminKey();

  const url = `${baseUrl}${path}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), MEMBRIDGE_TIMEOUT_MS);

  try {
    const res = await fetch(url, {
      ...options,
      signal: controller.signal,
      headers: {
        "Content-Type": "application/json",
        "X-MEMBRIDGE-ADMIN": adminKey,
        ...(options?.headers || {}),
      },
    });
    return res;
  } finally {
    clearTimeout(timeout);
  }
}

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

  setInterval(async () => {
    const expired = await storage.expireStaleLeases();
    if (expired > 0) {
      console.log(`[runtime] expired ${expired} stale lease(s), requeued tasks`);
    }
  }, 30000);

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

  app.post("/api/runtime/test-connection", async (_req, res) => {
    try {
      const response = await membridgeFetch("/health");
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
      const [agentsRes, localWorkers] = await Promise.all([
        membridgeFetch("/agents").catch(() => null),
        storage.listWorkers(),
      ]);

      const merged = new Map<string, WorkerNode>();
      for (const w of localWorkers) {
        merged.set(w.id, w);
      }

      if (agentsRes && agentsRes.ok) {
        const agents: any[] = await agentsRes.json();
        for (const agent of agents) {
          const id = agent.name || agent.node_id || agent.id;
          if (!merged.has(id)) {
            const worker: WorkerNode = {
              id,
              node_id: agent.name || agent.node_id || id,
              url: agent.url || "",
              status: agent.status || "unknown",
              capabilities: {
                claude_cli: true,
                max_concurrency: agent.max_concurrency || 1,
                labels: agent.labels || [],
              },
              last_heartbeat: agent.last_seen || null,
              ip_addrs: agent.ip_addrs || [],
              obs_count: agent.obs_count || 0,
              db_sha: agent.db_sha || "",
              registered_at: agent.registered_at || Date.now(),
              active_leases: 0,
            };
            merged.set(id, worker);
            await storage.upsertWorker(worker);
          } else {
            const existing = merged.get(id)!;
            existing.status = agent.status || existing.status;
            existing.last_heartbeat = agent.last_seen || existing.last_heartbeat;
            if (agent.ip_addrs) existing.ip_addrs = agent.ip_addrs;
            if (agent.obs_count) existing.obs_count = agent.obs_count;
            merged.set(id, existing);
            await storage.upsertWorker(existing);
          }
        }
      }

      for (const w of Array.from(merged.values())) {
        w.active_leases = 0;
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
      res.json(await storage.listWorkers());
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

    const artifact = await storage.createArtifact({
      task_id: task.id,
      job_id: null,
      type: input.artifact_type,
      created_at: now,
      finalized: true,
      url: null,
      entity_refs: [],
      tags: input.artifact_tags,
      content: input.output,
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

  app.get("/api/runtime/runs", async (req, res) => {
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

  app.get("/api/runtime/stats", async (_req, res) => {
    const [tasks, leases, workers] = await Promise.all([
      storage.listTasks(),
      storage.listLeases(),
      storage.listWorkers(),
    ]);

    const tasksByStatus: Record<string, number> = {};
    for (const t of tasks) {
      tasksByStatus[t.status] = (tasksByStatus[t.status] || 0) + 1;
    }

    const activeLeases = leases.filter((l) => l.status === "active").length;
    const onlineWorkers = workers.filter((w) => w.status === "online").length;

    res.json({
      tasks: { total: tasks.length, by_status: tasksByStatus },
      leases: { total: leases.length, active: activeLeases },
      workers: { total: workers.length, online: onlineWorkers },
    });
  });

  return httpServer;
}
