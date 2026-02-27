"""Repository layer for User database access.

Pure async SQLAlchemy queries — no business logic, no commits.
"""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

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
    async def list_all(session: AsyncSession) -> list[User]:
        result = await session.execute(
            select(User).order_by(User.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        email: str,
        hashed_password: str,
        first_name: str | None = None,
        last_name: str | None = None,
        institution: str | None = None,
        country: str | None = None,
    ) -> User:
        user = User(
            email=email,
            hashed_password=hashed_password,
            first_name=first_name,
            last_name=last_name,
            institution=institution,
            country=country,
        )
        session.add(user)
        await session.flush()  # populates user.id without committing
        return user
