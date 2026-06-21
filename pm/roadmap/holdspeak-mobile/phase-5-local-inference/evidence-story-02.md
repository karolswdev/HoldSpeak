# Evidence — HSM-5-02 (Mode A on-device run) — REAL METAL, owner-witnessed

**Date:** 2026-06-20
**Story:** [story-02-llm-provider-impl.md](./story-02-llm-provider-impl.md)
**Result:** **DONE on real metal.** A GGUF model is hosted **entirely on the iPad
Air M4** and turns a meeting transcript into artifacts with **no network** (charter
Mode A). The owner watched the artifacts render on the device. This discharges the
long-pending "iPad airplane-mode run" that was blocked behind the device lock.

## What ran on the device

- **App:** the fully-local Mode-A harness (`App/LocalHarnessApp.swift`) — the first
  iOS build that LINKS the native engine (`InferenceLlama` / `LlamaProvider` =
  llama.cpp via LLM.swift) and loads a GGUF from the app's Documents.
- **Model:** **Qwen3-4B-Instruct-2507, Q6_K** (3.08 GB) — the July refresh, pushed
  into the app container with `push-model-device.sh`.
- **Device:** iPad Air 11-inch (M4), 8 GB, `6B2F424D-…` (devicectl `connected`).
- **Path:** transcript → `LlamaProvider` (Metal, no network) →
  `ArtifactGenerationEngine` → decisions / action_items / requirements cards.

## Proof

- **Owner observation (authoritative):** "I was sitting at the iPad and I saw the
  results … the local model is working." The artifact cards rendered on-device.
- **No OOM:** after auto-run, `xcrun devicectl device info processes` showed
  `HoldSpeakMobile` (PID 1463) alive with the 3.08 GB model resident — i.e. Q6_K
  fits the 8 GB Air's default memory ceiling without a jetsam kill.
- Headless device-log capture was **not** achieved (`log stream` cannot target a
  connected device; no `idevicescreenshot` installed) — the evidence is the owner's
  direct observation plus the live process.

## How it was built (snags cleared — keep for the next device build)

- `gen-local-harness.rb` stages Contracts/Providers/RuntimeCore/**InferenceLlama**
  into one module and adds an SPM dependency on **LLM.swift ≥ 2.1.0** (product `LLM`).
- **`-skipMacroValidation`** — LLM.swift ships a macro plugin; xcodebuild blocks it
  behind an interactive trust gate otherwise.
- **Do not flatten `CONFIGURATION_BUILD_DIR`** — LLM.swift pulls swift-syntax, and a
  flat product dir causes "Multiple commands produce …" collisions. Use
  `-derivedDataPath` (standard per-target layout). Both encoded in
  `local-harness-device.sh`.
- Build for `generic/platform=iOS`, then `devicectl device install` — more reliable
  than pinning the device id when the build-time tunnel is flaky.

## Known constraint (the next-level lever)

Without the **Increased Memory Limit** entitlement (rejected by automatic signing —
the App ID needs the capability enabled in the developer portal first), ~3 GB is the
safe app budget, so **4B Q-quant is the ceiling**. Enabling that capability unlocks
Qwen3-8B (~5 GB) on the 8 GB iPad. `App/Local.entitlements` is staged and ready;
re-enable `CODE_SIGN_ENTITLEMENTS` in the generator once the capability is on.

## Remaining for Phase 5

- Explicit radios-off airplane-mode toggle + the 30-min meeting (Gate 4 / HSM-5-05)
  — the run was fully-local (no endpoint, no network calls) by construction, but the
  formal airplane-mode + duration gate is still its own closeout.
