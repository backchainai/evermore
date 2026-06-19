# CHANGELOG

All notable changes to petbio will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## How to Update

**Automated:** Changelog is updated automatically by `python-semantic-release` on release based on commit messages.

**Manual additions:** If needed for clarity, add entries under `## Unreleased` section during development.

## Version Format

- **Major (X.0.0):** Breaking changes (incompatible API changes)
- **Minor (0.X.0):** New features (backwards-compatible functionality)
- **Patch (0.0.X):** Bug fixes (backwards-compatible fixes)

## Commit Message → Changelog Mapping

| Commit Type | Changelog Section | Version Bump |
|-------------|-------------------|--------------|
| `feat:` | Added | Minor (0.X.0) |
| `fix:` | Fixed | Patch (0.0.X) |
| `perf:` | Changed | Patch (0.0.X) |
| `docs:` | Documentation | None |
| `test:` | Testing | None |
| `refactor:` | Changed | None |
| `chore:` | Maintenance | None |
| BREAKING CHANGE | Breaking | Major (X.0.0) |

---

## Unreleased

<!-- Add manual entries here if needed during development -->

---

## v1.0.0 (2026-01-11)

### Added

**Phase 1: Data Extraction and Storage (Complete)**

- 7 Pydantic data models with type-safe validation and computed properties:
  - Animal: Core shelter dog/cat record with age calculation, adoptability status
  - VolunteerNote: Behavioral observations with 4-category ratings (0-5 scale)
  - KennelCard: Structured bio with compatibility, commands, preferences
  - StaffAssessment: Professional evaluations with structured tags
  - WalkRecord: Walk check-in/out activity tracking
  - AnimalImage: Photo gallery with display ordering
  - SyncLog: Data extraction operation audit trail

- SQLite database schema with referential integrity:
  - Foreign key constraints with CASCADE deletes
  - Indexes on lookup fields for query performance
  - JSON fields for flexible tag arrays
  - ISO timestamp tracking for data lineage

- Migration system with enterprise-grade safety:
  - Version tracking in migration_history table
  - SHA256 checksum verification prevents tampering
  - Gap and duplicate detection
  - Idempotent SQL with IF NOT EXISTS clauses
  - Transaction-safe execution (splits statements to avoid executescript's implicit commits)

- Repository pattern with full CRUD operations:
  - Database class with methods for all 7 models
  - Context managers for read (connection) and write (transaction) operations
  - Parameterized SQL queries (security audited, no injection risk)
  - Helper functions for timestamps, SQL generation, upserts
  - Cascade deletion support for related records

- Comprehensive test coverage (187 tests):
  - Unit tests: Model validation, computed properties, migration engine logic
  - Integration tests: Full CRUD operations, migration flow, foreign key constraints
  - 80%+ coverage on business logic
  - Pytest fixtures for test database management

- Quality tooling and automation:
  - ruff: Fast linting and formatting (replaces black, isort, flake8, etc.)
  - mypy --strict: Comprehensive type checking with no exceptions
  - bandit: Static security analysis for Python code
  - pytest-cov: Code coverage measurement and reporting
  - pre-commit: Git hook framework for automated quality checks
  - python-semantic-release: Automated versioning and changelog generation

- Documentation suite:
  - README.md: Project overview, features, quick start guide
  - CLAUDE.md: AI assistant guide with coding conventions and patterns
  - CONTRIBUTING.md: Comprehensive contribution guidelines
  - docs/design/architecture.md: System architecture and design patterns
  - docs/design/development-standards.md: Git workflow, testing, quality standards
  - docs/adr/002-mutable-pydantic-models.md: Key architectural decision record
  - LICENSE: MIT license
  - TODO.md: Future work roadmap for Phases 2-3

### Technical Details

- Python 3.13 with strict type checking (mypy --strict enforced)
- Pydantic 2.9+ for data modeling and validation
- SQLite for persistence (Phase 1 database)
- pydantic-settings for environment-based configuration
- uv package manager for fast, deterministic dependency resolution
- 80%+ test coverage with unit and integration tests
- Conventional Commits format for changelog automation
- GitHub Flow branching strategy with squash merges

### Architecture Decisions

- **ADR-002: Keep Pydantic Models Mutable**
  - Decision: Use `validate_assignment=True`, not `frozen=True`
  - Rationale: Validators must run on assignment, repository pattern requires mutability
  - Trade-off: Not hashable (acceptable for internal use only)
