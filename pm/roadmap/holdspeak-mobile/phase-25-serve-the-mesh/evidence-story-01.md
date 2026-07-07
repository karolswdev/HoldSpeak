# Evidence — HSM-25-01 — The Swift relay worker on the provider seam

- **Shipped:** 2026-07-07
- **Commit:** branch `hsm-25-01-swift-relay-worker` (PR to `main`)
- **Owner:** Claude (Fable 5 session)

## Files touched

- `apple/Sources/Providers/Desktop/HTTPDesktopClient+MeshServe.swift` — new
  extension file (the conflict rule): `MeshRelayJob` (tolerant snake_case
  decode; timestamps stay ISO strings) + the three wire calls —
  `claimMeshRelay(node:)` (POST `/api/mesh/relay/claim`, the liveness-
  stamping poll, `{job: null}` ⇒ nil), `completeMeshRelay(jobID:result:)`,
  `failMeshRelay(jobID:error:)`. Bearer discipline identical to the
  existing client; a late completion surfaces as `.http(409)`.
- `apple/Sources/Providers/Desktop/MeshServeWorker.swift` — the loop, the
  Python worker translated onto the actor model: claim → execute on THIS
  device's provider (built lazily via the injected factory, reused) → post
  the outcome verbatim → claim again immediately while work exists; idle
  sleeps jittered ~3s (polling IS liveness); hub outages back off 1s→30s
  and reset on success; cancellation honored between polls so an in-flight
  job always finishes. `MeshServeRefusal` carries the recursion guard's
  named reason (thrown by the 25-02 app-side factory); an empty provider
  answer fails by name instead of dangling to the deadline (the hub
  refuses empty results). `Stats` (jobs served / last outcome) feeds the
  25-02 serving surface.
- `apple/Tests/ProvidersTests/MeshServeWorkerTests.swift` — new, 7 tests,
  URLProtocol-stubbed with a request-scripted stub (one path can answer
  differently per call) and an injected sleep recorder that cancels the
  loop deterministically — no test ever waits.

The fold is the recorded v1 limit: `ILLMProvider.complete(prompt:)` takes
one string, so system + user ride folded; the job's temperature/max_tokens
are decoded and carried but unexpressed until the seam grows.

## Verification artifacts

- `swift test --filter MeshServeWorkerTests` → **7 passed, 0 failures**:
  - claim→execute→complete verbatim (result byte-equal; the claim body
    names the node; the token asserted as `Bearer s3cret`);
  - provider throw → fail verbatim;
  - the recursion guard's named refusal posted verbatim;
  - empty answer → named fail, never a dangle;
  - hub outage → backoff exactly `[1.0, 2.0, 4.0]`;
  - idle cadence within `[2.4, 3.6]`s and nothing posted;
  - late completion (409) logged once, never retried, not counted served.
- Full `swift test` → **500 tests, 0 failures, 9 skipped** (standing
  env-gated skips).

## Acceptance criteria — re-checked

- [x] Claim/execute/report loop against a stubbed hub, outcomes verbatim.
- [x] Backoff without crash; recovery resets.
- [x] Cancel stops cleanly (the sleep-recorder cancel path IS the test
  harness — every test ends by cancellation).
- [x] Recursion guard refuses by name.
- [x] Bearer token rides the header and appears in no label.

## Deviations from plan

- None of scope; one addition — the empty-answer named failure (found
  writing the tests: the hub's complete route refuses an empty result, so
  without it a blank answer would dangle the job to its deadline).

## Follow-ups

- HSM-25-02 wires the app-side provider factory (the Phase-24 resolution +
  the at-the-door guard) and the consent toggle that owns this worker's
  lifecycle.
