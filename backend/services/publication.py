"""Service layer for the model card publication workflow.

State machine:
  draft ──request──▶ pending ──approve──▶ approved
                         └────reject────▶ rejected
"""

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.model_card import ModelCard
from models.user import User
from repositories.model_card import ModelCardRepository


async def _get_card_or_404(session: AsyncSession, card_id: int) -> ModelCard:
    card = await ModelCardRepository.get_by_id(session, card_id)
    if card is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card with id={card_id} not found.",
        )
    return card


async def request_publication(
    session: AsyncSession,
    card_id: int,
    current_user: User,
) -> ModelCard:
    """Move a card from draft → pending.

    Raises:
        403 if the caller is not the card owner.
        409 if the card is not currently in draft status.
    """
    card = await _get_card_or_404(session, card_id)

    if card.owner_id is None or card.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this model card.",
        )
    if card.publication_status != "draft":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot request publication: card is '{card.publication_status}', expected 'draft'.",
        )

    card.publication_status = "pending"
    await session.commit()
    return await ModelCardRepository.get_by_id(session, card_id)  # type: ignore[return-value]


async def approve_card(
    session: AsyncSession,
    card_id: int,
    current_user: User,
) -> ModelCard:
    """Move a card from pending → approved.

    Raises:
        403 if the caller is not an admin.
        409 if the card is not currently pending.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    card = await _get_card_or_404(session, card_id)

    if card.publication_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve: card is '{card.publication_status}', expected 'pending'.",
        )

    card.publication_status = "approved"
    await session.commit()
    return await ModelCardRepository.get_by_id(session, card_id)  # type: ignore[return-value]


async def reject_card(
    session: AsyncSession,
    card_id: int,
    current_user: User,
) -> ModelCard:
    """Move a card from pending → rejected.

    Raises:
        403 if the caller is not an admin.
        409 if the card is not currently pending.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    card = await _get_card_or_404(session, card_id)

    if card.publication_status != "pending":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reject: card is '{card.publication_status}', expected 'pending'.",
        )

    card.publication_status = "rejected"
    await session.commit()
    return await ModelCardRepository.get_by_id(session, card_id)  # type: ignore[return-value]


async def list_approved_cards(session: AsyncSession) -> list[ModelCard]:
    """Return all approved model cards (public catalogue)."""
    return await ModelCardRepository.list_approved(session)
