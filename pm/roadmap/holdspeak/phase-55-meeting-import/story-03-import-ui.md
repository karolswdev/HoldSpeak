# HS-55-03 — The /history import UI

- **Project:** holdspeak
- **Phase:** 55
- **Status:** done
- **Depends on:** HS-55-02
- **Unblocks:** HS-55-05, HS-55-06
- **Owner:** unassigned

## Problem
The archive lives on the user's disk; the API alone doesn't make importing a
product feature. `/history` needs an inviting, honest way in — not a bare file
input.

## Scope
- **In:**
  - An **"Import a recording"** affordance on `/history` (placement that reads
    as part of the surface, e.g. beside the list header), opening a
    Signal-styled panel: drag/drop + file picker, optional title, speaker
    label (defaulted honestly), tags; the plain-language notes — formats
    (ffmpeg needed for compressed), one speaker label (no diarization),
    audio not kept, everything local.
  - **Upload + progress:** POST to the import route; the meeting appears in
    the list immediately in its importing state with live progress (poll the
    status surface), resolving **in place** to a normal meeting card;
    failures render the honest detail with a remove affordance.
  - Focus-safe; reduced-motion-safe; `is:global` for any JS-rendered DOM per
    `docs/internal/ARCHITECTURE_WEB_FRONTEND.md`; additions to the uncarved
    `history.astro`/`history-app.js` kept lean and cohesive.
  - Page-content tests for the affordance + panel markers; screenshots
    committed (empty panel, importing state, resolved meeting).
- **Out:** redesigning `/history`; batch drag-drop of multiple files (one at
  a time in v1); facet UI (HS-55-04).

## Acceptance criteria
- [x] The affordance + panel ship with the honest notes; screenshot-verified
      (a class in the bundle ≠ it applies). (`story03-panel.png`, reviewed.)
- [x] A real upload through the browser lands a meeting that progresses and
      resolves in place without a manual refresh (Playwright evidence).
      (`dogfood_story03.py` — RESULT: PASS, zero page errors; importing pill
      + progress detail + in-place resolution screenshots committed.)
- [x] Failure state renders the actionable detail and can be removed.
      (Danger pill + detail; Remove placed outside the card button — valid
      HTML — confirming via holdspeakConfirm → DELETE; page-content locked.)
- [x] Page-content tests green; `npm run build` clean; 0 `_built/` tracked.
      (4 new locks; full suite 2562 passed, 17 skipped — see
      `evidence-story-03.md`.)

## Test plan
- Integration: page-content markers; the status-poll wiring against a fake
  slow import.
- Playwright evidence script (the dogfood pattern) with screenshots.
- Full suite (`uv run pytest -q --ignore=tests/e2e/test_metal.py`).

## Notes / open questions
- `ui-ux-pro-max` bar applies: this is a marquee affordance — make it feel
  like Signal, not a form. Check overflow with long filenames.
