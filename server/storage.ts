import {
  type User,
  type InsertUser,
  type WorkerNode,
  type Lease,
  type LLMTask,
  type LLMResult,
  type RuntimeArtifact,
  type RuntimeConfig,
  type AuditLogEntry,
  type InsertLLMTask,
  type TaskStatus,
  type LeaseStatus,
  users,
  llmTasks,
  leases as leasesTable,
  workers as workersTable,
  runtimeArtifacts,
  llmResults,
  auditLogs as auditLogsTable,
  runtimeSettings,
} from "@shared/schema";
import { randomUUID } from "crypto";
import { eq, desc, and, lt } from "drizzle-orm";
import { db } from "./db";

export interface IStorage {
  getUser(id: string): Promise<User | undefined>;
  getUserByUsername(username: string): Promise<User | undefined>;
  createUser(user: InsertUser): Promise<User>;

  listWorkers(): Promise<WorkerNode[]>;
  getWorker(id: string): Promise<WorkerNode | undefined>;
  upsertWorker(worker: WorkerNode): Promise<WorkerNode>;
  removeWorker(id: string): Promise<void>;

  createTask(input: InsertLLMTask): Promise<LLMTask>;
  getTask(id: string): Promise<LLMTask | undefined>;
  listTasks(filter?: { status?: TaskStatus }): Promise<LLMTask[]>;
  updateTaskStatus(id: string, status: TaskStatus, fields?: Partial<LLMTask>): Promise<LLMTask | undefined>;

  createLease(taskId: string, workerId: string, ttlSeconds: number, contextId?: string | null): Promise<Lease>;
  getLease(id: string): Promise<Lease | undefined>;
  listLeases(filter?: { status?: LeaseStatus }): Promise<Lease[]>;
  renewLease(id: string): Promise<Lease | undefined>;
  releaseLease(id: string, status: LeaseStatus): Promise<Lease | undefined>;
  expireStaleLeases(): Promise<number>;

  createArtifact(artifact: Omit<RuntimeArtifact, "id">): Promise<RuntimeArtifact>;
  getArtifact(id: string): Promise<RuntimeArtifact | undefined>;
  listArtifacts(filter?: { task_id?: string }): Promise<RuntimeArtifact[]>;

  createResult(result: Omit<LLMResult, "id">): Promise<LLMResult>;
  listResults(filter?: { task_id?: string }): Promise<LLMResult[]>;

  getRuntimeConfig(): Promise<RuntimeConfig>;
  setRuntimeConfig(config: { membridge_server_url: string; admin_key: string }): Promise<RuntimeConfig>;

  addAuditLog(entry: Omit<AuditLogEntry, "id" | "timestamp">): Promise<AuditLogEntry>;
  listAuditLogs(limit?: number): Promise<AuditLogEntry[]>;

  getAdminKey(): string;
  getMembridgeUrl(): string;
  setConnectionStatus(connected: boolean): void;
}

function maskKey(key: string): string {
  if (key.length <= 8) return "****";
  return key.substring(0, 4) + "****" + key.substring(key.length - 4);
}

function toWorkerNode(row: typeof workersTable.$inferSelect): WorkerNode {
  return {
    id: row.id,
    node_id: row.node_id,
    url: row.url,
    status: row.status as WorkerNode["status"],
    capabilities: row.capabilities as WorkerNode["capabilities"],
    last_heartbeat: row.last_heartbeat,
    ip_addrs: (row.ip_addrs || []) as string[],
    obs_count: row.obs_count,
    db_sha: row.db_sha,
    registered_at: row.registered_at,
    active_leases: row.active_leases,
  };
}

function toTask(row: typeof llmTasks.$inferSelect): LLMTask {
  return {
    id: row.id,
    context_id: row.context_id,
    agent_slug: row.agent_slug,
    prompt: row.prompt,
    context_hints: (row.context_hints || []) as string[],
    policy: (row.policy || { timeout_sec: 120, budget: 0 }) as LLMTask["policy"],
    desired_format: row.desired_format as LLMTask["desired_format"],
    status: row.status as TaskStatus,
    created_at: row.created_at,
    updated_at: row.updated_at,
    lease_id: row.lease_id,
    worker_id: row.worker_id,
    attempts: row.attempts,
    max_attempts: row.max_attempts,
  };
}

