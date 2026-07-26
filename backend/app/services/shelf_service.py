from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.shelf import Shelf, ShelfType
from app.models.shelf_book import ShelfBook
from app.repositories.shelf_repository import shelf_repository
from app.utils.cache import cache_delete

# Factory Pattern — the 3 shelves every user gets on signup
DEFAULT_SHELVES: list[tuple[str, ShelfType]] = [
    ("Currently Reading", ShelfType.CURRENTLY_READING),
    ("Want to Read", ShelfType.WANT_TO_READ),
    ("Already Read", ShelfType.ALREADY_READ),
]


class ShelfService:
    async def create_default_shelves(self, db: AsyncSession, user_id: int) -> list[Shelf]:
        shelves = []
        for name, shelf_type in DEFAULT_SHELVES:
            shelf = Shelf(
                user_id=user_id,
                name=name,
                shelf_type=shelf_type,
                is_default=True,
            )
            shelf = await shelf_repository.create(db, shelf)
            shelves.append(shelf)
        return shelves

    async def get_user_shelves(self, db: AsyncSession, user_id: int) -> list[Shelf]:
        return await shelf_repository.get_user_shelves(db, user_id)

    async def get_shelf_with_books(self, db: AsyncSession, shelf_id: int, user_id: int) -> Shelf:
        shelf = await shelf_repository.get_shelf_with_books(db, shelf_id)
        if not shelf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelf not found")
        if shelf.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not your shelf")
        return shelf

    async def add_to_shelf(self, db: AsyncSession, *, user_id: int, shelf_id: int, book_id: int) -> ShelfBook:
        shelf = await shelf_repository.get_by_id(db, shelf_id)
        if not shelf or shelf.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelf not found")

        # Business rule: a book can only be on ONE default shelf at a time.
        # If the target is a default shelf, remove the book from other default shelves first.
        if shelf.shelf_type != ShelfType.CUSTOM:
            await self._remove_from_default_shelves(db, user_id=user_id, book_id=book_id, except_shelf_id=shelf_id)

        shelf_book = await shelf_repository.add_book(db, shelf_id, book_id)
        await db.commit()

        # Update genre affinity when adding to "Already Read" or "Currently Reading"
        if shelf.shelf_type in (ShelfType.ALREADY_READ, ShelfType.CURRENTLY_READING):
            from app.services.affinity_service import affinity_service
            await affinity_service.boost_from_book(db, user_id=user_id, book_id=book_id, delta=0.5)
            await db.commit()

        # Invalidate cached insights — reading history changed
        await cache_delete(f"reading_insights:{user_id}")

        return shelf_book

    async def remove_from_shelf(self, db: AsyncSession, *, user_id: int, shelf_id: int, book_id: int) -> None:
        shelf = await shelf_repository.get_by_id(db, shelf_id)
        if not shelf or shelf.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Shelf not found")

        await shelf_repository.remove_book(db, shelf_id, book_id)
        await db.commit()

    async def create_custom_shelf(self, db: AsyncSession, *, user_id: int, name: str) -> Shelf:
        shelf = Shelf(
            user_id=user_id,
            name=name.strip(),
            shelf_type=ShelfType.CUSTOM,
            is_default=False,
        )
        shelf = await shelf_repository.create(db, shelf)
        await db.commit()
        await db.refresh(shelf)
        return shelf

    async def _remove_from_default_shelves(
        self, db: AsyncSession, *, user_id: int, book_id: int, except_shelf_id: int
    ) -> None:
        """Remove a book from all default shelves except the target one."""
        user_shelves = await shelf_repository.get_user_shelves(db, user_id)
        for shelf in user_shelves:
            if shelf.id != except_shelf_id and shelf.shelf_type != ShelfType.CUSTOM:
                await shelf_repository.remove_book(db, shelf.id, book_id)


shelf_service = ShelfService()
