from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.dependencies import get_current_user, get_db
from app.external.anthropic_client import generate_reading_insights
from app.models.book import Book
from app.models.rating import Rating
from app.models.shelf import Shelf, ShelfType
from app.models.shelf_book import ShelfBook
from app.models.user import User
from app.models.user_genre_affinity import UserGenreAffinity
from app.utils.cache import TTL_AI_SUMMARY, cache_delete, cache_get, cache_set

router = APIRouter(prefix="/users", tags=["users"])


class ChallengeOut(BaseModel):
    year: int
    goal: int
    books_read_this_year: int

    @property
    def percent(self) -> float:
        if self.goal == 0:
            return 0.0
        return min(round(self.books_read_this_year / self.goal * 100, 1), 100.0)


class ChallengeUpdate(BaseModel):
    goal: int = Field(ge=0, le=10000)


@router.get("/me/challenge", response_model=ChallengeOut)
async def get_challenge(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    year = datetime.now(timezone.utc).year
    jan_1 = datetime(year, 1, 1, tzinfo=timezone.utc)

    # Count distinct books added to already_read shelf this calendar year
    result = await db.execute(
        select(func.count(ShelfBook.book_id.distinct()))
        .join(Shelf, ShelfBook.shelf_id == Shelf.id)
        .where(
            Shelf.user_id == user.id,
            Shelf.shelf_type == ShelfType.ALREADY_READ,
            ShelfBook.added_at >= jan_1,
        )
    )
    books_read = result.scalar() or 0

    return ChallengeOut(year=year, goal=user.reading_challenge_goal, books_read_this_year=books_read)


@router.get("/me/insights")
async def get_insights(
    refresh: bool = Query(default=False),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    cache_key = f"reading_insights:{user.id}"

    if not refresh:
        cached = await cache_get(cache_key)
        if cached:
            return {"insight": cached}

    year = datetime.now(timezone.utc).year
    jan_1 = datetime(year, 1, 1, tzinfo=timezone.utc)

    # Books read this year
    read_result = await db.execute(
        select(func.count(ShelfBook.book_id.distinct()))
        .join(Shelf, ShelfBook.shelf_id == Shelf.id)
        .where(Shelf.user_id == user.id, Shelf.shelf_type == ShelfType.ALREADY_READ, ShelfBook.added_at >= jan_1)
    )
    books_read_this_year = read_result.scalar() or 0

    # Total books in library
    total_result = await db.execute(
        select(func.count(ShelfBook.book_id.distinct()))
        .join(Shelf, ShelfBook.shelf_id == Shelf.id)
        .where(Shelf.user_id == user.id)
    )
    total_books = total_result.scalar() or 0

    # Top 5 rated books
    ratings_result = await db.execute(
        select(Rating).where(Rating.user_id == user.id)
        .options(selectinload(Rating.book))
        .order_by(Rating.score.desc()).limit(5)
    )
    top_rated = [f"{r.book.title} ({r.score}★)" for r in ratings_result.scalars().all() if r.book]

    # Top 3 genres
    genres_result = await db.execute(
        select(UserGenreAffinity).where(UserGenreAffinity.user_id == user.id)
        .options(selectinload(UserGenreAffinity.genre))
        .order_by(UserGenreAffinity.score.desc()).limit(3)
    )
    top_genres = [a.genre.name for a in genres_result.scalars().all() if a.genre]

    # Currently reading
    curr_result = await db.execute(
        select(ShelfBook).join(Shelf, ShelfBook.shelf_id == Shelf.id)
        .where(Shelf.user_id == user.id, Shelf.shelf_type == ShelfType.CURRENTLY_READING)
        .options(selectinload(ShelfBook.book))
        .limit(1)
    )
    curr = curr_result.scalar_one_or_none()
    currently_reading = curr.book.title if curr and curr.book else None

    insight = await generate_reading_insights(
        books_read_this_year=books_read_this_year,
        total_books=total_books,
        top_rated=top_rated,
        top_genres=top_genres,
        currently_reading=currently_reading,
    )

    await cache_set(cache_key, insight, TTL_AI_SUMMARY)
    return {"insight": insight}


@router.put("/me/challenge", response_model=ChallengeOut)
async def update_challenge(
    body: ChallengeUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    user.reading_challenge_goal = body.goal
    await db.commit()
    await db.refresh(user)

    # Re-derive progress after goal update
    year = datetime.now(timezone.utc).year
    jan_1 = datetime(year, 1, 1, tzinfo=timezone.utc)
    result = await db.execute(
        select(func.count(ShelfBook.book_id.distinct()))
        .join(Shelf, ShelfBook.shelf_id == Shelf.id)
        .where(
            Shelf.user_id == user.id,
            Shelf.shelf_type == ShelfType.ALREADY_READ,
            ShelfBook.added_at >= jan_1,
        )
    )
    books_read = result.scalar() or 0

    return ChallengeOut(year=year, goal=user.reading_challenge_goal, books_read_this_year=books_read)


@router.get("/me/knowledge-graph")
async def get_knowledge_graph(
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    result = await db.execute(
        select(ShelfBook)
        .join(Shelf, ShelfBook.shelf_id == Shelf.id)
        .where(Shelf.user_id == user.id, Shelf.shelf_type == ShelfType.ALREADY_READ)
        .options(selectinload(ShelfBook.book).selectinload(Book.genres))
    )
    shelf_books = result.scalars().all()
    books = [sb.book for sb in shelf_books if sb.book]

    nodes: list[dict] = []
    edges: list[dict] = []
    seen_authors: set[str] = set()
    seen_genres: set[str] = set()

    for book in books:
        book_node_id = f"book-{book.id}"
        nodes.append({
            "id": book_node_id,
            "type": "book",
            "label": book.title,
            "cover_url": book.cover_url,
            "book_id": book.id,
        })

        for author in (book.authors or "").split(","):
            author = author.strip()
            if not author:
                continue
            author_node_id = f"author-{author}"
            if author not in seen_authors:
                nodes.append({"id": author_node_id, "type": "author", "label": author})
                seen_authors.add(author)
            edges.append({"source": author_node_id, "target": book_node_id, "type": "wrote"})

        for genre in book.genres:
            genre_node_id = f"genre-{genre.id}"
            if genre.slug not in seen_genres:
                nodes.append({"id": genre_node_id, "type": "genre", "label": genre.name})
                seen_genres.add(genre.slug)
            edges.append({"source": book_node_id, "target": genre_node_id, "type": "belongs-to"})

    return {"nodes": nodes, "edges": edges}
