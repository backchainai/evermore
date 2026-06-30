"""Add a nullable species column to petdata_animals.

Revision ID: 002
Revises: 001
Create Date: 2026-06-30

Notes
-----
- Adds ``species`` (dog/cat) to ``petdata_animals`` so the Pet Data API can
  expose per-animal species. The column is nullable: existing rows predate the
  extraction mapping that populates it, and the SMS field is a placeholder until
  verified against real responses.
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "petdata_animals",
        sa.Column("species", sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("petdata_animals", "species")
