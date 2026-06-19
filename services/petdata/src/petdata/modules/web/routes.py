"""FastAPI routes for Pet Data API.

Endpoints depend on the async repository (``get_repository``), which is bound to
a request-scoped SQLAlchemy session. The detail endpoint fetches related data
sequentially on that one session, which is not safe to share across concurrent
awaits.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from petdata.modules.db.models import Animal  # noqa: TC001
from petdata.modules.web.dependencies import get_repository
from petdata.modules.web.schemas import (
    AnimalDetailResponse,
    AnimalListResponse,
    AnimalResponse,
    KennelCardResponse,
    StaffAssessmentResponse,
    VolunteerNoteResponse,
)

if TYPE_CHECKING:
    from petdata.modules.db import Database

router = APIRouter(tags=["animals"])


def _animal_to_response(animal: Animal) -> AnimalResponse:
    """Convert Animal model to API response with computed properties."""
    return AnimalResponse(
        id=animal.id,
        name=animal.name,
        aka=animal.aka,
        breed=animal.breed,
        weight_lbs=animal.weight_lbs,
        birth_date=animal.birth_date,
        intake_date=animal.intake_date,
        location=animal.location,
        color_category=animal.color_category,
        behavior_mod_tags=animal.behavior_mod_tags,
        is_in_kennel=animal.is_in_kennel,
        is_foster_care=animal.is_foster_care,
        photo_url=animal.photo_url,
        public_profile_url=animal.public_profile_url,
        age_years=animal.age_years,
        days_in_shelter=animal.days_in_shelter,
        is_adoptable=animal.is_adoptable,
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
    """Get animal detail with notes, kennel card, and assessments."""
    animal = await repo.get_animal(animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")

    kennel_card = await repo.get_kennel_card(animal_id)
    notes = await repo.get_notes_for_animal(animal_id)
    assessments = await repo.get_assessments_for_animal(animal_id)

    return AnimalDetailResponse(
        animal=_animal_to_response(animal),
        kennel_card=KennelCardResponse.model_validate(kennel_card.model_dump())
        if kennel_card
        else None,
        volunteer_notes=[
            VolunteerNoteResponse.model_validate(n.model_dump()) for n in notes
        ],
        staff_assessments=[
            StaffAssessmentResponse.model_validate(a.model_dump()) for a in assessments
        ],
    )
