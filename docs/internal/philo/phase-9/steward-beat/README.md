# PHILO-9-02 — The steward's lifecycle and child authority

**Status:** RATIFIED design 2026-09-27: authored by Astra; Muad'Dib's
[check r1](checks/steward-beat-muaddib-r1.md) RATIFY-WITH-CONDITIONS, paid.
The two earlier rounds were an Astra-invoked Claude session
(`claude-fable-5-1`), not Muad'Dib's counsel:
[round 1](checks/steward-beat-astra-invoked-claude-r1.md) and
[reply](checks/steward-beat-astra-invoked-claude-r2.md).
**Source pin:** `ffbeb04be5681f6e972800dae04599dba38176e0`. Line anchors below
refer to that tree; verify them after story 01 lands.
**Scope:** design and diagnostic evidence only. Story 02 remains backlog.
No implementation, grant, canvas or closing walk is certified here.

This settles the charter's five lifecycle points, B2 and R4-1 before
[story 02](../../../../../pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-02-the-steward-and-the-connectors-under-article-xi.md)
is briefed. Story 07 takes the grant-specific rules and fences into its
own beat. B1 remains the charter's separate connection-cache contract.

**Tuesday:** the owner starts work, can stop it, and can find its final
result after a restart. His agent can do the granted project work; the
receipt still names the agent and the policy that allowed each effect.
Tenets 1/3/7: keep the existing steward loop, kernel states, warrant,
grant hashing and atomic receipt seam. No second lifecycle engine, new
user workflow, general delegation framework or automatic resumption.

## 1. Authority and what exists

The owner's Q1 is admission by effect. Q2's exact direct grant set is
`{project.run_steward, project.stop_steward, project.publish_update}`.
The charter is
`pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md`:
Q1/Q2 at :24–25, bound at :28, admission table at :133, lifecycle at :209,
B1/B2 at :382/:388, R4-1 at :419, r5 delivery clauses at :183.
The checks `checks/charter-astra-r1.md` F7 and `-r4.md` F2 require this
beat; r2/r3/r5 and the Phase 7
[grant beat](../../../../../pm/roadmap/holdspeak-philo/phase-7-the-desk-on-the-contract/design/grant-lifecycle-beat.md)
and its `checks/lifecycle-beat-astra-r1.md` through `-r3.md` bound it.
The Seven Tenets and Articles V/IX/XI in `docs/internal/CONSTITUTION.md`
outrank this design.

| Source at the pin | Current fact; consequence for build |
|---|---|
| `holdspeak/web/routes/steward.py:99`, :116; `holdspeak/mcp/families/project.py:1594`, :1628 | Insert a run, then start a daemon; return only `run_id`. Request completion cannot terminalise the run's operation. |
| `holdspeak/services/project_steward_service.py:460`, :472, :480 | Run stores `requested_by=principal:<identity>`; stop takes only a run id; recovery interrupts domain rows, without a kernel receipt. |
| `holdspeak/services/project_steward_service.py:871`; `holdspeak/services/project_delta_service.py:1848` | COMPARE reads `id`; the real producer returns `review_id`. Fix the field and its real-producer fence together. The same wrong key occurs in `_effect_create_proposals` at :1263. |
| `holdspeak/kernel/causation.py:16`, :28, :41 | Parent must be claimed/live. Even the same AGENT actor needs a live owner continuation: the final guard says `parent_continuation_identity_required`; a foreign actor fails `parent_operation_scope_required`. A project grant alone cannot pass these checks. |
| `holdspeak/kernel/broker.py:201`, :304; `holdspeak/kernel/executor.py:46`, :61 | Approval and scheduler capability checks also need a scoped steward path. Existing ancestor and codec claim checks remain in force. |
| `holdspeak/services/project_steward_service.py:1313`, :1323 | Proposal application passes the initiator to `decide_proposal`; its broad catch would otherwise swallow authority loss and continue. |
| `holdspeak/workbench_conductor.py:621` | Scheduled steward work currently constructs OWNER `local-steward-conductor`. Replace that steward caller with a SCHEDULER actor whose authority is the recorded policy. |
| `holdspeak/services/project_steward_service.py:795`, :804, :852 | OBSERVE reads local evidence but also fetches CI history before ACT. The provider fetch needs an authorised child too. |
| `holdspeak/services/project_evidence_collector.py:40`; `holdspeak/services/project_steward_service.py:1229`, :1535, :1753 | The collector reads stored snapshots. `refresh_sources` does not itself refresh the provider today. `github_comment` prepares a proposed nudge; `send_nudge` performs the send later. Names do not prove egress. |
| `holdspeak/kernel/journal_atomic.py:58`, :83; `holdspeak/kernel/desk_broker.py:125` | Refused inserts and terminal transitions already have atomic helpers; desk startup recovery supplies the scoped precedent. |

