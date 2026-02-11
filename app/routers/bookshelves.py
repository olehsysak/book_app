from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.depends import get_async_db
from app.models.bookshelves import BookShelf as BookShelfModel
from app.models.books_in_shelf import BookInShelf as BookInShelfModel
from app.models.users import User as UserModel
from app.models.books import Book as BookModel

from app.schemas.bookshelves import BookShelf as BookShelfSchema, BookShelfCreate, BookShelfList, BookShelfUpdate
from app.schemas.books_in_shelf import BookInShelf as BookInShelfSchema, BookAdd
from app.auth import get_current_user


router = APIRouter(
    prefix="/bookshelves",
    tags=["bookshelves"],
)


@router.post("/", response_model=BookShelfSchema, status_code=status.HTTP_201_CREATED)
async def create_bookshelf(
        bookshelf_data: BookShelfCreate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Create a new bookshelf for the current user
    """

    # Check if a list with the same name already exists for the user
    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.user_id == current_user.id,
            BookShelfModel.name == bookshelf_data.name,
        )
    )
    existing_bookshelf = result.scalars().first()


    if existing_bookshelf:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You already have a bookshelf with this name."
        )

    new_bookshelf = BookShelfModel(
        name=bookshelf_data.name,
        description=bookshelf_data.description,
        user_id=current_user.id,
    )

    db.add(new_bookshelf)
    await db.commit()
    await db.refresh(new_bookshelf)

    return BookShelfSchema(
        id=new_bookshelf.id,
        name=new_bookshelf.name,
        description=new_bookshelf.description,
        created_at=new_bookshelf.created_at,
        books=[]
    )


@router.get("/", response_model=list[BookShelfSchema])
async def get_bookshelves(
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Get all bookshelves of the current user
    """

    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.user_id == current_user.id,
        )
    )

    bookshelves = result.scalars().all()

    return [
        BookShelfSchema(
            id=b.id,
            name=b.name,
            description=b.description,
            created_at=b.created_at,
            books=[]
        )
        for b in bookshelves
    ]


@router.post("/{bookshelf_id}/books", response_model=BookInShelfSchema, status_code=status.HTTP_201_CREATED)
async def add_book_in_shelf(
        bookshelf_id: int,
        book_data: BookAdd,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Add a book to a user's bookshelf
    """

    # Check that bookshelf exists and belongs to current user
    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.id == bookshelf_id,
            BookShelfModel.user_id == current_user.id,
        )
    )
    bookshelf = result.scalars().first()

    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found"
        )

    # Check if the book is already in the bookshelf
    result = await db.execute(
        select(BookInShelfModel).where(
            BookInShelfModel.bookshelf_id == bookshelf.id,
            BookInShelfModel.work_olid == book_data.work_olid,
        )
    )
    existing_book = result.scalars().first()

    if existing_book:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This book is already in the bookshelf"
        )

    book_in_shelf = BookInShelfModel(
        bookshelf_id=bookshelf.id,
        work_olid=book_data.work_olid,
    )

    db.add(book_in_shelf)
    await db.commit()
    await db.refresh(book_in_shelf)

    return BookInShelfSchema(
        id=book_in_shelf.id,
        work_olid=book_in_shelf.work_olid,
        added_at=book_in_shelf.added_at
    )


@router.get("/{bookshelf_id}", response_model=BookShelfList)
async def get_bookshelf(
        bookshelf_id: int,
        request: Request,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Get a specific bookshelf along with full details of all books in it.
    """

    # Get the bookshelf
    result = await db.execute(
        select(BookShelfModel)
        .where(BookShelfModel.id == bookshelf_id,
               BookShelfModel.user_id == current_user.id)
        .options(selectinload(BookShelfModel.books))
    )
    bookshelf = result.scalars().first()

    if not bookshelf:
        raise HTTPException(
            status_code=404,
            detail="Bookshelf not found"
        )

    service = request.app.state.open_library_service
    books_full = []

    for book_in_shelf in bookshelf.books:
        # Try to get the book from local books table
        book = await db.scalar(
            select(BookModel).where(BookModel.work_olid == book_in_shelf.work_olid)
        )

        # If not found locally, fetch from Open Library
        if not book:
            book_data = await service.get_book_by_work(book_in_shelf.work_olid)
            if book_data:
                book = BookModel(
                    work_olid=book_in_shelf.work_olid,
                    title=book_data.get("title"),
                    authors=", ".join(book_data.get("authors") or []),
                    cover_url=book_data.get("cover_url"),
                    published_year=book_data.get("year"),
                )
                db.add(book)
                await db.commit()
                await db.refresh(book)

        books_full.append(
            BookInShelfSchema(
                id=book_in_shelf.id,
                work_olid=book_in_shelf.work_olid,
                title=book.title if book else None,
                authors=book.authors.split(", ") if book and book.authors else [],
                year=book.published_year if book else None,
                cover_url=book.cover_url if book else None,
                added_at=book_in_shelf.added_at,
            )
        )

    return BookShelfList(
        id=bookshelf.id,
        name=bookshelf.name,
        description=bookshelf.description,
        created_at=bookshelf.created_at,
        books=books_full
    )


@router.patch("/{bookshelf_id}", response_model=BookShelfSchema)
async def update_bookshelf(
        bookshelf_id: int,
        bookshelf_data: BookShelfUpdate,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Update a specific bookshelf of the current user
    """

    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.id == bookshelf_id,
            BookShelfModel.user_id == current_user.id,
        )
    )
    bookshelf = result.scalars().first()

    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found"
        )

    if bookshelf_data.name is not None:
        bookshelf.name = bookshelf_data.name

    if bookshelf_data.description is not None:
        bookshelf.description = bookshelf_data.description

    await db.commit()
    await db.refresh(bookshelf)

    return BookShelfSchema(
        id=bookshelf.id,
        name=bookshelf.name,
        description=bookshelf.description,
        created_at=bookshelf.created_at,
        books=[]
    )


@router.delete("/{bookshelf_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bookshelf(
        bookshelf_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a specific bookshelf of the current user
    """

    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.id == bookshelf_id,
            BookShelfModel.user_id == current_user.id,
        )
    )
    bookshelf = result.scalars().first()

    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found"
        )

    await db.delete(bookshelf)
    await db.commit()

    return None


@router.delete("/{bookshelf_id}/books/{book_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_book_from_shelf(
        bookshelf_id: int,
        book_id: int,
        db: AsyncSession = Depends(get_async_db),
        current_user: UserModel = Depends(get_current_user)
):
    """
    Delete a specific book from a user's bookshelf.
    """

    result = await db.execute(
        select(BookShelfModel).where(
            BookShelfModel.id == bookshelf_id,
            BookShelfModel.user_id == current_user.id
        )
    )
    bookshelf = result.scalars().first()

    if not bookshelf:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Bookshelf not found"
        )

    result = await db.execute(
        select(BookInShelfModel).where(
            BookInShelfModel.id == book_id,
            BookInShelfModel.bookshelf_id == bookshelf.id
        )
    )
    book = result.scalars().first()

    if not book:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Book not found in this bookshelf"
        )

    await db.delete(book)
    await db.commit()

    return None