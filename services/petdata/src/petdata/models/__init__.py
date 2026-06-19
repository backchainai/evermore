# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""SQLAlchemy persistence layer for petdata.

The ORM rows here are the persistence representation; the Pydantic models in
``petdata.modules.db.models`` remain the wire/domain contract. ``mappers``
bridges the two.
"""

from petdata.models.base import (
    Base,
    create_engine,
    create_session_factory,
)
from petdata.models.tables import (
    DEFAULT_TENANT_ID,
    TENANT_OWNED_TABLES,
    Animal,
    AnimalImage,
    KennelCard,
    StaffAssessment,
    SyncLog,
    VolunteerNote,
    WalkRecord,
)

__all__ = [
    "DEFAULT_TENANT_ID",
    "TENANT_OWNED_TABLES",
    "Animal",
    "AnimalImage",
    "Base",
    "KennelCard",
    "StaffAssessment",
    "SyncLog",
    "VolunteerNote",
    "WalkRecord",
    "create_engine",
    "create_session_factory",
]
