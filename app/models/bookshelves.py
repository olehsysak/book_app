from sqlalchemy import Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.users import User
    from app.models.books_in_shelf import BookInShelf

class BookShelf(Base):
    """
    Represents a user's custom book list.
    """
    __tablename__ = "bookshelf"

    # Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Foreign key
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="bookshelves")
    books: Mapped[list["BookInShelf"]] = relationship("BookInShelf", back_populates="bookshelf", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_user_bookshelf_name"),
    )