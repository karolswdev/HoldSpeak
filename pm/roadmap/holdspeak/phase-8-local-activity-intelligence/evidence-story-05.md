# HS-8-05 Evidence - Shared Activity Context for Plugins

## Shipped Result

HS-8-05 promotes the Phase 8 activity ledger from a standalone browser
history feature into a shared local context source for plugins.

The implementation adds `holdspeak/activity_context.py` with:

- `ActivityContextBundle`, a serializable plugin-safe data shape
- recent activity records
- entity, domain, and source counts
- optional project scoping
- optional one-shot refresh from browser history readers
- `ActivityContextProvider`, a callable provider for plugin hosts

`PluginHost` now supports registered context providers. Before a hosted
plugin runs, the host enriches the plugin context with provider output,
so any MIR-style plugin can read `context["activity"]` without knowing
Safari, Firefox, SQLite, or checkpoint details.

The web runtime registers an `ActivityContextProvider` by default with a
one-shot refresh, making local activity available to hosted plugins
during normal runtime use.

Dictation transducers now have an `Utterance.activity` field. The live
controller populates it from the current local ledger without refreshing
browser databases on every utterance.

## Context Shape

The plugin-facing bundle contains:

- `records`
- `entity_counts`
- `domain_counts`
- `source_counts`
- `generated_at`
- `project_id`
- `refreshed`
- `refresh_errors`

Records include URL/title/domain, browser source, visit count,
normalized first/last seen timestamps, entity type/id, and optional
project ID.

## Verification

```text
uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_db.py tests/unit/test_plugin_host.py tests/unit/test_dictation_contracts.py
83 passed in 1.65s
```

```text
uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
1136 passed, 13 skipped in 26.22s
```

```text
git diff --check
```
