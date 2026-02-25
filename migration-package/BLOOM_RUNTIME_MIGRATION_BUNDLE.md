# BLOOM Runtime Migration Bundle

Всі файли нижче потрібно створити в директорії `bloom-runtime/` в NotebookLM Repl.
Замініть всі `@shared/schema` на відповідні відносні шляхи.

---

## bloom-runtime/schema.ts

```typescript
import { sql } from "drizzle-orm";
import { pgTable, text, varchar, integer, boolean, bigint, jsonb } from "drizzle-orm/pg-core";
import { createInsertSchema } from "drizzle-zod";
import { z } from "zod";

export const users = pgTable("users", {
  id: varchar("id").primaryKey().default(sql`gen_random_uuid()`),
  username: text("username").notNull().unique(),
  password: text("password").notNull(),
});

export const insertUserSchema = createInsertSchema(users).pick({
  username: true,
  password: true,
});

export type InsertUser = z.infer<typeof insertUserSchema>;
export type User = typeof users.$inferSelect;

export const llmTasks = pgTable("llm_tasks", {
  id: varchar("id").primaryKey(),
  context_id: text("context_id").notNull(),
  agent_slug: text("agent_slug").notNull(),
  prompt: text("prompt").notNull(),
  context_hints: jsonb("context_hints").$type<string[]>().notNull().default([]),
  policy: jsonb("policy").$type<{ timeout_sec: number; budget: number }>().notNull().default({ timeout_sec: 120, budget: 0 }),
  desired_format: text("desired_format").$type<"json" | "text">().notNull().default("text"),
  status: text("status").$type<TaskStatus>().notNull().default("queued"),
  created_at: bigint("created_at", { mode: "number" }).notNull(),
  updated_at: bigint("updated_at", { mode: "number" }).notNull(),
  lease_id: varchar("lease_id"),
  worker_id: varchar("worker_id"),
  attempts: integer("attempts").notNull().default(0),
  max_attempts: integer("max_attempts").notNull().default(3),
});

export const leases = pgTable("leases", {
  id: varchar("id").primaryKey(),
  task_id: varchar("task_id").notNull(),
  worker_id: varchar("worker_id").notNull(),
  started_at: bigint("started_at", { mode: "number" }).notNull(),
  expires_at: bigint("expires_at", { mode: "number" }).notNull(),
  ttl_seconds: integer("ttl_seconds").notNull(),
  status: text("status").$type<LeaseStatus>().notNull().default("active"),
  last_heartbeat: bigint("last_heartbeat", { mode: "number" }).notNull(),
  context_id: varchar("context_id"),
});

export const workers = pgTable("workers", {
  id: varchar("id").primaryKey(),
  node_id: text("node_id").notNull(),
  url: text("url").notNull().default(""),
  status: text("status").$type<WorkerStatus>().notNull().default("unknown"),
  capabilities: jsonb("capabilities").$type<WorkerCapability>().notNull().default({ claude_cli: true, max_concurrency: 1, labels: [] }),
  last_heartbeat: bigint("last_heartbeat", { mode: "number" }),
  ip_addrs: jsonb("ip_addrs").$type<string[]>().notNull().default([]),
  obs_count: integer("obs_count").notNull().default(0),
  db_sha: text("db_sha").notNull().default(""),
  registered_at: bigint("registered_at", { mode: "number" }).notNull(),
  active_leases: integer("active_leases").notNull().default(0),
});

export const runtimeArtifacts = pgTable("runtime_artifacts", {
  id: varchar("id").primaryKey(),
  task_id: varchar("task_id").notNull(),
  job_id: varchar("job_id"),
  type: text("type").notNull(),
  created_at: bigint("created_at", { mode: "number" }).notNull(),
  finalized: boolean("finalized").notNull().default(false),
  url: text("url"),
  entity_refs: jsonb("entity_refs").$type<string[]>().notNull().default([]),
  tags: jsonb("tags").$type<string[]>().notNull().default([]),
  content: text("content"),
});

export const llmResults = pgTable("llm_results", {
  id: varchar("id").primaryKey(),
  task_id: varchar("task_id").notNull(),
  worker_id: varchar("worker_id").notNull(),
  artifact_id: varchar("artifact_id").notNull(),
  status: text("status").$type<"success" | "error">().notNull(),
  output: text("output"),
  error_message: text("error_message"),
  metrics: jsonb("metrics").$type<{ duration_ms: number; tokens_used?: number }>().notNull(),
  completed_at: bigint("completed_at", { mode: "number" }).notNull(),
});

export const auditLogs = pgTable("audit_logs", {
  id: varchar("id").primaryKey(),
  timestamp: bigint("timestamp", { mode: "number" }).notNull(),
  action: text("action").notNull(),
  entity_type: text("entity_type").notNull(),
  entity_id: varchar("entity_id").notNull(),
  actor: text("actor").notNull(),
  detail: text("detail").notNull(),
});

export const runtimeSettings = pgTable("runtime_settings", {
  key: varchar("key").primaryKey(),
  value: text("value").notNull(),
});

export type WorkerStatus = "online" | "offline" | "syncing" | "error" | "unknown";

export type TaskStatus = "queued" | "leased" | "running" | "completed" | "failed" | "dead";

export type LeaseStatus = "active" | "expired" | "released" | "failed";

export interface WorkerCapability {
  claude_cli: boolean;
  max_concurrency: number;
  labels: string[];
}

export interface WorkerNode {
  id: string;
  node_id: string;
  url: string;
  status: WorkerStatus;
  capabilities: WorkerCapability;
  last_heartbeat: number | null;
  ip_addrs: string[];
  obs_count: number;
  db_sha: string;
  registered_at: number;
  active_leases: number;
}

export interface Lease {
  id: string;
  task_id: string;
  worker_id: string;
  started_at: number;
  expires_at: number;
  ttl_seconds: number;
  status: LeaseStatus;
  last_heartbeat: number;
  context_id: string | null;
}

export interface LLMTask {
  id: string;
  context_id: string;
  agent_slug: string;
  prompt: string;
  context_hints: string[];
  policy: {
    timeout_sec: number;
    budget: number;
  };
  desired_format: "json" | "text";
  status: TaskStatus;
  created_at: number;
  updated_at: number;
  lease_id: string | null;
  worker_id: string | null;
  attempts: number;
  max_attempts: number;
}

export interface LLMResult {
  id: string;
  task_id: string;
  worker_id: string;
  artifact_id: string;
  status: "success" | "error";
  output: string | null;
  error_message: string | null;
  metrics: {
    duration_ms: number;
    tokens_used?: number;
  };
  completed_at: number;
}

export interface RuntimeArtifact {
  id: string;
  task_id: string;
  job_id: string | null;
  type: string;
  created_at: number;
  finalized: boolean;
  url: string | null;
  entity_refs: string[];
  tags: string[];
  content: string | null;
}

export interface RuntimeConfig {
  membridge_server_url: string;
  admin_key_masked: string;
  connected: boolean;
  last_test: number | null;
}

export interface AuditLogEntry {
  id: string;
  timestamp: number;
  action: string;
  entity_type: string;
  entity_id: string;
  actor: string;
  detail: string;
}

export const insertLLMTaskSchema = z.object({
  context_id: z.string().min(1),
  agent_slug: z.string().min(1),
  prompt: z.string().min(1),
  context_hints: z.array(z.string()).default([]),
  policy: z.object({
    timeout_sec: z.number().int().min(1).max(3600).default(120),
    budget: z.number().min(0).default(0),
  }).default({ timeout_sec: 120, budget: 0 }),
  desired_format: z.enum(["json", "text"]).default("text"),
  max_attempts: z.number().int().min(1).max(10).default(3),
});

export type InsertLLMTask = z.infer<typeof insertLLMTaskSchema>;

export const completeTaskSchema = z.object({
  status: z.enum(["success", "error"]),
  output: z.string().nullable().default(null),
  error_message: z.string().nullable().default(null),
  metrics: z.object({
    duration_ms: z.number().int().min(0),
    tokens_used: z.number().int().min(0).optional(),
  }),
  artifact_type: z.string().default("LLM_RESULT"),
  artifact_tags: z.array(z.string()).default([]),
});

export type CompleteTaskInput = z.infer<typeof completeTaskSchema>;

export const runtimeConfigSchema = z.object({
  membridge_server_url: z.string().url(),
  admin_key: z.string().min(1),
});

export type RuntimeConfigInput = z.infer<typeof runtimeConfigSchema>;

export const registerWorkerSchema = z.object({
  name: z.string().min(1).max(128),
  url: z.string().optional(),
  status: z.enum(["online", "offline", "syncing", "error", "unknown"]).optional().default("online"),
  capabilities: z.object({
    claude_cli: z.boolean().default(true),
    max_concurrency: z.number().int().min(1).max(32).default(1),
    labels: z.array(z.string()).default([]),
  }).optional(),
  ip_addrs: z.array(z.string()).optional(),
});

export type RegisterWorkerInput = z.infer<typeof registerWorkerSchema>;
```

