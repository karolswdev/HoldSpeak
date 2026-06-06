# HS-42-03 — Welcome / Setup route + CLI nudge

- **Project:** holdspeak
- **Phase:** 42
- **Status:** done (2026-06-06)
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

- [x] `/setup` renders the checklist from `/api/setup/status`; `/` redirects to
      `/setup` only when `first_run|blocked` (a healthy returning user — incl. one
      with mere WARNs — is **not** nagged) — proven live for both states. *(Chosen
      gate: `first_run || blocked`, not any `needs_attention`, to honor "never nag";
      a returning user with optional warnings keeps the dashboard.)*
- [x] Exactly one primary action per state; each section shows status + fix; the
      `primary_action.route` (`/setup#<id>`) anchors resolve.
- [x] The CLI prints the setup URL + readiness summary on launch (same status
      source), verified by tests of the print path.
- [x] One restrained PixelLab visual (the brand mark) + status glyphs only — no
      field wall, no raw doctor dump.
- [x] Bundle rebuilt; only `web/src` (+ `web/public/holdspeak-mark.png`)
      committed; a desktop screenshot of the needs-attention state captured.
      *(empty/fail-state screenshots folded into closeout HS-42-08.)*
- [x] Default suite green (**2291 passed, 16 skipped**); the healthy path is the
      unchanged dashboard.

## Test plan

- Integration: `tests/integration/test_web_setup_route.py` (setup-mode vs dashboard
  by status).
- Unit: the CLI launch-nudge print path.
- Frontend: `cd web && npm run build && npm run shots`; Playwright for the three states.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- The "needs_attention" gate must be cheap (HS-42-01 guarantees the status read is
  cheap) so `/` stays fast for healthy users.
