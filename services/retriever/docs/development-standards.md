# Development Standards

Standards for Retriever development.

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
refactor/simplify-rag-pipeline
test/add-rag-coverage
chore/update-dependencies
```

### Commit Messages (Conventional Commits)

```
feat: add volunteer login functionality
fix: resolve chat timeout on slow connections
docs: add API endpoint documentation
test: add coverage for RAG retrieval
refactor: extract LLM provider interface
chore: update dependencies
```

**Format:** `<type>: <description>` (lowercase, imperative mood, no period)

## Code Quality

### Required Checks (CI enforced)

All backend commands run from the `backend/` directory using `uv run`:

```bash
# Linting
uv run ruff check src/ tests/ --fix
uv run ruff format src/ tests/

# Type checking (strict mode — use python -m mypy, NOT uv run mypy)
uv run python -m mypy src/ --strict

# Tests with coverage
uv run python -m pytest tests/ --cov=src/retriever --cov-report=term-missing --cov-fail-under=80

# Security audit
uv run pip-audit
```

### All Checks (run before PR)

Run from `backend/`:

```bash
uv run ruff check src/ tests/ --fix && \
uv run ruff format src/ tests/ && \
uv run python -m mypy src/ --strict && \
uv run python -m pytest tests/ --cov=src/retriever --cov-fail-under=80
```

## Local Development

The dev workflow runs infrastructure in Docker + Supabase CLI, with backend and frontend running natively for fast live reload.

```bash
# 1. Start Supabase (auth, realtime, storage)
supabase start

# 2. Start infrastructure (pgvector postgres + jaeger)
docker compose up -d

# 3. Backend (separate terminal)
cd backend && uv sync --dev
uv run alembic upgrade head          # first time / after migrations
uv run uvicorn retriever.main:app --reload --port 8000

# 4. Frontend (separate terminal)
cd frontend && npm install
npm run dev                          # live reload on :5173

# 5. Stop everything
docker compose down && supabase stop
```

**Why this approach:**
- Backend and frontend run natively for fast hot-reload
- Docker Compose provides pgvector Postgres and Jaeger for local tracing
- Supabase CLI provides local Auth, Realtime, and Storage
- No container rebuilds during development

## Type Hints

**Required** on all function signatures, including return types.

```python
# Good
async def ask_question(question: str, user_id: UUID) -> Answer:
    ...

# Bad - missing types
async def ask_question(question, user_id):
    ...
```

## Docstrings (Google Style)

Required for public APIs and non-trivial functions.

```python
def generate_answer(question: str, context: list[str]) -> str:
    """Generate an answer using retrieved context.

    Args:
        question: The user's question.
        context: Retrieved document chunks relevant to the question.

    Returns:
        The generated answer text.

    Raises:
        LLMProviderError: If the LLM API call fails.
    """
```

## Testing

### Coverage

80% minimum for new code.

### Naming

`test_<function>_<scenario>_<expected>`

```python
def test_ask_question_with_valid_input_returns_answer():
    ...

def test_ask_question_with_empty_context_returns_fallback():
    ...
```

### Categories

```
tests/
├── unit/           # Fast, isolated tests (mock dependencies)
├── integration/    # Tests with real dependencies (DB, APIs)
├── e2e/            # Full workflow tests
└── rag_evaluation/ # RAG quality tests
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
- Content moderation on user input

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
- [CLAUDE.md](../CLAUDE.md) - Quick reference
