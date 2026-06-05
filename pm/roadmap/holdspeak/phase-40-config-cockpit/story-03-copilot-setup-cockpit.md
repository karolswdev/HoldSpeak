# HS-40-03 — Copilot Setup cockpit (UI)

- **Project:** holdspeak
- **Phase:** 40
- **Status:** backlog
- **Depends on:** HS-40-01
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Setting up the copilot today means hand-editing `config.json` (and knowing the
field names). Nobody wants that. The web UI already has a `/dictation` page with
readiness/runtime/blocks/KB sections, but the pipeline depth knobs aren't there
at all. This story makes the **whole dictation/copilot setup doable from the
UI** — rich, Signal-styled, readiness-driven, no file editing.

## Scope

- In:
  - Signal-styled controls in the dictation cockpit (`web/src/pages/dictation.astro`
    + `web/src/scripts/dictation-app.js`) for the pipeline + the new knobs:
    - `rewrite_passes` — a slider/stepper (1–5) with a "multi-pass refines your
      draft" affordance.
    - `corrections_enabled` — a toggle ("learn from my corrections this session").
    - `target_detect_llm_enabled` + `target_detect_llm_below` — a toggle + a
      threshold control ("infer the target when window detection is unsure").
    - The existing runtime/pipeline fields (`enabled`, `stages`,
      `max_total_latency_ms`, `target_profile_override`, backend/model) presented
      coherently in the same surface.
  - Wired to `GET`/`PUT /api/settings` (HS-40-01); **inline validation** mirroring
    the API bounds; optimistic UI with error surfacing.
  - **Readiness-driven**: the cockpit reads `/api/dictation/readiness` and shows
    what's configured / missing / next, with one-click fixes where they exist.
  - Rebuild the bundle: `cd web && npm run build`; **commit only `web/src`** (the
    `holdspeak/static/_built/` output is gitignored).
- Out:
  - Rebuilding the blocks / project-KB editors — **link/embed the existing ones**,
    don't reimplement.
  - The corrections + telemetry panels (HS-40-04).
  - Non-dictation settings.

## Acceptance criteria

- [ ] Every dictation/pipeline knob — including the four Phase-39 knobs — is
      settable from the UI and round-trips (set in UI → `PUT` → reload shows it).
- [ ] The UI is **rich Signal**, not flat: type-appropriate controls, states,
      affordances/help text; passes the `feedback_high_ui_standards` bar.
- [ ] Inline validation matches the API (rejects out-of-range before/at submit).
- [ ] The cockpit is readiness-driven (surfaces missing config + next steps).
- [ ] No JSON editing is required to fully configure the copilot.
- [ ] Bundle rebuilt; `git status` shows **no** `holdspeak/static/_built/`
      files staged; a screenshot of the cockpit is captured.

## Test plan

- Build: `cd web && npm run build` (must succeed).
- Integration: any settings round-trip still green
  (`tests/integration/test_web_dictation_settings_api.py`).
- Manual / screenshot: load `/dictation`, set each knob, confirm persistence;
  capture a screenshot for evidence.
- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- Use the **`ui-ux-pro-max`** skill (vendored at `.claude/skills/`) + Signal
  tokens. Reference the Phase-36 elevated-card patterns for the look.
- Default (status decision): **expand the existing `/dictation` page** rather
  than add a new route — it already hosts the readiness/runtime sections.
- The dry-run surface is the perfect "try it" companion to the cockpit — wire a
  "test this config" affordance to the existing dry-run.
