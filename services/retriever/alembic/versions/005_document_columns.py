"""Add file_size_bytes, description, uploaded_by, file_type to documents.

Revision ID: 005
Revises: 004
Create Date: 2026-03-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision: str = "005"
down_revision: str | None = "004"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "documents",
        sa.Column(
            "file_size_bytes",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
    )
    op.add_column(
        "documents",
        sa.Column("description", sa.Text(), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column("uploaded_by", UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "documents",
        sa.Column(
            "file_type",
            sa.String(100),
            nullable=False,
            server_default=sa.text("'text/plain'"),
        ),
    )


def downgrade() -> None:
    op.drop_column("documents", "file_type")
    op.drop_column("documents", "uploaded_by")
    op.drop_column("documents", "description")
    op.drop_column("documents", "file_size_bytes")
