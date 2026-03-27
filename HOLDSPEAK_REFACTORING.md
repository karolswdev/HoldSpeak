# HoldSpeak Refactoring Recipe

This document is the working recipe for stabilizing and simplifying HoldSpeak without losing product momentum.
It is intentionally biased toward correctness, maintainability, and incremental delivery.

The codebase already has meaningful strengths:
- real product surface area
- strong local-first design
- broad automated test coverage
- a documented target architecture for the TUI

It also has clear structural debt:
- oversized orchestration modules
- partial mismatch between architecture docs and implementation
- concurrency hazards in meeting shutdown
- duplicated persistence logic
- success paths that can mask partial failure

The goal is not a rewrite.
The goal is to remove the dangerous parts first, then make the architecture match the intended shape.

## Baseline

Current baseline observed locally:
- `527 passed, 19 skipped` via `uv run pytest -q`
- project compiles via `uv run python -m compileall holdspeak`
- largest modules are:
  - `holdspeak/main.py`
  - `holdspeak/meeting_session.py`
  - `holdspeak/db.py`
  - `holdspeak/web_server.py`
  - `holdspeak/tui/app.py`
  - `holdspeak/tui/screens/meeting_detail.py`

This means the repo is not in crisis.
It does mean refactoring should be done under test and in small phases.

## Core Findings

### 1. Meeting shutdown has a real deadlock risk

`holdspeak/meeting_session.py` currently holds `self._lock` in `stop()`, then calls methods that try to acquire the same lock again:
- final transcription path
- final intel path
- transcript formatting path

That is the highest-risk issue because it affects the core meeting lifecycle and is easy to miss in test coverage.

### 2. Save semantics are misleading

`MeetingSession.save()` logs database failures, still writes JSON, and returns success.
The caller then tells the user the meeting was saved.

That is not acceptable for the primary persistence path.
Users should not be told a meeting is saved if the canonical history store failed.

### 3. TUI architecture is only partially implemented

The TUI architecture docs already say the right thing:
- UI emits intents
- App orchestrates
- services persist
- UI should not import the DB directly

But several screens and components still read/write SQLite directly.
That keeps the code working today while making it harder to reason about state, navigation, and side effects.

### 4. Persistence code has drift and duplication

`holdspeak/db.py` contains duplicated method definitions, including `update_action_item_status`.
That is a concrete sign that the module is doing too much and no longer has a single obvious contract.

### 5. Too much responsibility is concentrated in a few files

The system currently relies on a small number of large modules to do orchestration, state transitions, persistence, export, and feature wiring.

That is survivable for a while, but expensive to evolve.

## Refactoring Principles

These are the non-negotiables for this work:

1. Fix correctness before elegance.
2. Prefer extraction over rewrite.
3. Keep behavior stable unless the current behavior is wrong.
4. Make architecture enforceable by grep, tests, and review checklists.
5. Keep UI code side-effect light.
6. Make primary persistence failure visible to callers and users.
7. Avoid adding new abstractions unless they remove an existing dependency edge.

## Target Shape

High-level target architecture:

### UI layer

Owns:
- rendering
- local interaction handling
- local view state
- intent emission

Does not own:
- SQLite access
- export writes
- meeting/session orchestration
- cross-feature navigation decisions

### App / controller orchestration layer

Owns:
- intent handling
- navigation
- calling services
- coordinating background work
- applying results to UI state

### Service layer

Owns:
- persistence operations
- export operations
- entity loading and updates
- use-case shaped logic that is not UI

### Domain/runtime layer

Owns:
- audio capture
- transcription
- meeting runtime
- web dashboard runtime
- diarization/intel integration

## Recommended Execution Order

Do the work in this order:

1. Phase 0: establish guardrails
2. Phase 1: fix shutdown and save correctness
3. Phase 2: clean persistence seams
4. Phase 3: finish TUI boundary separation
5. Phase 4: reduce orchestration mass
6. Phase 5: add regression gates

Do not start by extracting twenty services.
Start by removing the correctness hazards.

## Progress