function toLease(row: typeof leasesTable.$inferSelect): Lease {
  return {
    id: row.id,
    task_id: row.task_id,
    worker_id: row.worker_id,
    started_at: row.started_at,
    expires_at: row.expires_at,
    ttl_seconds: row.ttl_seconds,
    status: row.status as LeaseStatus,
    last_heartbeat: row.last_heartbeat,
    context_id: row.context_id,
  };
}

function toArtifact(row: typeof runtimeArtifacts.$inferSelect): RuntimeArtifact {
  return {
    id: row.id,
    task_id: row.task_id,
    job_id: row.job_id,
    type: row.type,
    created_at: row.created_at,
    finalized: row.finalized,
    url: row.url,
    entity_refs: (row.entity_refs || []) as string[],
    tags: (row.tags || []) as string[],
    content: row.content,
  };
}

function toResult(row: typeof llmResults.$inferSelect): LLMResult {
  return {
    id: row.id,
    task_id: row.task_id,
    worker_id: row.worker_id,
    artifact_id: row.artifact_id,
    status: row.status as LLMResult["status"],
    output: row.output,
    error_message: row.error_message,
    metrics: (row.metrics || { duration_ms: 0 }) as LLMResult["metrics"],
    completed_at: row.completed_at,
  };
}

function toAuditEntry(row: typeof auditLogsTable.$inferSelect): AuditLogEntry {
  return {
    id: row.id,
    timestamp: row.timestamp,
    action: row.action,
    entity_type: row.entity_type,
    entity_id: row.entity_id,
    actor: row.actor,
    detail: row.detail,
  };
}

export class DatabaseStorage implements IStorage {
  private configCache: {
    membridge_server_url: string;
    admin_key: string;
    connected: boolean;
    last_test: number | null;
  };

  constructor() {
    this.configCache = {
      membridge_server_url: process.env.MEMBRIDGE_SERVER_URL || "http://127.0.0.1:8000",
      admin_key: process.env.MEMBRIDGE_ADMIN_KEY || "",
      connected: false,
      last_test: null,
    };
  }

  async init(): Promise<void> {
    const rows = await db.select().from(runtimeSettings);
    for (const row of rows) {
      if (row.key === "membridge_server_url") this.configCache.membridge_server_url = row.value;
      if (row.key === "admin_key") this.configCache.admin_key = row.value;
      if (row.key === "connected") this.configCache.connected = row.value === "true";
      if (row.key === "last_test") this.configCache.last_test = parseInt(row.value) || null;
    }
  }

  async getUser(id: string): Promise<User | undefined> {
    const [row] = await db.select().from(users).where(eq(users.id, id));
    return row || undefined;
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    const [row] = await db.select().from(users).where(eq(users.username, username));
    return row || undefined;
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const [row] = await db.insert(users).values({ ...insertUser, id }).returning();
    return row;
  }

  async listWorkers(): Promise<WorkerNode[]> {
    const rows = await db.select().from(workersTable);
    return rows.map(toWorkerNode);
  }

  async getWorker(id: string): Promise<WorkerNode | undefined> {
    const [row] = await db.select().from(workersTable).where(eq(workersTable.id, id));
    return row ? toWorkerNode(row) : undefined;
  }

  async upsertWorker(worker: WorkerNode): Promise<WorkerNode> {
    const [row] = await db.insert(workersTable).values({
      id: worker.id,
      node_id: worker.node_id,
      url: worker.url,
      status: worker.status,
      capabilities: worker.capabilities,
      last_heartbeat: worker.last_heartbeat,
      ip_addrs: worker.ip_addrs,
      obs_count: worker.obs_count,
      db_sha: worker.db_sha,
      registered_at: worker.registered_at,
      active_leases: worker.active_leases,
    }).onConflictDoUpdate({
      target: workersTable.id,
      set: {
        node_id: worker.node_id,
        url: worker.url,
        status: worker.status,
        capabilities: worker.capabilities,
        last_heartbeat: worker.last_heartbeat,
        ip_addrs: worker.ip_addrs,
        obs_count: worker.obs_count,
        db_sha: worker.db_sha,
        active_leases: worker.active_leases,
      },
    }).returning();
    return toWorkerNode(row);
  }

  async removeWorker(id: string): Promise<void> {
    await db.delete(workersTable).where(eq(workersTable.id, id));
  }

  async createTask(input: InsertLLMTask): Promise<LLMTask> {
    const now = Date.now();
    const id = randomUUID();
    const [row] = await db.insert(llmTasks).values({
      id,
      context_id: input.context_id,
      agent_slug: input.agent_slug,
      prompt: input.prompt,
      context_hints: input.context_hints,
      policy: input.policy,
      desired_format: input.desired_format,
      status: "queued",
      created_at: now,
      updated_at: now,
      attempts: 0,
      max_attempts: input.max_attempts,
    }).returning();
    return toTask(row);
  }

