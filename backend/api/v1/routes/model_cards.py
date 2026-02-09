"""API routes for model card management.

All routes are thin: parse input, call one service function, return schema.
Business logic lives in services/model_card.py and services/publication.py.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
from models.user import User
from schemas.model_card import (
    DiffResponse,
    ModelCardCreate,
    ModelCardRead,
    ModelCardSummary,
    ModelCardVersionCreate,
    ModelCardVersionRead,
    SectionDiff,
)
from services import model_card as model_card_service
from services.diff import compute_diff
from services.publication import request_publication
from repositories.model_card import ModelCardVersionRepository

router = APIRouter(prefix="/model-cards", tags=["model-cards"])


@router.post(
    "",
    response_model=ModelCardRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new model card with its first version",
)
async def create_model_card(
    data: ModelCardCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardRead:
    card = await model_card_service.create_model_card(
        db, data, owner_id=current_user.id
    )
    return ModelCardRead.model_validate(card)


@router.get(
    "",
    response_model=list[ModelCardRead],
    status_code=status.HTTP_200_OK,
    summary="List model cards owned by the authenticated user",
)
async def list_model_cards(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[ModelCardRead]:
    cards = await model_card_service.list_model_cards_for_user(db, current_user.id)
    return [ModelCardRead.model_validate(c) for c in cards]


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


@router.delete(
    "/{card_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a model card and all its versions",
)
async def delete_model_card(
    card_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    await model_card_service.delete_model_card(db, card_id, owner_id=current_user.id)


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
    current_user: User = Depends(get_current_user),
) -> ModelCardVersionRead:
    version = await model_card_service.create_new_version(
        db, card_id, data, created_by=current_user.id
    )
    return ModelCardVersionRead.model_validate(version)


@router.get(
    "/{card_id}/versions/compare",
    response_model=DiffResponse,
    status_code=status.HTTP_200_OK,
    summary="Compare two versions of a model card",
)
async def compare_versions(
    card_id: int,
    old_id: int = Query(..., description="ID of the older version"),
    new_id: int = Query(..., description="ID of the newer version"),
    db: AsyncSession = Depends(get_db),
) -> DiffResponse:
    if old_id == new_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="old_id and new_id must be different.",
        )

    old_ver = await ModelCardVersionRepository.get_by_id(db, old_id)
    new_ver = await ModelCardVersionRepository.get_by_id(db, new_id)

    missing = [
        label
        for label, ver in (("old_id", old_ver), ("new_id", new_ver))
        if ver is None
    ]
    if missing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Version(s) not found: {', '.join(missing)}.",
        )

    # Both versions must belong to the same card.
    if old_ver.model_card_id != card_id or new_ver.model_card_id != card_id:  # type: ignore[union-attr]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both versions must belong to the specified model card.",
        )

    raw_diff = compute_diff(old_ver.content, new_ver.content)  # type: ignore[union-attr]

    sections = {
        section: SectionDiff.model_validate(section_data)
        for section, section_data in raw_diff.items()
    }

    return DiffResponse(
        old_version_id=old_id,
        new_version_id=new_id,
        old_version=old_ver.version,  # type: ignore[union-attr]
        new_version=new_ver.version,  # type: ignore[union-attr]
        sections=sections,
    )


@router.post(
    "/{card_id}/versions/{version_id}/submit",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Submit a version for publication review",
)
async def submit_version(
    card_id: int,  # kept for URL legibility / future ownership checks at route level
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardVersionRead:
    ver = await request_publication(db, version_id, current_user)
    return ModelCardVersionRead.model_validate(ver)
