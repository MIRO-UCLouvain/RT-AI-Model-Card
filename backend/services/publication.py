"""Service layer for the per-version publication workflow.

Each ModelCardVersion owns its own status.  The card itself has no status;
only its individual versions do.

State machine (per version):
    draft ──submit──▶ in_review ──approve──▶ published
      ▲                   └──────reject────▶ rejected
      └──────────────────────────────────────────┘
                   (re-submit after rejection)
"""

import uuid

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from models.model_card import ModelCardVersion
from models.user import User
from repositories.model_card import ModelCardVersionRepository
from services.content_validation import validate_content_for_publication

# Statuses from which a user may submit/re-submit for review.
_SUBMITTABLE = {"draft", "rejected"}


async def _get_version_or_404(
    session: AsyncSession, version_id: int
) -> ModelCardVersion:
    ver = await ModelCardVersionRepository.get_by_id(session, version_id)
    if ver is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Model card version with id={version_id} not found.",
        )
    return ver


async def request_publication(
    session: AsyncSession,
    version_id: int,
    current_user: User,
    is_anonymous: bool = False,
) -> ModelCardVersion:
    """Move a version from draft|rejected → in_review.

    Once in_review the version is immutable: no new saves to this version entry.
    The user is still free to create a new version entry on the same card.

    Raises:
        403 if the caller is not the owner of the parent card.
        409 if the version is not in a submittable status.
        422 if the content is missing required fields for publication.
    """
    ver = await _get_version_or_404(session, version_id)

    owner_id: uuid.UUID | None = ver.model_card.owner_id  # type: ignore[union-attr]
    if owner_id is None or owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this model card.",
        )
    if ver.status not in _SUBMITTABLE:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=(
                f"Cannot submit version '{ver.version}' for review: "
                f"current status is '{ver.status}'. "
                "Only versions with status 'draft' or 'rejected' can be submitted."
            ),
        )

    # Validate required fields before allowing publication submission.
    task_type: str | None = getattr(ver.model_card, "task_type", None)
    validate_content_for_publication(ver.content or {}, task_type=task_type)

    ver.status = "in_review"
    ver.is_anonymous = is_anonymous
    await session.commit()
    return await _get_version_or_404(session, version_id)


async def approve_version(
    session: AsyncSession,
    version_id: int,
    current_user: User,
) -> ModelCardVersion:
    """Move a version from in_review → published.

    Raises:
        403 if the caller is not an admin.
        409 if the version is not currently in_review.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    ver = await _get_version_or_404(session, version_id)

    if ver.status != "in_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot approve: version is '{ver.status}', expected 'in_review'.",
        )

    ver.status = "published"
    await session.commit()
    return await _get_version_or_404(session, version_id)


async def reject_version(
    session: AsyncSession,
    version_id: int,
    current_user: User,
    feedback: str | None = None,
) -> ModelCardVersion:
    """Move a version from in_review → rejected.

    Raises:
        403 if the caller is not an admin.
        409 if the version is not currently in_review.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    ver = await _get_version_or_404(session, version_id)

    if ver.status != "in_review":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Cannot reject: version is '{ver.status}', expected 'in_review'.",
        )

    ver.status = "rejected"
    ver.rejection_feedback = feedback or None
    await session.commit()
    return await _get_version_or_404(session, version_id)


async def list_published_versions(
    session: AsyncSession,
) -> list[ModelCardVersion]:
    """Return all published versions (public catalogue), newest first."""
    return await ModelCardVersionRepository.list_published(session)


async def list_pending_versions(
    session: AsyncSession,
    current_user: User,
) -> list[ModelCardVersion]:
    """Return all versions awaiting admin review (in_review), oldest first.

    Raises:
        403 if the caller is not an admin.
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required.",
        )
    return await ModelCardVersionRepository.list_pending(session)
