from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.users import User as UserModel
from app.schemas.users import User as UserSchema, UserCreate, UserUpdate
from app.depends import get_async_db
from app.auth import hash_password
from app.auth import get_current_user, get_current_admin


router = APIRouter(
    prefix="/users",
    tags=["users"],
)


@router.get("/me", response_model=UserSchema, summary="Get current user info")
async def get_me(
    current_user: UserModel = Depends(get_current_user),
):
    """
    Returns the information of the currently authenticated user.
    """
    return current_user


@router.get("/", response_model=list[UserSchema], summary="Get all users")
async def get_users(
    admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Returns a list of all registered users.

    - Only accessible to admins
    """

    result = await db.scalars(select(UserModel))
    return result.all()


@router.get("/{user_id}", response_model=UserSchema, summary="Get user by ID")
async def get_user(
    user_id: int,
    admin: UserModel = Depends(get_current_admin),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Returns the details of a specific user by ID.

    - Only admins can access this endpoint
    """

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user


@router.patch("/{user_id}", response_model=UserSchema, summary="Update user info")
async def update_user(
    user_id: int,
    data: UserUpdate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Update information of a user.

    - Users can update only their username
    - Admins can update username, role, and active status
    """

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin = current_user.role == "admin"
    is_owner = current_user.id == user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    if not is_admin and data.username is not None:
        user.username = data.username

    if is_admin:
        if data.username is not None:
            user.username = data.username
        if data.role is not None:
            user.role = data.role
        if data.is_active is not None:
            user.is_active = data.is_active

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, summary="Delete a user")
async def delete_user(
    user_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_async_db),
):
    """
    Delete a user by ID.

    - Users can delete themselves
    - Admins can delete any user
    """

    result = await db.scalars(
        select(UserModel).where(UserModel.id == user_id)
    )
    user = result.first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    is_admin = current_user.role == "admin"
    is_owner = current_user.id == user_id

    if not (is_admin or is_owner):
        raise HTTPException(status_code=403, detail="Not enough permissions")

    await db.delete(user)
    await db.commit()
    return None



@router.post("/", response_model=UserSchema, status_code=status.HTTP_201_CREATED, summary="Create a new user")
async def create_user(
        user: UserCreate,
        db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user with email, username, and password.

    - Role is set to 'user' by default
    """

    result = await db.scalar(select(UserModel).where(UserModel.email == user.email))
    if result:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User already exists"
        )

    db_user = UserModel(
        email=user.email,
        username=user.username,
        hashed_password=hash_password(user.password),
        role="user",
        is_active=True,
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user