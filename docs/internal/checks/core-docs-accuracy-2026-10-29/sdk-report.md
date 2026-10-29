# SDK documentation accuracy report

Date: 2026-10-29  
Base: `4dce2796d`  
Scope: the three SDK-owned guides and this lane's audit artifacts. Product
source, tests, defaults, packages and generated regions were not edited.

## Result

The three guides were source-checked and corrected where the previous wording
could make an architect confuse a stored proposal, a capability admission and a
completed external action.

- `docs/ACTUATOR_DEVELOPMENT.md` now describes the approval authority binding
  and the conditional YOLO fixed-destination seam (`holdspeak/db/actuators.py:262-395`,
  `holdspeak/web/routes/actuator_shared.py:108-152`). It distinguishes the bare
  `PluginHost` actuator capability gate and web runtime's `llm`-only capability
  set (`holdspeak/plugins/host.py:138-169`, `holdspeak/web_runtime.py:255-271`)
  from executor policy and the shipped meeting config values
  (`holdspeak/config/meeting.py:117-131`,
  `holdspeak/plugins/actuator_executor.py:60-117`). The companion idempotency
  description now matches target-specific key material and does not claim that
  changing a webhook destination always creates a new proposal
  (`holdspeak/services/actuator_service.py:50-85`).
- `docs/CONNECTOR_DEVELOPMENT.md` now uses the committed `gh-happy-path.json`
  fixture and its actual two-command/two-annotation expectations
  (`tests/fixtures/connectors/gh-happy-path.json`,
  `tests/unit/test_connector_fixture_harness.py:30-48`). It explains the active
  registry/restart prerequisite and uses an isolated HOME plus
  `scripts/test_lock.py` in the test example.
- `docs/PLUGIN_AUTHORING.md` now identifies the pipeline/synthesis persistence
  boundary and the exact four-field, per-host idempotency cache
  (`holdspeak/plugins/pipeline.py:164-215`,
  `holdspeak/plugins/host.py:118-135,487-506,605-606`). It separates
  `PluginHost.register()` from plugin-pack manifest validation
  (`holdspeak/plugins/host.py:211-217`, `holdspeak/plugin_sdk.py:209-318`),
  labels `_parse_and_validate` as an example skeleton, and assigns disabled
  plugin handling to the dispatcher (`holdspeak/plugins/dispatch.py:120-162`).

## Verification

- `python3 scripts/check_docs.py docs/ACTUATOR_DEVELOPMENT.md docs/CONNECTOR_DEVELOPMENT.md docs/PLUGIN_AUTHORING.md`
- `git diff --check`

Both commands are run after the edits. No pytest, package install, browser or
Desk/provider/device operation was performed under the lane brief.

## Unknowns

Source review does not establish a live Desk face, runtime restart, CLI
availability, provider response, webhook/GitHub result or physical device flow.
Those remain unverified deployment facts.

Status: **DRAFT — hold for SHIP**.
