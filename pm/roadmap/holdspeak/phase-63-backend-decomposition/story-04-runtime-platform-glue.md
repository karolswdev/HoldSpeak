# HS-63-04 — WebRuntime mixins: the platform glue + thin core

- **Project:** holdspeak
- **Phase:** 63
- **Status:** backlog
- **Depends on:** HS-63-03
- **Unblocks:** HS-63-05
- **Owner:** unassigned

## Problem
Meeting lifecycle glue, MIR/routing glue, the deferred plugin queue, and
the activity/status payload builders fill the rest of the god-object.

## Scope
- **In:** `holdspeak/runtime/` gains `meeting_glue.py` (start/stop,
  segment/intel/broadcast handlers, action-item handlers),
  `routing_glue.py` (MIR controls, route preview, history persistence,
  artifact synthesis, project association), `plugin_queue.py` (the
  deferred queue loop + flush), `activity.py` (runtime activity/state/
  status payloads), and `transcriber_state.py` (status + load/warm).
  `web_runtime.py` keeps __init__, config apply/presence sync, the
  onboarding nudges, signal handling, run(), and run_web_runtime —
  under the guard budget. Patch-target moves (MeetingSession,
  drain_plugin_run_queue, Transcriber) documented as in HS-63-03.
- **Out:** behavior changes; web_server.py.

## Acceptance criteria
- [ ] The five mixins are single-concern and under budget; the core
      `web_runtime.py` is boot/run/config only, under budget.
- [ ] Test edits are patch-target paths ONLY, enumerated in evidence.
- [ ] Full suite green.

## Test plan
- Full suite + the web_runtime / meeting-flow / MIR slices.
