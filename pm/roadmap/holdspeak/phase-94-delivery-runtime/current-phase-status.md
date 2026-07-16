# Phase 94 — The Delivery Runtime

**Status:** IN PROGRESS (2/10). HS-94-02 is done: the delivery source registry, single-flight collector, and coherent delivery_schema:1 read model with poll economy and wire hygiene proven. HS-94-01 is done: the vendored dw implements the counterpart contract (capabilities, cursored events, evidence manifest/asset) and worktree/self-hosted truth, proven by 20 subprocess tests against real scratch repositories. Activated 2026-07-16 by the owner's standing
close directive after Phase 93 closed all nine stories; the current roadmap
pointer remains Phase 91.

**Last updated:** 2026-07-16 (activated; HS-94-01 implementation integrated).

## Activation record (2026-07-16)

- Phase 93's Desk object/affordance and shared authority contracts: frozen by
  the Phase 93 close (all nine stories done; desk-window grammar, workroom
  context, operation-policy v2 shipped).
- Delivery Workbench counterpart: implemented in this repo's vendored dw
  (capabilities, cursored events, evidence manifest/asset, worktree truth);
  upstream reusable-processes adoption is BACKLOG candidate Y scope.
- Owner acceptance of the phase boundary and sequence: the standing close
  directive (2026-07-16).
- Second real node / linked worktree / physical iPad: linked-worktree
  fixtures are real in-repo; the second node runs as a second local process
  with the physical machine and iPad legs preserved in candidate Y.
- This phase's branch is stacked on the Phase 93 close; the pointer does not
  move.

## Goal

Make Delivery Workbench-backed projects, Story progress, remote/local Coder
sessions, terminals, evidence, and receipts one robust HoldSpeak platform
primitive, so the owner can observe, review, start, and voice-steer delivery work
from the Desk on a workstation, an iPad, or a tailnet HTTPS Web view without
losing target identity, proof, authority, or outcome.

## Why this phase exists

Phases 82 and 86–90 proved the parts. The integration still assumes one mapped
local checkout, one local session registry, repo-wide story guessing, separate
remote terminal URLs, raw Markdown evidence, per-client polling, and local-only
execution audits. Those assumptions fail the intended multi-worktree,
multi-machine daily use.

The comprehensive audit and target are in
[INTEGRATION-OVERVIEW.md](./INTEGRATION-OVERVIEW.md). The normative protocol and
invariants are in [PLATFORM-CONTRACT.md](./PLATFORM-CONTRACT.md).

## Activation gates

- [x] Phase 93's final Desk object/affordance and shared authority contracts are
      available and reconciled into this phase.
- [x] Delivery Workbench Phase 17 is closed or its status/capability contract is
      frozen.
- [x] The Delivery Workbench counterpart phase is accepted and scheduled (implemented in the vendored dw; upstream adoption in candidate Y).
- [x] The owner accepts this phase boundary and ten-story sequence (standing close directive, 2026-07-16).
- [x] A second real node, a linked worktree, and physical iPad are reserved for
      continuous evidence.
- [x] This phase is rebased onto Phase 93 and added to the central project index
      without changing the current-phase pointer.

## Scope

### In

- Delivery Workbench worktree/event/evidence/capability counterpart;
- versioned Delivery Source and Worktree registry;
- coherent cached hub read model with event cursor;
- authenticated outbound node runtime and embedded local adapter;
- remote delivery sources, agent sessions, terminal targets, and audit receipts;
- explicit Work attempts joining Story/worktree/session/terminal;
- evidence dossiers and safe media/log browsing;
- resumable terminal output and snapshot fallback;
- idempotent, ordered, target-generation-checked command envelopes;
- remote pane discovery, factory, and configured agent launch;
- Project/Story/Session/Evidence expression through the Phase 93 Desk;
- Web and native parity for the north-star journeys;
- tailnet-only HTTPS readiness;
- multi-node chaos, security, performance, and owner proof.

### Out

- replacing Delivery Workbench's Markdown or gate;
- cloud relay or public Funnel exposure;
- arbitrary remote shell execution;
- a generic SSH/terminal product;
- replacing tmux;
- autonomous scheduling or prioritization;
- another dashboard/control center;
- another Project, policy, Receipt, Attention, or node model;
- retaining full terminal transcripts by default;
- broad GitHub project management.

## Exit criteria

- [ ] A shared counterpart fixture proves standard, self-hosted, and linked
      worktree layouts; rail events emit in worktrees; evidence manifests resolve
      every layout; schema/capability drift is typed.
- [ ] A versioned source registry discovers configured local worktrees and
      paired-node sources without exposing raw paths; one coherent snapshot has
      revision/freshness; client count does not increase `dw`/`gh` process rate.
- [ ] A remote node connects outbound, authenticates with a node-scoped secret,
      advertises capabilities, resumes its cursor after reconnect, and becomes
      stale/offline on the specified clock without invented absence.
- [ ] A launched or manually attached session has one exact Work attempt joining
      node, source, worktree, Story, agent session, and terminal; legacy
      correlation stays explicitly heuristic; the real HoldSpeak fixture no
      longer yields only ambiguous sessions.
- [ ] A completed Story and Phase open as evidence dossiers with rendered
      Markdown, captured runs, final summary, PNG, JSON, and text log plus
      commit/gate/PR/CI receipts where present; remote/offline bytes remain
      honestly listed.
- [ ] Web and native can watch a real ANSI/TUI agent window over the node link;
      lost response, duplicate envelope, out-of-order command, and recycled pane
      produce zero duplicate/wrong-target effects and complete Receipts.
