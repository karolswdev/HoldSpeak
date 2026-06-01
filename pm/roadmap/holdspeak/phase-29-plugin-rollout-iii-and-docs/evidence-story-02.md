# HS-29-02 Evidence — Incident plugins (real run)

**Date:** 2026-06-01.
**Story:** [story-02-incident-plugins.md](./story-02-incident-plugins.md).

## Implementation Evidence

Two incident stubs flipped to real LLM-backed plugins (deferred, `["llm"]`),
Phase-16 pattern, registered in `_REAL_PLUGINS` (**12 real plugins now, 2 stubs**).
**No routing ripple** — both already on the incident chain.

- **`incident_timeline`** (`holdspeak/plugins/builtin/incident_timeline.py`) →
  `{"events": [{time|null, event}]}`, preserved in the model's chronological
  order; accepts bare-string events. Artifact `incident_timeline`.
- **`runbook_delta`** (`runbook_delta.py`) → `{"changes": [{change, type, detail|
  null}]}`; `type` enum-coerced `added|modified|removed` (`changed`→modified,
  `deleted`→removed, unknown→modified). Artifact `runbook_delta`.

**Synthesis** (registry): `_incident_timeline_body` (ordered list, optional time
prefix) + `_runbook_delta_body` (grouped by Added/Modified/Removed) +
`_render_incident_timeline` / `_render_runbook_delta` registered under
`incident_timeline` / `runbook_delta`.

**Web render** (`history.astro` + `history-app.js`): `incidentEventsFor` (an `<ol>`
with monospace time markers), `runbookChangesFor` (typed change chips,
add=success/modify=warning/remove=danger); both folded into
`hasStructuredRender`. `(cd web && npm run build)` clean.

## Tests

- `tests/unit/test_incident_timeline_plugin.py` (10),
  `tests/unit/test_runbook_delta_plugin.py` (11): attributes, success +
  order/coercion, bare-string events, item-without-required-field dropped, empty →
  failure, unparseable → failure, no-transcript, provider-exception, `_extract_*`
  / `_normalize_type`, registrar, capability-blocked.
- `tests/unit/test_artifact_synthesis_diagram.py` (+2): `incident_timeline`,
  `runbook_delta` body cases; byte-for-byte default-body guard still passes.
- **Two pre-existing stub-representative tests repointed** to
  `stakeholder_update_drafter` (the remaining stub), since `incident_timeline` is
  now real — `test_plugin_host.py::test_builtin_plugins_register_and_execute` and
  `test_mermaid_architecture_plugin.py::test_register_builtin_plugins_uses_real_class`.

```bash
uv run pytest -q tests/unit/test_incident_timeline_plugin.py tests/unit/test_runbook_delta_plugin.py tests/unit/test_artifact_synthesis_diagram.py   # 36 passed
uv run pytest -q --ignore=tests/e2e/test_metal.py                                                                                                     # 2039 passed, 14 skipped
```

`ruff check` on changed files: **All checks passed!**

## Live evidence (real `.43` Q6)

Verified with an incident-retro transcript (these plugins are **not** in the
shared spoken e2e — its conversation is a product kickoff with no incident, per the
story scope):

```
TIMELINE: 4 timeline event(s).
   9:02 | Alerts fired for elevated 5xx errors after afternoon deploy
   9:10 | Bad config change identified
   9:15 | Rollback executed
   9:20 | Recovery confirmed
RUNBOOK: 3 runbook change(s).
   added | Flush CDN cache after every deploy
   modified | Update rollback command
   removed | Remove manual database failover step
```

## Result

Twelve real plugins now; only the two comms drafters remain. **Next: HS-29-03**
(comms) takes it to fourteen real / zero stubs.
