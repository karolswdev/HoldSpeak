# Phase 131 — One Admission Path

**Status:** IN PROGRESS (15/17).

**Last updated:** 2026-08-14.

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

## Fence amendment wave

HS-131-10 classified 145 executable/model-bearing sites with zero unregistered
sites, but retained 48 pinned findings across eleven real or latent execution
families. On 2026-08-12 the owner chartered the smallest five-story wave that
covers the complete ledger:

| Story | Families owned |
|---|---|
| HS-131-13 | Cadence, second Decisions route, dormant Delivery review, and retirement of `build_intel_for_target` |
| HS-131-14 | Fourteen builtin plugin default providers plus `segment_probe`; retirement of uncontextual provider construction |
| HS-131-15 | Dictation dry-run and CLI command; design beat chooses admitted session versus lexical-only |
| HS-131-16 | Mesh receiver authority; design beat chooses verified envelope plus local claim versus node-side runner |
| HS-131-17 | Dormant MIR, parallel live meeting engine, and bookmark auto-label |

This amendment records work, not an Article-XI exception. All five stories have
landed, the same census returns zero findings, and HS-131-10 is closed.
HS-131-11 and HS-131-12 are unblocked.

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
| HS-131-06 | Scheduled work carries bounded delegation | done | [story-06](./story-06-bounded-schedules.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-131-07 | The remaining direct callers join the spine | done | [story-07](./story-07-service-callers.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-131-08 | Meetings are admitted per session | done | [story-08](./story-08-meeting-sessions.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-131-09 | Dictation and transcription are admitted per session | done | [story-09](./story-09-dictation-sessions.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-131-10 | The one-path fence | done | [story-10](./story-10-one-path-fence.md) | [evidence-story-10](./evidence-story-10.md) |
| HS-131-11 | The entry-point contract | backlog | [story-11](./story-11-entry-point-docs.md) | — |
| HS-131-12 | The walk | backlog | [story-12](./story-12-the-walk.md) | — |
| HS-131-13 | Residual services take the admitted door | done | [story-13](./story-13-residual-service-admission.md) | [evidence-story-13](./evidence-story-13.md) |
| HS-131-14 | Plugins receive admitted intelligence | done | [story-14](./story-14-plugin-provider-admission.md) | [evidence-story-14](./evidence-story-14.md) |
| HS-131-15 | Speech side doors become sessions or stay lexical | done | [story-15](./story-15-speech-side-door-admission.md) | [evidence-story-15](./evidence-story-15.md) |
| HS-131-16 | The mesh receiver proves authority locally | done | [story-16](./story-16-mesh-receiver-authority.md) | [evidence-story-16](./evidence-story-16.md) |
| HS-131-17 | Meetings lose the parallel engine | done | [story-17](./story-17-meeting-residual-admission.md) | [evidence-story-17](./evidence-story-17.md) |

## Delivery order

1. **Foundation:** HS-131-01 freezes the thing admission names and repairs the
   sync contract; HS-131-02 establishes the only runner.
2. **Finite runs:** HS-131-03 and HS-131-04 migrate the five issue-450 run
   families with parent-child semantics.
3. **Workbench and authority:** HS-131-05 migrates manual work and cancellation;
   HS-131-06 adds owner-created bounded delegation for schedules.
4. **Remaining callers and sessions:** HS-131-07 migrates direct service paths;
   HS-131-08 and HS-131-09 establish session parents and lightweight children.
5. **Fence checkpoint:** HS-131-10 installs the executable fence, records the
   complete findings ledger, and remains blocked rather than granting an
   exception.
6. **Amend the residuals:** HS-131-13 through HS-131-17 delete or admit the five
   chartered groups; then HS-131-10 reruns the census and closes at zero
   findings.
7. **Document and prove:** HS-131-11 updates the entry points and HS-131-12
   performs the assembled real-model walk and full-suite diff.

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
HS-131-06 is done — scheduled Workbench work now runs on bounded owner
delegation (design ruled in ONE Sol round with nine binding amendments;
four implementation rounds to RATIFY-WITH-RESERVATIONS): deliberately
enabling a schedule mints one device-local, exact-terms delegation
(schema v52: `kernel_schedule_delegations` under a partial live-unique
index, durable due-minute tick claims, `workbenches.schedule_revision`),
the conductor authenticates as a rights-empty SCHEDULER principal, and
every due tick admits atomically — term re-verification, tick claim,
parent persistence, and delegator/authority-basis provenance in ONE
transaction, with every named refusal (schedule_disabled,
delegation_missing/revoked/expired/cadence_changed/stale_work/
target_changed, duplicate_tick) leaving a provenance-stamped terminal
receipt before dispatch. Bound-term edits and incoming sync changes
revoke and epoch-fence in the same write transaction; recipe and
effective-deployment drift is refused at child admission AND re-derived
from live rows inside the publication transaction, so an in-flight
provider result cannot publish after any bounded term changes. The
legacy no-principal scheduler leg (`_run_scheduled_workbench_legacy`)
is deleted; synced `schedule_enabled` is configuration, never
authority. The walk on .43 caught a live inherited crash
(`WorkbenchRunRecord` lacking the `mint_failures` field its repository
passes — every run-history read on main raises TypeError once a run
row exists; repaired) and Sol's review surfaced a latent HS-131-05
claimed-item stranding race (fixed with an epoch-conditioned claim).
Real-metal walk on .43: five legs green (admitted scheduler run with
honest receipts, duplicate refusal, revoke→re-enable with new terms,
sync-flag refusal, disable-mid-run fence). Sol's four reservations
(process-global admission guards, internal enable helper,
pre-authoritative crash shell, provisional child-success observability)
ride in the evidence. Cadence census: its scheduled tick performs no
model work; the sole Cadence LLM call is request-time authenticated and
belongs to HS-131-07.
HS-131-07 is done — the bounded four-caller census (Rails observer
summary, Decision promotion, Delivery PR review, voice reference
resolution) executes models only through the admitted InferenceRunner
(design ruled in ONE Sol round with four binding amendments; three
implementation rounds to RATIFY-WITH-RESERVATIONS). One generic
`inference.invoke@1` with versioned ServiceContracts; real domain parents
(`decision.promotion-draft@1`, `delivery.pr-review-draft@1`,
`voice_reference_resolve@1` — schema v53 admits the new parent kinds)
replace the generic `inference.run@1` placeholders and pass trusted
parent contexts into every child so no retry escapes cancellation. Rails
runs as an explicit non-owner SERVICE principal
(`rails-observer:journal-only`); the silent owner-elevation fallback in
voice resolution is dead (missing principal refuses
`resolver_principal_required`); domain artifact writes happen INSIDE the
projection-finalization transaction under the publication permit, so a
cancellation election can never publish a decision draft, PR review, or
voice resolution late. Mesh dispatch carries an envelope with the
admitted deployment revision and a warrant whose signed `target_binding`
names that exact revision — the worker refuses missing/tampered/
foreign-node/swapped-revision envelopes by name and builds ONLY from the
frozen fields, and the hub independently re-validates warrant, operation
target, and envelope revision before accepting any result: worker-side
silent retargeting is dead. The Cadence get_loop LLM call is recorded as
an explicit HS-131-10 fence finding, not absorbed. The walk on .43 (all
four legs through the real services/route) caught a 100%-deterministic
persistence bug (invalid "inference" artifact source type — the review
route could never persist); the orchestrator's diff read caught two more
(outcome-object passed to parent close, copy-pasted projection kinds).
Sol's four reservations (rails note crash gap, exceptional parent
cleanup, mesh unit-proof scope, parent-close-after-commit ordering) ride
in the evidence.
HS-131-08 is done — meeting intelligence admits once per SESSION (the
owner's per-sesh ruling made real; one Sol design round with two
amendments, three implementation rounds to RATIFY-WITH-RESERVATIONS).
One authenticated `meeting.session` parent (schema v54; 12h/4096 bounds,
route principal threaded through _start_meeting; no-principal starts
refuse intelligence honestly while recording proceeds) over a frozen
content-free MeetingIntelPlan whose capabilities carry ORDERED immutable
revision lists — the legacy intra-engine auto local→cloud fallback is
DEAD: the cloud leg freezes as a real second revision and each entry runs
as its own admitted child, advancing only on an honest failed receipt
(returned IntelResult.error is classified before receipt election, so a
receipt never says succeeded for a failed attempt). Live windows,
bookmark labels, and auto-title (two seams the design ABSORBED by Sol's
ruling) are trusted children; transcript text is dispatch-only. stop()
cancels the live parent first and durably enqueues the displaced work
(structured intel_jobs.displaced_work, schema v55) before returning; the
late-ready race is fenced under the session lock; the meeting reaches
ready only after ALL displaced work settles. Deferred queue jobs admit
their own short-lived parent under the meeting-intel-queue SERVICE
principal (a closed live session is never revived; every retry is a new
bounded parent); plugin llm dispatches run ON the revision-built engine
inside the child's cancellation seam or refuse
plugin_llm_engine_not_injectable. Walk on .43: four legs green.
Sol reservations R1-R3/R6/R9 ride in the evidence — R9 surfaces an
INHERITED live production bug (undefined ConflictError at
web/routes/meetings/crud.py:161) needing a separate hotfix.
HS-131-09 is done — dictation, wake, and shared Whisper admitted per
SESSION, and DICTATION GOT FASTER (one Sol design round with eight
amendments incl. his 12-hour budget-exhaustion arithmetic; four
implementation rounds — 8→2→1→ratify blockers — to
RATIFY-WITH-RESERVATIONS). Schema v56 adds dictation.session and
wake.session; the new speech_session package freezes content-free plans
ONCE at session open (ordered per-capability revision lists carrying the
frozen DeploymentRevision objects). Desktop hold = one session per press
with a generation token and a two-stage sealed deadline; browser open mic
= one session per authenticated interval (opaque server handle,
30m/1024/90s-inactivity, the lease refreshed inside the first Whisper
child claim with NO resurrection, terminal fences forcing the client
interval closed); wake = 30s/12 under SERVICE wake-capture with the
authority revision derived from the canonical config, stop
generation-fenced through the admission window. Every Whisper call is a
receipted child (MLX preload and silent-audio fallback as SEPARATE
sibling children; pre-session warmup requires the new preload-authority
knob naming the exact model-config revision); classify/rewrite/mesh/
intent-router calls are children whose dispatched runtime is
verified/REBOUND from the frozen revision (config changes after
admission cannot retarget; the legacy browser-pipeline admission is
DELETED; egress labels derive from the frozen revisions through the one
classifier, combining all provider capabilities). The charter's latency
A/B initially FAILED (+36ms median — profiled to 24 short-lived SQLite
connections per child admission); the per-Database connection cache
(Sol-accepted in-story, strict 8-cap, zero new suite names) took child
admission 39.6→6.8ms and the final A/B PASSES with dictation FASTER
than the fork point: median 82.5→68.3ms, p95 85.1→70.5ms. Walk on .43
green. Sol's five reservations + the runtime._dispose production hazard
ride in the evidence; the two recorded unadmitted seams go to the
HS-131-10 fence by name.
HS-131-10 is done — the blocked checkpoint closed without weakening its fence.
The five amendment stories moved the original 145-site / 48-finding /
eleven-family inventory to 100 sites, ZERO findings, ZERO blocking families, and
zero unregistered execution. The authorized gateway remains one context mint;
69 physical adapter sites and 27 admitted seams account for every other execution
site. No product surface or command entered the adapter allowlist. The same five
literal-spine, context, cardinality, provenance, and mutation suites now pass 143
tests under a fresh isolated HOME; success, refusal, failure, retry/fallback,
cancellation, indeterminate recovery, causation, exact revision, authority,
receipt immutability, late-publication fencing, and journal hygiene remain green.
The complete eleven-family final disposition is in
[findings-inventory](./assets/hs-131-10/findings-inventory.md); the original ruling
remains in
[OWNER-DECISION-PACKAGE-HS-131-10](./OWNER-DECISION-PACKAGE-HS-131-10.md).
HS-131-13 is done — the first fence amendment removes the residual service
side doors. Cadence request-time drafting now opens one authenticated
`cadence.next-action-draft` parent (schema v57), freezes placement and the exact
local model before child admission, dispatches through the generic runner, and
stages output behind the parent cancellation fence. The first hostile pass found
two real defects — mutable model A→B retargeting and outer-task cancellation that
could publish during recovery — and both were repaired with production-path
race tests; the final verdict is RATIFY FOR STORY CLOSE. The duplicate Decisions
route model seam, dormant Delivery review helper, and `build_intel_for_target`
are deleted with no shims. The census is now 134 sites, 38 findings, eight
families, zero unregistered (145→134 / 48→38 / 11→8). The quiet isolated full
gate has zero new failure names against the HS-131-10 checkpoint and one repaired
meeting fallback name. Next: HS-131-14, plugins receive admitted intelligence.
HS-131-14 is done — plugins now receive intelligence rather than constructing
providers (one Sol design round; the hostile implementation pass found and
repaired three real concurrency/cardinality defects before returning RATIFY FOR
STORY CLOSE). Fourteen builtins and `segment_probe` lost `_cached_provider`,
configured-factory, and `intel_call` side doors; one opaque per-invocation
`PluginDispatch` binds the runner's exact context, revision, destination,
warrant basis, ordinal, cancellation signal, and exactly one physical
completion. A single lock elects claim versus release: timeout before claim
mechanically prevents late work; timeout after claim is indeterminate and
cannot publish. Provider failure now fails the child, while compatibility retry
gets a distinct `_r2` child/handle/context/receipt and only the winner
materializes. Meeting startup stays lexical until HS-131-17 rather than building
a segment probe before admission. The public uncontextual configured-provider
factory is gone; its private body is dominated by exact context validation. The
census is 105 sites, six findings in six families, zero unregistered
(134→105 / 38→6 / 8→6); no plugin entered the adapter allowlist. Captured
focused proof: 811 passed. The quiet isolated full gate found and repaired one
HS-131-14 test-double regression; its final 91-name ledger has no current-diff
product regression. The one apparent new name is the inherited live `.43` mesh
canary flake, reproduced on the untouched HS-131-13 control tree and present in
earlier Phase-131 ledgers.
HS-131-15 is done — synthetic-text speech side doors now admit exactly when
provider work exists and remain honestly lexical otherwise. Browser rehearsal,
replay, template preview, and authenticated CLI dry-run open one fresh bounded
`dictation.session` (90 seconds / 12 children), freeze only the physically
selected capability revisions, and construct exclusively from that parent-bound
plan with warm-on-start disabled. CLI authority comes only from
`$HOLDSPEAK_TOKEN` checked against the hub bearer through the central owner
authenticator; missing or invalid credentials refuse before construction. Fatal
speech controls escape raw-text degradation. A durable SQLite publication claim
serializes final response/journal/effect handoff against cancellation,
revocation, expiry, new children, and cross-process mutation; exact-token live
recovery clears transient release faults without replay. Browser egress at the
decision point and response proof share the frozen-plan resolver. The census is
105 sites, four findings in four families, zero unregistered; both speech
findings became admitted seams and no product scope entered the allowlist.
Hostile verification returned SHIP-CANDIDATE; focused proof is 501 + 304 passing,
both mutations are caught, web typecheck and 45 tests pass. The inherited-red
full gate found five current-diff regressions, all repaired and re-proved; the
final three apparent Slack names were xdist lock-contamination and pass serially.
HS-131-16 is done. Product pairing now provisions the node bearer plus public
offer pin; the hub alone holds the Ed25519 private key. A destination-,
generation-, revision-, operation-, ordinal-, and deadline-bound offer verifies
and reserves once before the worker-local `InferenceRunner` constructs or calls a
provider. Every physical attempt receives its own immutable worker receipt; a
content-free MACed report is independently settled by the hub, and byte-identical
transport retry never reruns the model. Stop, replay, expiry, revocation, and
wrong-destination paths refuse before late output can settle.

The owner stopped the academic review loop after the 151-path candidate was
rejected and the reduced R2 work exposed one stale unpaired-node test. The final
40-path candidate fixes that regression plus three schema-v59 assertions and the
broker density guard, then freezes at manifest
`24e25287380abcbad6527d5037f051afccbf155620059b38f11069f8085b1413` / complete
diff `17cb83aaf53082bfccf1e963b942c7304e43fad8f76aca2038fea4e018b14450`.
The evidence matrix is 864 passed, including separate-process loopback and the
zero-finding mesh census; the full unit candidate lane is 4,643 passed. Three
unchanged backend guards and two unchanged Speak test mocks remain inherited
baseline, while 785 other web tests, tokens, architecture, typecheck, and build
pass.
HS-131-17 is done — the final fence amendment deletes the dormant session-owned
MIR branch and the parallel config-time `MeetingIntel`. `MeetingSession` now keeps
only its frozen plan, admitted parent, closed fence, and explicit live flag;
startup reads frozen placement readiness and constructs no provider. Automatic
bookmark refinement goes through `_admitted_bookmark_label`, with one exact-
revision child and terminal receipt per real attempt; deterministic, refused,
failed, cancelled, and late cases keep the timestamp label. Deferred routed
intelligence remains under its separate admitted queue parent. The one-path census
is now 100 sites, ZERO findings, ZERO blocking families, and zero unregistered
execution, with mutations proving both retired names fail if reintroduced.
Captured proof is 166 passed; the isolated full unit lane is 4,676 passed with
only the three unchanged inherited UI/copy guards. Next: rerun and close
HS-131-10 at zero, then HS-131-11 docs and HS-131-12's real-model walk.
The roadmap still has inherited structural lint errors in old phases; they are
named baseline and are not silently bundled into this product phase.

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

- 2026-08-14 — **The one-path fence closes at zero without an exception.** The
  exact five-suite rerun is 143 passed; the census is 100 sites, zero findings,
  zero blocking families, and zero unregistered execution. All eleven original
  families left by deletion or admission, never allowlist promotion. HS-131-11
  and HS-131-12 are unblocked.
- 2026-08-14 — **Delete dormant live-session MIR; keep separately admitted
  deferred routing.** HS-131-17 removes every private `mir_*` constructor input,
  plugin enumeration, and post-stop `process_meeting_state()` dispatch from
  `MeetingSession`. It also deletes the config-time `MeetingIntel`; frozen plan
  readiness drives explicit liveness, and automatic bookmarks use the existing
  admitted child seam. The current deferred queue continues to decide routed
  intelligence under its own authenticated parent.
- 2026-08-14 — **HS-131-16 ships at the owner's functional bar.** The exact
  40-path candidate passes the 864-test evidence matrix and the 4,643-test unit
  candidate lane. Pairing, authenticated offer verification, worker-local
  admission/receipts, independent hub settlement, stop, replay, bounded report
  retry, separate-process loopback, and the zero-finding mesh census are green.
  Three backend guards and two Speak mock files are unchanged inherited baseline;
  they do not widen this story or reverse the SHIP call.
- 2026-08-14 — **The owner closes the HS-131-16 academic review loop.** After
  R2 implemented a 36-path candidate and the true 42-file union reached 799
  passes with one functional test-double red, the owner ruled that the project
  had become too strict and academic instead of functional. No R3 hostile review
  or protocol-hardening brief is authorized. Repair the stale unpaired-node test,
  prove the ordinary production pairing/worker/two-receipt/census path, run the
  real regression gates, and make the ship call. Remaining signer, microscopic
  interleaving, future-schema, and taxonomy observations are ledger notes unless
  normal product use reproduces damage.
- 2026-08-14 — **HS-131-16 gets one second reduced repair; a third stops first.**
  R1's 33-path candidate passed the attached 574-test matrix but failed bounded
  hostile re-review. [REPAIR-HS-131-16-R2](./REPAIR-HS-131-16-R2.md) sustains only
  ordinary-use defects and activates one surgical existing-runner deadline seam.
  Its content-free authority expectation is hash-bound by the signed offer without
  crossing the hub warrant; structured 4xx and malformed 2xx are terminal, while
  bounded byte-identical 5xx delivery retry remains allowed because no
  acknowledgement occurred. If R2 re-review fails, ORCHESTRATION's three-round
  valve requires a fresh design/scope ruling before any R3 patch.
- 2026-08-14 — **The first reduced HS-131-16 review fails once and repairs once.**
  The 31-path candidate made the real boundary visible. Sol's hostile review and
  Terra's static verification sustained ordinary failures in observation hygiene,
  production pairing, wire custody, credential/settlement transactions, signed
  semantic binding, stop/owner elections, deadline/liveness generation, strict
  acknowledgement, empty-result consistency, terminal-report grammar, and proof.
  They are consolidated in [REPAIR-HS-131-16-R1](./REPAIR-HS-131-16-R1.md), with
  one fresh implementer and no piecemeal briefs. Generic observer/process/DB work
  remains out; the user approved attaching the orchestrator session to the durable
  worktree for the blocked executable Terra gate after repair.
- 2026-08-14 — **HS-131-16 resets to a reduced clean-room implementation.** The
  first isolated candidate is preserved at an independently reproduced 151-path,
  2.03 MB fingerprint but is DO-NOT-SHIP: review history widened mesh authority
  into profile/UI, Setup/Doctor, browser audio, meeting, generic database,
  process-hardening, docs, and walk concerns. The binding
  [acceptance map](./ACCEPTANCE-MAP-HS-131-16.md) retains the full authenticated
  offer plus worker-local admission protocol while allowing only CORE, focused
  PROOF, and before/after-demonstrated REGRESSION work. The rejected candidate is
  reference material, never an implicit patch; owner may overrule this boundary
  at the sitting.
- 2026-08-13 — **The mesh receiver requires two independent proofs: an
  asymmetrically authenticated hub offer and a worker-local admitted physical
  attempt.** Sol ratified HS-131-16's design with six binding amendments. The
  existing per-node token continues to authenticate worker HTTP/report traffic,
  but cannot verify hub authority because symmetric verification would let the
  worker forge offers; pairing therefore pins a per-node Ed25519 public key. A
  private single-use `VerifiedMeshOffer`, atomic replay reservation, stable node
  identity/generation, nonce/monotonic freshness, transactional hub elections,
  bounded compatibility ordinal, and gapless stop handoff are implementation
  floor. Hardware attestation and cross-machine atomicity remain recorded limits,
  not excuses for accepting late output.
- 2026-08-12 — **The owner charters the complete five-story fence amendment
  wave and authorizes the blocked checkpoint to ship.** HS-131-13 owns residual
  services and retirement of `build_intel_for_target`; HS-131-14 owns plugin
  provider injection; HS-131-15 owns the Speech admit-versus-lexical design;
  HS-131-16 owns mesh receiver authority; HS-131-17 owns dormant MIR, the
  parallel live meeting engine, and bookmark auto-label. This is a visible
  phase-charter amendment under the pre-charter census rule, not an Article-XI
  exception. HS-131-10 remains blocked until all 48 pinned findings reach zero;
  HS-131-11 and HS-131-12 remain held.
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
