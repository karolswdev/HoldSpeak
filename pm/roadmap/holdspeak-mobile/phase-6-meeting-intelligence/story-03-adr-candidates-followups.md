# HSM-6-03 — ADR Candidates + Follow-ups

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** backlog
- **Depends on:** HSM-6-01, HSM-6-02
- **Unblocks:** HSM-6-04
- **Owner:** unassigned

## Problem

The charter's Vision lists ADR Candidates and Follow-ups among the intelligence a
meeting should yield, beyond the five core types. They are the architecture- and
aftercare-flavored outputs that make HoldSpeak useful to the developer audience
the positioning targets.

## Scope

- **In:** generation of ADR (Architecture Decision Record) Candidates and
  Follow-ups, modeled as `Artifact` types per the Phase-0 contract; their
  extraction intent (an ADR candidate ties to a Decision with architectural
  weight; a Follow-up ties to an open thread / next action); round-trip
  validation.
- **Out:** the five core types (HSM-6-02). The desktop aftercare/digest surface
  (that's a desktop feature; here we emit the artifact shapes). UI. Acting on
  follow-ups (Propose→Approve→Execute boundary preserved — emit only).

## Acceptance criteria

- [ ] ADR Candidates and Follow-ups generate from a real transcript and validate
      against the Phase-0 `Artifact` contract with zero schema errors.
- [ ] An ADR Candidate references the Decision/architectural context it derives
      from; a Follow-up references the open thread it tracks (provenance per the
      contract).
- [ ] Neither type fabricates: a transcript with no architectural decision yields
      no ADR candidate.
- [ ] The two types are substance-tested (coverage), not string-matched.

## Test plan

- Unit: generation over an architecture-review transcript fixture → ADR
  candidate(s) present + schema-valid; over a transcript with no architectural
  content → none. Follow-ups similarly over a transcript with open threads.
- Manual / device: spot-check on a real architecture-review recording.

## Notes / open questions

- Default to modeling these as `Artifact` subtypes per the Phase-0 contract until
  the contract says otherwise (phase decision deferred).
- These pair naturally with MIR's Architect profile (Phase 7), which will weight
  ADR candidates up — keep the extraction profile-agnostic here.
