"""Application middleware for request IDs, access logging, and rate limits."""

from __future__ import annotations

import logging
import time
import uuid
from collections import defaultdict, deque
from threading import Lock

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.dependencies import error_payload
from app.db.redis import get_redis_client

logger = logging.getLogger(__name__)


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach request IDs and log request timing."""

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        request.state.request_id = request_id
        start_time = time.perf_counter()

        response = await call_next(request)

        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            "request_id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Apply a simple per-IP request limit."""

    _local_windows: dict[str, deque[float]] = defaultdict(deque)
    _lock = Lock()

    def __init__(self, app):
        """Initialize the rate limiter and attempt a Redis connection once."""

        super().__init__(app)
        try:
            self.redis = get_redis_client()
            self.redis.ping()
        except Exception:
            self.redis = None
            logger.warning("Redis unavailable for rate limiting, using local in-process fallback.")

    async def dispatch(self, request: Request, call_next):
        if not request.url.path.startswith(settings.api_v1_prefix):
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        allowed = self._check_limit(client_ip)
        if not allowed:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content=error_payload("Too many requests. Please retry in one minute.", "RATE_LIMIT_EXCEEDED"),
            )
        return await call_next(request)

    def _check_limit(self, client_ip: str) -> bool:
        """Return whether the client IP is under the current request limit."""

        max_requests = settings.rate_limit_requests_per_minute
        if self.redis is not None:
            key = f"rate-limit:{client_ip}"
            current = self.redis.incr(key)
            if current == 1:
                self.redis.expire(key, 60)
            return current <= max_requests

        now = time.time()
        with self._lock:
            window = self._local_windows[client_ip]
            while window and now - window[0] >= 60:
                window.popleft()
            if len(window) >= max_requests:
                return False
            window.append(now)
            return True
