from sqlalchemy import Integer, String, DateTime, func, UniqueConstraint, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from datetime import datetime
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.users import User
    from app.models.books import Book


class Favorite(Base):
    """
    Represents a user's favorite book
    """
    __tablename__ = 'favorites'

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_olid: Mapped[str] = mapped_column(String(50), ForeignKey("books.work_olid"), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # Foreign key
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="favorites")
    book: Mapped["Book"] = relationship(
        "Book",
        back_populates="favorites",
        uselist=False,
        lazy="joined"
    )

    __table_args__ = (
        UniqueConstraint("work_olid", "user_id", name="uq_favorite_work_user"),
    )