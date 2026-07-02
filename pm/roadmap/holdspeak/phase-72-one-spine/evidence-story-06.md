# Evidence — HS-72-06 — Split the meetings god-module

- **Shipped:** 2026-07-02
- **Commit:** this commit (branch `phase-72-one-spine`)
- **Owner:** agent (Fable) + a delegated mechanical-split agent, verified here

## The split

`holdspeak/web/routes/meetings.py` (1,855 lines at phase open; 1,424 after
HS-72-03/04 carved out the relay and the lifecycle) is now a package —
every file under the post-Phase-63 budget (≤650):

| File | Lines |
|---|---|
| `meetings/__init__.py` (the `build_meetings_router` façade) | 44 |
| `meetings/_shared.py` | 24 |
| `meetings/action_items.py` | 358 |
| `meetings/aftercare.py` | ~350 |
| `meetings/crud.py` | 192 |
| `meetings/insights.py` | 161 |
| `meetings/intel.py` | ~187 |
| `meetings/live.py` | 152 |
| `meetings/speakers.py` | 133 |

`routes/__init__.py` and `web_server.py` unchanged — the package exports
the same `build_meetings_router(ctx)`. Handler bodies moved verbatim (the
only mechanical delta: relative-import dot depth, one level deeper).
`/api/meetings/facets` keeps its registration order before
`/api/meetings/{meeting_id}` (both in `crud.py`) — the FastAPI match-order
hazard checked explicitly.

## The route table is byte-identical

The regenerated manifest diff contains ONLY `"module"` field changes — all
33 meetings routes, redistributed exactly (action_items 7, aftercare 6,
crud 5, insights 3, intel 4, live 5, speakers 3); zero path/method/consumer
changes. The HS-72-02 guard is the identity proof the story demanded.

## A real bug the split surfaced (fixed + regression-locked)

`api_process_intel_jobs`'s `_on_meeting_ready` callback (HS-56-04: the
`aftercare_ready` broadcast when deferred intel completes) referenced
`get_database` with NO import in scope — in the old module too (verified:
no module-level db import; the neighbors' imports are function-scoped). The
callback NameError'd on every real invocation, so the aftercare-ready
event never fired through the intel-process path. Fixed with the
function-scoped import (house style) and locked by
`tests/unit/test_intel_process_aftercare_callback.py`, which drives the
callback through the real route and pins the broadcast.

Also removed: two dead bindings in `aftercare.py`
(`_actuator_result_event`, the `_execute_slack_proposal` wrapper) —
orphaned by HS-72-04's decision-route rewrite, kept verbatim by the split,
deleted here with grep proof of zero consumers.

## Verification artifacts

- Split agent's run: targeted slice **118 passed**; full suite
  **3062 passed, 37 skipped** (before the bug fix).
- Post-fix verification (mine): regression + api-surface + proposals +
  relay slice **26 passed**; full suite at ship: **3063 passed, 37 skipped,
  0 failures**.
- `wc -l`: every package file ≤650 (table above).

## Acceptance criteria — re-checked

- [x] `meetings.py` split under the module budget.
- [x] Route table byte-identical (manifest diff = module fields only).
- [x] Patch targets traced (none existed on `routes.meetings` after
      HS-72-03 moved `_GITHUB_RUNNER`; grep in evidence).
- [x] Module-budget documentation updated where it exists (the watch-item
      lived in an exploration-cited doc absent from `docs/`; the
      architecture story HS-72-10 records the new package shape).

## Deviations from plan

- The mechanical extraction was delegated to a subagent with exact rules
  (verbatim bodies, manifest-identity, budget, test gates) and verified
  here; the bug fix, dead-binding removal, regression test, and evidence
  are first-party. The split agent's honest reporting (the unused
  bindings, the latent NameError, the match-order hazard) is quoted in
  its output and was each independently verified before acting.

## Follow-ups

- `db/activity.py` (1,596 lines) remains the largest module in the repo —
  noted at scaffold as a non-story; candidate for a future phase.
