import { sql } from "drizzle-orm";
import { pgTable, text, varchar } from "drizzle-orm/pg-core";
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
