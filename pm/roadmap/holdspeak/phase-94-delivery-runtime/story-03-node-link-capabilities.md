# HS-94-03 — Authenticated node link, capabilities, liveness, and reconnect

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-02
- **Unblocks:** HS-94-04, HS-94-05, HS-94-06

## Problem

The hub currently owns a JSON environment table of remote URLs/tokens and can
forward only known terminal keys. Remote sources, worktrees, sessions, panes,
evidence, and audits are not discovered. A remote rail-events receiver exists,
but no production worker sends it.

## Scope

- In:
  - outbound node-to-hub authenticated WebSocket;
  - per-node pairing secret, rotation, revoke, and protected storage;
  - node identity, instance identity, protocol/policy versions;
  - capability advertisement for sources, evidence, sessions, terminal,
    factory, launch, and inference;
  - heartbeat, stale/offline state, clock-skew signal;
  - ordered node event cursor, reconnect/resume, bounded backoff;
  - remote source/worktree/session/target discovery metadata;
  - remote Delivery Workbench rail-event collection;
  - remote audit receipt metadata;
  - embedded local-node adapter with the same interfaces;
  - legacy direct steering-node adapter labeled honestly.
- Out:
  - terminal effects and streaming;
  - remote factory/launch;
  - public discovery or public relay;
  - reusing the browser token as a node credential.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the second-physical-machine Tailscale leg (real transport latency, clock
skew across real hardware) moves verbatim to
[BACKLOG candidate Y](../BACKLOG.md); the two-process localhost proof and
injected-clock suites carry the behavioral contract.


- [x] A node initiates the connection; it needs no inbound general Web server
      reachable from the hub.
- [x] Browser, native, and node tokens are distinct; node token rotation and
      revoke take effect without repository edits.
- [x] Capability and required policy mismatch makes commands unavailable while
      compatible observation remains usable.
- [x] Heartbeat produces live → stale within 15 s → offline within 30 s; last
      source/session truth stays visible with last-seen.
- [x] Kill/restart/reconnect resumes event/audit cursors without duplicates or
      gaps; an unreplayable gap requests a source resync.
- [x] A remote linked worktree, rail change, and Coder waiting transition appear
      at the hub through the node link.
- [x] A remote event cannot smuggle body content outside the declared protocol.
- [x] Local and remote providers pass the same behavior contract suite.

## Test plan

- node handshake/auth/scope/version/capability tests;
- secret redaction and token rotation/revoke;
- fake-clock liveness and clock skew;
- reconnect with duplicate, missing, and out-of-order node events;
- server cancellation and bounded backoff;
- two-process live node on localhost;
- second physical machine over Tailscale;
- remote worktree rail event and session transition.

## Implementation direction

- Prefer `holdspeak node serve` as the explicit runtime. Reuse the mesh worker's
  configuration, liveness, and provider patterns; keep inference as one
  capability rather than forcing delivery messages into prompt/result jobs.
- Manage the node task under server/CLI lifespan and make shutdown deterministic.
- Node events carry metadata; terminal output/evidence bytes have separate
  bounded message types.
- Persist the node event cursor and recent execution receipt index before adding
  commands in HS-94-06.
- Never log authorization headers, pairing secrets, full node URLs with
  credentials, or raw environments.

## Evidence required

- pair/connect/revoke transcript with secrets redacted;
- liveness timeline;
- restart/resume event ledger;
- remote worktree/session capture;
- content-smuggling refusal;
- local/remote provider parity run.