- [ ] From the Desk, the owner can discover remote panes, create or choose a
      worktree, launch configured Claude/Codex work for a Story, rename/steer/end
      it, and recover a partial launch without arbitrary shell input.
- [ ] The Web Desk expresses delivery through Project, Story, Coder session,
      Evidence, Receipt, and Attention views at desktop and compact widths; past
      work and evidence are reachable without the current-phase belt.
- [ ] The physical iPad native app and iPad Web over tailnet HTTPS complete
      observe, evidence, voice-steer, and outcome-reconcile journeys with the
      same target/policy/reason contracts; remote disarm is verified.
- [ ] The two-node closeout passes the full fault matrix, latency/process
      budgets, security review, generated contract/API guards, and owner replay;
      HS-94-10's own work and evidence are visible through the platform.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HS-94-01 | Counterpart contract and worktree truth | done | [story-01-counterpart-contract-worktree-truth](./story-01-counterpart-contract-worktree-truth.md) | [evidence-story-01](./evidence-story-01.md) · [progress record](./progress-story-01.md) |
| HS-94-02 | Delivery Source registry and coherent read model | done | [story-02-source-registry-read-model](./story-02-source-registry-read-model.md) | [evidence-story-02](./evidence-story-02.md) · [progress record](./progress-story-02.md) |
| HS-94-03 | Authenticated node link, capabilities, liveness, reconnect | backlog | [story-03-node-link-capabilities](./story-03-node-link-capabilities.md) | - |
| HS-94-04 | Work attempts and exact Story/session/worktree correlation | backlog | [story-04-work-attempts-correlation](./story-04-work-attempts-correlation.md) | - |
| HS-94-05 | Evidence dossiers and safe asset browsing | backlog | [story-05-evidence-dossiers](./story-05-evidence-dossiers.md) | - |
| HS-94-06 | Terminal stream and idempotent command receipts | backlog | [story-06-terminal-stream-command-receipts](./story-06-terminal-stream-command-receipts.md) | - |
| HS-94-07 | Remote factory and Story-bound agent launch | backlog | [story-07-remote-factory-agent-launch](./story-07-remote-factory-agent-launch.md) | - |
| HS-94-08 | Delivery work inhabits the Web Desk | backlog | [story-08-web-desk-delivery-experience](./story-08-web-desk-delivery-experience.md) | - |
| HS-94-09 | Native parity and tailnet HTTPS onboarding | backlog | [story-09-native-tailnet-parity](./story-09-native-tailnet-parity.md) | - |
| HS-94-10 | Multi-node chaos/security/performance owner walk and close | backlog | [story-10-closeout-chaos-owner-walk](./story-10-closeout-chaos-owner-walk.md) | - |

## Where we are

The isolated audit is complete. No product code has changed. The review found
two directly reproduced cross-layout/worktree defects, unusable real-world
session correlation, incomplete remote discovery/factory/audit, target-identity
risks in client state, missing command deduplication, incomplete evidence
browsing, and polling that scales with client count.

This directory is a draft so Phase 94 can be evaluated without colliding with
Phase 93. Next is owner/maintainer review of the phase boundary and Delivery
Workbench counterpart, then rebase and formal activation.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Scope becomes a platform rewrite | high | adapters over existing `dw`, steering, factory, policy, and Desk primitives; story sequence | new universal entity/event store or wholesale route rewrite |
| Delivery Workbench and HoldSpeak drift | high | counterpart contract, capabilities, shared fixtures, independent schemas | private parser or unversioned required field |
| Remote command duplicates or targets wrong pane | high | immutable compound target, generation, sequence, idempotency ledger, unknown reconciliation | blind retry or node selector reinterprets key |
| Node transport weakens local safety | medium | node runs existing executors; shared policy; node owns verification/audit | raw input WebSocket or browser shell string |
| Evidence transport leaks repository data | medium | manifest-only assets, containment, MIME/size/hash/range, explicit fetch | arbitrary path endpoint or recursive repo send |
| New view violates Phase 93 Desk direction | medium | Project/Story/process/evidence views in existing grammar | new home/dashboard/control center |
| Polling/streaming harms the hub | medium | collector single-flight, fan-out, backpressure, budgets and metrics | subprocess rate grows with clients |
| Native becomes a second protocol | medium | shared fixtures and reason codes; same-story native acceptance | Swift-only policy/target matrix |
| Adjacent Phase 17/93 changes invalidate plan | medium | activation gate and rebase review | implementation before contracts freeze |

## Decisions made in this draft

- Delivery Workbench stays the rail/evidence authority.
- HoldSpeak gains a Delivery Runtime projection, not another source of truth.
- Worktree and Work attempt are first-class.
- Nodes connect outbound and advertise capabilities.
- Local is an embedded node adapter.
- Terminal output may stream; terminal input remains typed commands.
- Remote terminal commands require idempotency and outcome reconciliation.
- The node owns execution truth; the hub mirrors a joined Receipt.
- Evidence membership comes from Delivery Workbench.
- The Phase 93 Desk and authority grammar is consumed, never forked.
- Tailnet-only HTTPS plus HoldSpeak bearer auth is the canonical Web journey.

## Decisions deferred until activation

- final CLI name: `holdspeak node serve` versus extending `mesh serve`;
- exact node pairing UX and secret store;
- whether Work attempt metadata also emits a Delivery Workbench-local receipt;
- final terminal stream transport implementation;
- whether native ANSI streaming lands simultaneously or behind the same story's
  bounded parity milestone;
- compatibility-facade removal release.
