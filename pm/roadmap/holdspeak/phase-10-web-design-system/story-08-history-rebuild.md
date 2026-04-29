# HS-10-08 - `/history` rebuild

- **Project:** holdspeak
- **Phase:** 10
- **Status:** done
- **Depends on:** HS-10-03, HS-10-04, HS-10-05
- **Unblocks:** HS-10-13
- **Owner:** karol

## Problem

`/history` is the long-tail review surface — meeting list, meeting
detail, action items, artifacts, exports, speakers, intel queue, and
the de-facto settings panel. Today's `history.html` renders these as a
mix of summary tiles and a tabbed inner panel; the visual weight does
not match the actual operator workflow (review a recent meeting, find
an action item, or export).

## Scope

- **In:**
  - Replace `holdspeak/static/history.html` with `web/src/pages/
    history.astro` (and any sub-pages needed for meeting detail —
    `history/[meetingId].astro`).
  - Meeting list as `ListRow`s with stable secondary lines (date, tags,
    candidate source, intel readiness pill).
  - Meeting detail layout: header (title, dates, status pills) + tabbed
    body for transcript, action items, artifacts, speakers, intel,
    exports.
  - Settings sub-surface remains under `/history` for this phase but
    uses the new component grammar.
  - Action item rows use `ListRow`; each row shows status, owner, due
    where present, and an inline-edit affordance consistent with the
    rest of the system.
  - Empty state for "no meetings yet" links to `/` (start a meeting)
    *and* `/activity` (saved candidates).
- **Out:**
  - Splitting settings to its own route (out of phase scope; tracked
    later if needed).
  - New export formats — those are phase-7 concerns and stay there.
  - Search/filter behavior changes beyond using the standard form
    controls.

## Acceptance Criteria

- [x] `/history` list renders cleanly with seeded data and with no
  data (empty state).
- [x] Meeting detail renders all current sub-views (transcript, action
  items, artifacts, speakers, intel, exports) with no regressions in
  the data each view shows.
- [x] Settings panel uses the new component grammar; all settings still
  function (smoke test in evidence).
- [x] No inline `<style>` in the rendered output.
- [x] Existing `/history`/`/api/history/...` API contracts unchanged.

## Test Plan

- Static surface integration test for `/history`.
- Manual smoke test of meeting detail with one seeded meeting.
- Manual settings round-trip: change a setting, reload, confirm
  persistence.

## Notes

Defer any "should settings be its own route?" debate to a later phase
— resolving it here would either bloat this story or split the work
across phases mid-flight.