## 2. The durable run and pending handle

One logical start has one kernel operation and at most one steward run.
Both HTTP and MCP call the same hub service. The service owns the async
boundary; transports do not each start a thread. Synchronous internal
`run_once` uses the same admission and terminal path.

1. Authenticate, resolve the stored project, validate, and admit
   `project.run_steward` under the real caller. Mint the run id before
   admission and freeze it, project, watermark and authority. Reuse
   kernel replay by principal and command key (`kernel/journal.py:123`).
   Same key and payload returns the same operation/run; changed payload
   returns `idempotency_conflict`. An omitted key means a new attempt.
   Minted internal ids must not make a matching retry's hash different.
2. Persist the queued run, linked to that operation, before exposing the
   handle or scheduling work. Keep the active-run unique index
   (`db/schema.py:4194`). The codec's admission-side insert uses the
   existing repository's supplied-connection form. A replay never inserts
   a second run or launches a second worker. A process loss between the
   kernel insert and the domain insert is recovered as an orphan operation.
3. Approval is the owner's gesture, the validated policy for scheduler
   work, or story 07's frozen grant for the agent. No HELD state. Claim
   through the existing NODE executor before phases run. Carry the
   authenticated actor and verified run context explicitly into the
   daemon; request-local context does not propagate by assumption.
4. Return `{success: true, run_id, operation_id, state, receipt}` promptly.
   `receipt` is null while pending. `state` is the stored kernel state,
   never an invented success. A run may finish before serialization;
   then return its actual terminal receipt. Keep `run_id` for compatibility.
   Poll/read returns the same ids and terminal receipt, including after a
   restart; `kernel.receipt` retains own/foreign read checks.

Minimal additive storage in story 02: `steward_runs.operation_id` (unique
reference to `kernel_operations`, required for every new admitted run;
nullable only for existing rows), and an immutable `authority_json` on
the run. It holds the policy snapshot/provenance and, for an agent, the
grant id and terms hash. Step result/receipt JSON already exists
(`db/schema.py:4211`): use it to link child operation/receipt ids; do not
build a second journal. `requested_by` already exists; add no second
run-owner column. Schema reconcile is additive (`db/reconcile.py:655`).

The run's native id and operation link are committed before the pending
handle. A start refused before a run exists still has its refused
operation/receipt, with `run_id=null`. Cooldown, disabled policy, missing
project and active-run conflict are named refusals of this identifiable
operation. They must not leave an unused queued run.

No kernel state is added. Domain and kernel states are separate:

| Event | Domain state | Kernel state / receipt |
|---|---|---|
| Admitted/approved, worker not yet claimed | `queued` | `admitting`, `awaiting_decision` or `awaiting_execution`; no terminal receipt |
| Worker claimed | `running` | `claimed`; no terminal receipt |
| Stop committed; claimed child still settling | `stopping` | `claimed` (or existing pre-claim non-terminal state); no run receipt yet |
| All phases/effects finish with known outcomes | `completed` | `succeeded`; actual partial/skipped effect outcomes retained in summary |
| Known execution failure | `failed` | `failed`, named cause |
| Stop reaches its boundary | `interrupted` | `cancelled`, `stop_requested` |
| Grant/policy lost at next boundary | `interrupted` | `refused`, exact authority code; earlier completed effects remain recorded |
| Restart, liveness loss or unknown effect outcome | `interrupted` | `indeterminate`, named cause; never call unknown work failed or completed |

## 3. One terminal winner, stop and restart

Every in-scope terminal path uses `transition_and_receipt(..., strict=True,
effect=...)`. The callback updates the steward row/summary and unfinished
step bookkeeping on **the supplied connection only**, then the helper
writes the kernel state and receipt in the same transaction. No nested
service call, external effect or new connection in that callback.
`BEGIN IMMEDIATE`, receipt/revision check before effect, rollback on any
failure and immutable existing receipts are already supplied by
`kernel/journal_atomic.py:83`. Journal events follow the commit.

Scope the Phase 7 atomic broker hooks to this phase's admitted project
operations and internal steward effects: admission refusal
(`create_refused_with_receipt`), native-admission failure, approval
refusal, explicit rejection, claim refusal, success/failure, reaper and
startup recovery. Include delivery and project-grant operations when they
land; do not add them to the agent grant set. Unrelated operation families
stay with the existing non-desk terminal-write debt. A claim/approval
refusal after a queued run was inserted must also close that run atomically.

`operation_already_terminal` and `operation_revision_conflict` are lost
CAS races: reread the winner, perform no effect, append no false event.
Never raise a refusal carrying another winner's success receipt. Terminal
domain state cannot be overwritten by a late daemon completion.

