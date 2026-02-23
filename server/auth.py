"""Authentication middleware for Membridge services."""

import os
import secrets
from typing import Optional

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import Response

HEALTH_PATHS = {"/health", "/docs", "/openapi.json", "/redoc", "/ui"}


def _is_dev_mode() -> bool:
    return os.environ.get("MEMBRIDGE_DEV", "0") == "1"


class AdminAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _is_dev_mode():
            return await call_next(request)
        if request.url.path in HEALTH_PATHS or request.url.path.startswith("/static/"):
            return await call_next(request)
        expected = os.environ.get("MEMBRIDGE_ADMIN_KEY", "")
        if not expected:
            return Response(
                content='{"detail":"MEMBRIDGE_ADMIN_KEY not configured on server"}',
                status_code=500,
                media_type="application/json",
            )
        provided = request.headers.get("X-MEMBRIDGE-ADMIN", "")
        if not provided or not secrets.compare_digest(provided, expected):
            return Response(
                content='{"detail":"Unauthorized — invalid or missing X-MEMBRIDGE-ADMIN header"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)


class AgentAuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _is_dev_mode():
            return await call_next(request)
        if request.url.path in HEALTH_PATHS:
            return await call_next(request)
        # Some agent paths are callable from localhost without key (hooks, scripts)
        _LOCAL_OPEN = {"/register_project", "/projects"}
        if request.url.path in _LOCAL_OPEN:
            client_host = request.client.host if request.client else ""
            if client_host in ("127.0.0.1", "::1", "localhost"):
                return await call_next(request)
        expected = os.environ.get("MEMBRIDGE_AGENT_KEY", "")
        if not expected:
            return Response(
                content='{"detail":"MEMBRIDGE_AGENT_KEY not configured on agent"}',
                status_code=500,
                media_type="application/json",
            )
        provided = request.headers.get("X-MEMBRIDGE-AGENT", "")
        if not provided or not secrets.compare_digest(provided, expected):
            return Response(
                content='{"detail":"Unauthorized — invalid or missing X-MEMBRIDGE-AGENT header"}',
                status_code=401,
                media_type="application/json",
            )
        return await call_next(request)
