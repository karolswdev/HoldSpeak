# HS-131-17 design — Meetings lose the parallel engine

**Status:** RATIFIED (Sol, 2026-08-14)
**Decision boundary:** delete the dormant session-owned MIR branch; retain the separately admitted deferred routing product. A live `MeetingSession` keeps only its frozen `MeetingIntelPlan`, parent context, and explicit liveness state. It never owns a `MeetingIntel` engine. Every retained provider dispatch is built from the plan's exact revision inside one claimed `inference.invoke@1` child.

## Context and ruling

Three residuals remain after HS-131-08:

1. `MeetingSession.start()` checks mutable runtime configuration and constructs a
   long-lived `MeetingIntel` beside the already frozen plan.
2. `add_bookmark()` uses that object as a liveness flag, then a background thread
   calls `generate_bookmark_label()` directly.
3. `stop()` retains an opt-in `mir_routing_enabled` branch that calls the old MIR
   pipeline after the live parent has closed.

The third branch is dormant in production: `WebRuntime._start_meeting()` does not
supply its enable flag, plugin host, database, or tuning parameters. Tests are its
only caller. Current routed-intelligence behavior lives elsewhere and is already
admitted: `intel_queue.process_next_intel_job()` reads
`MeetingConfig.intent_router_enabled`, admits a fresh
`meeting.deferred-intel-job`, and gives each routed plugin attempt its own child.
The config, plugin system, route-preview/manual tools, and deferred chain therefore
remain. Only the duplicate automatic `MeetingSession.stop()` pipeline is deleted.
Enabling it would create a second product path with no present user contract.

This is the least product work that makes the meeting honest. It follows
Constitution Article VI.2 (failure and refusal stay visible), Article IX (the
runtime and census prove the claim), and Article XI.1–3 (one admitted child and
one terminal receipt per consequential model attempt).

## 1. Session state without an engine

`MeetingSession` no longer imports, constructs, stores, or clears
`MeetingIntel`. It retains:

- `_intel_plan`: the immutable capability → ordered revision map;
- `_intel_parent`: the opaque authenticated live-parent context;
- `_intel_closed`: the stop/cancellation fence; and
- `_intel_live`: an explicit boolean saying live intelligence may schedule work.

`_intel_live` becomes true only when intelligence is enabled and parent admission
successfully froze a plan containing `live-analysis`. It becomes false on named
refusal, provider failure/deferral, stop handoff, and cleanup. Capability checks
come from `plan.has(capability)`; liveness never comes from the presence of an
engine object.

Start does not preflight or load a provider. Plan resolution remains the readiness
and placement decision. The first actual child constructs the exact frozen
revision through `InferenceRunner`; a construction/provider failure takes the
existing queued-or-error path. This avoids loading a model merely to announce
that a meeting is live.

A start without an authenticated intelligence principal still records. Admission
refuses by name, `_intel_live` stays false, and neither an inference child nor an
engine exists.

## 2. Bookmark state machine

`add_bookmark()` always creates the deterministic timestamp label first.

- Explicit label, `auto_label=False`, or no local transcript context: return the
  deterministic bookmark; no child exists.
- Planned `bookmark-label` capability plus a live parent: launch the existing
  background refinement, but call `_admitted_bookmark_label()` with the local
  context and the latest earned meeting summary (or the empty summary when none
  exists).
- The admitted seam selects the exact frozen revision, admits one trusted child,
  builds the engine only inside that child's dispatch context, and publishes from
  its terminal receipt.
- Refusal, cancellation, provider failure, or a discarded projection leaves the
  deterministic label intact. A stop that wins first sets `_intel_closed`; a
  late label cannot update the bookmark.

The old context-only `MeetingIntel.generate_bookmark_label()` leaf has no other
caller and is deleted. `generate_bookmark_label_with_context()` remains the one
adapter leaf used by live and deferred admitted children.

## 3. MIR deletion boundary

Delete from `MeetingSession`:

- the `mir_routing_enabled`, profile, host, database, tuning, synthesis,
  disabled-plugin, and segment-probe constructor inputs and stored fields;
- plugin enumeration from the live session plan;
- the routed-intelligence displaced-work inference based on those fields;
- the post-stop `process_meeting_state()` branch and its proposal callback; and
- tests whose only purpose is to activate that private branch.

Also remove the dead MIR arguments and segment-probe placeholder from
`WebRuntime._start_meeting()`.

Do **not** delete `MeetingConfig.intent_router_enabled`, MIR persistence, plugins,
manual route tools, or the deferred queue chain. They are a current product path
and already execute under the separately admitted deferred parent. This ruling
removes one dormant duplicate; it does not erase routed meeting artifacts.

## 4. Stop and deferred behavior

HS-131-08's ordering remains unchanged:

1. mark the live session closed;
2. cancel/drain the live parent and discard late stages;
3. close the live parent honestly;
4. durably enqueue final analysis, deferred bookmark labels, and auto-title before
   `stop()` returns; and
5. let the deferred job decide routed intelligence from current configuration
   under its own parent.

The live session no longer adds `routed-intelligence` by consulting private MIR
flags. The deferred worker already owns that decision. Recording-only sessions
with no admitted parent enqueue no intelligence and construct no engine.

## 5. Executable proof

- Start sentinel: an authenticated start freezes the plan and admits one parent
  while constructing zero engines; the first live child constructs exactly one.
- Bookmark cardinality: a contextual automatic label creates one child with the
  meeting parent, exact `bookmark-label` revision, and one terminal receipt;
  explicit/deterministic/no-context labels create none.
- Refusal and stop: no-principal recording creates no engine/child; closed or
  cancelled sessions cannot publish a late label.
- MIR deletion: constructor and stop-path tests no longer expose the private live
  MIR switch; deferred routed-intelligence tests remain green.
- Census: `dormant-mir`, `legacy-live-meeting-engine`, and
  `bookmark-auto-label` leave the blocking ledger; no meeting scope enters
  `ADAPTER_ALLOWLIST`, and restoring either direct call fails as unregistered.

## Sol disposition

**DELETE dormant session MIR; ADMIT the bookmark through the existing child seam;
DELETE the parallel live engine.** No compatibility fallback is retained. The
current deferred routing product is preserved exactly where it is already
admitted. Hostile scheduler proofs, future live MIR, and broader plugin redesign
are below this story's functional bar unless ordinary use reproduces a failure.
