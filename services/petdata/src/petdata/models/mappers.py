# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Thin mapping between the Pydantic contract and the SQLAlchemy ORM rows.

The Pydantic models (``petdata.modules.db.models``) stay the wire/domain
contract and keep timestamps as ISO strings. The ORM rows
(``petdata.models.tables``) use native ``date`` / ``datetime`` columns. These
helpers convert between the two. The async repository (#9b) builds on them.

``tenant_id`` lives only on the ORM row; ``*_to_row`` leaves it unset so the
column default applies, and ``*_from_row`` drops it (the contract has no such
field).
"""

import datetime

from petdata.models import tables as orm
from petdata.modules.db import models as pyd


def _parse_dt(value: str | None) -> datetime.datetime | None:
    """Parse an ISO timestamp string into a datetime."""
    return None if value is None else datetime.datetime.fromisoformat(value)


def _fmt_dt(value: datetime.datetime | None) -> str | None:
    """Render a datetime as an ISO timestamp string."""
    return None if value is None else value.isoformat()


def _parse_date(value: str | None) -> datetime.date | None:
    """Parse an ISO date (or datetime) string into a date."""
    if value is None:
        return None
    try:
        return datetime.date.fromisoformat(value)
    except ValueError:
        return datetime.datetime.fromisoformat(value).date()


def _fmt_date(value: datetime.date | None) -> str | None:
    """Render a date as an ISO date string."""
    return None if value is None else value.isoformat()


def animal_to_row(model: pyd.Animal) -> orm.Animal:
    """Map an Animal contract model to an ORM row."""
    row = orm.Animal(
        id=model.id,
        name=model.name,
        aka=model.aka,
        breed=model.breed,
        weight_lbs=model.weight_lbs,
        birth_date=_parse_date(model.birth_date),
        intake_date=_parse_date(model.intake_date),
        location=model.location,
        color_category=model.color_category,
        behavior_mod_tags=model.behavior_mod_tags,
        is_in_kennel=model.is_in_kennel,
        is_foster_care=model.is_foster_care,
        photo_url=model.photo_url,
        public_profile_url=model.public_profile_url,
        adalo_record_id=model.adalo_record_id,
        last_synced_at=_parse_dt(model.last_synced_at),
    )
    # created_at / updated_at carry server defaults; only override when supplied.
    if model.created_at is not None:
        row.created_at = datetime.datetime.fromisoformat(model.created_at)
    if model.updated_at is not None:
        row.updated_at = datetime.datetime.fromisoformat(model.updated_at)
    return row


def animal_from_row(row: orm.Animal) -> pyd.Animal:
    """Map an ORM Animal row back to the contract model."""
    return pyd.Animal(
        id=row.id,
        name=row.name,
        aka=row.aka,
        breed=row.breed,
        weight_lbs=row.weight_lbs,
        birth_date=_fmt_date(row.birth_date),
        intake_date=_fmt_date(row.intake_date),
        location=row.location,
        color_category=row.color_category,
        behavior_mod_tags=row.behavior_mod_tags,
        is_in_kennel=row.is_in_kennel,
        is_foster_care=row.is_foster_care,
        photo_url=row.photo_url,
        public_profile_url=row.public_profile_url,
        adalo_record_id=row.adalo_record_id,
        created_at=_fmt_dt(row.created_at),
        updated_at=_fmt_dt(row.updated_at),
        last_synced_at=_fmt_dt(row.last_synced_at),
    )


def kennel_card_to_row(model: pyd.KennelCard) -> orm.KennelCard:
    """Map a KennelCard contract model to an ORM row."""
    row = orm.KennelCard(
        animal_id=model.animal_id,
        about_text=model.about_text,
        dogs_compatibility=model.dogs_compatibility,
        dogs_compatibility_notes=model.dogs_compatibility_notes,
        cats_compatibility=model.cats_compatibility,
        cats_compatibility_notes=model.cats_compatibility_notes,
        kids_compatibility=model.kids_compatibility,
        kids_compatibility_notes=model.kids_compatibility_notes,
        commands_known=model.commands_known,
        housebreaking_status=model.housebreaking_status,
        things_likes=model.things_likes,
        things_dislikes=model.things_dislikes,
        last_synced_at=_parse_dt(model.last_synced_at),
    )
    if model.id is not None:
        row.id = model.id
    return row


def kennel_card_from_row(row: orm.KennelCard) -> pyd.KennelCard:
    """Map an ORM KennelCard row back to the contract model."""
    return pyd.KennelCard(
        id=row.id,
        animal_id=row.animal_id,
        about_text=row.about_text,
        dogs_compatibility=row.dogs_compatibility,
        dogs_compatibility_notes=row.dogs_compatibility_notes,
        cats_compatibility=row.cats_compatibility,
        cats_compatibility_notes=row.cats_compatibility_notes,
        kids_compatibility=row.kids_compatibility,
        kids_compatibility_notes=row.kids_compatibility_notes,
        commands_known=row.commands_known,
        housebreaking_status=row.housebreaking_status,
        things_likes=row.things_likes,
        things_dislikes=row.things_dislikes,
        last_synced_at=_fmt_dt(row.last_synced_at),
    )


def volunteer_note_to_row(model: pyd.VolunteerNote) -> orm.VolunteerNote:
    """Map a VolunteerNote contract model to an ORM row."""
    note_date = _parse_dt(model.note_date)
    if note_date is None:
        raise ValueError("VolunteerNote.note_date is required")
    row = orm.VolunteerNote(
        animal_id=model.animal_id,
        adalo_record_id=model.adalo_record_id,
        volunteer_name=model.volunteer_name,
        note_date=note_date,
        note_text=model.note_text,
        rating_strong_on_leash=model.rating_strong_on_leash,
        rating_leash_reactivity=model.rating_leash_reactivity,
        rating_shy_fearful=model.rating_shy_fearful,
        rating_jumpy_mouthy=model.rating_jumpy_mouthy,
        last_synced_at=_parse_dt(model.last_synced_at),
    )
    if model.id is not None:
        row.id = model.id
    if model.created_at is not None:
        row.created_at = datetime.datetime.fromisoformat(model.created_at)
    return row


def volunteer_note_from_row(row: orm.VolunteerNote) -> pyd.VolunteerNote:
    """Map an ORM VolunteerNote row back to the contract model."""
    return pyd.VolunteerNote(
        id=row.id,
        animal_id=row.animal_id,
        adalo_record_id=row.adalo_record_id,
        volunteer_name=row.volunteer_name,
        note_date=_fmt_dt(row.note_date) or "",
        note_text=row.note_text,
        rating_strong_on_leash=row.rating_strong_on_leash,
        rating_leash_reactivity=row.rating_leash_reactivity,
        rating_shy_fearful=row.rating_shy_fearful,
        rating_jumpy_mouthy=row.rating_jumpy_mouthy,
        created_at=_fmt_dt(row.created_at),
        last_synced_at=_fmt_dt(row.last_synced_at),
    )


def staff_assessment_to_row(model: pyd.StaffAssessment) -> orm.StaffAssessment:
    """Map a StaffAssessment contract model to an ORM row."""
    row = orm.StaffAssessment(
        animal_id=model.animal_id,
        assessment_tags=model.assessment_tags,
        notes=model.notes,
        recorded_at=_parse_dt(model.recorded_at),
        last_synced_at=_parse_dt(model.last_synced_at),
    )
    if model.id is not None:
        row.id = model.id
    return row


def staff_assessment_from_row(row: orm.StaffAssessment) -> pyd.StaffAssessment:
    """Map an ORM StaffAssessment row back to the contract model."""
    return pyd.StaffAssessment(
        id=row.id,
        animal_id=row.animal_id,
        assessment_tags=row.assessment_tags,
        notes=row.notes,
        recorded_at=_fmt_dt(row.recorded_at),
        last_synced_at=_fmt_dt(row.last_synced_at),
    )


def walk_record_to_row(model: pyd.WalkRecord) -> orm.WalkRecord:
    """Map a WalkRecord contract model to an ORM row."""
    row = orm.WalkRecord(
        animal_id=model.animal_id,
        adalo_record_id=model.adalo_record_id,
        volunteer_name=model.volunteer_name,
        out_time=_parse_dt(model.out_time),
        in_time=_parse_dt(model.in_time),
    )
    if model.id is not None:
        row.id = model.id
    if model.created_at is not None:
        row.created_at = datetime.datetime.fromisoformat(model.created_at)
    return row


def walk_record_from_row(row: orm.WalkRecord) -> pyd.WalkRecord:
    """Map an ORM WalkRecord row back to the contract model."""
    return pyd.WalkRecord(
        id=row.id,
        animal_id=row.animal_id,
        adalo_record_id=row.adalo_record_id,
        volunteer_name=row.volunteer_name,
        out_time=_fmt_dt(row.out_time),
        in_time=_fmt_dt(row.in_time),
        created_at=_fmt_dt(row.created_at),
    )


def animal_image_to_row(model: pyd.AnimalImage) -> orm.AnimalImage:
    """Map an AnimalImage contract model to an ORM row."""
    row = orm.AnimalImage(
        animal_id=model.animal_id,
        image_url=model.image_url,
        display_order=model.display_order,
        last_synced_at=_parse_dt(model.last_synced_at),
    )
    if model.id is not None:
        row.id = model.id
    return row


def animal_image_from_row(row: orm.AnimalImage) -> pyd.AnimalImage:
    """Map an ORM AnimalImage row back to the contract model."""
    return pyd.AnimalImage(
        id=row.id,
        animal_id=row.animal_id,
        image_url=row.image_url,
        display_order=row.display_order,
        last_synced_at=_fmt_dt(row.last_synced_at),
    )


def sync_log_to_row(model: pyd.SyncLog) -> orm.SyncLog:
    """Map a SyncLog contract model to an ORM row."""
    started_at = _parse_dt(model.started_at)
    if started_at is None:
        raise ValueError("SyncLog.started_at is required")
    row = orm.SyncLog(
        sync_type=model.sync_type,
        table_name=model.table_name,
        started_at=started_at,
        completed_at=_parse_dt(model.completed_at),
        records_processed=model.records_processed,
        records_created=model.records_created,
        records_updated=model.records_updated,
        status=model.status,
        error_message=model.error_message,
    )
    if model.id is not None:
        row.id = model.id
    return row


def sync_log_from_row(row: orm.SyncLog) -> pyd.SyncLog:
    """Map an ORM SyncLog row back to the contract model."""
    return pyd.SyncLog(
        id=row.id,
        sync_type=row.sync_type,
        table_name=row.table_name,
        started_at=_fmt_dt(row.started_at) or "",
        completed_at=_fmt_dt(row.completed_at),
        records_processed=row.records_processed,
        records_created=row.records_created,
        records_updated=row.records_updated,
        status=row.status,
        error_message=row.error_message,
    )
