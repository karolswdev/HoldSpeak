# Phase 94 agent brief — The Delivery Runtime

## Status of this brief

This is an exploratory, implementation-ready draft. Phase 94 is not activated
on the project index and does not move the Phase 91 pointer. Phase 93 is being
authored in another worktree. Rebase this phase onto that work, reconcile its
final Desk and operation-policy contracts, schedule the Delivery Workbench
counterpart, and obtain owner acceptance before implementation.

## Owner intent

Delivery work should feel native to HoldSpeak:

- see what every local or remote agent is doing;
- know the machine, worktree, Story, and current need;
- open the real agent terminal from the Desk;
- dictate a precise instruction from the workstation, an iPad, or a remote
  browser over Tailscale;
- browse the proof attached to each completed Story and Phase;
- start, steer, recover, and end work without losing target identity or audit.

The goal is not another mission-control screen. It is a platform primitive that
makes delivery work inhabit the Desk's Projects, Stories, Coder sessions,
Evidence, Receipts, Attention, nodes, and authority grammar.

## Read first

1. [INTEGRATION-OVERVIEW.md](./INTEGRATION-OVERVIEW.md) — current system,
   verified gaps, and target architecture.
2. [PLATFORM-CONTRACT.md](./PLATFORM-CONTRACT.md) — normative identities,
   protocols, invariants, and proof obligations.
3. Phase 93's final agent brief, control-posture contract, copy contract, and
   Desk affordance grammar after that work lands.
4. Delivery Workbench `docs/mission-control.md` and the accepted WLA counterpart
   contract.
5. HoldSpeak Phases 82 and 86–90 final summaries. Preserve their safety and
   honesty decisions unless this phase explicitly supersedes one.

## The thesis

The existing implementation joined features by UI:

- the belt polls local `dw`;
- Delivery Workbench correlates the HoldSpeak registry;
- the terminal pullout opens a local session key;
- a separate node selector redirects some verbs;
- evidence opens one Markdown path;
- local and remote audits live in different places.

Phase 94 joins the underlying identities instead:

```text
Project/Story
  -> Work attempt
  -> node + source + worktree
  -> agent session
  -> terminal target generation
  -> evidence and execution Receipts
```

Once that graph is true, the belt, board, Project inspector, terminal window,
evidence dossier, native Desk, and attention layer become views of the same
records.

## What must be preserved

- Delivery Workbench is rail truth. HoldSpeak does not parse roadmap state.
- Markdown remains Delivery Workbench's source of truth.
- The `dw` gate keeps final say over rail mutations.
- Watching a terminal is read-only.
- Terminal effects use one typed executor and re-verify target generation.
- The executing node owns pane truth and its audit.
- The hub authenticates the person/device and owns the policy decision.
- Grants fail closed across node restart unless Phase 93 deliberately replaces
  the interruption with an eligible shared policy decision.
- Secure/Normal/YOLO never weaken authentication, secret custody, target
  identity, payload/destination binding, schema checks, or Receipts.
- No client invents success when a source/node/asset is absent.
- Native and Web use the same contracts and reason codes.
- The Desk stays the primary operating environment; no new dashboard shell.

## The verified starting defects

Before touching UI, reproduce and lock these:

1. a linked worktree emits no Delivery Workbench event because `.git` is a
   file;
2. HoldSpeak refuses evidence from Delivery Workbench's self-hosted
   `pmo-roadmap/pm/roadmap` layout;
3. the real session feed produces only `ambiguous`/`off_rails` associations;
4. remote pane discovery is absent;
5. Web target node and pane key are independent mutable fields;
6. terminal relay has no idempotency/ordering receipt;
7. remote audit is not available at the hub;
8. remote factory/agent launch is absent;
9. the remote rail-events worker is absent;
10. native remote disarm calls the local route.

Each becomes a fixture or regression test in the story that owns the repair.

## Ownership

| Concern | Owner |
|---|---|
| roadmap/status/evidence pairing/event privacy | Delivery Workbench counterpart |
| source/worktree Git metadata | node delivery provider |
| source registry and coherent read model | HoldSpeak hub |
| agent hook ingestion | node-local `agent_context` |
| explicit Story association | HoldSpeak Work attempt service |
| node pairing/link/liveness | HoldSpeak node runtime |
| pane generation and terminal execution | node-local steering/factory |
| human authentication and policy decision | HoldSpeak hub |
| local execution audit | node |
| aggregate requested+executed Receipt | hub projection |
| Project/Story/Session/Evidence experience | shared Desk object/view layer |

Stop if a story creates another owner for any row.

## Story sequence

### 1. Contract and worktree truth

Land the Delivery Workbench counterpart and shared fixtures first. The phase
cannot build a robust transport over path and event contracts known to be
wrong in worktrees and self-hosted layouts.

