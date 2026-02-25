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
  type CompleteTaskInput,
  type TaskStatus,
  type LeaseStatus,
} from "@shared/schema";
import { randomUUID } from "crypto";

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

export class MemStorage implements IStorage {
  private users: Map<string, User>;
  private workers: Map<string, WorkerNode>;
  private tasks: Map<string, LLMTask>;
  private leases: Map<string, Lease>;
  private artifacts: Map<string, RuntimeArtifact>;
  private results: Map<string, LLMResult>;
  private auditLogs: AuditLogEntry[];
  private runtimeConfig: { membridge_server_url: string; admin_key: string; last_test: number | null; connected: boolean };

  constructor() {
    this.users = new Map();
    this.workers = new Map();
    this.tasks = new Map();
    this.leases = new Map();
    this.artifacts = new Map();
    this.results = new Map();
    this.auditLogs = [];
    this.runtimeConfig = {
      membridge_server_url: process.env.MEMBRIDGE_SERVER_URL || "http://127.0.0.1:8000",
      admin_key: process.env.MEMBRIDGE_ADMIN_KEY || "",
      last_test: null,
      connected: false,
    };
  }

  async getUser(id: string): Promise<User | undefined> {
    return this.users.get(id);
  }

  async getUserByUsername(username: string): Promise<User | undefined> {
    return Array.from(this.users.values()).find((user) => user.username === username);
  }

  async createUser(insertUser: InsertUser): Promise<User> {
    const id = randomUUID();
    const user: User = { ...insertUser, id };
    this.users.set(id, user);
    return user;
  }

  async listWorkers(): Promise<WorkerNode[]> {
    return Array.from(this.workers.values());
  }

  async getWorker(id: string): Promise<WorkerNode | undefined> {
    return this.workers.get(id);
  }

  async upsertWorker(worker: WorkerNode): Promise<WorkerNode> {
    this.workers.set(worker.id, worker);
    return worker;
  }

  async removeWorker(id: string): Promise<void> {
    this.workers.delete(id);
  }

  async createTask(input: InsertLLMTask): Promise<LLMTask> {
    const now = Date.now();
    const task: LLMTask = {
      id: randomUUID(),
      context_id: input.context_id,
      agent_slug: input.agent_slug,
      prompt: input.prompt,
      context_hints: input.context_hints,
      policy: input.policy,
      desired_format: input.desired_format,
      status: "queued",
      created_at: now,
      updated_at: now,
      lease_id: null,
      worker_id: null,
      attempts: 0,
      max_attempts: input.max_attempts,
    };
    this.tasks.set(task.id, task);
    return task;
  }

  async getTask(id: string): Promise<LLMTask | undefined> {
    return this.tasks.get(id);
  }

  async listTasks(filter?: { status?: TaskStatus }): Promise<LLMTask[]> {
    let all = Array.from(this.tasks.values());
    if (filter?.status) {
      all = all.filter((t) => t.status === filter.status);
    }
    return all.sort((a, b) => b.created_at - a.created_at);
  }

  async updateTaskStatus(id: string, status: TaskStatus, fields?: Partial<LLMTask>): Promise<LLMTask | undefined> {
    const task = this.tasks.get(id);
    if (!task) return undefined;
    task.status = status;
    task.updated_at = Date.now();
    if (fields) {
      Object.assign(task, fields);
    }
    return task;
  }

  async createLease(taskId: string, workerId: string, ttlSeconds: number, contextId?: string | null): Promise<Lease> {
    const now = Date.now();
    const lease: Lease = {
      id: randomUUID(),
      task_id: taskId,
      worker_id: workerId,
      started_at: now,
      expires_at: now + ttlSeconds * 1000,
      ttl_seconds: ttlSeconds,
      status: "active",
      last_heartbeat: now,
      context_id: contextId ?? null,
    };
    this.leases.set(lease.id, lease);
    return lease;
  }

  async getLease(id: string): Promise<Lease | undefined> {
    return this.leases.get(id);
  }

