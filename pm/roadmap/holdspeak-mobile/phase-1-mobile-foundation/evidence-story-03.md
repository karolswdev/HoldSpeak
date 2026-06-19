# Evidence — HSM-1-03 — CI pipeline

- **Shipped:** 2026-06-18
- **Commit:** Phase-1 close bundle on `main` (see commit message)
- **Owner:** unassigned

## Files touched

- `.github/workflows/holdspeak-mobile-ci.yml` — a `swift` job (macOS runner: the
  layer grep-guard + `swift build` + `swift test`) and a `contracts` job (ubuntu:
  the Python validator over the golden fixtures). Path-scoped to `apple/**` +
  `contracts/**` so it never gates the Python repo.

## Verification artifacts

**Green on a real hosted run** — GitHub Actions run `27801601150` (push
`ddb6788..a4e0722` on `main`), watched to completion via `gh run watch
--exit-status` (exit 0):

```
✓ Swift package (build + test + layer guard) in 31s
  ✓ Layer rule — core layers import no UI
  ✓ Build
  ✓ Test (round-trips the Phase-0 fixtures)
✓ Contract schemas (Python validator) in 27s
  ✓ Validate schemas against the golden fixtures
```

Run: https://github.com/karolswdev/HoldSpeak/actions/runs/27801601150

## Acceptance criteria — re-checked

- [x] CI builds + runs the test suite green on a real hosted run — run
  27801601150, both jobs ✓, exit 0.
- [x] The layer rule is enforced as a CI step (the grep-guard job step passed).
- [x] The contract validator runs in CI (the `contracts` job passed).

## Deviations from plan

- The story title says "iPhone + iPad sim"; `swift test` runs on the macOS host
  (the round-trip tests are platform-agnostic Foundation code, a valid proxy).
  Sim-destination `xcodebuild test` is a noted optional enhancement; the device
  launch itself is proven by HSM-1-04's Gate-1 simulator run.
- Minor: a GitHub annotation flags Node.js 20 deprecation for `actions/checkout@v4`
  (informational; auto-forced to Node 24). No action needed now.

## Follow-ups

Optional: add `xcodebuild -destination 'platform=iOS Simulator'` test runs; bump
the checkout action when v5 is standard.
