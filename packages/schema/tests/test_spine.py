"""Unit tests for the generation-side data-spine contracts."""

from __future__ import annotations

from evermore_schema import (
    Composition,
    CompositionUnit,
    Package,
    PackageItem,
    Provenance,
)


class TestProvenance:
    """Tests for Provenance."""

    def test_construct(self):
        """Provenance records source, location, and category."""
        prov = Provenance(
            source="sms-export",
            location="page 2",
            category="behavior",
        )
        assert prov.source == "sms-export"
        assert prov.location == "page 2"
        assert prov.category == "behavior"


class TestPackageItem:
    """Tests for PackageItem."""

    def test_item_carries_provenance(self):
        """Every PackageItem carries its provenance."""
        item = PackageItem(
            content="Walks well on leash.",
            provenance=Provenance(
                source="volunteer-note-12",
                location="2026-06-01",
                category="behavior",
            ),
        )
        assert item.provenance.source == "volunteer-note-12"
        assert item.provenance.category == "behavior"


class TestPackage:
    """Tests for Package."""

    def test_defaults(self):
        """Package defaults to version 1 with an empty item list."""
        pkg = Package(name="adoption", animal_id="A-00001")
        assert pkg.version == 1
        assert pkg.items == []

    def test_items_carry_provenance(self):
        """Items in a Package each retain their provenance."""
        pkg = Package(
            name="adoption",
            animal_id="A-00001",
            items=[
                PackageItem(
                    content="Loves fetch.",
                    provenance=Provenance(
                        source="note-1", location="l1", category="behavior"
                    ),
                ),
                PackageItem(
                    content="Up to date on shots.",
                    provenance=Provenance(
                        source="med-2", location="l2", category="medical"
                    ),
                ),
            ],
        )
        assert len(pkg.items) == 2
        assert {i.provenance.category for i in pkg.items} == {"behavior", "medical"}

    def test_default_item_lists_are_independent(self):
        """Two Packages do not share a mutable default items list."""
        a = Package(name="a", animal_id="A-1")
        b = Package(name="b", animal_id="A-2")
        a.items.append(
            PackageItem(
                content="x",
                provenance=Provenance(source="s", location="l", category="c"),
            )
        )
        assert b.items == []


class TestComposition:
    """Tests for Composition."""

    def _package(self) -> Package:
        return Package(
            name="adoption",
            animal_id="A-00001",
            items=[
                PackageItem(
                    content="Friendly.",
                    provenance=Provenance(
                        source="note-1", location="l1", category="behavior"
                    ),
                )
            ],
        )

    def test_construct_from_package_and_template(self):
        """A Composition binds a Package to a Template with a version."""
        comp = Composition(package=self._package(), template="kennel-card")
        assert comp.version == 1
        assert comp.content == ""
        assert comp.units == []
        assert comp.package.name == "adoption"

    def test_unit_links_back_to_item_and_rule(self):
        """A CompositionUnit links generated text to its item and rule."""
        pkg = self._package()
        comp = Composition(
            package=pkg,
            template="kennel-card",
            content="Meet a friendly dog.",
            units=[
                CompositionUnit(
                    content="friendly dog",
                    source_item=pkg.items[0],
                    rule="lead-with-temperament",
                )
            ],
        )
        assert comp.units[0].source_item is not None
        assert comp.units[0].source_item.provenance.source == "note-1"
        assert comp.units[0].rule == "lead-with-temperament"
