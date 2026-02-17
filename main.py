from contextlib import asynccontextmanager

import httpx
import uvicorn
from fastapi import FastAPI

from app.routers import auth, users, books, reviews, favorites, bookshelves, user_books
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
    description=("Library Hub is a REST API for managing books, reviews, favorites and personal bookshelves."),
    lifespan=lifespan
)


# connecting routers
app.include_router(auth.router)
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
