# HS-29-04 Evidence — Public README + plugin docs

**Date:** 2026-06-01.
**Story:** [story-04-public-docs.md](./story-04-public-docs.md).

## What shipped

A new **"Meeting intelligence plugins"** section in the public `README.md`
(between "Where to go next" and "Configuration"):

- A how-it-works paragraph: saved/recorded meeting → transcript → MIR routing
  (intent scoring → per-profile plugin chain) → each plugin calls the configured
  OpenAI-compatible LLM → typed artifacts persisted + rendered **read-only** at
  `/history` (diagrams as SVG; others as structured lists/tables). Calls out the
  `llm` capability gate, saved-meetings-only scope, and the local/LAN egress
  posture.
- A **14-row table** of the built-in plugins: plugin ID → what it produces
  (artifact) → the profile/intent it fires on.
- A pointer to the plugin RFC (`docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`) and the
  Meeting Mode Guide.

## Accuracy cross-check (table vs code)

The table was built from the code, not memory:

- **Plugin IDs / count** — all 14 in `_REAL_PLUGINS`
  (`holdspeak/plugins/builtin/__init__.py`); `test_no_deterministic_stub_remains`
  proves all 14 are real.
- **Artifact types** — match `_ARTIFACT_TYPE_BY_PLUGIN`
  (`holdspeak/plugins/synthesis.py`): diagram, adr, requirements, action_items,
  milestone_plan, dependency_map, decisions, scope_review, customer_signals,
  incident_timeline, runbook_delta, risk_register, stakeholder_update,
  decision_announcement.
- **Profiles / intents** — match `router.py` (`PROFILE_PLUGIN_BASE_CHAINS` +
  `_INTENT_PLUGIN_CHAIN`): `decision_capture` on the default/balanced base chain;
  architecture/delivery/product/incident/comms chains as listed.
- Referenced docs exist: `docs/PLAN_ARCHITECT_PLUGIN_SYSTEM.md`,
  `docs/MEETING_MODE_GUIDE.md`.

No "coming soon" / stale claims — every listed plugin is shipped and real.

## Tests

Docs-only change (no code). Regression sweep still green:

```bash
uv run pytest -q --ignore=tests/e2e/test_metal.py   # 2062 passed, 14 skipped
```

## Result

The public README now tells users what HoldSpeak produces from a meeting — the
prerequisite the user set for publishing. **Next: HS-29-05** closes the phase (RFC
table → 14 ✅ / 0 ⚠️ + `final-summary.md`), after which we push.