Completed:
- Phase 1A: `MeetingSession.stop()` no longer performs final transcription, final intel, web shutdown, or diarizer persistence while holding the session lock.
- Added a regression test covering the former stop-path deadlock shape.
- Phase 1B: `MeetingSession.save()` now returns a structured result and callers report success, partial success, and failure honestly.
- Phase 2A: removed the duplicate public `MeetingDatabase.update_action_item_status()` definition and added a structural regression test so `db.py` keeps one canonical implementation per public method.
- Phase 2A: hardened the action-item status contract in `holdspeak/db.py`; invalid statuses now fail fast and re-saving a meeting no longer resets terminal action-item state back to `pending`.
- Phase 2B: shared meeting export helpers now back CLI and TUI exports, removing duplicate markdown/text/json formatting logic across `commands/history.py`, `tui/services/meetings.py`, and `meeting_detail.py`.

In progress:
- Phase 2: persistence cleanup, with duplicate-method removal and action-item status hardening complete; remaining work is to keep carving `db.py` into clearer persistence seams.
- Phase 3: first TUI service extraction has started with action-item persistence moved behind `holdspeak/tui/services/action_items.py`.
- Phase 3: speaker/profile persistence has been moved out of `meeting_detail.py` and `speaker_profile.py` into `holdspeak/tui/services/speakers.py`.
- Phase 3: saved-meeting list/search/get/delete/update/export now flow through `holdspeak/tui/services/meetings.py`, removing DB access from `tui/app.py` and `meetings_hub_pane.py`.
- Phase 3 milestone reached: `rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui/screens holdspeak/tui/components holdspeak/tui/app.py` now returns no hits.
- Phase 4 started: CLI history/actions/migrate handlers have been extracted from `holdspeak/main.py` into `holdspeak/commands/*`, reducing `main.py` from 1336 lines to 1057 lines.
- Phase 4 milestone: runtime/controller wiring has been extracted into `holdspeak/controller.py`, reducing `main.py` further from 1057 lines to 538 lines.

## Phase 0: Guardrails

Goal:
- make refactoring safe before code movement begins

Tasks:
- keep `uv run pytest -q` green after each phase
- add a dedicated test for the meeting stop path
- add a dedicated test for save failure semantics
- add a grep-based review rule for UI-layer DB imports

Acceptance criteria:
- there is a test that would fail if `MeetingSession.stop()` deadlocks
- there is a test that would fail if DB save fails silently
- team can run a one-line grep to detect TUI DB violations

Suggested checks:

```bash
uv run pytest -q
rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui
```

## Phase 1: Correctness First

Goal:
- remove deadlock risk
- make save/reporting semantics honest

Scope:
- `holdspeak/meeting_session.py`
- `holdspeak/main.py`
- tests around meeting session and controller save behavior

### 1A. Rewrite `MeetingSession.stop()` to avoid lock re-entry

Desired pattern:
- acquire lock only to snapshot mutable references and mark stop intent
- release lock before:
  - joining threads
  - stopping recorder
  - final transcription
  - final intel
  - web server shutdown
  - speaker persistence
- reacquire lock only to commit final state mutations

Implementation guidance:
- use lock sections for state mutation, not for long-running work
- treat `_state`, `_recorder`, `_intel`, `_web_server`, `_diarizer` as snapshotted dependencies
- make the final state transition explicit:
  - stopping requested
  - recorder stopped
  - final transcript applied
  - final intel applied
  - ended_at set

Acceptance criteria:
- no long-running or callback-heavy work occurs while holding `self._lock`
- stop path completes under a test using fake recorder/transcriber/intel
- reproduced deadlock no longer reproduces

### 1B. Make save results explicit

Current problem:
- DB failure is swallowed
- JSON write can succeed
- caller treats that as full success

Refactor target:
- return a structured save result, not just a path
- distinguish:
  - database_saved
  - json_saved
  - database_error
  - json_error

Recommended shape:

```python
@dataclass
class MeetingSaveResult:
    database_saved: bool
    json_saved: bool
    json_path: Path | None
    database_error: str | None = None
    json_error: str | None = None
```

Caller behavior in `holdspeak/main.py`:
- success notification only when DB save succeeded
- degraded notification when JSON succeeded but DB failed
- error notification when both failed

