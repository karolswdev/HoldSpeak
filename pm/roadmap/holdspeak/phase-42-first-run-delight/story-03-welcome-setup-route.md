# HS-42-03 — Welcome / Setup route + CLI nudge

- **Project:** holdspeak
- **Phase:** 42
- **Status:** backlog
- **Depends on:** HS-42-01, HS-42-02
- **Unblocks:** HS-42-04
- **Owner:** unassigned

## Problem

A new or returning-but-broken user has no guided entrance — the dashboard shows
meeting UI at idle and `/dictation` opens to the expert **Blocks** tab. Onboarding
also starts in the terminal (`holdspeak` auto-opens the browser) with no pointer to
where to go.

## Scope

- In:
  - A Signal-styled first-run surface driven by `GET /api/setup/status`:
    `/` renders **setup-mode** when `overall == needs_attention|blocked` or
    `first_run`; `/setup` is the addressable full-checklist deep link. A healthy
    user's `/` yields to the normal dashboard instantly (no nag).
  - The surface: a plain-language headline ("Ready for voice typing" /
    "3 things need attention"), exactly **one** primary action, the checklist
    (Microphone, Hotkey, Text insertion, Transcription, Web runtime, Model/runtime,
    Privacy, Presence) with per-section status + fix + deep link, a local-only badge,
    and "Try first dictation" promoted to primary only when the core path is ready.
  - **CLI nudge:** `holdspeak`'s first terminal lines print the setup URL + a
    one-line readiness summary from the same status data
    (`Open http://127.0.0.1:PORT/setup — 3 things need attention`).
  - One restrained **PixelLab** visual (operator-at-terminal / local-cockpit scene);
    provenance in `docs/assets/pixellab/README.md`.
- Out:
  - The guided first-dictation flow itself (HS-42-04) — this story links to it.
  - The trust panel internals (HS-42-05) — the Privacy checklist row links to it.

## Acceptance criteria

- [ ] `/setup` renders the checklist from `/api/setup/status`; `/` shows setup-mode
      only when `needs_attention|blocked|first_run`, else the dashboard (a healthy
      user is **not** nagged) — proven by tests for both states.
- [ ] Exactly one primary action per state; each section shows status + fix + a
      working deep link.
- [ ] The CLI prints the setup URL + readiness summary on launch (using the same
      status source), verified by a test of the print path.
- [ ] One restrained PixelLab visual is present (no field wall, no raw doctor dump,
      no decorative overload); provenance recorded.
- [ ] Bundle rebuilt; only `web/src` committed; desktop + empty/fail/ready
      screenshots; a focus-order/contrast a11y check.
- [ ] Default suite green; default (healthy) path byte-identical to today's dashboard.

## Test plan

- Integration: `tests/integration/test_web_setup_route.py` (setup-mode vs dashboard
  by status).
- Unit: the CLI launch-nudge print path.
- Frontend: `cd web && npm run build && npm run shots`; Playwright for the three states.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- The "needs_attention" gate must be cheap (HS-42-01 guarantees the status read is
  cheap) so `/` stays fast for healthy users.
