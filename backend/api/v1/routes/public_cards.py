"""Public catalogue — no authentication required."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db
from repositories.model_card import ModelCardVersionRepository
from schemas.model_card import ModelCardVersionRead, PublishedVersionSummary
from services.publication import list_published_versions

router = APIRouter(prefix="/public-model-cards", tags=["public"])


@router.get(
    "",
    response_model=list[PublishedVersionSummary],
    status_code=status.HTTP_200_OK,
    summary="List all published model card versions (public catalogue)",
)
async def list_public_cards(
    db: AsyncSession = Depends(get_db),
) -> list[PublishedVersionSummary]:
    versions = await list_published_versions(db)
    return [PublishedVersionSummary.from_version(v) for v in versions]


@router.get(
    "/{version_id}",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Get full content of a published model card version",
)
async def get_public_card_detail(
    version_id: int,
    db: AsyncSession = Depends(get_db),
) -> ModelCardVersionRead:
    ver = await ModelCardVersionRepository.get_by_id(db, version_id)
    if ver is None or ver.status != "published":
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Published version not found.",
        )
    return ModelCardVersionRead.model_validate(ver)
