"""Repository layer for ModelCard and ModelCardVersion.

Responsibilities: async SQLAlchemy queries only.
No business logic, no HTTP exceptions, no commits.
"""

import uuid

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from models.model_card import ModelCard, ModelCardVersion


class ModelCardRepository:
    """Data-access methods for the ModelCard table."""

    @staticmethod
    async def get_by_id(
        session: AsyncSession, card_id: int
    ) -> ModelCard | None:
        result = await session.execute(
            select(ModelCard)
            .where(ModelCard.id == card_id)
            .options(selectinload(ModelCard.versions))
        )
        return result.scalars().first()

    @staticmethod
    async def get_by_slug(
        session: AsyncSession, slug: str
    ) -> ModelCard | None:
        result = await session.execute(
            select(ModelCard).where(ModelCard.slug == slug)
        )
        return result.scalars().first()

    @staticmethod
    async def list_for_owner(
        session: AsyncSession, owner_id: uuid.UUID
    ) -> list[ModelCard]:
        """Return all cards owned by *owner_id*, newest first."""
        result = await session.execute(
            select(ModelCard)
            .where(ModelCard.owner_id == owner_id)
            .options(selectinload(ModelCard.versions))
            .order_by(ModelCard.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        slug: str,
        task_type: str,
        owner_id: uuid.UUID | None = None,
    ) -> ModelCard:
        card = ModelCard(slug=slug, task_type=task_type, owner_id=owner_id)
        session.add(card)
        await session.flush()  # populate card.id without committing
        return card


class ModelCardVersionRepository:
    """Data-access methods for the ModelCardVersion table."""

    @staticmethod
    async def get_by_id(
        session: AsyncSession, version_id: int
    ) -> ModelCardVersion | None:
        """Return a single version with its parent card loaded."""
        result = await session.execute(
            select(ModelCardVersion)
            .where(ModelCardVersion.id == version_id)
            .options(selectinload(ModelCardVersion.model_card))
        )
        return result.scalars().first()

    @staticmethod
    async def get_all_for_card(
        session: AsyncSession, card_id: int
    ) -> list[ModelCardVersion]:
        result = await session.execute(
            select(ModelCardVersion)
            .where(ModelCardVersion.model_card_id == card_id)
            .order_by(ModelCardVersion.created_at.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def version_exists(
        session: AsyncSession, card_id: int, version: str
    ) -> bool:
        """Return True if a version with the given string already exists for this card."""
        result = await session.execute(
            select(ModelCardVersion.id).where(
                ModelCardVersion.model_card_id == card_id,
                ModelCardVersion.version == version,
            )
        )
        return result.scalar() is not None

    @staticmethod
    async def list_published(
        session: AsyncSession,
    ) -> list[ModelCardVersion]:
        """Return all versions with status 'published', with parent card loaded."""
        result = await session.execute(
            select(ModelCardVersion)
            .where(ModelCardVersion.status == "published")
            .options(selectinload(ModelCardVersion.model_card))
            .order_by(ModelCardVersion.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        card_id: int,
        version: str,
        title: str,
        content: dict,
        created_by: uuid.UUID | None = None,
    ) -> ModelCardVersion:
        ver = ModelCardVersion(
            model_card_id=card_id,
            version=version,
            title=title,
            content=content,
            status="draft",
            created_by=created_by,
        )
        session.add(ver)
        await session.flush()
        return ver
