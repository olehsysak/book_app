from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

from typing import TYPE_CHECKING


if TYPE_CHECKING:
    from app.models.favorites import Favorite


class Book(Base):
    """
    Book table represents books fetched from OpenLibrary
    and stored in the local database.
    """
    __tablename__ = "books"

    # Fields
    id: Mapped[int] = mapped_column(primary_key=True)
    work_olid: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    authors: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cover_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    published_year: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Relationships
    favorites: Mapped[list["Favorite"]] = relationship(
        "Favorite",
        back_populates="book",
        cascade="all, delete-orphan"
    )