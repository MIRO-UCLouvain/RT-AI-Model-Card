"""add_name_fields_to_user

Revision ID: c8e2f1a3b490
Revises: dfd4d38319af
Create Date: 2026-03-23 10:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c8e2f1a3b490'
down_revision: Union[str, None] = 'dfd4d38319af'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('user', sa.Column('first_name', sa.String(length=100), nullable=True))
    op.add_column('user', sa.Column('last_name', sa.String(length=100), nullable=True))


def downgrade() -> None:
    op.drop_column('user', 'last_name')
    op.drop_column('user', 'first_name')
