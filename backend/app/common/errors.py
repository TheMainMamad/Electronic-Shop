from typing import Any

import structlog
from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = structlog.get_logger()


class AppError(Exception):
    """Base class for domain errors that carry a stable machine-readable code."""

    code = "APP_ERROR"
    message = "خطایی در پردازش درخواست رخ داد."
    status_code = status.HTTP_400_BAD_REQUEST

    def __init__(self, message: str | None = None, details: Any = None) -> None:
        self.message = message or self.message
        self.details = details
        super().__init__(self.message)


class NotFoundError(AppError):
    code = "NOT_FOUND"
    message = "منبع موردنظر پیدا نشد."
    status_code = status.HTTP_404_NOT_FOUND


class PermissionDeniedError(AppError):
    code = "PERMISSION_DENIED"
    message = "شما اجازه دسترسی به این بخش را ندارید."
    status_code = status.HTTP_403_FORBIDDEN


class ConflictError(AppError):
    code = "CONFLICT"
    message = "درخواست با وضعیت فعلی سیستم در تناقض است."
    status_code = status.HTTP_409_CONFLICT


class UnauthorizedError(AppError):
    code = "UNAUTHORIZED"
    message = "برای ادامه لازم است وارد حساب کاربری خود شوید."
    status_code = status.HTTP_401_UNAUTHORIZED


class IdempotentReplay(Exception):  # noqa: N818
    """Raised to short-circuit a route and replay a previously completed
    response verbatim, without re-running any business logic."""

    def __init__(self, status_code: int, body: Any) -> None:
        self.status_code = status_code
        self.body = body


def _envelope(code: str, message: str, details: Any, request: Request) -> dict[str, Any]:
    request_id = request.headers.get("X-Request-Id") or getattr(
        request.state, "request_id", None
    )
    return {
        "error": {
            "code": code,
            "message": message,
            "details": details,
            "request_id": request_id,
        }
    }


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope(exc.code, exc.message, exc.details, request),
        )

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            content=_envelope(
                "VALIDATION_ERROR",
                "اطلاعات ارسال‌شده معتبر نیست.",
                jsonable_encoder(exc.errors()),
                request,
            ),
        )

    @app.exception_handler(IdempotentReplay)
    async def handle_idempotent_replay(request: Request, exc: IdempotentReplay) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content=exc.body)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_exception(
        request: Request, exc: StarletteHTTPException
    ) -> JSONResponse:
        return JSONResponse(
            status_code=exc.status_code,
            content=_envelope("HTTP_ERROR", str(exc.detail), None, request),
        )

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled_exception", error=str(exc))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_envelope(
                "INTERNAL_ERROR", "خطای داخلی سرور رخ داد. لطفاً دوباره تلاش کنید.", None, request
            ),
        )
