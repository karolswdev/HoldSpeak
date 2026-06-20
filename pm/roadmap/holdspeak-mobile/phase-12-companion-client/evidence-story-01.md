# Evidence — HSM-12-01 (Desktop client seam + pairing)

**Date:** 2026-06-20
**Story:** [story-01-desktop-client-seam.md](./story-01-desktop-client-seam.md)
**Result:** DONE — host-proven. The `IDesktopClient` seam + `HTTPDesktopClient`
(pairing → handshake against `/health` + `/api/runtime/status`, honest egress,
offline-tolerant) and the Runtime-Core `CompanionLink` consumer. `swift test`
**96 passed / 6 skipped / 0 failed** (was 84; +12 this story).

## What shipped

- **Layer 3 (Providers):** `IDesktopClient` (Providers.swift) — a non-throwing
  `handshake() async -> DesktopConnection` seam, so an unreachable desktop is a
  first-class state, never an error on the caller path. Concrete
  `HTTPDesktopClient` + `DesktopPeer` (host/port + token pairing) +
  `DesktopConnection` in `Providers/Desktop/HTTPDesktopClient.swift`. URLSession
  over the desktop's existing HTTP API; honest egress `local + LAN → <host>`; Bearer
  token joined at call time, never in the egress label; `/api/runtime/status`
  decoded loosely (every field optional) for robustness.
- **Layer 2 (RuntimeCore):** `CompanionLink` (RuntimeCore/Companion/) holds the
  `IDesktopClient` interface — the Runtime Core depends on the seam, not a transport
  — and is the thin entry point the verb stories (HSM-12-02 / HSM-13) extend.

## Acceptance criteria → proof

- **Seam exists; core depends on the interface; a fake drives it.** `CompanionLink`
  takes `IDesktopClient`; `CompanionLinkTests.FakeDesktop` drives the flow with no
  network. ✅
- **Configure a peer (host/port + token); handshake vs `/health` +
  `/api/runtime/status`; surface reachable/unreachable + readiness.**
  `DesktopPeer` → `Config`; `testHandshakeReachableAndRuntimeReady`,
  `testHandshakeReachableButRuntimeStatusUnavailable`,
  `testHandshakeSurfacesActiveMeeting`. ✅
- **Honest egress descriptor.** `testEgressLabelIsHonest` (`LAN` + host present),
  `testTokenRidesAsBearerAndIsNotInEgress` (token never in the label). ✅
- **Offline-tolerant: fails soft, no throw; on-device flow unaffected.**
  `testHandshakeUnreachableFailsSoft` (no `try`, returns `.offline`),
  `testHandshakeBadHealthStatusIsOffline`, and the core guarantee
  `CompanionLinkTests.testOnDeviceWorkUnaffectedWhenDesktopUnreachable`. ✅

## Commands + output

```
$ swift build
Build complete! (2.62s)

$ swift test --filter 'DesktopClientTests|CompanionLinkTests'
Test Suite 'CompanionLinkTests' passed   — Executed 3 tests, 0 failures
Test Suite 'DesktopClientTests' passed   — Executed 9 tests, 0 failures
Test Suite 'Selected tests' passed       — Executed 12 tests, 0 failures

$ swift test
Test Suite 'HoldSpeakMobilePackageTests.xctest' passed
Executed 96 tests, with 6 tests skipped and 0 failures (0 unexpected)
```

## Notes

- Fix during the run: `DesktopPeer.baseURL` now rejects an empty host / non-positive
  port (URLComponents otherwise built `http://:0`), so a half-filled pairing form
  stays offline instead of producing a junk client.
- The 6 skips are the pre-existing opt-in device/live tests (unchanged by this story).
- Device proof of the companion is the Track-M gate (HSM-12-04); this story is the
  fully host-testable spine and needs no hardware.
