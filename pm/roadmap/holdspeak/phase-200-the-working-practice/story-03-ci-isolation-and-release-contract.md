# HS-200-03: Make release checks isolated and actionable

- **Project:** holdspeak
- **Phase:** 200
- **Status:** done
- **Depends on:** HS-200-01
- **Unblocks:** HS-200-04, HS-200-05, HS-200-06, HS-200-07, HS-200-08, HS-200-40
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** AA-NFR-003; AC-01–03; C12

## Problem

Main has red unit and E2E jobs. A mixture of stale fixtures, environmental dependencies, and product failures cannot serve as release evidence.

## Scope

Build the current failure ledger and repair test isolation at the affected seams. Define the critical journey suite using real services with substituted external adapters.

Implementation seams: .github/workflows/test.yml; tests/conftest.py; existing isolated proof driver; schema and seed fixtures.

Out: Repairing every unrelated historical feature in one PR; silent test deletion or broad quarantine.

## Acceptance criteria

- [ ] Each baseline failure has a reproduced classification, owner, and repair destination.
- [ ] The critical journey fixture cannot open the owner database or depend on a developer model path.
- [ ] Schema, seed, and generated-contract fixtures are regenerated only from their authoritative source after behavioral review.
- [ ] Time-dependent tests inject time and zone explicitly; required dependencies are declared or correctly platform-scoped.
- [ ] CI reports the critical journeys separately. No assertion or required coverage is weakened to make a baseline pass.

## Test plan

Run the isolated critical journey subset locally and in CI. Include missing models, non-macOS execution, a fresh data root, and multiple workers where supported. Retain before/after failure identities.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G0](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
