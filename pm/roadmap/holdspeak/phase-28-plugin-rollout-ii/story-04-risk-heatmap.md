# HS-28-04 — `risk_heatmap` real run (risk register)

- **Project:** holdspeak
- **Phase:** 28
- **Status:** backlog
- **Depends on:** HS-28-01 (registry)
- **Unblocks:** HS-28-05
- **Owner:** unassigned

## Problem

`risk_heatmap` is registered (`kind="synthesizer"`,
`artifact_type="risk_register"`) but is still a `DeterministicPlugin` stub. Risk
surfacing is cross-cutting — eng, delivery, and incident meetings all raise risks
("if the vendor slips we can't launch", "the migration could lose data"). A real
run captures each as a register row: impact, likelihood, mitigation, owner.

## Scope

### In

- Real `RiskHeatmapPlugin` (deferred, `required_capabilities=["llm"]`), registered
  in `_REAL_PLUGINS` in place of the stub. Mirror the proven pattern.
- Output: `{"summary", "confidence_hint", "active_intents", "risks": [{"risk",
  "impact": "low"|"medium"|"high", "likelihood": "low"|"medium"|"high",
  "mitigation": "or null", "owner": "or null"}]}`. Validate; `impact` /
  `likelihood` enums coerced to `medium` on unknown; success when ≥1 risk, else
  clean failure.
- Registry body (HS-28-01) for `risk_register` + `structured_json["risks"]`.
- Structured `/history` render: a risk table/list, each row showing impact +
  likelihood chips, mitigation, owner (`risksFor(artifact)` helper + `x-for`).
  Rebuild web.
- Unit + synthesis tests; extend the spoken e2e + screenshot.

### Out

- A literal 2D heatmap visual — v1 is a structured table (see status-doc deferred
  decision). The artifact type stays `risk_register`.
- Quantitative scoring / risk-exposure math — v1 is categorical low/medium/high.

## Acceptance criteria

- [ ] Real `run()` returns the validated `risks` payload; failure + capability-
      blocked paths covered.
- [ ] `register_builtin_plugins` returns the real class for `risk_heatmap`; others
      unaffected. (No routing ripple — already on the incident chain.)
- [ ] `risk_register` artifacts render structured in `/history`.
- [ ] Tests green; full sweep green; verified live on `.43` Q6.

## Test plan

- Unit: `tests/unit/test_risk_heatmap_plugin.py` (mock intel) — success, enum
  coercion, missing mitigation/owner → null, empty → failure, unparseable →
  failure, no-transcript, provider-raises, registrar, capability-blocked.
- Synthesis: a `risk_register` body case in `test_artifact_synthesis_diagram.py`.
- Full sweep; live `.43` against a risk-flavored transcript.

## Notes / open questions

- The plugin ID is `risk_heatmap` but the artifact type is `risk_register` (the
  existing `_ARTIFACT_TYPE_BY_PLUGIN` mapping) — keep that; don't rename either.
