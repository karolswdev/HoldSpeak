# HS-171-06 — The Monday brief recurring

- **Project:** holdspeak
- **Phase:** 171
- **Status:** done
- **Depends on:** HS-171-02
- **Unblocks:** HS-171-08
- **Owner:** unassigned

## Problem

The Monday brief ran once (2026-08-24, 1839 items) and never again. The
cadence tick already calls `_maybe_push_daily_brief` (runtime/cadence.py:
62) which pushes to Telegram, but the brief itself is not regenerated
automatically. The MondayBriefService (services/monday_brief_service.py)
has a `generate` method (line 110) but it is only called on explicit API
request (`/api/brief`). The brief should regenerate on its own cadence
loop and land in the shade.

## Scope

- In:
  - The Monday brief regenerates on its own cadence loop (one loop per
    day, after quiet hours, triggered by the cadence tick).
  - The regenerated brief is stored and served by the existing
    `GET /api/brief` route (monday_brief.py:53).
  - The shade shows the most recent brief as a row in the PROJECTS
    section or a dedicated BRIEF section (per the HS-171-01 artboard).
  - The brief's cadence loop respects quiet hours (existing config).
  - The brief regeneration is receipted (Article XI.2).
- Out:
  - Changing the brief's collection logic (the five collectors in
    MondayBriefService stay as-is).
  - Per-project briefs (the brief is desk-wide).
  - Sending the brief externally (the Telegram push exists but is
    a separate concern).

## Acceptance criteria

- [x] The brief regenerates once per day after quiet hours without the
      owner opening the desk; verified by reading the `monday_briefs`
      table timestamp (Article IX.1).
- [x] The shade shows the most recent brief (date, item count, a verb
      to open the full brief); the row is omitted when no brief exists
      (UX-CANON.md rule A.8).
- [x] Quiet hours suppress the regeneration until the window closes.
- [x] The regeneration leaves a pipeline_events receipt (Article XI.2).
- [x] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k brief_recurring`
  - The cadence tick triggers brief regeneration when the last brief
    is older than 24 h.
  - The cadence tick does NOT regenerate when the brief is fresh.
  - Quiet hours suppress the regeneration.
- Integration: the rig boots a hub, waits for a cadence tick past the
  brief interval, asserts a new brief row in the DB.
- Manual: the shade on his desk shows the brief row.

## Notes / open questions

- The existing `_maybe_push_daily_brief` (runtime/cadence.py:62-90)
  already has the daily-push logic and quiet-hours check. The missing
  piece is calling `MondayBriefService.generate()` inside it. This may
  be a small change.

## Proof (2026-09-05)

tests/unit/test_hs171_aggregate_notify.py (one generate across the quiet-hours boundary; suppressed until the window closes; a pipeline_events receipt per regeneration) + tests/e2e/test_hs171_shade_glass.py::test_shade_brief_row_1440 (date · item count · Open).