**The stop/completion race uses the same SQLite write lock, not a stale
pre-read.** Inside the successful-completion callback, reread the linked
run and `stop_requested_at` on the supplied connection before changing
anything. A stop already committed raises a typed `StewardStopWon`; the
helper rolls back. Outside it, reread the operation and close it once as
cancelled through the same helper, after claimed children have settled.
The stop callback likewise rereads the run and its operation's terminal
state under its transaction: if completion won, raise
`StewardRunAlreadyTerminal`, roll back, and close **only the stop command**
as refused. If stop won, commit the stop flag and stop-command receipt;
completion's callback will observe it. A run operation's revision alone
cannot detect a separate stop operation. L4 injects the competing commit
between the pre-read and callback in both directions.

**Stop has two receipts.** `project.stop_steward` is a separate admitted
operation. Resolve project from the stored run. For an agent require a
LIVE grant containing stop and exact
`run.requested_by == 'principal:' + authenticated_identity`; also bind
the stored run operation's actor. Owner may stop any run. Another actor's
run is refused `steward_run_owner_required`, even in the same project.
Missing run is `not_found`, with the identifiable stop's refusal receipt.

Commit `stop_requested_at`/`stopping` with the **stop operation's** success
receipt using the same atomic callback. Its result means “stop requested,”
not “run has stopped.” A terminal run gives `steward_run_already_terminal`
with no domain mutation; a retry of the same stop command returns its
original receipt. Repeated new stop commands on a stopping run may record
the already-pending request; they never create another run receipt.

Before each phase, each child claim/dispatch, and final completion, check
durable stop, terminal state and frozen grant/policy authority. If
authority is lost when no next child is attempted, end the parent
`interrupted/refused` with that authority code; invent no child receipt.
The final completion callback checks these durable conditions under its
transaction too; a typed authority refusal rolls back success and is
closed through the refusal path. A stop committed before the child's final claim check
prevents that dispatch. A child already past that check can finish once;
stop cannot undo a remote effect. Wait for its terminal outcome before
closing the parent. Check inside proposal batches and retry loops, not
only at the outer ACT slot. An attempted child refused at that boundary
gets its own receipt; unvisited slots remain skipped, with no fabricated
attempts. No further child starts after the cutoff.
**Liveness:** use the existing claim/execution deadlines (the default
execution TTL is 3600s, `kernel/model.py:76`); no renewable lease engine.
Clamp a child's execution deadline to its parent's. The scoped reaper
uses the same terminal callback, marks unresolved children indeterminate,
and then closes their parent. A daemon that returns after the deadline
cannot replace those receipts. Provider calls keep their existing timeouts.

**Restart:** on the database-owning hub, settle abandoned steward work
before accepting starts or running the conductor. Use the hub's composed
service, not the temporary under-composed service currently built at
`web_server.py:1317`. Reconcile descendants first, then parents. Sweep
`admitting`, `awaiting_decision`, `awaiting_execution`, `claimed` and
queued/running/stopping domain rows, including an operation with no run
and a queued run whose worker never started. Close unknown work
`indeterminate/hub_restart_during_steward`; atomically interrupt linked
steps/run and write each terminal receipt. Preserve existing winners.
An old unlinked run is interrupted as legacy work, without invented past
authority or a backdated receipt. Repeat recovery is a no-op. Never replay
an uncertain external effect. Freeing the active-run slot allows a new
explicit start, subject to normal policy and idempotency checks.

## 4. The child's authority: grant AND policy

The grant authorises starting a steward, not arbitrary direct decisions.
`decide_proposal` outside the run remains refused for an agent, even with
all three granted operations. The run can apply a proposal only through
its internal child path and only with `apply_proposal_effects` eligible.
No manufactured OWNER, owner bearer token, widened palette or caller
supplied `authority_basis` pays this requirement.

