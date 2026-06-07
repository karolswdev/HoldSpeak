# Evidence — HS-49-02: Transcript provenance ("show me the moment")

Write-once record of the provenance jump. The rule that matters: the affordance
appears only when a real `source_timestamp` resolves to a real transcript
segment — never a fake 0:00 — and the jump reveals that segment without stealing
focus. Read-only; built on data that already exists.

## What shipped

**Backend** (`holdspeak/meeting_aftercare.py`)
- `resolve_provenance_segment(segments, source_timestamp)` — the canonical seek
  target. Returns None (no affordance, honest) when the timestamp is
  missing/non-numeric or there are no segments. Otherwise picks the segment with
  the greatest `start_time` at or before the timestamp, clamped to the first
  segment, so a real `0.0` resolves to the opening segment rather than a fake
  jump. Returns `{source_timestamp, segment_index, segment_start, speaker,
  text_preview}`.
- The aftercare digest now threads provenance through the current meeting's
  segments (`MeetingState.segments`, already loaded by `get_meeting`): each open
  action item and each decision carries a resolved `provenance` (or null). The
  since-last-meeting `new_actions` carry it too; `closed_actions` (prior meeting)
  do not — their provenance would point at another meeting's transcript.
- No schema churn: decisions get the jump only where the `decisions` artifact
  already carries a `source_timestamp`; the common no-timestamp decision stays
  unlinked (honest), exactly the path the story preferred.

**UI** (`web/src/pages/history.astro` + `web/src/scripts/history-app.js`)
- `jumpToSegment(index)` — reveals + briefly flashes the transcript segment.
  **Focus-safe:** it `scrollIntoView`s the segment and toggles a flash class, but
  never calls `.focus()`, so it cannot steal keyboard focus from a live
  dictation/presence surface sharing the bundle. The flash self-clears after
  2.2s so a repeat jump re-triggers it; `prefers-reduced-motion` swaps the
  animation for a static outline.
- `jumpToMoment(ts)` mirrors the backend resolver client-side for the legacy
  intel action-item cards (which carry only the raw `source_timestamp`).
  `hasMoment(ts)` gates their button on a real timestamp + a loaded transcript.
- Transcript segments are now addressable (`:id="seg-${segIndex}"`) and flashable
  (`segment-flash` on the highlighted index).
- "Show me the moment" buttons sit on the aftercare open items, the aftercare
  decisions (when timestamped), and the action-item cards. The displayed label is
  the real recorded `source_timestamp` everywhere (the resolved segment is the
  jump *target*, not the displayed time), so the same item never shows two
  different times across surfaces.

## Tests (ran, read the output)

- `tests/unit/test_meeting_aftercare.py` — `resolve_provenance_segment` picks the
  segment at/before the timestamp, clamps a real 0.0 to the opening segment and a
  past-the-end timestamp to the last segment, and returns None for no-timestamp /
  no-segments; aftercare open items + decisions carry provenance only when the
  timestamp is real.
- `tests/integration/test_web_meeting_aftercare_api.py` — the API surfaces a
  resolved `provenance.segment_index` / `segment_start` for a timestamped open
  item (15.0 → the [10,30) segment, index 1).
- `uv run pytest -q -k "meeting or aftercare or transcript or action_item or artifact or proposal" --ignore=tests/e2e/test_metal.py`
  → **509 passed, 12 skipped** (pre-existing opt-in / missing-fixture e2e).

## Build + screenshots

- `(cd web && npm run build)` clean; `git ls-files holdspeak/static/_built` →
  empty (0 tracked; source-only).
- `scripts/screenshot_aftercare_provenance.py` boots the real server with a
  transcript + timestamped results.
  - `screenshots/story-02-provenance-buttons.png` — "Show me the moment · [1:12]"
    on the Priya open item, "[0:14]" on the Postgres decision, matching buttons on
    the action-item cards.
  - `screenshots/story-02-provenance-jumped.png` — after the jump, the justifying
    segment ("Priya [1:10] Yes — I'll wire it behind the feature flag.") is
    scrolled into view and flashed with the accent border.

## Honesty / invariants held

- Affordance shown only when a real timestamp resolves to a real segment; never a
  fake 0:00; decisions without a moment stay unlinked.
- Read-only and behavior-preserving: provenance is derived from existing
  `source_timestamp` + segment `start_time`; no new writes, no schema change, no
  change to capture/plugins/synthesis.
- Focus-safe: reveal + flash, never `.focus()`.
