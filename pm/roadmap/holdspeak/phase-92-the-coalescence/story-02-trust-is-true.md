# HS-92-02 — Trust is true before it is easy

- **Project:** holdspeak
- **Phase:** 92
- **Status:** in-progress (pre-close implementation; physical-device trust walk pending)
- **Depends on:** HS-92-01
- **Unblocks:** HS-92-03, HS-92-04, HS-92-07, HS-92-08
- **Owner:** unassigned

## Problem

Convenience presets cannot safely ship over unresolved trust defects. The
general WebSocket is not authenticated off loopback, general settings reads
return raw configuration secrets, settings writes can reset top-level sections,
approval payload binding is optional, and the Apple pairing token is stored in
`AppStorage`. These are correctness defects, not adjustable friction.

## Scope

- **In:** WebSocket handshake auth; redacted settings view models and dedicated
  secret set/rotate/delete operations; section-safe config persistence;
  destination/operation registry used by setup/trust/doctor; mandatory approval
  binding to material payload, normalized destination, renderer and policy
  version; Apple pairing-token Keychain migration; Desk trust drawer showing
  named destinations and hard warnings.
- **Out:** Safe/Neutral/YOLO behavior changes; TLS productization; third-party
  pack sandboxing; coordinated deletion from external services.
- **Paths:** `holdspeak/web_auth.py`, `holdspeak/web_server.py`,
  `holdspeak/web/routes/system/ws.py`,
  `holdspeak/web/routes/system/settings.py`, `holdspeak/config.py`,
  `holdspeak/setup_status.py`, `holdspeak/plugins/actuator_executor.py`,
  `holdspeak/db/actuators.py`, `web/src/components/AppShell.tsx`,
  `apple/App/MeetingCapture/CompanionMesh.swift`,
  `apple/App/MeetingCapture/ProfileKeyStore.swift`, `docs/SECURITY.md`, and
  focused auth/settings/actuator/Keychain tests.

## Acceptance criteria

- [x] Loopback, valid-token, missing-token, and bad-token WebSocket handshakes
      follow the same off-loopback policy as HTTP; authenticated React and Swift
      clients reconnect without token leakage in URLs or logs.
- [x] `GET /api/settings` and setup/trust responses contain no raw web token,
      device PSK, webhook URL secret, Telegram token, failure-webhook credential,
      or profile key; dedicated replacement/rotation routes never echo a secret.
- [x] Updating any one settings section preserves byte-equivalent mesh, Cadence,
      Telegram, Rails observer, version, and unrelated feature sections.
- [x] Every approval records and every execution verifies payload hash,
      normalized destination, material preview renderer version, effect class,
      and policy version; a changed field invalidates authority before egress.
- [x] Apple moves the hub/pairing bearer token to device-only Keychain storage,
      deletes the migrated plaintext value, and keeps only peer identity in
      defaults; profile-key behavior remains unchanged.
- [x] Setup status, doctor, Security inventory, Web trust drawer, and Swift trust
      detail derive enabled destination, boundary, data class, authority basis,
      background ability, revoke action, and last receipt from one registry.
- [x] Local-provider no-fallback, destination allow-lists, pane identity, secret
      non-sync, audit integrity, and schema refusal remain green.

## Test plan

- **Unit:** `uv run pytest -q tests/unit/test_web_auth.py tests/unit/test_actuator_executor.py tests/unit/test_actuator_contract.py tests/unit/test_config.py tests/unit/test_intel_egress_invariant.py tests/unit/test_coder_steering_grants.py tests/unit/test_db_schema_policy.py` plus new registry/settings-secret tests; focused Swift Keychain tests.
- **Integration:** `uv run pytest -q tests/integration/test_web_auth_gate.py tests/integration/test_web_settings_page.py tests/integration/test_web_setup_status_api.py tests/integration/test_web_meeting_proposals_api.py tests/integration/test_web_trust_chip.py`; Web RuntimeBus valid/invalid-token tests.
- **Manual / device:** Bind a test hub off loopback; prove Web and physical iOS
  connect with the token, bad/missing credentials fail visibly, rotate the
  credential, and inspect Keychain/defaults plus network/log output for leaks.

## Notes / open questions

This story may add compatibility response fields such as `*_set` and host-only
fingerprints. It must not preserve raw-secret round trips for form convenience.

Implementation began on 2026-07-10 by direct owner instruction to continue to
the next story while Phase 91 remains current. The general runtime socket now
uses header/subprotocol auth without URL credentials, with reconnect-capable
React and Swift clients; settings reads and writes are secret-redacted,
dedicated, and section-preserving; schema v13 captures and the executor verifies
the complete material authority tuple before egress; the paired-hub bearer has
a one-way device-only Keychain migration; and one versioned destination/operation
registry feeds setup, doctor, Security, Web, and Swift trust detail.

Automated evidence is green: 230 focused Python/integration tests, Web
architecture/typecheck/112 tests/build, 524 Swift tests with 9 expected skips,
the generated iOS simulator app build,
Ruff, and wheel packaging (both registries present). The story remains open only
for the test plan's real off-loopback hub and physical iPhone/iPad inspection:
valid/bad/missing auth, rotation/reconnect, Keychain/defaults, and network/log
leak review. No device result is inferred from simulator compilation.
