"""ORM model registry.

Import all models here so that SQLAlchemy's metadata is fully populated
before Alembic or any table-creation call runs.
"""

from models.model_card import ModelCard, ModelCardVersion
from models.user import User

__all__ = ["ModelCard", "ModelCardVersion", "User"]
