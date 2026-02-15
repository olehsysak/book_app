from fastapi import APIRouter, Request, Query, HTTPException, status, Depends
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends import get_async_db
from app.models.favorites import Favorite as FavoriteModel
from app.models.users import User as UserModel
from app.models.books import Book as BookModel

from app.schemas.favorites import Favorite as FavoriteSchema, FavoriteList
from app.auth import get_current_user


router = APIRouter(
    prefix="/favorites",
    tags=["favorites"],
)


@router.get("/", response_model=FavoriteList, summary="Get paginated list of favorite books")
async def get_favorites(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> FavoriteList:
    """
    Returns a paginated list of the current user's favorite books.

    - Fetches book details from local DB or Open Library if missing
    """
    total = await db.scalar(
        select(func.count())
        .select_from(FavoriteModel)
        .where(FavoriteModel.user_id == current_user.id)
    )
    offset = (page - 1) * page_size

    # Retrieve the current user's favorite records from the database
    result = await db.execute(
        select(FavoriteModel)
        .where(FavoriteModel.user_id == current_user.id)
        .limit(page_size)
        .offset(offset)
    )
    favorites = result.scalars().all()

    items = []
    service = request.app.state.open_library_service

    # Check if the book exists in the local books table
    for fav in favorites:
        book = await db.scalar(
            select(BookModel).where(BookModel.work_olid == fav.work_olid)
        )

    # If not, fetch the book data from Open Library
        if not book:
            book_data = await service.get_book_by_work(fav.work_olid)
            if book_data:
                book = BookModel(
                    work_olid=fav.work_olid,
                    title=book_data.get("title"),
                    authors=", ".join(book_data.get("authors") or []),
                    cover_url=book_data.get("cover_url"),
                    published_year=book_data.get("year"),
                )
                db.add(book)
                await db.commit()
                await db.refresh(book)

        items.append(
            FavoriteSchema(
                id=fav.id,
                work_olid=fav.work_olid,
                title=book.title if book else None,
                authors=book.authors.split(", ") if book and book.authors else None,
                year=book.published_year if book else None,
                cover_url=book.cover_url if book else None,
                created_at=fav.created_at,
            )
        )

    return FavoriteList(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("/{work_olid}", response_model=FavoriteSchema, status_code=status.HTTP_201_CREATED, summary="Add a book to favorites")
async def add_to_favorite(
    work_olid: str,
    request: Request,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> FavoriteSchema:
    """
    Adds a book to the current user's favorites list by its OLID.

    - Checks if already in favorites
    - Fetches book details from local DB or Open Library if missing
    """
    service = request.app.state.open_library_service

    # Check if the book is already in favorites
    exists = await db.scalar(
        select(FavoriteModel).where(
            FavoriteModel.work_olid == work_olid,
            FavoriteModel.user_id == current_user.id
        )
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This book is already in favorites",
        )

    # Check if the book exists in `books`, if not fetch from Open Library
    book = await db.scalar(select(BookModel).where(BookModel.work_olid == work_olid))
    if not book:
        book_data = await service.get_book_by_work(work_olid)
        if not book_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Book not found in Open Library",
            )

        # Save book to books
        book = BookModel(
            work_olid=work_olid,
            title=book_data.get("title"),
            authors=", ".join(book_data.get("authors") or []),
            cover_url=book_data.get("cover_url"),
            published_year=book_data.get("year"),
        )

        db.add(book)
        await db.commit()
        await db.refresh(book)

    # Add to favorites
    favorite = FavoriteModel(
        work_olid=work_olid,
        user_id=current_user.id,
    )
    
    db.add(favorite)
    await db.commit()
    await db.refresh(favorite)

    authors_list = book.authors.split(", ") if book.authors else None

    return FavoriteSchema(
        id=favorite.id,
        work_olid=book.work_olid,
        title=book.title,
        authors=authors_list,
        year=book.published_year,
        cover_url=book.cover_url,
        created_at=favorite.created_at,
    )


@router.delete("/{work_olid}", status_code=status.HTTP_204_NO_CONTENT, summary="Remove a book from favorites")
async def remove_from_favorite(
    olid_id: str,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
) -> None:
    """
    Removes a book from the current user's favorites list by its OLID.
    """
    # Check if the book exists in the current user's favorites
    favorite = await db.scalar(
        select(FavoriteModel)
        .where(FavoriteModel.work_olid == olid_id,
               FavoriteModel.user_id == current_user.id)
    )

    if not favorite:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This book is not in favorites",
        )

    # Remove the book from favorites only for the current user
    await db.execute(
        delete(FavoriteModel)
        .where(
            FavoriteModel.work_olid == olid_id,
            FavoriteModel.user_id == current_user.id
        )
    )

    await db.commit()

    return None