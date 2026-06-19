# 2. Keep Pydantic Models Mutable

Date: 2026-01-12
Status: Accepted

## Context

Evaluated whether to make Pydantic models immutable (frozen=True) for the SQLite repository pattern. The codebase uses a fetch-modify-update cycle where models are retrieved from the database, modified in-memory, and persisted.

Current implementation has models with `validate_assignment=True`, enabling:
- Validators that run on field assignment (JSON parsing, SQLite bool conversion)
- Update tracking via `exclude_unset=True` for partial updates
- Ergonomic mutation pattern: `animal.weight_lbs = 70.0`

Investigation found 18+ mutation sites in tests and no usage of models as dict keys or in sets (no hashability requirement).

## Decision

Keep models mutable with `validate_assignment=True`. Do not implement `frozen=True`.

Rationale:
1. **Critical validators require validate_assignment**: `parse_behavior_mod_tags` converts JSON strings to lists, `validate_sqlite_bool` converts SQLite 0/1 to Python booleans. These must run on assignment.
2. **Update pattern relies on mutability**: `exclude_unset=True` tracking only works with mutable models. Frozen models would require manual change tracking.
3. **High refactoring cost**: 18+ mutation sites would need refactoring with no current benefit.
4. **No current need for immutability**: Models only used internally in repository module, no concurrency requirements, not used as dict keys.

## Consequences

**Positive**:
- Maintains clean, ergonomic update pattern
- Validators run on all field assignments (data integrity)
- Zero refactoring cost (187 tests continue passing)
- Well-established pattern for repository-backed models

**Negative**:
- Models can be mutated unexpectedly by external code (mitigated: internal use only)
- Not hashable (acceptable: not used in sets or as dict keys)
- Potential for aliasing bugs with shared references (mitigated: single-threaded, clear ownership)

**Migration**:
None required. Add usage documentation to model docstrings to clarify intended mutation pattern.

## When to Reconsider

Re-evaluate frozen models if:
- Models are exposed in public API to external consumers
- Concurrency becomes a requirement (async operations)
- Models need to be used as dict keys or in sets
- Team experiences aliasing bugs from shared mutable state