  async getTask(id: string): Promise<LLMTask | undefined> {
    const [row] = await db.select().from(llmTasks).where(eq(llmTasks.id, id));
    return row ? toTask(row) : undefined;
  }

  async listTasks(filter?: { status?: TaskStatus }): Promise<LLMTask[]> {
    let query = db.select().from(llmTasks);
    if (filter?.status) {
      query = query.where(eq(llmTasks.status, filter.status)) as any;
    }
    const rows = await (query as any).orderBy(desc(llmTasks.created_at));
    return rows.map(toTask);
  }

  async updateTaskStatus(id: string, status: TaskStatus, fields?: Partial<LLMTask>): Promise<LLMTask | undefined> {
    const updates: Record<string, any> = {
      status,
      updated_at: Date.now(),
    };
    if (fields?.lease_id !== undefined) updates.lease_id = fields.lease_id;
    if (fields?.worker_id !== undefined) updates.worker_id = fields.worker_id;
    if (fields?.attempts !== undefined) updates.attempts = fields.attempts;

    const [row] = await db.update(llmTasks).set(updates).where(eq(llmTasks.id, id)).returning();
    return row ? toTask(row) : undefined;
  }

  async createLease(taskId: string, workerId: string, ttlSeconds: number, contextId?: string | null): Promise<Lease> {
    const now = Date.now();
    const id = randomUUID();
    const [row] = await db.insert(leasesTable).values({
      id,
      task_id: taskId,
      worker_id: workerId,
      started_at: now,
      expires_at: now + ttlSeconds * 1000,
      ttl_seconds: ttlSeconds,
      status: "active",
      last_heartbeat: now,
      context_id: contextId ?? null,
    }).returning();
    return toLease(row);
  }

  async getLease(id: string): Promise<Lease | undefined> {
    const [row] = await db.select().from(leasesTable).where(eq(leasesTable.id, id));
    return row ? toLease(row) : undefined;
  }

  async listLeases(filter?: { status?: LeaseStatus }): Promise<Lease[]> {
    let query = db.select().from(leasesTable);
    if (filter?.status) {
      query = query.where(eq(leasesTable.status, filter.status)) as any;
    }
    const rows = await (query as any).orderBy(desc(leasesTable.started_at));
    return rows.map(toLease);
  }

  async renewLease(id: string): Promise<Lease | undefined> {
    const [existing] = await db.select().from(leasesTable).where(eq(leasesTable.id, id));
    if (!existing || existing.status !== "active") return undefined;

    const now = Date.now();
    const [row] = await db.update(leasesTable).set({
      last_heartbeat: now,
      expires_at: now + existing.ttl_seconds * 1000,
    }).where(and(eq(leasesTable.id, id), eq(leasesTable.status, "active"))).returning();
    return row ? toLease(row) : undefined;
  }

  async releaseLease(id: string, status: LeaseStatus): Promise<Lease | undefined> {
    const [row] = await db.update(leasesTable).set({ status }).where(eq(leasesTable.id, id)).returning();
    return row ? toLease(row) : undefined;
  }

  async expireStaleLeases(): Promise<number> {
    const now = Date.now();
    const stale = await db.select().from(leasesTable).where(
      and(eq(leasesTable.status, "active"), lt(leasesTable.expires_at, now))
    );

    if (stale.length === 0) return 0;

    let count = 0;
    for (const lease of stale) {
      await db.transaction(async (tx) => {
        await tx.update(leasesTable).set({ status: "expired" }).where(eq(leasesTable.id, lease.id));

        const [task] = await tx.select().from(llmTasks).where(eq(llmTasks.id, lease.task_id));
        if (task && task.status === "leased") {
          if (task.attempts < task.max_attempts) {
            await tx.update(llmTasks).set({
              status: "queued",
              lease_id: null,
              worker_id: null,
              updated_at: now,
            }).where(eq(llmTasks.id, task.id));
          } else {
            await tx.update(llmTasks).set({
              status: "dead",
              updated_at: now,
            }).where(eq(llmTasks.id, task.id));
          }
        }
      });
      count++;
    }
    return count;
  }