Acceptance criteria:
- user-facing messaging reflects actual persistence status
- DB failure cannot be mistaken for success

## Phase 2: Persistence Cleanup

Goal:
- make `db.py` predictable and remove copy-paste drift

Scope:
- `holdspeak/db.py`
- tests for DB contract

Tasks:
- remove duplicate method definitions
- make action item status semantics explicit and consistent
- decide whether `dismissed` should set `completed_at`
- centralize export-format helpers if needed, but do not over-generalize
- audit method names for single clear behavior

Recommended sub-steps:

### 2A. Remove duplicate methods

At minimum:
- remove duplicate `update_action_item_status`

Acceptance criteria:
- AST scan or grep shows one definition per public DB method

### 2B. Define action item lifecycle

Decide and document:
- what `pending` means
- what `done` means
- what `dismissed` means
- whether `completed_at` is used for both `done` and `dismissed`, or only `done`

Then update:
- database method implementation
- CLI behavior
- TUI behavior
- tests

Acceptance criteria:
- one consistent semantic contract across DB, CLI, web, and TUI

### 2C. Decide the canonical persistence model

Current state:
- SQLite is primary for history
- JSON is still written for backward compatibility

Decision needed:
- keep dual-write intentionally
- or make JSON export-only / migration-only

Recommended direction:
- SQLite is canonical
- JSON becomes optional compatibility/export behavior, not an equal persistence path

Acceptance criteria:
- docs and implementation match
- save flow reflects the chosen canonical store

## Phase 3: Finish TUI Boundary Separation

Goal:
- make the TUI actually follow the architecture already described in the docs

Scope:
- `holdspeak/tui/app.py`
- `holdspeak/tui/screens/*`
- `holdspeak/tui/components/*`
- new `holdspeak/tui/services/*`

### 3A. Introduce minimal service modules

Do not create a giant framework.
Create small modules shaped around use cases.

Recommended modules:
- `holdspeak/tui/services/meetings.py`
- `holdspeak/tui/services/speakers.py`
- `holdspeak/tui/services/action_items.py`
- `holdspeak/tui/services/export.py`

Recommended responsibilities:

`meetings.py`
- get saved meeting
- list meetings
- update metadata
- delete meeting

`speakers.py`
- get speaker profile data
- update speaker name/avatar

`action_items.py`
- list cross-meeting actions
- update action status

`export.py`
- export meeting markdown/json/txt

Acceptance criteria:
- services are small and use-case shaped
- UI modules stop importing `holdspeak.db`

### 3B. Convert direct UI persistence to intents

Priority targets:
- `holdspeak/tui/screens/meeting_detail.py`
- `holdspeak/tui/screens/speaker_profile.py`
- `holdspeak/tui/screens/actions.py`
- `holdspeak/tui/components/meetings_hub_pane.py`

Pattern:
- screen/component emits intent
- `HoldSpeakApp` handles intent
- app calls service in worker
- UI thread applies results

Examples to convert:
- action item toggle
- speaker rename/avatar update
- meeting export
- speaker history load
- meeting detail data load
- meetings hub preview data load

Acceptance criteria:

```bash
rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui
```

Expected result:
- no hits in `holdspeak/tui/screens`
- no hits in `holdspeak/tui/components`
- if services live under `holdspeak/tui/services`, DB access is allowed there

### 3C. Make App handlers call services, not DB directly

`holdspeak/tui/app.py` is better than the screens today, but it still does direct persistence work.
Move that into services too.

Acceptance criteria:
- app intent handlers coordinate work, but service modules own DB access

## Phase 4: Reduce Module Mass

Goal:
- break up the largest files along natural seams

Do not do this before Phases 1-3.

### 4A. Break down `holdspeak/main.py`

Current problem:
- controller orchestration, CLI commands, utility flows, and mode runners all live together

Recommended split:
- `holdspeak/controller.py`
  - `HoldSpeakController`
- `holdspeak/cli.py`
  - argument parsing and subcommand dispatch
- `holdspeak/commands/history.py`
- `holdspeak/commands/actions.py`
- `holdspeak/commands/migrate.py`
- keep `holdspeak/main.py` as a thin entrypoint

