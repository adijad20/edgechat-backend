"""
Step 5 — Middleware: request ID for tracing; global exception handler in main.py.
Step 6 — Rate limiting per IP via Redis.
Step 7 — Usage logging for authenticated requests.
"""
import uuid

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.config import settings
from app.core.redis_client import get_redis
from app.core.security import decode_token
from app.services.usage_service import log_usage


# Header we read (client can send) and echo back; we generate if missing
REQUEST_ID_HEADER = "X-Request-ID"


def _client_ip(request: Request) -> str:
    """Client IP: X-Forwarded-For (first) when behind proxy, else request.client.host."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Assigns a request ID to each request for tracing and logs.
    If the client sends X-Request-ID, we use it; otherwise we generate one.
    The same value is set on request.state and returned in the response header.
    """

    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get(REQUEST_ID_HEADER) or str(uuid.uuid4())
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[REQUEST_ID_HEADER] = request_id
        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Step 6 — Limit requests per IP using Redis (fixed window).
    Key = ratelimit:ip:<ip>; INCR each request; EXPIRE on first hit in window.
    If count > RATE_LIMIT_REQUESTS, return 429. If Redis is down, allow request (fail open).
    """

    async def dispatch(self, request: Request, call_next):
        redis = get_redis()
        if redis is None:
            return await call_next(request)

        ip = _client_ip(request)
        key = f"ratelimit:ip:{ip}"
        window = settings.RATE_LIMIT_WINDOW_SECONDS
        limit = settings.RATE_LIMIT_REQUESTS

        try:
            count = await redis.incr(key)
            if count == 1:
                await redis.expire(key, window)
            if count > limit:
                body = {"detail": "Too many requests"}
                if rid := getattr(request.state, "request_id", None):
                    body["request_id"] = rid
                response = JSONResponse(status_code=429, content=body)
                response.headers["Retry-After"] = str(window)
                if rid := getattr(request.state, "request_id", None):
                    response.headers[REQUEST_ID_HEADER] = rid
                return response
        except Exception:
            # Redis error: fail open (allow request)
            pass
        return await call_next(request)


class UsageLogMiddleware(BaseHTTPMiddleware):
    """
    Log API calls for authenticated users (Bearer token valid, type=access).
    After the request is handled, if we have user_id from JWT we append a row to api_usage.
    Logging errors are ignored so the API response is never broken.
    """

    async def dispatch(self, request: Request, call_next):
        user_id = None
        auth = request.headers.get("Authorization")
        if auth and auth.startswith("Bearer "):
            token = auth[7:].strip()
            payload = decode_token(token)
            if payload and payload.get("type") == "access":
                try:
                    user_id = int(payload["sub"])
                except (ValueError, KeyError):
                    pass
        response = await call_next(request)
        if user_id is not None:
            try:
                await log_usage(user_id, request.url.path, request.method)
            except Exception:
                pass
        return response
