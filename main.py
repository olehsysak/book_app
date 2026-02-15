from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI

from app.routers import users, books, reviews, favorites, bookshelves, user_books
from app.services.open_library import OpenLibraryService


@asynccontextmanager
async def lifespan(app: FastAPI):
    # startup
    http_client = httpx.AsyncClient(base_url="https://openlibrary.org")
    app.state.open_library_service = OpenLibraryService(http_client)
    yield  # here FastAPI handles requests
    # shutdown
    await app.state.open_library_service.client.aclose()


# Connecting lifespan to FastAPI
app = FastAPI(
    title="Library Hub",
    version="0.1.0",
    description=(
        "The Library Hub API is an API for managing books.\n"
        "It allows users to:\n"
        "- Search for books and view detailed information about specific books\n"
        "- Add and view reviews for books\n"
        "- Mark books as favorites\n\n"
        "- Add, edit, and delete books on their own bookshelves\n"
        "- Set and update the reading status of books\n"
        "- The API integrates with Open Library to fetch book metadata."
    ),
    lifespan=lifespan
)


# connecting routers
app.include_router(users.router)
app.include_router(books.router)
app.include_router(reviews.router)
app.include_router(favorites.router)
app.include_router(bookshelves.router)
app.include_router(user_books.router)


# root endpoint
@app.get("/")
async def root():
    return {"status": "ok"}


if __name__ == '__main__':
    uvicorn.run('main:app', reload=True)
