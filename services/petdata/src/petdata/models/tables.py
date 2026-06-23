# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""SQLAlchemy 2.0 ORM models for the petdata store.

These are the persistence layer. The Pydantic models in
``petdata.modules.db.models`` remain the wire/domain contract; the helpers in
``petdata.models.mappers`` bridge the two.

Every table is namespaced with the ``petdata_`` prefix so it can share a single
Supabase Postgres instance with the other Evermore services without colliding.
Tenant-owned tables carry a ``tenant_id`` for row-level security; the policies
are created inert (see ``alembic/versions/001_initial_schema.py``) and activate
once the JWT tenant claim is wired in (#29).
"""

import datetime
import uuid

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from petdata.models.base import Base

# Default tenant UUID for the single-tenant MVP. RLS policies compare against
# the JWT tenant claim; until #29 sets that claim, rows written with this value
# remain visible only to the table owner (migrations, tests) and are inert for
# constrained roles.
DEFAULT_TENANT_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


def _tenant_column() -> Mapped[uuid.UUID]:
    """Standard tenant_id column shared by every tenant-owned table."""
    return mapped_column(
        UUID(as_uuid=True), nullable=False, default=lambda: DEFAULT_TENANT_ID
    )


class Animal(Base):
    """Core animal record extracted from a shelter management system (SMS)."""

    __tablename__ = "petdata_animals"
    __table_args__ = (
        Index("idx_animals_color_category", "color_category"),
        Index("idx_animals_last_synced", "last_synced_at"),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)  # e.g. "A-00000"
    name: Mapped[str] = mapped_column(String, nullable=False)
    aka: Mapped[str | None] = mapped_column(String, nullable=True)
    breed: Mapped[str | None] = mapped_column(String, nullable=True)
    weight_lbs: Mapped[float | None] = mapped_column(Float, nullable=True)
    birth_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    intake_date: Mapped[datetime.date | None] = mapped_column(Date, nullable=True)
    location: Mapped[str | None] = mapped_column(String, nullable=True)
    color_category: Mapped[str | None] = mapped_column(String, nullable=True)
    behavior_mod_tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    is_in_kennel: Mapped[bool | None] = mapped_column(nullable=True)
    is_foster_care: Mapped[bool | None] = mapped_column(nullable=True)
    photo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    public_profile_url: Mapped[str | None] = mapped_column(String, nullable=True)
    source_record_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=text("now()"),
        onupdate=func.now(),
    )
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


class KennelCard(Base):
    """Structured kennel-card information for one animal."""

    __tablename__ = "petdata_kennel_cards"
    __table_args__ = (
        UniqueConstraint("animal_id", name="uq_kennel_cards_animal"),
        Index("idx_kennel_cards_animal", "animal_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[str] = mapped_column(
        ForeignKey("petdata_animals.id", ondelete="CASCADE"), nullable=False
    )
    about_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    dogs_compatibility: Mapped[str | None] = mapped_column(String, nullable=True)
    dogs_compatibility_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cats_compatibility: Mapped[str | None] = mapped_column(String, nullable=True)
    cats_compatibility_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    kids_compatibility: Mapped[str | None] = mapped_column(String, nullable=True)
    kids_compatibility_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    commands_known: Mapped[str | None] = mapped_column(Text, nullable=True)
    housebreaking_status: Mapped[str | None] = mapped_column(String, nullable=True)
    things_likes: Mapped[str | None] = mapped_column(Text, nullable=True)
    things_dislikes: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


class VolunteerNote(Base):
    """Volunteer behavioral observation with ratings.

    Critical for time-decay analysis: the timestamps and the two indexes below
    let the decay algorithm weight recent observations.
    """

    __tablename__ = "petdata_volunteer_notes"
    __table_args__ = (
        CheckConstraint(
            "rating_strong_on_leash BETWEEN 0 AND 5",
            name="ck_volunteer_notes_strong_on_leash",
        ),
        CheckConstraint(
            "rating_leash_reactivity BETWEEN 0 AND 5",
            name="ck_volunteer_notes_leash_reactivity",
        ),
        CheckConstraint(
            "rating_shy_fearful BETWEEN 0 AND 5",
            name="ck_volunteer_notes_shy_fearful",
        ),
        CheckConstraint(
            "rating_jumpy_mouthy BETWEEN 0 AND 5",
            name="ck_volunteer_notes_jumpy_mouthy",
        ),
        # Decay-critical: per-animal recency and global recency.
        Index(
            "idx_volunteer_notes_animal_date",
            "animal_id",
            text("note_date DESC"),
        ),
        Index("idx_volunteer_notes_date", text("note_date DESC")),
        Index("idx_volunteer_notes_last_synced", "last_synced_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[str] = mapped_column(
        ForeignKey("petdata_animals.id", ondelete="CASCADE"), nullable=False
    )
    source_record_id: Mapped[str | None] = mapped_column(
        String, nullable=True, unique=True
    )
    volunteer_name: Mapped[str] = mapped_column(String, nullable=False)
    note_date: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    note_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    rating_strong_on_leash: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_leash_reactivity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_shy_fearful: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rating_jumpy_mouthy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


class StaffAssessment(Base):
    """Staff behavioral assessment with structured tags."""

    __tablename__ = "petdata_staff_assessments"
    __table_args__ = (Index("idx_staff_assessments_animal", "animal_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[str] = mapped_column(
        ForeignKey("petdata_animals.id", ondelete="CASCADE"), nullable=False
    )
    assessment_tags: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


class WalkRecord(Base):
    """Walk check-in / check-out record."""

    __tablename__ = "petdata_walk_records"
    __table_args__ = (Index("idx_walk_records_animal", "animal_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[str] = mapped_column(
        ForeignKey("petdata_animals.id", ondelete="CASCADE"), nullable=False
    )
    source_record_id: Mapped[str | None] = mapped_column(
        String, nullable=True, unique=True
    )
    volunteer_name: Mapped[str | None] = mapped_column(String, nullable=True)
    out_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    in_time: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=text("now()")
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


class AnimalImage(Base):
    """Animal photo URL reference."""

    __tablename__ = "petdata_animal_images"
    __table_args__ = (Index("idx_animal_images_animal", "animal_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[str] = mapped_column(
        ForeignKey("petdata_animals.id", ondelete="CASCADE"), nullable=False
    )
    image_url: Mapped[str] = mapped_column(String, nullable=False)
    display_order: Mapped[int | None] = mapped_column(Integer, nullable=True)
    last_synced_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


class SyncLog(Base):
    """Sync-operation tracking for extraction runs."""

    __tablename__ = "petdata_sync_log"
    __table_args__ = (Index("idx_sync_log_status", "status", text("started_at DESC")),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    sync_type: Mapped[str] = mapped_column(String, nullable=False)  # full/incremental
    table_name: Mapped[str] = mapped_column(String, nullable=False)
    started_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    completed_at: Mapped[datetime.datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    records_processed: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    records_created: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    records_updated: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default=text("0")
    )
    status: Mapped[str] = mapped_column(
        String, nullable=False, server_default=text("'running'")
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    tenant_id: Mapped[uuid.UUID] = _tenant_column()


#: Tables that carry a tenant_id and receive an inert RLS policy in migration 001.
TENANT_OWNED_TABLES = (
    Animal.__tablename__,
    KennelCard.__tablename__,
    VolunteerNote.__tablename__,
    StaffAssessment.__tablename__,
    WalkRecord.__tablename__,
    AnimalImage.__tablename__,
    SyncLog.__tablename__,
)
