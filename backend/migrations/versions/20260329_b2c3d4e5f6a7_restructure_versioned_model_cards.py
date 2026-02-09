"""restructure_versioned_model_cards

Move publication status from ModelCard to ModelCardVersion so each version
owns its own lifecycle.  Also rename columns and add created_by.

Changes to model_card_version:
  - Rename version_number  → version  (VARCHAR 50, unique per card)
  - Rename content_json    → content
  - Add    status          VARCHAR(20) DEFAULT 'draft'
  - Add    created_by      UUID NULL FK → user.id
  - Drop   is_latest

Changes to model_card:
  - Drop   publication_status
  - Drop   is_public

Data migration:
  - Copy each card's publication_status into all of its versions' status
    (keeps existing data consistent; all versions of a card inherit the
    card-level status that was in place before this migration).

Revision ID: b2c3d4e5f6a7
Revises: a7b8c9d0e1f2
Create Date: 2026-03-29 00:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── model_card_version ────────────────────────────────────────────────────

    # 1. MySQL won't drop an index that backs a FK — drop FK first.
    op.drop_constraint(
        'model_card_version_ibfk_1', 'model_card_version', type_='foreignkey'
    )
    op.drop_constraint('uq_card_version', 'model_card_version', type_='unique')

    # 2. Rename version_number → version (already VARCHAR 50 from prev migration).
    op.alter_column(
        'model_card_version', 'version_number',
        new_column_name='version',
        existing_type=sa.String(50),
        existing_nullable=False,
    )

    # 3. Rename content_json → content.
    op.alter_column(
        'model_card_version', 'content_json',
        new_column_name='content',
        existing_type=sa.JSON(),
        existing_nullable=False,
    )

    # 4. Add status column (initially nullable so we can back-fill).
    op.add_column(
        'model_card_version',
        sa.Column('status', sa.String(20), nullable=True),
    )

    # 5. Back-fill: copy each card's publication_status into its versions.
    op.execute(
        """
        UPDATE model_card_version mcv
        JOIN   model_card mc ON mc.id = mcv.model_card_id
        SET    mcv.status = mc.publication_status
        """
    )

    # 6. Any version that still has NULL status gets 'draft'.
    op.execute(
        "UPDATE model_card_version SET status = 'draft' WHERE status IS NULL"
    )

    # 7. Now make status NOT NULL with server default.
    op.alter_column(
        'model_card_version', 'status',
        existing_type=sa.String(20),
        nullable=False,
        server_default='draft',
    )

    # 8. Add created_by column (nullable — existing rows have no creator recorded).
    #    Do NOT use an inline ForeignKey here — MySQL would auto-name the FK and
    #    collide with the name we restore later.  Create the FK explicitly instead.
    op.add_column(
        'model_card_version',
        sa.Column('created_by', sa.String(36), nullable=True),
    )
    op.create_foreign_key(
        'fk_mcv_created_by',
        'model_card_version',
        'user',
        ['created_by'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_index(
        'ix_model_card_version_created_by',
        'model_card_version',
        ['created_by'],
    )

    # 9. Drop is_latest — no longer needed; ordering by created_at is canonical.
    op.drop_column('model_card_version', 'is_latest')

    # 10. Recreate the unique constraint on the renamed column.
    op.create_unique_constraint(
        'uq_card_version',
        'model_card_version',
        ['model_card_id', 'version'],
    )
    # Restore the FK (now backed by the recreated uq_card_version index).
    op.create_foreign_key(
        'model_card_version_ibfk_1',
        'model_card_version',
        'model_card',
        ['model_card_id'],
        ['id'],
        ondelete='CASCADE',
    )

    # ── model_card ────────────────────────────────────────────────────────────

    # 11. Drop publication_status (now lives on versions).
    op.drop_column('model_card', 'publication_status')

    # 12. Drop is_public (never used functionally).
    op.drop_column('model_card', 'is_public')


def downgrade() -> None:
    # ── model_card ────────────────────────────────────────────────────────────

    op.add_column(
        'model_card',
        sa.Column(
            'is_public',
            sa.Boolean(),
            nullable=False,
            server_default='0',
        ),
    )
    op.add_column(
        'model_card',
        sa.Column(
            'publication_status',
            sa.String(20),
            nullable=False,
            server_default='draft',
        ),
    )

    # Restore card-level status from the latest version's status.
    op.execute(
        """
        UPDATE model_card mc
        JOIN (
            SELECT model_card_id, status
            FROM   model_card_version
            WHERE  created_at = (
                SELECT MAX(created_at)
                FROM   model_card_version mcv2
                WHERE  mcv2.model_card_id = model_card_version.model_card_id
            )
        ) latest ON latest.model_card_id = mc.id
        SET mc.publication_status = latest.status
        """
    )

    # ── model_card_version ────────────────────────────────────────────────────

    op.drop_constraint(
        'model_card_version_ibfk_1', 'model_card_version', type_='foreignkey'
    )
    op.drop_constraint('uq_card_version', 'model_card_version', type_='unique')
    op.drop_constraint('fk_mcv_created_by', 'model_card_version', type_='foreignkey')
    op.drop_index('ix_model_card_version_created_by', 'model_card_version')
    op.drop_column('model_card_version', 'created_by')
    op.drop_column('model_card_version', 'status')

    op.add_column(
        'model_card_version',
        sa.Column('is_latest', sa.Boolean(), nullable=False, server_default='1'),
    )

    op.alter_column(
        'model_card_version', 'content',
        new_column_name='content_json',
        existing_type=sa.JSON(),
        existing_nullable=False,
    )
    op.alter_column(
        'model_card_version', 'version',
        new_column_name='version_number',
        existing_type=sa.String(50),
        existing_nullable=False,
    )

    op.create_unique_constraint(
        'uq_card_version',
        'model_card_version',
        ['model_card_id', 'version_number'],
    )
    op.create_foreign_key(
        'model_card_version_ibfk_1',
        'model_card_version',
        'model_card',
        ['model_card_id'],
        ['id'],
        ondelete='CASCADE',
    )
