from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse


class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400):
        self.code = code
        self.message = message
        self.status_code = status_code
        super().__init__(message)


class NotFoundError(AppError):
    def __init__(self, message: str = "Not found"):
        super().__init__("NOT_FOUND", message, 404)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__("FORBIDDEN", message, 403)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__("UNAUTHORIZED", message, 401)


async def app_error_handler(_: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": {"code": exc.code, "message": exc.message}},
    )


async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {"code": "HTTP_ERROR", "message": str(exc.detail)},
        },
    )


async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
    from app.core.config import get_settings

    message = str(exc) if not get_settings().is_production else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": {"code": "INTERNAL_ERROR", "message": message}},
    )
