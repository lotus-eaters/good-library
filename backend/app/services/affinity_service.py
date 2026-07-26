from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.book_repository import book_repository
from app.repositories.user_genre_affinity_repository import user_genre_affinity_repository


class AffinityService:
    """
    Tracks how much a user likes each genre based on their ratings and shelving behavior.
    Higher score = stronger preference = shows up first in recommendations.
    """

    # Score deltas by star rating
    RATING_DELTAS = {1: -1.0, 2: -0.5, 3: 0.25, 4: 1.0, 5: 1.5}

    async def boost_from_book(
        self, db: AsyncSession, *, user_id: int, book_id: int, delta: float
    ) -> None:
        """Add `delta` to every genre the book belongs to."""
        book = await book_repository.get_with_genres(db, book_id)
        if not book or not book.genres:
            return
        for genre in book.genres:
            await user_genre_affinity_repository.increment(db, user_id, genre.id, delta)

    async def update_from_rating(
        self,
        db: AsyncSession,
        *,
        user_id: int,
        book_id: int,
        new_score: int,
        old_score: int | None = None,
    ) -> None:
        """
        Adjust genre affinity when a user rates a book.
        If they're changing an existing rating, we subtract the old delta first.
        """
        book = await book_repository.get_with_genres(db, book_id)
        if not book or not book.genres:
            return

        new_delta = self.RATING_DELTAS.get(new_score, 0.0)
        old_delta = self.RATING_DELTAS.get(old_score, 0.0) if old_score else 0.0
        net_delta = new_delta - old_delta  # only the change in sentiment

        if net_delta == 0:
            return

        for genre in book.genres:
            await user_genre_affinity_repository.increment(db, user_id, genre.id, net_delta)


affinity_service = AffinityService()
