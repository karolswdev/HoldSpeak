# Phase 7 — MIR Port — final summary

**Closed:** 2026-06-19 (Track-H gate met). Track H of the Council Implementation Charter.

## Charter gate — PASSED

**Track H: profile changes measurably alter extraction.** A control-vs-treatment
run over one identical transcript, everything constant except the profile:
balanced vs architect produced an artifact-type **delta of `{action_items,
dependency_map, risk_register}`** (symmetric difference of the routed type sets).
Deterministic + reproducible. See [`evidence-story-04.md`](./evidence-story-04.md).

## What shipped

| Story | Outcome |
|---|---|
| HSM-7-01 | The MIR routing decision in RuntimeCore: `IntentScorer` (deterministic lexical scoring of MIR-01's five intents) + `MIRRouter` (profile + scores → ordered `ArtifactType` chain) + `RoutedArtifactGenerator` driving the Phase-6 engine. |
| HSM-7-02 | The five charter profiles (Balanced/Architect/Delivery/Product/Incident) with distinct per-profile artifact emphasis; each differs from Balanced. |
| HSM-7-03 | Profile seam on the Phase-0 contract (`Meeting.mirProfile` + `routingProfile` helper); round-trip proven. |
| HSM-7-04 | **Gate PASSED** (above). |

`swift test` **69 / 6 skipped (opt-in) / 0 failures**.

## Scope honored / parked

- Ported only the **routing decision** (charter Track H), model-free (lexical, not
  the LLM) so the gate is reproducible — the artifact generators themselves are
  Phase 6.
- **Parked desktop-fidelity follow-ups** (per Decisions deferred): rolling windows,
  hysteresis, intent-transition events, synthesis, lineage persistence, and
  per-window profile override (v1 is one profile per meeting). File as a parity
  story if/when a surface needs them.

## Decisions of record
- Routing is deterministic + lexical (MIR-F-006), one profile per `Meeting` for v1,
  carried on the contract field (no fork). Intent vocabulary is MIR-01's verbatim
  five (architecture/delivery/product/incident/comms).
