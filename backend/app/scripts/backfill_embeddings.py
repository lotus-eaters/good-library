"""
One-time script: embed all books that don't have an embedding yet.

Run from the backend directory:
    python -m app.scripts.backfill_embeddings
"""
import asyncio

from sqlalchemy import select

from app.database import AsyncSessionFactory
from app.external.embedding_client import embed_batch
import app.models  # noqa: F401 — registers all models so relationships resolve
from app.models.book import Book

BATCH_SIZE = 100  # OpenAI allows up to 2048 per call; 100 is safe


def _book_text(book: Book) -> str:
    parts = [book.title, book.authors]
    if book.description:
        parts.append(book.description[:400])
    return " ".join(parts)


async def run() -> None:
    async with AsyncSessionFactory() as db:
        result = await db.execute(
            select(Book).where(Book.embedding.is_(None))
        )
        books = result.scalars().all()

        if not books:
            print("All books already have embeddings.")
            return

        print(f"Embedding {len(books)} books in batches of {BATCH_SIZE}...")

        for i in range(0, len(books), BATCH_SIZE):
            batch = books[i : i + BATCH_SIZE]
            texts = [_book_text(b) for b in batch]
            vectors = await embed_batch(texts)
            for book, vector in zip(batch, vectors):
                book.embedding = vector
            await db.commit()
            print(f"  {min(i + BATCH_SIZE, len(books))}/{len(books)} done")

        print("Backfill complete.")


if __name__ == "__main__":
    asyncio.run(run())
