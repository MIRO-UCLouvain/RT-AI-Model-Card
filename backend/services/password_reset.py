"""Service layer for the forgot-password / reset-password flow.

Security invariants enforced here:
- Email existence is never revealed to the caller.
- Tokens are hashed before storage; only the hash touches the database.
- Every token expires after PASSWORD_RESET_EXPIRE_MINUTES minutes.
- Tokens are single-use: after a successful reset every active token for
  that user (including the one just consumed) is invalidated.
- Older active tokens are pre-emptively invalidated when a new one is issued.
- Passwords are hashed with the same bcrypt context used at registration.
- SMTP errors are caught and logged; the caller still receives a generic
  success so as not to leak email enumeration information.
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from config import settings
from repositories.password_reset import PasswordResetRepository
from repositories.user import UserRepository
from security import hash_password
from services.email import send_password_reset_email

logger = logging.getLogger(__name__)

_RESET_TOKEN_BYTES = 32  # 256 bits of entropy → URL-safe base64 string


def _hash_token(raw_token: str) -> str:
    """Return the SHA-256 hex digest of *raw_token*.

    The digest (64 hex chars) is what we store in the database.
    """
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


async def request_password_reset(
    session: AsyncSession,
    email: str,
) -> None:
    """Trigger a password reset request for *email*.

    Always returns without raising — callers must show the same generic
    success message regardless of whether the email is registered.

    If the email corresponds to an active account:
    1. Any existing active reset tokens for that user are invalidated.
    2. A new cryptographically secure token is generated and its hash stored.
    3. A reset email is sent with the raw token embedded in the link.
    """
    normalised_email = email.lower().strip()
    user = await UserRepository.get_by_email(session, normalised_email)

    if user is None:
        # Not found — return silently so caller cannot enumerate emails.
        return

    # Invalidate pre-existing active tokens so only this new one is valid.
    await PasswordResetRepository.invalidate_active_tokens_for_user(
        session, user.id
    )

    raw_token = secrets.token_urlsafe(_RESET_TOKEN_BYTES)
    token_hash = _hash_token(raw_token)
    expires_at = datetime.now(UTC) + timedelta(
        minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES
    )

    await PasswordResetRepository.create(
        session,
        user_id=user.id,
        token_hash=token_hash,
        expires_at=expires_at,
    )
    await session.commit()

    reset_url = (
        f"{settings.FRONTEND_BASE_URL}"
        f"/?view=reset_password&token={raw_token}"
    )

    try:
        await send_password_reset_email(
            recipient_email=normalised_email,
            reset_url=reset_url,
            expiry_minutes=settings.PASSWORD_RESET_EXPIRE_MINUTES,
        )
    except Exception:
        # SMTP delivery failure must not cause a 500 — the token is already
        # stored so a retry (re-requesting reset) will work.  Log only the
        # user_id (never email or token) to avoid leaking PII in log aggregators.
        logger.exception(
            "Failed to deliver password reset email for user_id=%s", user.id
        )


async def reset_password(
    session: AsyncSession,
    raw_token: str,
    new_password: str,
) -> None:
    """Apply the password reset identified by *raw_token*.

    On any invalid state (unknown, expired, or already-used token) raises
    HTTP 400 with a generic message — callers must not distinguish between
    these cases in user-facing output.

    On success:
    1. The user's hashed_password is updated.
    2. The consumed token and all other active tokens for that user are
       invalidated so the link cannot be reused.
    3. The transaction is committed atomically.
    """
    token_hash = _hash_token(raw_token)

    token_record = await PasswordResetRepository.get_valid_by_hash(
        session, token_hash
    )
    if token_record is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired.",
        )

    user = await UserRepository.get_by_id(session, token_record.user_id)
    if user is None:
        # User was deleted after token creation — treat as invalid token.
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This reset link is invalid or has expired.",
        )

    # Update password using the same bcrypt mechanism as registration.
    user.hashed_password = hash_password(new_password)
    session.add(user)

    # Invalidate ALL active tokens for this user (including the one just used).
    # This covers both the normal case and any parallel reset requests.
    await PasswordResetRepository.invalidate_active_tokens_for_user(
        session, user.id
    )

    await session.commit()
