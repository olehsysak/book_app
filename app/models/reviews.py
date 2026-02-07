from sqlalchemy import Integer, String, Text, DateTime, Float, ForeignKey, func, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.users import User


class Review(Base):
    """
    Represents a review saved by the user
    """
    __tablename__ = 'reviews'

    # Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_olid: Mapped[str] = mapped_column(String, nullable=False)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), onupdate=func.now())
    rating: Mapped[float] = mapped_column(Float, nullable=False)

    # Foreign key
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="reviews")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "work_olid", name="uq_user_work_review"),
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_review_rating"),
    )
