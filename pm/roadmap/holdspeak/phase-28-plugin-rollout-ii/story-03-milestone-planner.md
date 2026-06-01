# HS-28-03 — `milestone_planner` real run (delivery)

- **Project:** holdspeak
- **Phase:** 28
- **Status:** backlog
- **Depends on:** HS-28-01 (registry)
- **Unblocks:** HS-28-05
- **Owner:** unassigned

## Problem

`milestone_planner` is registered (`kind="synthesizer"`,
`artifact_type="milestone_plan"`) but is still a `DeterministicPlugin` stub. It's
the delivery counterpart to `action_owner_enforcer`: planning and roadmap meetings
produce milestones with target dates, deliverables, and dependencies. A real run
turns "let's aim to ship the beta by Q3, after the API freezes" into a structured
plan.

## Scope

### In

- Real `MilestonePlannerPlugin` (deferred, `required_capabilities=["llm"]`),
  registered in `_REAL_PLUGINS` in place of the stub. Mirror the proven pattern.
- Output: `{"summary", "confidence_hint", "active_intents", "milestones":
  [{"name", "target": "date/timeframe or null", "deliverables": [str],
  "dependencies": [str]}]}`. Validate; success when ≥1 milestone, else clean
  failure. Empty `deliverables`/`dependencies` lists allowed.
- Registry body (HS-28-01) for `milestone_plan` + `structured_json["milestones"]`.
- Structured `/history` render: per milestone, name + target chip + deliverables
  list + dependencies list (`milestonesFor(artifact)` helper + `x-for`). Rebuild web.
- Unit + synthesis tests; extend the spoken e2e + screenshot.

### Out

- A Gantt / timeline visual — v1 is a structured list.
- Resolving dependencies against other artifacts or a real backlog (later).

## Acceptance criteria

- [ ] Real `run()` returns the validated `milestones` payload; failure +
      capability-blocked paths covered.
- [ ] `register_builtin_plugins` returns the real class for `milestone_planner`;
      others unaffected. (No routing ripple — already on the delivery chains.)
- [ ] `milestone_plan` artifacts render structured in `/history`.
- [ ] Tests green; full sweep green; verified live on `.43` Q6.

## Test plan

- Unit: `tests/unit/test_milestone_planner_plugin.py` (mock intel) — success,
  multi-milestone, missing-target → null, empty → failure, unparseable → failure,
  no-transcript, provider-raises, registrar, capability-blocked.
- Synthesis: a `milestone_plan` body case in `test_artifact_synthesis_diagram.py`.
- Full sweep; live `.43` against a planning transcript.

## Notes / open questions

- Keep `target` free-text (date or timeframe like "end of Q3") — don't force date
  parsing in v1.
