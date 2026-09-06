# HS-200-04: Make first value and model readiness work cold

- **Project:** holdspeak
- **Phase:** 200
- **Status:** in-progress
- **Depends on:** HS-200-02, HS-200-03
- **Unblocks:** HS-200-05, HS-200-11, HS-200-12, HS-200-40
- **Owner:** unassigned
- **Gate:** G0
- **Trace:** AA-IVW-013; AA-ENV-003; AC-03, AC-38; C1

## Problem

Useful AI depends on a compatible model route, but setup must preserve the user's first task and allow capture before AI is available.

## Scope

Prove and repair Concierge, assignment readiness, and return-to-task behavior through the existing first-value and Settings surfaces.

Implementation seams: ConciergeService; inference assignments; speech sessions; first-value Desk; SettingsCore; Interview/Thought handoffs.

Out: A replacement model library, provider survey, or model download without an actual chosen setup.

## Acceptance criteria

- [ ] A clean installation can dictate or enter text, edit, Copy, and Keep without a configured LLM.
- [ ] One supported route completes a real task probe and records its actual model and boundary.
- [ ] Missing files, unavailable endpoints, incompatible tools, and expired source credentials have exact recovery actions.
- [ ] Returning from setup preserves the unfinished task and refreshes readiness without reload or duplicated configuration.
- [ ] Configured fallbacks and failures follow the existing frozen-route contract.

## Test plan

Planned suites: phase200_first_value and phase200_readiness. Drive the real coordinator with adapter fixtures. Live: one selected model, one no-model case, and a failed prerequisite at both widths.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G0](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
