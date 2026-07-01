# Copyright (C) 2025 Backchain LLC
# SPDX-License-Identifier: Apache-2.0

"""Generation-side data-spine contracts: Package and Composition.

These model the middle of the spine ``Animal Record -> Package -> Composition``.
Per the vision doc:

- A **Package** is "a curated, named selection of evidence assembled by a human
  (now) or the LLM (later), the generation-ready subset of the Animal Record";
  it is versioned and every item carries provenance ``{source, location,
  category}``.
- A **Composition** is "the generated and human-edited piece = Package +
  Template + customizations", auto-versioned, and each unit links back to its
  package items and the research rule it satisfies.

Provenance lives in Package and Composition and drops at Export.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


class Provenance(BaseModel):
    """Per-item provenance for a piece of curated evidence.

    Records where one Package item came from. Per the vision doc, every Package
    item carries provenance ``{source document, location, category}``.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    source: str  # the source document the evidence came from
    location: str  # where in the source (page, field, timestamp, URL fragment)
    category: str  # the kind of evidence (behavior, medical, demographics, ...)


class PackageItem(BaseModel):
    """A single unit of curated evidence within a Package.

    Each item carries its own provenance so the generated Composition can cite
    exactly where a claim originated.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    content: str
    provenance: Provenance


class Package(BaseModel):
    """A curated, named, versioned selection of evidence for one animal.

    The generation-ready subset of the Animal Record; the seam between PetData
    and BioWriter.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    name: str
    animal_id: str
    version: int = 1
    items: list[PackageItem] = Field(default_factory=list)


class CompositionUnit(BaseModel):
    """One unit of a Composition linked to its evidence and research rule.

    Ties a span of generated text back to the Package item it draws from and the
    research rule it satisfies, preserving provenance through generation.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    content: str
    source_item: PackageItem | None = None
    rule: str | None = None


class Composition(BaseModel):
    """A generated and human-edited piece: Package + Template + edits.

    The living source of truth inside the platform. Auto-versioned, and each
    unit links back to its package items and the research rule it satisfies,
    so provenance is retained until Export flattens it.
    """

    model_config = ConfigDict(
        validate_assignment=True,
    )

    package: Package
    template: str
    version: int = 1
    content: str = ""
    units: list[CompositionUnit] = Field(default_factory=list)
