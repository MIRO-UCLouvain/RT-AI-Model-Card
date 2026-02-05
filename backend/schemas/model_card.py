"""Pydantic schemas for model card API input/output validation."""

import enum
import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class PublicationStatus(str, enum.Enum):
    """Valid states for a model card version's moderation lifecycle.

    State machine (per version):
        draft ──submit──▶ in_review ──approve──▶ published
          ▲                   └──────reject────▶ rejected
          └──────────────────────────────────────────┘
    """

    DRAFT = "draft"
    IN_REVIEW = "in_review"
    PUBLISHED = "published"
    REJECTED = "rejected"


# ── Version schemas ───────────────────────────────────────────────────────────

class ModelCardVersionBase(BaseModel):
    """Fields shared between create and read version schemas."""

    title: str = Field(..., max_length=500, description="Human-readable title")
    content: dict = Field(..., description="Full model card content as JSON")


class ModelCardVersionCreate(ModelCardVersionBase):
    """Input schema for creating a new version."""

    user_version: str = Field(
        ...,
        max_length=50,
        description=(
            "User-defined version string from the card form, e.g. 'v1.0', '2.1'. "
            "Must be unique within the same model card."
        ),
    )


class ModelCardVersionRead(ModelCardVersionBase):
    """Output schema for a version record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    model_card_id: int
    version: str
    status: PublicationStatus
    created_at: datetime
    created_by: uuid.UUID | None


# ── ModelCard schemas ─────────────────────────────────────────────────────────

class ModelCardBase(BaseModel):
    """Fields shared between create and read model card schemas."""

    slug: str = Field(
        ...,
        max_length=255,
        pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$",
        description="URL-safe identifier, e.g. my-segmentation-model",
    )
    task_type: str = Field(
        ...,
        max_length=100,
        description="One of the 4 RT task types",
    )


class ModelCardCreate(ModelCardBase):
    """Input schema for creating a new model card with its first version."""

    first_version: ModelCardVersionCreate


class ModelCardRead(ModelCardBase):
    """Output schema for a model card with its full version history."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    versions: list[ModelCardVersionRead]


class ModelCardSummary(ModelCardBase):
    """Lightweight output schema for listing model cards (no version content)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime


# ── Diff schemas ─────────────────────────────────────────────────────────────

class FieldAdded(BaseModel):
    """A field that exists in the new version but not the old."""
    field: str
    value: Any = None


class FieldRemoved(BaseModel):
    """A field that existed in the old version but not the new."""
    field: str
    value: Any = None


class FieldChanged(BaseModel):
    """A field that exists in both versions but whose value changed."""
    field: str
    old: Any = None
    new: Any = None


class SectionDiff(BaseModel):
    """Diff result for one section of a model card."""
    added: list[FieldAdded] = []
    removed: list[FieldRemoved] = []
    changed: list[FieldChanged] = []


class DiffResponse(BaseModel):
    """Full diff between two versions of a model card."""
    old_version_id: int
    new_version_id: int
    old_version: str
    new_version: str
    sections: dict[str, SectionDiff]

    @property
    def has_changes(self) -> bool:
        return bool(self.sections)


# ── Public catalogue schema ───────────────────────────────────────────────────

class PublishedVersionSummary(BaseModel):
    """Flattened summary of a published version for the public catalogue.

    Combines version fields with its parent card's stable identifiers so the
    UI has everything it needs in a single object.
    """

    id: int               # version id
    card_id: int
    slug: str
    task_type: str
    version: str
    status: PublicationStatus
    created_at: datetime

    @classmethod
    def from_version(cls, v: object) -> "PublishedVersionSummary":
        return cls(
            id=v.id,  # type: ignore[attr-defined]
            card_id=v.model_card_id,  # type: ignore[attr-defined]
            slug=v.model_card.slug,  # type: ignore[attr-defined]
            task_type=v.model_card.task_type,  # type: ignore[attr-defined]
            version=v.version,  # type: ignore[attr-defined]
            status=v.status,  # type: ignore[attr-defined]
            created_at=v.created_at,  # type: ignore[attr-defined]
        )
