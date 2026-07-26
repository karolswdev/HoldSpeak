# HoldSpeak’s kernel should be an operation broker, not another world model

## Verdict

The kernel is not the Desk, `WebRuntime`, the primitive catalog, or the Delivery Runtime. Those are respectively the shell/compositor, the current boot-time orchestrator, an object contract, and one unusually mature subsystem. The kernel should be the small local substrate that answers five questions for any consequential operation: **who asked, what exact operation and data were admitted, what authority allowed it, which immutable target/process received it, and what actually happened**.

Today HoldSpeak has the pieces of that substrate, but as a federation of feature-local microkernels. The pivot should consolidate their invariants, not replace their domain models. If “kernel” becomes a universal `execute(dict)` service or a new workflow engine, the pivot has failed.

## 1. The de facto kernel today

The strongest syscall-like seam is terminal control. `holdspeak/coder_steering.py` owns `deliver()` and `deliver_keys()`: it resolves a tmux target to canonical `%N`, consumes either a bounded pane grant or YOLO posture authority, re-verifies identity immediately before input, allow-lists named keys, and audits success and refusal. `holdspeak/delivery/terminal.py` improves the address into opaque `target_id + target_generation`. `holdspeak/delivery/commands.py` is already a specialized kernel protocol: a versioned immutable envelope, UUID, expiry, payload hash, hub-derived authority, per-target sequence, node-side deduplication, and reconciliation by command ID. `NodeCommandProcessor` even specifies an admission/execution order. `db/delivery_receipts.py` supplies the node ledger and aggregate hub Receipt.

The external-effect microkernel is separate. `db/actuators.py` implements `proposed -> approved -> executed|rejected|failed`, bounded grants, and transition audit. `actuator_authority.py` binds approval to payload, normalized destination, preview, effect class, and policy version. `plugins/actuator_executor.py` rechecks that binding before egress, and `plugins/gated_connector.py` narrows the operation again through `connector_runtime.PermissionGate`. This is a good driver stack, although `PermissionGate` explicitly says it disciplines honest packs rather than sandboxing malicious Python.

The compute/run microkernel is younger. `web/routes/primitives/_shared.py::RunLifecycle` and `db/invocations.py` give Recipes, Chains, and Workflows durable invocation/attempt identities, placement, result refs, and lineage. `PluginHost`, the durable deferred plugin queue, and `intel/mesh_relay.py` provide idempotency, scheduling, and remote model placement. Ask does not use that lifecycle: `/api/ask` resolves canonical grounding and reports honest placement, but persists no run unless the user later keeps an artifact.

Capability and consent policy lives in `operation_policy.py`: typed descriptors, Secure/Normal/YOLO, hard invariants, scoped-grant matching, and named refusals. It is kernel-shaped but intentionally incomplete. Its registry covers four families, and Phase 93 explicitly deferred much of dictation, inference, factory, cadence, sync, and destructive Desk mutation.

IPC is also plural:

- FastAPI routes are the typed client boundary.
- `web/src/runtime/RuntimeBus.tsx` and `/ws` provide one `type + data` broadcast socket, token-gated off loopback, but it is ephemeral, server-to-client, and has no cursor or replay.
- `delivery/node_link.py` has stronger node IPC: distinct tokens, capabilities, monotonic liveness, allow-listed metadata events, cursors, and outbound long-poll command claims.
- Agent hooks communicate through `agent_context`’s JSON registry and file-mtime polling.
- Delivery events, the mesh inference queue, and the plugin-job queue each have their own replay/claim semantics.

Audit is consequently fragmented across steering audit, actuator transition/grant audit, delivery command Receipts, capability invocations, Work-attempt history, and the dictation journal. The seams are real, but there is no operation-wide correlation spine.

There are also honest cracks in the “one chokepoint” story. `runtime/dictation_capture.py` and `web/routes/cadence.py` call `tmux_transport.send_text_to_pane` directly, while dictation/wake and voice macros call `TextTyper` directly. The steering chokepoint is true for steering surfaces, not yet for every way HoldSpeak types. That is precisely the sort of census a kernel migration must close.

## 2. The proposed kernel

I would build `holdspeak/kernel/` around four public calls:

