# HSM-24-02 — Apple basic config: the active-profile picker over the existing seam

**Status:** planned (after 24-01).

## Problem

Settings → Intelligence currently shows "Where intelligence runs" as a two-card choice (This
device / LAN endpoint) wired straight to `InferenceConfigStore.mode`. With profiles, "basic" should
simply be: **pick one active profile** — no new concepts for the single-target user.

## The design

- `InferenceConfigStore` keeps a `profiles: [RuntimeProfile]` (synced) + `activeProfileId`. The
  legacy `mode`/endpoint fields become computed views over the active profile (kept until callers
  migrate).
- `makeProvider` switches on the **active profile's** `kind`, not the global `mode`:
  - `.onDevice` → `LlamaProvider.make(modelPath:)` (the auto-template factory).
  - `.openAICompatible` → `OpenAIEndpointProvider(config:)`, where `config` joins the synced shape +
    the Keychain key at call time.
- The basic Settings UI: one row, "Run on: [active profile ▾]", the menu listing profiles; an
  "Advanced…" entry opens 24-03. The egress badge reads the active profile's `egress`.
- Byte-identical for a user who has exactly one profile (the migrated default).

## Scope

- `InferenceConfigStore`: `profiles` + `activeProfileId`; `makeProvider(active)`; legacy fields as
  computed shims.
- Basic Settings row (active picker) + the egress badge from the profile.
- The on-device-budget `contextLimit` is computed for on-device profiles (reuse `OnDeviceBudget`).

## Test plan

- `swift test`: `makeProvider` returns the right provider for each active profile kind; the endpoint
  provider's `EndpointConfig` carries the key from the Keychain (not the synced shape).
- Sim: Settings shows the active picker; selecting a profile switches the runtime; egress badge
  matches.

## Done when

A single-profile user sees no change; switching the active profile switches the runtime through the
existing seam; the API key is sourced from the Keychain at request time. Verified on the iPad.