  async listLeases(filter?: { status?: LeaseStatus }): Promise<Lease[]> {
    const all = Array.from(this.leases.values());
    if (filter?.status) {
      return all.filter((l) => l.status === filter.status);
    }
    return all.sort((a, b) => b.started_at - a.started_at);
  }

  async renewLease(id: string): Promise<Lease | undefined> {
    const lease = this.leases.get(id);
    if (!lease || lease.status !== "active") return undefined;
    lease.last_heartbeat = Date.now();
    lease.expires_at = Date.now() + lease.ttl_seconds * 1000;
    return lease;
  }

  async releaseLease(id: string, status: LeaseStatus): Promise<Lease | undefined> {
    const lease = this.leases.get(id);
    if (!lease) return undefined;
    lease.status = status;
    return lease;
  }

  async expireStaleLeases(): Promise<number> {
    const now = Date.now();
    let count = 0;
    for (const lease of Array.from(this.leases.values())) {
      if (lease.status === "active" && lease.expires_at < now) {
        lease.status = "expired";
        const task = this.tasks.get(lease.task_id);
        if (task && task.status === "leased") {
          if (task.attempts < task.max_attempts) {
            task.status = "queued";
            task.lease_id = null;
            task.worker_id = null;
            task.updated_at = now;
          } else {
            task.status = "dead";
            task.updated_at = now;
          }
        }
        count++;
      }
    }
    return count;
  }

  async createArtifact(artifact: Omit<RuntimeArtifact, "id">): Promise<RuntimeArtifact> {
    const full: RuntimeArtifact = { ...artifact, id: randomUUID() };
    this.artifacts.set(full.id, full);
    return full;
  }

  async getArtifact(id: string): Promise<RuntimeArtifact | undefined> {
    return this.artifacts.get(id);
  }

  async listArtifacts(filter?: { task_id?: string }): Promise<RuntimeArtifact[]> {
    const all = Array.from(this.artifacts.values());
    if (filter?.task_id) {
      return all.filter((a) => a.task_id === filter.task_id);
    }
    return all.sort((a, b) => b.created_at - a.created_at);
  }

  async createResult(result: Omit<LLMResult, "id">): Promise<LLMResult> {
    const full: LLMResult = { ...result, id: randomUUID() };
    this.results.set(full.id, full);
    return full;
  }

  async listResults(filter?: { task_id?: string }): Promise<LLMResult[]> {
    const all = Array.from(this.results.values());
    if (filter?.task_id) {
      return all.filter((r) => r.task_id === filter.task_id);
    }
    return all.sort((a, b) => b.completed_at - a.completed_at);
  }

  async getRuntimeConfig(): Promise<RuntimeConfig> {
    return {
      membridge_server_url: this.runtimeConfig.membridge_server_url,
      admin_key_masked: this.runtimeConfig.admin_key ? maskKey(this.runtimeConfig.admin_key) : "",
      connected: this.runtimeConfig.connected,
      last_test: this.runtimeConfig.last_test,
    };
  }

  async setRuntimeConfig(config: { membridge_server_url: string; admin_key: string }): Promise<RuntimeConfig> {
    this.runtimeConfig.membridge_server_url = config.membridge_server_url;
    this.runtimeConfig.admin_key = config.admin_key;
    return this.getRuntimeConfig();
  }

  getAdminKey(): string {
    return this.runtimeConfig.admin_key;
  }

  getMembridgeUrl(): string {
    return this.runtimeConfig.membridge_server_url;
  }

  setConnectionStatus(connected: boolean): void {
    this.runtimeConfig.connected = connected;
    this.runtimeConfig.last_test = Date.now();
  }

  async addAuditLog(entry: Omit<AuditLogEntry, "id" | "timestamp">): Promise<AuditLogEntry> {
    const full: AuditLogEntry = { ...entry, id: randomUUID(), timestamp: Date.now() };
    this.auditLogs.push(full);
    if (this.auditLogs.length > 1000) {
      this.auditLogs = this.auditLogs.slice(-500);
    }
    return full;
  }

  async listAuditLogs(limit = 100): Promise<AuditLogEntry[]> {
    return this.auditLogs.slice(-limit).reverse();
  }
}

export const storage = new MemStorage();
