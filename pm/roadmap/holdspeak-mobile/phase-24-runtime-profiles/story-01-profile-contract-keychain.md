# HSM-24-01 — The `RuntimeProfile` contract + `SyncKind.profile` + the Keychain key store

- **Status:** done (2026-06-28) — **leads, load-bearing** (every surface depends on it). Evidence: [evidence-story-01.md](./evidence-story-01.md). `swift test` 389/0 (+8).

## Problem

`InferenceConfigStore` (`SketchDiagram.swift`) holds ONE target: `mode` + a single endpoint
`url`/`model`/`key` in `UserDefaults`. There is no notion of a *named, reusable* target, no list,
and no per-agent assignment. And the API key currently lives in `UserDefaults` — fine for one
device, unsafe to sync.

## The design

A new contract type in `Sources/Contracts` (so every surface shares it, like `Agent`):

```
public struct RuntimeProfile: Codable, Identifiable, Equatable, Sendable {
    public var id: String
    public var name: String
    public var kind: Kind            // .onDevice | .openAICompatible
    public var modelFile: String     // onDevice: the .gguf filename
    public var baseURL: String       // openAICompatible
    public var model: String         // openAICompatible
    public var contextLimit: Int     // usable window (on-device computed; endpoint known/declared)
    public var egress: EgressScope   // .local | .cloud(host)
    // NO apiKey field. The key is referenced by id and read from the Keychain at request time.
}
```

- Add `case profile` to `SyncKind` (`Sources/Contracts/Sync.swift`) and carry profiles in
  `ChangeSet` like agents/notes/kbs.
- A `ProfileKeyStore` (Keychain-backed) keyed by `profile.id` → the API key. **The key is never a
  field on `RuntimeProfile` and never enters a `ChangeSet`.** `EndpointConfig` is assembled at
  request time by joining the synced shape + the local key (mirrors how the connector joins the
  credential at execute time).
- A migration: the existing single `InferenceConfigStore` config becomes one seed profile
  ("This device" if local, or "My endpoint" if an endpoint was set), so existing users land on an
  equivalent active profile with zero visible change.

## Scope

- `RuntimeProfile` + `EgressScope` in Contracts; `SyncKind.profile` + `ChangeSet.profiles`.
- `ProfileKeyStore` (Keychain wrapper) with get/set/delete by profile id.
- The one-time migration from the legacy `InferenceConfigStore` fields → a seed profile + active id.
- Pure unit tests for the contract, the never-sync invariant, and the migration.

## Test plan

- `swift test`: `RuntimeProfile` round-trips Codable; a `ChangeSet` carrying a profile **never**
  serializes a key (assert the encoded JSON contains no key material); migration produces the
  equivalent active profile from each legacy state (local / endpoint / endpoint+key).
- Keychain store: set → get → delete by id (device test; sim acceptable for the API shape).

## Done when

The contract + sync kind + Keychain store exist and are tested; the never-sync invariant has an
explicit test; legacy config migrates to a seed active profile with no behavior change. No UI yet.
