# Phase 5 — Local Inference

**Status:** in-progress (HSM-5-04 done 2026-06-18; **HSM-5-01 done 2026-06-19 —
engine = llama.cpp+GGUF**; **HSM-5-06 — endpoint provider (Modes B/C) + mode
setting — host/live-proven, device build+install done, on-device launch pending
the iPad unlock**; **HSM-5-02 — `LlamaProvider` (llama.cpp/Mode A) host-proven on
Metal, iPad airplane-mode run pending the unlock**; HSM-5-03 in-progress; HSM-5-05
**HSM-5-03 — model packaging both delivery paths host-proven (Files sideload +
Hugging Face download), iPad clean-install pending the unlock**; HSM-5-05
device-gated). Track F
of the Council Implementation Charter. The phase
that lights up Mode A (Fully Local): it delivers the on-device `ILLMProvider`
(Layer 3) so a meeting can go Audio → Whisper → LLM → Artifacts with no network.
It also resolves the Phase-0 deferred decision — which inference engine the mobile
runtime stands on.

**Last updated:** 2026-06-20 (**HSM-5-02 DONE — Mode A proven on REAL METAL.** A GGUF
is hosted entirely on the iPad Air M4 and turns a meeting transcript into artifacts
with no network — the owner witnessed the artifact cards render on the device. Model:
**Qwen3-4B-Instruct-2507 Q6_K** (3.08 GB), pushed via `push-model-device.sh`; app =
the first iOS build that links the native llama.cpp engine (`gen-local-harness.rb`
stages InferenceLlama + the LLM.swift SPM package). The process stayed alive with the
3 GB model resident, so Q6 fits the 8 GB ceiling without the increased-memory
entitlement (which would unlock Qwen3-8B once the App-ID capability is enabled). Build
snags cleared for the next device build: `-skipMacroValidation` (the LLM macro plugin)
+ `-derivedDataPath` rather than a flat `CONFIGURATION_BUILD_DIR` (swift-syntax object
collisions). See [`evidence-story-02.md`](./evidence-story-02.md).
Earlier: **HSM-5-03 — model packaging: both delivery paths host-proven.** A
`ModelCatalog` pins the per-tier GGUFs (4B Llama-3.2-3B / 8B
Llama-3.1-8B / 12B+ Mistral-Nemo, all Q4_K_M; HF URLs verified live), a Foundation
`ModelStore` is the model manager (list / **Files-sideload import** / delete /
per-device `resolveActive`), and a Foundation `ModelDownloader` does the **Hugging
Face download** by canonical resolve-URL with real progress (LLM.swift's built-in
HF scraper is broken against current HF, so we download by pinned URL). `swift test`
**62/62** (6 opt-in skips) incl. store/catalog tests; the real download is proven by
an opt-in test (TinyLlama 0→100% → load → complete). `push-model-device.sh` adds the
`devicectl` dev path. Remaining: the iPad clean-install first-run (unlock). Earlier:
**HSM-5-02 — the on-device (Mode A) engine, host-proven on Metal.** `LlamaProvider` (an `ILLMProvider` backed by **llama.cpp via LLM.swift**,
the HSM-5-01 pick) loads a GGUF by path and completes with no network. Proven on this
Mac's Metal against **Qwen2.5-7B Q4_K_M**: a completion (`PONG`, ~8.5s incl. cold load)
and a full **fully-local** run (transcript → `LlamaProvider` → `ArtifactGenerationEngine`
→ real decisions + action_items, ~13.4s). The native engine is isolated to a separate
`InferenceLlama` SPM product so the domain never links it (the Phase-6
"ProviderInterfaces" concern, resolved). `swift test` **57/57** (5 opt-in skips), layer
guard green. Remaining: the iPad airplane-mode run (gated on the device unlock) +
model packaging (HSM-5-03). Earlier: **HSM-5-06 — the OpenAI-compatible endpoint provider
(charter Modes B/C) + a runtime-mode setting**, shipped ahead of the on-device
engine on the owner's steer: inference mode is a user setting (local default) and
the runtime must point at any OpenAI-compatible endpoint, so the iPad need not
spend unified memory on a resident model. `OpenAIEndpointProvider` (URLSession,
Foundation only) + `RuntimeMode`/`EndpointConfig`/`InferenceProviderFactory`;
`swift test` **46/46** (+8), a live run emits real contract-shaped artifacts from a
transcript against a clean LAN `llama-server` (Qwen2.5-7B), and the HSM-6-05 parity
*mechanism* scores that real output **1.00 PASS**. The Mode-C harness **built +
signed + installed on the physical iPad Air M4**; launch is blocked only by the
device lock screen (one command finishes it once unlocked). Finding: the `.43`
homelab box forces a `{"line": …}` grammar, so the proof used a clean dev-Mac
endpoint over the LAN. HSM-5-02 (on-device GGUF, Mode A) reuses this same seam +
harness. Earlier: **HSM-5-01 done — engine = `llama.cpp` + GGUF**, a
banked decision from the research canon (not a bake-off, per the owner's no-spikes
directive); resolves the Phase-0 Track-F deferral. Decisive axis: off-the-shelf
4B/8B GGUF availability (no Core ML conversion / MLC compile); mature Metal; a C
API behind the existing `ILLMProvider` port → reversible. Named models
`Llama-3.2-3B` (Tier-1) + `Llama-3.1-8B` (Tier-2) Q4_K_M GGUF; MLX is the fallback.
**HSM-5-02 next** — wire llama.cpp + run a GGUF completion on the connected iPad
Air M4 (the iPad's first real on-device inference; unblocks HSM-6-05). Earlier:
**HSM-5-04 done + host slice** — the structured-output plumbing (`StructuredOutput`:
extract JSON from messy model text → decode through the contract `Codable` →
bounded repair-retry) and the per-device LLM model policy (`InferenceModelPolicy`:
iPhone→4B / iPad→8B, 12B+ plugged-in-only) are host-tested (`swift test` **24/24**).
Earlier: pre-grounded by the owner's inference brief
([`../research/inference-on-apple.md`](../research/inference-on-apple.md)) — candidate
set Core ML / llama.cpp+GGUF / MLC-LLM, 4-bit PTQ default, per-device tiers.).

## Goal

Stand up on-device LLM inference for the Apple mobile runtime: evaluate the
candidate engines (MLC-LLM, llama.cpp, CoreML-native) on Tier-1 hardware and pick
one, implement the `ILLMProvider` abstraction on the chosen engine with Mode A
wired end to end, ship the model packaging/download path with the per-device
defaults (4B on iPhone, 8B on iPad, 12B+ experimental only when plugged in), and
plumb structured output so artifacts come back in the Phase-0 contract shapes.
The phase closes on Quality Gate 4: a 30-minute meeting processed fully locally
on Tier-1 hardware.

## Scope

- **In:** the engine evaluation + the recorded pick (HSM-5-01); the
  `ILLMProvider` implementation on the chosen engine with Mode A wired
  (HSM-5-02); model packaging/download + the per-device default strategy
  (HSM-5-03); structured/JSON generation plumbing producing Phase-0 contract
  shapes (HSM-5-04); the Gate-4 closeout — a 30-minute meeting processed locally
  (HSM-5-05).
- **Out:** the meeting-intelligence prompts and the artifact-quality parity bar
  (Track G / Phase 6 — this phase proves a meeting *processes* locally and emits
  *contract-shaped* artifacts; it does not chase the desktop quality baseline).
  MIR profile behavior (Track H / Phase 7). The Whisper transcription runtime
  (Track D / Phase 3 — Mode A consumes its output). Homelab/endpoint providers
  (Modes B and C — separate `ILLMProvider` implementations, not this phase).
  Cloud LLM providers.

## Exit criteria (evidence required)

- [ ] One inference engine is chosen from MLC-LLM / llama.cpp / CoreML-native,
      with the decision and its rationale recorded against measured Tier-1
      behavior — resolves the Phase-0 deferred Track-F decision (HSM-5-01).
- [ ] `ILLMProvider` is implemented on the chosen engine and Mode A
      (Audio → Whisper → local LLM → Artifacts, no network) runs end to end on a
      Tier-1 device (HSM-5-02).
- [ ] Model packaging/download works first-run on a clean install, and the
      per-device default resolves correctly: 4B on iPhone, 8B on iPad, 12B+
      selectable only when the device is plugged in (HSM-5-03).
- [ ] Structured generation returns artifacts that validate against the Phase-0
      JSON Schemas for `ActionItem`, `Decision`, `Risk`, `Requirement`,
      `Artifact` with zero schema errors (HSM-5-04).
- [ ] **Track F gate — a 30-minute meeting is processed fully locally** on a
      Tier-1 device (airplane-mode or network-disabled), end to end, emitting
      contract-shaped artifacts (HSM-5-05).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-5-01 | Engine evaluation & pick | done | [story-01](./story-01-engine-evaluation.md) | [evidence-01](./evidence-story-01.md) |
| HSM-5-02 | `ILLMProvider` impl + Mode A | in-progress (host-proven; iPad run pending unlock) | [story-02](./story-02-llm-provider-impl.md) | in story (host Metal proof) |
| HSM-5-03 | Model packaging & per-device defaults | in-progress (sideload + HF download host-proven; iPad install pending) | [story-03](./story-03-model-packaging-strategy.md) | in story (host proof) |
| HSM-5-04 | Structured / JSON output | done | [story-04](./story-04-structured-output.md) | [evidence-04](./evidence-story-04.md) |
| HSM-5-05 | 30-minute meeting closeout (Gate 4) | backlog | [story-05](./story-05-thirty-minute-meeting-closeout.md) | — |
| HSM-5-06 | Endpoint provider (Modes B/C) + mode setting | in-progress | [story-06](./story-06-endpoint-provider.md) | in story (evidence-06 on `done`) |

## Where we are

The host-testable slice of Track F is shipped. **HSM-5-04 (done)** is the
structured-output bridge — `StructuredOutput.extractJSON`/`decode`/`generate`
turns messy model text into validated contract values with a bounded repair-retry
(tested with a fake provider, 24/24). The **per-device model policy**
(`InferenceModelPolicy`, part of HSM-5-03) is done + tested (iPhone→4B / iPad→8B,
12B+ plugged-in-only). The candidate set is fixed (Core ML / llama.cpp+GGUF /
MLC-LLM; Ollama/vLLM Mode-B/C). **HSM-5-01 is now done — the engine is
`llama.cpp` + GGUF** (banked from the canon, not a bake-off, per the owner's
no-spikes directive; named models `Llama-3.2-3B`/`Llama-3.1-8B` Q4_K_M GGUF). Phase
6 (Meeting Intelligence) is built on this seam (6-01/02/03/04 done). What remains is
device/dep: the **engine-backed `ILLMProvider`** (HSM-5-02 — wire llama.cpp, bridge
the C API, run a GGUF completion on the connected iPad Air M4), **model packaging**
(HSM-5-03's other half), and the **30-min local gate** (HSM-5-05). **HSM-5-02 is the
next thrust** for true airplane-mode-local inference. But the **iPad already runs
real meeting intelligence today via HSM-5-06** — the OpenAI-compatible endpoint
provider (Modes B/C), built/signed/installed on the iPad Air M4 and host/live-proven
against a real model; that path also gives HSM-6-05 a real on-device `ILLMProvider`,
so the parity verdict is no longer engine-blocked.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| The engine evaluation has no clean winner — each engine wins on a different axis (model coverage, structured output, integration cost) | high | HSM-5-01 fixes the decision axes up front (Tier-1 throughput, 4B/8B model availability, structured-output support, on-device integration cost) and weights them before measuring; record the trade-off, do not stall on a tie | Two engines tie on the weighted criteria after a full Tier-1 measurement — escalate the tie to the owner with the data rather than re-running benchmarks indefinitely |
| Thermal throttling or memory pressure makes a 30-minute meeting unprocessable on a Tier-1 device — the model loads but the device throttles or the OS kills it mid-run | high | Size defaults conservatively (4B iPhone / 8B iPad), gate 12B+ behind plugged-in only, process in chunks rather than one giant context, and measure sustained (not burst) throughput in HSM-5-01 | A 30-minute meeting cannot complete locally on a Tier-1 device at the per-device default without thermal kill or OOM — drop to a smaller default tier and re-baseline Gate 4; if even 4B can't hold, escalate the gate to the owner |
| The chosen engine can't reliably emit Phase-0 contract-shaped JSON (free-form drift, no grammar/constrained-decoding support) | medium | Make structured-output support a weighted criterion in HSM-5-01; HSM-5-04 adds validation + a repair/retry path rather than trusting raw model output | Artifacts fail Phase-0 schema validation more often than a retry budget can absorb — revisit the engine choice (HSM-5-01) before building Phase-6 intelligence on top |
| The picked engine's model formats lag (no current 4B/8B Apple-silicon-optimized build) | medium | HSM-5-01 confirms a concrete, available Tier-1 and Tier-2 model per engine before picking; HSM-5-03 pins exact model artifacts | No production-ready 4B build exists for the chosen engine on Apple silicon — re-open HSM-5-01 |

## Decisions made (this phase)

- 2026-06-18 — **Pre-grounded by the owner's inference brief**
  ([`../research/inference-on-apple.md`](../research/inference-on-apple.md)): the
  in-app engine candidate set is **Core ML / llama.cpp+GGUF / MLC-LLM**;
  **Ollama and vLLM are explicitly Mode-B/C server companions, not in-app
  runtimes** (they belong to the homelab/endpoint providers + Phase-10 sync
  targets); **4-bit PTQ** is the shipping default; the charter's per-device tiers
  (4B iPhone / 8B iPad / 12B-experimental-plugged-in) are confirmed, with 7B the
  practical phone upper bound and 12B an iPad-16GB/hybrid target.
- 2026-06-19 — **HSM-5-01 resolved: the engine is `llama.cpp` + GGUF** (resolves
  the Phase-0 deferred Track-F decision). **Banked, not bake-off measured** — the
  owner's standing directive is no measurement spikes before implementation, so the
  pick is made from the research canon (decisive axis: off-the-shelf 4B/8B GGUF
  model availability with no conversion/compile step; mature Metal backend; a C API
  bridged behind the existing `ILLMProvider` port, so the choice is reversible).
  Named models: `Llama-3.2-3B` (Tier-1) + `Llama-3.1-8B` (Tier-2) Q4_K_M GGUF;
  12B+ plugged-in-only. MLX is the recorded fallback if llama.cpp underperforms
  on-device (validated implicitly in HSM-5-02 — failure re-opens HSM-5-01).

- 2026-06-19 — **Inference mode is a user setting, and any OpenAI-compatible
  endpoint is a first-class target (owner steer).** Local (Mode A) is the privacy
  default, but a meeting can instead run against a LAN/homelab (Mode B) or any
  endpoint (Mode C), so the iPad need not load a resident model when a capable
  endpoint is available. Modeled as `RuntimeMode` + `EndpointConfig` +
  `InferenceProviderFactory` on the one `ILLMProvider` seam (HSM-5-06). This
  re-sequences the endpoint provider ahead of the on-device GGUF (HSM-5-02), since
  it is the faster route to real on-device inference and unblocks HSM-6-05.
- 2026-06-19 — **The `.43` homelab box is not used for the structured-output
  proof:** it forces a server-side `{"line": …}` grammar that ignores the request's
  system prompt and `response_format`. The live proof runs against a clean
  dev-Mac `llama-server` over the LAN. Open question surfaced to the owner: relaunch
  `.43` without the grammar, or target per-call `response_format`.

## Decisions deferred

- **Default runtime mode** (local-as-privacy-default vs homelab-as-recommended,
  which the charter calls Mode B "recommended") — trigger: the Phase-8/9 settings
  UI — default: ship the setting now (HSM-5-06), confirm the shipped default with
  the owner before the experience phases.
- The inference engine itself (Core ML vs llama.cpp+GGUF vs MLC-LLM) — trigger:
  HSM-5-01 — default: none; this story makes the measured pick from the
  research-narrowed candidate set above (inherited from Phase 0's Track-F
  deferral). If Core ML wins, its `MLState` KV cache sets an iOS-18+ deployment
  floor — reconcile with Phase 1's minimum-deployment-target decision.
- Exact Tier-1 (4B) and Tier-2 (8B) model artifacts to ship — trigger: HSM-5-01
  picks the engine, HSM-5-03 pins the artifacts — default: the
  best-available Apple-silicon-optimized 4B/8B build for the chosen engine.
- Whether 12B+ is a shipped option or an opt-in download — trigger: HSM-5-03 —
  default: opt-in download, plugged-in-only, never the device default.
- Chunking strategy for long meetings (whole-transcript vs windowed) — trigger:
  HSM-5-04 / HSM-5-05 — default: windowed chunking sized to the per-device model's
  sustainable context, reconciled with the Track-G artifact prompts in Phase 6.
