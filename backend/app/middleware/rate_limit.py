from collections import defaultdict
from time import time
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from app.core.config import get_settings

_hits: dict[str, list[float]] = defaultdict(list)


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path.startswith("/api/v1/health"):
            return await call_next(request)
        limit = get_settings().rate_limit_per_minute
        key = request.client.host if request.client else "unknown"
        now = time()
        window = [t for t in _hits[key] if now - t < 60]
        if len(window) >= limit:
            return JSONResponse(
                status_code=429,
                content={"success": False, "error": {"code": "RATE_LIMIT", "message": "Too many requests. Wait a minute."}},
            )
        window.append(now)
        _hits[key] = window
        return await call_next(request)
