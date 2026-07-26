# The HoldSpeak Kernel — an operation broker, not a world model

**Status:** DRAFT RFC (2026-07-25). Not yet ratified; contains a
proposed constitutional amendment (§10) that only the owner may
adopt. Until ratification, this document binds nothing; after
ratification, it joins the source canon beside the plugin-system
RFC and the Constitution wins wherever they disagree.

**Provenance:** the owner's kernel directive (2026-07-25): the Desk
OS pivot is not only the Workbench-2.0 world layer — "what is our
kernel? how do things get routed through kernel calls? how do we
abstract specific actions of this OS so that, over time, we can plug
into the pipeline and build the foundation of working with agentic
engineering models and supporting SDLC / tech-lead / architect / CTO
work." Two independent designs were produced and collided: one by
the resident agent, one by Codex (read-only pass over this repo,
archived verbatim at
`pm/roadmap/holdspeak/proposals/kernel-council-codex-opinion.md`).
A third member (gpt-5.6-sol) then adversarially reviewed the
synthesis itself and returned "ratify with six required amendments"
(archived at
`pm/roadmap/holdspeak/proposals/kernel-council-sol-opinion.md`);
all six are applied in this revision. §11 records every
disagreement and who won each.

---

## 1. The thesis

HoldSpeak already contains a kernel — shattered. Phase 87's steering
chokepoint, Phase 93's operation-policy v2 (postures, bounded
grants, invariants), Phase 94's command envelope (idempotent,
generation-checked, receipted), Phase 72's one bus, and the receipts
scattered across six audit stores are five dialects of ONE pattern:

> For any consequential operation: who asked, what exact operation
> and data were admitted, what authority allowed it, which immutable
> target received it, and what actually happened.

The kernel is the small local substrate that answers those five
questions uniformly. It is NOT the Desk (that is the
shell/compositor), not the primitive catalog (that is the object
contract), not the Delivery Runtime (that is one unusually mature
subsystem), and not a workflow engine. If the kernel becomes a
universal `execute(dict)` service, this pivot has failed.

