# Evidence — HSM-24-02 (Apple basic config: active-profile picker over the existing seam)

**Date:** 2026-06-28
**Story:** [story-02-apple-basic-config.md](./story-02-apple-basic-config.md)
**Result:** DONE (foundation + basic picker; a live multi-profile *switch* is walked in 24-03, which
adds profile creation). `swift test` **389/0** (no regression); app builds (iphonesimulator) and
device-SDK compiles; migration verified by screenshot.

## What shipped

- **`InferenceConfigStore` is now profile-backed** (`SketchDiagram.swift`): `profiles:
  [RuntimeProfile]` + `activeProfileId`, persisted locally as JSON. `activeProfile` resolves
  (selected → first → synthesized local default).
- **One-time migration** (`migrateLegacyToProfiles`): on first launch the legacy single config (mode
  + one endpoint) becomes a profile list + active id via `RuntimeProfileMigration`, and **any API key
  is moved from UserDefaults into the Keychain** (`ProfileKeyStore`) and cleared from UserDefaults —
  the key leaves the shape's storage.
- **The active profile is applied onto the legacy fields** (`applyActive`), so every existing reader
  (`endpointConfig`, `isLocal`, `localGGUF`) keeps working unchanged — profiles are a management
  layer, not a rewrite of the inference path. `endpointConfig` now sources the key from the Keychain
  (active id) first, legacy field as a transition fallback.
- **`makeProvider(profile:localModelPath:context:)`** — the explicit-profile path the inline "Runs
  on" override will use; the legacy `makeProvider(localModelPath:context:)` now delegates to it with
  the active profile. The endpoint key is joined from the Keychain at call time.
- **`resolveProfile(agentProfileId:override:)`** — the owner's resolution order (override → agent →
  active), ready for 24-03's per-surface chips.
- **`RunsOnPicker`** (`RunsOnPicker.swift`) — the ONE reusable inline control (the owner's principle:
  the resolved profile is shown + changeable at the point of use). Settings shows it as the always-
  exposed **"Active profile"** chip above "Where intelligence runs".

## Acceptance criteria → proof

- **Single-profile user sees no behavior change.** The active profile is applied onto the legacy
  fields; the existing cards/editor are unchanged. The new chip merely *exposes* the default (per the
  owner's "the default must always be exposed"). Screenshot: the "Active profile · This device" chip
  over the unchanged cards. ✅
- **The key is sourced from the Keychain at request time.** `endpointConfig` + `makeProvider(profile:)`
  read `ProfileKeyStore.get(id)`; migration moved the legacy key into the Keychain and cleared it from
  UserDefaults. ✅
- **`makeProvider` routes through the active profile.** The legacy call path delegates to
  `makeProvider(profile: activeProfile, …)`. ✅
- **No engine regression.** `swift test` 389/0. ✅

## Deferred to 24-03 (honest)

A live multi-profile *switch* on device needs profile **creation**, which is 24-03 (advanced). Until
then there's one migrated profile, so the chip exposes it but has nothing to switch to. The
edit-writes-back-to-profile two-way sync is also 24-03's (its advanced editor owns profile CRUD on
the `profiles` array directly, avoiding any legacy-field entanglement in the live path).
