import enum

from sqlalchemy import Boolean, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.base import TimestampMixin


class ShelfType(str, enum.Enum):
    CURRENTLY_READING = "currently_reading"
    WANT_TO_READ = "want_to_read"
    ALREADY_READ = "already_read"
    CUSTOM = "custom"


class Shelf(TimestampMixin, Base):
    __tablename__ = "shelves"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    shelf_type: Mapped[ShelfType] = mapped_column(Enum(ShelfType), nullable=False)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    user: Mapped["User"] = relationship("User", back_populates="shelves")
    shelf_books: Mapped[list["ShelfBook"]] = relationship("ShelfBook", back_populates="shelf", cascade="all, delete-orphan")
