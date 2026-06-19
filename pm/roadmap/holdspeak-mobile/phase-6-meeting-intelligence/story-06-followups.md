# HSM-6-06 — Follow-ups

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** blocked
- **Depends on:** HSM-6-01, HSM-6-02, **a `follow_up` artifact-type contract decision**
- **Unblocks:** —
- **Owner:** unassigned

## Problem

The charter's Vision lists **Follow-ups** among the intelligence a meeting should
yield (the aftercare-flavored output: open threads / next actions to chase). Split
from HSM-6-03 because it cannot ship as a mobile-only change.

## Blocker — a cross-runtime contract decision

`artifact_type` is a **closed enum** in `contracts/schemas/artifact.schema.json`
(the 15 shipped desktop types + `plugin_output`), sourced from the desktop's
`plugins/synthesis.py _ARTIFACT_TYPE_BY_PLUGIN`. **There is no follow-up type.**
Modeling Follow-ups as an `Artifact` (the phase default) therefore requires adding
a `follow_up` type across:

1. the desktop parity source (`synthesis.py`),
2. `artifact.schema.json` (the enum),
3. the Swift `ArtifactType`,
4. the golden fixtures + the Python validator.

The owner has confirmed cross-runtime work is in scope (we build the server sync
API too — see the program memory / Phase 10), so this is unblockable; it is parked
only by sequencing (**finish Phase 6 core, then the sync thrust**). Pick this up
when the cross-runtime contract pass happens (alongside or after the sync API).

## Scope (when unblocked)

- **In:** add the `follow_up` artifact type cross-runtime (keeping desktop/mobile
  parity), then generate Follow-ups as `Artifact(.followUp)` — each referencing the
  open thread it tracks (provenance) — with round-trip validation and the
  "no fabrication / empty when none" guarantee, on the HSM-6-01 seam.
- **Out:** acting on follow-ups (Propose→Approve→Execute — emit only); the desktop
  aftercare/digest surface; UI.

## Acceptance criteria (draft)

- [ ] A `follow_up` artifact type exists and validates in BOTH runtimes (the Python
      validator + the Swift `swift test`), with the golden fixtures updated.
- [ ] Follow-ups generate from a real transcript and validate against the Phase-0
      `Artifact` contract with zero schema errors.
- [ ] Each references the open thread it tracks; none is fabricated.
- [ ] Substance-tested (coverage), not string-matched.

## Notes

- Default to modeling as an `Artifact` subtype per the Phase-0 contract.
- Pairs with MIR aftercare routing (later) — keep extraction profile-agnostic.
