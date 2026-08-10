# Phase 131 — One Admission Path

**Status:** IN PROGRESS (3/12).

**Last updated:** 2026-08-09.

## Goal

Every actual model invocation enters one reusable inference runner, receives one
kernel admission before execution, and ends in exactly one immutable terminal
receipt. Nested invocations are admitted as children of the run or session that
offered them. HoldSpeak may have many domain projections of a run, but it has
one door through which intelligence acts.

## Scope

### In

- A versioned deployment revision captured at admission and used unchanged at
  execution, with the sync registry and the seven Phase-130-assigned sync
  failures repaired in the same phase.
- One runner for inference admission, execution, cancellation, child causation,
  terminal receipts, and domain result references.
- Ask, Agent run/chat, Sequence, Workflow, manual Workbench work, Workbench
  memory writeback, Rails, Decisions, Delivery, and remaining service-side
  intelligence callers moved onto that runner.
- Meeting, dictation, and configured-wake session admission, including shared
  local Whisper transcription. A session pays the owner authority and placement
  decision once; each actual model invocation is an admitted, causally linked
  child (a continuation of that session) with its own terminal receipt, and each
  child claim rechecks liveness and revocation.
- Explicitly enabled Workbench and Cadence schedules represented as bounded
  delegation for the exact work, effective target, and cadence until changed
  or disabled.
- A mechanical fence that fails when product code opens another inference
  execution path.
- Entry-point documentation and a real-model walk.

### Out

- Any Swift, iPad, iPhone, or native Apple implementation. The finished Python
  and React/Vite contract will specify that later work.
- Phase 132's web ownership consolidation and Phase 133's product-language
  consolidation.
- The 94 unrelated inherited Phase 118–128 failures assigned by HS-130-10.
- `capability_ref`, generated-contract machinery, or a general workflow-hosting
  expansion.
- Changes to the Constitution. This phase implements Articles V and XI as
  ratified.
- Journaling token streams, prompts, audio frames, or model payload bodies.

## Constitutional grounding

- **Article V.2:** every attempt leaves a receipt. Refusal, cancellation,
  failure, indeterminate outcome, and success all close through the same
  terminal path.
- **Article IX:** the phase closes only after the real runtime and real model
  have exercised success, refusal, cancellation, nested child admission,
  scheduled delegation, and session admission.
- **Article XI.1–2:** invoking a model is consequential; nesting exempts
  nothing. One parent run may own several model-invocation children, but no
  child may disappear inside the parent's receipt.
- **Article XI.3:** deployment, payload hash, target, and authority basis are
  immutable after admission. Execution uses the admitted revision, not a
  mutable profile re-read.
- **Article XI.4:** the scheduler authenticates as the scheduler. It may act
  only under owner-created bounded delegation and must never manufacture an
  owner principal.
- **Article XI.5:** token streams and other computation inside an admitted
  invocation are not separately journaled. The invocation and its effects are.

## Pre-charter execution census

Two current-tree Terra audits on `0fc14aca` traced actual model execution before
this charter was written. This is the bounded migration list, not a discovery
story:

| Execution family | Known production seams | Owning story |
|---|---|---|
| Ask and saved Agent | `ask_service.py`; Recipe run and chat | HS-131-03 |
| Sequence and Workflow | `chains.py`; `workflows.py` model steps/nodes | HS-131-04 |
| Workbench | item generation and memory writeback | HS-131-05 |
| Recurring work | Workbench conductor and any Cadence-triggered model run | HS-131-06 |
| Finite services | Rails summary, Decision promotion, Delivery review, voice resolution, local/cloud/mesh execution | HS-131-07 |
| Meeting intelligence | live analysis, deferred queue, retries, routed plugins | HS-131-08 |
| Shared transcription and dictation | `Transcriber` local Whisper including MLX silent-audio preload/warmup, meeting transcription, dictation capture, wake capture, transcription/classification/rewrite/punctuation runtimes | HS-131-09 |
| Provider adapters and bypass prevention | all SDK, local runtime, streaming, fallback, mesh, and `.transcribe()` dispatch forms | HS-131-02 and HS-131-10 |

The final fence may prove the census complete; it may not silently enlarge an
already shipped migration story. Any newly discovered model execution site is a
blocking charter amendment with an explicit owner story before HS-131-10 can
close. This preserves the standing rule against pre-implementation measurement
gates while keeping every known site bounded now.

## Exit criteria (evidence required)

- [ ] One production inference runner owns admission, exact-revision execution,
  child causation, cancellation, and terminal receipt closure.
