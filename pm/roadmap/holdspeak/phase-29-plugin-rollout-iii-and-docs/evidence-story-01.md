# HS-29-01 Evidence — Delivery & product plugins (real run)

**Date:** 2026-06-01.
**Story:** [story-01-delivery-product-plugins.md](./story-01-delivery-product-plugins.md).

## Implementation Evidence

Three stubs flipped to real LLM-backed plugins (deferred, `["llm"]`), each the
Phase-16 pattern (strict prompt → fenced ```json → `_extract_*` → structured
output), registered in `_REAL_PLUGINS` (**10 real plugins now, 4 stubs**). **No
routing ripple** — all three were already on the delivery/product chains.

- **`dependency_mapper`** (`holdspeak/plugins/builtin/dependency_mapper.py`) →
  `{"dependencies": [{from, to, note|null}]}`; each edge needs both endpoints.
  Artifact `dependency_map`.
- **`scope_guard`** (`scope_guard.py`) → `{"findings": [{item, verdict, rationale|
  null}]}`; `verdict` enum-coerced `in_scope|out_of_scope|scope_creep`
  (`deferred`→out_of_scope, `creep`→scope_creep, unknown→in_scope). Artifact
  `scope_review`.
- **`customer_signal_extractor`** (`customer_signal_extractor.py`) → `{"signals":
  [{signal, type, quote|null}]}`; `type` enum-coerced `request|pain|praise|
  churn_risk` (`complaint`→pain, `churn`→churn_risk, unknown→request). Artifact
  `customer_signals`.

**Synthesis** (registry): `_dependency_body` (edge list), `_scope_body` (grouped
by verdict), `_customer_signal_body` (typed list) + `_render_dependencies` /
`_render_scope` / `_render_customer_signals` registered under `dependency_map` /
`scope_review` / `customer_signals`.

**Web render** (`history.astro` + `history-app.js`): `dependenciesFor` (from→to
list), `scopeFindingsFor` (+ `scopeVerdictLabel`, colour-coded verdict chips),
`customerSignalsFor` (typed chips). The raw-`body_markdown` fallback was
consolidated behind a new `hasStructuredRender(artifact)` helper (now 10 types) so
the binding stays maintainable. `(cd web && npm run build)` clean.

## Tests

- `tests/unit/test_dependency_mapper_plugin.py` (10), `test_scope_guard_plugin.py`
  (11), `test_customer_signal_extractor_plugin.py` (11): attributes, success +
  classification/coercion, item-without-required-field dropped, empty → failure,
  unparseable → failure, no-transcript, provider-exception, `_extract_*` /
  `_normalize_*` edge cases, registrar, capability-blocked.
- `tests/unit/test_artifact_synthesis_diagram.py` (+3): `dependency_map`,
  `scope_review`, `customer_signals` body cases; byte-for-byte default-body guard
  still passes.

```bash
uv run pytest -q tests/unit/test_dependency_mapper_plugin.py tests/unit/test_scope_guard_plugin.py tests/unit/test_customer_signal_extractor_plugin.py tests/unit/test_artifact_synthesis_diagram.py tests/unit/test_intent_dispatch.py   # 52 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                                                                                                                              # 2015 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

```
DEPS: 2 dependency edge(s) mapped.
   billing service → API contract frozen (cannot start until)
   GA → private beta finishing (depends on)
SCOPE: 3 scope finding(s); 1 flagged as scope creep.
   in_scope PDF export · scope_creep Live chat · out_of_scope SSO
SIGNALS: 5 customer signal(s) (3 request, 1 pain, 1 churn risk).
   pain Frustration with slow dashboard performance · churn_risk Risk of customer leaving · ...
```

## Live evidence (spoken e2e, extended)

The spoken e2e now runs **ten** real plugins and asserts all three new artifact
types + their `/history` renders (`.dependency-list`, `.scope-list`,
`.signal-list`). Refreshed `evidence/spoken_meeting_artifacts.png`.

```bash
HOLDSPEAK_SPOKEN_E2E=1 uv run pytest -q -m spoken_e2e -s
# 1 passed (artifacts: action_items, adr, customer_signals, decisions, dependency_map, diagram, milestone_plan, requirements, risk_register, scope_review)
```

## Result

Ten real plugins now. **Next: HS-29-02** (incident: `incident_timeline`,
`runbook_delta`), then comms, docs, close.
