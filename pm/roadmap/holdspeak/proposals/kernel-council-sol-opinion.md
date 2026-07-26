# Third Council Opinion: the broker is right; the claimed boundary is not

**Verdict: ratify with amendments.** The RFC has the right center of gravity: consolidate invariant machinery, preserve domain state machines, and keep SDLC orchestration in userland. I would not ratify its interface or Article XI as written, however. It currently promotes a cooperative routing convention into a constitutional security guarantee, and it describes a four-call *client* API as though it were the complete kernel protocol.

## 1. Weakest load-bearing claim: “the only entrance”

The weakest claim is the strategic payoff in §1: “every action any human or agent takes” becomes capability-checked, journaled, and replayable, backed by §3’s assertion that `submit` is the “ONLY entrance” for consequences (`PLAN_KERNEL_OPERATION_BROKER.md`, §1 lines 43–50; §3 lines 94–120). Nothing in the design makes that true.

HoldSpeak is a Python process full of ambient effect authority. Today `runtime/dictation_capture.py::_try_tmux_agent_reply` imports `send_text_to_pane` and calls it directly (lines 422–430); the same class invokes `TextTyper.type_text` on several paths (lines 178–192, 484–510). `web/routes/cadence.py::reply_to_agent` also imports and invokes the transport directly (lines 229–263). The RFC knows these call sites and proposes a census test, but a census only detects bypasses somebody remembered to put on the list. A later plugin can import `subprocess`, open a socket, call `TextTyper`, or invoke the tmux transport without the broker seeing an attempt.

The existing “chokepoint” also does not guarantee a receipt: `coder_steering._audit_delivery_result` catches every audit exception and returns `audit_id = None` after the effect may already have happened (`coder_steering.py`, lines 538–586). Worse, the connector gate explicitly says it is “honest enforcement, not a security boundary” because malicious Python can call `subprocess.run` directly (`connector_runtime.py`, lines 16–23).

Thus the likely practical failure is not a bad codec; it is invisible execution. The journal can be complete only over calls it receives. Without privilege separation or an explicitly non-adversarial threat model, the honest claim is “all migrated, cooperating HoldSpeak surfaces route through the broker,” not “every action any agent takes.”

## 2. Sharp edges lost in synthesis

The synthesis lost two important qualifications from the raw Codex opinion.

First, it changed the authority rule. The raw opinion says the hub resolves policy once and a remote executor consumes that snapshot while rechecking **local hard prerequisites** (`kernel-council-codex-opinion.md`, §2 line 71). The synthesis instead says all four layers—including authenticated principal, capability, and interruption policy—are rechecked locally immediately before effect (`PLAN_KERNEL_OPERATION_BROKER.md`, §5 lines 153–167).

The code implements the raw rule deliberately. `delivery/commands.py` says authority is resolved once at the hub (lines 13–16); `decode_decision` says the decision is “never re-resolved node-side” (lines 187–190); `NodeCommandProcessor.process` validates protocol/expiry/target generation/sequence and consumes the policy snapshot (lines 418–541). A node cannot freshly re-authenticate the initiating human or re-resolve hub grants and posture without replicated authority state or an online callback. Doing so creates the second policy decision that §7 line 219 forbids. Not doing so makes §5 false. The RFC must choose: one hub decision represented by a verifiable, expiring execution warrant plus local prerequisite checks, or a specified distributed authorization protocol with freshness and revocation semantics.

Second, the synthesis dropped the raw opinion’s explicit warning that `PermissionGate` does not sandbox malicious packs (raw §1 line 13). That caveat is not editorial trivia; it bounds the meaning of “capability-checked.” It should survive beside every kernel security claim. The raw opinion’s “density guards” against broker conditionals (raw §5 line 118) also became a softer two-driver maxim without an enforceable acceptance test.

## 3. An operation that fits none of the four calls

The real counterexample is **a remote node claiming its pending command batch**.

`NodeLinkState.poll_commands` authenticates the node, checks its command capability and protocol, then calls the command source and returns executable envelopes (`delivery/node_link.py`, lines 466–486). The source is `HubCommandService.claim_for_node`, which atomically drains the node’s queue and mutates durable hub state to `claimed` (`delivery/commands.py`, lines 891–899).

This is not `read`: it is destructive queue acquisition, and concurrent or repeated calls have claim semantics. It is not `events`: §6 says events carry facts, never commands. It is not `decide`: the node is not the owner approving an operation. It does not fit `submit` cleanly either: the executor is not proposing a new consequential act; it is acquiring already-admitted work and needs a batch of command envelopes in the response, not an operation handle.

