"""Pydantic response schemas for the Pet Data API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class AnimalResponse(BaseModel):
    """Animal summary for list views."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    aka: str | None = None
    breed: str | None = None
    weight_lbs: float | None = None
    birth_date: str | None = None
    intake_date: str | None = None
    location: str | None = None
    color_category: str | None = None
    behavior_mod_tags: list[str] | None = None
    is_in_kennel: bool | None = None
    is_foster_care: bool | None = None
    photo_url: str | None = None
    public_profile_url: str | None = None
    age_years: float | None = None
    days_in_shelter: int | None = None
    is_adoptable: bool | None = None


class VolunteerNoteResponse(BaseModel):
    """Volunteer behavioral observation."""

    model_config = ConfigDict(frozen=True)

    id: int | None = None
    animal_id: str
    volunteer_name: str
    note_date: str
    note_text: str | None = None
    rating_strong_on_leash: int | None = None
    rating_leash_reactivity: int | None = None
    rating_shy_fearful: int | None = None
    rating_jumpy_mouthy: int | None = None


class KennelCardResponse(BaseModel):
    """Kennel card information."""

    model_config = ConfigDict(frozen=True)

    id: int | None = None
    animal_id: str
    about_text: str | None = None
    dogs_compatibility: str | None = None
    cats_compatibility: str | None = None
    kids_compatibility: str | None = None
    commands_known: str | None = None
    housebreaking_status: str | None = None
    things_likes: str | None = None
    things_dislikes: str | None = None


class StaffAssessmentResponse(BaseModel):
    """Staff behavioral assessment."""

    model_config = ConfigDict(frozen=True)

    id: int | None = None
    animal_id: str
    assessment_tags: list[str] | None = None
    notes: str | None = None
    recorded_at: str | None = None


class AnimalListResponse(BaseModel):
    """Paginated animal list."""

    model_config = ConfigDict(frozen=True)

    animals: list[AnimalResponse]
    count: int


class AnimalDetailResponse(BaseModel):
    """Full animal detail with related data."""

    model_config = ConfigDict(frozen=True)

    animal: AnimalResponse
    kennel_card: KennelCardResponse | None = None
    volunteer_notes: list[VolunteerNoteResponse]
    staff_assessments: list[StaffAssessmentResponse]
