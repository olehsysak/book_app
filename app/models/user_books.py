from sqlalchemy import Integer, String, DateTime, Enum, ForeignKey, func, UniqueConstraint, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime

from app.database import Base
import enum
from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models import User


class ReadingStatus(str, enum.Enum):
    PLANNED = "planned"
    READING = "reading"
    COMPLETED = "completed"
    DROPPED = "dropped"


class UserBook(Base):
    """
    Represents a user's book entry in their personal reading list
    """
    __tablename__ = "user_books"

    # Fields
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    work_olid: Mapped[str] = mapped_column(String, nullable=False, index=True)
    status: Mapped[ReadingStatus] = mapped_column(Enum(ReadingStatus, name="reading_status_enum", native_enum=False), default=ReadingStatus.PLANNED, nullable=False)
    progress_percent: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # Foreign key
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # Relationship
    user: Mapped["User"] = relationship("User", back_populates="user_books")

    # Constraints
    __table_args__ = (
        UniqueConstraint("user_id", "work_olid", name="uq_user_work"),
        CheckConstraint(
            "progress_percent >= 0 AND progress_percent <= 100",
            name="check_progress_range",
        ),
        CheckConstraint(
            "rating IS NULL OR (rating >= 1 AND rating <= 5)",
            name="check_rating_range",
        ),
    )