  async createArtifact(artifact: Omit<RuntimeArtifact, "id">): Promise<RuntimeArtifact> {
    const id = randomUUID();
    const [row] = await db.insert(runtimeArtifacts).values({
      id,
      task_id: artifact.task_id,
      job_id: artifact.job_id,
      type: artifact.type,
      created_at: artifact.created_at,
      finalized: artifact.finalized,
      url: artifact.url,
      entity_refs: artifact.entity_refs,
      tags: artifact.tags,
      content: artifact.content,
    }).returning();
    return toArtifact(row);
  }

  async getArtifact(id: string): Promise<RuntimeArtifact | undefined> {
    const [row] = await db.select().from(runtimeArtifacts).where(eq(runtimeArtifacts.id, id));
    return row ? toArtifact(row) : undefined;
  }

  async listArtifacts(filter?: { task_id?: string }): Promise<RuntimeArtifact[]> {
    let query = db.select().from(runtimeArtifacts);
    if (filter?.task_id) {
      query = query.where(eq(runtimeArtifacts.task_id, filter.task_id)) as any;
    }
    const rows = await (query as any).orderBy(desc(runtimeArtifacts.created_at));
    return rows.map(toArtifact);
  }

  async createResult(result: Omit<LLMResult, "id">): Promise<LLMResult> {
    const id = randomUUID();
    const [row] = await db.insert(llmResults).values({
      id,
      task_id: result.task_id,
      worker_id: result.worker_id,
      artifact_id: result.artifact_id,
      status: result.status,
      output: result.output,
      error_message: result.error_message,
      metrics: result.metrics,
      completed_at: result.completed_at,
    }).returning();
    return toResult(row);
  }

  async listResults(filter?: { task_id?: string }): Promise<LLMResult[]> {
    let query = db.select().from(llmResults);
    if (filter?.task_id) {
      query = query.where(eq(llmResults.task_id, filter.task_id)) as any;
    }
    const rows = await (query as any).orderBy(desc(llmResults.completed_at));
    return rows.map(toResult);
  }

  async getRuntimeConfig(): Promise<RuntimeConfig> {
    return {
      membridge_server_url: this.configCache.membridge_server_url,
      admin_key_masked: this.configCache.admin_key ? maskKey(this.configCache.admin_key) : "",
      connected: this.configCache.connected,
      last_test: this.configCache.last_test,
    };
  }

  async setRuntimeConfig(config: { membridge_server_url: string; admin_key: string }): Promise<RuntimeConfig> {
    this.configCache.membridge_server_url = config.membridge_server_url;
    this.configCache.admin_key = config.admin_key;

    await db.insert(runtimeSettings).values({ key: "membridge_server_url", value: config.membridge_server_url })
      .onConflictDoUpdate({ target: runtimeSettings.key, set: { value: config.membridge_server_url } });
    await db.insert(runtimeSettings).values({ key: "admin_key", value: config.admin_key })
      .onConflictDoUpdate({ target: runtimeSettings.key, set: { value: config.admin_key } });

    return this.getRuntimeConfig();
  }

  getAdminKey(): string {
    return this.configCache.admin_key;
  }

  getMembridgeUrl(): string {
    return this.configCache.membridge_server_url;
  }

  setConnectionStatus(connected: boolean): void {
    this.configCache.connected = connected;
    this.configCache.last_test = Date.now();

    db.insert(runtimeSettings).values({ key: "connected", value: String(connected) })
      .onConflictDoUpdate({ target: runtimeSettings.key, set: { value: String(connected) } })
      .then(() => {});
    db.insert(runtimeSettings).values({ key: "last_test", value: String(this.configCache.last_test) })
      .onConflictDoUpdate({ target: runtimeSettings.key, set: { value: String(this.configCache.last_test) } })
      .then(() => {});
  }

  async addAuditLog(entry: Omit<AuditLogEntry, "id" | "timestamp">): Promise<AuditLogEntry> {
    const id = randomUUID();
    const timestamp = Date.now();
    const [row] = await db.insert(auditLogsTable).values({
      id,
      timestamp,
      action: entry.action,
      entity_type: entry.entity_type,
      entity_id: entry.entity_id,
      actor: entry.actor,
      detail: entry.detail,
    }).returning();
    return toAuditEntry(row);
  }

  async listAuditLogs(limit = 100): Promise<AuditLogEntry[]> {
    const rows = await db.select().from(auditLogsTable)
      .orderBy(desc(auditLogsTable.timestamp))
      .limit(limit);
    return rows.map(toAuditEntry);
  }
}

export const storage = new DatabaseStorage();
