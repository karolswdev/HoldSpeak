# HSM-5-01 — Engine evaluation & pick

- **Project:** holdspeak-mobile
- **Phase:** 5
- **Status:** backlog
- **Depends on:** none
- **Unblocks:** HSM-5-02, HSM-5-03, HSM-5-04, HSM-5-05
- **Owner:** unassigned

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

- [ ] The decision axes are fixed and weighted before measurement, and at minimum
      cover: sustained (not burst) Tier-1 throughput at the 4B and 8B sizes,
      4B/8B model availability for Apple silicon, structured-output / constrained
      decoding support, and on-device integration cost.
- [ ] Each of the three engines is run on real Tier-1 hardware with a concrete 4B
      model, and the measured numbers per axis are recorded.
- [ ] A concrete, currently-available 4B and 8B model is named for each engine
      (or the absence is recorded as a disqualifier).
- [ ] One engine is chosen, and the choice is written up with the measured
      evidence and the trade-off accepted — recorded as a "Decisions made" entry
      in the phase's `current-phase-status.md`.
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
