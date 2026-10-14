# Memory and History repair canvas

DRAFT — HOLD FOR SHIP. This composition follows the owner's approved
`SURFACE-REPAIR-2026-10-14.md`; root owns the combined review and delivery.

Run with the existing web Vite executable and this directory's
`vite.config.mjs`. Port: 24188. Artboards: `?face=memory` and `?face=history`.
Content is synthetic; the rows, verbs, filters and stream are production
components. The canvas was created before the composition edits.

Memory uses a wrapping `SurfaceLedgerRow`: Action, work title, known owner/date
or No owner/No date, the actual named meeting opener, and one next mutation.
The existing owner/date well remains below the row. Recent reads say Recent
work; empty REF and the device footer are omitted. Source projection uses the
existing meeting joins and recorded decision source only; it infers no segment
and merges no objects by title.

History includes the stored summary title, item id and type. Open switches to
Room and focuses that exact existing Plan node. Missing items have no Open.
Other reference openers retain their existing behavior.

## Focused proof

All runs used `.tmp/surface-audit/locked.py`, isolated HOME, machine state off,
Node 22 and `UV_NO_SYNC=1`.

- `.tmp/surface-audit/repair-memory/pytest-collect.log`: 7 named tests collected
  from `tests/unit/test_phase200_continuity.py` with `-k 'recall or owed'`.
- `.tmp/surface-audit/repair-memory/pytest.log`: those 7 passed, `-n 8
  --dist worksteal`.
- `.tmp/surface-audit/repair-memory/vitest.log`: 5 files, 64 tests passed,
  `--maxWorkers=2`: RecallFace, recallActionAndKinds, recentMemory202, Room model,
  and roomOpen.philo1306.

Actual isolated desk-sweep captures are in
`.tmp/surface-audit/repair-memory/`:

- `memory-recent-{1440,393}.png`: known owners and separate named sources;
  measured clipped, overlap and target faults all empty.
- `blocked-memory-{1440,393}.png`: actual searched results after REF changed to
  SURFACE ROLLBACK; the capture assertion stopped before clicking the source.
- `history-{1440,393}.png`, `history-search-{1440,393}.png`, and
  `history-item-open-{1440,393}.png`: stored title search and actual Open;
  focus id equals the producer's recorded item id at both widths. No console
  errors, clipped text, overlap or target faults in these History poses.
- `observations.json` and `observations-final.json`: exact observations;
  `capture.log` and `capture-final.log`: the two permitted capture attempts.

## Verification gap

The Memory capture incorrectly expected exactly two owed results. Existing
relationship recall also returned two other recorded commitments, so both
attempts stopped at that assertion. The second attempt waited for the actual
searched query before reading the results. This is a capture assumption, not
proof of a product failure. The named source click's destination is covered by
focused component tests, but the live Memory source click was not observed.
No third capture was run. No owner runtime, DB, model, microphone or terminal
was used.
