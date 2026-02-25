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
