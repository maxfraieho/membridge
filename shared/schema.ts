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
