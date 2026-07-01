# HS-71-08 — Closeout: the side-by-side, proven

- **Status:** todo
- **Priority:** HIGH (the gate)
- **Depends on:** HS-71-01 … HS-71-07
- **Evidence:** _(added at close)_
- **Phase-exit:** ships `evidence-story-08.md` **and** `final-summary.md`.

## Goal

Prove the phase's thesis: the web `/desk` now reads as the same world as the
iPad, and the whole diorama works end to end.

## Scope

- **The vibe test (the real bar):** a side-by-side of the iPad desk
  (`apple/.../2001-ipad-wide.png` or a fresh device shot) and the web `/desk`,
  seeded comparably. Record the honest read: at a glance of the atmosphere +
  floating objects + depth, do they read as one world? (AGENT-BRIEF §1.)
- **The full walk:** atmosphere → sprites → floating objects → drag-to-arrange
  (persists) → drag-to-file onto a zone (real `PUT`) → dive into the zone + back
  → Qlippy in the corner → tap-to-open. Screenshot the sequence on a seeded
  instance.
- **No dead doors / no regressions:** route pre-flight green (`/desk` swept, zero
  page errors); the two-mode cockpits (Home/Dictation/Meetings) unchanged.
- Full suite green (`uv run pytest -q --ignore=tests/e2e/test_metal.py`); `cd web
  && npm run build` clean; `web/public/desk/sprites/*` committed; `_built/`
  never committed.
- Cadence: story headers, this `current-phase-status.md`, the project
  `README.md`, POSITIONING.
- `final-summary.md` written; PR to `main` merged on green.

## Proof required

The side-by-side; the full-walk screenshot sequence; route pre-flight + zero
page errors; full suite count; the final summary.

## Done

_(filled at close)_