---

## bloom-runtime/db.ts

```typescript
import { drizzle } from "drizzle-orm/node-postgres";
import { Pool } from "pg";
import * as schema from "./schema";

if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL must be set");
}

export const pool = new Pool({ connectionString: process.env.DATABASE_URL });
export const db = drizzle(pool, { schema });
```

---

## bloom-runtime/storage.ts

```typescript
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
} from "./schema";
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
```

---

## bloom-runtime/middleware/runtimeAuth.ts

```typescript
import type { Request, Response, NextFunction } from "express";
import { timingSafeEqual } from "crypto";

const UNPROTECTED_PATHS = [
  "/api/runtime/health",
  "/api/runtime/test-connection",
];

const UNPROTECTED_SUFFIXES = [
  "/health",
  "/test-connection",
];

function constantTimeCompare(a: string, b: string): boolean {
  if (a.length !== b.length) {
    const dummy = Buffer.alloc(a.length);
    timingSafeEqual(dummy, Buffer.from(a));
    return false;
  }
  return timingSafeEqual(Buffer.from(a), Buffer.from(b));
}

export function runtimeAuthMiddleware(req: Request, res: Response, next: NextFunction) {
  const apiKey = process.env.RUNTIME_API_KEY;

  if (!apiKey) {
    return next();
  }

  const fullPath = req.originalUrl?.split("?")[0] || req.path;
  if (
    UNPROTECTED_PATHS.some((p) => fullPath === p) ||
    UNPROTECTED_SUFFIXES.some((s) => req.path === s)
  ) {
    return next();
  }

  const provided = req.headers["x-runtime-api-key"] as string | undefined;

  if (!provided || !constantTimeCompare(provided, apiKey)) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  next();
}
```

