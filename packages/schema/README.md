# evermore-schema

The single canonical source for the Evermore data-spine contracts:

```
Sources -> Animal Record -> Package -> Composition -> Export
```

- `evermore_schema.animal` — the canonical Animal Record layer (the seven
  normalized domain models plus the composite `AnimalRecord`). Owned
  conceptually by PetData.
- `evermore_schema.spine` — the generation-side contracts (`Provenance`,
  `PackageItem`, `Package`, `Composition`, `CompositionUnit`). The `Package`
  is the seam between PetData and BioWriter.

See `docs/evermore-vision-and-architecture.md` for the settled definitions of
each object.
