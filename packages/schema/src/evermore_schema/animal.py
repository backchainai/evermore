# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Canonical Animal Record contracts for the Evermore data spine.

These are the normalized domain models for one animal: the core ``Animal``
record plus its related evidence (behavior profile, volunteer notes, staff
assessments, walk records, images) and the ``SyncLog`` that tracks extraction.
The composite ``AnimalRecord`` aggregates one animal with all of its evidence.

Per the vision doc, the Animal Record is the "canonical normalized data for one
animal (demographics, history, behavior observations, medical)" and is owned by
PetData.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator


def _parse_json_tags(v: str | list[str] | None) -> list[str] | None:
    """Parse JSON string to list[str], or pass through if already parsed.

    Args:
        v: Input value (JSON string, list, or None)

    Returns:
        Parsed list of strings, or None

    Raises:
        ValueError: If JSON is invalid or not an array
    """
    if v is None:
        return None
    if isinstance(v, list):
        return v  # Already parsed (direct instantiation)
    if isinstance(v, str):
        if v.strip() == "":
            return None
        if len(v) > 10000:  # 10KB limit for tag arrays
            raise ValueError("JSON array exceeds maximum size (10KB)")
        try:
            parsed = json.loads(v)
            if not isinstance(parsed, list):
                raise ValueError(f"Expected JSON array, got {type(parsed).__name__}")
            return [str(item) for item in parsed]  # Coerce to strings
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}") from e
    raise ValueError(f"Expected str or list, got {type(v).__name__}")


def _serialize_json_tags(v: list[str] | None) -> str | None:
    """Serialize list[str] back to JSON string for database storage."""
    return None if v is None else json.dumps(v)


class Animal(BaseModel):
    """Core animal record from a shelter management system (SMS).

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: str  # A-00000 format
    name: str
    aka: str | None = None
    breed: str | None = None
    species: str | None = None  # dog/cat
    weight_lbs: float | None = None
    birth_date: str | None = None  # ISO format date
    intake_date: str | None = None  # ISO format date
    location: str | None = None
    color_category: str | None = None  # Green/Yellow/Orange/Senior/Designated
    custody_location: Literal["kennel", "foster"] | None = None
    photo_url: str | None = None
    public_profile_url: str | None = None
    source_record_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_synced_at: str | None = None

    @property
    def age_years(self) -> float | None:
        """Calculate age in years from birth_date.

        Returns:
            Age in years (float), or None if birth_date is not set or in the future
        """
        if not self.birth_date:
            return None
        try:
            birth = datetime.fromisoformat(self.birth_date).date()
            today = date.today()
            if birth > today:
                return None  # Future birth date is invalid
            age_days = (today - birth).days
            return round(age_days / 365.25, 1)  # Account for leap years
        except ValueError, AttributeError:
            return None

    @property
    def days_in_custody(self) -> int | None:
        """Calculate days in custody from intake_date.

        Returns:
            Number of days in custody, or None if intake_date is not set or
            in the future
        """
        if not self.intake_date:
            return None
        try:
            intake = datetime.fromisoformat(self.intake_date).date()
            today = date.today()
            if intake > today:
                return None  # Future intake date is invalid
            return (today - intake).days
        except ValueError, AttributeError:
            return None

    @property
    def is_adoptable(self) -> bool | None:
        """Determine adoptability based on color_category.

        Green/Yellow/Orange animals are adoptable (case-insensitive).
        Senior/Designated animals are not adoptable.

        Returns:
            True if adoptable, False if not adoptable or unknown category,
            None if category not set
        """
        if not self.color_category:
            return None

        adoptable_categories = {"green", "yellow", "orange"}
        return self.color_category.lower() in adoptable_categories


class BehaviorProfile(BaseModel):
    """The animal's behavior, social, and preferences profile.

    Source-of-truth structured record of how one animal behaves and what it
    prefers: species/kids compatibility, known commands, housebreaking status,
    and likes/dislikes. It is attached to exactly one animal and is source
    data, not a generated public document (that belongs to the Composition
    layer).

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    dogs_compatible: bool | None = None
    dogs_compatibility_notes: str | None = None
    cats_compatible: bool | None = None
    cats_compatibility_notes: str | None = None
    kids_compatible: bool | None = None
    kids_compatibility_notes: str | None = None
    knows_commands: bool | None = None
    commands_notes: str | None = None
    housebroken: bool | None = None
    housebreaking_notes: str | None = None
    behavior_mod_tags: list[str] | None = None
    things_likes: list[str] | None = None
    things_dislikes: list[str] | None = None
    last_synced_at: str | None = None

    @field_validator(
        "things_likes", "things_dislikes", "behavior_mod_tags", mode="before"
    )
    @classmethod
    def parse_preference_tags(cls, v: str | list[str] | None) -> list[str] | None:
        """Parse JSON string to list[str], or pass through if already parsed."""
        return _parse_json_tags(v)

    @field_serializer(
        "things_likes", "things_dislikes", "behavior_mod_tags", when_used="json"
    )
    def serialize_preference_tags(self, v: list[str] | None) -> str | None:
        """Serialize list[str] back to JSON string for database storage."""
        return _serialize_json_tags(v)


