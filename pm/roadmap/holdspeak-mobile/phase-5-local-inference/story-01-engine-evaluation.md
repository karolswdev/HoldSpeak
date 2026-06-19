# HSM-5-01 — Engine evaluation & pick

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** done (banked decision — see "Decision" below)
- **Depends on:** none
- **Unblocks:** HSM-5-02, HSM-5-03, HSM-5-04, HSM-5-05
- **Owner:** unassigned

## Progress (2026-06-18)

Pre-grounded by the owner's inference brief (`../research/inference-on-apple.md`):
candidate set fixed to **Core ML / llama.cpp+GGUF / MLC-LLM** (Ollama/vLLM are
Mode-B/C companions, not in-app); 4-bit PTQ default; per-device tiers confirmed
(now encoded as `InferenceModelPolicy`).

## Decision (banked, 2026-06-19) — **llama.cpp + GGUF**

**Method note (supersedes the measured bake-off below):** the owner's standing
directive is *bank on chosen tech — no measurement spikes/gates before
implementation*. So this story is resolved by a **banked decision from the
research canon**, not a three-engine on-device bake-off. The real validation is
implicit: HSM-5-02 runs the chosen engine on the Tier-1 device, and if it
disappoints (the risk register's "engine can't hold Gate 4" / "can't emit
contract JSON" stop-signals), HSM-5-01 re-opens with that evidence.

**Chosen engine: `llama.cpp` + GGUF.** Rationale, against the canon's axes:

- **Model availability (decisive):** any 4B/8B in GGUF at 4-bit, off the shelf —
  no Core ML conversion pipeline, no MLC compile step.
- **Maturity + Metal:** a battle-tested Metal backend at the M-series decode-bound
  sweet spot the brief describes; the brief names llama.cpp one of "the relevant
  embedded iOS/iPadOS runtimes."
- **Integration cost:** a C API bridged from Swift behind the existing
  `ILLMProvider` port — so the pick is **reversible** (swap the adapter, not the
  app) if on-device behavior argues for MLX/Core ML later.
- **Structured output:** llama.cpp supports GBNF grammars (a future constrained-
  decoding optimization); the engine-agnostic `StructuredOutput` floor (HSM-5-04)
  already covers correctness.

**Concrete, currently-available models (HSM-5-03 pins exact artifacts):**
- **Tier-1 (iPhone, 4B):** `Llama-3.2-3B-Instruct` Q4_K_M GGUF (~2GB).
- **Tier-2 (iPad, 8B):** `Llama-3.1-8B-Instruct` Q4_K_M GGUF (~4.9GB) — fits the
  M4 iPad's unified memory.
- **12B+ (plugged-in only):** a 12–14B Q4 GGUF (e.g. `Qwen2.5-14B-Instruct`),
  gated by `InferenceModelPolicy.isAllowed(_, pluggedIn:)`.

**MLX considered, not chosen (now):** Swift-native and the desktop uses it for
Whisper, but it is outside the owner's captured candidate set and llama.cpp wins on
raw model availability. Recorded as the first fallback if llama.cpp underperforms
on-device.

## Problem

Phase 0 deliberately did not pick the on-device inference engine — it parked the
choice (MLC-LLM vs llama.cpp vs CoreML-native) for this phase, where it can be
decided against measured behavior rather than a guess (see
`../phase-0-contracts-and-charter-lock/current-phase-status.md` §"Decisions
deferred"). Every other Phase-5 story builds on whichever engine wins, so the
pick is the first thing that has to happen and it has to be defensible.

## Scope

- **In:** an evaluation of the three charter candidate engines (MLC-LLM,
  llama.cpp, CoreML-native) on Tier-1 hardware (iPad Air M4 / iPad Pro M4),
  against a fixed set of weighted decision axes; a concrete available 4B (Tier-1)
  and 8B (Tier-2) model identified per engine; a recorded decision document with
  the chosen engine, the measured numbers behind it, and the rationale.
- **Out:** the `ILLMProvider` implementation (HSM-5-02 — this story may build a
  throwaway probe per engine, not the production provider). The model
  packaging/download path (HSM-5-03). Structured-output plumbing (HSM-5-04 — but
  structured-output *support* is one of the axes evaluated here).

## Acceptance criteria

> **Superseded by the owner's no-spikes directive (2026-06-19):** the two
> *measured-bake-off* criteria below are replaced by a banked decision from the
> research canon. On-device behavior is validated implicitly in HSM-5-02 (re-open
> this story if it disappoints). The model-availability + named-engine + recorded-
> decision criteria still hold and are met.

- [~] ~~Decision axes fixed and weighted before measurement~~ — **superseded**:
      no pre-implementation measurement gate (owner directive). The canon's axes
      (model availability, Metal maturity, structured-output, integration cost)
      still framed the decision — see "Decision".
- [~] ~~Each of the three engines run on real Tier-1 hardware, numbers recorded~~
      — **superseded** (no bake-off). The chosen engine is exercised on-device in
      HSM-5-02; failure re-opens this story (risk register stop-signal).
- [x] A concrete, currently-available 4B and 8B model is named — `Llama-3.2-3B`
      (Tier-1) + `Llama-3.1-8B` (Tier-2) Q4_K_M GGUF (see "Decision").
- [x] One engine is chosen and written up with the rationale + the trade-off
      accepted (reversibility behind `ILLMProvider`; MLX as the fallback) —
      recorded here + as a "Decisions made" entry in `current-phase-status.md`.
- [ ] The Phase-0 deferred Track-F decision is marked resolved (cross-referenced
      from Phase 0's "Decisions deferred").

## Test plan

- Manual / device: run each engine's 4B probe on a Tier-1 device; capture
  sustained throughput, peak memory, and a thermal observation per run.
- Manual: feed each engine a structured-output prompt and record whether it can
  return JSON conforming to a Phase-0 schema (and via what mechanism — grammar,
  constrained decoding, or prompt-only).
- Unit: n/a (decision deliverable; the probes are throwaway).

## Notes / open questions

- **Grounded by [`../research/inference-on-apple.md`](../research/inference-on-apple.md)**
  (owner's brief, 2026-06-18): the in-app candidate set is exactly the three here
  — **Core ML / llama.cpp+GGUF / MLC-LLM**. **Ollama and vLLM are NOT in-app
  candidates** — they are Mode-B/C server companions (they belong to the homelab/
  endpoint providers and Phase-10 sync targets, not the on-device `ILLMProvider`).
  The brief's perf/feasibility tables are planning estimates this story replaces
  with real Tier-1 numbers.
- **iOS-18 floor for the Core ML candidate:** Core ML KV-cache persistence uses
  `MLState` (iOS/iPadOS 18+). If Core ML wins, it sets the deployment-target floor
  — reconcile with Phase 1's deferred minimum-deployment-target decision.
- This resolves Phase 0's deferred Track-F decision. If no engine has a
  production-ready 4B Apple-silicon build, that is itself a finding — surface it
  to the owner rather than picking a non-viable engine.
- Per the program's measurement posture, weight the axes and pick — do not turn
  this into an open-ended benchmark marathon. The phase risk table names the tie
  stop-signal: a weighted tie escalates to the owner with data.
- Thermal and memory headroom feed directly into HSM-5-03's default sizing and
  HSM-5-05's Gate-4 feasibility — record sustained behavior, not best-case bursts.
