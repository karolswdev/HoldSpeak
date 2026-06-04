# Evidence — HS-35-01: Public plugin-authoring guide (`docs/PLUGIN_AUTHORING.md`)

**Date:** 2026-06-03. **Story:** [story-01-plugin-authoring-guide.md](./story-01-plugin-authoring-guide.md).

## What shipped

A new public doc, `docs/PLUGIN_AUTHORING.md`, mirroring the shape of
`docs/CONNECTOR_DEVELOPMENT.md`, plus two wire-in links. The doc is grounded in a
direct read of the current code (file:line verified, not paraphrased from the RFC):

- **`HostPlugin` protocol** — `holdspeak/plugins/host.py:30` (`id`/`version` +
  `run(context: dict) -> dict`; `kind`/`execution_mode`/`required_capabilities`
  read via `getattr`, validated in `register()` at `host.py:171`).
- **Context dict** — assembled in `holdspeak/plugins/dispatch.py` (`transcript`,
  `active_intents`, `profile`, `meeting_id`, `window_id`, `tags`, `project`).
- **`kind` + actuator gate** — `host.py:192` (`_is_actuator_plugin`) / `host.py:354`
  (blocked unless `allow_actuators=True`); built-in kinds from
  `holdspeak/plugins/builtin/__init__.py`.
- **Execution mode** — `host.py:205` (`_is_deferred_plugin`: `inline` default,
  `deferred`/`queued`/`queue`/`heavy` queue).
- **`llm` capability gate** — `host.py:196` (`_missing_capabilities`) →
  `status="blocked"`; production resolution via
  `holdspeak/intel/providers.py:171` (`resolve_llm_capability`) →
  `holdspeak/web_runtime.py:145` (`enabled_capabilities={"llm"}`).
- **Reference run pattern** — `holdspeak/plugins/builtin/decision_capture.py`
  (prompt → `build_configured_meeting_intel()._chat_completion_text` → parse →
  success shape `confidence_hint=1.0` / failure shape `0.0`).
- **Synthesis renderers** — `holdspeak/plugins/synthesis.py`
  (`_ARTIFACT_TYPE_BY_PLUGIN`, `_ARTIFACT_RENDERERS`, the `_Rendered` tuple).
- **Chains** — `holdspeak/plugins/router.py` (`PROFILE_PLUGIN_BASE_CHAINS`,
  `_INTENT_PLUGIN_CHAIN`, `SUPPORTED_INTENTS`, `build_plugin_chain`) + the
  routing-ripple warning (HANDOVER §5).
- **Testing pattern** — `tests/unit/test_decision_capture_plugin.py` (the
  `intel_call` injection seam + the host-level `blocked` capability test).

Wire-in:
- `docs/README.md` — new "Plugin Authoring" entry in **Reference & integrations**.
- `README.md` — "Meeting intelligence plugins" section now points at the guide
  (was internal-RFC-only).

Code-fence note: three Python examples embed a literal ` ```json ` fence, so those
blocks use four-backtick outer fences to render correctly on GitHub.

## Tests

### Doc drift-guard + link-check (the story's named test)

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
...                                                                      [100%]
3 passed in 0.02s
```

(`test_no_live_doc_has_a_dangling_relative_link` is in this file — it green-lights
every relative link in the new doc; `test_drift_guard_actually_scans_docs` confirms
the scan is non-vacuous.)

Referenced code files confirmed to exist (link-check targets):

```
$ ls holdspeak/plugins/builtin/mermaid_architecture.py holdspeak/plugins/builtin/action_owner_enforcer.py
holdspeak/plugins/builtin/action_owner_enforcer.py
holdspeak/plugins/builtin/mermaid_architecture.py
```

### Full suite

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
...
1966 passed, 15 skipped in 51.28s
```

(Skips are the hardware/model-gated integration + mock-meeting-fixture tests, as
expected on a remote no-hardware session.)

## Done-when verification

- [x] `docs/PLUGIN_AUTHORING.md` documents the full contract + workflow (6 points),
      accurate against the current code (file:line verified above).
- [x] Linked from `docs/README.md` + the README plugin section; link-check green.
- [x] Full suite green (1966 passed / 15 skipped).
