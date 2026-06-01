# HS-29-02 — Incident plugins (real run)

- **Project:** holdspeak
- **Phase:** 29
- **Status:** backlog
- **Depends on:** HS-28-01 (renderer registry)
- **Unblocks:** HS-29-05
- **Owner:** unassigned

## Problem

Two registered stubs cover incident reviews and are still `DeterministicPlugin`s:
`incident_timeline` (`incident_timeline`) and `runbook_delta` (`runbook_delta`).
Incident retros produce an ordered timeline and a set of runbook changes. Flip
both as one themed atomic chunk.

## Scope

### In

- Two real plugins (deferred, `required_capabilities=["llm"]`), registered in
  `_REAL_PLUGINS`:
  - `incident_timeline` → `{"events": [{"time"|null, "event"}]}` (ordered as given).
  - `runbook_delta` → `{"changes": [{"change", "type": "added"|"modified"|
    "removed", "detail"|null}]}` (type enum-coerced).
- A renderer + structured `/history` render for each (`incident_timeline`,
  `runbook_delta`).
- Unit + synthesis tests per plugin.
- A direct live `.43` Q6 check per plugin with an incident-flavored transcript,
  recorded in evidence. (Not added to the shared spoken e2e — its conversation is a
  product kickoff with no incident.)

### Out

- Severity scoring / MTTR math (later).
- Linking runbook deltas to an actual runbook file (later).

## Acceptance criteria

- [ ] Two real `run()`s return validated payloads; failure + capability-blocked
      covered.
- [ ] `register_builtin_plugins` returns the real classes; others unaffected. (No
      routing ripple — already on the incident chain.)
- [ ] Both artifact types render structured in `/history`.
- [ ] Tests green; full sweep green; each verified live on `.43` Q6.

## Test plan

- Unit: `tests/unit/test_incident_timeline_plugin.py`,
  `test_runbook_delta_plugin.py`.
- Synthesis: a body case per type in `test_artifact_synthesis_diagram.py`.
- Full sweep + direct live checks (incident transcript).

## Notes / open questions

- `incident_timeline` should preserve the order the model returns (the LLM orders
  chronologically); synthesis does not re-sort.
