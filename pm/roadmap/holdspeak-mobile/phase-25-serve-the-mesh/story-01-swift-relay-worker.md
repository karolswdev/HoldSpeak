# HSM-25-01 — The Swift relay worker on the provider seam

- **Status:** backlog
- **Depends on:** desktop phase-85 (shipped)
- **Unblocks:** HSM-25-02, HSM-25-03

## Problem

The hub's relay wire (claim / complete / fail, HS-85-01) has one worker
implementation: the Python `holdspeak mesh serve`. The devices need the
same loop in Swift, executing on the device's OWN provider through the
existing `ILLMProvider` seam — no new provider concepts, no key movement.

## The design

- `MeshRelayClient` (Sources/Providers/Desktop, beside
  `HTTPDesktopClient`): three calls mirroring the wire —
  `claim(node:) -> MeshRelayJob?`, `complete(jobID:result:)`,
  `fail(jobID:error:)`. Bearer token discipline identical to the existing
  client (never logged, never in a label). `MeshRelayJob` decodes
  `{id, node, task_kind, system_prompt, user_prompt, temperature,
  max_tokens, model_hint}` tolerantly.
- `MeshServeWorker` (the loop, translated from
  `holdspeak/commands/mesh_serve.py`): claim on a ~3s jittered cadence →
  execute → post the outcome verbatim → immediately claim again while
  work exists; hub outage backs off exponentially (1s→30s, reset on
  success) without dying; cancellation stops cleanly with the in-flight
  job finishing. Injectable client + provider factory + sleep for tests.
- **Execution folds onto the seam:** system + "\n\n" + user →
  `ILLMProvider.complete(prompt:)` (the provider protocol takes one
  string in v1; recorded limit — temperature/max_tokens ride the job but
  the seam cannot express them yet). A provider throw posts `fail` with
  the error text verbatim.
- **The recursion guard:** the worker's provider factory resolves the
  active profile the Phase-24 way; a `meshNode` or `desktop` active
  profile refuses to serve by name (`this device's profile runs
  elsewhere — serving needs an on-device model or an endpoint`) — the
  job fails honestly, mirroring the Python guard.
- One honest log line per claim/outcome (the walk's evidence shape).

## Scope

- In: `MeshRelayJob` + `MeshRelayClient` + `MeshServeWorker`; unit tests.
- Out: any UI (25-02), any background mode, protocol changes to
  `ILLMProvider`.

## Test plan

`swift test` (ProvidersTests, URLProtocol stubbing per
`DesktopClientTests.swift`):

- claim returns a job → provider runs → complete posts the result
  verbatim (body captured and asserted).
- provider throws → fail posts the error verbatim.
- hub unreachable → backoff sequence (1, 2, 4 …) via injected sleep; no
  crash; recovery resets.
- claim returns `{job: null}` → idle cadence, nothing posted.
- cancel mid-loop → loop exits; no further requests.
- recursion guard: a meshNode active profile → the job fails with the
  named reason; nothing executes.
- the token rides `Authorization: Bearer` (asserted via `lastAuth`).

## Done when

The worker round-trips a real job shape against the stubbed hub in tests,
with the guard, backoff, and verbatim outcomes proven. No UI yet.
