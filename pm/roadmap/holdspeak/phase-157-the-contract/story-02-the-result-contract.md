# HS-157-02 - The result contract: envelope, typed errors, ID prefixes

- **Project:** holdspeak
- **Phase:** 157
- **Status:** in-progress
- **Depends on:** HS-157-01
- **Unblocks:** HS-157-05
- **Owner:** unassigned

## Problem

P0's exit is "schema/API names are agreed." Every later phase (the
Room's command contract API-001..003, the MCP family MCP-001..005,
the Watch effects) returns the same envelope: `result_kind`,
`project_id`, `project_revision`, `changed_refs`, typed
warnings/errors. If P1 invents these shapes ad hoc, Web and MCP
drift apart and the graduation promise breaks. Freeze the names now,
before any of them is implemented.

## Scope

- **In:** a typed contract module (e.g.
  `holdspeak/services/project_contracts.py`): the command result
  envelope shape, the closed `result_kind` vocabulary, the typed
  error codes (stale-revision conflict, idempotency conflict,
  not-found, validation, capability), and the ID prefixes from
  SRS_DOMAIN_DRIVER §4.1 (`pitem_`, `psrc_`, `pobs_`, `pprop_`,
  `prev_`, `pupd_`, `pchg_`, `pcmd_`, `pstpol_`, `pstrun_`,
  `pststep_`) as constants with generators/validators. A P0 contract
  doc (`docs/internal/project-rooms/CONTRACTS-P0.md` or a §-addition
  the suite prefers) recording the agreed names, each traced to its
  SRS requirement ID. Tests pinning the frozen names so a later
  rename is a deliberate suite amendment, not an accident.
- **Out:** implementing any command handler, revision column, or
  endpoint that USES the envelope — that is P1. No behavior change.

## Acceptance criteria

- [ ] The envelope fields, `result_kind` values, and error codes exist as typed constants and are asserted by tests; each name traces to an SRS requirement ID in the contract doc.
- [ ] All eleven ID prefixes from §4.1 have a generator + validator, tested (deterministic-prefix rules from the table respected in the generator signatures, even where determinism itself lands later).
- [ ] The contract doc is committed alongside the module and the SRS suite needs no contradicting edit — or the suite is amended in the same commit (README precedence rule).
- [ ] Zero branch-new; no runtime path imports change behavior.

## Test plan

- **Unit:** `tests/unit/test_project_contracts.py` (frozen names, prefix generators/validators, error-code table).

## Notes / open questions

- Keep it boring: constants, dataclasses/TypedDicts, validators. The value is that P1..P6 import names instead of inventing them.
