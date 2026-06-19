# HSM-6-03 — ADR Candidates

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** done
- **Depends on:** HSM-6-01, HSM-6-02
- **Unblocks:** HSM-6-04
- **Owner:** unassigned

> **Scope split (2026-06-19):** this story originally covered "ADR Candidates +
> Follow-ups". **Follow-ups** is split out to **[HSM-6-06](./story-06-followups.md)**
> because the Phase-0 `artifact_type` is a *closed, cross-runtime enum* (the 15
> shipped desktop types + `plugin_output`) with **no follow-up type** — adding one
> touches the desktop parity source, the schema, both runtimes, and the golden
> fixtures, which is a contract decision, not a mobile edit (owner call: ship ADR
> now, defer Follow-ups). ADR Candidates map to the existing `.adr` type, so they
> ship here.

## Problem

The charter's Vision lists ADR Candidates among the intelligence a meeting should
yield, beyond the five core types — the architecture-flavored output that makes
HoldSpeak useful to the developer audience the positioning targets.

## Scope

- **In:** generation of ADR (Architecture Decision Record) Candidates, modeled as
  an `Artifact(.adr)` per the Phase-0 contract (open `structured_json`); their
  extraction intent (an ADR candidate ties to a decision with architectural
  weight, referencing the decision context); round-trip validation.
- **Out:** Follow-ups (now **HSM-6-06**, blocked on a `follow_up` artifact-type
  contract decision). The five core types (HSM-6-02). The desktop aftercare/digest
  surface. UI. Acting on anything (Propose→Approve→Execute boundary — emit only).

## Acceptance criteria

- [x] ADR Candidates generate from a real transcript and validate against the
      Phase-0 `Artifact` contract with zero schema errors. (`Artifact(.adr)`
      round-trips through the contract coder — `testADRCandidatesValidate`.)
- [x] An ADR Candidate references the decision/architectural context it derives
      from (provenance per the contract): the artifact carries a transcript
      `ArtifactSource`, and each candidate a `source_timestamp` to the moment.
- [x] Does not fabricate: a transcript with no architectural decision yields no
      ADR candidate. (`testADRDoesNotFabricate` → empty `candidates`.)
- [x] Substance-tested (coverage), not string-matched.

## Test plan

- Unit: generation over an architecture-review transcript fixture → ADR
  candidate(s) present + schema-valid; over a transcript with no architectural
  content → none. **Done** (`ADRCandidatesTests`).
- Manual / device: spot-check on a real architecture-review recording — deferred
  to the device/parity pass (HSM-6-04/05).

## Notes / open questions

- Modeled as an `Artifact(.adr)` subtype per the Phase-0 contract (phase decision:
  default to Artifact types). Pairs naturally with MIR's Architect profile
  (Phase 7), which will weight ADR candidates up — extraction stays
  profile-agnostic here.