The strategic payoff, stated at its HONEST strength (amendment 1,
sol): **every consequential act by a cooperating, migrated HoldSpeak
surface is a capability-checked, journaled, replayable operation.**
The broker is an audit/consent boundary for cooperating code, not a
security boundary against malicious Python — HoldSpeak is one
process full of ambient effect authority, and a census test only
catches bypasses someone listed. The stronger claim ("every action
by ANY agent") becomes true only at the §5b confinement threshold:
raw effect primitives moved into a privileged executor process,
untrusted code holding warrants instead of imports. Until then,
documentation and UI must not say "security boundary." Humans and
agents share the same call schemas with different rights; the GUI,
voice, ⌘K, the wire, and an agent's tool harness are all shells
composing the same operations.

## 2. The de facto kernel today (the honest inventory)

Strongest seam: terminal control. `coder_steering.deliver/
deliver_keys` (canonical `%N`, grant or posture authority, identity
re-verified before input, allow-listed keys, audits success AND
refusal); `delivery/terminal.py` improves addressing into
`target_id + target_generation`; `delivery/commands.py` is already a
specialized kernel protocol (versioned immutable envelope, UUID,
expiry, payload hash, hub-derived authority, per-target sequence,
node dedup, reconciliation by command id).

External effects: `db/actuators.py` (proposed → approved →
executed/rejected/failed), `actuator_authority.py` (approval bound
to payload, destination, preview, effect class, policy version),
re-checked by the executor before egress.

Compute: `RunLifecycle` + `db/invocations.py` give recipes, chains,
and workflows durable invocation identity, placement, lineage. Ask
does not yet use it.

Policy: `operation_policy.py` — typed descriptors, Secure/Normal/
YOLO, hard invariants that refuse even in YOLO, scoped-grant
matching, named refusals. Kernel-shaped, deliberately incomplete
(four families; dictation, inference, factory, cadence, sync, and
destructive desk mutation deferred by Phase 93).

Known cracks (the census the migration must close):

- `runtime/dictation_capture.py` and `web/routes/cadence.py` call
  `tmux_transport.send_text_to_pane` DIRECTLY — the steering
  chokepoint is true for steering surfaces, not for every way
  HoldSpeak types.
- Dictation/wake and voice macros call `TextTyper` directly.
- `web_auth.py` treats loopback as trusted owner — a local agent
  handed the current API would be a confused deputy with owner
  authority (§8, prerequisite 1).
- Audit is fragmented across steering audit, actuator audit,
  delivery receipts, capability invocations, attempt history, and
  the dictation journal, with no operation-wide correlation spine.

## 3. The kernel interface: four calls

`holdspeak/kernel/` exposes exactly four public calls. Operations
are REGISTERED, VERSIONED TYPES submitted through `submit` — never
new syscalls. Registration is trusted startup configuration; no
LLM, plugin, or runtime caller may register operation types.

1. **`read(refs, view, consistency)`** — canonical objects, process
   state, operation state, receipt projections. Grounding is a
   bounded read view; callers pass refs, never copied authoritative
   content. Reads are cheap and pay no kernel ceremony beyond auth.
2. **`submit(OperationRequest)`** — the ONLY entrance for a
   consequential run, mutation, signal, or external effect. Returns
   an operation handle: `running | awaiting_decision | refused |
   <terminal>`.
3. **`decide(operation_id, approve|reject, expected_revision)`** —
   records a decision against the already-admitted operation. It
   can never change payload, target, or placement; approval mints
   ONE-USE authority bound to the admitted envelope hash. (The
   Phase-104 tool-call gate is this call, prototyped early.)
4. **`events(after_cursor, filter)`** — replayable batches from the
   operation journal. WebSocket/long-poll are transports for this
   call, never truths of their own.

The routing path is deliberately boring: authenticate caller →
typed validation per operation module → canonical ref + immutable
target binding → capability and policy admission → journal commit →
decision wait or driver dispatch → executor receipt → replayable
event.

**The four calls are the CALLER/USERLAND plane only** (amendment 3,
sol). A second, separately-specified EXECUTOR plane exists for
authenticated executors (nodes, the privileged effect process of
§5b): `claim` (atomically acquire admitted work — destructive queue
acquisition with claim semantics, as `HubCommandService.
claim_for_node` already implements), `receipt`/`ack` (report the
immutable outcome, including indeterminate), and `reconcile`
(resolve uncertain effects by command id). This plane is not hidden
as an implementation detail and is never forced through `submit` —
an executor acquiring already-admitted work is not proposing a new
consequential act.

## 4. The operation envelope

Callers send roughly:

```json
{
  "request_schema": 1,
  "request_id": "uuid",
  "idempotency_key": "caller-stable",
  "operation": {"name": "process.input", "version": 1},
  "subject_refs": ["note:n_123"],
  "target": {"ref": "process:p_456", "expected_generation": "gen_7"},
  "arguments": {"text": "Continue.", "submit": true},
  "grounding_refs": [{"ref": "story:HS-105-02", "revision": "tree_abc"}],
  "placement": "node:studio",
  "correlation": {"parent_process_id": "p_456", "attempt_id": "att_9"},
  "deadline": "2026-07-25T20:00:30Z"
}
```

**The caller never asserts its own authority.** Actor, control mode,
authority basis, effect class, data classes, and policy version are
DERIVED AT ADMISSION: the broker authenticates the principal,
validates against the operation module's typed codec (the envelope
must never become a JSON junk drawer), resolves refs, hashes the
canonical material, snapshots the operation spec + current policy,
and records an admitted envelope. Example registered operations:
`process.spawn`, `process.input`, `process.interrupt`,
`inference.run`, `external.github.create_issue`,
`knowledge.propose_ingest`, `desktop.type_text`.

## 5. Authority: four distinct layers, three principals

Layers (all four checked, in order, at admission — see the
one-decision rule below for what executors re-check):

1. **Authenticated principal.**
2. **Declared capability** for that principal and executor — an
   object capability bound to principal, operation type,
   resource/target generation, data classes, constraints, TTL/use
   count, and delegator.
3. **Hard prerequisites** — schema, configured destination, payload
   binding, target generation, secret custody. These refuse even in
   YOLO (the Phase-93 invariant rule, unchanged).
4. **Interruption policy** — allow / propose / refuse under
   Secure/Normal/YOLO.

