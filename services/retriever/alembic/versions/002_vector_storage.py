"""Vector storage: pgvector extension + document_chunks table.

Revision ID: 002
Revises: 001
Create Date: 2026-03-13

Indexes
-------
- HNSW (m=16, ef_construction=64) on embedding using vector_cosine_ops
- GIN on to_tsvector('english', content) for hybrid BM25 retrieval
- Composite (tenant_id, document_id) for tenant-scoped deletes
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from pgvector.sqlalchemy import Vector  # type: ignore[import-untyped]
from sqlalchemy.dialects.postgresql import UUID

revision: str = "002"
down_revision: str | None = "001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_EMBEDDING_DIM = 1536


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "document_chunks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("document_id", UUID(as_uuid=True), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(_EMBEDDING_DIM), nullable=False),
        sa.Column("source", sa.Text(), nullable=False, server_default=""),
        sa.Column("title", sa.Text(), nullable=False, server_default=""),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )

    # HNSW index for cosine similarity search
    op.execute(
        "CREATE INDEX ix_document_chunks_embedding_hnsw "
        "ON document_chunks USING hnsw (embedding vector_cosine_ops) "
        "WITH (m = 16, ef_construction = 64)"
    )
    # GIN index for full-text search (hybrid retrieval)
    op.execute(
        "CREATE INDEX ix_document_chunks_content_tsv "
        "ON document_chunks USING gin (to_tsvector('english', content))"
    )
    op.create_index(
        "ix_document_chunks_tenant_doc",
        "document_chunks",
        ["tenant_id", "document_id"],
    )
    op.execute("ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS document_chunks")
    # Leave the vector extension — other tables may use it.
