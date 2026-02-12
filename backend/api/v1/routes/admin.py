"""Admin routes for model card version moderation."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db, require_admin
from models.user import User
from schemas.model_card import ModelCardVersionRead, PublishedVersionSummary, RejectRequest
from services.publication import approve_version, list_pending_versions, reject_version
from repositories.model_card import ModelCardVersionRepository

router = APIRouter(prefix="/admin/model-card-versions", tags=["admin"])


@router.get(
    "/pending",
    response_model=list[PublishedVersionSummary],
    status_code=status.HTTP_200_OK,
    summary="List all model card versions awaiting admin review (in_review)",
)
async def list_pending(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> list[PublishedVersionSummary]:
    versions = await list_pending_versions(db, current_user)
    return [PublishedVersionSummary.from_version(v) for v in versions]


@router.get(
    "/{version_id}",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Fetch full content of any version for admin review (read-only)",
)
async def get_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ModelCardVersionRead:
    from fastapi import HTTPException  # noqa: PLC0415

    ver = await ModelCardVersionRepository.get_by_id(db, version_id)
    if ver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card version with id={version_id} not found.",
        )
    return ModelCardVersionRead.model_validate(ver)


@router.put(
    "/{version_id}/approve",
    response_model=ModelCardVersionRead,
    status_code=status.HTTP_200_OK,
    summary="Approve a model card version for publication",
)
async def approve(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
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
    body: RejectRequest = RejectRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> ModelCardVersionRead:
    ver = await reject_version(db, version_id, current_user, feedback=body.feedback)
    return ModelCardVersionRead.model_validate(ver)
