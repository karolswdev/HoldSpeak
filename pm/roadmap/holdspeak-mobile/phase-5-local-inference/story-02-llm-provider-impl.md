# HSM-5-02 — `ILLMProvider` impl + Mode A

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** done (2026-06-20 — **Mode A proven on real metal**: Qwen3-4B-Instruct-2507
  Q6_K hosted fully on the iPad Air M4, transcript → on-device artifacts, no network,
  owner-witnessed. First iOS build linking the llama.cpp engine. See
  [evidence-story-02.md](./evidence-story-02.md).)
- **Depends on:** HSM-5-01
- **Unblocks:** HSM-5-04, HSM-5-05, HSM-6-01
- **Owner:** unassigned

## Progress (2026-06-18)

The seam the impl plugs into is ready + host-tested: the `ILLMProvider` protocol
(`complete(prompt:)`) and the `StructuredOutput.generate(...)` layer on top of it
(HSM-5-04) that turns a provider's text into validated contract values with a
bounded repair-retry — exercised by a fake provider. The **concrete engine-backed
`ILLMProvider`** (the HSM-5-01 engine + a model, running Mode A on a device) is
device/dep work and stays in-progress until then.

## Progress & evidence (2026-06-19) — host-proven on Metal

The engine-backed provider is implemented and **Mode A is proven on real metal
(this Mac's Metal)**; only the iPad-specific run is gated on the device unlock.

- **`LlamaProvider`** (`apple/Sources/InferenceLlama/LlamaProvider.swift`) — an
  `ILLMProvider` backed by **llama.cpp via LLM.swift** (the HSM-5-01 pick). Loads a
  GGUF by path, `complete(prompt:)` returns text with **no network**. The native
  engine is isolated to the `InferenceLlama` SPM target, so the domain
  (Contracts/RuntimeCore) never links it (the Phase-6 "ProviderInterfaces" concern,
  resolved as a separate product).
- **Proof** (`apple/Tests/InferenceLlamaTests/LlamaProviderTests.swift`, opt-in via
  `HS_GGUF_PATH`), against **Qwen2.5-7B-Instruct Q4_K_M** on disk:
  - `testLoadsGGUFAndCompletes` — loads the GGUF, completion = `PONG` (~8.5s incl.
    cold model load, 512-ctx).
  - `testModeAArtifactGenerationFullyLocal` — transcript → `LlamaProvider` →
    `ArtifactGenerationEngine` → real `decisions` + `action_items` artifacts, fully
    local (~13.4s for two generations). Propose-only (`.draft`).
- Full suite: `swift test` **57 executed / 5 skipped (opt-in) / 0 failures**;
  llama.cpp builds; the layer guard still confirms the domain doesn't link the engine.

**Remaining:** the on-device airplane-mode run on the iPad Air M4 (HSM-5-02's
device acceptance) — gated on the device unlock; it reuses this exact `LlamaProvider`
behind the same seam. Model packaging/download is HSM-5-03.

## Problem

The engine pick (HSM-5-01) is a decision, not a running provider. The runtime
needs a concrete `ILLMProvider` (Layer 3) on the chosen engine so the Runtime
Core can run inference without knowing which engine sits underneath, and so Mode
A (fully local) works end to end.

## Scope

- **In:** the `ILLMProvider` implementation on the chosen engine; loading a model
  and running a completion on-device; wiring Mode A so a transcript can reach the
  provider with no network. The provider stays behind the Layer-3 abstraction so
  Modes B (homelab) and C (endpoint) can be other implementations of the same
  interface later.
- **Out:** the engine evaluation itself (HSM-5-01). Structured/JSON output
  shaping (HSM-5-04). Model packaging/download (HSM-5-03 — this story can assume a
  model is present locally). The Mode B/C providers. Artifact prompts (Phase 6).

## Acceptance criteria

- [x] `ILLMProvider` is implemented on the HSM-5-01 engine and returns a
      completion (proven on host Metal; the iPad-device run is gated on the unlock).
- [~] Mode A runs end to end with no network — proven host-side (transcript →
      `LlamaProvider` → artifacts, no egress); the airplane-mode run on the iPad
      Air M4 is pending the device unlock.
- [x] The Runtime Core calls only the `ILLMProvider` interface — the engine lives
      in a separate `InferenceLlama` product; the domain doesn't link it (layer
      guard green), so swapping the engine wouldn't touch core code.
- [x] Cold-load and warm-call behavior documented: Qwen2.5-7B Q4_K_M on this Mac's
      Metal — ~8.5s to first token incl. cold load (512-ctx); two artifact
      generations ~13.4s. iPad figures land with the device run.

## Test plan

- Unit: a fake `ILLMProvider` proves the Runtime Core depends only on the
  interface; the real provider has an on-device smoke test (load + one completion).
- Manual / device: airplane-mode Mode A run on a Tier-1 device — transcript in,
  response out, no network.

## Notes / open questions

- Keep the interface narrow and engine-agnostic; anything engine-specific
  (sampling, grammar/constrained decoding) lives behind the protocol so HSM-5-04
  can lean on it without leaking the engine into the core.
- This is where Mode A becomes real — the charter's headline "no laptop, fully
  local" promise rides on this story plus HSM-5-05.
