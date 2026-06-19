# Evidence — HSM-5-01 — Engine evaluation & pick

- **Shipped:** 2026-06-19
- **Commit:** Phase-5 HSM-5-01 on `main` (see commit message)
- **Owner:** unassigned

## Decision: `llama.cpp` + GGUF

The on-device inference engine for the mobile runtime (Track F) is **`llama.cpp`
with GGUF weights**. This resolves the Phase-0 deferred Track-F decision.

**Banked, not bake-off measured.** The story-as-written wanted a three-engine
on-device measurement bake-off (MLC-LLM / llama.cpp / Core ML). The owner's
standing directive is *bank on chosen tech — no measurement spikes/gates before
implementation*, so the decision is made from the research canon
(`../research/inference-on-apple.md`) and the choice is validated **implicitly**
when HSM-5-02 runs it on the device; if it disappoints (the phase risk register's
stop-signals), HSM-5-01 re-opens with that evidence.

## Rationale (against the canon's axes)

- **Model availability — decisive:** any 4B/8B in GGUF at 4-bit, off the shelf; no
  Core ML conversion pipeline, no MLC compile step.
- **Maturity + Metal:** battle-tested Metal backend at the M-series decode-bound
  sweet spot; the brief names llama.cpp one of "the relevant embedded iOS/iPadOS
  runtimes."
- **Integration cost / reversibility:** a C API bridged from Swift behind the
  existing `ILLMProvider` port — swap the adapter, not the app, if MLX/Core ML
  wins later.
- **Structured output:** GBNF grammars available as a future constrained-decoding
  optimization; the engine-agnostic `StructuredOutput` floor (HSM-5-04) already
  covers correctness.

## Named models (HSM-5-03 pins exact artifacts)

| Tier | Device | Model | Notes |
|---|---|---|---|
| Tier-1 | iPhone (4B) | `Llama-3.2-3B-Instruct` Q4_K_M GGUF | ~2GB |
| Tier-2 | iPad (8B) | `Llama-3.1-8B-Instruct` Q4_K_M GGUF | ~4.9GB; fits the M4 iPad |
| 12B+ | plugged-in only | a 12–14B Q4 GGUF (e.g. `Qwen2.5-14B-Instruct`) | gated by `InferenceModelPolicy.isAllowed(_, pluggedIn:)` |

## Trade-off accepted

**MLX** (Swift-native; the desktop uses it for Whisper) was considered and is the
recorded fallback — it offers cleaner SPM integration but sits outside the owner's
captured candidate set and loses to llama.cpp on raw model availability. The
`ILLMProvider` abstraction keeps the switch cheap.

## Next

HSM-5-02 — wire llama.cpp into the package, bridge its C API behind `ILLMProvider`,
pull a Tier-1/Tier-2 GGUF, and run a real completion on the connected **iPad Air
M4** (the device's first real on-device inference; unblocks the Phase-6 parity
verdict HSM-6-05).
