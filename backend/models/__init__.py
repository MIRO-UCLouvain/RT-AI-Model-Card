"""ORM model registry.

Import all models here so that SQLAlchemy's metadata is fully populated
before Alembic or any table-creation call runs.
"""

from models.model_card import ModelCard, ModelCardVersion

__all__ = ["ModelCard", "ModelCardVersion"]
