# HS-49-02 — Transcript provenance ("show me the moment")

- **Project:** holdspeak
- **Phase:** 49
- **Status:** backlog
- **Depends on:** HS-49-01
- **Owner:** unassigned

## Problem
Aftercare asks the user to trust a result enough to act on it ("file this", "this
is still open"). Trust is strongest when the result can point at the transcript
moment that justifies it. Action items already carry `source_timestamp`, but
nothing surfaces a "jump to that moment" affordance, and the link is invisible on
the aftercare surface.

## Scope
- **In:**
  - A **"jump to the transcript moment"** affordance wherever a real provenance
    timestamp exists: action items carry `source_timestamp` (a meeting-offset
    float); thread it onto the aftercare surface (HS-49-01) and the action-item
    cards, and open the transcript at that segment (`start_time`).
  - Where feasible **without schema churn**, extend the surface to decisions/other
    results that already carry a usable moment; otherwise leave them without the
    affordance (honest).
- **Out:** the aggregation (HS-49-01); actions-to-issues (HS-49-03); the draft
  (HS-49-04). This story makes provenance visible and navigable.

## Acceptance criteria
- [ ] A "jump to the transcript moment" control appears only when a real
      `source_timestamp` / segment range exists (hidden otherwise; never a fake
      0:00), and it scrolls/opens the transcript at that segment.
- [ ] The provenance comes from existing data (action-item `source_timestamp`,
      segment `start_time`); no fabricated linkage; behavior-preserving.
- [ ] Focus-safe; tests assert the affordance presence/absence + the seek target;
      `npm run build` ✓; 0 `_built/` tracked.

## Test plan
- Unit/integration: an action item with a `source_timestamp` exposes the jump
  target; one without does not; the seek maps to the right segment;
  `uv run pytest -q -k "meeting or aftercare or transcript or action_item"`.
- Manual + screenshot: click "show me the moment" on an open action, land on the
  segment.

## Notes / open questions
- Prefer the no-schema-churn path first (surface what already exists). Backfilling
  a transcript-moment link onto decisions is a schema touch; only do it if the
  value clearly warrants it (settle here).
- The transcript view already renders segments with `start_time`; reuse it as the
  seek target rather than building a new viewer.
- Keep it focus-safe (the standing dictation/presence invariant applies to any
  shared bundle): reveal/scroll, never steal keyboard focus.
