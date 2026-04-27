# HS-8-05 - Shared activity context for plugins

- **Project:** holdspeak
- **Phase:** 8
- **Status:** done
- **Depends on:** HS-8-03, HS-8-04
- **Unblocks:** usable recent work context
- **Owner:** unassigned

## Problem

Imported activity needs to be more than a standalone history feature. It
should be an active local data source available to HoldSpeak plugins
through a stable context contract, so future plugins can consume recent
work context without knowing Safari/Firefox schemas or ingestion details.

## Scope

- **In:**
  - Shared serializable activity context bundle.
  - Recent records, entity counts, domain counts, and source counts.
  - Plugin-host context provider support.
  - Default web-runtime registration of the activity context provider.
  - Dictation utterance contract support for activity context.
  - Tests proving any hosted plugin can receive activity.
- **Out:**
  - External sync.
  - Automatic Project KB mutation without user action.
  - Browser UI for recent activity records.
  - Manual project mapping rules.

## Acceptance Criteria

- [x] Activity can be serialized as a plugin-safe context bundle.
- [x] Any `PluginHost` plugin can receive activity through a context provider.
- [x] Web runtime registers the activity provider by default.
- [x] Dictation transducers have an activity context field.
- [x] No external network calls are required.
- [x] Focused and full tests pass.

## Test Plan

- `uv run pytest -q tests/unit/test_activity_context.py tests/unit/test_activity_entities.py tests/unit/test_activity_history.py tests/unit/test_db.py tests/unit/test_plugin_host.py tests/unit/test_dictation_contracts.py`
- `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`

## Evidence

- [evidence-story-05.md](./evidence-story-05.md)
