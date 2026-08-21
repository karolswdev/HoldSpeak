# Phase 142 - The Inference Instrument

**Last updated:** 2026-08-21.

## Goal

Make AI capability, runtime, artifact, route, and readiness truth server-owned before adding acquisition or new execution paths.

## Scope

- **In:** the read-only Capability Truth slice ruled by
  [`proposals/inference-instrument.md`](../proposals/inference-instrument.md):
  one server-owned setup projection; bounded hardware/runtime/artifact
  inspection; packaged verified preset metadata; current Config route and v1
  Thought-deployment truth; owner-only HTTP/MCP parity; and Models consuming
  those facts with one selected choice/action seat.
- **Out:** downloads, activation, route migration, MLX Thought execution,
  recommendation labels, calibration, exact token admission, tool execution,
  Workbench destination overrides, or any new inference path.

## Exit criteria (evidence required)

- [x] `get_inference_setup()` is the sole transport-neutral authority and its
  first read performs zero writes, loads, provider calls, downloads, or probes.
- [x] HTTP `GET /api/inference/setup` and MCP
  `holdspeak://inference/setup` expose the same recursively closed owner-only
  inner DTO with no secret or absolute locator.
- [x] Current Config routes, v1 deployment revision/readiness, runtime support,
  and detected artifact state are truthful; MLX is named unsupported for
  Thoughts until its later slice.
- [x] Only packaged, verified, platform-applicable preset metadata projects;
  Capability Truth never calls it Recommended/Ready from estimates and never
  exposes a fake download action.
- [x] Models consumes the projection, keeps existing mutation behavior, and
  proves one radiogroup/action-seat grammar at 1440 and 393.
- [x] Isolated cold walks cover configured GGUF, missing dependency/path, no
  model, detected unsupported MLX, restart, and 0/1/2/3 preset projection truth.

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSEGHS001HS104-142-01 | Capability Truth | done | [story-01-capability-truth](./story-01-capability-truth.md) | [evidence-story-01](./evidence-story-01.md) |
| HSEGHS001HS104-142-02 | Artifact Acquisition and Activation | backlog | [story-02-artifact-acquisition-and-activation](./story-02-artifact-acquisition-and-activation.md) | - |

## Where we are

Story 01 has delivered the complete read-only Capability Truth slice. The later
executable Inference Instrument slices remain held behind their ruled authority
prerequisites.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Inspection accidentally loads or mutates runtime state | high | pure inspectors, write/load/provider spies, zero-write census | any setup GET changes state or touches an inference leaf |
| Browser remains a competing preset/readiness authority | high | one closed server DTO and delete/move browser constants | UI invents a model, context, readiness, or hardware fact |
| Current v1 execution proof regresses | high | byte-identical revision/hash and one-path regression suites | a historical/current v1 route dispatch changes |
| Unsupported candidate looks executable | medium | closed support states and no fake action | MLX/Gemma/catalog candidate projects Ready/Download |

## Decisions made (this phase)

- 2026-08-21 - Phase scaffolded with `dw phase create` - keeps roadmap structure consistent - CLI.
- 2026-08-21 - Capability Truth is the only first delivery - creates truthful
  setup authority without broadening inference execution - owner-ratified
  Inference Instrument design.

## Decisions deferred

- Acquisition/activation and the minimal local-execution lease - trigger after
  Capability Truth closes - remains Slice 2.
- MLX Thought execution - trigger after the shared runtime seam and lease -
  remains Slice 3.
- Context recommendation/admission and tool capability foundation - trigger
  only in their ruled later slices.
