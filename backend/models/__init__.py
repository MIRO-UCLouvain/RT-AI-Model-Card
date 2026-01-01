"""ORM model registry.

Import all models here so that SQLAlchemy's metadata is fully populated
before Alembic or any table-creation call runs.
"""

from models.model_card import ModelCard, ModelCardVersion
from models.password_reset_token import PasswordResetToken
from models.user import User

__all__ = ["ModelCard", "ModelCardVersion", "PasswordResetToken", "User"]
