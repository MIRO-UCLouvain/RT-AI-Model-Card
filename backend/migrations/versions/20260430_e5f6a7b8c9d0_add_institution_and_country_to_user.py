"""add_institution_and_country_to_user

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-04-30 00:00:00.000000+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'user',
        sa.Column('institution', sa.String(255), nullable=True),
    )
    op.add_column(
        'user',
        sa.Column('country', sa.String(100), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('user', 'country')
    op.drop_column('user', 'institution')
