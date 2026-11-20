---
title: Move daedalus enablement to local settings
issue: 345
type: Task
date: 2026-11-20
---

# Move daedalus enablement to local settings

## Context

Implements the acceptance criteria of #345. The repository is public (`gh repo view` reports `PUBLIC`), but the tracked `.claude/settings.json` enables `daedalus@backchain` and declares the `backchain` marketplace, which lives in the private `backchainai/daedalus` repo, so a fresh clone points at a plugin it cannot install. daedalus is also enabled a second time in the untracked `.claude/settings.local.json`.

Acceptance criteria:

- `.claude/settings.json`: `enabledPlugins` drops `daedalus@backchain`; `extraKnownMarketplaces` drops `backchain` and `astral-sh`.
- `supabase@claude-plugins-official`, the `claude-plugins-official` marketplace, and `permissions.deny` stay tracked, unchanged.
- `.claude/settings.local.json` (gitignored) declares the `backchain` and `astral-sh` marketplaces, keeps `daedalus@backchain`, `github@claude-plugins-official`, and `astral@astral-sh` enabled, and drops `context7@claude-plugins-official`, which daedalus 12.4.0 dropped as a dependency.
- CLAUDE.md says daedalus is enabled per clone in `.claude/settings.local.json` and that each new worktree needs that file copied in.
- daedalus still loads in a fresh session on the main checkout.

Operator decision taken in planning: track a `.worktreeinclude` listing only `.claude/settings.local.json`, so every worktree Claude Code creates gets the local settings copied in. The main checkout's untracked `.worktreeinclude` carries stale bg-lead lines (`.daedalus/config.json`, `.daedalus/plans/*.md`); the tracked file replaces it. The main checkout excludes it through `.git/info/exclude` line 22, so it is added with `git add -f`; other clones carry no such exclude.

The local settings files are untracked and never reach the pull request. Both copies (this worktree's and the main checkout's) are updated so daedalus keeps loading once the tracked settings stop enabling it. The main checkout's copy is updated before merge; if the worktree fence refuses that edit, the operator gets the exact JSON to paste.

## Files

- `.claude/settings.json`
- `.claude/settings.local.json`
- `.worktreeinclude`
- `.gitignore`
- `CLAUDE.md`

Outside the pull request (untracked, main checkout, operator-side if the fence refuses): `/Users/ckrough/Code/evermore/.claude/settings.local.json`, and removal of line 22 (`.worktreeinclude`) from `/Users/ckrough/Code/evermore/.git/info/exclude`.

## Work order

1. Update the untracked local settings with the Edit tool (Bash writes to both paths are sandbox-denied): in this worktree's `.claude/settings.local.json` and in the main checkout's copy, add `extraKnownMarketplaces` with `backchain` (`backchainai/daedalus`) and `astral-sh` (`astral-sh/claude-code-plugins`), remove `context7@claude-plugins-official`, and keep the other enabled plugins and `permissions.additionalDirectories`. If the main-checkout edit is refused, hand the operator the full JSON, along with removing line 22 of the main checkout's `.git/info/exclude`. Check: `jq` parses both files and shows the expected keys. No commit (untracked).
2. Edit `.claude/settings.json` to drop `daedalus@backchain`, `backchain`, and `astral-sh`; reword the `.gitignore` comment that says the tracked settings enable daedalus; add a tracked `.worktreeinclude` listing `.claude/settings.local.json` with a one-line comment, staged with `git add -f`. Check: `make check` exits 0 and the settings assertions in Verification pass. Commit.
3. Add a "Claude Code configuration" bullet under CLAUDE.md `## Working conventions`: the tracked `.claude/settings.json` holds only public plugins and the deny list; daedalus, github, and astral are enabled per clone in the gitignored `.claude/settings.local.json`, which also declares the `backchain` and `astral-sh` marketplaces; the tracked `.worktreeinclude` copies that file into every worktree Claude Code creates (`claude --worktree`, EnterWorktree, subagent worktree isolation), and a worktree made with `git worktree add` needs it copied in by hand. Check: `make check` exits 0. Commit.

## Tests

No code changes, so no unit tests. The `jq` assertions and the headless session check in Verification prove the configuration.

## Verification

- `make check` exits 0.
- `jq -e '.enabledPlugins | has("daedalus@backchain") | not' .claude/settings.json`, `jq -e '.extraKnownMarketplaces | (has("backchain") or has("astral-sh")) | not' .claude/settings.json`, and `jq -e '.enabledPlugins["supabase@claude-plugins-official"] and .extraKnownMarketplaces["claude-plugins-official"]' .claude/settings.json` each exit 0.
- `diff <(git show origin/main:.claude/settings.json | jq -S .permissions) <(jq -S .permissions .claude/settings.json)` exits 0.
- `jq` on both local settings files shows the two marketplaces, daedalus, github, and astral enabled, and no context7.
- `git ls-files .worktreeinclude` prints the file.
- `claude -p "ok" --output-format stream-json --verbose` in this worktree emits a `system`/`init` event whose `plugins` array includes `daedalus`.
- After merge, the operator deletes the main checkout's untracked `.worktreeinclude` before pulling, so its stale bg-lead lines are not lost unnoticed, then a fresh session on main prints the daedalus SessionStart status.

## Experiments

No experiment warranted: `extraKnownMarketplaces` and `enabledPlugins` are valid in any settings scope per the Claude Code settings docs. The headless check proves daedalus loads, but the `backchain` marketplace is already registered at user level on this machine, so it does not on its own prove the local `extraKnownMarketplaces` declaration works for a fresh clone.

## Architect review

- Important: two Verification `jq -e` commands named no file and would read stdin; the `permissions.deny` check was visual -> amended: both name `.claude/settings.json`, and a `diff` of `.permissions` against `origin/main` replaces the visual check.
- Nit: the stated reason for deleting main's untracked `.worktreeinclude` was wrong (an ignored file is overwritten, not refused) -> amended: the reason is now preserving the stale lines visibly.
- Nit: `.git/info/exclude` line 22 goes stale once the file is tracked -> amended: removing it sits beside the main-checkout settings edit, operator-side.
- Nit: CLAUDE.md wording undersold coverage (EnterWorktree and subagent worktrees also copy) and named no single location -> amended: one "Claude Code configuration" bullet under Working conventions naming every creation path.
- Nit: Bash writes to `settings.local.json` are sandbox-denied -> amended: step 1 names the Edit tool.
- Nit: the headless check asked a model to judge plugin loading, and the Experiments line overclaimed -> amended: the check reads the `init` event's `plugins` array, and Experiments states what it does not prove.
- Nit: "the repository is public" might be wrong -> not amended, because `gh repo view backchainai/evermore --json visibility` reports `PUBLIC`.
