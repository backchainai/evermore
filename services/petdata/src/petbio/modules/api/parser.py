"""Response parsers for Adalo API to Pydantic models.

IMPORTANT: Adalo field names are placeholders and must be verified against
real API responses before production use.
"""

from __future__ import annotations

from typing import Any

from pydantic import ValidationError

from petbio.modules.api.exceptions import APIValidationError
from petbio.modules.db.models import Animal, VolunteerNote, WalkRecord


def parse_animal_response(raw_data: dict[str, Any]) -> list[Animal]:
    """Parse Adalo animals API response to Animal models.

    Handles Adalo-specific field mappings:
    - "id" field in Adalo → "adalo_record_id" in model
    - Custom field names to model field names

    Args:
        raw_data: Raw JSON response from Adalo API with {"records": [...]} structure.

    Returns:
        List of validated Animal models. Empty list if no records.

    Raises:
        APIValidationError: If response structure is invalid or any
            record fails Pydantic validation.

    Example:
        >>> raw = client.fetch_animals(limit=10)
        >>> animals = parse_animal_response(raw)
        >>> len(animals)
        10
    """
    try:
        records = raw_data.get("records", [])
        if not isinstance(records, list):
            msg = f"Expected 'records' to be list, got {type(records).__name__}"
            raise APIValidationError(msg)

        animals: list[Animal] = []
        for record in records:
            # CRITICAL: These field names are PLACEHOLDERS - verify with real API
            # Map Adalo fields to Animal model fields
            animal_data = {
                "id": record.get("FOHA ID", ""),  # Custom field in Adalo
                "adalo_record_id": record.get("id", ""),  # Adalo internal ID
                "name": record.get("Name", ""),
                "aka": record.get("AKA"),
                "breed": record.get("Breed"),
                "weight_lbs": record.get("Weight (lbs)"),
                "birth_date": record.get("Birth Date"),
                "intake_date": record.get("Intake Date"),
                "location": record.get("Location"),
                "color_category": record.get("Color Category"),
                "behavior_mod_tags": record.get(
                    "Behavior Mod Tags"
                ),  # Adalo returns as list
                "is_in_kennel": record.get("In Kennel"),
                "is_foster_care": record.get("Foster Care"),
                "photo_url": record.get("Photo URL"),
                "public_profile_url": record.get("Public Profile URL"),
                "created_at": record.get("created_at"),
                "updated_at": record.get("updated_at"),
            }

            # Pydantic validates and handles None values
            try:
                animal = Animal.model_validate(animal_data)
                animals.append(animal)
            except ValidationError as e:
                # Chain Pydantic validation errors to APIValidationError
                msg = f"Failed to validate animal {record.get('id')}: {e}"
                raise APIValidationError(msg) from e

        return animals

    except KeyError as e:
        msg = f"Missing required field in response: {e}"
        raise APIValidationError(msg) from e
    except Exception as e:
        # Catch-all for unexpected errors, but don't catch our own APIValidationError
        if isinstance(e, APIValidationError):
            raise
        msg = f"Failed to parse animal response: {e}"
        raise APIValidationError(msg) from e


def parse_volunteer_note_response(raw_data: dict[str, Any]) -> list[VolunteerNote]:
    """Parse Adalo volunteer notes API response to VolunteerNote models.

    Args:
        raw_data: Raw JSON response from Adalo API with {"records": [...]} structure.

    Returns:
        List of validated VolunteerNote models. Empty list if no records.

    Raises:
        APIValidationError: If response structure is invalid or any
            record fails Pydantic validation.

    Example:
        >>> raw = client.fetch_volunteer_notes(limit=50)
        >>> notes = parse_volunteer_note_response(raw)
        >>> ratings = [n.rating_strong_on_leash for n in notes
        ...            if n.rating_strong_on_leash is not None]
        >>> all(0 <= r <= 5 for r in ratings)
        True
    """
    try:
        records = raw_data.get("records", [])
        if not isinstance(records, list):
            msg = f"Expected 'records' to be list, got {type(records).__name__}"
            raise APIValidationError(msg)

        notes: list[VolunteerNote] = []
        for record in records:
            # CRITICAL: These field names are PLACEHOLDERS - verify with real API
            # Map Adalo fields to VolunteerNote model fields
            note_data = {
                "adalo_record_id": record.get("id", ""),
                "animal_id": record.get("Animal ID", ""),  # Relationship field
                "volunteer_name": record.get("Volunteer Name", ""),
                "note_date": record.get("Note Date", ""),
                "note_text": record.get("Note Text"),
                "rating_strong_on_leash": record.get("Strong on Leash"),
                "rating_leash_reactivity": record.get("Leash Reactivity"),
                "rating_shy_fearful": record.get("Shy/Fearful"),
                "rating_jumpy_mouthy": record.get("Jumpy/Mouthy"),
                "created_at": record.get("created_at"),
            }

            try:
                note = VolunteerNote.model_validate(note_data)
                notes.append(note)
            except ValidationError as e:
                # Chain Pydantic validation errors to APIValidationError
                msg = f"Failed to validate volunteer note {record.get('id')}: {e}"
                raise APIValidationError(msg) from e

        return notes

    except KeyError as e:
        msg = f"Missing required field in response: {e}"
        raise APIValidationError(msg) from e
    except Exception as e:
        if isinstance(e, APIValidationError):
            raise
        msg = f"Failed to parse volunteer note response: {e}"
        raise APIValidationError(msg) from e


def parse_walk_record_response(raw_data: dict[str, Any]) -> list[WalkRecord]:
    """Parse Adalo walk records API response to WalkRecord models.

    Args:
        raw_data: Raw JSON response from Adalo API with {"records": [...]} structure.

    Returns:
        List of validated WalkRecord models. Empty list if no records.

    Raises:
        APIValidationError: If response structure is invalid or any
            record fails Pydantic validation.

    Example:
        >>> raw = client.fetch_walk_records(limit=100)
        >>> walks = parse_walk_record_response(raw)
        >>> all(w.animal_id for w in walks)
        True
    """
    try:
        records = raw_data.get("records", [])
        if not isinstance(records, list):
            msg = f"Expected 'records' to be list, got {type(records).__name__}"
            raise APIValidationError(msg)

        walks: list[WalkRecord] = []
        for record in records:
            # CRITICAL: These field names are PLACEHOLDERS - verify with real API
            walk_data = {
                "adalo_record_id": record.get("id", ""),
                "animal_id": record.get("Animal ID", ""),
                "volunteer_name": record.get("Volunteer Name"),
                "out_time": record.get("Out Time"),
                "in_time": record.get("In Time"),
                "created_at": record.get("created_at"),
            }

            try:
                walk = WalkRecord.model_validate(walk_data)
                walks.append(walk)
            except ValidationError as e:
                # Chain Pydantic validation errors to APIValidationError
                msg = f"Failed to validate walk record {record.get('id')}: {e}"
                raise APIValidationError(msg) from e

        return walks

    except KeyError as e:
        msg = f"Missing required field in response: {e}"
        raise APIValidationError(msg) from e
    except Exception as e:
        if isinstance(e, APIValidationError):
            raise
        msg = f"Failed to parse walk record response: {e}"
        raise APIValidationError(msg) from e
