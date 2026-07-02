"""FastAPI routes for Pet Data API.

Endpoints depend on the async repository (``get_repository``), which is bound to
a request-scoped SQLAlchemy session. The detail endpoint fetches related data
sequentially on that one session, which is not safe to share across concurrent
awaits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from petdata.modules.auth.dependencies import require_auth
from petdata.modules.db.models import Animal  # noqa: TC001
from petdata.modules.web.dependencies import get_repository
from petdata.modules.web.schemas import (
    AnimalDetailResponse,
    AnimalListResponse,
    AnimalResponse,
    BehaviorProfileResponse,
    StaffAssessmentResponse,
    VolunteerNoteResponse,
)

if TYPE_CHECKING:
    from petdata.modules.db import Database

router = APIRouter(tags=["animals"], dependencies=[Depends(require_auth)])


def _animal_to_response(animal: Animal) -> AnimalResponse:
    """Convert Animal model to API response with computed properties."""
    return AnimalResponse(
        id=animal.id,
        name=animal.name,
        aka=animal.aka,
        breed=animal.breed,
        species=animal.species,
        weight_lbs=animal.weight_lbs,
        birth_date=animal.birth_date,
        intake_date=animal.intake_date,
        location=animal.location,
        color_category=animal.color_category,
        custody_location=animal.custody_location,
        photo_url=animal.photo_url,
        public_profile_url=animal.public_profile_url,
        age_years=animal.age_years,
        days_in_custody=animal.days_in_custody,
        is_adoptable=animal.is_adoptable,
        synced_at=animal.last_synced_at,
    )


@router.get("/animals", response_model=AnimalListResponse)
async def list_animals(
    limit: int = 100,
    offset: int = 0,
    repo: Database = Depends(get_repository),  # noqa: B008
) -> AnimalListResponse:
    """List animals with pagination."""
    animals = await repo.list_animals(limit, offset)
    return AnimalListResponse(
        animals=[_animal_to_response(a) for a in animals],
        count=len(animals),
    )


@router.get("/animals/{animal_id}", response_model=AnimalDetailResponse)
async def get_animal(
    animal_id: str,
    repo: Database = Depends(get_repository),  # noqa: B008
) -> AnimalDetailResponse:
    """Get animal detail with notes, behavior profile, and assessments."""
    animal = await repo.get_animal(animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")

    behavior_profile = await repo.get_behavior_profile(animal_id)
    notes = await repo.get_notes_for_animal(animal_id)
    assessments = await repo.get_assessments_for_animal(animal_id)

    return AnimalDetailResponse(
        animal=_animal_to_response(animal),
        behavior_profile=BehaviorProfileResponse.model_validate(
            behavior_profile.model_dump()
        )
        if behavior_profile
        else None,
        volunteer_notes=[
            VolunteerNoteResponse.model_validate(n.model_dump()) for n in notes
        ],
        staff_assessments=[
            StaffAssessmentResponse.model_validate(a.model_dump()) for a in assessments
        ],
    )
