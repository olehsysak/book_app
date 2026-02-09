from sqlalchemy import Integer, String, DateTime, ForeignKey, func, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.bookshelves import BookShelf


class BookInShelf(Base):
    """
    Books added to users' bookshelves
    """
    __tablename__ = "books_in_shelf"

    # Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_olid: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    added_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Foreign key
    bookshelf_id: Mapped[int] = mapped_column(Integer, ForeignKey("bookshelf.id", ondelete="CASCADE"), nullable=False)

    # Relationship
    bookshelf: Mapped["BookShelf"] = relationship("BookShelf", back_populates="books")

    # Constraints
    __table_args__ = (
        UniqueConstraint("bookshelf_id", "work_olid", name="uq_bookshelf_openlibrary_book"),
    )
