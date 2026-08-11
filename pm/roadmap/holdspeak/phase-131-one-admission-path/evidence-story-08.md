# Evidence - HS-131-08

- **Story:** HS-131-08 - Meetings are admitted per session
- **Status:** done
- **Date:** 2026-08-10

## Proof

### Captured run — 2026-08-11T01:53:34Z

- **Command:** `env HOME=/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/tmp.F7mDwJnMZ1 uv run pytest -q tests/unit/test_meeting_session_admission.py tests/unit/test_meeting_deferred_admission.py tests/unit/test_meeting_plugins.py tests/unit/test_meeting_session.py tests/integration/test_meeting_intel_recovery.py tests/unit/test_kernel_effect_fence.py tests/unit/test_intel_queue.py tests/unit/test_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d57c7927d80f4832376a1b65aa7482461e4ffcec

```text
........................................................................ [ 54%]
...........................................................              [100%]
131 passed in 51.35s
```

## Verification narrative

### The design beat (committed separately as a2976b89)

Terra drafted [DESIGN-HS-131-08](./DESIGN-HS-131-08.md) applying the owner's
per-session ruling; Sol ruled RATIFY-AS-AMENDED in ONE round with two
binding amendments (ordered immutable primary+fallback revision sets per
capability; a durable stop-to-deferred handoff owning every displaced final
seam under honest completion state) plus scope rulings: the bookmark-label
and auto-title provider seams the draft discovered are ABSORBED into this
story (intra-family seams inside the story's own AC), device-started
intelligence is refused-by-default until a narrow meeting-capture
service-principal issuer exists, and a missing plan capability refuses,
never falls back.

### What shipped

- **Schema v54 then v55**: v54 admits parent kinds `meeting.session` and
  `meeting.deferred-intel-job`; v55 adds the durable structured
  `intel_jobs.displaced_work` column (Sol: "the correct durable contract").
  The stale canonical schema fixture was regenerated (Sol accepted
  in-story: the v55 column made the fixture meaningful again; the folded
  prior-phase drift is snapshot maintenance).
- **One authenticated session parent** (`meeting_session/intel_admission.py`,
  `session.py`, `runtime/meeting_glue.py`, `services/meeting_service.py`):
  the route principal threads through `_start_meeting` into MeetingSession;
  one `meeting.session` parent admits right after MeetingState creation
  (12h deadline, 4096 provider-attempt budget, idempotent per meeting);
  the OuterRunContext lives only on the live session. A no-principal start
  refuses intelligence honestly (`meeting_intel_principal_required`) while
  recording proceeds; no OWNER synthesis.
- **The frozen MeetingIntelPlan@1** (`meeting_session/intel_plan.py`):
  content-free per-capability ORDERED revision lists. Sol Amendment 1 made
  the legacy intra-engine auto local→cloud fallback honest: the
  no-adoption auto path freezes the cloud leg as a REAL second deployment
  revision (nameable `hub_default_cloud` destination; unreachable cloud →
  one entry with the reason recorded), `internal_provider_fallback` is
  permanently false (this_machine engines pinned local via one shared
  rule), and `run_admitted_capability` walks the entries — one admitted
  child per entry, advancing ONLY on an honest `failed` outcome
  (cancelled/refused/indeterminate terminal). Provider failures RETURNED
  as `IntelResult.error` (the established production vocabulary) are
  classified before receipt election (`provider_error_result` sanitized
  failure) so the child receipt never says succeeded for a failed attempt
  and the frozen fallback actually engages; on exhaustion the callers see
  their existing error vocabulary byte-identically.
- **Live windows, bookmark labels, auto-title**
  (`meeting_session/intel_analysis.py`, `intel_child.py`): every actual
  model window is one trusted child (contract
  `holdspeak.meeting-live-analysis@1`; transcript text dispatch-only,
  hashed into the contract, never journaled; sanitized adapter errors);
  empty/superseded windows admit nothing; token streaming stays ephemeral;
  window snapshots are staged projections with the cancelled-parent
  discard. The two ABSORBED seams run as admitted children
  (`holdspeak.meeting-bookmark-label@1`, `holdspeak.meeting-auto-title@1`)
  with capability-missing refusals.
- **The stop handoff (Amendment 2)**: stop cancels the live parent FIRST
  (provider cancel attempted; unknown remote → indeterminate; staged live
  projections discarded), then durably enqueues the displaced work —
  final analysis, bookmark labels, auto-title, routed plugins — as a
  structured slug list BEFORE stop returns; the meeting stays honestly
  `queued` (a mid-meeting ready stamp is cleared) and reaches `ready` only
  after ALL displaced work settles. The late-ready race is fenced under
  the session lock: the closed flag rises before cancel/enqueue and any
  later live-window apply or status stamp is discarded (verified
  non-vacuously — neutralizing the gate makes the race test fail).
- **The deferred queue** (`intel_queue.py`,
  `meeting_session/deferred_admission.py`,
  `kernel/meeting_plugin_projection.py`): each claimed job admits ONE
  `meeting.deferred-intel-job` parent under the narrow
  `meeting-intel-queue` SERVICE principal over a freshly frozen plan
  (finite: 30min deadline; budget = 1 base + planned plugins + displaced
  children + 2 retry allowance); base analysis, each executed plugin, and
  the displaced bookmark/title work are trusted children; deduped/skipped
  plugins admit nothing; every queue retry is a NEW parent (idempotency
  includes requested_at so manual requeues mint new bounded parents); a
  closed live session is never revived (`meeting_session_closed`). Plugin
  runs/artifacts and the title/bookmark writes are in-transaction
  receipt-gated materializers (title never overwrites an owner title).
- **Plugin engine honesty**: the plugin host gained an injected-engine
  seam (`bound_llm_engine`); an executed llm plugin runs ON the
  revision-built engine inside the admitted child's cancellation seam; a
  plugin that cannot take the injection refuses
  `plugin_llm_engine_not_injectable` rather than self-building.

### The counsel ledger (implementation)

Sol rode THREE implementation rounds to RATIFY-WITH-RESERVATIONS:

- **Round 1** (4 blockers): the intra-engine auto fallback silently
  retargeted despite plan metadata; plugin llm dispatches ignored their
  named revisions; the displaced bookmark/auto-title work was queued but
  never executed; a live child finalizing around stop's join timeout could
  stamp ready after queued.
- **Round 2** (1 blocker): the fallback advanced only on kernel `failed` —
  a provider failure RETURNED as IntelResult.error closed the child
  succeeded and never engaged the frozen cloud entry.
- **Round 3**: the returned-error classification landed;
  **RATIFY-WITH-RESERVATIONS**, both amendments discharged, all
  twenty-five acceptance areas pass.

### Sol's sitting-visible reservations (final)

1. **R1 — configuration source skew**: the plan freezes
   `Config.load().meeting` at admission rather than the constructor's
   copied terms; dispatch follows the admitted revision so receipts stay
   honest.
2. **R2 — crash after admission**: a start failure after admission relies
   on lease reconciliation rather than explicit cleanup.
3. **R3 — dormant MIR branch**: unadmitted MIR could run if
   `mir_routing_enabled=True` were ever enabled without an admitted
   parent; no production caller enables it; the seam rides the HS-131-10
   fence before activation.
4. **R6 — symbolic schema pins**: two schema tests now assert
   `SCHEMA_VERSION` symbolically; at least one independent literal
   sentinel remains (the four decision/monday pin files).
5. **R9 — inherited production defect**: the undefined `ConflictError` at
   `web/routes/meetings/crud.py:161` is a REAL live bug (inherited,
   unrelated to this path) needing a separate prompt hotfix — surfaced to
   the owner here.

### The verification liturgy

1. **Two-part implementation** (the story was too large for one agent):
   Part A (schema/plan/session/live windows/absorbed seams) and Part B
   (stop handoff/deferred queue/plugins), each with honest flag lists;
   the four-blocker and one-blocker fix rounds followed Sol's reviews.
2. **Focused suites** (orchestrator re-ran after every round, output read
   from files): 268 tests green at the widest run — both admission suites
   (34 tests incl. the fallback, race, and displaced-work proofs), the
   migrated meeting/plugin/session suites, meeting_intel_recovery
   integration, the kernel fence, test_db against the regenerated
   fixture, all v55 pins, and every prior-story regression suite.
   intel_streaming stays at its INHERITED 9f/34p (proven byte-identical
   on a HEAD copy).
3. **Real-metal walk**
   (`assets/hs-131-08/walk_meeting_session_lan.py` on .43; output in
   `assets/hs-131-08/walk-output.txt`; capture hardware stubbed, NO
   provider fakes): four legs green after every round — one admitted
   session parent over a plan freezing the real lan43 revision; two live
   windows as two admitted succeeded children (the .43 server's forced
   line-JSON didn't parse into an IntelResult — the recurring endpoint
   observation, recorded); stop during a streaming third window →
   parent CANCELLED, work durably enqueued, meeting honestly queued; the
   deferred job as its own admitted parent under the queue service
   principal running TWO succeeded children on metal, with the meeting
   reaching ready only after the job settled.
4. **Full gate** on the quiet tree: accounting below.

### Gate accounting (final run)

Baseline: `assets/hs-131-07/gate-failures.txt` (100 normalized names).
This story's gate: `assets/hs-131-08/gate-failures.txt` (96 names,
`gate-tail.txt` alongside). Diff: **ZERO deterministic new names, NINE
disappeared** — the eight github-actuator names were the prior story's
accounted flake family (their passing here confirms the classification),
and `test_fresh_schema_matches_canonical_snapshot` is a GENUINE REPAIR
(the stale canonical fixture regenerated with the v55 schema; it had been
failing on the inherited baseline for several phases). Five new names are
accounted flakes: four `test_voice_macro_connector` subprocess-argv tests
(the same species as the actuator family) plus the recurring
`test_cloud_stream_forwards_endpoint_deltas` — all 10/10 on an immediate
serial re-run on identical code.

### Version-pin note

Two schema tests now assert `SCHEMA_VERSION` symbolically (Sol R6:
accepted with the reservation that literal sentinels must survive — the
four decision/monday pin files remain literal, updated 54→55 by the
orchestrator after the v55 bump).
