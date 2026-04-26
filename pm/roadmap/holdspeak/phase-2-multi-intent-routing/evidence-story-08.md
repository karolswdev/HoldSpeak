# Evidence — HS-2-08 (API + CLI surfaces)

**Story:** [story-08-api-cli.md](./story-08-api-cli.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `tests/integration/test_web_intent_timeline_api.py` (new, 6 cases) —
  exercises `/api/meetings/{id}/intent-timeline` + `/plugin-runs` +
  `/artifacts` against a `MeetingWebServer` with `TestClient` over
  a seeded sqlite DB. Covers happy-path payload shape, 404 on
  unknown meeting, plugin-run filter by `window_id`, and lineage
  round-trip on artifacts.
- `tests/integration/test_web_intent_controls.py` (new, 8 cases) —
  exercises the four `/api/intents/*` control endpoints in two
  flavors: callback-unset → `501` for mutations + safe defaults for
  GET; callback-wired → invokes the callback with the right shape
  and surfaces the result.
- Bug fix in `holdspeak/plugins/pipeline.py` — lazy-import
  `build_intent_windows` inside `process_meeting_state` to break the
  `plugins/__init__.py` ↔ `intent_timeline.py` circular load.
  Comment added explaining the cycle.

## Why this story is mostly tests

The endpoints + CLI subcommand all already existed:

- Web (`holdspeak/web_server.py`):
  - `GET /api/intents/control` (line 486)
  - `PUT /api/intents/profile` (line 505)
  - `PUT /api/intents/override` (line 522)
  - `POST /api/intents/preview` (line 539)
  - `GET /api/meetings/{id}/intent-timeline` (line 1261)
  - `GET /api/meetings/{id}/plugin-runs` (line 1313)
  - `GET /api/meetings/{id}/artifacts` (line 1360)
- CLI (`holdspeak/commands/intel.py`): `_run_mir_route_command`
  with dry-run + reroute + persist (line 139).

What spec §9.8 asked for and was actually missing: the two
integration test files. Writing them flushed out the
circular-import bug.

## Test output

### New integration tests

```
$ uv run pytest tests/integration/test_web_intent_timeline_api.py -q
......                                                                   [100%]
6 passed in 0.49s

$ uv run pytest tests/integration/test_web_intent_controls.py -q
........                                                                 [100%]
8 passed in 0.20s
```

### Spec §9.8 verification gates

```
$ uv run pytest -q tests/integration/test_web_intent_timeline_api.py -m requires_meeting
6 passed in 0.50s

$ uv run pytest -q tests/integration/test_web_intent_controls.py -m requires_meeting
8 passed in 0.20s

$ uv run pytest -q tests/unit/test_intel_command.py
7 passed in 0.16s
```

The fourteen new cases:

**`test_web_intent_timeline_api.py`**
1. `test_intent_timeline_endpoint_returns_windows_and_transitions` — windows shape + intent_scores + transitions array.
2. `test_intent_timeline_endpoint_404_for_unknown_meeting`
3. `test_plugin_runs_endpoint_returns_persisted_runs` — both success and deduped statuses surfaced; output payload preserved.
4. `test_plugin_runs_endpoint_filters_by_window_id`
5. `test_artifacts_endpoint_returns_artifacts_with_lineage` — all 4 source rows (2 intent_window + 2 plugin_run) present.
6. `test_artifacts_endpoint_404_for_unknown_meeting`

**`test_web_intent_controls.py`**
1. `test_intent_controls_get_returns_safe_default_when_callback_unset`
2. `test_intent_profile_put_returns_501_when_callback_unset`
3. `test_intent_override_put_returns_501_when_callback_unset`
4. `test_intent_preview_post_returns_501_when_callback_unset`
5. `test_intent_controls_get_invokes_callback_and_returns_payload`
6. `test_intent_profile_put_invokes_callback_with_profile_string`
7. `test_intent_override_put_invokes_callback_with_intent_list`
8. `test_intent_preview_post_invokes_route_preview_callback` — verifies all 7 kwargs (profile/threshold/intent_scores/override_intents/previous_intents/tags/transcript) reach the callback.

### First-pass failures + the real bug

1. `MeetingWebServer.__init__()` requires `on_bookmark`, `on_stop`,
   `get_state` — added no-op fixtures.
2. **Real bug**: timeline endpoint returned `500` with
   `cannot import name 'build_intent_windows' from partially
   initialized module 'holdspeak.intent_timeline'`. Trace:
   `intent_timeline` imports `IntentWindow` from
   `plugins.contracts` → loads `plugins/__init__.py` → loads
   `pipeline.py` → tries to import `build_intent_windows` from the
   still-loading `intent_timeline`. Fix: lazy-load
   `build_intent_windows` inside `process_meeting_state`. Lesson
   logged in story Notes: integration tests through the real entry
   points catch import-graph regressions that module-scoped unit
   tests miss.

## Regression sweep

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
954 passed, 12 skipped in 17.77s
```

Pass delta vs. HS-2-07 baseline (940): **+14** (6 timeline + 8 controls).
Skip count unchanged at 12.

## Acceptance criteria — re-checked

All 7 checked in [story-08-api-cli.md](./story-08-api-cli.md).

## Deviations from plan

- CLI subcommand additions (`holdspeak meeting timeline`) deferred —
  the existing `holdspeak intel route` subcommand already satisfies
  spec §9.8 line 2, and MIR-A-008 says docs/examples should lead with
  web flows, not TUI. Documented in story Notes.
- Web UI HTML/JS controls deferred — the JSON contract is tested;
  UI rendering is its own concern and best done in HS-2-11 (DoD
  sweep) where the user can verify the look + flow once.

## Follow-ups

- Optional CLI extension: `holdspeak meeting timeline <id>` /
  `meeting artifacts <id>` mirroring the API endpoints for
  TUI-only workflows. Additive, low-risk.
- Web UI controls (profile selection, route preview, manual
  override) — HTML/JS in `holdspeak/static/dashboard.html` against
  the now-tested endpoints. Best done as part of HS-2-11 with the
  user in the loop.

## Files in this commit

- `holdspeak/plugins/pipeline.py` (bug fix: lazy import + comment)
- `tests/integration/test_web_intent_timeline_api.py` (new, 6 cases)
- `tests/integration/test_web_intent_controls.py` (new, 8 cases)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/story-08-api-cli.md`
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/evidence-story-08.md` (this file)
- `pm/roadmap/holdspeak/phase-2-multi-intent-routing/current-phase-status.md`
- `pm/roadmap/holdspeak/README.md`
