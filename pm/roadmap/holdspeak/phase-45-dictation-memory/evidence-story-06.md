# Evidence — HS-45-06: Closeout (dogfood + before/after + PR)

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-45-dictation-memory`.

## The no-mic dogfood

`scripts/dogfood_journal.py` drives the **real** journal HTTP surface end-to-end
(via the FastAPI TestClient — no port, no mic, no LAN-LLM, zero file edits):

```
$ uv run python scripts/dogfood_journal.py
HoldSpeak dictation-journal dogfood

1. record
  ✓ journaling is on (local, default)
  ✓ three dry-runs journaled (count=3)
  ✓ every entry tagged source=dry_run
2. review
  ✓ newest-first ordering
  ✓ per-stage latency captured
3. correct (the moment of truth)
  ✓ correction recorded + taught
  ✓ journal entry flipped to corrected
4. replay (prove it learned)
  ✓ replay routes to the corrected target
  ✓ replay reports the routing changed
  ✓ replay created no new row (it's a preview)
5. invariant: journal off ⇒ no new row, byte-identical output
  ✓ journal-off wrote no row
  ✓ typed output is byte-identical with journaling on vs off

JOURNAL DOGFOOD OK
```

The complete arc — **record → review → correct → replay** — plus the
byte-identical invariant, proven with no mic.

## Before / after

The "after" is captured live: `evidence/journal_timeline.png` (review),
`evidence/moment_of_truth.png` (correct), `evidence/replay_before_after.png`
(replay — target flips `terminal_shell → browser`). The "before" was the
*absence* of all of it (dictation evaporated the instant it typed; only an
in-memory correction ring + latency ring, gone on restart) — there was no
surface to screenshot. The contrast table is in `final-summary.md`.

## Invariants re-asserted

- **journal-off ⇒ byte-identical** — dogfood step 5: same dry-run text with
  `journal_enabled=false` writes **no** row and returns the identical `final_text`.
- **no transcript egress** — the journal is local SQLite; the repository +
  recorder make no network calls; the dogfood completes with no outbound request.
- **focus-safe** — the in-moment fix + replay re-insert never `autofocus` or
  call `.focus()` (asserted in HS-45-03/04 page-content tests).

## Suite + hygiene

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2363 passed, 17 skipped
```

**0** `holdspeak/static/_built/` tracked. `final-summary.md` written; the phase
flips to **CLOSED ✅ (6/6)**; the roadmap README (phase-index status +
current-phase + last-updated) reflects it. PR to `main` opened (merge when CI
green).
