# HS-35-03 — Per-project plugin enable/disable

- **Status:** done (2026-06-03). Evidence: [evidence-story-03.md](./evidence-story-03.md).

## Goal

Every chain-selected plugin fires on every saved meeting; a team can't suppress one
they don't want (e.g. skip `mermaid_architecture` for a product team). Add a
config-driven enable/disable that the dispatch honors — a disabled plugin is
**skipped, not failed**.

## Scope

- A **config knob** (e.g. `meeting.disabled_plugins: list[str]` and/or a
  per-profile map) on `MeetingConfig`, validated like the existing intent knobs.
- A **dispatch gate** in the routing/dispatch layer (`plugins/router.py` /
  `plugins/dispatch.py`): after the chain is built, drop disabled plugin ids before
  execution; the skip is recorded in readiness/telemetry (so the UI can show "N
  disabled"), distinct from a capability-blocked or failed run.
- The chain-construction output stays the same; only the *executed* set narrows. The
  existing chain constants in `test_intent_dispatch.py` describe the *built* chain
  and stay unchanged; new tests cover the *executed* (post-filter) set.

## Test plan

- Unit: disabling a plugin id removes it from the executed set for the relevant
  profile/intent; an unknown id is a no-op; an empty/missing list = today's
  behavior.
- Telemetry: a disabled plugin shows as `skipped` (not `failed`/`blocked`).
- Routing regression: `test_intent_dispatch.py` + the two full-pipeline tests
  (`test_intent_pipeline.py`, `test_multi_intent_routing.py`) updated in lockstep if
  touched — not silenced (HANDOVER §5).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Done when

- [x] A config knob suppresses specific plugin ids; dispatch skips them (not
      failed); skip surfaced in telemetry/readiness.
- [x] Default (no config) behavior is byte-identical to today.
- [x] Routing tests cover enable/disable; full suite green.

## Notes

- **Gate location:** the filter lives in `dispatch.py` (the *executed* set), not
  `router.py` (the *built* chain). `build_plugin_chain`/`preview_route` are untouched,
  so `RouteDecision.plugin_chain` and `test_intent_dispatch.py` are unchanged — a
  disabled plugin still appears in the built chain but is recorded as `skipped`.
- **Status model:** added `skipped` to `PLUGIN_RUN_STATUSES` (distinct from `blocked`
  = capability/actuator gate and `error` = ran-and-failed). Synthesis already ignores
  any status outside `{success, deduped}`, so a skipped run produces no artifact.
- **Telemetry:** `skipped` persists through `record_plugin_run` and surfaces verbatim
  on `GET /api/meetings/{id}/plugin-runs` — no new route needed.
- **Wiring:** `disabled_plugins` threads `dispatch_window`/`dispatch_windows` →
  `process_meeting_state` → `MeetingSession` ctor + `stop()` → `WebRuntime` passes
  `config.meeting.disabled_plugins`. (MIR dispatch is dormant in the flagship today,
  but the knob is wired end-to-end for when it's enabled.)
- **Config:** flat `disabled_plugins: list[str]` (the agreed default — a per-profile
  map was the "and/or" option, deferred). Normalized + validated in `__post_init__`;
  unknown ids are a harmless dispatch no-op.
