"""Repository layer for PasswordResetToken database access.

Pure async SQLAlchemy queries — no business logic, no commits.
"""

import uuid
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from models.password_reset_token import PasswordResetToken


class PasswordResetRepository:
    @staticmethod
    async def invalidate_active_tokens_for_user(
        session: AsyncSession,
        user_id: uuid.UUID,
    ) -> None:
        """Mark all non-expired, unused tokens for *user_id* as consumed now.

        Called both when issuing a new token (so older links become dead)
        and after a successful reset (to clean up any parallel requests).
        """
        now = datetime.now(UTC)
        await session.execute(
            update(PasswordResetToken)
            .where(
                PasswordResetToken.user_id == user_id,
                PasswordResetToken.used_at.is_(None),
                PasswordResetToken.expires_at > now,
            )
            .values(used_at=now)
        )

    @staticmethod
    async def create(
        session: AsyncSession,
        user_id: uuid.UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """Insert a new token row and return it (id populated after flush)."""
        token = PasswordResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at,
        )
        session.add(token)
        await session.flush()
        return token

    @staticmethod
    async def get_valid_by_hash(
        session: AsyncSession,
        token_hash: str,
    ) -> PasswordResetToken | None:
        """Return the token if it exists, is not expired, and has not been used.

        Returns ``None`` for any invalid state — callers must never distinguish
        between expired, used, or non-existent tokens in user-facing messages.
        """
        now = datetime.now(UTC)
        result = await session.execute(
            select(PasswordResetToken).where(
                PasswordResetToken.token_hash == token_hash,
                PasswordResetToken.expires_at > now,
                PasswordResetToken.used_at.is_(None),
            )
        )
        return result.scalar_one_or_none()  # type: ignore[return-value]
