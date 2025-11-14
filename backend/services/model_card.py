"""Service layer for model card business logic.

Responsibilities:
- Enforce business rules (slug uniqueness, version auto-increment, is_latest flag)
- Own the transaction boundary (commit)
- Raise HTTPException for domain violations
- Delegate all DB access to the repository layer
"""

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.model_card import ModelCard, ModelCardVersion
from repositories.model_card import (
    ModelCardRepository,
    ModelCardVersionRepository,
)
from schemas.model_card import ModelCardCreate, ModelCardVersionCreate


async def create_model_card(
    session: AsyncSession,
    data: ModelCardCreate,
) -> ModelCard:
    """Create a new model card with its first version.

    Raises 409 if a card with the same slug already exists.
    """
    existing = await ModelCardRepository.get_by_slug(session, data.slug)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A model card with slug '{data.slug}' already exists.",
        )

    card = await ModelCardRepository.create(
        session, slug=data.slug, task_type=data.task_type
    )
    await ModelCardVersionRepository.create(
        session,
        card_id=card.id,
        version_number=1,
        title=data.first_version.title,
        content_json=data.first_version.content_json,
    )

    await session.commit()
    await session.refresh(card)
    return card


async def create_new_version(
    session: AsyncSession,
    card_id: int,
    data: ModelCardVersionCreate,
) -> ModelCardVersion:
    """Add a new version to an existing model card.

    - Flips is_latest=False on all previous versions.
    - Auto-increments version_number.
    - Touches card.updated_at.

    Raises 404 if the model card does not exist.
    """
    card = await ModelCardRepository.get_by_id(session, card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card with id={card_id} not found.",
        )

    await ModelCardVersionRepository.unset_latest(session, card_id)

    next_num = (
        await ModelCardVersionRepository.get_max_version_number(session, card_id) + 1
    )
    version = await ModelCardVersionRepository.create(
        session,
        card_id=card_id,
        version_number=next_num,
        title=data.title,
        content_json=data.content_json,
    )

    # Touch the parent card's updated_at so listings reflect the latest activity
    card.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(version)
    return version


async def list_model_cards(session: AsyncSession) -> list[ModelCard]:
    """Return all model cards ordered by creation date (newest first)."""
    return await ModelCardRepository.list_all(session)


async def get_versions(
    session: AsyncSession,
    card_id: int,
) -> list[ModelCardVersion]:
    """Return all versions of a model card ordered by version_number ascending.

    Raises 404 if the model card does not exist.
    """
    card = await ModelCardRepository.get_by_id(session, card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card with id={card_id} not found.",
        )
    return await ModelCardVersionRepository.get_all_for_card(session, card_id)
