# Arrival seam (c)/(d) — worker proof

2026-09-23. The frontend fence uses `tests/fixtures/philo3_summary_wire.json`
from the summary detail producer. It covers imported duration/transcript, ready
summary and transcript, scheduled retry after its due time, terminal failure,
the three detail read cap, stale generation/identity, and a mismatched detail
identity named read error, and the running → ready → retrying → failed
desk_changed transition with durable receipt retention.

## Collection

`vitest list src/desk/chair/arrivalSummaryCompletion.test.tsx` collected eight
tests:

```text
renders imported duration and transcript from the producer detail
renders the ready summary and transcript from the producer detail
keeps a failed lineage as RETRYING after its scheduled time and names the producer cause
renders the terminal producer failure and keeps the named cause
reads only the top three visible meeting details per desk refresh
drops a stale response when the visible meeting identity changes
names a response whose identity does not match the requested meeting
refreshes running to ready to retry to failed from desk_changed and keeps durable receipts
```

## Post-fix focused run

```text
Test Files  4 passed (4)
     Tests  20 passed (20)
```

Command:

```text
PATH=/Users/karol/.nvm/versions/node/v22.21.0/bin:$PATH HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm ./node_modules/.bin/vitest run src/desk/chair/arrivalSummaryCompletion.test.tsx src/desk/chair/arrivalSummaryRun.test.tsx src/desk/chair/__tests__/drainerBadge.test.tsx src/desk/__tests__/deskChangedRefresh.test.tsx --maxWorkers=1
```

Typecheck passed with `npm exec tsc -- --noEmit`. `git diff --check` passed.

The required origin/main pre-fix run against the same real fixture is retained
in [pre-fix-real-fixture.txt](pre-fix-real-fixture.txt). It failed all seven
tests because the pre-fix adapter did not export `fromWireMeeting`.

The refreshed producer fixture carries planned routes and durable
`run_receipt.attempts` for the ready, retry and terminal-failure cases. The
adapter and Arrival read that durable field, and the post-run surface uses
`RunAttempts`; the optimistic Run response host is not rendered as an actual
contact. The imported and running fixtures correctly carry no executed receipt
yet.
