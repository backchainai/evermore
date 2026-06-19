"""Data models for petdata database entities."""

from __future__ import annotations

import json
from datetime import date, datetime

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

    Usage: Mutable models for repository pattern.
      1. Fetch:  animal = db.get_animal(id)
      2. Modify: animal.weight_lbs = 70.0
      3. Persist: db.update_animal(animal)

    Note: Mutations outside repository methods may cause data inconsistency.
    Always use repository update methods to persist changes.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: str  # A-55833 format
    name: str
    aka: str | None = None
    breed: str | None = None
    weight_lbs: float | None = None
    birth_date: str | None = None  # ISO format date
    intake_date: str | None = None  # ISO format date
    location: str | None = None
    color_category: str | None = None  # Green/Yellow/Orange/Senior/Designated
    behavior_mod_tags: list[str] | None = None
    is_in_kennel: bool | None = None
    is_foster_care: bool | None = None
    photo_url: str | None = None
    public_profile_url: str | None = None
    adalo_record_id: str | None = None
    created_at: str | None = None
    updated_at: str | None = None
    last_synced_at: str | None = None

    @field_validator("behavior_mod_tags", mode="before")
    @classmethod
    def parse_behavior_mod_tags(cls, v: str | list[str] | None) -> list[str] | None:
        """Parse JSON string to list[str], or pass through if already parsed."""
        return _parse_json_tags(v)

    @field_serializer("behavior_mod_tags", when_used="json")
    def serialize_behavior_mod_tags(self, v: list[str] | None) -> str | None:
        """Serialize list[str] back to JSON string for database storage."""
        return _serialize_json_tags(v)

    @field_validator("is_in_kennel", "is_foster_care", mode="before")
    @classmethod
    def validate_sqlite_bool(cls, v: int | bool | None) -> bool | None:
        """Convert SQLite integer (0/1) to bool, preserving None."""
        if v is None:
            return None
        if isinstance(v, bool):
            return v  # Already boolean (direct instantiation)
        return bool(v)  # Convert 0/1 to False/True

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
    def days_in_shelter(self) -> int | None:
        """Calculate days in shelter from intake_date.

        Returns:
            Number of days in shelter, or None if intake_date is not set or
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


class KennelCard(BaseModel):
    """Structured kennel card information.

    Usage: Mutable models for repository pattern.
    Fetch, modify, persist via repository update methods.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    about_text: str | None = None
    dogs_compatibility: str | None = None  # Unknown/Good/Bad
    dogs_compatibility_notes: str | None = None
    cats_compatibility: str | None = None
    cats_compatibility_notes: str | None = None
    kids_compatibility: str | None = None
    kids_compatibility_notes: str | None = None
    commands_known: str | None = None
    housebreaking_status: str | None = None
    things_likes: str | None = None
    things_dislikes: str | None = None
    last_synced_at: str | None = None


class VolunteerNote(BaseModel):
    """Volunteer behavioral observation with ratings.

    Critical for time-decay analysis - timestamps enable weighting recent observations.

    Usage: Mutable models for repository pattern.
    Fetch, modify, persist via repository update methods.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    adalo_record_id: str | None = None
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

    Usage: Mutable models for repository pattern.
    Fetch, modify, persist via repository update methods.
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

    Usage: Mutable models for repository pattern.
    Fetch, modify, persist via repository update methods.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    id: int | None = None
    animal_id: str = ""
    adalo_record_id: str | None = None
    volunteer_name: str | None = None
    out_time: str | None = None
    in_time: str | None = None
    created_at: str | None = None


class AnimalImage(BaseModel):
    """Animal photo URL reference.

    Usage: Mutable models for repository pattern.
    Fetch, modify, persist via repository update methods.
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

    Usage: Mutable models for repository pattern.
    Fetch, modify, persist via repository update methods.
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