### 2. Sources and read model

Replace per-client subprocess polling with a hub collector over versioned local
providers. Migrate the current map through an adapter. Prove one coherent
snapshot and client-count-independent subprocess rate.

### 3. Node link

Add an outbound authenticated node runtime with capability discovery, cursors,
liveness, reconnect, and an embedded local adapter. Observation only at first;
no terminal effects until its link and identity are stable.

### 4. Work attempts

Bind Story, worktree, session, and terminal explicitly. Keep repo-wide
correlation only as labeled fallback. Move manual pins out of browser storage.

### 5. Evidence dossiers

Transport the Delivery Workbench manifest and assets. Render current and
historical Story/Phase proof on the Desk before adding more control.

### 6. Terminal stream and command receipts

Make the actual window responsive and terminal effects retry-correct. Reuse the
existing executors; do not build a raw input WebSocket.

### 7. Remote factory and launch

Only after command correctness: discover remote panes, spawn/rename/kill on the
node, and launch configured Claude/Codex profiles into an exact Story/worktree.

### 8. Web Desk product expression

Replace the global conveyor-as-product with Project/Story/Session/Evidence
views using Phase 93's Desk grammar. Keep compatibility routes during parity.

### 9. Native and tailnet journey

Ship the same object and command contracts on native, prove remote disarm and
target identity, and make tailnet HTTPS readiness discoverable.

### 10. Break it and close

Two machines, multiple worktrees and agents, real evidence, lost responses,
node restarts, recycled panes, slow clients, policy modes, desktop Web, iPad
Web, and a physical iPad native walk.

## Implementation rules

- Add a focused `holdspeak/delivery/` package. Do not grow
  `missioncontrol_bridge.py` into the new monolith.
- Put typed wire models in a contract module with shared fixtures for Python,
  TypeScript, and Swift.
- Keep provider interfaces pure enough to run local and node fixtures without
  network or real tmux.
- Keep blocking CLI/git/gh work out of the event loop.
- Use `asyncio` tasks only under the server lifespan with bounded cancellation.
- Persist Work attempts, command states, node metadata, and aggregate Receipts.
  The derived source snapshot cache may remain rebuildable.
- Preserve last-known-good plus freshness on provider failure.
- All node/client inputs are size-capped and enum-validated.
- Every command is immutable after creation.
- Never pass agent launch through `sh -c` or accept an executable from a client.
- Never send arbitrary filesystem paths over node/client wires.
- Do not let Web `localStorage` become authority for source, Story association,
  target, grant, or command state.
- Generate the API surface and update SECURITY/ARCHITECTURE from actual code in
  the story that changes the boundary.

## UI rules

- Reuse Project, Story, Coder session, Evidence, Receipt, Attention, tool shelf,
  windows/pullouts, search, and inspector patterns from Phase 93.
- A machine selector is part of target discovery, not a global toggle that
  reinterprets an open pane.
- Every terminal header names node, worktree, Story, agent, and target state.
- A stale/offline object stays in place with last-seen and recovery.
- Evidence supports keyboard, touch, and compact width; no hover-only or
  drag-only path.
- Voice fills an instruction. Sending follows the shared policy decision and
  shows the exact destination.
- Consequential buttons use exact verbs and consequences.
- `unknown` command outcome is a first-class state with reconcile, never a
  generic retry.
- Product copy follows Phase 93's professional, task-first contract.

## Evidence discipline

Every story carries:

- focused unit/contract tests;
- a standard-layout and self-hosted/worktree fixture where relevant;
- Web production-root capture for user-facing work;
- actual Swift capture for native work;
- a real node/process leg for node stories;
- captured command output in the story evidence file;
- structured JSON of the walk/receipts where it improves auditability;
- failures and refusals, not only the happy path.

The phase close uses the platform it built: HS-94-10's own Work attempt,
terminal, commands, evidence dossier, gate, commit, PR, and CI appear through
the Delivery Runtime.

## Stop signals

Stop and redesign if:

- HoldSpeak parses status/evidence from Markdown;
- a client can combine a node name with an unrelated pane key;
- a possible terminal effect is automatically repeated;
- a node executes a browser-supplied shell string;
- remote execution has no node receipt;
- a last-known snapshot looks live;
- source refresh rate grows with the number of browser/iPad clients;
- a second policy/receipt/attention/node registry appears;
- Phase 94 adds a dashboard above the Desk;
- native uses different target or authority semantics;
- the WLA counterpart changes a consumed schema without a fixture/version.

## Handoff after the phase

The old mission-control and steering APIs may remain as documented compatibility
facades for one release. Their deletion is a later, measured cleanup after
generated consumer parity says Web, Swift, scripts, and UAT have moved.
