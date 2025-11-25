"""Admin routes for model card moderation."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
from models.user import User
from schemas.model_card import ModelCardRead
from services.publication import approve_card, reject_card

router = APIRouter(prefix="/admin/model-cards", tags=["admin"])


@router.put(
    "/{card_id}/approve",
    response_model=ModelCardRead,
    status_code=status.HTTP_200_OK,
    summary="Approve a model card for publication",
)
async def approve(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardRead:
    card = await approve_card(db, card_id, current_user)
    return ModelCardRead.model_validate(card)


@router.put(
    "/{card_id}/reject",
    response_model=ModelCardRead,
    status_code=status.HTTP_200_OK,
    summary="Reject a model card publication request",
)
async def reject(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardRead:
    card = await reject_card(db, card_id, current_user)
    return ModelCardRead.model_validate(card)
