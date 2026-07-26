from sqlalchemy import Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class UserGenreAffinity(TimestampMixin, Base):
    __tablename__ = "user_genre_affinities"
    __table_args__ = (
        UniqueConstraint("user_id", "genre_id", name="uq_user_genre_affinity"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    genre_id: Mapped[int] = mapped_column(ForeignKey("genres.id", ondelete="CASCADE"), nullable=False)
    score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)  # higher = stronger preference

    user: Mapped["User"] = relationship("User", back_populates="genre_affinities")
    genre: Mapped["Genre"] = relationship("Genre", back_populates="user_affinities")
