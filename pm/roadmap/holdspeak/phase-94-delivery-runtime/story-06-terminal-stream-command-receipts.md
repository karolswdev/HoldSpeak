# HS-94-06 — Terminal stream and idempotent command receipts

- **Project:** holdspeak
- **Phase:** 94
- **Status:** done
- **Depends on:** HS-94-03, HS-94-04, Phase 93 shared operation policy
- **Unblocks:** HS-94-07, HS-94-08, HS-94-09

## Problem

The current pullout polls 200 ANSI-stripped lines every 1.5 seconds. Remote
input is a one-shot HTTP request with no command identity, ordering, or
deduplication. A dropped response can leave the owner unable to know whether
text landed and a retry can duplicate it. Node and pane are also separate
client state.

## Scope

- In:
  - immutable node-issued terminal target and generation;
  - shared node-side output subscription with initial snapshot and sequenced
    ANSI-preserving deltas;
  - hash-gated snapshot fallback;
  - bounded replay ring, resync, backpressure, and hub fan-out;
  - typed command envelope for text, keys, disarm, and terminal lifecycle
    effects used in this story;
  - command ID, expiry, target generation, expected sequence, payload hash;
  - per-target serialization and node deduplication ledger;
  - shared operation-policy decision envelope;
  - node audit plus durable aggregate hub Receipt;
  - `unknown`/reconcile behavior after lost response;
  - migration adapters over `coder_steering` and `coder_factory`.
- Out:
  - raw terminal input WebSocket;
  - arbitrary keys outside the existing named/literal contract;
  - full terminal transcript persistence;
  - remote agent launch (HS-94-07);
  - replacing tmux.

## Acceptance criteria

Rescoped 2026-07-16 by direct owner decision (the standing close directive):
the tailnet output-latency budget (p95 <750ms over real Tailscale) moves
verbatim to [BACKLOG candidate Y](../BACKLOG.md); every behavioral and
safety criterion is machine-verified here, including on real local tmux.


- [x] Two clients watching one target cause one node capture/stream and see
      ordered output; a slow client cannot stall the pane or other client.
- [x] Disconnect/resume replays from sequence or returns `resync_required` and a
      new snapshot without fabricated output.
- [x] Every command names immutable node/target/generation and cannot be
      redirected by changing a UI node selector.
- [x] Duplicate command envelopes apply at most once and return the same Receipt.
- [x] Lost connection before receipt reconciles by command ID; the UI never
      offers a blind retry for a possibly applied command.
- [x] Out-of-order expected sequence refuses without typing.
- [x] Recycled pane generation refuses, revokes applicable grant, and types
      nothing.
- [x] Secure/Normal/YOLO use the same Phase 93 decision and preserve auth,
      target, payload, configuration, schema, and audit invariants.
- [x] Node and hub Receipt halves join and are browseable from the attempt.
- [x] Existing local steering/factory live tests remain green through adapters.

## Test plan

- stream sequence/ring/gap/backpressure/multi-viewer;
- ANSI/TUI output and snapshot fallback;
- duplicate, timeout-before-send, lost-response-after-send, reconcile;
- parallel/out-of-order commands;
- pane recycle/node restart/grant expiry;
- policy-mode fixture parity across Python/TypeScript/Swift;
- real tailnet latency measurement;
- audit/Receipt completeness census.

## Implementation direction

- Reuse `coder_steering.deliver`/`deliver_keys` and factory executors; pass a
  resolved immutable target rather than resolving from mutable client state.
- Store the minimal deduplication result before acknowledging success. Define
  retention long enough to cover client reconciliation and node reconnect.
- A node reset that loses an uncertain result returns
  `indeterminate_after_node_reset`; it never executes the old envelope again.
- Terminal output is ephemeral; Receipts retain hash/head under the existing
  privacy limit.
- Keep stream and command channels logically separate even if they share one
  node WebSocket.

## Evidence required

- actual ANSI/TUI window on desktop and compact Web;
- sequence/backpressure metrics;
- lost-response trace proving one effect;
- duplicate/out-of-order/recycled-pane refusal ledger;
- joined node+hub Receipts;
- policy-mode invariant matrix.
