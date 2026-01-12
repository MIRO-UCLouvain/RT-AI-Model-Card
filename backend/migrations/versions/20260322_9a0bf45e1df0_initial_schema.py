"""initial_schema

Revision ID: 9a0bf45e1df0
Revises: 
Create Date: 2026-03-22 17:22:44.194920+00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9a0bf45e1df0'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'model_card',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('slug', sa.String(length=255), nullable=False),
        sa.Column('task_type', sa.String(length=100), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('slug'),
    )
    op.create_table(
        'model_card_version',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('model_card_id', sa.Integer(), nullable=False),
        sa.Column('version_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('content_json', sa.JSON(), nullable=False),
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['model_card_id'], ['model_card.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_card_id', 'version_number', name='uq_card_version'),
    )


def downgrade() -> None:
    op.drop_table('model_card_version')
    op.drop_table('model_card')
