"""Unit tests for web route helpers."""

from __future__ import annotations

from petdata.modules.db.models import Animal
from petdata.modules.web.routes import _animal_to_response


def test_animal_to_response_exposes_species_location_foster_and_synced_at() -> None:
    """_animal_to_response wires through species, location, foster, and freshness."""
    animal = Animal(
        id="A-00000",
        name="Buddy",
        species="dog",
        location="Line 3, 3A",
        is_foster_care=True,
        last_synced_at="2026-06-02T08:30:00+00:00",
    )

    response = _animal_to_response(animal)

    assert response.species == "dog"
    assert response.location == "Line 3, 3A"
    assert response.is_foster_care is True
    assert response.synced_at == animal.last_synced_at
