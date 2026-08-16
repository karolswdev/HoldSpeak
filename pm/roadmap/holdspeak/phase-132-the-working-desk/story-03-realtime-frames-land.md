# HS-132-03 — The desk hears intelligence live

- **Project:** holdspeak
- **Phase:** 132
- **Status:** done
- **Depends on:** HS-132-02
- **Unblocks:** HS-132-14
- **Owner:** unassigned

## Problem

The realtime vocabulary is broken on both sides. Emitted with zero consumers
anywhere in `web/src`: `intel_token`
(`holdspeak/meeting_session/intel_admission.py:456`), `intel_complete`
(`intel_analysis.py:197`, `meeting_glue.py:114`), `bookmark`
(`holdspeak/web/routes/meetings/live.py:67`), `intent_controls_updated`,
`device_health`, `actuator_result`
(`meeting_aftercare_service.py:109,111,140`), and `runtime_queue`
(`holdspeak/runtime/plugin_queue.py:59-70`). Subscribed with zero emitters:
`plugin_jobs`/`plugin_job` (`web/src/components/AmbientLayer.tsx:85-86`) and
all five `workbench.*` frames
(`web/src/desk/components/WorkbenchWindow.tsx:990-1016`) — the conductor's
`_emit` (`holdspeak/workbench_conductor.py:33-39`) is wired to broadcast at
`web_server.py:845-846` and never called. Net effect: meeting intelligence
streams token by token to nobody, the queue HUD never renders, and a running
workbench never updates live.

## Scope

### In

- LiveCore renders the intelligence stream: token stream (or throttled
  progressive text) and completion state from `intel_token`/`intel_complete`;
  a dropped bookmark confirms live.
- The queue HUD consumes `runtime_queue` (retire the phantom
  `plugin_jobs`/`plugin_job` subscriptions).
- The workbench conductor emits `workbench.run_start`, `item_claimed`,
  `item_done`, `item_failed`, `run_complete` at the real transition points;
  the existing WorkbenchWindow subscriptions come alive.
- `actuator_result` updates any open surface showing the proposal it decides.
- One frame-vocabulary registry (shared constant list on the Python side,
  mirrored or generated for the web) plus a guard test that fails when a
  frame type is emitted with no consumer or consumed with no emitter.

### Out

- New frame types beyond the existing vocabulary.
- Mascot/presence redesign (HS-132-08 surfaces aftercare without the mascot).
- Token-stream journaling (Article XI.5 — display only).

## Acceptance criteria

- [ ] During a live meeting the desk shows intelligence arriving (progressive
  text or equivalent) and its completion, without a manual refetch.
- [ ] A bookmark dropped mid-meeting produces a visible confirmation.
- [ ] Pending/running/failed deferred intel jobs are visible on the desk.
- [ ] A workbench run updates its window live: items move through
  claimed/done/failed and the run shows complete without reload.
- [ ] The orphan guard test enumerates emitters and consumers and fails on
  any one-sided frame type; it passes on the finished tree.

## Test plan

- New guard test (unit) over the frame registry.
- Focused unit tests: conductor emissions; LiveCore/AmbientLayer/Workbench
  frame handling (vitest).
- Live verification rides HS-132-14's walk.
