# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Shared Pydantic contracts for the Evermore data spine.

``Sources -> Animal Record -> Package -> Composition -> Export``

This package is the single canonical source for the data-spine models. The
Animal Record layer lives in :mod:`evermore_schema.animal`; the generation-side
Package and Composition contracts live in :mod:`evermore_schema.spine`.
"""

from __future__ import annotations

from evermore_schema.animal import (
    Animal,
    AnimalImage,
    AnimalRecord,
    BehaviorProfile,
    StaffAssessment,
    SyncLog,
    VolunteerNote,
    WalkRecord,
)
from evermore_schema.spine import (
    Composition,
    CompositionUnit,
    Package,
    PackageItem,
    Provenance,
)

__all__ = [
    "Animal",
    "AnimalImage",
    "AnimalRecord",
    "BehaviorProfile",
    "Composition",
    "CompositionUnit",
    "Package",
    "PackageItem",
    "Provenance",
    "StaffAssessment",
    "SyncLog",
    "VolunteerNote",
    "WalkRecord",
]
