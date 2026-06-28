# Evidence — HSM-24-01 (RuntimeProfile contract + SyncKind.profile + Keychain key store)

**Date:** 2026-06-28
**Story:** [story-01-profile-contract-keychain.md](./story-01-profile-contract-keychain.md)
**Result:** DONE. The load-bearing contract foundation ships with zero behavior change.
`swift test` **389 passed / 8 skipped / 0 failed** (was 381; +8 this story). Contracts target
builds; the app (iphonesimulator) builds with the additions.

## What shipped

- **`RuntimeProfile`** (`Sources/Contracts/Primitives.swift`) — a named inference target:
  `kind: .onDevice | .openAICompatible`, `modelFile` / `baseURL` / `model`, `contextLimit`,
  `requiresKey`, timestamps. **No `apiKey` field by design.** `isLocal` + `egressHost` derive the
  trust scope (on-device → no host → "local").
- **`RuntimeProfileMigration`** (same file) — a pure, deterministic mapping (takes `now`) from the
  legacy single config (mode + one endpoint) → `(profiles, activeId)`. Always seeds a local profile;
  preserves a configured endpoint as a second profile even if the user was on local; `endpointHasKey`
  only flags the caller to move the key into the Keychain (no key flows through).
- **Sync** (`Sources/Contracts/Sync.swift`) — `SyncKind.profile`; `ChangeSet.profiles:
  [Synced<RuntimeProfile>]` wired into `init` / `isEmpty` / `count`. A **custom tolerant
  `init(from:)`** decodes any absent array to `[]` — so a surface that doesn't yet know `profiles`
  (the hub pre-24-04) still decodes, and old payloads keep working.
- **`ProfileKeyStore`** (`App/MeetingCapture/ProfileKeyStore.swift`) — the device-local Keychain
  custodian (`kSecClassGenericPassword`, `…AfterFirstUnlockThisDeviceOnly`), keyed by profile id.
  The key lives ONLY here, joined to an `EndpointConfig` at request time, never on the shape.

## Acceptance criteria → proof

- **Contract round-trips Codable.** `RuntimeProfileTests.testRoundTrip` ✅
- **A `ChangeSet` carries a profile and round-trips.** `testChangeSetCarriesProfilesAndRoundTrips` ✅
- **Back-compat: a payload without `profiles` still decodes.** `testChangeSetDecodesWhenProfilesAbsent`
  (and the full sync suite stayed green — no regression from the custom decoder). ✅
- **The never-sync invariant.** `testKeyNeverInThePayload` — the encoded profile + a `ChangeSet`
  carrying it contain no `apiKey` and no `sk-`-shaped material; the shape *cannot* carry a key. ✅
- **Migration.** local-only / endpoint-active / local-active-but-endpoint-preserved all map as
  specified. ✅
- **No UI / no behavior change.** The contract + store exist; nothing wires them yet (that is 24-02).

## Notes

- The Keychain store itself is not exercised by `swift test` (no keychain in the macOS test context);
  its API shape is verified by compilation and will be walked on device in 24-02/24-03.
