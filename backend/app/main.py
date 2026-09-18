from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.exceptions import HTTPException
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from app.api.v1.router import router as v1
from app.core.config import get_settings
from app.core.exceptions import AppError, app_error_handler, http_error_handler, unhandled_error_handler
from app.core.logging import RequestIdMiddleware, configure_logging
from app.db.indexes import ensure_indexes
from app.db.mongo import close_db, enable_memory, get_db, ping_db
from app.middleware.rate_limit import RateLimitMiddleware


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=(self)"
        return response


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)
    if not await ping_db() and settings.login_hidden and not settings.is_production:
        await enable_memory()
    else:
        await ensure_indexes(get_db())
    if (settings.run_seed or settings.login_hidden) and not settings.is_production:
        from app.seed import seed_demo

        await seed_demo(get_db())
    yield
    await close_db()


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version=settings.app_version, lifespan=lifespan)
    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(SecurityHeadersMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(HTTPException, http_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
    app.include_router(v1, prefix="/api/v1")
    return app


app = create_app()
