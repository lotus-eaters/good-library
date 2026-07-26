from sqlalchemy import Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Genre(Base):
    __tablename__ = "genres"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    icon: Mapped[str | None] = mapped_column(String(50))  # emoji or icon name

    books: Mapped[list["Book"]] = relationship("Book", secondary="book_genres", back_populates="genres")
    user_affinities: Mapped[list["UserGenreAffinity"]] = relationship("UserGenreAffinity", back_populates="genre")
