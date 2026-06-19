"""Initial petdata schema: 7 tables, pgvector extension, inert RLS.

Revision ID: 001
Revises:
Create Date: 2026-06-19

Notes
-----
- The ``vector`` extension is enabled so the store is ready for embeddings; no
  embedding columns are added yet (#9 decision: extension only).
- Every tenant-owned table enables ROW LEVEL SECURITY and carries an inert
  tenant-isolation policy. The policy reads the tenant from the JWT claim via
  ``current_setting('request.jwt.claims', true)``; until #29 wires that claim it
  resolves to NULL, so the policy denies all rows to constrained roles. The
  table owner (migrations, tests) bypasses RLS, so local dev and CI on plain
  Postgres are unaffected.
- Index names are preserved from the SQLite schema so the time-decay analysis
  keeps both ``idx_volunteer_notes_animal_date`` and ``idx_volunteer_notes_date``.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Tenant-owned tables receiving ENABLE ROW LEVEL SECURITY + an inert policy.
_TENANT_TABLES = (
    "petdata_animals",
    "petdata_kennel_cards",
    "petdata_volunteer_notes",
    "petdata_staff_assessments",
    "petdata_walk_records",
    "petdata_animal_images",
    "petdata_sync_log",
)


def _enable_inert_rls(table: str) -> None:
    """Enable RLS and add the inert tenant-isolation policy for one table."""
    op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
    op.execute(
        f"CREATE POLICY {table}_tenant_isolation ON {table} "
        "USING (tenant_id = (current_setting('request.jwt.claims', true)::jsonb "
        "->> 'tenant_id')::uuid)"
    )


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # ── petdata_animals ───────────────────────────────────────────────────────
    op.create_table(
        "petdata_animals",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("aka", sa.String(), nullable=True),
        sa.Column("breed", sa.String(), nullable=True),
        sa.Column("weight_lbs", sa.Float(), nullable=True),
        sa.Column("birth_date", sa.Date(), nullable=True),
        sa.Column("intake_date", sa.Date(), nullable=True),
        sa.Column("location", sa.String(), nullable=True),
        sa.Column("color_category", sa.String(), nullable=True),
        sa.Column("behavior_mod_tags", JSONB(), nullable=True),
        sa.Column("is_in_kennel", sa.Boolean(), nullable=True),
        sa.Column("is_foster_care", sa.Boolean(), nullable=True),
        sa.Column("photo_url", sa.String(), nullable=True),
        sa.Column("public_profile_url", sa.String(), nullable=True),
        sa.Column("adalo_record_id", sa.String(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    )
    op.create_index("idx_animals_color_category", "petdata_animals", ["color_category"])
    op.create_index("idx_animals_last_synced", "petdata_animals", ["last_synced_at"])

    # ── petdata_kennel_cards ──────────────────────────────────────────────────
    op.create_table(
        "petdata_kennel_cards",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "animal_id",
            sa.String(),
            sa.ForeignKey("petdata_animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("about_text", sa.Text(), nullable=True),
        sa.Column("dogs_compatibility", sa.String(), nullable=True),
        sa.Column("dogs_compatibility_notes", sa.Text(), nullable=True),
        sa.Column("cats_compatibility", sa.String(), nullable=True),
        sa.Column("cats_compatibility_notes", sa.Text(), nullable=True),
        sa.Column("kids_compatibility", sa.String(), nullable=True),
        sa.Column("kids_compatibility_notes", sa.Text(), nullable=True),
        sa.Column("commands_known", sa.Text(), nullable=True),
        sa.Column("housebreaking_status", sa.String(), nullable=True),
        sa.Column("things_likes", sa.Text(), nullable=True),
        sa.Column("things_dislikes", sa.Text(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.UniqueConstraint("animal_id", name="uq_kennel_cards_animal"),
    )
    op.create_index("idx_kennel_cards_animal", "petdata_kennel_cards", ["animal_id"])

    # ── petdata_volunteer_notes ───────────────────────────────────────────────
    op.create_table(
        "petdata_volunteer_notes",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "animal_id",
            sa.String(),
            sa.ForeignKey("petdata_animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("adalo_record_id", sa.String(), nullable=True, unique=True),
        sa.Column("volunteer_name", sa.String(), nullable=False),
        sa.Column("note_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("note_text", sa.Text(), nullable=True),
        sa.Column("rating_strong_on_leash", sa.Integer(), nullable=True),
        sa.Column("rating_leash_reactivity", sa.Integer(), nullable=True),
        sa.Column("rating_shy_fearful", sa.Integer(), nullable=True),
        sa.Column("rating_jumpy_mouthy", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
        sa.CheckConstraint(
            "rating_strong_on_leash BETWEEN 0 AND 5",
            name="ck_volunteer_notes_strong_on_leash",
        ),
        sa.CheckConstraint(
            "rating_leash_reactivity BETWEEN 0 AND 5",
            name="ck_volunteer_notes_leash_reactivity",
        ),
        sa.CheckConstraint(
            "rating_shy_fearful BETWEEN 0 AND 5",
            name="ck_volunteer_notes_shy_fearful",
        ),
        sa.CheckConstraint(
            "rating_jumpy_mouthy BETWEEN 0 AND 5",
            name="ck_volunteer_notes_jumpy_mouthy",
        ),
    )
    # Decay-critical indexes (descending recency).
    op.execute(
        "CREATE INDEX idx_volunteer_notes_animal_date "
        "ON petdata_volunteer_notes (animal_id, note_date DESC)"
    )
    op.execute(
        "CREATE INDEX idx_volunteer_notes_date "
        "ON petdata_volunteer_notes (note_date DESC)"
    )
    op.create_index(
        "idx_volunteer_notes_last_synced",
        "petdata_volunteer_notes",
        ["last_synced_at"],
    )

    # ── petdata_staff_assessments ─────────────────────────────────────────────
    op.create_table(
        "petdata_staff_assessments",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "animal_id",
            sa.String(),
            sa.ForeignKey("petdata_animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("assessment_tags", JSONB(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    )
    op.create_index(
        "idx_staff_assessments_animal",
        "petdata_staff_assessments",
        ["animal_id"],
    )

    # ── petdata_walk_records ──────────────────────────────────────────────────
    op.create_table(
        "petdata_walk_records",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "animal_id",
            sa.String(),
            sa.ForeignKey("petdata_animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("adalo_record_id", sa.String(), nullable=True, unique=True),
        sa.Column("volunteer_name", sa.String(), nullable=True),
        sa.Column("out_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column("in_time", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    )
    op.create_index("idx_walk_records_animal", "petdata_walk_records", ["animal_id"])

    # ── petdata_animal_images ─────────────────────────────────────────────────
    op.create_table(
        "petdata_animal_images",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "animal_id",
            sa.String(),
            sa.ForeignKey("petdata_animals.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("image_url", sa.String(), nullable=False),
        sa.Column("display_order", sa.Integer(), nullable=True),
        sa.Column("last_synced_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    )
    op.create_index("idx_animal_images_animal", "petdata_animal_images", ["animal_id"])

    # ── petdata_sync_log ──────────────────────────────────────────────────────
    op.create_table(
        "petdata_sync_log",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("sync_type", sa.String(), nullable=False),
        sa.Column("table_name", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "records_processed",
            sa.Integer(),
            nullable=False,
            server_default=sa.text("0"),
        ),
        sa.Column(
            "records_created", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "records_updated", sa.Integer(), nullable=False, server_default=sa.text("0")
        ),
        sa.Column(
            "status", sa.String(), nullable=False, server_default=sa.text("'running'")
        ),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("tenant_id", UUID(as_uuid=True), nullable=False),
    )
    op.execute(
        "CREATE INDEX idx_sync_log_status "
        "ON petdata_sync_log (status, started_at DESC)"
    )

    for table in _TENANT_TABLES:
        _enable_inert_rls(table)


def downgrade() -> None:
    # Drop children before the parent so the FK cascade is satisfied; policies
    # drop with their tables. The vector extension is left in place.
    op.drop_table("petdata_sync_log")
    op.drop_table("petdata_animal_images")
    op.drop_table("petdata_walk_records")
    op.drop_table("petdata_staff_assessments")
    op.drop_table("petdata_volunteer_notes")
    op.drop_table("petdata_kennel_cards")
    op.drop_table("petdata_animals")
