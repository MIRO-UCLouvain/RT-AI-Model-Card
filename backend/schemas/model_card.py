"""Pydantic schemas for model card API input/output validation."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


# ── Version schemas ───────────────────────────────────────────────────────────

class ModelCardVersionBase(BaseModel):
    """Fields shared between create and read version schemas."""

    title: str = Field(..., max_length=500, description="Human-readable title")
    content_json: dict = Field(..., description="Full model card content as JSON")


class ModelCardVersionCreate(ModelCardVersionBase):
    """Input schema for creating a new version."""


class ModelCardVersionRead(ModelCardVersionBase):
    """Output schema for a version record."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    model_card_id: int
    version_number: int
    is_latest: bool
    created_at: datetime


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
    is_public: bool
    created_at: datetime
    updated_at: datetime
    versions: list[ModelCardVersionRead]


class ModelCardSummary(ModelCardBase):
    """Lightweight output schema for listing model cards (no version content)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    is_public: bool
    created_at: datetime
    updated_at: datetime