1. **`read(refs, view, consistency)`** resolves canonical objects, process state, operation state, or Receipt projections. Grounding is a bounded read view; callers pass refs, never authoritative copied content.
2. **`submit(OperationRequest)`** is the only entrance for a consequential run, mutation, signal, or effect. It returns an operation handle in `running`, `awaiting_decision`, `refused`, or a terminal state.
3. **`decide(operation_id, approve|reject, expected_revision)`** records a decision against the already-bound operation. It cannot change payload, target, or placement.
4. **`events(after_cursor, filter)`** returns a replayable batch from the operation journal. WebSocket is one transport for this call, not the source of truth.

The routing path is deliberately boring: caller authentication → operation lookup and typed validation → canonical ref/target binding → capability and policy admission → journal commit → decision wait or driver dispatch → executor Receipt → replayable event.

`process.spawn`, `process.input`, `process.interrupt`, `inference.run`, `external.github.create_issue`, and `knowledge.propose_ingest` are registered, versioned operation types submitted through the same call; they are not additional syscalls. Registration is trusted startup configuration, not something an LLM or plugin may perform dynamically.

A client request should be roughly:

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

The caller does **not** set actor, control mode, authority basis, effect class, data classes, or policy version. At admission the broker authenticates the principal, validates the operation-specific input schema, resolves refs and immutable targets, hashes the canonical material, snapshots the registered operation spec and current policy, then records an admitted envelope. Each operation type keeps a typed codec; the envelope must not become an unvalidated JSON junk drawer.

Authority needs four distinct layers:

1. authenticated principal;
2. declared capability for that principal and executor;
3. non-negotiable prerequisites such as schema, configured destination, payload binding, target generation, and secret custody;
4. interruption policy: allow, propose, or refuse under Secure/Normal/YOLO.

A grant is an object capability bound to principal, operation type, resource/target generation, data classes, constraints, TTL/use count, and delegator. `decide` mints one-use authority bound to the admitted envelope hash. Remote executors consume the hub’s policy snapshot once, as `delivery/commands.py` does now, but recheck their local hard prerequisites immediately before the effect.

Humans and agents should share request, status, Receipt, and event schemas, but not credentials or rights. The owner principal may make decisions and issue/revoke delegation. An agent principal is minted for one agent process or Work attempt, expires, sees only delegated refs, may submit allowed work or proposals, and can never call `decide`, change posture, or claim to be the owner. A node principal remains distinct. This is a prerequisite for agentic engineering: `web_auth.py` currently treats loopback as trusted owner, so exposing that API directly to local agents would create a confused deputy. The kernel endpoint should authenticate even on loopback when used by agents, via scoped bearer capability or a protected local socket.

The process model should be a projection, not a forced rewrite of every table:

```text
process_id, kind, definition_ref, principal, parent_process_id,
generic_state, domain_state, node, target_ref+generation,
current_operation_id, heartbeat, result_refs, started/ended
```

An agent session, capability invocation, plugin job, capture, and delivery Work attempt can project into this index while retaining its native record. Universal states should stay small (`starting/running/waiting/unknown/ended/failed`); domain states remain domain data. A process signal is just a typed submitted operation.

The journal is append-only operation lifecycle metadata with hub sequence, event ID, operation/process/correlation/causation IDs, typed event version, refs, privacy class, and timestamp. Domain content remains in its canonical store; the kernel normally retains refs, hashes, bounded heads, and result refs. Executor attempts produce immutable terminal Receipts, including refusals and unknown/indeterminate outcomes. Node effects retain the existing two-sided ledger rule: persist before final response, dedupe by command ID, never blindly retry an uncertain effect.

The bus is a projection of this journal with at-least-once delivery and cursor replay. It carries facts, not commands. Commands travel through `submit` and targeted executor queues. `/ws`, node long-poll, and future native streams can all transport the same event batches without becoming independent truths.

## 3. Migration without a big bang

