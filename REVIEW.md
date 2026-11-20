# Review policy

The `reviewer` agent applies these passes to `git diff origin/<default>...HEAD` in a fresh context. The ship skill hands it the findings of `/code-review` for the bugs pass and of the `security` agent, which runs `/security-review`, for the security pass (skipped when every changed path is Markdown), and the reviewer confirms, ranks, or drops each. Findings inform the human reviewer and never approve a pull request; an Important finding still open in the third review cycle stops `/daedalus:ship` before it opens one.

## Passes

1. **Bugs.** Logic errors, unhandled failure paths, broken edge cases, and tests that pass without exercising the change.
2. **Security.** Injection, authorization gaps, secrets, unsafe deserialization, path traversal, and new dependencies.
3. **Conformance.** The diff against the issue's spec, its plan (including `## Files`), and the decisions in `docs/decisions/`.

## Severity

- **Important**: a defect, a security exposure, or a departure from the spec or plan. Each one is fixed before the pull request opens; `/daedalus:ship` stops for the operator when one is still open in its third review cycle.
- **Nit**: style or a small improvement. Report at most five of your own; list every finding passed in from `/code-review` or `/security-review` with its disposition.

## Callouts

The pull request lists each callout that applies under Reviewer callouts, above its evidence, so the human reviewer sees them first:

- **Harness paths.** Changed files under or named `.claude/`, `.github/`, `CLAUDE.md`, `AGENTS.md`, `REVIEW.md`, `Makefile`, `GNUmakefile`, `justfile`, `package.json`, `pyproject.toml`, and the paths in the CLAUDE.md Harness paths section. They define the gates or the agent's instructions.
- **Dependencies and decisions.** New or loosened dependencies, and new files in `docs/decisions/`.
- **Project paths.** Changed paths that Project specifics below names for human review.

## Project specifics

- **Client and tool names.** No client names or branded shelter-system tool names anywhere in the tree; refer to shelter systems generically (ADR 0022 and the CLAUDE.md working conventions). An integration module is named after its integration point.
- **Auth and data access.** Changes to Supabase RLS policies, migrations, the auth path (`packages/auth`, `apps/stacker/src/lib/server/supabase.ts`, `apps/stacker/src/hooks.server.ts`), or the cookie handling in ADR 0032 need human review.
- **Secrets.** Secrets stay in untracked `.env` files; a `.env.example` carries names only, never values.
- **Generated types.** `types.generated.ts` under `apps/stacker` changes only by `npm run gen:types` after an OpenAPI change, never by hand.
- **Decisions.** A change to a settled decision (see `docs/decisions/`) arrives with a superseding decision, not an in-place edit of the old record.
