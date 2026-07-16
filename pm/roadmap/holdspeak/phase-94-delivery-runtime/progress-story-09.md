# HS-94-09 progress record — Native parity and tailnet HTTPS onboarding

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped machine-verifiable scope;
the physical iPad, tailnet-HTTPS onboarding, and the full native
terminal/factory parity UI are BACKLOG candidate Y.

## What shipped

- `apple/Sources/Contracts/DeliveryRuntime.swift`: Codable v2 models for the
  snapshot, sources, nodes, work attempts, story/phase dossiers, captured
  runs, and the typed refusal envelope, with six tolerant vocabularies
  (unknown enum raw values decode to a carrying case, unknown fields
  ignored, round-trip byte-honest) — the additive-tolerance contract is
  binding and test-pinned.
- Eight golden fixtures under `apple/Tests/ContractsTests/Fixtures/` derived
  from the REAL hub emitters (read_model, collector, node_link.nodes_view,
  attempts.to_wire, dossiers), each mirroring Python-test-asserted values and
  carrying extra/unknown fields to pin tolerance; a hygiene sweep asserts no
  fixture string is a filesystem path.
- `apple/Sources/Providers/Desktop/HTTPDesktopClient+Delivery.swift`:
  snapshot/sources/nodes/attempts/story-dossier clients following the
  existing extension patterns, surfacing the typed refusal envelope.
- The remote-disarm bug fix: `disarmCoder(key:node:)` now routes through the
  same relay helper as the other steering verbs, so a disarm against a noded
  session hits the node-routed path (a remote-armed grant no longer survives
  a native disarm). Regression tests lock both the relay and local routes.

## Verification

`swift test --package-path apple` — 556 cases, 0 failures, 9 skipped
(captured at close in [evidence-story-09](./evidence-story-09.md)). New
suites: DeliveryRuntimeTests 10, DeliveryClientTests 8, SteeringClientTests
+2 disarm regressions.

## Candidate-Y residue

The physical iPad app + iPad Safari over tailnet-HTTPS (Tailscale Serve,
secure-context microphone), the live readiness walk across transport
failure modes, the token-custody screenshot audit, and the full native
observe/evidence/terminal-stream/factory parity UI that consumes these
contracts.
