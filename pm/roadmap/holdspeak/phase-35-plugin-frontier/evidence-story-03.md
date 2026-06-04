# Evidence — HS-35-03: Per-project plugin enable/disable

**Date:** 2026-06-03. **Story:** [story-03-per-project-enable-disable.md](./story-03-per-project-enable-disable.md).

## What shipped

A config-driven enable/disable that the dispatch layer honors — a disabled plugin is
**skipped, not failed**, and the *built* chain is unchanged.

- **Config knob** — `MeetingConfig.disabled_plugins: list[str]` (`holdspeak/config.py`),
  validated in `__post_init__` (must be a list of strings) and normalized in place
  (strip, dedupe, preserve order). Unknown ids are intentionally allowed — a harmless
  no-op at dispatch.
- **New `skipped` status** — added to `PLUGIN_RUN_STATUSES` (`plugins/contracts.py`),
  distinct from `blocked` (capability/actuator gate) and `error` (ran-and-failed).
  Synthesis already accepts only `{success, deduped}`, so a skipped run yields no
  artifact.
- **Dispatch gate** — `plugins/dispatch.py`: pure `normalize_disabled_plugins` +
  `partition_chain` helpers, and `dispatch_window`/`dispatch_windows` gain a
  `disabled_plugins` param. For each id in the built `RouteDecision.plugin_chain`, a
  disabled id is recorded as a zero-duration `skipped` `PluginRun` (carrying the
  plugin's real version) and **never invoked**; siblings run normally.
- **`router.py` is untouched** — `build_plugin_chain`/`preview_route` and
  `RouteDecision.plugin_chain` are unchanged, so the *built* chain (and
  `test_intent_dispatch.py`) stays byte-identical.
- **End-to-end wiring** — `disabled_plugins` threads `process_meeting_state` →
  `MeetingSession` (ctor `mir_disabled_plugins` + `stop()`) → `WebRuntime` passes
  `config.meeting.disabled_plugins`.
- **Telemetry** — `skipped` persists through `record_plugin_run` and surfaces verbatim
  on the existing `GET /api/meetings/{id}/plugin-runs` route; no new route.
- **Doc** — `docs/PLUGIN_AUTHORING.md` gained a "Disabling a plugin per project" note
  and the stale "next story" line was corrected.

## Tests

### New disable tests + routing/config regressions

```
$ uv run pytest -q tests/unit/test_plugin_disable.py tests/unit/test_intent_dispatch.py tests/unit/test_intent_contracts.py tests/unit/test_intent_pipeline.py tests/unit/test_intent_router.py tests/unit/test_config_intent_router.py
...
45 passed
```

`test_plugin_disable.py` (12 tests): `skipped` is a known status; the pure
`normalize_disabled_plugins`/`partition_chain` helpers (clean/dedupe, order-preserving,
unknown-id no-op, empty-is-identity); a disabled plugin recorded as `skipped` and never
invoked while siblings run; the skipped record carries the real plugin version; unknown
disabled id is a no-op; **default no-disabled is byte-identical** to the built chain;
and config validation (default empty, normalization, non-list / non-string rejection).
`test_intent_dispatch.py` (the built-chain constants) is **unchanged and green**.

### Doc drift-guard + link-check

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
...                                                                      [100%]
3 passed in 0.02s
```

### ruff on authored files

```
$ uv run ruff check holdspeak/plugins/dispatch.py holdspeak/plugins/pipeline.py holdspeak/plugins/contracts.py holdspeak/config.py tests/unit/test_plugin_disable.py
All checks passed!
```

(`meeting_session.py`/`web_runtime.py` carry a pre-existing F841/unused-import unrelated
to this change — confirmed present at HEAD; the repo is not ruff-clean repo-wide by
default rules, and my added lines introduce no new violations.)

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
...
2007 passed, 15 skipped in 49.04s
```

(+12 over HS-35-02's 1995.)

## Done-when verification

- [x] A config knob (`MeetingConfig.disabled_plugins`) suppresses specific plugin ids;
      dispatch records them as `skipped` (not failed); the status persists +
      surfaces on the plugin-runs route.
- [x] Default (empty list) behavior is byte-identical — `test_default_no_disabled_is_byte_identical`
      + `test_intent_dispatch.py` unchanged.
- [x] Routing tests cover enable/disable (`test_plugin_disable.py`); full suite green
      (2007 / 15).
