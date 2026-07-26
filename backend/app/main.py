from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.config import settings
from app.middleware.error_handler import register_error_handlers
from app.routers import auth, books, genres, oauth, ratings, recommendations, shelves, users

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
    # SessionMiddleware must come before CORSMiddleware — authlib OAuth needs it
    app.add_middleware(SessionMiddleware, secret_key=settings.session_secret_key)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

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
        return {"status": "ok", "environment": settings.environment}

    return app


app = create_app()
