# Evidence - HS-146-06

- **Story:** HS-146-06 - The calendar book (thorough docs)
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-29T00:01:07Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_doc_drift_guard.py 2>&1 | tail -2 && grep -rn -i "calendar subscription\|one subscription\|single subscription" docs/*.md README.md | wc -l`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 9a44e3ee1897e1e99c3ecf1cacb9736f66bc0c95

```text
.........................                                                [100%]
25 passed in 0.54s
       0
```

## Orchestrator triage note

Captured: the doc-drift guard (25 passed — including the NEW
retirement fence `_RETIRED_CALENDAR_SINGULAR` and its nonvacuous
counterpart) and the grep proof (zero singular-subscription claims
across docs/ + README; internal historical phase docs exempt by the
guard's user-facing scoping). The worker's report carries the full
structure: the USER_GUIDE Calendars section (six subsections incl.
the snapshot walkthrough with UI labels verified against web/src at
named lines), the SECURITY egress table rewritten as two rows (ICS
sources + snapshot extraction), the ARCHITECTURE calendar-pipeline
section with every file anchor verified at HEAD, the trust-boundary
diagram gaining the calendar ICS arrow, and the entry points.

**One branch-new violation caught and fixed in-round:** the worker's
baseline-guard honesty check surfaced
`CalendarSnapshotReviewCore.tsx:57` inside product_copy's
(baseline-failing) violation list — story 07's catch-all "Failed to
parse extraction" carried none of the four failure facts. The
orchestrator fixed the copy ("Could not read events from this
screenshot. Nothing was written. Retry with a clearer capture." —
what failed / retained work / next action), verified the guard's
CalendarSnapshot entry is gone, reran the review-core vitest (8
passed) and rebuilt the bundle. The two baseline guards otherwise
carry identical violation lists before and after this story.