---

## bloom-runtime/runtime/membridgeClient.ts

```typescript
import { storage } from "../storage";

const DEFAULT_TIMEOUT_MS = 10000;
const MAX_RETRIES = 3;
const INITIAL_BACKOFF_MS = 500;

interface MembridgeClientState {
  consecutiveFailures: number;
  lastSuccess: number | null;
  lastError: string | null;
}

const state: MembridgeClientState = {
  consecutiveFailures: 0,
  lastSuccess: null,
  lastError: null,
};

async function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function membridgeFetch(
  path: string,
  options?: RequestInit & { retries?: number; timeoutMs?: number }
): Promise<Response> {
  const baseUrl = storage.getMembridgeUrl();
  const adminKey = storage.getAdminKey();
  const url = `${baseUrl}${path}`;
  const maxRetries = options?.retries ?? MAX_RETRIES;
  const timeoutMs = options?.timeoutMs ?? DEFAULT_TIMEOUT_MS;

  let lastError: Error | null = null;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    if (attempt > 0) {
      const backoff = INITIAL_BACKOFF_MS * Math.pow(2, attempt - 1);
      const jitter = Math.random() * backoff * 0.3;
      await sleep(backoff + jitter);
    }

    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);

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

      clearTimeout(timeout);

      if (res.ok || res.status < 500) {
        state.consecutiveFailures = 0;
        state.lastSuccess = Date.now();
        state.lastError = null;
        storage.setConnectionStatus(true);
        return res;
      }

      lastError = new Error(`HTTP ${res.status}: ${res.statusText}`);
      state.lastError = lastError.message;

      if (res.status >= 500 && attempt < maxRetries) {
        continue;
      }

      return res;
    } catch (err: any) {
      clearTimeout(timeout);
      lastError = err;
      state.consecutiveFailures++;
      state.lastError = err.message || "Connection failed";

      if (err.name === "AbortError") {
        state.lastError = `Timeout after ${timeoutMs}ms`;
      }

      if (attempt < maxRetries) {
        continue;
      }
    }
  }

  storage.setConnectionStatus(false);
  throw lastError || new Error("membridgeFetch failed after retries");
}

export function getMembridgeClientState(): MembridgeClientState & { connected: boolean } {
  return {
    ...state,
    connected: state.consecutiveFailures === 0 && state.lastSuccess !== null,
  };
}
```

