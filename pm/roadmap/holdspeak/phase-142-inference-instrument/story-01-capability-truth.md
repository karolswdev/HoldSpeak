# HSEGHS001HS104-142-01 - Capability Truth

- **Project:** holdspeak
- **Phase:** 142
- **Status:** done
- **Depends on:** none
- **Unblocks:** (optional)
- **Owner:** HoldSpeak orchestration

## Problem

Models and Thought Workbench currently receive a mixture of server facts,
browser-owned presets, Config fields, filename/path guesses, and runtime-specific
readiness. That ambiguity already produced a broken local selection and an
opaque setup experience. Before HoldSpeak downloads or executes another model,
one application projection must say what this hub can actually do without
loading a model, changing authority, or leaking paths/secrets.

## Scope

- **In:** `InferenceSetupApplicationService.get_inference_setup`; stable and
  volatile hardware facts; pure runtime/artifact inspection; packaged verified
  local/hosted preset metadata; Config route and v1 Thought deployment truth;
  owner-only HTTP/MCP resource parity; Models projection client/composition;
  focused unit/integration/browser/glass evidence; API/MCP inventory updates.
- **Out:** any download/acquisition command, artifact installation, deployment
  or route mutation, model load/probe/benchmark, MLX Thought inference,
  recommendation or measured-memory claims, exact context planning, tool calls,
  per-Thought destination switching, provider secret exposure, or schema-v2
  execution migration.

## Acceptance criteria

- [x] A closed versioned setup DTO contains `schema_version`, `observed_at`,
  hardware capability/observation/detection, runtimes, current Config routes,
  current Thought target and immutable v1 deployment/readiness, detected local
  artifact safe facts/support states, applicable verified presets, and named
  limitations/repairs.
- [x] The first and repeated projection perform zero SQLite/Config writes,
  network/catalog/provider calls, inference admissions, model loads, probes, or
  benchmarks.
- [x] Hardware/runtime/artifact inspectors return nullable named reasons on
  unsupported/missing/unknown states and expose no environment value or
  absolute path.
- [x] Packaged preset entries are recursively validated, immutable, and filtered
  by proven platform/runtime applicability; unverified/mutable candidates are
  absent. Zero applicable presets is valid.
- [x] `GET /api/inference/setup` and `holdspeak://inference/setup` call the same
  application method and expose identical inner data; OWNER is required and
  MODEL_TURN/AGENT cannot discover the resource.
- [x] Existing profile/Config mutation endpoints, v1 revision hashes, Ask path,
  local GGUF execution, and hosted preset creation remain compatible.
- [x] Models removes browser authority for projected facts and uses one labelled
  selection group plus one fixed action seat without Download/Recommended/Ready
  promises not present in the projection.
- [x] At 393 all controls are at least 44 px, no horizontal overflow exists,
  and keyboard/focus order remains stable; 1440 and 393 captures cover the
  ruled setup states.
- [x] Public/API/MCP/DOM/log fixtures contain no secret, absolute model path, or
  unverified native-context/memory/quality claim.

## Test plan

- **Unit:** DTO closure, packaged catalog validation/filtering, pure inspectors,
  zero-write/load/network census, Config/v1 projection truth, missing/unsupported
  reasons, secret/path redaction, legacy mutation/revision compatibility.
- **Integration:** reciprocal HTTP/MCP golden fixtures, owner denial and model
  resource absence, API/MCP inventory, restart-stable facts, event-loss GET
  recovery.
- **Manual / device:** isolated HOME/database at 1440x900 and 393x900 for no
  model, valid GGUF, missing path/dependency, unsupported detected MLX, and
  0/1/2/3 applicable presets; no console errors or network/model activity.

## Notes / open questions

The canonical design is
[`proposals/inference-instrument.md`](../proposals/inference-instrument.md),
with concrete candidate/scaling policy in
[`proposals/inference-catalog-and-context-policy.md`](../proposals/inference-catalog-and-context-policy.md).
Capability Truth deliberately exposes candidates as informational or absent;
it cannot offer a disabled/fake future action.
