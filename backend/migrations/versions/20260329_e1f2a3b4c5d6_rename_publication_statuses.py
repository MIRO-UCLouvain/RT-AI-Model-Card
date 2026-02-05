"""rename_publication_statuses

Rename publication_status values to match the explicit state machine:
  pending  → in_review
  approved → published

Revision ID: e1f2a3b4c5d6
Revises: f8a3e2c1d094
Create Date: 2026-03-29 00:00:00.000000+00:00
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e1f2a3b4c5d6'
down_revision: Union[str, None] = 'f8a3e2c1d094'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("UPDATE model_card SET publication_status = 'in_review' WHERE publication_status = 'pending'")
    op.execute("UPDATE model_card SET publication_status = 'published' WHERE publication_status = 'approved'")


def downgrade() -> None:
    op.execute("UPDATE model_card SET publication_status = 'pending' WHERE publication_status = 'in_review'")
    op.execute("UPDATE model_card SET publication_status = 'approved' WHERE publication_status = 'published'")
