# Phase 106 - The Kernel

**Status:** ACTIVE (3/10). Chartered 2026-07-26 from
[`PLAN_KERNEL_OPERATION_BROKER.md`](../../../docs/internal/PLAN_KERNEL_OPERATION_BROKER.md)
(the RFC, three council passes) and the owner's direct charge:

> "HoldSpeak's ambition to come a lot closer to an Operating System
> based on the Web for the Tech-Lead/Architect who uses AI on the
> day-to-day, who follows on to PRs, who controls agents through
> xterm.js, who keeps project memory, who chats to agents, who
> records decisions and then creates artifacts out of those
> decisions and meetings."

**Last updated:** 2026-07-26 (HS-106-04 shipped; 3/10).

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

- [ ] HS-106-01 through HS-106-08 shipped with evidence.
- [ ] The kill criterion (RFC §12) applied at HS-106-07 and its
      verdict recorded honestly — including the outcome where it
      fails and the name is dropped.
- [ ] The broker density guards green before any slice merges: a
      line-budget guard in the Phase-79 style, and a census test
      asserting zero driver-specific conditionals in broker modules.
- [ ] `uv run pytest -q --ignore=tests/e2e/test_metal.py` green
      (pre-existing unrelated failures documented per-story).
- [ ] `cd web && npx tsc --noEmit -p . && npx vitest run && npm run
      build && npm run tokens:gate` green.
- [ ] The userland program (HS-106-08) proven on the owner's REAL
      pull requests on real metal, not seeded fixtures.
- [ ] HS-106-09 docs shipped touching the entry points.
- [ ] HS-106-10 closeout: the sitting loop run to the owner's
      verdict per Article IX.4.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-106-01 | Article XI ratified, with the migration provision | ready | [story-01-article-xi](./story-01-article-xi.md) | — |
| HS-106-02 | Principal separation on loopback | done | [story-02-principals](./story-02-principals.md) | [evidence-story-02](./evidence-story-02.md) |
| HS-106-03 | The effect census, pinned as a test | done | [story-03-census-test](./story-03-census-test.md) | [evidence-story-03](./evidence-story-03.md) |
| HS-106-04 | The broker and the journal — four calls | done | [story-04-broker-journal](./story-04-broker-journal.md) | [evidence-story-04](./evidence-story-04.md) |
| HS-106-05 | Thin slice I — terminal input | ready | [story-05-slice-terminal](./story-05-slice-terminal.md) | — |
| HS-106-06 | Thin slice II — actuator egress | ready | [story-06-slice-actuator](./story-06-slice-actuator.md) | — |
| HS-106-07 | Thin slice III — inference, and the kill criterion | ready | [story-07-slice-inference-kill](./story-07-slice-inference-kill.md) | — |
| HS-106-08 | Userland — PR follow-through, the tech-lead's loop | ready | [story-08-userland-pr-follow](./story-08-userland-pr-follow.md) | — |
| HS-106-09 | Docs — the kernel at the entry points | ready | [story-09-docs](./story-09-docs.md) | — |
| HS-106-10 | Closeout — the sitting and the kernel ledger | ready | [story-10-closeout](./story-10-closeout.md) | — |

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

**2026-07-26 — HS-106-04 shipped, 3/10.** The kernel spine now has
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