**The one-decision rule** (amendment 2, sol — restoring the raw
council rule the first synthesis wrongly strengthened): authority is
resolved ONCE, at hub admission, and represented as a verifiable,
expiring, payload-bound EXECUTION WARRANT (the policy snapshot +
envelope hash `delivery/commands.py` already models). A remote
executor validates the warrant (expiry, revocation, target
generation, sequence, payload hash) and re-checks its LOCAL HARD
PREREQUISITES immediately before the effect — it never
re-authenticates the initiating human or re-resolves grants and
posture, which would either require replicated authority state or
create the second policy decision §7 forbids. Explicit rules ride
the warrant: expiry (deny after), revocation (hub-published, checked
at claim), and indeterminate effects (never blindly retried;
reconciled by command id).

Principals:

- **Owner** — may decide, issue and revoke delegation, change
  posture.
- **Agent** — minted per agent process or Work attempt, expires,
  sees only delegated refs, may submit allowed work or proposals,
  and can NEVER call `decide`, change posture, or claim ownership.
- **Node** — distinct, as `delivery/node_link.py` already models.

Prerequisite finding: because `web_auth.py` trusts loopback as
owner, kernel endpoints authenticate even on loopback when the
caller is an agent (scoped bearer capability or protected local
socket). This lands BEFORE any agent gets kernel access.

### 5b. Effect-capability confinement (the enforcement boundary)

Amendment 6's original contribution (sol), adopted: the broker
alone is import-discipline — `connector_runtime.PermissionGate`
itself says it is "honest enforcement, not a security boundary,"
and any Python in-process can call `subprocess`, `TextTyper`, or
the tmux transport directly. The enforcement path, phased:

- Raw effect primitives (Accessibility typing, tmux input, external
  sockets, connector subprocesses, destructive process control)
  move into a SMALL PRIVILEGED EXECUTOR PROCESS.
