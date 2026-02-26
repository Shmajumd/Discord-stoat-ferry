---
name: ship
description: The ONLY way to commit code. Runs verification, audit, code review, second opinion, documentation, and commit in sequence. Adapted from HubSpot Health Hero's 7-step shipping gate for Python.
user_invocable: true
---

# /ship — The Only Way to Commit

Seven mandatory sequential steps. Do NOT skip any step. If a step fails, fix the issue and restart from Step 1.

## Step 1: Verify

Run the full verification suite. Stop on first failure.

```bash
uv run ruff check . && uv run ruff format --check . && uv run mypy src/ && uv run pytest
```

If anything fails: fix it, then restart from Step 1.

## Step 2: Audit

Grep the entire codebase for the pattern(s) just changed. Report any unaddressed instances of the same pattern.

Examples:
- Changed how masquerade colour is set? Grep for all masquerade usage.
- Changed error handling in one migrator? Check all migrators follow the same pattern.
- Changed a dataclass field? Check all usages.

If unaddressed instances found: fix them, then restart from Step 1.

## Step 3: Code Review Gate

Check the diff size:
```bash
git diff --stat HEAD
```

**If >20 lines of non-docs code changed:** mandatory code review.

Dispatch chain (use first available):
1. Invoke `superpowers:requesting-code-review`
2. Fallback: `Task(octo:personas:code-reviewer)`
3. Fallback: `Task(octo:skills:octopus-code-review)`

Fix all **Critical** and **Important** findings. Re-run Step 1 after fixes.

**Skip if:** <=20 lines changed OR docs-only changes.

## Step 4: Second Opinion

Same >20 line threshold as Step 3.

Categorize the changed files:
- **Security**: token handling, auth, permissions
- **Performance**: rate limits, async, caching
- **API**: Stoat API calls, Autumn uploads
- **Migration Logic**: parser, transforms, state management
- **General**: everything else

Use `mcp__second-opinion__get_default_opinion` with:
- personality: `honest`
- temperature: `0.3`
- Include the categorized diff and ask for focused review

Fix **Critical** issues. Re-run Step 1 after fixes.

**Skip if:** <=20 lines changed OR docs-only changes.

## Step 5: Documentation

Update these files as applicable:

| File | When |
|------|------|
| `CHANGELOG.md` | **Always** (Keep a Changelog format) |
| `docs/` pages | If user-facing behavior changed |
| `README.md` | If feature table or download links need updating |
| `pyproject.toml` version | If version bump needed (see below) |

**Version bump logic:**
- **Patch**: bugfix, small tweak
- **Minor**: new feature, new migration phase
- **Major**: breaking change, architecture overhaul
- **No bump**: docs-only, CLAUDE.md/rules, CI config (use `content:` commit prefix)

## Step 6: Commit and Push

1. Stage specific files only — **NEVER** use `git add -A` or `git add .`
2. Write a clear commit message (imperative mood, explain the *why*)
3. Include Co-Authored-By trailer:
   ```
   Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
   ```
4. Push to remote (if on a branch with upstream)

## Step 7: Report

Display:
- Commit hash
- Version (if bumped)
- Verification results (all green)
- Files changed count
- Brief summary of what shipped

## NEVERs

- **Never** skip code review for >20 lines of non-docs code
- **Never** use `git add -A` or `git add .`
- **Never** skip CHANGELOG update
- **Never** commit without passing Step 1 verification
- **Never** push without Co-Authored-By trailer
- **Never** bump version without checking previous version first
- **Never** amend a previous commit — always create a new one
