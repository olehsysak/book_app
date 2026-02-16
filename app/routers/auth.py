from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import OAuth2PasswordRequestForm
import jwt

from app.models.users import User as UserModel
from app.schemas.auth import RefreshTokenRequest
from app.depends import get_async_db
from app.auth import verify_password, create_access_token, create_refresh_token
from app.config import SECRET_KEY, ALGORITHM


router = APIRouter(
    prefix="/auth",
    tags=["auth"],
)


@router.post("/token", summary="User login",)
async def login(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: AsyncSession = Depends(get_async_db)
):
    """
    Authenticate user and return JWT access and refresh tokens.
    """

    result = await db.scalars(
        select(UserModel).where(UserModel.email == form_data.username, UserModel.is_active == True))
    user = result.first()

    if not user or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": user.role,
            "id": user.id}
    )

    refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "role": user.role,
            "id": user.id})

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }


@router.post("/refresh-token", summary="Refresh JWT token")
async def refresh_token(
    body: RefreshTokenRequest,
    db: AsyncSession = Depends(get_async_db),
):
    """
    Send a refresh token to obtain a new JWT access token and refresh token.
    """

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate refresh token",
        headers={"WWW-Authenticate": "Bearer"},
    )

    old_refresh_token = body.refresh_token

    # Validate refresh JWT (signature, expiration, token type)
    try:
        payload = jwt.decode(old_refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str | None = payload.get("sub")
        token_type: str | None = payload.get("token_type")

        if email is None or token_type != "refresh":
            raise credentials_exception

    except jwt.ExpiredSignatureError:
        raise credentials_exception

    except jwt.PyJWTError:
        raise credentials_exception

    result = await db.scalars(
        select(UserModel).where(
            UserModel.email == email,
            UserModel.is_active == True
        )
    )
    user = result.first()
    if user is None:
        raise credentials_exception

    new_refresh_token = create_refresh_token(
        data={
            "sub": user.email,
            "role": user.role,
            "id": user.id}
    )

    return {
        "refresh_token": new_refresh_token,
        "token_type": "bearer",
    }