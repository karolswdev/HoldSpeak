# Phase 5 — Local Inference

**Status:** planning (scaffolded 2026-06-18). Track F of the Council
Implementation Charter. The phase that lights up Mode A (Fully Local): it
delivers the on-device `ILLMProvider` (Layer 3) so a meeting can go
Audio → Whisper → LLM → Artifacts with no network. It also resolves the
Phase-0 deferred decision — which inference engine the mobile runtime stands on.

**Last updated:** 2026-06-18 (scaffolded + **pre-grounded** — the owner's
inference brief landed early ([`../research/inference-on-apple.md`](../research/inference-on-apple.md)):
the in-app candidate set is Core ML / llama.cpp+GGUF / MLC-LLM (Ollama and vLLM
are Mode-B/C companions, not in-app), 4-bit PTQ is the shipping default, and the
charter's per-device model tiers are confirmed. HSM-5-01 and HSM-5-03 are updated
to cite it; the measured engine pick is still HSM-5-01's job. No build work
started.).

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
| HSM-5-01 | Engine evaluation & pick | backlog | [story-01](./story-01-engine-evaluation.md) | — |
| HSM-5-02 | `ILLMProvider` impl + Mode A | backlog | [story-02](./story-02-llm-provider-impl.md) | — |
| HSM-5-03 | Model packaging & per-device defaults | backlog | [story-03](./story-03-model-packaging-strategy.md) | — |
| HSM-5-04 | Structured / JSON output | backlog | [story-04](./story-04-structured-output.md) | — |
| HSM-5-05 | 30-minute meeting closeout (Gate 4) | backlog | [story-05](./story-05-thirty-minute-meeting-closeout.md) | — |

## Where we are

Scaffolded and pre-grounded. Phase 0 deferred the engine choice to this phase, and
the owner's inference brief ([`../research/inference-on-apple.md`](../research/inference-on-apple.md))
arrived early — so HSM-5-01 no longer starts from a blank page: the candidate set
is fixed (Core ML / llama.cpp+GGUF / MLC-LLM), the eval axes and device/quant
budgets are documented, and Ollama/vLLM are ruled out as in-app. HSM-5-01 is still
the story that makes the measured pick, and everything else depends on its outcome. The five stories are stubbed
against Track F's three deliverable areas (engine evaluation, the on-device
`ILLMProvider`, the local-model strategy) plus the two stories this program needs
to make Mode A real and testable (structured output in the contract shapes, and
the Gate-4 closeout). Next: pick up HSM-5-01 — evaluate the three engines on
Tier-1 hardware and record the pick.

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
  practical phone upper bound and 12B an iPad-16GB/hybrid target. The measured
  pick is still HSM-5-01.

## Decisions deferred

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
