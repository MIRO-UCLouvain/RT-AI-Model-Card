"""Public catalogue — no authentication required."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from schemas.model_card import ModelCardSummary
from services.publication import list_approved_cards

router = APIRouter(prefix="/public-model-cards", tags=["public"])


@router.get(
    "",
    response_model=list[ModelCardSummary],
    status_code=status.HTTP_200_OK,
    summary="List all approved model cards (public catalogue)",
)
async def list_public_cards(
    db: AsyncSession = Depends(get_db),
) -> list[ModelCardSummary]:
    cards = await list_approved_cards(db)
    return [ModelCardSummary.model_validate(c) for c in cards]
