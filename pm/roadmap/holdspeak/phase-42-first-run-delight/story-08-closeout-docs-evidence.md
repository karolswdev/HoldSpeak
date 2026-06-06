# HS-42-08 — First-run evidence + docs closeout

- **Project:** holdspeak
- **Phase:** 42
- **Status:** backlog
- **Depends on:** HS-42-01 … HS-42-07
- **Unblocks:** none
- **Owner:** unassigned

## Problem

The phase closes when the guided first-run path is proven by real use, the
**TTFD** headline is captured on both platforms, the docs lead with the guided
path (not hand-edited JSON), and the tracking docs are reconciled.

## Scope

- In:
  - **The TTFD headline:** measured time-to-first-successful-dictation from a fresh
    clone, **zero file edits**, on macOS **and** Linux (to the extent hardware
    allows; structural where not) — the phase's before/after equivalent.
  - Docs lead with the guided path: install → launch → open Setup → first-dictation
    test → then choose intelligent typing / meeting / presence / companion.
    Demote hand-edited JSON/YAML from the primary path. Update
    `docs/GETTING_STARTED.md` + `docs/USER_GUIDE.md` + the docs index.
  - PixelLab provenance recorded; doc drift-guard + link-check green.
  - `final-summary.md`; README phase row → done + pointer advanced; HANDOVER refreshed.
  - Push + open a PR to `main`; merge when CI green.
- Out:
  - New surfaces — closeout is verification + record only.

## Acceptance criteria

- [ ] TTFD captured (fresh clone, zero file edits, macOS + Linux where possible) as
      the closeout headline, with evidence.
- [ ] Getting Started / User Guide lead with the guided path; no live doc makes
      hand-edited config the primary path; doc-guards + link-check green.
- [ ] Full suite green; all-optional-off default byte-identity re-asserted; no
      `_built/` tracked.
- [ ] `final-summary.md` exists; status frozen; README → done; HANDOVER updated;
      PR opened/merged.

## Test plan

- Full: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Docs: `uv run pytest -q tests/unit/test_doc_drift_guard.py`.
- Manual: the TTFD dogfood run(s).

## Notes / open questions

- Reuse the Phase-41 closeout pattern (live dogfood + flag/option-off byte-identity
  + final-summary).
