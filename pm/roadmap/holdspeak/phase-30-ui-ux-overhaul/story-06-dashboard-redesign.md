# HS-30-06 — Dashboard (`index`) redesign

- **Project:** holdspeak
- **Phase:** 30
- **Status:** done
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

- [x] `index.astro` matches the IA-spec dashboard layout in Signal: dominant
      transcript column + an intel rail grouped under **Intelligence / Work /
      Operations** eyebrow labels — one designed surface, not 8 mismatched boxes.
- [~] Idle state verified on the running build (`evidence/after-hs06/dashboard.png`).
      active/stopping are driven by the **unchanged** `:class` binding + the
      updated state CSS (`state-active` → accent border + glow; `state-stopping` →
      warn border); not separately screenshotted — no live-meeting backend in this
      env (full state walk is part of HS-30-09's manual pass).
- [x] Alpine bindings intact **by construction**: no `x-*` attribute was touched —
      the redesign is CSS migration (local panel/hero/btn CSS → Signal) + inserted
      non-Alpine rail group-label divs. The page mounts and Alpine evaluates (idle
      render confirms).
- [x] Before/after: `evidence/before/before-runtime.png` → `evidence/after-hs06/dashboard.png`.
- [x] `npm run build` green; backend sweep green (2062 passed, 14 skipped).

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
