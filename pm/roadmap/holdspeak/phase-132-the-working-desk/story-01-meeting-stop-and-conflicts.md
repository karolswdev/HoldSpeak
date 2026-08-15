# HS-132-01 — Stopping a meeting never stops the hub

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-132-02
- **Owner:** unassigned

## Problem

Two route-level defects make the most basic meeting verbs dangerous or
dishonest, both caught by named tests that have been red on main unnoticed:

1. `holdspeak/web_server.py:635-640` composes the production `MeetingService`
   with `on_stop=self.on_stop` (the runtime-fallback stop,
   `allow_runtime_fallback=True`) instead of the intended
   `ctx.on_meeting_stop or ctx.on_stop` binding shown at
   `holdspeak/web/routes/meetings/live.py:43`. When no meeting is live —
   stale desk orb after a socket drop, external CLI stop, crash-recovered
   session — `holdspeak/runtime/meeting_glue.py:353-359` sets
   `runtime_stop_event` and the whole hub main loop
   (`holdspeak/web_runtime.py:596`) exits. Stopping a meeting can terminate
   the runtime, with a success response.
2. `holdspeak/services/meeting_service.py:30` imports only `NotFound` and
   `ValidationError`, but `ConflictError` is raised at lines 402, 407, 412,
   416, 420. Every meeting sync-conflict branch raises `NameError` and
   returns 500; the conflict-recovery card
   (`web/src/desk/pullouts/MeetingPullout.tsx:100`) tells the user to retry
   an action that can never succeed.

## Scope

### In

- Bind `POST /api/meeting/stop` (and any composition path reaching
  `MeetingService`) to the no-fallback `on_meeting_stop`, refusing by name
  ("No active meeting") when nothing is live.
- Import `ConflictError` in `meeting_service.py`; verify all five branches
  return their chartered 409/400 with their written messages.
- Re-green the named tests:
  `tests/integration/test_web_server.py::TestRuntimeControlEndpoints::test_meeting_stop_prefers_on_meeting_stop_callback`
  and `tests/integration/test_meeting_conflict_recovery.py`.

### Out

- Any change to the runtime-fallback stop used by legitimate runtime control
  surfaces.
- The action-item triage repair (HS-132-02).

## Acceptance criteria

- [ ] Stopping with no live meeting returns a named refusal and the hub
  process keeps running.
- [ ] Stopping a live meeting still stops it (no regression on the real
  path).
- [ ] All five conflict branches answer their honest status codes and
  messages; no `NameError` is reachable.
- [ ] Both previously red test groups pass in isolation and in-suite.

## Test plan

- `HOME=$(mktemp -d) uv run pytest -q tests/integration/test_meeting_conflict_recovery.py tests/integration/test_web_server.py -k "meeting_stop or conflict" --tb=short`
- Manual: with the hub running and no meeting live, press the desk Record orb
  stop; verify refusal shown and hub alive.
