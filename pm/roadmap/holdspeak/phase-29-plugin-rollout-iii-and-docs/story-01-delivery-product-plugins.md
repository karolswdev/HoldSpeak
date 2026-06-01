# HS-29-01 — Delivery & product plugins (real run)

- **Project:** holdspeak
- **Phase:** 29
- **Status:** done
- **Depends on:** HS-28-01 (renderer registry)
- **Unblocks:** HS-29-05
- **Owner:** unassigned

## Problem

Three registered stubs cover the delivery/product space and are still
`DeterministicPlugin`s: `dependency_mapper` (`dependency_map`), `scope_guard`
(`scope_review`), `customer_signal_extractor` (`customer_signals`). They fire on
planning and product meetings, which are common. Flip all three as one themed
atomic chunk.

## Scope

### In

- Three real plugins (deferred, `required_capabilities=["llm"]`), registered in
  `_REAL_PLUGINS`, mirroring the Phase-28 plugins:
  - `dependency_mapper` → `{"dependencies": [{"from", "to", "note"|null}]}`.
  - `scope_guard` → `{"findings": [{"item", "verdict": "in_scope"|"out_of_scope"|
    "scope_creep", "rationale"|null}]}` (verdict enum-coerced).
  - `customer_signal_extractor` → `{"signals": [{"signal", "type": "request"|
    "pain"|"praise"|"churn_risk", "quote"|null}]}` (type enum-coerced).
- A renderer in `synthesis._ARTIFACT_RENDERERS` + a structured `/history` render
  for each (`dependency_map`, `scope_review`, `customer_signals`).
- Unit + synthesis tests per plugin (success / failure / capability-blocked).
- A direct live `.43` Q6 check per plugin (theme-appropriate transcript), recorded
  in evidence. Add `dependency_mapper` / `scope_guard` / `customer_signal_extractor`
  to the spoken e2e (they fit the customer-feedback conversation).

### Out

- Graph visualization for `dependency_map` (a structured list is v1).
- The incident/comms plugins (HS-29-02/03).

## Acceptance criteria

- [x] Three real `run()`s return validated payloads; failure + capability-blocked
      covered. Enums coerced with safe fallbacks.
- [x] `register_builtin_plugins` returns the real classes; others unaffected. (No
      routing ripple — already on delivery/product chains.)
- [x] All three artifact types render structured in `/history`.
- [x] Tests green; full sweep green (2015 passed); each verified live on `.43` Q6.

## Test plan

- Unit: `tests/unit/test_dependency_mapper_plugin.py`,
  `test_scope_guard_plugin.py`, `test_customer_signal_extractor_plugin.py`.
- Synthesis: a body case per type in `test_artifact_synthesis_diagram.py`.
- Full sweep + spoken e2e (extended for these three).

## Notes / open questions

- Keep prompts strict + parsers defensive; reuse the fenced-JSON + enum-coerce
  shape from `risk_heatmap` / `adr_drafter`.
