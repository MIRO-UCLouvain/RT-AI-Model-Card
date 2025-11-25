"""Repository layer for User database access.

Pure async SQLAlchemy queries — no business logic, no commits.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.types import Uuid

from models.user import User


class UserRepository:
    @staticmethod
    async def get_by_id(session: AsyncSession, user_id: uuid.UUID) -> User | None:
        result = await session.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_email(session: AsyncSession, email: str) -> User | None:
        result = await session.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def create(
        session: AsyncSession,
        email: str,
        hashed_password: str,
    ) -> User:
        user = User(email=email, hashed_password=hashed_password)
        session.add(user)
        await session.flush()  # populates user.id without committing
        return user
