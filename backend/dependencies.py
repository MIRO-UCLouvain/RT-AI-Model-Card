"""FastAPI dependency injection providers."""

import uuid
from collections.abc import AsyncGenerator

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from db.session import AsyncSessionLocal
from models.user import User
from repositories.user import UserRepository
from security import verify_token

# Points to the login endpoint so Swagger UI's "Authorize" button works.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/v1/auth/login")


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session and guarantee it is closed afterwards."""
    async with AsyncSessionLocal() as session:
        yield session


async def get_current_user_id(
    token: str = Depends(oauth2_scheme),
) -> uuid.UUID:
    """Extract and validate the JWT, returning the authenticated user's id."""
    return verify_token(token)


async def get_current_user(
    user_id: uuid.UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the JWT to a full User ORM object.

    Raises 401 if the token is valid but the user no longer exists.

    Usage in protected route handlers::

        @router.get("/me")
        async def me(current_user: User = Depends(get_current_user)):
            ...
    """
    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
