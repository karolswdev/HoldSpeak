# HSM-0-04 — Conformance fixtures

- **Project:** holdspeak-mobile
- **Phase:** 0
- **Status:** backlog
- **Depends on:** HSM-0-02, HSM-0-03
- **Unblocks:** Phase 1 (the Swift types validate against these), Phase 10 (sync
  round-trips these)
- **Owner:** unassigned

## Problem

"The mobile runtime is compatible with desktop" must be testable, not asserted.
We need golden serialized examples that both runtimes are required to round-trip,
and a validator both can run, so a regression on either side fails loudly.

## Scope

- **In:** `contracts/fixtures/*.json` — a curated set of golden payloads covering
  every canonical entity and the realistic nesting (a full Meeting with
  Segments/Speakers/Artifacts/Actions across more than one MIR profile; an
  IntelJob in each lifecycle state; an Artifact carrying egress scope). A
  validator entry point (reusing HSM-0-02's script) that checks every fixture
  against the schema set and, where feasible, asserts round-trip stability
  (parse → re-serialize → byte/semantic-equal).
- **Out:** the Swift round-trip test itself (Phase 1 consumes these fixtures).
  Sync transport (Phase 10 reuses these fixtures as its payloads).

## Acceptance criteria

- [ ] At least one golden fixture per canonical entity, plus one full nested
      Meeting fixture for each MIR profile present in the desktop data.
- [ ] Every fixture validates against the HSM-0-02 schema set (validator output
      in evidence).
- [ ] Fixtures are derived from or checked against real desktop payloads, not
      hand-invented, where a desktop sample is obtainable.
- [ ] The validator is a single documented command both runtimes can run.

## Test plan

- Unit: run the validator over all fixtures → all pass; mutate one fixture to
  violate the contract → that fixture fails. Both in evidence.
- Manual: n/a.

## Notes / open questions

- These fixtures become the shared interop test bed for Phase 1 (Swift `Codable`
  round-trip) and Phase 10 (sync). Treat them as long-lived canon, not throwaway.
- Keep content realistic but synthetic enough to commit (no private meeting data).
