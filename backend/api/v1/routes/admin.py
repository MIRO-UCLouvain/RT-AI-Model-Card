"""Admin routes for model card version moderation."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_current_user, get_db
from models.user import User
from schemas.model_card import ModelCardVersionRead
from services.publication import approve_version, reject_version

router = APIRouter(prefix="/admin/model-card-versions", tags=["admin"])


@router.put(
    "/{version_id}/approve",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Approve a model card version for publication",
)
async def approve(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardVersionRead:
    ver = await approve_version(db, version_id, current_user)
    return ModelCardVersionRead.model_validate(ver)


@router.put(
    "/{version_id}/reject",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Reject a model card version publication request",
)
async def reject(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ModelCardVersionRead:
    ver = await reject_version(db, version_id, current_user)
    return ModelCardVersionRead.model_validate(ver)
