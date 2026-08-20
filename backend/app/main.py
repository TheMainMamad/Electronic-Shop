from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.common.errors import register_exception_handlers
from app.core.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import csrf_protection_middleware, request_context_middleware

settings = get_settings()
configure_logging(settings.debug)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="فروشگاه الکترونیک - API",
        version="0.1.0",
        docs_url="/docs" if settings.openapi_enabled else None,
        redoc_url="/redoc" if settings.openapi_enabled else None,
        openapi_url="/openapi.json" if settings.openapi_enabled else None,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_allow_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Authorization", "Content-Type", "X-CSRF-Token", "Idempotency-Key"],
    )
    app.middleware("http")(csrf_protection_middleware)
    app.middleware("http")(request_context_middleware)

    register_exception_handlers(app)
    app.include_router(api_router)

    return app


app = create_app()
