"""ORM models for model card persistence and versioning."""

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.types import Uuid

from models.base import Base, TimestampMixin

if TYPE_CHECKING:
    pass  # avoid circular imports when type checkers resolve forward refs


class ModelCard(Base, TimestampMixin):
    """Stable identity container for a model card.

    Content and status live in :class:`ModelCardVersion`.
    A card can accumulate many versions over time; each version is immutable
    once submitted for review.

    Workflow per version:
        draft ──submit──▶ in_review ──approve──▶ published
          ▲                   └──────reject────▶ rejected
          └──────────────────────────────────────────┘
    """

    __tablename__ = "model_card"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)

    # Ownership — nullable so cards created before auth was added still work.
    owner_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    versions: Mapped[list["ModelCardVersion"]] = relationship(
        "ModelCardVersion",
        back_populates="model_card",
        cascade="all, delete-orphan",
        order_by="ModelCardVersion.created_at",
    )

    def __repr__(self) -> str:
        return f"<ModelCard id={self.id} slug={self.slug!r}>"


class ModelCardVersion(Base, TimestampMixin):
    """Immutable snapshot of a model card at a specific user-defined version.

    ``content`` stores the full model card dict as a MySQL JSON column.
    ``title`` is denormalised from the JSON payload for fast listing.
    ``version`` is a user-defined string (e.g. "v1.0") taken from the
    ``card_metadata.version_number`` form field; unique per card.
    ``status`` owns the moderation lifecycle for this version.
    ``created_by`` records which user created this version.
    """

    __tablename__ = "model_card_version"
    __table_args__ = (
        UniqueConstraint("model_card_id", "version", name="uq_card_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_card.id", ondelete="CASCADE"), nullable=False
    )
    version: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content: Mapped[dict] = mapped_column(JSON, nullable=False)

    # Per-version moderation status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

    # Who created this version (nullable for rows pre-dating auth)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(native_uuid=False),
        ForeignKey("user.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    model_card: Mapped["ModelCard"] = relationship(
        "ModelCard",
        back_populates="versions",
    )

    def __repr__(self) -> str:
        return (
            f"<ModelCardVersion id={self.id} "
            f"card_id={self.model_card_id} v={self.version!r} status={self.status!r}>"
        )