class VolunteerNote(BaseModel):
    """Volunteer behavioral observation with ratings.

    Critical for time-decay analysis - timestamps enable weighting recent observations.

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    source_record_id: str | None = None
    volunteer_name: str = ""
    note_date: str = ""  # ISO format timestamp
    note_text: str | None = None
    rating_strong_on_leash: int | None = Field(default=None, ge=0, le=5)
    rating_leash_reactivity: int | None = Field(default=None, ge=0, le=5)
    rating_shy_fearful: int | None = Field(default=None, ge=0, le=5)
    rating_jumpy_mouthy: int | None = Field(default=None, ge=0, le=5)
    created_at: str | None = None
    last_synced_at: str | None = None


class StaffAssessment(BaseModel):
    """Staff behavioral assessment with structured tags.

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    assessment_tags: list[str] | None = None
    notes: str | None = None
    recorded_at: str | None = None
    last_synced_at: str | None = None

    @field_validator("assessment_tags", mode="before")
    @classmethod
    def parse_assessment_tags(cls, v: str | list[str] | None) -> list[str] | None:
        """Parse JSON string to list[str], or pass through if already parsed."""
        return _parse_json_tags(v)

    @field_serializer("assessment_tags", when_used="json")
    def serialize_assessment_tags(self, v: list[str] | None) -> str | None:
        """Serialize list[str] back to JSON string for database storage."""
        return _serialize_json_tags(v)


class WalkRecord(BaseModel):
    """Walk check-in/check-out record.

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    source_record_id: str | None = None
    volunteer_name: str | None = None
    out_time: str | None = None
    in_time: str | None = None
    created_at: str | None = None


class AnimalImage(BaseModel):
    """Animal photo URL reference.

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).

    Planned: an animal will support multiple images with one designated the
    Primary ("hero") image. That field is not modeled yet.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    image_url: str = ""
    display_order: int | None = None
    last_synced_at: str | None = None


class SyncLog(BaseModel):
    """Sync operation tracking for extraction.

    Mutable domain model with pydantic ``validate_assignment=True``: fetch it,
    mutate attributes, and persist through the repository (validation runs on
    assignment).
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    sync_type: str = ""  # full/incremental
    table_name: str = ""
    started_at: str = ""
    completed_at: str | None = None
    records_processed: int = 0
    records_created: int = 0
    records_updated: int = 0
    status: str = "running"  # running/completed/failed
    error_message: str | None = None

    @field_validator(
        "records_processed", "records_created", "records_updated", mode="before"
    )
    @classmethod
    def default_counter_fields(cls, v: int | None) -> int:
        """Convert None to 0 for counter fields."""
        return v if v is not None else 0


class AnimalRecord(BaseModel):
    """Composite Animal Record: one animal with all of its related evidence.

    Aggregates the canonical ``Animal`` with the behavior profile, volunteer
    notes, staff assessments, walk records, and images that describe it. This is
    the normalized view PetData owns and the raw material a Package is curated
    from.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    animal: Animal
    behavior_profile: BehaviorProfile | None = None
    volunteer_notes: list[VolunteerNote] = Field(default_factory=list)
    staff_assessments: list[StaffAssessment] = Field(default_factory=list)
    walk_records: list[WalkRecord] = Field(default_factory=list)
    images: list[AnimalImage] = Field(default_factory=list)
