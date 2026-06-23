"""Semantic cache table backed by pgvector.

Revision ID: 003
Revises: 002
Create Date: 2026-03-13
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy.dialects.postgresql import JSONB, UUID

revision: str = "003"
down_revision: str | None = "002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.create_table(
        "semantic_cache",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("query_embedding", Vector(_EMBEDDING_DIM), nullable=False),
        sa.Column("answer", sa.Text(), nullable=False),
        sa.Column("sources", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    op.execute(
        "CREATE INDEX ix_semantic_cache_embedding_hnsw "
        "ON semantic_cache USING hnsw (query_embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    op.create_index("ix_semantic_cache_tenant", "semantic_cache", ["tenant_id"])
    op.execute("ALTER TABLE semantic_cache ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS semantic_cache")
