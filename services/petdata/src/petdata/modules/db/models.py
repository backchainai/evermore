# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Data models for petdata database entities.

The canonical domain models now live in the shared ``evermore_schema`` package
(the single source for the Evermore data-spine contracts). This module
re-exports them so existing imports (``petdata.modules.db.models.Animal``,
``petdata.modules.db.Animal``) keep resolving unchanged. petdata no longer
defines these classes; it imports them.
"""

from __future__ import annotations

from evermore_schema import (
    Animal,
    AnimalImage,
    AnimalRecord,
    Composition,
    KennelCard,
    Package,
    StaffAssessment,
    SyncLog,
    VolunteerNote,
    WalkRecord,
)

__all__ = [
    "Animal",
    "AnimalImage",
    "AnimalRecord",
    "Composition",
    "KennelCard",
    "Package",
    "StaffAssessment",
    "SyncLog",
    "VolunteerNote",
    "WalkRecord",
]
