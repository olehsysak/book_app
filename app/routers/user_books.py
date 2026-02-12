from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends import get_async_db
from app.models.user_books import UserBook as UserBookModel
from app.models.users import User as UserModel
from app.models.books import Book as BookModel

from app.schemas.user_books import UserBook as UserBookSchema, UserBookAdd, ReadingStatus
from app.auth import get_current_user


router = APIRouter(
    prefix="/user-books",
    tags=["user-books"],
)


@router.post("/", response_model=UserBookSchema, status_code=status.HTTP_201_CREATED)
async def add_user_books(
        book_data: UserBookAdd,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user),
):
    """
    Add a book to the user's personal reading list
    """

    # Check if the book is already in user's list
    existing = await db.scalar(
        select(UserBookModel).where(
            UserBookModel.user_id == current_user.id,
            UserBookModel.work_olid == book_data.work_olid
        )
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already in your list"
        )

    # Add new book entry
    user_book = UserBookModel(
        user_id=current_user.id,
        work_olid=book_data.work_olid,
        status=book_data.status,
        progress_percent=book_data.progress_percent,
        rating=book_data.rating
    )
    db.add(user_book)
    await db.commit()
    await db.refresh(user_book)

    # Try to get book info from local books table
    book = await db.scalar(
        select(BookModel)
        .where(BookModel.work_olid == book_data.work_olid
        )
    )

    return UserBookSchema(
        id=user_book.id,
        work_olid=user_book.work_olid,
        status=user_book.status.value,
        progress_percent=user_book.progress_percent,
        rating=user_book.rating,
        started_at=user_book.started_at,
        finished_at=user_book.finished_at,
        created_at=user_book.created_at,
        updated_at=user_book.updated_at,
        title=book.title if book else None,
        authors=book.authors.split(", ") if book and book.authors else [],
        cover_url=book.cover_url if book else None,
        published_year=book.published_year if book else None
    )


@router.get("/", response_model=list[UserBookSchema])
async def get_user_books(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: ReadingStatus | None = Query(None, description="Filter by reading status"),
    db: AsyncSession = Depends(get_async_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Get the user's personal reading list with optional status filter and pagination.
    """
    offset = (page - 1) * page_size

    query = select(UserBookModel).where(UserBookModel.user_id == current_user.id)
    if status_filter:
        query = query.where(UserBookModel.status == status_filter)
    query = query.limit(page_size).offset(offset)

    result = await db.execute(query)
    user_books = result.scalars().all()

    # Load book info from local books table
    books_full = []
    for ub in user_books:
        book = await db.scalar(select(BookModel).where(BookModel.work_olid == ub.work_olid))
        books_full.append(
            UserBookSchema(
                id=ub.id,
                work_olid=ub.work_olid,
                status=ub.status.value,
                progress_percent=ub.progress_percent,
                rating=ub.rating,
                started_at=ub.started_at,
                finished_at=ub.finished_at,
                created_at=ub.created_at,
                updated_at=ub.updated_at,
                title=book.title if book else None,
                authors=book.authors.split(", ") if book and book.authors else [],
                cover_url=book.cover_url if book else None,
                published_year=book.published_year if book else None
            )
        )

    return books_full