- Agent, plugin, and ordinary web-runtime processes do not possess
  those ambient capabilities; they hold only a protected local IPC
  endpoint that accepts broker-minted, payload-bound, expiring
  execution warrants (§5's one-decision rule, applied locally).
- **The named threshold:** before untrusted plugins or
  agent-authored code EXECUTE, capability claims require
  process/OS isolation — not import discipline. Until that
  threshold, every kernel security claim in docs and UI is scoped
  to cooperating code (§1).

## 6. Processes, the journal, and the bus

**Process model = a projection, not a rewrite.** One index
(`process_id, kind, definition_ref, principal, parent, generic_state,
domain_state, node, target_ref+generation, current_operation_id,
heartbeat, result_refs, started/ended`) over the NATIVE records —
agent sessions, capability invocations, plugin jobs, captures, Work
attempts project in; their tables stay authoritative. Universal
states stay small (`starting/running/waiting/unknown/ended/failed`);
domain states remain domain data. A signal is a submitted operation.

**The journal** is append-only operation lifecycle metadata: hub
sequence, event id, operation/process/correlation/causation ids,
typed event version, refs, privacy class, timestamp. Domain content
stays in its canonical store — the journal holds refs, hashes,
bounded heads, result refs. Every attempted consequence produces an
immutable terminal receipt, INCLUDING refusals and
unknown/indeterminate outcomes. Node effects keep the two-sided
ledger rule (persist before final response, dedupe by command id,
never blindly retry an uncertain effect). Journal records are
SHA-256 hash-chained per stream (the Borrowed-Fire-II carry-over):
tamper-evidence is cheap at this one write path and upgrades the §1
claim from audited to provable.

**The bus is a projection of the journal** — at-least-once, cursor
replay, carries FACTS never commands. Commands travel through
`submit` and targeted executor queues. `/ws`, node long-poll, and
future native streams transport the same event batches without
becoming independent truths (today's `/ws` broadcast is ephemeral
with no cursor — it becomes a transport, not a source).

## 7. Migration: the strangler ladder (no big bang)

Old routes and tables remain throughout; adapters dual-link by
operation/correlation id; reads move only after generated consumer
parity; a transactional outbox may feed the journal from existing
repositories; NEVER dual-execute or maintain two policy decisions.

Order amended per sol (amendment 4): the census TEST lands first as
pure hardening, but broad migration waits until three HETEROGENEOUS
thin slices have proven the shared spine — breadth within the
terminal family is not heterogeneity, and a terminal-shaped broker
ossified around Phase 94 semantics would force driver conditionals
when actuators (durable proposal transitions, material-authority
parity) and inference (placement, long attempts, streaming,
cancellation) arrive.

1. **Pin the typing-effect census test** (no rerouting yet) and land
   the §8 prerequisites.
2. **Thin terminal slice** — reference driver. Add broker + journal;
   adapt `HubCommandService`/`NodeCommandProcessor`, do not rewrite
   their protocol; delivery/coder routes become façades returning an
   additive kernel operation id; `coder_steering`/`coder_factory`
   remain the executors.
3. **Thin actuator slice.** A kernel operation creates/links the
   existing proposal; `decide` advances the EXISTING state machine;
   `ActuatorExecutor` stays the driver; existing audit rows project
   as receipts. No rival proposal system.
4. **Thin bounded-inference slice.** `RunLifecycle` becomes a kernel
   adapter for recipes first. **Apply the kill criterion here
   (§12)** — three drivers sharing admission/principal/journal/
   receipt code without broker conditionals, or stop.
5. **Broad migration of the typing census.** Define dictation's
   commit-boundary semantics FIRST, then route Cadence replies,
   dictation-to-agent, keys, kill, spawn, launch through
   `process.input` — dictation is migrated once, with settled
   authority semantics, never twice. Then chains/workflows, Ask
   (content may stay ephemeral; every attempt gets an
   operation/placement receipt), plugin jobs and mesh runs as child
   attempts. Capture, Whisper, punctuation, rewrite stay on the
   low-latency path; audio frames are never journaled.
6. **Phase 105 consumes, never defines.** The verb registry and drop
   matrix are USERLAND dispatch: menu, ⌘K, and wire invoke the same
   userland handler, and only consequential handlers cross the
   kernel (note→recipe submits `inference.run`; note→KB submits a
   proposal; filing a zone is the existing reversible membership
   update; groundable→orb is UI context only).

## 8. Prerequisites (checkable now, before any kernel code)

1. **Principal separation on loopback** (§5) — close the confused
   deputy before agents touch any API in anger.
2. **The typing-effect census** (§2 cracks) — even without the
   broker, pinning today's bypass call sites is pure win.

## 9. Userland: the SDLC / tech-lead / architect / CTO layer

Programs written on `read/submit/decide/events` — never new
syscalls:

- **Delivery orchestration:** Story → attempt → worktree → launch
  agent → watch → bounded instruction → dw gate → evidence. Phase
  94 is the first such program already.
- **Review and release:** exact commit/PR/story/evidence refs →
  reviewer processes → findings as artifacts → PROPOSED GitHub
  comments/status → a release cut only through receipted external
  operations.
- **Architecture decisions:** meeting/ask material → ADR objects
  with source revisions and lineage; publication and announcement
  as separate proposals. A decision queryable years later, with its
  provenance receipts attached.
- **Tech-lead loops:** triage waiting agents, failing CI, missing
  evidence, stale attempts; delegate scoped follow-ups; draft the
  status update. Cadence and Attention are INPUTS, not a second
  scheduler.
- **Portfolio views:** projects, decisions, risks, freshness,
  cost/placement, outstanding authority — pure `read + events`; no
  executive syscall exists.

What the kernel guarantees userland: stable opaque identity,
canonical ref resolution, immutable target/payload binding,
authenticated principals, least authority, typed refusal,
idempotency with explicit uncertainty, replayable state, source
revision + lineage, honest placement/egress, privacy-aware
retention, and a receipt for every attempted consequence. What it
never guarantees: that a rubric is wise, an LLM is right, or a
priority is good — those are userland judgments.

## 10. Proposed constitutional amendment (owner ratification only)

> **Article XI — The Kernel**
>
> 1. A consequential operation is one that crosses a principal,
>    process, machine, model/egress, or irreversible-effect
>    boundary. An operation's consequence is judged for itself:
>    nesting inside an admitted operation never exempts it.
> 2. Every consequential operation enters the system through the
>    kernel's one admission path and produces a receipt, including
>    on refusal. A consequential effect performed by a tool inside
>    a model's run is submitted as a causally linked child
>    operation of that run.
> 3. The caller never asserts its own authority; authority is
>    derived at admission and bound immutably to the admitted
>    operation.
> 4. Humans and agents share the kernel's schemas and never its
>    rights; only the owner decides.
> 5. Reads, presentation, and side-effect-free computation —
>    including the token stream inside a model's run — are not
>    consequential operations and owe the kernel nothing. This
>    clause exempts computation, never effects.
> 6. Nothing in this Article narrows Article V: whatever types,
>    sends, files, spawns, or kills passes propose/approve/execute
>    regardless of how local or reversible it appears.

(Clauses 1, 2, 5, and 6 close the nested-effects loophole sol
demonstrated: without them, one admitted `inference.run` exposing
in-process file/terminal tools could classify every tool effect as
"the run's interior" — receipted at the outer layer, invisible where
the actual engineering happens, technically compliant while
defeating the Article and colliding with Article V.)

## 11. Council record: disagreements and dispositions

- Resident agent proposed "verbs = syscalls"; Codex corrected:
  operations are registered types under one `submit`, and the 105
  verb registry is userland dispatch. **Codex adopted.**
- Codex surfaced the loopback confused deputy and the typing-effect
  census cracks with file-level evidence. **Adopted as
  prerequisites.**
- Resident agent added journal hash-chaining (from the AgentGlass
  research pass). **Adopted (§6).**
- Both independently: journal-as-truth/bus-as-projection, process
  model as projection, strangler migration starting at terminal
  delivery, reads exempt, no audio/token journaling. **Convergent —
  highest-confidence elements of this design.**
- Third member (gpt-5.6-sol), adversarial pass on the synthesis:
  verdict "ratify with six amendments," ALL SIX ADOPTED — (1) the
  "only entrance" claim narrowed to cooperating surfaces with the
  threat model named (§1); (2) the one-decision/warrant rule
  restored after the synthesis wrongly strengthened executor
  re-checks into distributed re-authorization contradicting
  `delivery/commands.py` (§5); (3) the executor plane
  (claim/receipt/reconcile) specified beside the four caller calls
  (§3); (4) the migration ladder reordered to three heterogeneous
  thin slices before broad terminal-family migration, dictation
  semantics before dictation rerouting (§7); (5) Article XI's
  nested-effects loophole closed and reconciled with Article V
  (§10); (6) effect-capability confinement added as the enforcement
  boundary with a named threshold (§5b). Sol also restored two
  sanded-off caveats: `PermissionGate` is not a sandbox, and broker
  density guards must be testable (§12).

## 12. Non-goals and the kill criterion

Never routed through the kernel: pointer motion, selection, icon
state, window placement, Info rendering, menu composition, drop
physics, audio frames, transcription windows, token streams.
Never replaced by generic "resources": notes, meetings, artifacts,
dw Markdown, git, tmux, provider SDKs, their state machines.
Ordinary reversible local edits never pay remote-command ceremony.

Top risks: (1) a God envelope/registry — countered by typed
operation modules, a tiny broker, and no generalizing a field until
two real drivers need it, ENFORCED as testable acceptance criteria
(amendment 6b, sol): a broker line-budget guard in the Phase-79
style, and a census test asserting zero driver-specific conditionals
in broker modules — both green before any slice merges; (2) false
authority through a shared
interface — countered by §5/§8 landing first; (3) migration double
truth / a central bottleneck — countered by domain tables staying
authoritative, correlation over copying, the outbox, executor-local
ledgers, one census at a time.

**The kill criterion (Codex's, adopted verbatim in spirit):** if the
first three drivers — terminal input, actuator egress, inference
runs — cannot share admission, principal, journal, and receipt code
without driver-specific conditionals in the broker, stop calling it
a kernel. The durable idea is the invariant spine, not the name.

## 13. Sequencing

Phase 103 close → Phase 105 (Workbench, the face) → Phase 104
(Borrowed Fire II — whose gate and receipts are early kernel organs:
the gate is `decide`, the hash chain is §6, the capability ledger is
a §5 precursor) → kernel phases chartered from this RFC's ladder
(§7), beginning with the §8 prerequisites, which may land in any
earlier phase as riders since they are pure hardening.
