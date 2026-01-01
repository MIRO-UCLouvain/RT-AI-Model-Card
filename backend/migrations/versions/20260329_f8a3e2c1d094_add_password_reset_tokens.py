"""add_password_reset_tokens

Revision ID: f8a3e2c1d094
Revises: c8e2f1a3b490
Create Date: 2026-03-29 10:00:00.000000+00:00

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'f8a3e2c1d094'
down_revision: Union[str, None] = 'c8e2f1a3b490'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'password_reset_token',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(native_uuid=False), nullable=False),
        sa.Column('token_hash', sa.String(length=64), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('used_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            'created_at',
            sa.DateTime(timezone=True),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['user_id'], ['user.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token_hash'),
    )
    op.create_index(
        op.f('ix_password_reset_token_user_id'),
        'password_reset_token',
        ['user_id'],
        unique=False,
    )
    op.create_index(
        op.f('ix_password_reset_token_token_hash'),
        'password_reset_token',
        ['token_hash'],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        op.f('ix_password_reset_token_token_hash'),
        table_name='password_reset_token',
    )
    op.drop_index(
        op.f('ix_password_reset_token_user_id'),
        table_name='password_reset_token',
    )
    op.drop_table('password_reset_token')
