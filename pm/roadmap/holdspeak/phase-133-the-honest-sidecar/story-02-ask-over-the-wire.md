# HS-133-02 — Ask over the wire

- **Project:** holdspeak
- **Phase:** 133
- **Status:** done
- **Depends on:** HS-133-01
- **Unblocks:** HS-133-11
- **Owner:** unassigned

## Problem

An MCP client cannot ask the desk a question. `AskService`
(`holdspeak/services/ask_service.py`) carries the full admitted Ask
path — `ask()` (:117) enters `InferenceRunner.invoke()` via
`_as_principal` (:59) — but no MCP tool reaches it.

## Scope

### In

Per assets/surface-spec.md §1A, verbatim: `holdspeak/mcp/families/ask.py`
implementing `ask.models`, `ask.resolve_grounding`, `ask.run`,
`ask.cancel`, `ask.keep` with the spec's exact schemas and dispatch
anchors (list_models :64, resolve_grounding :107, ask :117, cancel :200,
keep :205). `ask.run` is async — wrap in the existing `_run()` pattern
(tools.py:406-411). Constructor per spec dispatch notes: `db`,
`observer=get_observer()`, no `broadcast`, no `rails_hydrator`. The
result passes through the service's receipt fields (`model`, `provider`,
`actual_placement`, `egress`, `grounding_claims`) unmodified.

### Out

- Any change to AskService itself. Model retargeting by name (the
  service refuses it, ask_service.py:137-139 — the schema correctly
  omits `model`). Streaming/WS frames (the sidecar is request/response).

## Acceptance criteria

- [ ] All five tools appear in the catalogue with closed schemas and
  dispatch to the anchored methods.
- [ ] `ask.run` reaches `AskService.ask()` and returns the receipt
  fields; a monkeypatched-service test proves the `_run()` wrapping.
- [ ] Error paths: missing `question`, unknown `invocation_id` on
  cancel — both return `isError: true`, never a crash.
- [ ] REQUIRED_TOOLS extended with the five names.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/unit/test_mcp_phase133.py tests/unit/test_mcp_tools.py --tb=short`
- Dispatch + error-path tests per spec Invariant 6; model-invoking test
  monkeypatches `AskService.ask` with a canned coroutine.
