# Evidence — HSM-7-03 — Profile-selection seam

- **Shipped:** 2026-06-19 · **Branch:** `holdspeak-mobile/phase-7-mir-port`

## What
The routing profile rides on the Phase-0 contract field `Meeting.mirProfile` (no
side-table, no contract fork). A RuntimeCore helper `Meeting.routingProfile` reads
it, defaulting to `.balanced` when unset; `RoutedArtifactGenerator.generate(from:for:)`
uses it. A host UI reads/writes `mirProfile` without touching engine internals.

## Verification
`testProfileSeamRoundTripsOnMeeting` — a `Meeting` with `mirProfile = .architect`
round-trips through the contract coder (`mirProfile` + `routingProfile` == `.architect`);
`nil` → `routingProfile == .balanced`. `swift test` 69 / 6 skipped / 0 failures.

## Note
v1 is one profile per meeting; per-window override (MIR-F-007) is parked (Decisions deferred).
