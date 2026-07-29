# Phase 106 - The Kernel

**Status:** CLOSED (10/10, 2026-07-29). Chartered 2026-07-26 from
[`PLAN_KERNEL_OPERATION_BROKER.md`](../../../docs/internal/PLAN_KERNEL_OPERATION_BROKER.md)
(the RFC, three council passes) and the owner's direct charge:

> "HoldSpeak's ambition to come a lot closer to an Operating System
> based on the Web for the Tech-Lead/Architect who uses AI on the
> day-to-day, who follows on to PRs, who controls agents through
> xterm.js, who keeps project memory, who chats to agents, who
> records decisions and then creates artifacts out of those
> decisions and meetings."

**Last updated:** 2026-07-29 (CLOSED 10/10 — the owner's sitting passed all eight beats; census delta ZERO, printed in final-summary.md).

## Why this phase exists

Phase 105 gave the desk a bench. Phase 104 gave it a watched hand: a
capability ledger, a fail-closed gate that stops an agent's risky
call and asks the desk, and hash-chained receipts. The owner's rider
after the 105 sitting named what is still missing: **104 plus the
kernel is what makes this an actual OS.**

Today HoldSpeak has a de facto kernel — it is simply unnamed and
scattered. `PermissionGate`, the actuator proposal state machine,
`HubCommandService`/`NodeCommandProcessor`, `RunLifecycle`, and the
Phase-104 gate each implement a private slice of the same four
ideas: admit an operation, derive who is allowed to ask for it,
decide it once, and leave a receipt. The
[effect census](../proposals/kernel-effect-census-2026-07-25.md)
counted the cost of that scatter: **40 effect-capable call sites, of
which only 4 are universally covered** by an audited chokepoint. The
other 36 bypass, are mixed, or expose a dormant unowned raw path.

An operating system is not a look. It is the property that
consequential things cannot happen except through one admission path
that names who asked, decides once, and remembers. This phase
installs that path — and then writes the first real program on top
of it, so the kernel is not an article of faith but something the
owner can watch working on his own pull requests.

## Constitutional grounding

- **Article XI (The Kernel)** — proposed in RFC §10, ratified by
  HS-106-01 with the Sol council pass on record. This phase IS
  Article XI's first enforcement pass.
- **Article V (Consent is the spine of action):** never narrowed.
  Whatever types, sends, files, spawns, or kills still passes
  propose/approve/execute. Article XI closes the nested-effects
  loophole rather than opening one.
- **Article III (Local first, honest egress):** the journal records
  placement and egress for every attempt; the userland program's
  outward comments are proposals, never silent sends.
- **Article VI (Honest by construction):** the journal is truth, the
  bus is a projection, and a receipt exists for every attempted
  consequence including refusals.
- **Article IX (Proof over claim):** the kill criterion (RFC §12) is
  an acceptance test, not an opinion; this phase can honestly fail
  it.

## Goal

Four calls — `read`, `submit`, `decide`, `events` — with a
hash-chained journal behind them, proven by **three heterogeneous
drivers** (terminal input, actuator egress, inference runs) sharing
admission, principal, journal, and receipt code **without
driver-specific conditionals in the broker**. On top of it, one
visible tech-lead program: PR follow-through, where the owner sees a
pull request, decides once, and the desk does the rest with a
receipt for every consequence.

## Scope

- **In:** the two RFC §8 prerequisites, the broker and journal,
  three thin heterogeneous slices, the kill-criterion verdict, one
  userland program, docs, closeout.
- **Out:** broad migration of the typing census (RFC §7 rung 5 — it
  waits for the kill criterion, and for dictation's commit-boundary
  semantics to be settled first, so dictation is migrated once and
  never twice); effect-capability confinement (RFC §5b, the
  privileged executor process — named as the enforcement boundary,
  deliberately later); ALL iPad/HSM work (the standing
  web-desk-is-the-spec direction); any new primitive kinds; any
  rework of the Phase-105 verb registry, which is userland dispatch
  and stays that way.

## Exit criteria (evidence required)

- [x] HS-106-01 through HS-106-08 shipped with evidence.
- [x] The kill criterion (RFC §12) applied at HS-106-07 and its
      verdict recorded honestly — including the outcome where it
      fails and the name is dropped.
- [x] The broker density guards green before any slice merges: a
      line-budget guard in the Phase-79 style, and a census test
      asserting zero driver-specific conditionals in broker modules.
- [x] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (4297 passed / 37 skipped at HS-106-08; the single failure is the
      pre-adjudicated voice-notes wording drift, documented per-story).
- [x] `cd web && npx tsc --noEmit -p . && npx vitest run && npm run
      build && npm run tokens:gate` green.
- [x] The userland program (HS-106-08) proven on the owner's REAL
      pull requests on real metal, not seeded fixtures.
- [x] HS-106-09 docs shipped touching the entry points.
- [x] HS-106-10 closeout: the sitting loop run to the owner's
      verdict per Article IX.4.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-106-01 | Article XI ratified, with the migration provision | done | [story-01-article-xi](./story-01-article-xi.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-106-02 | Principal separation on loopback | done | [story-02-principals](./story-02-principals.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-106-03 | The effect census, pinned as a test | done | [story-03-census-test](./story-03-census-test.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-106-04 | The broker and the journal — four calls | done | [story-04-broker-journal](./story-04-broker-journal.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-106-05 | Thin slice I — terminal input | done | [story-05-slice-terminal](./story-05-slice-terminal.md) | [evidence-story-05](./evidence-story-05.md) |
| HS-106-06 | Thin slice II — actuator egress | done | [story-06-slice-actuator](./story-06-slice-actuator.md) | [evidence-story-06](./evidence-story-06.md) |
| HS-106-07 | Thin slice III — inference, and the kill criterion | done | [story-07-slice-inference-kill](./story-07-slice-inference-kill.md) | [evidence-story-07](./evidence-story-07.md) |
| HS-106-08 | Userland — PR follow-through, the tech-lead's loop | done | [story-08-userland-pr-follow](./story-08-userland-pr-follow.md) | [evidence-story-08](./evidence-story-08.md) |
| HS-106-09 | Docs — the kernel at the entry points | done | [story-09-docs](./story-09-docs.md) | [evidence-story-09](./evidence-story-09.md) |
| HS-106-10 | Closeout — the sitting and the kernel ledger | done | [story-10-closeout](./story-10-closeout.md) | [evidence-story-10](./evidence-story-10.md) |

## Sequencing

Strictly ladder order for 01 through 07 — the RFC §7 ordering is
load-bearing, not cosmetic. 01 (law) and 02/03 (prerequisites) are
pure hardening and can land in any order among themselves. 04 is the
spine. 05, 06, 07 must be **heterogeneous** and land in that order:
breadth inside the terminal family is not heterogeneity, and a
broker ossified around terminal semantics would force driver
conditionals the moment actuators and inference arrive. 08 rides on
whatever 05 through 07 actually delivered — if the kill criterion
fails at 07, 08 is rechartered against the honest result rather than
pretending.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| A God envelope or registry — the broker generalizes to fit every driver | high | Typed operation modules; no field generalized until two real drivers need it; line-budget guard + zero-conditional census test green before any slice merges | A broker module needs `if driver ==` to pass a slice |
| False authority through a shared interface | medium | HS-106-02 and the principal derivation land BEFORE any slice; caller never asserts authority | A slice needs the caller to pass its own principal |
| Migration double truth — two policy decisions for one act | medium | Domain tables stay authoritative; correlation over copying; one decision, executor re-checks warrant only | Two code paths can both approve the same act |
| Slices are homogeneous in disguise (three terminal-shaped drivers) | medium | 05/06/07 are deliberately terminal / actuator / inference; heterogeneity is an acceptance criterion, not a hope | Slice II or III reuses slice I's envelope shape unchanged |
| The phase ships a name, not a kernel | medium | The kill criterion at 07 is a real gate with a real failing outcome | Three drivers cannot share admission/principal/journal/receipt code |

## Decisions made (this phase)

- 2026-07-27 - Register `process.spawn@1` in HS-106-08 as a typed peer over the existing `worktree.create` / `factory.spawn` records; the four caller calls and driver-blind spine stay unchanged - the HS-106-05 deferral and HS-106-08 requirement contradicted each other, the implementing agent stopped rather than reach around the kernel, and the owner resolved the contradiction after the three-driver kill criterion passed. The deferral's reason is spent; dictation's commit boundary remains deferred.
- 2026-07-26 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-07-26 - Charter is "kernel spine PLUS one visible userland program" (owner's call) - the spine alone is invisible and unfalsifiable to the owner; one real program makes it watchable in a day - owner direction.
- 2026-07-26 - The userland program is PR follow-through - it is the only §9 program that exercises all three heterogeneous slices at once (dispatch an agent, propose an outward comment, summarize with a model), and the owner named PR follow-through first - orchestrator.
- 2026-07-26 - Fourth council pass (Sol) on Article XI returned **do not ratify yet** - the drafted clauses turn the RFC's destination into present-tense fact; clauses 2 and 6 would be false at signing and still false at phase close - archived verbatim at [kernel-council-sol-article-xi.md](../proposals/kernel-council-sol-article-xi.md). Two findings re-verified directly against the tree and both hold (`gate_routes.py:152` caller-asserted `actor` defaulting to owner; `coder_steering.py:649-658` effect before receipt).
- 2026-07-26 - Sol's rewritten clauses 1-5 ADOPTED and the drafted clause 6 DELETED (redundant with constitutional supremacy; collides with RFC §12 on reversible local edits) - orchestrator, on the council's evidence.
- 2026-07-26 - **The owner ruled: ratify NOW with an explicit temporary migration provision** naming unmigrated cooperating paths as declared debt and forbidding agent access to them - Article X, the owner alone amends. Sol's preference (wait until clause 2 is materially true) is recorded as dissent, not absorbed into agreement.
- 2026-07-26 - The migration provision's register IS the HS-106-03 effect ledger - one artifact, so the law and the test cannot drift apart; the provision sunsets when the register is empty - orchestrator.

## Decisions deferred

- **Effect-capability confinement (RFC §5b)** — the privileged
  executor process, warrants over IPC. This is the enforcement
  boundary; until it lands the kernel's claim stays narrowed to
  cooperating surfaces (sol's amendment 1). Named, not built here.
- **Broad typing-census migration (rung 5)** — waits on the kill
  criterion and on dictation's commit-boundary semantics.
- **The process window** — deferred out of Phase 105, and honestly a
  kernel consumer: "what is running" is a `read` plus `events`
  projection. Belongs to the phase after this one.
- **Project memory and decisions-to-artifacts** — named in the
  owner's charge, and real §9 userland. Held as the SECOND userland
  program so this phase ships one visible program well rather than
  three thinly.

## Where we are

**2026-07-29 — CLOSED 10/10. The owner's sitting passed all eight
beats.** His verdict, verbatim: *"all passed, make progress."* No
riders raised. He was shown every known rough edge before he walked —
the beat-7 failure and its rider fix, the two stray receipt comments on
#387, the unresolved 772ms-vs-85ms latency discrepancy, and the census
delta — rather than discovering any of them mid-walk.

**The number, printed rather than framed: 4 covered of 40 at start,
4 of 40 at close. Delta ZERO.** This phase built the kernel and proved
it real; it closed no side doors. Phase 107 is chartered to move it,
with an honest ceiling of 4 → 30 stated at ITS charter time because the
ten raw-desktop primitives close only under §5b confinement.

The kill criterion passed and was then exceeded: HS-106-08 registered a
FOURTH driver and built a real product feature on the spine with
`git diff --exit-code` returning zero across all five spine modules.
Full ledger, the Article XI clause-by-clause re-audit, and the findings
worth carrying forward are in [final-summary.md](./final-summary.md).

**2026-07-27 — HS-106-09 shipped, 9/10: the kernel is at the entry points.**
Backend architecture now names the four-call caller plane, the three-call
executor plane, the journal/bus truth rule, all six registered operation types,
and a rendered submit-to-receipt diagram. Security leads with the boundary's
honest scope: cooperating code only, not a sandbox; 36 of 40 ledgered effect
sites remain outside the kernel, and the stronger claim waits for RFC section
5b process confinement. The User Guide puts the PR loop beside steering in the
owner's words, and the README leads with the benefit. The claim-by-claim evidence
names the shipped file and line behind every sentence. Final proof: docs and
effect guards 25 passed; Mermaid rendered; the full suite recorded 4,279 passed,
41 skipped, and only the pre-adjudicated voice-notes wording failure. HS-106-10
is next: the owner sitting and closeout.

**2026-07-28 — HS-106-08 shipped, 8/10: the kernel is visible.** The
first §9 userland program rides on all four slices. Four verbs and no
more — send an agent at it (`process.spawn` + `process.input`), draft
the review (`inference.run`), propose the comment or status (an
actuator proposal). Merge, close, force-push and approve-review stay
OUT of v1 deliberately.

**The spine did not move.** `git diff --exit-code` over
`broker/admission/journal/model/executor` exits 0 with a FOURTH driver
registered — the broker's own code did not change by a single character
to accept `process.spawn`. Six operation types now; the spine still
names none of them. That is a stronger result than HS-106-07's kill
criterion asked for: three heterogeneous drivers proved the spine
shared, and a real product feature then plugged into it needing nothing
but a new codec.

Proven on the owner's REAL pull request #387: spawn, input, a
tool-effect CHILD operation with its own receipt, and inference all
succeeded. The approved comment landed exactly once and was confirmed
**on GitHub itself**, not merely in the receipt; the denied probe —
whose own text read "this probe will be denied and must not land" — is
absent from the real PR. A credential yank retained the row as stale,
kept local verbs available, and refused the GitHub verbs by name.

The walk was read, not merely captured: verbs ghost WITH their reason
(`no matching worktree`) rather than hiding, the proposal card carries
the GitHub egress badge with the full drafted text above Deny/Approve,
and there is no modal.

**A charter contradiction was found and fixed rather than worked
around.** The implementing agent stopped with nothing built on
discovering that story-08 required `process.spawn` while story-05 had
deferred spawn to rung 5 — both written in the same scaffolding
session. It refused to reach around the kernel into
`delivery/factory_launch.py`. The owner authorized registering
`process.spawn` as a sixth operation type (RFC §3's sanctioned
mechanism: registered types under `submit`, never new syscalls), the
deferral's stated reason being spent once the kill criterion passed.
story-05's out-of-scope list was amended so the contradiction does not
sit in the roadmap for someone else to trip over.

**2026-07-27 — HS-106-08 shipped, 8/10: the kernel has visible userland.**
Real PR #387 stayed on the Desk while the owner sent a bounded Claude agent into
its exact registered worktree through `process.spawn@1` and child
`process.input@1`. The agent's real Bash diff read was admitted as a causally
linked `tool.call` child, approved once, claimed by the local node, and closed
with its own receipt. A real `.43` `inference.run@1` produced a durable review
artifact. The complete GitHub comment text was shown before approval; approval
landed it exactly once on PR #387 through `actuator.egress@1`, while two denied
probes did not land. A live credential yank retained the stale PR row, kept the
local agent/draft verbs available, and refused only the GitHub verbs by name.
The 1440 and 393 screenshots show the exact row and complete proposal in place,
with no modal and no mobile body overflow. The public caller plane remains
`read` / `submit` / `decide` / `events`; the protected broker, admission,
journal, model, and executor files are byte-unchanged. HS-106-09 is next.

**2026-07-27 — HS-106-07 shipped, 7/10: KILL-CRITERION PASS.**
`inference.run@1` routes recipe runs through the same admission, principal,
journal, and receipt functions as terminal input and actuator egress. Placement,
model, and egress derive at admission; token-stream material refuses before a
native invocation exists. Clause 2 is now mechanism: a tool effect inside a run
is a causally linked child with its own claim, journal events, and receipt.
Cancellation is the same submitted child-operation path. A real LAN recipe on
192.168.1.43 returned the treatment marker and a succeeded receipt; a real file
write appeared as a receipted child; a blocked run cancelled by submitted signal;
and a hub SIGKILL recovered the native run and Desk receipt as the exact word
`unknown`, with an `indeterminate` kernel receipt. The final census is literal:
zero driver-specific conditionals, all three drivers traced through
`Broker._admit_authority`, `JournalStore.create_operation` / `append`, and
`ExecutorPlane._terminal`, with the unchanged 300-line budget holding at a
299-line maximum. Child causality cost two durable linkage fields and adapter
work, not a broker branch. The generic no-executor liveness seam remains:
pending forever is still not indeterminate. The final full suite recorded 4,285
passed / 37 skipped / only the pre-adjudicated voice-notes wording failure; all
three live-bus tests are green. HS-106-08 is next against the validated kernel
spine.

**2026-07-27 — HS-106-06 shipped, 6/10.** `actuator.egress@1` is the
first outward, durable-decision driver. `submit` creates and links the existing
proposal; the owner reads its native material and `decide` advances the existing
state machine; `ActuatorExecutor` exact-claims by proposal ID and closes the
kernel receipt from the native audit ref. Historic audit rows project through
`read` without journal copies. A real webhook body crossed once after approval
and a real hub restart; rejection never egressed, stale revision refused as
`operation_revision_conflict`, and the Desk's journal-fed badge named Custom
webhook in the captured 1440px walk. The broker remains driver-blind: the final
guard reports 2 passed and every module below 300 lines. `native_id` is now
validated by terminal and actuator callers. The durable rows avoided slice I's
restart queue-loss boundary; the no-executor liveness edge remains recorded for
HS-106-07's kill criterion. Final slice proof: 86 backend tests and 296 Desk
tests passed; the exact full suite recorded 4,257 passed / 41 skipped / exactly
the five pre-adjudicated failures, while all three repaired live-bus tests are
green. HS-106-07 is next: bounded inference and the kill criterion.

**2026-07-27 — HS-106-05 shipped, 5/10.** `process.input@1` is the
second real driver. The delivery and coder façades now admit terminal text,
return an additive operation ID, exact-claim the correlated native command,
and close the generic receipt from the unchanged Phase-94 node receipt. The
native envelope/result protocol, `HubCommandService`, `NodeCommandProcessor`,
`coder_steering.deliver`, and `send_text_to_pane` remain authoritative; no
other typing family moved. Real spawned-hub/tmux proof landed text in 84.76 ms,
real `claude -p --settings` sessions preserved gate approve and verbatim deny,
and the audit showed one decision per proposal. Real SIGKILL after bytes landed
reconciled by command ID to `indeterminate_after_node_reset` and an
`indeterminate` kernel receipt, with no retry. The executor plane's
receipt-without-claim resistance was resolved in the adapter; `native_id` has
one filtered caller and HS-106-06 must confirm or refute that seam. Final slice
and density proof: 79 passed. The exact full suite completed 4,252 passed / 39
skipped / 8 unrelated failures: seven reproduced with the same signatures on
clean `origin/main`, and the eighth is the already-recorded voice-notes wording
drift. HS-106-06 is next: actuator egress must be genuinely heterogeneous.

**2026-07-26 — HS-106-04 shipped, 4/10.** The kernel spine now has
exactly four caller calls (`read`, `submit`, `decide`, `events`) and the
separate `claim` / `receipt` / `reconcile` executor plane. One trusted
startup codec adapts the existing Phase-104 gate rather than creating a
second decision state machine. Admission derives authority in four
ordered layers and approval mints an expiring, revocable, one-use
warrant bound to the immutable envelope hash, target, and placement.
The durable lifecycle journal carries only refs, hashes, and bounded
heads on a per-stream SHA-256 chain; canonical gate state and process
state remain native-backed projections. Real HTTP against a spawned hub
proved refusal receipts, agent decision refusal, immutable decisions,
claim and terminal receipt, then real SIGKILL restart with byte-equal
cursor replay and an honest indeterminate recovery receipt. Tamper,
driver-conditional, and line-budget mutations all failed by name and
returned green after restore. Final kernel/gate/schema proof: 64 passed.
The exact full suite completed 4,245 passed / 41 skipped / 1 pre-existing
unrelated UAT wording failure, documented in the story and evidence.
HS-106-05 is next: the terminal slice must lean on this spine without
adding a driver conditional.

**2026-07-26 — HS-106-01 shipped, 3/10: Article XI is law.** The
fourth council pass refused the drafted Article and was sustained on
three counts — the process-topology definition error in clause 1 that
the first three passes all missed, the present-tense fiction in clauses
2 and 6, and clause 6's redundancy plus its collision with RFC §12.
Clauses 1-5 landed as the council rewrote them; the drafted clause 6
was deleted. The council's further recommendation — defer ratification
entirely until clause 2 is materially true — was OVERRULED by the owner
under Article X.1, who ratified early behind a transitional migration
provision. The dissent is recorded verbatim in the archive, named in
the RFC §11 council record, and named again in the Constitution's own
amendment record. It was overruled, not absorbed.

Clause 6 is the price and the proof: the register is
`holdspeak/kernel/effect_ledger.json` (40 sites, 4 covered, 36 not),
fenced by the HS-106-03 test — so the law and its test are one
artifact and cannot drift apart — and no agent principal may reach a
path it names. The unmigrated surface is the owner's to carry by hand.
The clause is self-repealing: it expires with the register.

Honest standing at ratification, re-audited against the shipped tree
(the council wrote its audit before 02 and 03 landed, and three of its
rows improved): clauses 1, 3, 4, 5 are law the code can obey today —
02's principal work made 3 and 4 newly true — clause 6 is transitional
and executable, and **clause 2 is knowingly false**, which is exactly
what clause 6 enumerates. Also flipped: the RFC is RATIFIED, and §10 is
now the ratification record rather than a proposal.

**2026-07-26 — HS-106-02 shipped, 2/10.** Loopback is no longer an
authority signal. The HTTP and WebSocket doors derive typed `owner`,
`agent`, and `node` principals from distinct credentials; the right
table closes `decide`, posture, and delegation to agents before route
code runs. Gate proposal identity, usage identity, decision actor, and
authority-grant actor now come from the derived principal rather than
the request body. Agent credentials are minted at supervised spawn /
SessionStart, expire, self-revoke at SessionEnd, revoke on factory
kill, and rotate on respawn. The owner's tokenized first-load URL is
captured and scrubbed by the Desk with no login ceremony. A real
`claude -p` process proved proposal HTTP 200 and decision HTTP 403 by
name against a real staged hub; the 1440/393 first-load walk and the
full 4,231-test suite are green. Both §8 prerequisites are now landed; the broker spine
(HS-106-04) is unblocked.

**2026-07-26 — HS-106-03 shipped, 1/10.** The Article XI migration
debt register is now checked-in data: 40 static statements, 4 covered
and 36 not, with the ratified 4/8/5/13/10 family split and the ban on
agent principals reaching its named paths stated in the artifact. A
filesystem AST walk fences additions and removals by stable selector
while reporting the live file:line and family. Imported origins survive
plain from-imports, renamed imports, module aliases, and simple callable
aliases across all five families; the follow-up mutation named seven
such sites in one pass. The broker field is still empty,
but its 300-line module budget and zero driver-specific conditional
census already stand around it, including match, ternary, registry,
and table dispatch. No effect site was rerouted. HS-106-01 and
HS-106-02 remain the other pure-hardening prerequisites before the
broker spine.
