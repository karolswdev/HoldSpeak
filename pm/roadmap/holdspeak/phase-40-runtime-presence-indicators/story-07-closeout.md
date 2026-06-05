# HS-40-07 — Closeout + Final Summary

- **Project:** holdspeak
- **Phase:** 40
- **Status:** done
- **Depends on:** HS-40-06
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The phase needs PMO closeout: evidence, docs, README status, and a final
summary. Without this, future agents will not know which desktop/web presence
states are canonical or what follow-ups remain.

## Scope

- **In:**
  - Update public/user docs that describe runtime, desktop presence, dictation
    status, and meeting status.
  - Update `pm/roadmap/holdspeak/README.md` and this phase's
    `current-phase-status.md`.
  - Write `final-summary.md`.
  - Record follow-up candidates: tray icon, deeper desktop preferences, audio
    level meters, native controls, persistent activity history.
  - Run final backend, web, and desktop-host verification commands and paste
    actual output into evidence.
- **Out:**
  - Shipping new indicator functionality beyond small closeout fixes.

## Acceptance Criteria

- [x] All story statuses and evidence links are current.
- [x] `final-summary.md` states whether the phase goal was met and names
      residual risks/follow-ups.
- [x] User-facing docs accurately describe desktop presence and web fallback.
- [x] Final verification output is captured in evidence.
- [x] PMO contract can be honestly certified for the closeout commit.

## Test Plan

- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Web: run the documented web build/test/screenshot commands.
- Desktop: run host fixture/smoke command on available GUI platform(s).
- Docs: run existing doc drift/link-check tests.

## Notes / Open Questions

- 2026-06-05: closeout written in [final-summary.md](./final-summary.md).
  Interactive native GUI smoke and focus evidence are captured in Story 06
  evidence.
- This is where to decide whether the next phase should pursue a persistent
  tray icon/menu, richer desktop controls, or stay with transient presence only.
