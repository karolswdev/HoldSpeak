# HS-200-06: Separate citation, factual support, and acceptance

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-01, HS-200-03
- **Unblocks:** HS-200-08, HS-200-10, HS-200-11, HS-200-12, HS-200-17, HS-200-24, HS-200-27, HS-200-40
- **Owner:** unassigned
- **Gate:** G1
- **Trace:** AA-CTX; AA-DEC; AC-05, AC-08; C2

## Problem

The current update parser can mark a sentence verified when it contains an existing reference. That state overstates what reference validation establishes.

## Scope

Implement C2 in the existing claim and update paths. Preserve provenance and conservatively interpret old records.

Implementation seams: holdspeak/services/project_update_service.py; existing claims serializers; update and artifact rendering.

Out: A universal automated truth oracle or acceptance granted by an LLM score.

## Acceptance criteria

- [x] A real but irrelevant citation cannot mark invented prose supported.
- [x] Observation, inference, proposal, and accepted domain decision remain distinct.
- [x] Support records identify their source versions and validation method or reviewer.
- [x] Editing a supported sentence invalidates support without deleting its provenance.
- [x] Existing citation-only verified records migrate conservatively, with readable historical meaning.

## Test plan

Planned suite: phase200_claim_support. Include irrelevant citations, mixed valid/invalid refs, altered figures, invented owners, edited prose, and old records. Live: inspect a generated Project update.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G1](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
