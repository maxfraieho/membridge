import type { Request, Response, NextFunction } from "express";
import { timingSafeEqual } from "crypto";

const UNPROTECTED_PATHS = [
  "/api/runtime/health",
  "/api/runtime/test-connection",
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

  if (UNPROTECTED_PATHS.some((p) => req.path === p)) {
    return next();
  }

  const provided = req.headers["x-runtime-api-key"] as string | undefined;

  if (!provided || !constantTimeCompare(provided, apiKey)) {
    return res.status(401).json({ error: "Unauthorized" });
  }

  next();
}
