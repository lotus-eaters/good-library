from sqlalchemy import Boolean, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)  # null for OAuth users

    # OAuth fields — populated when user signs in via Google/GitHub
    oauth_provider: Mapped[str | None] = mapped_column(String(50))   # "google", "github"
    oauth_provider_id: Mapped[str | None] = mapped_column(String(255), index=True)  # provider's user ID

    display_name: Mapped[str | None] = mapped_column(String(100))
    avatar_url: Mapped[str | None] = mapped_column(String(500))
    bio: Mapped[str | None] = mapped_column(Text)
    reading_challenge_goal: Mapped[int] = mapped_column(Integer, default=0)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Relationships — SQLAlchemy will join these for you
    shelves: Mapped[list["Shelf"]] = relationship("Shelf", back_populates="user", cascade="all, delete-orphan")
    ratings: Mapped[list["Rating"]] = relationship("Rating", back_populates="user", cascade="all, delete-orphan")
    genre_affinities: Mapped[list["UserGenreAffinity"]] = relationship("UserGenreAffinity", back_populates="user", cascade="all, delete-orphan")