Acceptance criteria:
- `main.py` becomes an entrypoint/wiring module, not the kitchen sink

### 4B. Break down `holdspeak/meeting_session.py`

Current problem:
- runtime lifecycle
- state mutation
- transcript chunk processing
- web broadcasting
- bookmarking
- intel scheduling
- saving

Recommended split:
- `holdspeak/meeting_runtime.py` or `holdspeak/meeting_session.py`
  - lifecycle orchestration
- `holdspeak/meeting_transcription.py`
  - chunk-to-segment logic
- `holdspeak/meeting_intel_runtime.py`
  - intel scheduling/streaming coordination
- `holdspeak/meeting_persistence.py`
  - save/load contract if needed

Do not split everything mechanically.
Split only where dependencies become cleaner.

Acceptance criteria:
- `MeetingSession` becomes an orchestrator, not the owner of every feature detail

### 4C. Break down `holdspeak/web_server.py`

Current problem:
- route definitions
- websocket management
- history API
- meeting API
- server lifecycle

Recommended split:
- `holdspeak/web/socket_manager.py`
- `holdspeak/web/meeting_app.py`
- `holdspeak/web/history_routes.py`
- `holdspeak/web/server.py`

Acceptance criteria:
- server lifecycle and route concerns are separated

## Phase 5: Regression Gates

Goal:
- stop the codebase from sliding back

### 5A. Add missing tests for risky flows

High-value tests:
- `MeetingSession.stop()` does not deadlock with final chunks present
- save result is honest when DB write fails
- TUI intent flow updates saved meeting metadata correctly
- speaker update flow works through app/service path
- action item toggle works through app/service path

### 5B. Add architecture checks

Recommended checks:
- grep rule preventing DB imports in TUI UI layer
- test ensuring no duplicate public DB method names
- code review checklist in docs

Possible AST-based test:
- parse `holdspeak/db.py`
- assert no duplicate public method names in `MeetingDatabase`

### 5C. Add smoke commands to docs

Recommended command set:

```bash
uv run pytest -q
uv run pytest -q tests/unit
uv run pytest -q tests/integration
uv run python -m compileall holdspeak
rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui
```

## Suggested PR Sequence

Keep the work easy to review.

### PR 1
- fix `MeetingSession.stop()` locking
- add deadlock regression test

### PR 2
- introduce structured save result
- fix user notifications
- add save failure tests

### PR 3
- clean `db.py`
- remove duplicate methods
- normalize action item status semantics

### PR 4
- add `holdspeak/tui/services/*`
- move one vertical slice end-to-end:
  - action items

### PR 5
- move speaker profile and speaker updates to services/intents

### PR 6
- move meeting detail export and remaining saved meeting flows to services/intents

### PR 7
- split `main.py`

### PR 8
- split `meeting_session.py` and optionally `web_server.py`

## Definition of Done

The refactor is complete when all of the following are true:

1. Meeting stop is demonstrably free of the current deadlock path.
2. Save/reporting semantics reflect real persistence outcomes.
3. `holdspeak/tui/screens/*` and `holdspeak/tui/components/*` do not access the DB directly.
4. `holdspeak/tui/app.py` orchestrates via services rather than embedding persistence details.
5. `holdspeak/db.py` has no duplicated public methods and has one clear contract per operation.
6. The largest modules are reduced enough that responsibilities are legible.
7. Test and grep gates exist to prevent regressions.

## Anti-Patterns To Avoid During Refactor

- full rewrite of the app shell
- introducing a generic event bus for everything
- moving code into `utils.py` to avoid making real ownership decisions
- adding services that are just thin pass-through wrappers with no boundary value
- hiding persistence failures behind logs
- expanding `HoldSpeakApp` while trying to simplify the UI
- mixing state mutation and long-running work under the same lock

## Immediate Next Actions

If this recipe is followed literally, the next actions should be:

1. Add the deadlock regression test for `MeetingSession.stop()`.
2. Refactor `MeetingSession.stop()` so long-running work happens outside the lock.
3. Introduce `MeetingSaveResult` and update controller notifications.
4. Remove the duplicate `update_action_item_status` definition.
5. Create `holdspeak/tui/services/action_items.py` and migrate the action-items screen first.

