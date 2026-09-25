# PHILO-6-03 Arrival slot seam

Only the owner-authorized `chairhome.patch` is applied to ChairHome. Lane A owns reconciliation. This preparatory commit does not complete the story or claim placement.

Scoped chair run: 16 files / 93 assertions passed, but Vitest exits 1 with `TypeError: currentBucket is not iterable` from arrivalSummaryRun.test.tsx. The untouched d8f608c8 git archive reproduces the same 93 passes and the same unhandled error; raw logs and pinned archive provenance are beside this record. This is inherited test-double debt, not a green suite. Home: PHILO-6-03 placement-proof ledger; separate follow-up to repair the mock’s collection shape.

The focused ChairHome test capture follows verbatim.

# Evidence - PHILO-6-03

- **Story:** PHILO-6-03 - The toast that does not cover
- **Status:** in-progress
- **Date:** 2026-09-24

## Proof

### Captured run — 2026-09-25T04:25:00Z

- **Command:** `bash -c set -euo pipefail
export PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH
export HOME=$(mktemp -d)
cd web
./node_modules/.bin/vitest list src/desk/chair/ChairHome.test.tsx
./node_modules/.bin/vitest run src/desk/chair/ChairHome.test.tsx --maxWorkers=2`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 437406883fdc8f4f09697fd79249752a26703459

```text
src/desk/chair/ChairHome.test.tsx > Chair write recovery > keeps a failed generation actionable and clears the receipt after retry

 RUN  v4.1.9 /Users/karol/dev/tools/wt-philo-6-03/web


 Test Files  1 passed (1)
      Tests  1 passed (1)
   Start at  22:25:01
   Duration  929ms (transform 348ms, setup 59ms, import 463ms, tests 152ms, environment 179ms)
```
