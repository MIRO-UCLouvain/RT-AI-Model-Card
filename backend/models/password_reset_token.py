"""PasswordResetToken ORM model.

Security design:
- Only the SHA-256 hash of the raw token is persisted here.
- The raw token travels only in the reset URL emailed to the user.
- ``used_at`` is a timestamp rather than a boolean so that forensic queries
  can show exactly when a token was consumed.
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.types import Uuid

from models.base import Base


class PasswordResetToken(Base):
    """One-time, short-lived password reset token.

    Primary key is an auto-increment integer; the lookup key for the reset
    flow is ``token_hash`` (indexed unique).
    """

    __tablename__ = "password_reset_token"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)

    # FK to user — cascade delete so orphan rows are cleaned up automatically.
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("user.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # SHA-256 hex digest (64 chars) of the raw token that was emailed.
    token_hash: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
    )

    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # NULL = token not yet used; non-NULL = consumed timestamp.
    used_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        default=None,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
