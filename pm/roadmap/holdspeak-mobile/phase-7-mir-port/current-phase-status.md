# Phase 7 — MIR Port

**Status:** planning (scaffolded 2026-06-18). Track H of the Council
Implementation Charter. Ports the desktop's Meeting Intelligence Routing
(MIR-01 canon, `docs/internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md`) into the
mobile Runtime Core (Layer 2), so the artifact generation Phase 6 stood up
becomes profile-driven instead of one-size-fits-all.

**Last updated:** 2026-06-18 (scaffolded — stories HSM-7-01..04 stubbed from
charter Track H and the MIR-01 canon; no work started).

## Goal

Port the profile-driven routing of MIR into the mobile Runtime Core so that the
active profile measurably shapes what the artifact generation extracts and
emphasizes from a meeting. The engine selects which plugin chains / artifact
emphasis run from the active profile plus the per-window intent scores, exactly
as the desktop's MIR-01 does, and drives the Phase-6 artifact pipeline. The five
charter profiles (Balanced, Architect, Delivery, Product, Incident) exist with
distinct emphasis, the profile selection rides on the `Meeting` per the Phase-0
contract, and the Track H gate is demonstrated: same input, different profile,
measurably different extraction.

## Scope

- **In:** the MIR routing engine ported into the Runtime Core, driving Phase-6
  artifact generation per profile (HSM-7-01); the five charter profiles with
  their per-profile artifact emphasis matching MIR-01's intent set
  (`architecture`, `delivery`, `product`, `incident`, `comms`) (HSM-7-02); the
  profile-selection settings/seam the host UI will drive, carried on the
  `Meeting` per the Phase-0 contract (HSM-7-03); the gate closeout — a
  control-vs-treatment demonstration that switching the profile measurably
  changes extraction over the same input (HSM-7-04).
- **Out:** the artifact generation itself (Phase 6 / HSM-6-01 — this phase
  routes it, it does not build it). The local-inference engine (Phase 5). The
  host UI that surfaces the profile picker (iPad = Phase 8, iPhone = Phase 9 —
  this phase exposes the seam, not the screen). The whole-meeting capture/audio/
  transcription stack (Phases 2–4). Any actuator execution (charter non-goal:
  Propose → Review → Approve → Execute is preserved; actuator plugins stay
  disabled by default per MIR-S-002).

## Exit criteria (evidence required)

- [ ] The MIR routing engine runs inside the Runtime Core (Layer 2, no UI
      dependency) and selects artifact emphasis / plugin chains deterministically
      from `(active profile, per-window intent scores)`, driving the Phase-6
      artifact generation — proven by a unit suite over fixed inputs (HSM-7-01).
- [ ] All five charter profiles (Balanced, Architect, Delivery, Product,
      Incident) exist with a documented, distinct per-profile artifact emphasis
      that maps onto MIR-01's intent set; a profile-emphasis test asserts each
      profile's emphasis differs from Balanced's (HSM-7-02).
- [ ] The active profile is carried on the `Meeting` per the Phase-0 contract and
      reachable through a Runtime-Core seam a host UI can read/write without
      touching the engine internals — proven by a round-trip test (HSM-7-03).
- [ ] **Track H gate:** profile changes measurably alter extraction. A
      control-vs-treatment run over one identical transcript input, holding
      everything constant except the profile, produces a measurably different
      artifact set (different artifact mix, counts, or emphasis ordering) across
      at least two profiles, with the metric and the delta recorded (HSM-7-04).

## Story status

| ID | Story | Status | Story file | Evidence |
|---|---|---|---|---|
| HSM-7-01 | Port the MIR routing engine | backlog | [story-01](./story-01-mir-engine-port.md) | — |
| HSM-7-02 | The five profiles | backlog | [story-02](./story-02-five-profiles.md) | — |
| HSM-7-03 | Profile-selection seam | backlog | [story-03](./story-03-profile-selection-seam.md) | — |
| HSM-7-04 | Profile-effect gate closeout | backlog | [story-04](./story-04-profile-effect-closeout.md) | — |

