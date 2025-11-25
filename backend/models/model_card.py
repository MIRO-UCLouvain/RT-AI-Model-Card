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
    """Logical identity of a model card, independent of its content.

    Content is stored in :class:`ModelCardVersion`.  A model card can have
    many versions; the active snapshot is the one where ``is_latest=True``.

    ``publication_status`` drives the moderation workflow:
    draft → pending → approved | rejected.
    """

    __tablename__ = "model_card"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    task_type: Mapped[str] = mapped_column(String(100), nullable=False)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Moderation workflow
    publication_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        server_default="draft",
    )

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
        order_by="ModelCardVersion.version_number",
    )

    def __repr__(self) -> str:
        return f"<ModelCard id={self.id} slug={self.slug!r}>"


class ModelCardVersion(Base, TimestampMixin):
    """Immutable snapshot of a model card at a specific version.

    ``content_json`` stores the full model card dict as a MySQL JSON column.
    ``title`` is denormalised from the JSON payload to allow fast listing
    without deserialising the full document.

    ``version_number`` starts at 1 and is incremented by the service layer
    on each new save.  ``is_latest`` is flipped to ``False`` on the previous
    version whenever a new version is created.
    """

    __tablename__ = "model_card_version"
    __table_args__ = (
        UniqueConstraint("model_card_id", "version_number", name="uq_card_version"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    model_card_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("model_card.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    content_json: Mapped[dict] = mapped_column(JSON, nullable=False)
    is_latest: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    model_card: Mapped["ModelCard"] = relationship(
        "ModelCard",
        back_populates="versions",
    )

    def __repr__(self) -> str:
        return (
            f"<ModelCardVersion id={self.id} "
            f"card_id={self.model_card_id} v={self.version_number}>"
        )
