# evermore-schema

Single canonical source for the Evermore data-spine Pydantic contracts,
consumed by `services/petdata` and `services/biowriter` via a uv path
dependency (see `services/petdata/CLAUDE.md`, "Container build").

- `evermore_schema.animal` -- the Animal Record layer.
- `evermore_schema.spine` -- the generation-side (`Package`, `Composition`)
  contracts.

See `../../docs/evermore-vision-and-architecture.md` for the settled
data-spine definitions this package implements.
