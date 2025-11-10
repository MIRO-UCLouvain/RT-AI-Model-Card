"""Shared SQLAlchemy base and reusable mixins for all ORM models."""

from datetime import datetime

from sqlalchemy import DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models. Shares the same metadata registry."""


class TimestampMixin:
    """Adds created_at / updated_at columns to any model that inherits it.

    Both columns are managed automatically by the database server,
    so application code never needs to set them explicitly.
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
