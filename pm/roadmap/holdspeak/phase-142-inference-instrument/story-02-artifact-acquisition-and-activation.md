# HSEGHS001HS104-142-02 - Artifact Acquisition and Activation

- **Project:** holdspeak
- **Phase:** 142
- **Status:** backlog
- **Depends on:** HSEGHS001HS104-142-01
- **Unblocks:** (optional)
- **Owner:** HoldSpeak orchestration

## Problem

Capability Truth can now describe verified local candidates without pretending
they are installed or executable. The next slice must turn an explicit owner
choice into a durable, resumable, verified artifact and activate its immutable
deployment revision without bypassing the existing inference runner.

## Scope

- **In:** the ruled acquisition saga, signed source-plan resolution, bounded and
  resumable download, digest/license/disk verification, content-addressed
  adoption, minimal crash-safe local execution lease, immutable deployment-v2
  capture, narrow route CAS, HTTP/MCP parity, and Models progress/recovery.
- **Out:** MLX execution, capacity-aware shared resource queues, exact context
  planning, tool turns, per-Thought destination overrides, or automatic model
  acquisition without an explicit owner gesture.

## Acceptance criteria

- [ ] One explicit `Download & use` command durably records intent before
  network activity and converges on one verified content-addressed artifact.
- [ ] Restart, cancellation, response loss, route conflict, integrity failure,
  and disk failure reconcile to named truth without duplicate download or
  false activation.
- [ ] Every newly activated local physical leaf is fenced by the minimal
  serialized crash/cancel-safe runtime lease and the existing InferenceRunner.
- [ ] HTTP, MCP, and Models consume the same application projection/receipts;
  no secret, locator, artifact bytes, or owner MCP authority reaches a model.
- [ ] Real 1440/393 walks prove one action seat, byte progress, navigation and
  restart persistence, verification/install boundaries, and exact recovery.

## Test plan

- **Unit:** acquisition state machine, source-plan trust, bounded downloader,
  manifest/digest verification, artifact ledger, narrow CAS, lease fencing.
- **Integration:** crash/replay matrix, HTTP/MCP parity, runner one-path census,
  Config/deployment compatibility, event-loss GET recovery.
- **Manual / device:** isolated artifact server and HOME at 1440/393; optional
  real GGUF execution gate on supported hardware.

## Notes / open questions

Canonical details live in
[`proposals/inference-instrument.md`](../proposals/inference-instrument.md).
This story remains backlog until Story 01 is merged and its projection contract
is the base of `main`.
