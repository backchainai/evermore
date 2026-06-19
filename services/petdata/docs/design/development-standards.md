---
name: development-standards
description: Read when contributing code or reviewing PRs. Covers quality standards, git workflow, testing.
category: process
when_to_use:
- Setting up a new project
- Onboarding new contributors
- Establishing team conventions
- Reviewing code quality requirements
dependencies:
- architecture.md
---
# Development Standards

Standards for petbio development.

## Git Workflow: GitHub Flow

```
main (protected) ← feature branches via PR
```

### Process

1. Create feature branch from `main`
2. Make changes, commit with conventional messages
3. Open PR, request review
4. 1 approval required + CI passes
5. Squash merge to main
6. Delete feature branch

### Branch Naming

```
feature/add-user-auth
fix/chat-input-validation
docs/update-readme
refactor/simplify-pipeline
test/add-coverage
chore/update-dependencies
```

### Commit Messages (Conventional Commits)

```
feat: add login functionality
fix: resolve timeout on slow connections
docs: add API endpoint documentation
test: add coverage for retrieval
refactor: extract provider interface
chore: update dependencies
```

**Format:** `<type>: <description>` (lowercase, imperative mood, no period)

## Code Quality

### Required Checks (CI enforced)

```bash
# Linting
ruff check src/ tests/ --fix
ruff format src/ tests/

# Type checking (strict mode)
mypy src/ --strict

# Tests with coverage
pytest --cov=src --cov-report=term-missing --cov-fail-under=80

# Security audit
pip-audit
```

### All Checks (run before PR)

```bash
ruff check src/ tests/ --fix && \
ruff format src/ tests/ && \
mypy src/ --strict && \
pytest --cov=src --cov-fail-under=80
```

## Type Hints

**Required** on all function signatures, including return types.

```python
# Good
async def process_item(item_id: str, user_id: UUID) -> Result:
    ...

# Bad - missing types
async def process_item(item_id, user_id):
    ...
```

## Docstrings (Google Style)

Required for public APIs and non-trivial functions.

```python
def process_data(input_data: str, options: list[str]) -> str:
    """Process input data with the given options.

    Args:
        input_data: The raw input to process.
        options: Processing options to apply.

    Returns:
        The processed output string.

    Raises:
        ProcessingError: If processing fails.
    """
```

## Testing

### Coverage

80% minimum for new code.

### Naming

`test_<function>_<scenario>_<expected>`

```python
def test_process_data_with_valid_input_returns_result():
    ...

def test_process_data_with_empty_input_returns_fallback():
    ...
```

### Categories

```
tests/
├── unit/           # Fast, isolated tests (mock dependencies)
├── integration/    # Tests with real dependencies (DB, APIs)
└── e2e/            # Full workflow tests
```

### Required Tests

- Unit tests for all business logic
- Integration tests for API endpoints
- Regression tests for bug fixes

## Error Handling

```python
# Never bare except
try:
    result = await risky_operation()
except SpecificError as e:
    logger.error("Operation failed", error=str(e))
    raise DomainError("Friendly message") from e
```

- Never bare `except:` - always specify exception types
- Chain exceptions with `from` for context
- Use custom exception hierarchy for domain errors

## Security

### Never Commit

- API keys, secrets, passwords
- `.env` files (use `.env.example` as template)
- Credentials of any kind

### Required

- `pip-audit` in CI (vulnerability scanning)
- Secrets in environment variables only
- Input validation on all endpoints

## PR Requirements

### Before Opening PR

- [ ] All tests pass locally
- [ ] New code has tests (80% coverage)
- [ ] Types check with mypy
- [ ] Linting passes (ruff)
- [ ] Documentation updated if needed
- [ ] ADR created for significant decisions

### PR Template

```markdown
## Summary
Brief description of changes.

## Type
- [ ] Feature
- [ ] Bug fix
- [ ] Refactor
- [ ] Documentation
- [ ] Tests

## Testing
How was this tested?

## Checklist
- [ ] Tests pass
- [ ] Types check
- [ ] Docs updated
- [ ] ADR added (if significant decision)
```

### Review Process

- 1 approval required
- CI must pass
- Squash merge (clean history)

## Dependencies

### Adding New Dependencies

1. Check if stdlib solution exists
2. Verify library is well-maintained
3. Check for security vulnerabilities
4. Ask before adding unfamiliar dependencies

### Pre-Approved Libraries

| Category | Libraries |
|----------|-----------|
| HTTP | requests, httpx, aiohttp |
| CLI | click, typer |
| Validation | pydantic, pydantic-settings |
| Testing | pytest, pytest-cov, pytest-asyncio |
| Database | sqlalchemy, alembic |
| Logging | structlog, loguru |

## Related Documents

- [Architecture](architecture.md)
- [ADRs](decisions/)
