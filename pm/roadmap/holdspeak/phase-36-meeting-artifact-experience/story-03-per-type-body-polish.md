# HS-36-03 — Per-artifact-type body polish

- **Project:** holdspeak
- **Phase:** 36
- **Status:** not-started
- **Depends on:** HS-36-01
- **Unblocks:** none
- **Owner:** unassigned

## Problem

With the card shell (HS-36-01) in place, each artifact *body* still uses its original
flat markup. To make the output feel designed (not a dump), each renderer's body needs
the Signal treatment: typed status colors, iconography, spacing, and density tuned per
type.

## Scope

- **In:** A polish pass over each artifact body in `web/src/pages/history.astro`
  (within the new card shell), covering all current types:
  - `incident_timeline` — a real timeline (time rail + event), not a bare `<ol>`.
  - `runbook_delta` — added/removed/modified changes with typed color + icon.
  - `risk_register` — a designed table (or card grid at narrow width): severity-colored
    impact/likelihood, readable mitigation column.
  - `stakeholder_update` — headline + highlights/risks/next-steps as labeled sections.
  - `decision_announcement` — title + audience chip + message, accent-styled.
  - `decisions` / open-questions, `requirements` (typed badges), `adr`,
    `milestone_plan`, `dependency_map`, `scope_review` (verdict colors),
    `customer_signals` (typed + quote), `action_items` (owner/due chips), `mermaid`.
  - Consistent empty/`—` states, consistent chip/badge styling from the token set.
  - Rebuild + commit the bundle.
- **Out:**
  - Card shell + overflow (HS-36-01) and copy (HS-36-02).
  - Changing artifact data or adding new types.

## Acceptance criteria

- [ ] Every listed artifact type's body has been restyled with Signal tokens (typed
      colors, icons, spacing) — no remaining flat/default-looking body.
- [ ] Asserted inner selectors still resolve (or e2e updated in lockstep).
- [ ] Narrow-viewport behavior holds (no overflow regressions).
- [ ] `cd web && npm run build` + committed; suite green.

## Test plan

- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` — green.
- Manual: rebuild; review each artifact type rendered (use the incident-retro meeting
  for incident+comms types; the existing balanced/architecture/delivery/product meeting
  for the rest). Screenshots for the closeout.

## Notes / open questions

- Reuse the type→color map from HS-36-01.
- If a type has no live sample data handy, render it from a saved meeting or a fixture;
  don't guess the data shape — read the synthesis renderer in
  `holdspeak/plugins/synthesis.py` for the exact `structured_json` keys.