## Where we are

Just scaffolded. The desktop MIR-01 canon
([`../../../docs/internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md`](../../../../docs/internal/PLAN_PHASE_MULTI_INTENT_ROUTING.md))
defines the routing model (rolling-window multi-label intent scoring →
profile-driven plugin chains → synthesis), and Track H names the five profiles
the mobile port must ship. The four stories split the work: port the engine
(HSM-7-01, depends on Phase-6 artifact generation HSM-6-01), define the five
profiles' emphasis (HSM-7-02), expose the profile seam the host UI drives
(HSM-7-03, carried on the `Meeting` per Phase 0), and prove the gate with a
control-vs-treatment demonstration (HSM-7-04). Next: HSM-6-01 (Phase-6 artifact
generation) must exist before HSM-7-01 can route it; until then this phase is
blocked on its upstream.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
|---|---|---|---|
| Profiles end up cosmetic — same artifacts regardless of profile, gate fails | high | Build the gate's control-vs-treatment measurement (HSM-7-04) early and run it against the engine while it is still being shaped, not at the end | Two profiles over the same input produce identical artifact sets — halt; the routing is not actually reaching artifact generation, re-examine the HSM-7-01 wiring before adding more profiles |
| The desktop MIR-01 is a full web-runtime feature (windows, hysteresis, plugin host, synthesis, DB lineage); porting it whole blows the 2-week track | high | Port only the routing decision (profile + scores → emphasis/chains) needed to drive Phase-6 artifacts; treat windowing/synthesis/lineage persistence as desktop-fidelity to match only where the gate demands it, park the rest | The port keeps pulling in plugin-host/synthesis/lineage scope to compile — timebox; ship the minimal profile→emphasis routing that passes the gate, file the long tail as a follow-up story |
| Profile is stored somewhere other than the `Meeting`, breaking the Phase-0 contract | medium | HSM-7-03 carries it on the `Meeting` entity per the Phase-0 contract; cite the entity catalog (HSM-0-01) field | The seam needs a side-table or a runtime-only field the contract doesn't include — escalate to the contract (HSM-0-03), don't fork it |
| "Measurably different" has no agreed metric, so the gate becomes a vibe | medium | HSM-7-04 fixes the metric up front (artifact-type set diff, per-type counts, emphasis ordering) and records the baseline before treatment | The team can only argue the outputs "feel" different — stop; no metric means no gate, define it before claiming the gate is met |
| The intent set drifts from desktop (`architecture`/`delivery`/`product`/`incident`/`comms`) and breaks cross-runtime parity | low | HSM-7-02 maps the five charter profiles onto MIR-01's exact intent vocabulary verbatim | A profile needs an intent label not in the MIR-01 set — record as a proposed addition against the canon, do not silently invent |

## Decisions made (this phase)

- 2026-06-18 — This phase ports the *routing decision* (profile + intent scores →
  artifact emphasis / plugin chains) and wires it to drive Phase-6 artifact
  generation; it does not re-build the artifact generators themselves — charter
  Track H scopes "MIR Port", and Layer-2 separation puts generation in Phase 6.

## Decisions deferred

- How much of MIR-01's rolling-window / hysteresis / synthesis machinery the
  mobile port needs versus a simpler profile-driven emphasis selector — trigger:
  HSM-7-01 — default: port only what the Track H gate (HSM-7-04) requires; park
  full window/synthesis/lineage fidelity as a later parity story.
- Whether intent scoring on mobile reuses MIR-01's deterministic lexical signal
  extractor or leans on the local LLM (Phase 5) — trigger: HSM-7-01 — default:
  the deterministic lexical extractor (matches desktop, no model dependency, and
  keeps the gate reproducible).
- Whether a meeting may carry more than one profile over its timeline (per-window
  override, as MIR-F-007 allows on desktop) or a single profile per meeting for
  v1 — trigger: HSM-7-03 — default: one profile per `Meeting` for v1; per-window
  override parked.
