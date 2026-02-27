"""Admin routes for user management.

All endpoints require ``is_admin=True`` via the ``require_admin`` dependency.
Passwords and hashed_password are never exposed.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from dependencies import get_db, require_admin
from models.user import User
from repositories.user import UserRepository
from schemas.user import UserResponse

router = APIRouter(prefix="/admin/users", tags=["admin"])


@router.get(
    "",
    response_model=list[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="List all registered users (admin only)",
)
async def list_users(
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> list[UserResponse]:
    users = await UserRepository.list_all(db)
    return [UserResponse.model_validate(u) for u in users]


async def _get_target_user(
    db: AsyncSession, user_id: uuid.UUID
) -> User:
    """Fetch the target user or raise 404."""
    user = await UserRepository.get_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User with id={user_id} not found.",
        )
    return user


@router.put(
    "/{user_id}/activate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Activate a user account",
)
async def activate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> UserResponse:
    user = await _get_target_user(db, user_id)
    user.is_active = True
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/deactivate",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate a user account",
)
async def deactivate_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account.",
        )
    user = await _get_target_user(db, user_id)
    user.is_active = False
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/grant-admin",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Grant admin privileges to a user",
)
async def grant_admin(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(require_admin),
) -> UserResponse:
    user = await _get_target_user(db, user_id)
    user.is_admin = True
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)


@router.put(
    "/{user_id}/revoke-admin",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Revoke admin privileges from a user",
)
async def revoke_admin(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
) -> UserResponse:
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot revoke your own admin privileges.",
        )
    user = await _get_target_user(db, user_id)
    user.is_admin = False
    await db.commit()
    await db.refresh(user)
    return UserResponse.model_validate(user)