- [ ] Ask, Agent, Sequence, Workflow, Workbench, Rails, Decisions, Delivery,
  Cadence, meeting intelligence/transcription, dictation, wake transcription,
  and every other product model caller in the pre-charter census reach that
  runner; the one-path fence exits 0.
- [ ] Every actual model invocation creates exactly one admitted operation and
  one terminal receipt; multi-step Sequence and Workflow runs prove parent plus
  one child per model step.
- [ ] A profile change after admission cannot change the endpoint, model,
  boundary, or secret slot used by that invocation.
- [ ] The deployment revision and its receipt reference remain resolvable after
  sync; all seven HS-130-10 sync-registry tests pass.
- [ ] Cancellation prevents late model output from becoming a domain result and
  closes the invocation once as cancelled.
- [ ] An enabled schedule proves bounded delegation; changed, disabled,
  expired, or mismatched terms refuse by name without a model call.
- [ ] Meeting, dictation, and configured wake each prove the correct admitted
  session parent with causally linked invocation children, including shared
  local Whisper, without journaling audio or tokens.
- [ ] Focused tests, the web suite, and the full backend suite are captured and
  read. Any inherited failures are diffed by test name against HS-130-10.
- [ ] The real-model walk proves the contract against the live LAN endpoint and
  stores its output under the phase assets.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-131-01 | Frozen deployment revisions and one sync registry | done | [story-01](./story-01-frozen-deployment-revisions.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-131-02 | The admitted invocation runner | done | [story-02](./story-02-admitted-invocation-runner.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-131-03 | Ask and Agents take the same door | done | [story-03](./story-03-ask-and-agents.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-131-04 | Sequence and Workflow admit every model step | done | [story-04](./story-04-sequence-and-workflow.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-131-05 | Workbench work and memory cannot outrun cancellation | done | [story-05](./story-05-workbench-and-memory.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-131-06 | Scheduled work carries bounded delegation | backlog | [story-06](./story-06-bounded-schedules.md) | — |
| HS-131-07 | The remaining direct callers join the spine | backlog | [story-07](./story-07-service-callers.md) | — |
| HS-131-08 | Meetings are admitted per session | backlog | [story-08](./story-08-meeting-sessions.md) | — |
| HS-131-09 | Dictation and transcription are admitted per session | backlog | [story-09](./story-09-dictation-sessions.md) | — |
| HS-131-10 | The one-path fence | backlog | [story-10](./story-10-one-path-fence.md) | — |
| HS-131-11 | The entry-point contract | backlog | [story-11](./story-11-entry-point-docs.md) | — |
| HS-131-12 | The walk | backlog | [story-12](./story-12-the-walk.md) | — |

## Delivery order

1. **Foundation:** HS-131-01 freezes the thing admission names and repairs the
   sync contract; HS-131-02 establishes the only runner.
2. **Finite runs:** HS-131-03 and HS-131-04 migrate the five issue-450 run
   families with parent-child semantics.
3. **Workbench and authority:** HS-131-05 migrates manual work and cancellation;
   HS-131-06 adds owner-created bounded delegation for schedules.
4. **Remaining callers and sessions:** HS-131-07 migrates direct service paths;
   HS-131-08 and HS-131-09 establish session parents and lightweight children.
5. **Lock and prove:** HS-131-10 closes the census, HS-131-11 updates the entry
   points, and HS-131-12 performs the real-model walk and full-suite diff.

Stories ship one at a time through the Delivery Workbench gate. Implementation
uses the standing Opus implementer, Terra adversarial verifier, Sol final
judgment pipeline. Terra runs focused tests; Sol reads the implementation,
verification, and full-suite output before any done call.

## Where we are

Phase 130 is merged on `main` at `0fc14aca`; this phase is the next slice of
issue #450. The owner has now resolved both charter preconditions: meeting and
dictation admission is per session, and deliberately enabling a recurring
schedule grants bounded delegation for that exact work, effective target, and
cadence until changed or disabled. Terra's hostile charter review returned
seven findings; Sol sustained and amended every one, then recorded the final
judgment in [SOL-CHARTER-COUNSEL](./SOL-CHARTER-COUNSEL.md).
HS-131-01 is done: deployment revisions are immutable and content-addressed
(schema v44), engine construction has no mutable profile re-read, one
`SYNC_REGISTRY` derives the entire Python/web sync taxonomy, and revision
references round-trip over sync without credentials. The six assigned
HS-130-10 sync failures are repaired — full-suite diff against the pinned
charter baseline shows zero new failure names (84→78 failed, 17 errors
unchanged; artifacts under `assets/hs-131-01/`). The Swift-as-authority test
is retired for a stricter Python-contract assertion.
HS-131-02 is done: the admitted invocation runner exists — one gateway
owning admission → claim → exact-revision dispatch → one terminal receipt,
with `cancelled` first-class (schema v45), a per-invocation state machine
whose cancellation semantics survived a fourteen-round Sol counsel loop
(ledger in [SOL-COUNSEL-HS-131-02](./SOL-COUNSEL-HS-131-02.md); final
verdict: ratify), warrant-bound continuation identities, full-ancestor
claim revalidation, and a real-model walk on the live LAN endpoint
(revision immutability proven on metal; mid-generation cancellation
suppressed late output). Ship-gate full suite: zero new failure names,
one repaired (`test_migrates_v38_database_to_decision_commitments`).
The publication-staging protocol is HS-131-03's blocking criterion by
visible amendment.
HS-131-03 is done — the first design-beat story: Sol ruled the
ProjectionStager design before implementation (eight amendments on
paper), then Ask and Recipe run/chat migrated onto the admitted runner
with staged projections (schema v46), a broker-owned runner making
cancellation reachable across request lifetimes, and cancel routes.
Four defects were caught by the layered verification (metal walk, the
choreographed proofs, Sol's review, the full gate) — including a real
event-loop regression — and each is fixed with a regression test. Gate:
zero unaccounted new names, one repaired
(uat mesh dispatch). Sol: ratify with five named design-floor
reservations for the sitting.
HS-131-04 is done — the second design-beat story, and the deepest counsel
loop yet resolved on paper-plus-metal: Sol ruled the Sequence/Workflow
design before implementation (eight amendments), then rode five total
rounds to RATIFY FOR STORY CLOSE. Every Sequence step and Workflow model
node now dispatches as an admitted child of one authenticated native
parent (`sequence.run@1`/`workflow.run@1`, schema v47-v49): trusted-parent
admission is one atomic broker transaction (closing the causation
owner-parent loophole), `OuterRunContext` is an unexportable epoch-scoped
capability, parent closure is a terminal CAS electing the receipt winner,
abandoned parents are lease-protected (10s heartbeat daemon, 90s window,
stale-lease re-election in the closing transaction) and reconciled
indeterminate, advancement is a durable compare-and-swap that fences late
and superseded child output, aggregates stage before their receipts, and
child budgets are finite and transactional. The seventh HS-130-10 ledger
failure (`test_ipad_synced_graph_workflow_runs_on_the_hub`) is repaired
with the double confined to provider construction. Real-metal walk on .43
(parent+children receipts, pure nodes mint no children, mid-run cancel
fences admission). Gate: zero new failure names vs the HS-131-03
baseline, SEVEN repaired (the sync test + six intel_cloud tail flakes);
one gate-found product bug (lease daemon leak across broker replacement)
fixed. Sol's three reservations ride in the evidence.
HS-131-05 is done — the first story shipped under the owner's yolo-mode
rigor bar (design ruled in ONE Sol round; two implementation rounds to
RATIFY FOR STORY CLOSE): manual Workbench execution admits one
authenticated workbench.run@1 parent per attempt with one child per
item-generation call and the memory writeback surfaced as its own
distinct holdspeak.workbench-memory@1 child (schema v50-v51), per-child
Phase-130 placement, receipt-gated item/memory/artifact/history
projections, and parent-scoped cancellation with the deadline as an
epoch-changing fence. The layered verification caught five REAL defects
— including a production concurrency bug (per-request _configure
rebuilds destroying every in-flight parent controller) and a
100%-deterministic memory-child payload-hash refusal that vacuous tests
had masked — all fixed with regression tests. Real-metal walk on .43
(item+memory children with receipts; disabled memory mints none;
mid-run cancel honest end-to-end). Gate: zero deterministic new names
vs the HS-131-04 baseline; two run-to-run tail flakes accounted with
serial passes. Sol's reservation (best-effort provider signal after the
durable fence) rides in the evidence.
Next: HS-131-06, bounded schedules.
The roadmap still has nine inherited structural lint errors in old phases; they
are named baseline and are not silently bundled into this product phase.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A wrapper records receipts while callers still execute directly | high | Runner owns execution, not just journaling; the fence scans direct engine/provider invocations | Any migrated caller can invoke a model after bypassing the runner |
| Session admission becomes an exemption for utterance model calls | high | Session keeps immutable authority basis and a frozen plan; each invocation is an admitted child with its own receipt, and each child claim rechecks liveness/revocation | A model call exists only inside the parent receipt, or a revoked session still dispatches |
| Scheduled work fabricates owner identity | high | Scheduler principal plus owner-created delegation ref; kernel derives authority | A scheduled receipt names the owner as actor, or a tick runs without a live matching delegation |
| Deployment revision is a receipt-only copy that cannot execute or sync | medium | Executor consumes the admitted revision; sync round-trip and post-admission mutation tests ship with HS-131-01 | Engine construction re-reads the mutable profile row |
| Cancellation closes the receipt but late output still writes domain state | medium | One atomic terminal transition gates result projection | Any cancelled invocation can mint an answer, memory, artifact, or step result |
| The runner becomes a service God object | medium | Keep domain shaping in callers and kernel policy in the kernel; runner owns only invocation lifecycle | Runner branches on Ask, Workbench, Sequence, Workflow, meeting, or dictation domain types |
| Full-suite inherited debt masks a regression | medium | Diff failing test names against HS-130-10 after every shipping story; zero new names allowed | A new failure appears or an old name changes without classification |

## Decisions made (this phase)

- 2026-08-09 — **Issue #450 AC3 is corrected to Article XI.** Every actual
  model invocation is admitted once and receives one terminal receipt. Nested
  invocations are children of the run or session that offered them; an outer
  receipt cannot absorb them. This applies the Phase-130 Sol counsel and the
  owner's authorization to continue the program.
- 2026-08-09 — **Meeting and dictation admission is per session.** One session
  holds immutable authority basis and a frozen placement/deployment plan; each
  model invocation inside it is an admitted child operation, continuing the
  session with its own exact deployment revision rather than making a fresh
  top-level owner decision. Every child admission and claim still asks the
  kernel whether the session and authority are live, unexpired, and unrevoked.
  This records the owner's "per sesh" ruling without assuming every capability
  in a session uses the same model or turning the session into an exemption.
- 2026-08-09 — **Recurring schedules use bounded delegation.** Deliberately
  enabling a Workbench or Cadence schedule approves its exact work, effective
  target, and cadence until changed or disabled. Every tick still receives its
  own admission and receipt. The scheduler remains the actor; the owner is the
  delegation authority, never an impersonated principal.
- 2026-08-09 — **Disabling or changing bounded terms invalidates delegation.**
  A target, work definition, or cadence change cannot inherit old authority.
  A mismatched tick refuses by name before model execution. Delegation is
  device-local: synced schedule configuration cannot grant another machine the
  right to run.
- 2026-08-09 — **Deployment revisions and sync ship together.** A receipt that
  names an immutable revision must remain resolvable on peers; a local-only
  snapshot would create another half-truth.
- 2026-08-09 — **The pre-charter execution census is the migration boundary.**
  Ask/Agent, Sequence/Workflow, Workbench/manual/scheduled/memory, finite
  services, meeting intelligence, shared local Whisper transcription including
  MLX preload/warmup, meeting transcription, dictation capture, wake capture,
  and dictation model runtimes all have named owner stories. A new site found
  by the final fence blocks and amends the charter; it does not silently expand
  a shipped story.
- 2026-08-09 — **Model warmup is a model invocation.** MLX silent-audio preload
  receives normal invocation admission and a terminal receipt. When performed
  inside a live session it is that session's child. A pre-session preload acts
  as the authenticated runtime service under the owner's explicit configured
  local-model/preload authority basis, never as the owner; without that basis it
  defers to first-session admission or refuses before invoking the model.
- 2026-08-09 — **No new product surface.** Phase 131 changes runtime truth and
  receipts. The web ownership and language work stays in Phases 132 and 133.
- 2026-08-09 — **`cancelled` is a first-class kernel terminal state**
  (HS-131-02, Sol counsel round 1, sustained). A receipt whose outcome and
  durable state disagree is a representational contradiction; schema v45
  extends both kernel CHECK constraints with a rebuild migration preserving
  immutable evidence. Owner may overrule at the sitting.
- 2026-08-09 — **The durable publication-staging protocol is HS-131-03's
  blocking criterion** (Sol counsel round 2, sustained; owner may overrule).
  HS-131-02 ships the in-process gate, the atomic transition+receipt
  transaction, and defined publish-failure semantics; the cross-table crash
  window closes with one shared staging primitive in HS-131-03, required by
  every later domain migration, never re-implemented per story. Recorded in
  both story files and [SOL-COUNSEL-HS-131-02](./SOL-COUNSEL-HS-131-02.md).

## Decisions deferred

- The 94 unrelated inherited failures remain assigned to a separate remediation
  phase. Trigger: the owner's scope ruling; default: do not absorb them here.
- DecisionRecord-to-receipt lifecycle links remain Phase 133. Trigger: the
  language phase; default: preserve the Phase-130 rename and current behavior.
- Workbench `capability_ref` remains Backlog Candidate AA. Trigger: a separately
  chartered capability-hosting phase; default: Agent-backed Workbench only.
