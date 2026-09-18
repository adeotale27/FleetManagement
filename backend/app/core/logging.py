import logging
import uuid
from time import perf_counter
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


def configure_logging(level: str = "INFO") -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s request_id=%(request_id)s tenant_id=%(tenant_id)s %(message)s",
    )


class RequestContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = getattr(record, "request_id", "-")
        record.tenant_id = getattr(record, "tenant_id", "-")
        return True


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid.uuid4()))
        request.state.request_id = request_id
        start = perf_counter()
        response = await call_next(request)
        duration_ms = int((perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Response-Time-ms"] = str(duration_ms)
        logging.getLogger("app.http").info(
            "%s %s %s %sms",
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
            extra={"request_id": request_id, "tenant_id": getattr(request.state, "tenant_id", "-")},
        )
        return response
