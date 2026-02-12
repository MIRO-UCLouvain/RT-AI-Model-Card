"""add_rejection_feedback_to_version

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-12 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'model_card_version',
        sa.Column(
            'rejection_feedback',
            sa.String(2000),
            nullable=True,
        ),
    )


def downgrade() -> None:
    op.drop_column('model_card_version', 'rejection_feedback')
