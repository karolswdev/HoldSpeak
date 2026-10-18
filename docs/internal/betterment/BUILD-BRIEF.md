# Brief for a betterment build lane (shared by every builder)

You build one or two slices from a betterment RECIPE. Your prompt names the
recipe, the slices and your worktree name.

## Read first

- The slice text in `docs/internal/betterment/<cluster>/RECIPE.md`. It is
  your spec: Goal, Files, Changes, Done when, Tests, Not in this slice.
- The matching parts of that cluster's `DESIGN.md`, `RECON.md` and
  `MODEL.md`, for the why and the evidence.
- `docs/internal/betterment/PLAN.md` §2 (the product model) and
  `docs/internal/UX-CANON.md` if you touch a face.
- `CLAUDE.md`: the fast cycle, the test diet, the test lock, never the
  owner's real HOME, DB or Keychain.

Line numbers in a recipe are from 2026-10-17. Check them against
`origin/main` before you edit.

## How to work

1. Make your own worktree: `git worktree add ../wt-<name> -b <branch>
   origin/main`. Then `uv sync --extra dev` there ONLY. Run
   `npm ci` in `web/` only if `node_modules` is missing.
2. Build the slice: the smallest change that meets "Done when". Match the
   surrounding code. Do not take on the next slice.
3. Tests: the cheapest tier that proves it (T1 hub test, T2 vitest on
   recorded hub answers, a T4 browser test only for drag, focus, keys or
   geometry). Where you can, show that the new test fails on the old code.
   Every pytest or vitest run goes through
   `uv run python scripts/test_lock.py -- <cmd>` with `-n 8` for pytest.
   Run vitest from `web/` with `./node_modules/.bin/vitest`.
4. `scripts/quick_check.sh` must end GREEN.
5. Commit plainly, ending with
   `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`. Push, and open
   a PR whose body says what changed, how it was proven, and what was not
   verified, ending with
   `🤖 Generated with [Claude Code](https://claude.com/claude-code)`.
   **Do NOT merge.** The orchestrator reviews and merges.
6. Do not edit `pm/STATUS.md` or the betterment docs. Report instead.

## Final message

The PR URL; a diff summary; the exact test and quick-check results; what
was not verified; and anything that the recipe got wrong.
