# HSM-7-01 — Port the MIR routing engine

- **Project:** holdspeak-mobile
- **Phase:** 7
- **Status:** done (2026-06-19 — `IntentScorer` + `MIRRouter` + `RoutedArtifactGenerator`
  in RuntimeCore; deterministic, model-free; drives the Phase-6 engine. See
  [evidence-01](./evidence-story-01.md).)
- **Depends on:** HSM-6-01
- **Unblocks:** HSM-7-02, HSM-7-03, HSM-7-04
- **Owner:** unassigned

## Problem

Phase 6's artifact generation is one-size-fits-all. The desktop's value comes
from MIR (Meeting Intelligence Routing): the active profile plus per-window intent
scores decide which extraction emphasis runs. That routing decision has to live in
the mobile Runtime Core, ported from the MIR-01 canon, without dragging in the
whole desktop web-runtime feature.

## Scope

- **In:** the MIR routing decision in the Runtime Core (Layer 2): from
  `(active profile, per-window intent scores)` select the artifact emphasis /
  generation chains that drive Phase-6 generation. The deterministic intent
  signal extraction (matching desktop, no model dependency) sufficient to make the
  gate reproducible.
- **Out:** the artifact generators themselves (Phase 6). The five profiles'
  content (HSM-7-02). The host-facing profile picker (HSM-7-03 exposes the seam;
  Phases 8–9 build the screen). Full desktop fidelity of windowing / hysteresis /
  synthesis / DB lineage — port only what the Track H gate needs; park the rest as
  a parity follow-up.

## Acceptance criteria

- [ ] The routing engine runs inside the Runtime Core with no UI dependency and,
      given `(profile, intent scores)`, deterministically selects artifact
      emphasis / chains for fixed inputs — proven by a unit suite.
- [ ] The engine drives Phase-6 artifact generation (the selected emphasis
      actually changes what HSM-6-01 runs), not just returns a routing struct.
- [ ] Intent scoring uses the deterministic lexical extractor (matching desktop),
      keeping the gate reproducible — no reliance on the non-deterministic LLM for
      routing.
- [ ] The scope actually ported (vs. parked desktop machinery) is documented, so
      the parity follow-up is explicit.

## Test plan

- Unit: fixed transcript + fixed profile → deterministic emphasis selection; the
  selection demonstrably reaches the Phase-6 generator (a spy/fake confirms the
  chain changed).
- Manual: n/a (deterministic engine; the on-device proof is HSM-7-04).

## Notes / open questions

- The desktop MIR-01 is large (windows, hysteresis, plugin host, synthesis,
  lineage). Port the routing decision, not the web feature — timebox and file the
  long tail (phase risk + deferred decision).
- Routing stays deterministic on purpose: it keeps HSM-7-04's gate measurable.
