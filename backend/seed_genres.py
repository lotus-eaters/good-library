"""Run once: python seed_genres.py"""
import asyncio

from app.database import AsyncSessionFactory
from app.models.genre import Genre

# Must import all models so SQLAlchemy can resolve cross-model relationships
import app.models.user               # noqa: F401
import app.models.book               # noqa: F401
import app.models.book_genre         # noqa: F401
import app.models.shelf              # noqa: F401
import app.models.shelf_book         # noqa: F401
import app.models.rating             # noqa: F401
import app.models.user_genre_affinity  # noqa: F401


GENRES = [
    ("Fiction", "fiction", "Literary and commercial fiction", "📖"),
    ("Science Fiction", "science-fiction", "Speculative futures and technology", "🚀"),
    ("Fantasy", "fantasy", "Magic, myth, and other worlds", "🧙"),
    ("Mystery", "mystery", "Crime, thrillers, and whodunits", "🔍"),
    ("Romance", "romance", "Love stories and relationships", "💕"),
    ("Horror", "horror", "Fear, suspense, and the supernatural", "👻"),
    ("Historical Fiction", "historical-fiction", "Stories set in the past", "🏰"),
    ("Biography", "biography", "Real lives and memoirs", "👤"),
    ("Self Help", "self-help", "Personal growth and improvement", "🌱"),
    ("Science", "science", "Popular science and discovery", "🔬"),
    ("Philosophy", "philosophy", "Ideas, ethics, and existence", "🤔"),
    ("Poetry", "poetry", "Verse and lyrical expression", "✍️"),
    ("Graphic Novel", "graphic-novel", "Comics and visual storytelling", "🎨"),
    ("Young Adult", "young-adult", "Stories for teen readers", "⭐"),
    ("Children", "children", "Books for young readers", "🌈"),
    ("Business", "business", "Entrepreneurship and management", "💼"),
    ("History", "history", "The story of our world", "🌍"),
    ("Travel", "travel", "Adventures and destinations", "✈️"),
    ("Cooking", "cooking", "Recipes and food culture", "🍳"),
    ("Art", "art", "Visual arts and design", "🎭"),
]


async def seed():
    from sqlalchemy import select
    async with AsyncSessionFactory() as db:
        for name, slug, description, icon in GENRES:
            result = await db.execute(select(Genre).where(Genre.slug == slug))
            if not result.scalar_one_or_none():
                db.add(Genre(name=name, slug=slug, description=description, icon=icon))
        await db.commit()
        print(f"Seeded {len(GENRES)} genres.")


if __name__ == "__main__":
    asyncio.run(seed())
