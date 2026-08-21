# Phase 142 — The Inference Instrument: final summary

**Closed:** 2026-08-21.
**Stories shipped:** 2 / 2.

## Goal — was it met?

**Yes.** HoldSpeak now owns one truthful setup and acquisition waist. Models can
show what is actually available, accept one explicit `Download & use` gesture,
resume and verify a bounded GGUF download, adopt it content-addressably, capture
a locator-free immutable deployment revision, and activate the Thoughts route
without bypassing the existing `InferenceRunner`.

## What shipped

- **Capability Truth:** one owner-only HTTP/MCP setup projection for hardware,
  runtimes, artifacts, routes, readiness, and a signed packaged catalog. Reads
  do not download, load a model, call a provider, or expose locators/secrets.
- **Artifact acquisition:** a durable idempotent saga for source resolution,
  disk preflight, HTTP Range resume, digest and GGUF verification,
  content-addressed install, cancellation, recovery, and narrow route CAS.
- **Execution continuity:** deployment-revision v2 freezes safe artifact,
  runtime, model, boundary, and context facts while resolving the local locator
  only on the owning hub. The existing runner remains the only physical dispatch
  waist and applies a minimal crash/cancel-safe local runtime lease.
- **Product surface:** Models uses one server projection, one radiogroup, and one
  fixed action seat at 1440 and 393. It shows byte progress and exact
  verification/install/activation truth without inventing readiness.

## Evidence

| Story | Evidence |
|---|---|
| Capability Truth | [evidence-story-01.md](./evidence-story-01.md) |
| Artifact Acquisition and Activation | [evidence-story-02.md](./evidence-story-02.md) |

Story 02's captured gates include 278 focused backend/schema/API/MCP tests,
30 focused Models tests plus a production build, and four isolated-HOME browser
walks. The acquisition walk uses a real bounded HTTP byte server at both widths
and proves progress, verification, install, route activation, v2 projection,
and locator privacy. Optional metal execution of the 2.7 GB catalog artifact was
not run in this environment and is not claimed.

## Handoff

The next slices can add MLX execution, capacity-aware resource vectors and
sharing, exact context admission, per-Thought destination choice, and the ruled
ToolTurn capability foundation. None should create a second dispatch waist or
weaken the explicit owner-intent, receipt, and policy boundaries established
here.