**Record the owner policy.** `project.configure_steward` is owner-only and
admitted. Add `steward_policies.configure_operation_id`, referencing the
owner's successful configure operation; update the policy and that
operation's receipt atomically. Its operation supplies the delegator
identity. `project.archive` also writes the policy: it sets
`unattended_enabled=0` in its own transaction
(`services/project_service.py:3029-3035`). Its atomic callback sets
`configure_operation_id` to the archive operation in that same
transaction. The column thus names the latest owner operation that wrote
the terms, and a snapshot never pairs new terms with an older operation
(Muad'Dib r1 C1). Snapshot the policy id, configure operation id, project,
enabled/unattended flags, eligible kinds, bounds, retry/action limits,
cooldown, YOLO flags and nudge template into the run's `authority_json`.
Canonicalise JSON-valued fields; hash terms with the **imported** Phase 7
helper (`services/schedule_delegation.py:37`, used by `kernel/desk.py:77`).
`policy_sha256 = _hash(policy_terms, None)`: `policy_terms` contains exactly
`project_id`, `enabled`, `unattended_enabled`, sorted eligible kinds,
parsed bounds and YOLO flags, `max_retries`, `max_actions_per_run`,
`cooldown_seconds`, and `nudge_template`. Policy id, configure operation
id, actor and timestamps are provenance, outside this semantic hash.
Re-saving identical terms therefore does not stop a run. Grant hashing
includes its actual optional expiry, unchanged from Phase 7.
No migration backfills owner consent: old policies without this provenance
can be explicitly saved by the owner through the existing control.
Agent/scheduler starts without recorded policy refuse
`steward_policy_required`. Existing run/Room result presentation must show
that named refusal (story 02 API, story 03 face); never silently skip
unattended work until an unexplained re-save. An owner manual run without a policy may use
the existing empty-effects default; that gesture does not create future
scheduler or agent authority. Such a run freezes `policy_id=null`,
`configure_operation_id=null` and `policy_sha256=""`, and its
`authority_terms` carry that empty string. The policy checks at each
boundary apply only to a run that froze a policy id. A policy first
saved during a no-policy owner run does not stop that run: the run has no
eligible effect, and a policy cannot enlarge a running run (Muad'Dib r1 C2).

For an agent root, freeze story 07's grant id/hash alongside this policy
snapshot; root authority remains the project grant. Every child carries
`authority_basis=project-steward:<run_id>:<authority_sha256>` and the
policy's recorded owner as delegator. The referenced immutable snapshot
names **both** the grant and policy, so the receipt can explain them.
Owner-root children name the owner gesture plus policy; scheduler-root
children name the recorded unattended policy. Actor remains the actual
OWNER, AGENT or SCHEDULER for that run. NODE is its executor, not its actor.

`authority_sha256 = _hash(authority_terms, None)`, where `authority_terms`
contains exactly project id, actor kind/identity, `policy_sha256`, and
grant id/terms hash (empty strings for a non-agent). Policy provenance ids
stay outside semantic terms; the grant id binds the exact authority row.
The immutable snapshot retains all provenance separately. Extend the
existing receipt read/transport projection to include `authority_details`
for steward children: run id, project id, grant id/hash (or null), policy
id/hash, configure operation id (or the manual owner's root operation),
and delegator identity. Resolve these from the frozen run snapshot, never
the current policy or grant. Thus **one `kernel.receipt` response names
both authorities**; a cold client needs no second lookup. Persisted receipt
identity/outcome stay immutable. Refusal responses carry the same details
when a known frozen basis exists. A1/H3 fence this actual read shape.

The internal child context is issued only by the hub steward service
after a real run claim. It binds run/parent operation, actor, stored
project, step/effect, target and frozen authority digest. It is not a
public argument and cannot be reconstructed from an arbitrary parent id.
Use the existing service-path/claim-witness pattern (`kernel/desk.py:56`,
`kernel/executor.py:83`), without exporting a token or building a new
continuation service.

The same narrow predicate is required at four existing seams:

| Seam | Required check |
|---|---|
| Codec admission | Trusted steward context, stored project/target membership, eligible effect, limits, matching frozen grant/policy. Derive provenance in the kernel, never accept it from payload. |
| `kernel/causation.py:28` | Keep live-parent signature/state/deadline and actor matching. Permit an AGENT child through the validated steward predicate as an alternative to owner continuation, only for this internal path. Generic agent children keep today's refusal. |
| `kernel/broker.py:201`, :304 | Recognise this same predicate for the operation's own actor at approval and for the scoped SCHEDULER admission; never let another actor approve/terminalise it. An own-actor authority loss while awaiting decision ends atomically refused. |
| Codec `validate_claim`, called at `kernel/executor.py:61` | Recheck the exact frozen grant id/hash, policy digest, run stop/terminal state, parent liveness, target and remaining bound immediately before effect execution. Never replace G1 with a newer LIVE G2. |

For background `run_due`, the composed conductor passes SCHEDULER
`local-steward-conductor`, not OWNER. Require the stored policy's
`enabled` and `unattended_enabled`, and record it as the authority basis.
Manual owner `project.steward.trigger` is admitted and stays live until
its child runs settle; watch evaluation keeps its own admission. It uses
the same async launch pattern, returning `{success, operation_id, state,
receipt}` promptly. No fake run id is minted for a trigger. The existing
kernel operation read projects its child run ids and per-child outcomes
from stored parentage; terminal result carries the watch/run outcomes.
Repeated command keys return this same trigger handle. Include trigger
operations in the startup and liveness sweeps: settle children first,
then one indeterminate trigger receipt; no resume of the drain. Its
deadline caps its descendants. A
scheduler drain without a manual trigger has no invented owner ancestor;
each run is admitted under its own project's recorded policy. Other
conductor families are outside this beat.

**Cutoff:** Phase 7's claim-check boundary applies per child. A revoke,
expiry, re-grant or policy edit committed before that check refuses it.
G1 is never replaced by G2 inside a running parent. A child already past
the check may finish once under its frozen basis; the next attempted child
is refused and the parent ends terminal. Policy digest mismatch refuses
`steward_policy_changed`; disabled policy refuses `steward_disabled`.
Policy expansion cannot enlarge an existing run; it needs a new run.
Grant codes keep Phase 7's order: missing/wrong identity/project/operation
→ `project_delegation_required`; expired → `_expired`; revoked or changed
frozen terms → `_revoked`. Historical rows explain a refusal only.

Authority refusals are control flow: rethrow them through the broad
catches in effects and retries (`project_steward_service.py:1123`, :1323,
:1370), persist the attempted child's receipt and close the run. Do not
turn them into a skipped proposal, retry or a successful partial run.
Already completed effects remain true; a refused parent is not rollback.
Explicit credential revoke ends its grants durably before token removal;
reissue and restart preserve identity grants, as story 07 requires.

## 5. Effects, parentage and no duplicate admission

An executed effect is a child of the run; existing lower-level effects
keep their own admission and causal chain. Phases, reads and local
comparison do not acquire operations just for having a name. Use one
internal `project.steward.effect` spec with a closed effect-kind enum for
policy slots that have no existing admitted operation. It is not an MCP
tool or grantable operation. Do not add a generic child execution API.

| Work | Operation and authority boundary |
|---|---|
| OBSERVE local collector / COMPARE / PROPOSE | Local work in the run. Record the real `review_id`; no fabricated successful receipt for a read. |
| OBSERVE CI provider call | Admitted child: an OWNER-root run uses the owner's run gesture for this existing read, preserving health refresh even with only `draft_update` enabled or no policy. AGENT/SCHEDULER roots require `refresh_sources` eligibility; if absent, retain prior observations with their age and a named skipped result. No silent fresh-health claim. |
| ACT `refresh_sources` / `create_proposals` | One internal policy-effect child per executed slot. Current collector reads stored evidence; record that result without claiming a provider refresh. If a lower provider operation is used, it is the leaf admission, not a second wrapper for the same call. |
| ACT `apply_proposal_effects` | One `project.decide_proposal` child per actual proposal acceptance, directly under the run, tagged with this effect kind. Resolve proposal/project from stored data. No extra admitted batch wrapper; check cutoff/bounds between proposals. Direct agent decisions remain refused. |
| ACT `draft_update` | One internal policy-effect child owns draft creation in every mode. A model draft's existing `inference.invoke` is its child, with existing egress children beneath it; inference and local draft persistence are distinct effects. If model execution fails and the update service produces a deterministic fallback, the slot child covers that draft write and records the fallback; if no draft is written, record the failure/skip honestly. Preserve inference runner evidence/attestation; never forge its receipt through the generic helper. |
| ACT `create_door_item` | One internal policy-effect child around the actual canonical Door write; keep the watermark/follow-through dedup. Reusing a completed effect returns its recorded result, not a second write. |
| ACT `github_comment` | One internal child for preparing the nudge, recording only that preparation. Current code does not send here. Later `nudge.send` is a separate owner-only admitted act; an agent cannot turn a proposed nudge into a send with its run grant. |
| Direct stop / publish | Stop is its own admitted command as §3; publish resolves project from the stored update and uses its direct project grant. Neither inherits permission from caller-supplied project ids or a run id. |

Existing child operations such as `inference.invoke` retain their own
codecs, prerequisites and receipt producer. Extend only their trusted
steward provenance/claim path as needed; do not bypass their normal
authority or count one underlying call twice. A completed effect has one
leaf receipt; an indeterminate effect is never automatically retried.

## 6. B2: between authentication and the default HTTP right refusal

At `principals.py:354` the default protected-route requirement is OWNER;
`web_server.py:655` calls it before the route. A service-only fix is too
late. Do not change the default to AGENT_SUBMIT for `/api/projects/*`.

After authentication, give only the enumerated **exact method and route
patterns** for admitted or conditional project operations AGENT_SUBMIT in
`required_right`, before the default OWNER fallback. Follow Phase 7's
path-only edge; middleware does not read or consume the body. In that
route's parse/serialize adapter, classify validated arguments with the
same descriptor predicate used by `OperationRegistry.invoke`
(`operations.py:1407`). An admitted form reaches the declared operation
before any effect. A valid exempt form reapplies its previous HTTP right
requirement **in the adapter before any service call**, producing the same
protocol refusal and no receipt when the AGENT lacks it. This second
right check preserves bare Door/local-recheck behavior while allowing
the conditional path through the central edge. Reuse the descriptor;
no second admission table in middleware. The admitted form's codec returns the
named refusal receipt (or, after story 07, executes under the valid bound).
The spec's capability must also be `agent.submit` so it reaches the
project authority check (`broker.py:303`); this is eligibility to ask,
never authority to execute. HTTP keeps its status/envelope compatibility
while carrying `operation_id` and `receipt` on the error.

| Request | Boundary/result |
|---|---|
| Real PROJECT credential: Door count; Door create with nonempty sources; GitHub/Jira/working Confluence recheck | Identifiable admitted request reaches `project_delegation_required` receipt, no provider call/domain write. These are outside the grant even after story 07. |
| Valid bare Door create; Calendar/Models recheck; project read or exempt edit | Existing authentication/palette/right behavior; no new operation. If the HTTP gate refuses, it remains a protocol refusal. |
| Unknown route/method/tool; missing or invalid credential | Protocol failure, no receipt; authentication runs first. |
| Known admitted route/tool with bad arguments, including adapter/schema rejection | Identifiable consequential refusal `invalid_arguments` with receipt through the shared refusal path; do not return FastAPI 422 or MCP validation error before that path. |
| Conditional admitted route with malformed arguments | If the operation is identifiable but invalid inputs prevent proving the exempt form, record `invalid_arguments`; only a valid exempt form takes the exempt branch. |
| Agent run/stop/publish | Same route classification; story 02 refuses with receipt, story 07 enables only the bound. Resolve stop/publish project from stored run/update, not body or URL claims. |

Argument classification belongs only to the adapter and must not execute
a service. Preserve Phase 7's four refusal classes and its desk
boundary (`services/desk_kernel.py:18`). This design does not open reads
or exempt edits that the present HTTP right gate refuses. B1 separately
makes `connection.list` a cached remote read; a read cannot conceal a
provider probe to evade this table.

## 7. Fences owed by the implementation

These are build requirements, **not tests claimed present or green**.
For a defect marked red, first run the behavioral assertion on the pinned
main tree and keep its failing output; a diagnostic that asserts today's
bug is evidence, not a red fence. For new behavior/invariants, introduce
the real producer, then show the named mutation fails. Use real hub
services, the real kernel and Settings-issued credentials; never insert
a fake grant or make a test double lie about a producer's field.

| ID / owner | Behavioral assertion | Red or mutation proof |
|---|---|---|
| L1 / 02 | HTTP/MCP start returns durable run + operation, non-terminal while blocked in a real phase; one worker under concurrent/restart replay. | Red: no operation handle/row. Mutate return/launch before insert; remove replay bind. |
| L2 / 02 | One active run, named conflict with its own refused receipt and no spare queued row. | Red: conflict lacks receipt. Mutate active-run index or rollback. |
| L3 / 02 | Success, known failure, stop, disabled/cooldown/not-found, native-admit/approval/claim refusal and liveness loss each leave the mapped run state and exactly one terminal receipt. | Red: no kernel rows. Fault inside each terminal transaction after domain update; all three writes roll back. |
| L4 / 02 | Complete-vs-stop/reaper/recovery races have one winner; a late daemon cannot rewrite run/receipt or start another child. | Mutate strict CAS, terminal/stop checks, child deadline clamp. Assert rows and events, not just return values. |
| L5 / 02 | Stop has its own receipt; run remains pending while an already-claimed child settles, then its own cancelled receipt. Stop between two proposals prevents the second. | Red: stop has no kernel receipt. Mutate inner-loop check or close-parent-before-child. |
| L6 / 02 | Real process kill/restart on same isolated DB at pre-domain insert, queued, running and stopping; descendants and parent terminal, slot free, repeated recovery no-op, no remote replay. | Red: domain-only recovery/no operation receipt. Mutate startup wiring, orphan scan, receipt callback. A new service object is not a hub restart. |
| L7 / 02 | COMPARE and proposal-creation result use `open_review`'s actual `review_id`; receipt links actual child decisions. | Red: empty id at :871/:1263. Real producer and readback; mutation to old key. |
| A1 / 02+07 | All executed effects have the correct causal chain, actor and policy provenance; agent children also name frozen G1. Generic/forged/foreign parent children remain refused. | Red: no steward parentage; same-actor AGENT child hits continuation guard. In 07 mint G1 through owner grant operation. Mutate internal-context, actor or project bind. |
| A2 / 07 | Direct agent proposal accept/edit_accept/defer/dismiss refuses despite G1; the real run accepts only eligible proposals, same actor, and never sends a proposed nudge. | New grant behavior: mutate effect allowlist, eligibility or owner-only send check. No fabricated grants in 02. |
| A3 / 07 | Revoke/expiry/re-grant between admission→approval, approval→claim, and after child claim. Pre-check refusal has receipt; post-check child may finish once; next refuses with G1, never G2. | Mutate each recheck; lookup latest LIVE instead of frozen id; omit expiry from hash; wrong historical-code precedence. |
| A4 / 02+07 | Changed/disabled policy cuts off next child/phase or final completion; identical policy re-save does not; a first policy save does not stop a no-policy owner run; archive stamps its operation as the policy's provenance. No further child still ends the revoked parent refused. OWNER OBSERVE keeps CI refresh; AGENT/SCHEDULER OBSERVE requires eligibility and reports skipped/stale truthfully. | Red: OBSERVE fetch precedes agent/scheduler policy check. Mutate digest/phase/inner-loop/final callback checks, catch propagation or owner-gesture distinction. |
| A5 / 07 | Agent stops own run only, even with two actors in same project; grant A cannot stop/publish stored object B under a spoofed project A argument. | Current unbound stop is defective; full grant case is new. Mutate requested_by/stored-project checks. |
| A6 / 02 | Scheduled run actor is SCHEDULER with recorded enabled/unattended policy; trigger returns pending op handle, reads child outcomes, closes after them, replays/restarts correctly; no caller-crafted scheduler authority. | Red: conductor uses OWNER and trigger has no operation. Mutate policy/provenance check, trigger recovery or scoped capability/approval path. |
| A7 / 07 | Grant, policy and expiry hashing; credential revoke durable-first; reissue/restart preserve grant; orphan grant still visible/stoppable. | Reuse Phase 7 interleaving matrix with project dimension; mutate each check. Grant canvas/glass remain 07's prerequisite. |
| H1 / 02 | Actual HTTP PROJECT credential: Door count, sourced Door create, GitHub recheck each returns `project_delegation_required` + receipt, zero side effects. | Red: central 403 `principal_right_required`, zero operations. Mutate early right-gate ordering or codec capability. |
| H2 / 02 | Read, exempt edit, bare Door, local recheck, unknown route and unauthenticated request retain protocol/no-operation behavior; malformed identifiable write has receipt. | Mutate broad route-prefix bypass, remove the adapter's exempt-form right check, change argument classifier or adapter-refusal path. |
| H3 / 02 | Same principal/intent on HTTP and MCP yields equivalent outcome/provenance; own receipt readable and foreign agent receipt refused. | Mutate error-envelope attachment or read scope. |
| D1 / 02+07 | r5 delivery: same principal/key/payload, including concurrent and post-restart retry, one original row/time/op/receipt; changed payload conflicts; new/omitted MCP key creates new confirmation. | New capability: mutate replay or key/hash scope. 07 fences refusal with a real LIVE grant. |
| D2 / 02 | Delivery operation id is execution-derived, NOT NULL UNIQUE FK; stored update supplies project; insert/state/receipt rollback together. Published body stays immutable. | New capability: mutate each constraint, project resolution or atomic callback; replay after rollback succeeds once. |

The delivery clauses at charter :183–184 use this same atomic seam and
remain owner-only. This beat neither implements them nor changes the
meaning of confirmation to proof of external delivery. Story 03 owns the
rendered Copy/Mark-delivered transitions; 07 owns grant transitions. Their
receipts must remain visible wherever the action leaves the face, at
1440 and 393. Story 02 contributes its actual atlas cases; story 05
assembles them. Run one real case per `scripts/graph_walk.py` invocation
using `agent/skills/holdspeak-capability-verifier/SKILL.md`, “Walk a case.”
No sample atlas or new-service stand-in closes a walk or restart fence.

## 8. Evidence, ledger and handoff

Luna audited the lifecycle/source and HTTP boundary independently. Astra
read the scripts, reran both probes on fresh isolated homes, checked the
JSON assertions below, and ran the focused suites. These are diagnostics
of the pinned code, not behavioral red fences or proof of the new design.

Worker sessions: `01a0e5b4-6942-71b2-aa58-7a33262fc3ee`
(`steward_source_probe`) and `01a0e5b5-1fa7-7870-9ead-9d34dea6e91d`
(`http_edge_probe`). Astra verified both persisted rollout metadata:
`model=gpt-5.6-luna`, `effort=xhigh`. Orchestrator session:
`01a0e5b3-b8de-77c3-a224-0d7aade5184b`.

| Probe / retained evidence | Astra's observed result |
|---|---|
| [Real source producers](probes/source.py.txt), [raw output](probes/source.out.json) | Real `open_review` returns a nonempty `review_id`; COMPARE records empty. Real `run_once` completes with **zero kernel operations**. |
| Same source probe, stop adapter | An injected AGENT request principal stops a run with another actor's `requested_by`: HTTP 200, row `stopping`. This deliberately bypasses the central auth middleware; it proves the adapter/service gap, **not** authenticated wire reachability. |
| Same source probe, real configured kernel | AGENT submits a real `tool.call`, OWNER approves it, NODE claims it; that same AGENT's child is refused `parent_continuation_identity_required`. This demonstrates the causation seam, not an unbuilt project grant. No tool effect is executed. |
| [HTTP probe](probes/http.py.txt), [raw output](probes/http.out.json) | A real isolated hub issues a PROJECT credential through Settings. Door count, sourced Door create and GitHub Recheck each return 403 `principal_right_required`, with **zero operations and zero receipts** before/after each request. Provider handlers never run. |

To reproduce the recorded sources (the `.txt` suffix keeps them out of
test discovery):

```sh
mkdir -p .tmp/steward-beat
cp docs/internal/philo/phase-9/steward-beat/probes/source.py.txt .tmp/steward-beat/source-probe.py
cp docs/internal/philo/phase-9/steward-beat/probes/http.py.txt .tmp/steward-beat/http-probe-b2.py
env HOME="$(mktemp -d)" uv run python .tmp/steward-beat/source-probe.py "$(mktemp -d)"
env HOME="$(mktemp -d)" uv run python .tmp/steward-beat/http-probe-b2.py
```

After `uv sync --extra test`, Astra collected and ran:

```sh
env HOME="$(mktemp -d)" uv run pytest --collect-only -q \
  tests/unit/test_steward_engine.py tests/unit/test_steward_schema.py \
  tests/unit/test_steward_effects.py tests/integration/test_steward_routes.py \
  tests/integration/test_principal_separation.py \
  tests/unit/test_philo7_grant_lifecycle.py tests/unit/test_docs_navigation.py
env HOME="$(mktemp -d)" uv run pytest -q \
  tests/unit/test_steward_engine.py tests/unit/test_steward_schema.py \
  tests/unit/test_steward_effects.py tests/integration/test_steward_routes.py \
  tests/integration/test_principal_separation.py \
  tests/unit/test_philo7_grant_lifecycle.py tests/unit/test_docs_navigation.py
```

[Collection](validation/collect.txt): **160 tests collected**.
[Run tail](validation/tests.txt): **160 passed in 53.57s**. These existing
tests preserve the cited machinery; they do not prove the missing fences
in §7. `python3 scripts/check_docs.py` on the beat and story link,
`dw check holdspeak-philo` and `git diff --check` also passed.

Full product suites, new mutation fences, glass and actual atlas walks
were not run for this docs-only beat. They belong to the implementation
landings; no face is changed or story flipped here. Every probe/pytest
used an isolated HOME/database; `tests/e2e/test_metal.py` was not run.

| Ledger class | Finding / home |
|---|---|
| b — existing implementation defect | Missing run admission/receipt, unbound stop, owner-shaped scheduler, OBSERVE policy bypass and swallowed authority loss: story 02, §§2–7 above. |
| b — existing implementation defect | Real review producer key mismatch, including proposal-creation sibling: story 02 L7. |
| b — existing implementation defect | B2 central gate prevents operation refusal receipts: story 02 H1/H2. |
| New capability, no red claimed | Bounded project grant and child authority: story 07 A1–A7; delivery: stories 01/02/03 D1/D2. |
| Existing parked debt | Non-desk/non-project two-step terminal writes stay in BACKLOG “PHILO-7-02 lifecycle beat follow-ups.” |

**Amendments:** the owner assigned this prerequisite design to Astra, checked
by Muad'Dib, at this `docs/internal/` path; the charter lane/decision record
and story header now agree. Implementation ownership remains Muad'Dib,
checked by Astra. No owner ruling or acceptance criterion is waived. The beat
specifies the required lifecycle, adds source-grounded fence details, and
corrects the grounding distinction between proposed nudges and sending.
It records the minimal run/policy links needed for authority provenance.
Story 07 still needs its checked grant beat and owner-ratified canvas.
Story 02 must also settle B1 in its brief; this beat does not pay that
separate condition. Muad'Dib checked this artifact in check r1 before story 02 is briefed.

### Notes for the story 02 implementation brief (Astra-invoked Claude r2 F12; Muad'Dib r1)

- The owner/no-policy snapshot is settled in §4 (Muad'Dib r1 C2): `policy_sha256 = ""`, and a policy first saved mid-run does not cut off that run.
- The policy's recorded owner operation is also written by `project.archive` (§4, Muad'Dib r1 C1).
- A run refused `steward_policy_required` must show that refusal where the run result shows. The story 03 brief carries the face half (Muad'Dib r1 F7).
- Enumerate every admitted/conditional HTTP method and route pattern from the charter admission table and actual route declarations in the brief. §6 settles the two-stage boundary; no broad prefix or guessed route may enter the edge map.
- The check-pending status and repeated completion-check sentence are now corrected. These are nonblocking briefing notes, not an implementation or story-closure claim.
