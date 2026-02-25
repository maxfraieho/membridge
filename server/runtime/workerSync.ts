import { storage } from "../storage";
import { membridgeFetch } from "./membridgeClient";
import type { WorkerNode } from "@shared/schema";

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
