# HS-131-08 — Meetings are admitted per session

- **Project:** holdspeak
- **Phase:** 131
- **Status:** backlog
- **Depends on:** HS-131-01, HS-131-02, HS-131-07
- **Unblocks:** HS-131-10
- **Owner:** unassigned

## Problem

Meeting intelligence invokes models from live transcript windows, deferred queue
work, retries, and routed plugins. Today those calls execute directly, and an
"interrupted" stream may only stop consuming chunks without cancelling the
provider. Per-call top-level authority resolution would add the wrong latency,
but one session receipt cannot absorb the invocations inside it.

## Scope

### In

- Admit one meeting-intelligence session when the meeting/session begins. The
  parent captures immutable authority basis, meeting identity, a frozen routing
  and deployment plan, deadline/expiry, and cancellation state. Each invocation
  child names the exact deployment revision selected by that frozen plan; the
  design does not assume every plugin capability uses one model.
- Treat each live transcript-window call in
  `holdspeak/meeting_session/intel_analysis.py:60-102`, each deferred queue call
  in `holdspeak/intel_queue.py:193-230`, and every routed plugin provider call
  from `intel_queue.py:262-307` as an admitted invocation child through the
  runner, continuing the session.
- Each retry or fallback that reaches a provider creates another invocation
  child and terminal receipt.
- Reuse the session's immutable authority basis and frozen placement plan for
  lightweight child admission; do not perform a fresh top-level owner decision
  per transcript window. Every child admission and claim still asks the kernel
  whether the session and its authority are live, unexpired, and unrevoked.
- Stop/interrupt/expiry cancels active children, refuses new continuations, and
  prevents late output from entering meeting artifacts or plugin results.
- Record result refs, timing, boundary, and outcome, but never transcript prompt
  bodies, token streams, or raw audio in the kernel journal.
- Preserve meeting routing, plugin ordering, idempotency, and user-facing output
  semantics.

### Out

- Meeting UI redesign or new controls.
- Shared local Whisper execution and meeting transcription children, owned by
  HS-131-09 after this story establishes the meeting session parent.
- Dictation and wake sessions, owned by HS-131-09.
- One child per token or transcript segment that does not invoke a model.
- Folding plugin domain records into kernel receipts.

## Acceptance criteria

- [ ] Starting meeting intelligence creates exactly one admitted session parent
  with a frozen routing/deployment plan and authenticated authority basis; each
  invocation child names the exact revision it executes.
- [ ] Every actual live, deferred, retry, fallback, and routed-plugin provider
  call is a causally linked invocation child with one terminal receipt.
- [ ] Non-model transcript windows and skipped plugins create no invocation
  child.
- [ ] Child admission reuses immutable session authority basis and its frozen
  placement plan without a fresh top-level owner decision, captures its own
  exact deployment revision, and still satisfies Article XI once per invocation.
- [ ] Every child admission and claim validates current session liveness,
  authority validity, expiry, and revocation through the kernel.
- [ ] Stopping, interrupting, expiring, revoking, or cancelling the session prevents new
  children and blocks late child output from meeting state.
- [ ] Provider cancellation is attempted; unknown remote outcomes close
  indeterminate instead of success/failure guesswork.
- [ ] Session and child receipts contain no transcript body, prompt, token
  stream, or audio frame.
- [ ] Existing live/deferred/plugin output and retry idempotency remain intact.

## Test plan

- Unit: focused meeting session, queue, plugin, child-cardinality, retry,
  fallback, cancellation, expiry, and no-content-in-journal tests.
- Integration: `uv run pytest -q tests/integration/test_intel_streaming.py tests/integration/test_meeting_intel_recovery.py` plus a real LAN meeting window and deferred plugin run.
- Manual / device: start a real meeting intelligence session, produce two model
  windows and one plugin call, interrupt during streaming, and inspect one
  parent plus exact children and terminal receipts.

## Notes / open questions

"Per session" is a latency and authority ruling, not an exemption. The parent
admits the session once; each provider call still gets its own lightweight child
admission and terminal receipt.
