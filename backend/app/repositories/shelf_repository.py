from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.shelf import Shelf, ShelfType
from app.models.shelf_book import ShelfBook
from app.repositories.base import BaseRepository


class ShelfRepository(BaseRepository[Shelf]):
    def __init__(self):
        super().__init__(Shelf)

    async def get_user_shelves(self, db: AsyncSession, user_id: int) -> list[Shelf]:
        result = await db.execute(
            select(Shelf)
            .where(Shelf.user_id == user_id)
            .order_by(Shelf.is_default.desc(), Shelf.created_at)
            .options(selectinload(Shelf.shelf_books).selectinload(ShelfBook.book))
        )
        return list(result.scalars().all())

    async def get_shelf_with_books(self, db: AsyncSession, shelf_id: int) -> Shelf | None:
        result = await db.execute(
            select(Shelf)
            .where(Shelf.id == shelf_id)
            .options(selectinload(Shelf.shelf_books).selectinload(ShelfBook.book))
        )
        return result.scalar_one_or_none()

    async def get_by_type(self, db: AsyncSession, user_id: int, shelf_type: ShelfType) -> Shelf | None:
        result = await db.execute(
            select(Shelf).where(
                Shelf.user_id == user_id,
                Shelf.shelf_type == shelf_type,
            )
        )
        return result.scalar_one_or_none()

    async def add_book(self, db: AsyncSession, shelf_id: int, book_id: int) -> ShelfBook:
        existing = await db.execute(
            select(ShelfBook).where(
                ShelfBook.shelf_id == shelf_id,
                ShelfBook.book_id == book_id,
            )
        )
        if existing.scalar_one_or_none():
            return existing.scalar_one_or_none()
        shelf_book = ShelfBook(shelf_id=shelf_id, book_id=book_id)
        db.add(shelf_book)
        await db.flush()
        return shelf_book

    async def remove_book(self, db: AsyncSession, shelf_id: int, book_id: int) -> None:
        await db.execute(
            delete(ShelfBook).where(
                ShelfBook.shelf_id == shelf_id,
                ShelfBook.book_id == book_id,
            )
        )
        await db.flush()

    async def is_book_on_shelf(self, db: AsyncSession, shelf_id: int, book_id: int) -> bool:
        result = await db.execute(
            select(ShelfBook).where(
                ShelfBook.shelf_id == shelf_id,
                ShelfBook.book_id == book_id,
            )
        )
        return result.scalar_one_or_none() is not None


shelf_repository = ShelfRepository()
