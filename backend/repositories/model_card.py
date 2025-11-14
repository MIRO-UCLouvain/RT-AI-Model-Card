"""Repository layer for ModelCard and ModelCardVersion.

Responsibilities: async SQLAlchemy queries only.
No business logic, no HTTP exceptions, no commits.
"""

from sqlalchemy import func, select, update
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
    async def list_all(session: AsyncSession) -> list[ModelCard]:
        result = await session.execute(
            select(ModelCard).order_by(ModelCard.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def create(
        session: AsyncSession,
        slug: str,
        task_type: str,
    ) -> ModelCard:
        card = ModelCard(slug=slug, task_type=task_type)
        session.add(card)
        await session.flush()  # populate card.id without committing
        return card


class ModelCardVersionRepository:
    """Data-access methods for the ModelCardVersion table."""

    @staticmethod
    async def get_all_for_card(
        session: AsyncSession, card_id: int
    ) -> list[ModelCardVersion]:
        result = await session.execute(
            select(ModelCardVersion)
            .where(ModelCardVersion.model_card_id == card_id)
            .order_by(ModelCardVersion.version_number.asc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_max_version_number(
        session: AsyncSession, card_id: int
    ) -> int:
        """Return the highest existing version_number for a card, or 0 if none."""
        result = await session.execute(
            select(func.max(ModelCardVersion.version_number)).where(
                ModelCardVersion.model_card_id == card_id
            )
        )
        value = result.scalar()
        return value if value is not None else 0

    @staticmethod
    async def unset_latest(
        session: AsyncSession, card_id: int
    ) -> None:
        """Set is_latest=False on all versions of a card."""
        await session.execute(
            update(ModelCardVersion)
            .where(ModelCardVersion.model_card_id == card_id)
            .values(is_latest=False)
        )

    @staticmethod
    async def create(
        session: AsyncSession,
        card_id: int,
        version_number: int,
        title: str,
        content_json: dict,
    ) -> ModelCardVersion:
        version = ModelCardVersion(
            model_card_id=card_id,
            version_number=version_number,
            title=title,
            content_json=content_json,
            is_latest=True,
        )
        session.add(version)
        await session.flush()
        return version