The RFC needs to say that the four calls are the **caller/userland plane**, and separately specify an authenticated executor plane such as `claim`, `ack/receipt`, and `reconcile`. Hiding that plane as a “private implementation detail” does not eliminate a machine-crossing protocol. Forcing it through `submit` would be exactly the universal-dictionary pressure the RFC says to resist.

## 4. The migration rung ordered wrong

Rung 2, “close the typing-effect census,” is too early. After one terminal vertical slice, it migrates Cadence, dictation-to-agent, keys, kill, spawn, and launch—all before the actuator and inference drivers test the abstraction (`PLAN_KERNEL_OPERATION_BROKER.md`, §7 lines 221–242). That contradicts §12’s own rule not to generalize until two real drivers need a field (lines 332–344).

Breadth within the terminal family is not heterogeneity. Terminal delivery wants generation checks, target sequencing, and a short command TTL. Actuators bring a durable proposal transition and material-authority parity. Inference brings placement, long-running attempts, streaming projections, and cancellation. If the team routes every typing/factory path through a terminal-shaped broker before seeing those other two, target, state, receipt, and retry semantics will ossify around Phase 94. When rungs 3 and 4 expose the mismatch, the team must either add driver conditionals or remigrate all the rung-2 façades—precisely the centralization and double-truth failure the strangler is meant to avoid.

Keep the census *test* as prerequisite hardening, but reorder implementation to: one thin terminal slice, one thin actuator slice, one bounded inference slice, apply the kill criterion, then migrate the remaining typing census. Rung 5’s dictation commit-boundary semantics must also be defined before rung 2 reroutes dictation-to-agent, or dictation is migrated twice with provisional authority semantics.

## 5. Article XI’s exploitable ambiguity

Clauses 1 and 5 have no rule for nested effects. Clause 1 defines consequence by crossing a boundary; clause 5 exempts “the interior of a model’s run” without limiting that interior to pure computation (`PLAN_KERNEL_OPERATION_BROKER.md`, §10 lines 294–306).

A future agent story can therefore submit one admitted `inference.run`, expose in-process `write_file`, process-launch, or terminal tools to the model, and classify every tool invocation as the run’s interior. A tracked worktree edit is local, reversible, and can execute under the same agent principal and process, so it crosses none of clause 1’s enumerated boundaries; clause 5 says it owes the kernel nothing. The outer inference has a receipt while the actual engineering actions do not. This technically complies with Article XI while defeating its purpose—and collides directly with existing Article V: anything that “types, sends, files, spawns, or kills” must pass propose/approve/execute, and every attempt leaves a receipt (`CONSTITUTION.md`, Article V lines 58–67).

Clause 5 must exempt only side-effect-free computation and presentation. Every nested tool effect must be evaluated independently under clause 1 and, when consequential, submitted as a causally linked child operation. “Reversible local edit” also needs reconciliation with Article V rather than a non-goal that silently narrows it.

## 6. Original contribution: effect-capability confinement

Neither prior member proposed an enforcement boundary. Add an **effect-capability confinement** section: raw effect primitives (Accessibility typing, tmux input, external sockets, connector subprocesses, destructive process control) belong to a small privileged executor process; agent, plugin, and ordinary web-runtime processes do not possess those ambient capabilities. They receive only a protected local IPC endpoint that accepts broker-minted, payload-bound, expiring execution warrants.

This can be phased, but the RFC must name the threshold: before untrusted plugins or agent-authored code execute, capability claims require process/OS isolation, not import discipline. Until then, documentation and UI must call the broker an audit/consent boundary for cooperating code, not a security boundary.

## Required amendments

1. Narrow the universal chokepoint claim until raw effect authority is confined; add the threat model and enforcement level.
2. Restore “one hub authorization decision; executor rechecks warrant validity and local hard prerequisites,” with explicit expiry, revocation, and indeterminate-effect rules.
3. Define the executor `claim`/receipt/reconcile plane separately from the four userland calls.
4. Validate the shared spine with thin terminal, actuator, and inference slices before broad terminal migration; move dictation boundary semantics ahead of dictation rerouting.
5. Rewrite Article XI clause 5 to exclude nested effects and reconcile “reversible local edits” with Article V.
6. Restore the malicious-pack caveat and make broker density/conditional guards testable acceptance criteria.

With those amendments, ratify. Without them, HoldSpeak would constitutionalize a kernel boundary that its process model and its own current code can bypass.
