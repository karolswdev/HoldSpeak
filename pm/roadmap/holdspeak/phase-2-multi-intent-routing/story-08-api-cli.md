# HS-2-08 — Step 7: API + CLI surfaces

- **Project:** holdspeak
- **Phase:** 2
- **Status:** done
- **Depends on:** HS-2-05 (persistence), HS-2-07 (synthesis)
- **Unblocks:** HS-2-09 (config gates use these surfaces), HS-2-11 (DoD evidence sweep)
- **Owner:** unassigned

## Problem

Spec §9.8 calls for: timeline endpoints in `holdspeak/web_server.py`,
CLI dry-run + reroute in `holdspeak/commands/intel.py`, web UI
controls, and three test files
(`tests/integration/test_web_intent_timeline_api.py`,
`tests/integration/test_web_intent_controls.py`,
`tests/unit/test_intel_command.py` updates). Audit (post-HS-2-07):

- All four `/api/intents/*` control endpoints exist
  (`/control` GET, `/profile` PUT, `/override` PUT, `/preview` POST)
  with `_IntentProfileRequest` / `_IntentOverrideRequest` /
  `_IntentPreviewRequest` Pydantic shapes.
- All three `/api/meetings/{id}/...` read endpoints exist
  (`/intent-timeline`, `/plugin-runs`, `/artifacts`).
- `holdspeak/commands/intel.py` already has `_run_mir_route_command`
  with dry-run + reroute + persist; `tests/unit/test_intel_command.py`
  has 7 cases including `..._route_dry_run_emits_route_json` and
  `..._reroute_persists_intent_window`.

The genuine gaps are the **two integration test files spec §9.8
names** and the **circular-import bug** that surfaced when the
timeline endpoint was first exercised against the HS-2-07-shaped
`plugins/__init__.py` re-exports.

## Scope

- **In:**
  - New `tests/integration/test_web_intent_timeline_api.py` (6 cases) — exercises the 3 read endpoints against a `MeetingWebServer` with `TestClient` over a seeded sqlite DB. Covers happy-path payload shape, 404 on unknown meeting, plugin-run filter by `window_id`, and lineage round-trip on artifacts (MIR-A-001, MIR-A-002, MIR-A-005, MIR-D-004).
  - New `tests/integration/test_web_intent_controls.py` (8 cases) — exercises the 4 control endpoints in two flavors: (a) callback-unset → `501 Not Implemented` for the mutation endpoints + safe defaults for the GET; (b) callback-wired → invokes the callback with the right shape and returns the result (MIR-A-006, MIR-F-007).
  - Bug fix in `holdspeak/plugins/pipeline.py`: lazy-import `build_intent_windows` inside `process_meeting_state` to break the `plugins/__init__.py` ↔ `intent_timeline.py` circular load that the new web tests surfaced. Added a comment explaining the cycle so future maintainers don't re-introduce a top-level import.
- **Out:**
  - New CLI subcommands. `holdspeak intel route` (existing) already covers the spec §9.8 CLI surface. Adding a `holdspeak meeting timeline` / `meeting artifacts` subcommand would be additive ergonomics; defer to a follow-up since the API gives the same data and is the spec's flagship surface (MIR-A-008).
  - Web UI HTML/JS controls. The endpoints + JSON contract are tested; the UI side is its own follow-up (HS-2-08b or part of HS-2-11 DoD).
  - `tests/unit/test_intel_command.py` updates — existing 7 cases already cover the route command surface (3 directly; verified with the spec's verification gate).

## Acceptance criteria

- [x] `tests/integration/test_web_intent_timeline_api.py` ships with 6 cases, all pass.
- [x] `tests/integration/test_web_intent_controls.py` ships with 8 cases, all pass.
- [x] Pre-existing `tests/unit/test_intel_command.py` (7 cases incl. 3 MIR-route ones) remains green.
- [x] Circular-import bug in `holdspeak/plugins/pipeline.py` fixed by lazy-loading `build_intent_windows`; no other call sites needed changing.
- [x] Spec §9.8 verification gates pass:
  - `uv run pytest -q tests/integration/test_web_intent_timeline_api.py -m requires_meeting` (6 cases).
  - `uv run pytest -q tests/integration/test_web_intent_controls.py -m requires_meeting` (8 cases).
  - `uv run pytest -q tests/unit/test_intel_command.py` (7 pre-existing cases).
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 954 passed, 12 skipped, 0 failed in 17.77s. Pass delta vs. HS-2-07 (940): +14.

## Test plan

- **Integration:** the two new integration files (14 cases total).
- **Spec §9.8 verification gates:** see Acceptance criteria.
- **Regression:** `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py`.

## Notes / open questions

- **Real bug found by integration tests.** The timeline-API test
  failed initially with `cannot import name 'build_intent_windows'
  from partially initialized module 'holdspeak.intent_timeline'`.
  Trace: `intent_timeline` imports `IntentWindow` from
  `plugins.contracts` → loads `plugins/__init__.py` →
  loads `pipeline.py` → tries to import `build_intent_windows` from
  the still-loading `intent_timeline`. Fix: move the import inside
  `process_meeting_state` (only call site). This is the kind of bug
  the unit tests for HS-2-06 wouldn't have caught because they don't
  exercise the web-server import path. Lesson: integration tests
  through the real entry points catch import-graph regressions that
  module-scoped unit tests miss.
- The two integration test files use `pytestmark = [pytest.mark.requires_meeting]` matching the existing `test_intel_streaming.py` convention so they're discoverable via the spec's `-m requires_meeting` gate.
- CLI extension (`holdspeak meeting timeline <id>`) deferred — the existing `holdspeak intel route` subcommand satisfies spec §9.8 line 2 and the API is the spec's flagship surface (MIR-A-008 says docs lead with web flows). Adding a meeting CLI subcommand is straightforward additive work for a follow-up.
