from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.middleware.error_handler import register_error_handlers
from app.middleware.request_logger import RequestLoggerMiddleware
from app.routers import auth, books, genres, oauth, ratings, recommendations, shelves, users
from app.utils.logging import logger, setup_logging

setup_logging()

API_PREFIX = "/api/v1"


def create_app() -> FastAPI:
    app = FastAPI(
        title="good_library API",
        description="A Goodreads clone — track, discover, and rate your books.",
        version="1.0.0",
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
    )

    # ── Middleware ──────────────────────────────────────────────────────────────
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggerMiddleware)

    # ── Prometheus metrics — exposes GET /metrics ───────────────────────────────
    Instrumentator(
        should_group_status_codes=False,
        excluded_handlers=["/health", "/metrics"],
    ).instrument(app).expose(app, tags=["system"])

    # ── Error handlers ─────────────────────────────────────────────────────────
    register_error_handlers(app)

    # ── Routers ────────────────────────────────────────────────────────────────
    app.include_router(auth.router, prefix=API_PREFIX)
    app.include_router(books.router, prefix=API_PREFIX)
    app.include_router(shelves.router, prefix=API_PREFIX)
    app.include_router(ratings.router, prefix=API_PREFIX)
    app.include_router(genres.router, prefix=API_PREFIX)
    app.include_router(recommendations.router, prefix=API_PREFIX)
    app.include_router(oauth.router, prefix=API_PREFIX)
    app.include_router(users.router, prefix=API_PREFIX)

    # ── Health check ───────────────────────────────────────────────────────────
    @app.get("/health", tags=["system"])
    async def health_check():
        from sqlalchemy import text
        from app.database import AsyncSessionFactory
        from app.utils.cache import cache_get

        checks: dict[str, str] = {}

        try:
            async with AsyncSessionFactory() as db:
                await db.execute(text("SELECT 1"))
            checks["db"] = "ok"
        except Exception as e:
            checks["db"] = f"error: {e}"
            logger.error("Health check DB failed", extra={"error": str(e)})

        try:
            await cache_get("__health__")
            checks["redis"] = "ok"
        except Exception as e:
            checks["redis"] = f"error: {e}"
            logger.error("Health check Redis failed", extra={"error": str(e)})

        status = "ok" if all(v == "ok" for v in checks.values()) else "degraded"
        logger.info(f"Health check: {status}", extra={"checks": checks})
        return {"status": status, "environment": settings.environment, "checks": checks}

    logger.info("good_library API started", extra={"environment": settings.environment})
    return app


app = create_app()