---

## bloom-runtime/runtime/workerSync.ts

```typescript
import { storage } from "../storage";
import { membridgeFetch } from "./membridgeClient";
import type { WorkerNode } from "../schema";

const SYNC_INTERVAL_MS = 10000;
let syncTimer: ReturnType<typeof setInterval> | null = null;
let running = false;

async function syncWorkers(): Promise<void> {
  if (running) return;
  running = true;

  try {
    const res = await membridgeFetch("/agents", { retries: 1, timeoutMs: 8000 });
    if (!res.ok) {
      return;
    }

    const agents: any[] = await res.json();
    const seenIds = new Set<string>();

    for (const agent of agents) {
      const id = agent.name || agent.node_id || agent.id;
      if (!id) continue;
      seenIds.add(id);

      const existing = await storage.getWorker(id);
      const worker: WorkerNode = {
        id,
        node_id: agent.name || agent.node_id || id,
        url: agent.url || existing?.url || "",
        status: agent.status || "unknown",
        capabilities: {
          claude_cli: agent.capabilities?.claude_cli ?? true,
          max_concurrency: agent.capabilities?.max_concurrency || agent.max_concurrency || 1,
          labels: agent.capabilities?.labels || agent.labels || [],
        },
        last_heartbeat: agent.last_seen || Date.now(),
        ip_addrs: agent.ip_addrs || existing?.ip_addrs || [],
        obs_count: agent.obs_count || existing?.obs_count || 0,
        db_sha: agent.db_sha || existing?.db_sha || "",
        registered_at: existing?.registered_at || Date.now(),
        active_leases: 0,
      };

      await storage.upsertWorker(worker);
    }

    const localWorkers = await storage.listWorkers();
    for (const w of localWorkers) {
      if (!seenIds.has(w.id) && w.status === "online") {
        const staleMs = Date.now() - (w.last_heartbeat || 0);
        if (staleMs > 60000) {
          await storage.upsertWorker({ ...w, status: "offline" });
        }
      }
    }
  } catch (_err) {
  } finally {
    running = false;
  }
}

export function startWorkerSync(): void {
  if (syncTimer) return;
  syncWorkers();
  syncTimer = setInterval(syncWorkers, SYNC_INTERVAL_MS);
  console.log("[worker-sync] started, interval 10s");
}

export function stopWorkerSync(): void {
  if (syncTimer) {
    clearInterval(syncTimer);
    syncTimer = null;
    console.log("[worker-sync] stopped");
  }
}
```

---

## bloom-runtime/runtime/minioArtifacts.ts

