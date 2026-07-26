from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db, get_optional_user
from app.models.user import User
from app.schemas.book import BookDetailOut, BookOut, ImportBookRequest
from app.services.book_service import book_service

router = APIRouter(prefix="/books", tags=["books"])


@router.get("/new-releases", response_model=list[BookOut])
async def new_releases(
    genre: str = Query(default="fiction", description="Genre to fetch new releases for"),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.get_new_releases(db, genre, limit=limit)


@router.get("/popular", response_model=list[BookOut])
async def popular_books(
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.get_popular(db, limit=limit)


@router.get("/search", response_model=list[BookOut])
async def search_books(
    q: str = Query(min_length=1, description="Search query"),
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.search(db, q, limit=limit)


@router.get("/search/semantic", response_model=list[BookOut])
async def semantic_search(
    q: str = Query(min_length=1, description="Natural language search query"),
    limit: int = Query(default=10, ge=1, le=30),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.semantic_search(db, q, limit=limit)


@router.get("/genre/{slug}", response_model=list[BookOut])
async def books_by_genre(
    slug: str,
    limit: int = Query(default=20, ge=1, le=50),
    db: AsyncSession = Depends(get_db),
):
    return await book_service.get_by_genre(db, slug, limit=limit)


@router.get("/{book_id}/summary")
async def get_book_summary(
    book_id: int,
    db: AsyncSession = Depends(get_db),
):
    summary = await book_service.get_summary(db, book_id)
    return {"summary": summary}


@router.get("/{book_id}", response_model=BookDetailOut)
async def get_book(
    book_id: int,
    db: AsyncSession = Depends(get_db),
    user: User | None = Depends(get_optional_user),
):
    return await book_service.get_by_id(db, book_id)


@router.post("/import", response_model=BookDetailOut, status_code=201)
async def import_book(
    body: ImportBookRequest,
    db: AsyncSession = Depends(get_db),
):
    return await book_service.import_from_google(db, body.google_books_id)
