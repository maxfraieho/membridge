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
