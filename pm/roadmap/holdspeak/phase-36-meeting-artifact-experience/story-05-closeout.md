# HS-36-05 — Phase closeout + final-summary

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** HS-36-01, HS-36-02, HS-36-03, HS-36-04
- **Unblocks:** none
- **Owner:** unassigned

## Problem

Close Phase 36 cleanly: confirm the artifact experience is overhauled end-to-end (card
shell, copy-as-Markdown, per-type polish, no overflow), the bundle is rebuilt, the
spoken-e2e still passes, and write the phase `final-summary.md`.

## Scope

- **In:**
  - Final `cd web && npm run build`; confirm `holdspeak/static/_built/` committed and
    consistent with source.
  - Re-run the spoken-e2e for real to capture the **new** artifact look — both the
    incident-retro (`test_spoken_incident_retro_end_to_end`) and especially the new
    **dynamic/messy meeting** (`test_spoken_dynamic_meeting_end_to_end`, HS-36-04),
    which produces the densest, most varied artifact set — before/after screenshots into
    this phase's `evidence/`.
  - Confirm all spoken-e2e artifact selectors pass (preserved or updated in lockstep —
    not silenced).
  - `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.
  - `final-summary.md`; flip the project README phase row → `done` + Current-phase +
    Last-updated; refresh HANDOVER (tee up Phase 37 — Actuators).
- **Out:** new work; this is verification + record.

## Acceptance criteria

- [ ] Bundle rebuilt + committed; source/bundle consistent.
- [ ] Incident-retro spoken-e2e re-run for real; new-look screenshot(s) in `evidence/`;
      all artifact selectors pass.
- [ ] Full suite green.
- [ ] `final-summary.md` written; README phase row `done`; HANDOVER refreshed (Phase 37
      — Actuators teed up).

## Test plan

- `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- `HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s` (dangerouslyDisableSandbox
  to reach the LAN LLM) — incident-retro passes; screenshot shows the new cards.

## Notes / open questions

- The spoken-e2e screenshot dir is set per-active-phase; point the incident-retro
  screenshot at this phase's `evidence/` (or copy the produced PNG in).
