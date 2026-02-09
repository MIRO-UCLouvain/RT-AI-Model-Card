"""user_defined_version_numbers

Change model_card_version.version_number from INTEGER to VARCHAR(50) so that
user-defined version strings (e.g. "v1.0", "2.1") can be stored directly.
Existing integer values (1, 2, 3 …) are preserved as their string equivalents.

Revision ID: a7b8c9d0e1f2
Revises: e1f2a3b4c5d6
Create Date: 2026-03-29 00:00:00.000000+00:00
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'a7b8c9d0e1f2'
down_revision: Union[str, None] = 'e1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # MySQL cannot drop an index that is the sole backing index for a FK.
    # Drop the FK first, then the unique index, alter the column, and restore both.
    op.drop_constraint(
        'model_card_version_ibfk_1', 'model_card_version', type_='foreignkey'
    )
    op.drop_constraint('uq_card_version', 'model_card_version', type_='unique')

    # Convert INTEGER → VARCHAR(50).
    # MySQL converts existing integer values to their string representation.
    op.alter_column(
        'model_card_version',
        'version_number',
        existing_type=sa.Integer(),
        type_=sa.String(50),
        existing_nullable=False,
    )

    # Recreate the unique constraint on the new string column.
    op.create_unique_constraint(
        'uq_card_version',
        'model_card_version',
        ['model_card_id', 'version_number'],
    )
    # Restore the foreign key (uq_card_version now backs it again).
    op.create_foreign_key(
        'model_card_version_ibfk_1',
        'model_card_version',
        'model_card',
        ['model_card_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    op.drop_constraint(
        'model_card_version_ibfk_1', 'model_card_version', type_='foreignkey'
    )
    op.drop_constraint('uq_card_version', 'model_card_version', type_='unique')

    op.alter_column(
        'model_card_version',
        'version_number',
        existing_type=sa.String(50),
        type_=sa.Integer(),
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