```typescript
import * as Minio from "minio";

const MINIO_ENDPOINT = process.env.MINIO_ENDPOINT || "";
const MINIO_PORT = parseInt(process.env.MINIO_PORT || "9000", 10);
const MINIO_ACCESS_KEY = process.env.MINIO_ACCESS_KEY || "";
const MINIO_SECRET_KEY = process.env.MINIO_SECRET_KEY || "";
const MINIO_BUCKET = process.env.MINIO_ARTIFACT_BUCKET || "bloom-artifacts";
const MINIO_USE_SSL = process.env.MINIO_USE_SSL === "true";

let client: Minio.Client | null = null;
let bucketEnsured = false;

export function isMinioConfigured(): boolean {
  return !!(MINIO_ENDPOINT && MINIO_ACCESS_KEY && MINIO_SECRET_KEY);
}

function getClient(): Minio.Client {
  if (!client) {
    client = new Minio.Client({
      endPoint: MINIO_ENDPOINT,
      port: MINIO_PORT,
      useSSL: MINIO_USE_SSL,
      accessKey: MINIO_ACCESS_KEY,
      secretKey: MINIO_SECRET_KEY,
    });
  }
  return client;
}

async function ensureBucket(): Promise<void> {
  if (bucketEnsured) return;
  const mc = getClient();
  const exists = await mc.bucketExists(MINIO_BUCKET);
  if (!exists) {
    await mc.makeBucket(MINIO_BUCKET, "");
    console.log(`[minio] created bucket: ${MINIO_BUCKET}`);
  }
  bucketEnsured = true;
}

export async function uploadArtifactToMinio(
  objectKey: string,
  content: string
): Promise<string> {
  await ensureBucket();
  const mc = getClient();
  const buf = Buffer.from(content, "utf-8");
  await mc.putObject(MINIO_BUCKET, objectKey, buf, buf.length, {
    "Content-Type": "application/json",
  });
  return `minio://${MINIO_BUCKET}/${objectKey}`;
}

export async function getMinioArtifactUrl(
  objectKey: string,
  expirySeconds = 3600
): Promise<string> {
  const mc = getClient();
  return mc.presignedGetObject(MINIO_BUCKET, objectKey, expirySeconds);
}

export async function downloadArtifactFromMinio(objectKey: string): Promise<string> {
  const mc = getClient();
  const stream = await mc.getObject(MINIO_BUCKET, objectKey);
  const chunks: Buffer[] = [];
  for await (const chunk of stream) {
    chunks.push(Buffer.isBuffer(chunk) ? chunk : Buffer.from(chunk));
  }
  return Buffer.concat(chunks).toString("utf-8");
}
```

---

## bloom-runtime/routes.ts

```typescript
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
  type WorkerNode,
  type TaskStatus,
} from "./schema";

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
```

---

## bloom-runtime/server.ts

```typescript
import express from "express";
import { createServer } from "http";
import { registerRoutes } from "./routes";

const app = express();
const httpServer = createServer(app);

app.use(express.json());
app.use(express.urlencoded({ extended: false }));

app.use((req, res, next) => {
  const start = Date.now();
  const path = req.path;

  res.on("finish", () => {
    const duration = Date.now() - start;
    if (path.startsWith("/api")) {
      console.log(`[bloom-runtime] ${req.method} ${path} ${res.statusCode} in ${duration}ms`);
    }
  });

  next();
});

(async () => {
  await registerRoutes(httpServer, app);

  app.use((err: any, _req: express.Request, res: express.Response, _next: express.NextFunction) => {
    const status = err.status || err.statusCode || 500;
    const message = err.message || "Internal Server Error";
    console.error("[bloom-runtime] Error:", err);
    if (!res.headersSent) {
      res.status(status).json({ message });
    }
  });

  const port = parseInt(process.env.BLOOM_RUNTIME_PORT || "3002", 10);
  httpServer.listen({ port, host: "0.0.0.0" }, () => {
    console.log(`[bloom-runtime] serving on port ${port}`);
  });
})();
```

---

## bloom-runtime/drizzle.config.ts

```typescript
import { defineConfig } from "drizzle-kit";

if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL must be set");
}

export default defineConfig({
  out: "./bloom-runtime/migrations",
  schema: "./bloom-runtime/schema.ts",
  dialect: "postgresql",
  dbCredentials: {
    url: process.env.DATABASE_URL,
  },
});
```

---

## .replit workflow additions

Add to `.replit`:

```toml
[[workflows.workflow]]
name = "BLOOM Runtime"
author = "agent"

[[workflows.workflow.tasks]]
task = "shell.exec"
args = "npx tsx bloom-runtime/server.ts"
waitForPort = 3002

[workflows.workflow.metadata]
outputType = "console"

[[ports]]
localPort = 3002
externalPort = 3002
```

Add to the parallel "Project" workflow tasks:

```toml
[[workflows.workflow.tasks]]
task = "workflow.run"
args = "BLOOM Runtime"
```
