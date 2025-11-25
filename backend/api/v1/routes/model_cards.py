"""API routes for model card management.

All routes are thin: parse input, call one service function, return schema.
Business logic lives in services/model_card.py and services/publication.py.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
from models.user import User
from schemas.model_card import (
    ModelCardCreate,
    ModelCardRead,
    ModelCardSummary,
    ModelCardVersionCreate,
    ModelCardVersionRead,
)
from services import model_card as model_card_service
from services.publication import request_publication

router = APIRouter(prefix="/model-cards", tags=["model-cards"])


@router.post(
    "",
    response_model=ModelCardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model card",
)
async def create_model_card(
    data: ModelCardCreate,
    db: AsyncSession = Depends(get_db),
) -> ModelCardRead:
    card = await model_card_service.create_model_card(db, data)
    return ModelCardRead.model_validate(card)


@router.get(
    "",
    response_model=list[ModelCardSummary],
    status_code=status.HTTP_200_OK,
    summary="List all model cards",
)
async def list_model_cards(
    db: AsyncSession = Depends(get_db),
) -> list[ModelCardSummary]:
    cards = await model_card_service.list_model_cards(db)
    return [ModelCardSummary.model_validate(c) for c in cards]


@router.get(
    "/{card_id}/versions",
    response_model=list[ModelCardVersionRead],
    status_code=status.HTTP_200_OK,
    summary="List all versions of a model card",
)
async def get_versions(
    card_id: int,
    db: AsyncSession = Depends(get_db),
) -> list[ModelCardVersionRead]:
    versions = await model_card_service.get_versions(db, card_id)
    return [ModelCardVersionRead.model_validate(v) for v in versions]


@router.post(
    "/{card_id}/versions",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_201_CREATED,
    summary="Save a new version of an existing model card",
)
async def create_new_version(
    card_id: int,
    data: ModelCardVersionCreate,
    db: AsyncSession = Depends(get_db),
) -> ModelCardVersionRead:
    version = await model_card_service.create_new_version(db, card_id, data)
    return ModelCardVersionRead.model_validate(version)


@router.post(
    "/{card_id}/request-publication",
    response_model=ModelCardRead,
    status_code=status.HTTP_200_OK,
    summary="Request publication review for a model card",
)
async def request_publication_endpoint(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardRead:
    card = await request_publication(db, card_id, current_user)
    return ModelCardRead.model_validate(card)
