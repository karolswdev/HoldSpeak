# Evidence — HS-72-11 — Closeout: the one-spine proof

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable), owner-directed phase

## The matrix (one run, outputs verbatim)

```
3066 passed, 37 skipped, 1 warning in 210.90s (0:03:30)
== preflight+mermaid ==
7 passed in 65.58s (0:01:05)
== validate ==
RESULT: ALL CHECKS PASSED
== swift ==
	 Executed 413 tests, with 8 tests skipped and 0 failures (0 unexpected)
== sim build ==
** BUILD SUCCEEDED **
```

(The 7 e2e are the route pre-flight (2), the mermaid render guard (2), and
the live-bus proofs (3). The python suite internally carries the
tri-surface contract validation, the API-manifest snapshot, the migration
matrix, and the doc/density guards.)

## The cross-surface walk (live, scripted)

A note created through the REAL web desk UI (Playwright driving `/desk`'s
create flow against a live hub on a scratch DB) → the hub row persisted
with title AND tags intact (the HS-72-09 class of loss, absent) → the
sync wire (`GET /api/sync/pull`) validated against the note schema and
the full ChangeSet envelope from HS-72-01. Screenshot:
`screenshots/11-walk-web-note.png`. The iPad half of the walk
(record ↔ contract) is proven at the behavior level by
`DeskRecordsTests`' golden-fixture round-trips; the interactive
iPad leg is the owner's standing walk (below).

## Drift spot-checks (both red, reverted, green)

- Removed `"note"` from `SYNC_KINDS` → the schema-vs-hub AND
  Swift-vs-hub kind locks failed (2 failed).
- Added a scratch route without regenerating → the manifest snapshot
  failed with the regenerate hint (1 failed).
- Reverted; the two guard files re-run: **13 passed**.

## Closeout bookkeeping

- `final-summary.md` written; `current-phase-status.md` frozen at
  10/10; README "Current phase" + phase index advanced to CLOSED;
  push + PR + merge on green (the standing phase-close cadence).

## The standing owner walk (explicitly flagged, per the story's rule)

The one proof class this phase could not produce itself: the iPad on
real metal with existing on-device data — the legacy `@AppStorage`
decode in anger (HS-72-09's migration), plus coder-board and desk-relay
taps against the renamed routes (HS-72-03). Recorded here as the
phase's standing follow-up.
