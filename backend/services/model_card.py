"""Service layer for model card business logic.

Responsibilities:
- Enforce business rules (slug uniqueness, user-defined version uniqueness)
- Own the transaction boundary (commit)
- Raise HTTPException for domain violations
- Delegate all DB access to the repository layer
"""

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.model_card import ModelCard, ModelCardVersion
from repositories.model_card import (
    ModelCardRepository,
    ModelCardVersionRepository,
)
from schemas.model_card import ModelCardCreate, ModelCardVersionCreate


def _require_nonempty_version(user_version: str) -> None:
    """Raise 422 if user_version is blank."""
    if not user_version.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Version number cannot be empty. "
                "Fill in the 'Version Number' field in the Card Metadata section before saving."
            ),
        )


async def create_model_card(
    session: AsyncSession,
    data: ModelCardCreate,
    owner_id: uuid.UUID | None = None,
) -> ModelCard:
    """Create a new model card with its first version (status=draft).

    Raises 409 if a card with the same slug already exists.
    Raises 422 if the version number is empty.
    """
    _require_nonempty_version(data.first_version.user_version)

    existing = await ModelCardRepository.get_by_slug(session, data.slug)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"A model card with slug '{data.slug}' already exists.",
        )

    card = await ModelCardRepository.create(
        session, slug=data.slug, task_type=data.task_type, owner_id=owner_id
    )
    await ModelCardVersionRepository.create(
        session,
        card_id=card.id,
        version=data.first_version.user_version.strip(),
        title=data.first_version.title,
        content=data.first_version.content,
        created_by=owner_id,
    )

    await session.commit()
    refreshed = await ModelCardRepository.get_by_id(session, card.id)
    assert refreshed is not None
    return refreshed


async def create_new_version(
    session: AsyncSession,
    card_id: int,
    data: ModelCardVersionCreate,
    created_by: uuid.UUID | None = None,
) -> ModelCardVersion:
    """Add a new draft version to an existing model card.

    Each call creates an independent, immutable version entry.
    Versions with status in_review or published are never modified.

    Raises 404 if the model card does not exist.
    Raises 409 if a version with the same number already exists for this card.
    Raises 422 if the version number is empty.
    """
    _require_nonempty_version(data.user_version)

    card = await ModelCardRepository.get_by_id(session, card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card with id={card_id} not found.",
        )

    user_version = data.user_version.strip()
    if await ModelCardVersionRepository.version_exists(session, card_id, user_version):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Version '{user_version}' already exists for this model card. "
                "Use a different version number."
            ),
        )

    version = await ModelCardVersionRepository.create(
        session,
        card_id=card_id,
        version=user_version,
        title=data.title,
        content=data.content,
        created_by=created_by,
    )

    # Touch the parent card's updated_at so listings reflect latest activity
    card.updated_at = datetime.now(UTC)

    await session.commit()
    await session.refresh(version)
    return version


async def list_model_cards_for_user(
    session: AsyncSession, owner_id: uuid.UUID
) -> list[ModelCard]:
    """Return only the cards owned by *owner_id*, newest first."""
    return await ModelCardRepository.list_for_owner(session, owner_id)


async def get_versions(
    session: AsyncSession,
    card_id: int,
) -> list[ModelCardVersion]:
    """Return all versions of a model card ordered by creation date ascending.

    Raises 404 if the model card does not exist.
    """
    card = await ModelCardRepository.get_by_id(session, card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card with id={card_id} not found.",
        )
    return await ModelCardVersionRepository.get_all_for_card(session, card_id)
