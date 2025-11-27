"""Service layer for user business logic.

Responsibilities:
- Normalise email (lowercase + strip)
- Enforce uniqueness (400 if email already registered)
- Hash password and delegate persistence to the repository
- Own the transaction boundary (commit)
- Authenticate users for login
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.user import User
from repositories.user import UserRepository
from schemas.user import UserCreate
from security import hash_password, verify_password


async def create_user(session: AsyncSession, data: UserCreate) -> User:
    """Register a new user.

    Raises 400 if the email is already taken.
    """
    normalised_email = data.email.lower().strip()
    existing = await UserRepository.get_by_email(session, normalised_email)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists.",
        )
    hashed = hash_password(data.password)
    user = await UserRepository.create(
        session,
        normalised_email,
        hashed,
        first_name=data.first_name,
        last_name=data.last_name,
    )
    await session.commit()
    # User has no lazy-loaded relationships — refresh is safe here
    await session.refresh(user)
    return user


async def authenticate_user(
    session: AsyncSession,
    email: str,
    password: str,
) -> User:
    """Verify credentials and return the User on success.

    Raises 401 if the email is not found or the password is wrong.
    Raises 400 if the account is inactive.
    """
    normalised_email = email.lower().strip()
    user = await UserRepository.get_by_email(session, normalised_email)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )
    return user