1. **Use terminal delivery as the reference driver.** Add the kernel broker/journal and adapt `HubCommandService`/`NodeCommandProcessor`; do not rewrite their protocol. Existing `/api/delivery/commands` and coder routes become façades that return an additive kernel operation ID. Keep `coder_steering` and `coder_factory` as executors.
2. **Close the effect census.** Route Cadence replies and dictation-to-agent around `process.input`; route allowed keys, kill, spawn, and launch similarly. Pin direct `tmux_transport` call sites in tests. Delivery Source, Work attempt, dossier, and terminal-stream reads remain Delivery Runtime projections, not kernel-owned business data.
3. **Wrap actuators.** A kernel operation creates/links the existing proposal; `decide` advances its existing state machine; `ActuatorExecutor` remains the driver. Preserve its material-authority parity and `PermissionGate`. Project existing audit rows as kernel Receipts rather than creating a rival proposal system.
4. **Adopt bounded runs.** Make `RunLifecycle` a kernel adapter, first for Recipes/Chains/Workflows, then Ask. Ask can still be ephemeral in content, but every attempt gets an operation/placement Receipt. Plugin jobs and mesh runs become child attempts, not new orchestration abstractions.
5. **Move only dictation’s commit boundary.** Capture, Whisper, punctuation, and rewrite stages stay on their low-latency path. The final `desktop.type_text`, paired delivery, or `process.input` is submitted with the held-key/direct-gesture authority and linked to the existing dictation journal. Do not journal audio frames.
6. **Let Phase 105 consume, not define, the kernel.** The drop matrix and verb registry are userland dispatch. Note→Recipe submits `inference.run`; Note→KB submits a proposal; filing a Zone uses the existing reversible membership update; groundable→orb is UI context only. Menu, Command-K, and wire invoke the same userland verb handler, and only consequential handlers cross the kernel.

During all six steps, old routes and tables remain; adapters dual-link by operation/correlation ID. Move reads only after generated consumer parity. A transactional outbox can feed the journal from existing repositories. Do not dual-execute or maintain two policy decisions.

## 4. SDLC, tech-lead, architect, and CTO work is userland

Useful programs on these calls include:

- **Delivery orchestration:** bind Story→Work attempt, create a worktree, launch Codex/Claude, watch the process, send a bounded instruction, reconcile output, run the `dw` gate, and collect evidence. Phase 94 is already the first such program.
- **Review and release:** resolve exact commit/PR/Story/evidence refs, run reviewer processes, retain findings as Artifacts, propose GitHub comments/status changes, and cut a release only through receipted external operations.
- **Architecture and decisions:** turn meeting/Ask material into an ADR using the existing `adr_drafter` and decision plugins; preserve source revisions and lineage; propose repository publication and stakeholder announcement separately.
- **Tech-lead operating loops:** triage waiting agents, failed CI, missing evidence, risks, dependencies, and stale attempts; delegate scoped follow-ups; draft a status update. Cadence and Attention become inputs, not a second scheduler kernel.
- **Portfolio views:** project Projects, decisions, risks, delivery freshness, costs/placement, and outstanding authority across sources. This is primarily `read + events`, with no special executive syscall.

For these programs to be trustworthy, the kernel must guarantee stable opaque identity, canonical ref resolution, immutable target/payload binding, authenticated principals, least authority, typed refusal, idempotency and explicit uncertainty, replayable process/events state, source revision and lineage, honest node/model/egress placement, privacy-aware retention, and a Receipt for every attempted consequence. It must not guarantee that a review rubric is wise, an LLM is correct, or a roadmap priority is good; those are userland judgments.

## 5. What not to abstract, and the three largest risks

Do not route pointer motion, selection, icon state, window placement, Info rendering, menu composition, or drop physics through the kernel. Do not put audio frames, transcription windows, or token streaming on the journal. Do not replace Notes, Meetings, Artifacts, Delivery Workbench Markdown, git, tmux, provider SDKs, or their state machines with generic “resources.” Do not make ordinary reversible local edits pay remote-command ceremony merely for architectural purity. The rule should be: use the kernel when work crosses a principal, process, machine, model/egress boundary, or consequential-effect boundary.

The top risks are:

1. **A God envelope and registry.** Feature-specific branches and arbitrary payloads would recreate `WebRuntime` as a more dangerous monolith. Require typed operation modules, tiny broker code, density guards, and at least two real drivers before generalizing a field.
2. **False authority through a shared interface.** Loopback owner trust, agent-supplied identity, dynamic operation registration, or YOLO interpreted as capability would make the kernel a privilege amplifier. Principal separation and human-only decision rights must land before agent tool access.
3. **Migration creates double truth and a central bottleneck.** Duplicate receipts, competing state machines, or synchronous journaling on typing/drag paths could make the product less honest and less responsive. Keep domain tables authoritative, correlate rather than copy, use an outbox, preserve executor-local ledgers, and migrate one side-effect census at a time.

My skepticism criterion is simple: if the first three drivers—terminal input, actuator egress, and inference runs—cannot share admission, principal, journal, and Receipt code without driver-specific conditionals in the broker, stop calling it a kernel. The durable idea is the invariant spine, not the name.
