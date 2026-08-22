# Phase 142 - The Inference Instrument

**Last updated:** 2026-08-21.

## Goal

Make AI capability, runtime, artifact, route, readiness, acquisition, and local
activation truth server-owned without adding a second inference path.

## Scope

- **In:** the Capability Truth and Artifact Acquisition slices ruled by
  [`proposals/inference-instrument.md`](../proposals/inference-instrument.md):
  one server-owned setup projection; bounded hardware/runtime/artifact
  inspection; packaged verified preset metadata; durable verified GGUF
  acquisition; content-addressed adoption; immutable v2 deployment capture;
  narrow Thoughts-route activation; a minimal local runtime lease; owner-only
  HTTP/MCP parity; and Models consuming those facts with one action seat.
- **Out:** MLX Thought execution, capacity-aware resource sharing,
  recommendation labels, calibration, exact token admission, tool execution,
  Workbench destination overrides, or any inference path outside the existing
  InferenceRunner.

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
| HSEGHS001HS104-142-02 | Artifact Acquisition and Activation | done | [story-02-artifact-acquisition-and-activation](./story-02-artifact-acquisition-and-activation.md) | [evidence-story-02](./evidence-story-02.md) |
| HSEGHS001HS104-142-03 | One Model Chooser | done | [story-03-one-model-chooser](./story-03-one-model-chooser.md) | [evidence-story-03](./evidence-story-03.md) |
| HSEGHS001HS104-142-04 | Hammer Evaluation Candidate | done | [story-04-hammer-evaluation-candidate](./story-04-hammer-evaluation-candidate.md) | [evidence-story-04](./evidence-story-04.md) |
| HSEGHS001HS104-142-05 | Model Setup Wizard | done | [story-05-model-setup-wizard](./story-05-model-setup-wizard.md) | [evidence-story-05](./evidence-story-05.md) |
| HSEGHS001HS104-142-06 | Task-First Model Picker | done | [story-06-task-first-model-picker](./story-06-task-first-model-picker.md) | [evidence-story-06](./evidence-story-06.md) |

## Where we are

Stories 01–06 have delivered truthful setup, verified local GGUF acquisition,
an honest evaluation-only Hammer candidate, and a compact task-first model
picker that puts choices and the sole action in the first useful viewport.
The later MLX, capacity, exact-context, and tool-turn slices remain held behind
their ruled authority prerequisites.

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

- MLX Thought execution - trigger after the shared runtime seam and lease -
  remains Slice 3.
- Context recommendation/admission and tool capability foundation - trigger
  only in their ruled later slices.
