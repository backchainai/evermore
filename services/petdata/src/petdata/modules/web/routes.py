"""FastAPI routes for Pet Data API.

Wraps the existing sync Database repository using asyncio.to_thread()
for non-blocking operation. Same pattern as Retriever's Docling processor.
"""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

from fastapi import APIRouter, Depends, HTTPException

from petdata.modules.db.models import Animal  # noqa: TC001
from petdata.modules.web.dependencies import get_db
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
    db: Database = Depends(get_db),  # noqa: B008
) -> AnimalListResponse:
    """List animals with pagination."""
    animals = await asyncio.to_thread(db.list_animals, limit, offset)
    return AnimalListResponse(
        animals=[_animal_to_response(a) for a in animals],
        count=len(animals),
    )


@router.get("/animals/{animal_id}", response_model=AnimalDetailResponse)
async def get_animal(
    animal_id: str,
    db: Database = Depends(get_db),  # noqa: B008
) -> AnimalDetailResponse:
    """Get animal detail with notes, kennel card, and assessments."""
    animal = await asyncio.to_thread(db.get_animal, animal_id)
    if animal is None:
        raise HTTPException(status_code=404, detail="Animal not found")

    kennel_card, notes, assessments = await asyncio.gather(
        asyncio.to_thread(db.get_kennel_card, animal_id),
        asyncio.to_thread(db.get_notes_for_animal, animal_id),
        asyncio.to_thread(db.get_assessments_for_animal, animal_id),
    )

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
