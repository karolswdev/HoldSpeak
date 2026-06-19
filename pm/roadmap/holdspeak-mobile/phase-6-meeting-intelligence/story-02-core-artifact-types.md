# HSM-6-02 — The five core artifact types

- **Project:** holdspeak-mobile
- **Phase:** 6
- **Status:** backlog
- **Depends on:** HSM-6-01
- **Unblocks:** HSM-6-04
- **Owner:** unassigned

## Problem

The engine (HSM-6-01) can produce contract-shaped output, but the charter names
five specific artifact types HoldSpeak meetings must yield: Action Items,
Decisions, Risks, Requirements, Summaries. Each has its own contract and its own
extraction intent; this story makes all five real.

## Scope

- **In:** generation for each of the five core types, each mapped to its Phase-0
  contract (`ActionItem`, `Decision`, `Risk`, `Requirement`, and the Summary
  artifact); the per-type prompt/extraction; round-trip validation per type.
- **Out:** ADR Candidates + Follow-ups (HSM-6-03). The parity bar (HSM-6-04/05).
  MIR profile weighting of these types (Phase 7 routes emphasis; this story makes
  the types exist). Any UI.

## Acceptance criteria

- [ ] All five types generate from a real transcript and each validates against
      its Phase-0 contract with zero schema errors.
- [ ] The engine emits nothing a contract can't hold (no stray fields); a type
      with no instances in a transcript yields an empty set, not a hallucinated
      one.
- [ ] Each type's extraction is a substance check in tests (presence/coverage of
      what's actually in the transcript), never an exact-string assertion.
- [ ] Provenance is carried where the contract supports it (e.g. a Decision/Action
      pointing at the transcript moment that justifies it), matching the desktop's
      shape.

## Test plan

- Unit: per-type generation over transcript fixtures → schema-valid output +
  substance coverage assertions; an empty-input case → empty sets, no
  hallucination.
- Manual / device: spot-check the five types on a real recorded meeting.

## Notes / open questions

- Coverage, not wording: the model phrases differently every run; assert that the
  decisions/actions actually present are captured, not their exact text.
- Keep the per-type prompts close to the desktop's intent so Phase-6 parity
  (HSM-6-04) is comparing like with like.