That order gives the best ratio of risk reduction to implementation cost.

## Handover

This section is the current-state handoff for a fresh context.

### Current Status

As of the latest refactoring pass:
- `uv run pytest -q` passes with `532 passed, 19 skipped`
- `uv run python -m compileall holdspeak` passes
- `rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui/screens holdspeak/tui/components holdspeak/tui/app.py` returns no hits

### Completed Work

Correctness and persistence:
- `MeetingSession.stop()` was refactored to avoid doing long-running finalization while holding the session lock.
- A regression test was added for the former stop-path deadlock shape.
- `MeetingSession.save()` now returns a structured `MeetingSaveResult`.
- TUI and menubar meeting-stop notifications now reflect real persistence outcomes.
- `holdspeak/db.py` duplicate `update_action_item_status` implementation was removed.
- Action-item status semantics were locked in with tests:
  - `done` sets `completed_at`
  - `dismissed` sets `completed_at`
  - `pending` clears `completed_at`

TUI architecture:
- Added `holdspeak/tui/services/action_items.py`
- Added `holdspeak/tui/services/speakers.py`
- Added `holdspeak/tui/services/meetings.py`
- Moved TUI action-item persistence out of screens into services.
- Moved speaker/profile persistence out of `meeting_detail.py` and `speaker_profile.py` into services.
- Moved saved-meeting list/search/get/delete/update/export flows out of `tui/app.py` and `meetings_hub_pane.py` into services.
- Moved `history.py` onto the meetings service.

Main entry decomposition:
- Extracted CLI subcommand handlers into:
  - `holdspeak/commands/history.py`
  - `holdspeak/commands/actions.py`
  - `holdspeak/commands/migrate.py`
- Extracted runtime/controller wiring into:
  - `holdspeak/controller.py`

### Size Snapshot

Current large-file situation after refactor:
- `holdspeak/main.py`: `538` lines
- `holdspeak/controller.py`: `474` lines

This is materially better than the starting point, where `holdspeak/main.py` was `1336` lines.

### Important Invariants Now True

These should not be regressed:
- No direct DB access from `holdspeak/tui/screens/*`
- No direct DB access from `holdspeak/tui/components/*`
- No direct DB access from `holdspeak/tui/app.py`
- `MeetingSession.stop()` must keep long-running work outside the session lock
- Save/reporting semantics must not claim success when DB persistence failed

### Best Next Steps

If continuing the refactor, the next highest-value work is:

1. Split `holdspeak/controller.py` into smaller runtime units.
   Candidate slices:
   - voice typing runtime
   - meeting runtime coordination
   - app/controller event bridge

2. Revisit `holdspeak/meeting_session.py`.
   This is still one of the biggest concentration points and likely wants separation between:
   - meeting lifecycle
   - chunk transcription
   - intel scheduling/streaming
   - persistence

3. Optionally split `holdspeak/web_server.py`.
   Good candidates:
   - server lifecycle
   - websocket manager
   - meeting routes
   - history routes

### Recommended Resume Checks

Run these first in a fresh context:

```bash
uv run pytest -q
uv run python -m compileall holdspeak
rg "from \\.\\.\\.db import|get_database\\(" holdspeak/tui/screens holdspeak/tui/components holdspeak/tui/app.py
wc -l holdspeak/main.py holdspeak/controller.py holdspeak/meeting_session.py holdspeak/web_server.py
```

### Files Most Worth Reading First

For a quick restart, read these in order:
- `HOLDSPEAK_REFACTORING.md`
- `holdspeak/controller.py`
- `holdspeak/main.py`
- `holdspeak/meeting_session.py`
- `holdspeak/tui/services/meetings.py`
- `holdspeak/tui/services/speakers.py`
- `holdspeak/tui/services/action_items.py`

### Risk Notes

- `holdspeak/meeting_session.py` is still the most likely place for subtle lifecycle/concurrency regressions.
- `holdspeak/controller.py` is improved but still dense enough that future changes should be split carefully.
- The TUI architecture is now much cleaner, but intent routing is still lighter than the long-term ideal described earlier in this document.
