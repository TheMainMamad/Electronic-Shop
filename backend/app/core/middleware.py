import time
import uuid
from collections.abc import Awaitable, Callable

import structlog
from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.security.csrf import CSRF_COOKIE_NAME, CSRF_HEADER_NAME, csrf_tokens_match

logger = structlog.get_logger()

_MUTATING_METHODS = {"POST", "PUT", "PATCH", "DELETE"}


async def request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request_id = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    request.state.request_id = request_id
    structlog.contextvars.clear_contextvars()
    structlog.contextvars.bind_contextvars(request_id=request_id)

    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)

    response.headers["X-Request-Id"] = request_id
    logger.info(
        "request_completed",
        method=request.method,
        route=request.url.path,
        status_code=response.status_code,
        duration_ms=duration_ms,
    )
    return response


async def csrf_protection_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Double-submit CSRF check for mutating requests on an existing session.

    A request with no csrf_token cookie yet (login/register) is not a forged
    request against an authenticated session, so it is exempt by construction.
    """
    if request.method in _MUTATING_METHODS:
        cookie_token = request.cookies.get(CSRF_COOKIE_NAME)
        header_token = request.headers.get(CSRF_HEADER_NAME)
        if cookie_token and not csrf_tokens_match(cookie_token, header_token):
            return JSONResponse(
                status_code=403,
                content={
                    "error": {
                        "code": "CSRF_VALIDATION_FAILED",
                        "message": "اعتبارسنجی درخواست ناموفق بود. صفحه را دوباره بارگذاری کنید.",
                        "details": None,
                        "request_id": getattr(request.state, "request_id", None),
                    }
                },
            )
    return await call_next(request)
