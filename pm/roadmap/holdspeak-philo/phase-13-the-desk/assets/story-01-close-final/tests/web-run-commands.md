# Web verification commands — B0 close, 2026-10-03

All commands ran in the closure worktree's `web/` directory, with a fresh
`HOME=$(mktemp -d)`, Node 22.21.0 first in PATH and
`npm_config_cache=/Users/karol/.npm`. No source or test changed between
attempts. The full Python run was active during these web runs.

1. `npx vitest run --reporter=json` → `web-vitest.json`, exit 1:
   3,257 passed, six failed. Stderr is `web-vitest-stderr.txt`.
   The supported baseline checker consumed that unaltered JSON:
   `uv run python scripts/check_web_baseline.py pm/roadmap/holdspeak-philo/phase-13-the-desk/assets/story-01-close-final/tests/web-vitest.json`.
   Its report is `web-baseline-initial.txt`: six names outside the baseline.
2. The five affected files were run serially, twice, with the exact command
   below. Both runs exited 0 with 90 passed, zero failed. Results and stderr
   are `web-serial-1.*` and `web-serial-2.*` (stderr has the `-stderr.txt` suffix).
3. The complete suite was then rerun with
   `npx vitest run --maxWorkers=1 --no-file-parallelism --reporter=json` →
   `web-vitest-final.json`, with `web-vitest-final-stderr.txt`.
   All 3,263 executed tests pass, but Vitest exits 1: `DeskApp.test.tsx`
   fails to load because its TrustWindow mock lacks `useTrustWindow`. The
   baseline checker exits 0 because it ignores suite-load errors. Both
   facts, rather than a green-suite claim, are retained in the canonical
   evidence. The same collection failure reproduces on exact main
   `050ce14d` in `baseline-deskapp.json` (exit 1, zero tests executed).

```sh
npx vitest run \
  src/desk/chair/arrivalAttention.test.tsx \
  src/desk/__tests__/phoneDoors.test.tsx \
  src/desk/components/DeskListView.test.tsx \
  src/desk/components/__tests__/workbenchAutomations.test.tsx \
  src/features/project-room/steward/__tests__/StewardPosture.test.tsx \
  --maxWorkers=1 --no-file-parallelism --reporter=json
```

The six failures are intermittent (class c: serial green twice). Resource
contention is a possible cause, not an established one. Their home is web
test timing/fixture maintenance in the five named files. The initial
failure record is retained; it is not overwritten by either serial run.
