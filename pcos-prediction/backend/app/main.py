"""FastAPI application entrypoint."""

from __future__ import annotations

import logging
from urllib.parse import urlparse

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from app.api.routes import admin, auth, patients, predict, reports
from app.core.config import settings
from app.core.dependencies import APIError, error_payload
from app.core.middleware import RateLimitMiddleware, RequestContextMiddleware
from app.db.database import engine
from app.models import Base


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)


def resolve_allowed_origins() -> list[str]:
    """Return local frontend origins allowed during development."""

    origins = {settings.frontend_url, "http://localhost:3000", "http://127.0.0.1:3000"}
    parsed = urlparse(settings.frontend_url)
    if parsed.scheme and parsed.port:
        if parsed.hostname == "localhost":
            origins.add(f"{parsed.scheme}://127.0.0.1:{parsed.port}")
        if parsed.hostname == "127.0.0.1":
            origins.add(f"{parsed.scheme}://localhost:{parsed.port}")
    return sorted(origins)


def initialize_local_sqlite() -> None:
    """Create the local SQLite schema automatically for development runs."""

    if not settings.database_url.startswith("sqlite"):
        return
    Base.metadata.create_all(bind=engine)


def create_application() -> FastAPI:
    """Build and configure the FastAPI app."""

    application = FastAPI(
        title=settings.project_name,
        openapi_url=f"{settings.api_v1_prefix}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=resolve_allowed_origins(),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestContextMiddleware)
    application.add_middleware(RateLimitMiddleware)

    initialize_local_sqlite()
    settings.resolved_report_storage_path.mkdir(parents=True, exist_ok=True)
    settings.resolved_model_storage_path.mkdir(parents=True, exist_ok=True)
    application.mount(
        "/report-files",
        StaticFiles(directory=settings.resolved_report_storage_path),
        name="report-files",
    )

    application.include_router(auth.router, prefix=f"{settings.api_v1_prefix}/auth", tags=["auth"])
    application.include_router(predict.router, prefix=settings.api_v1_prefix, tags=["predict"])
    application.include_router(patients.router, prefix=f"{settings.api_v1_prefix}/patients", tags=["patients"])
    application.include_router(reports.router, prefix=f"{settings.api_v1_prefix}/reports", tags=["reports"])
    application.include_router(admin.router, prefix=f"{settings.api_v1_prefix}/admin", tags=["admin"])

    @application.get("/health", tags=["health"])
    def health_check() -> dict[str, str]:
        """Return a simple health status."""

        return {"status": "ok"}

    @application.exception_handler(APIError)
    async def api_error_handler(_: Request, exc: APIError) -> JSONResponse:
        """Render structured application errors."""

        return JSONResponse(status_code=exc.status_code, content=error_payload(exc.message, exc.code))

    @application.exception_handler(HTTPException)
    async def http_error_handler(_: Request, exc: HTTPException) -> JSONResponse:
        """Normalize FastAPI HTTP exceptions."""

        detail = exc.detail if isinstance(exc.detail, dict) else error_payload(str(exc.detail), "HTTP_ERROR")
        return JSONResponse(status_code=exc.status_code, content=detail)

    @application.exception_handler(RequestValidationError)
    async def validation_error_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
        """Normalize request validation errors."""

        message = "; ".join(
            f"{'.'.join(map(str, error['loc']))}: {error['msg']}"
            for error in exc.errors()
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=error_payload(message, "VALIDATION_ERROR"),
        )

    @application.exception_handler(Exception)
    async def unhandled_error_handler(_: Request, exc: Exception) -> JSONResponse:
        """Hide internal exception details behind a standard response."""

        logging.getLogger(__name__).exception("Unhandled API exception: %s", exc)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=error_payload("An unexpected server error occurred.", "INTERNAL_SERVER_ERROR"),
        )

    return application


app = create_application()
