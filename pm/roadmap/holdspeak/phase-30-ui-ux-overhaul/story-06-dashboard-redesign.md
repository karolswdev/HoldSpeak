# HS-30-06 — Dashboard (`index`) redesign

- **Project:** holdspeak
- **Phase:** 30
- **Status:** backlog
- **Depends on:** HS-30-04, HS-30-05
- **Unblocks:** HS-30-09
- **Owner:** unassigned

## Problem

`web/src/pages/index.astro` (~985 lines) is the flagship: the live meeting
runtime — meeting state (idle / active / stopping), the live transcript stream
with speaker pills + timestamps, the intelligence side rail (intel, devices,
topics, summary, action items, plugin jobs, intent routing), export controls, and
modals. It carries the most Workbench markup and the most information density.
Redesign it to the IA spec on the Signal foundation.

## Scope

### In

- Rebuild the `index.astro` layout to the HS-30-01 IA: meeting-state hero, the
  live transcript as the primary column, the intelligence rail as a coherent
  secondary region (not a stack of mismatched panels), export + bookmark + metadata
  controls placed per the IA.
- Apply Signal: depth/hierarchy to separate the live stream from the rail, the
  accent reserved for the primary meeting action and live indicators, dark-tuned
  speaker pills + status.
- Preserve all Alpine.js behaviour (`HoldSpeakDashboard()` from
  `web/src/scripts/dashboard-app.js`): live updates, copy-on-click, modals,
  export — restyle the markup, don't break the bindings or the API contract.
- Verify against a **running meeting** (live or seeded), not a static snapshot.

### Out

- Backend / WebSocket / API changes — markup + CSS only; bindings unchanged.
- Other routes (HS-30-07/08).

## Acceptance criteria

- [ ] `index.astro` matches the IA-spec dashboard layout in Signal; the live
      transcript and the intel rail read as one designed surface.
- [ ] All idle / active / stopping states render correctly (screenshots of each).
- [ ] Alpine bindings intact: live transcript append, copy-on-click, export,
      bookmark + metadata modals all still work (verified on the running app).
- [ ] Before/after screenshots in evidence.
- [ ] `npm run build` green; backend sweep green.

## Test plan

- Unit / backend: `uv run pytest -q --ignore=tests/e2e/test_metal.py`.
- Visual / manual: `npm run dev` (or the full runtime); drive a meeting through
  idle → active → stopping; screenshot each state + an active transcript with
  intel populated.
- Build: `npm run build` exit 0.

## Notes / open questions

- This is the highest-risk page (size + live bindings). If the diff gets
  unreviewable, split the rail into its own follow-up commit (document the split).
- Don't regress the live-status pulse / connection indicators.
