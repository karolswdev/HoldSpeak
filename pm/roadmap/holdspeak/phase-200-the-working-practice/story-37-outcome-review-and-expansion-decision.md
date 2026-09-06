# HS-200-37: Review net value and decide the next investment

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-23, HS-200-30, HS-200-36
- **Unblocks:** HS-200-39, HS-200-40
- **Owner:** unassigned
- **Gate:** G5
- **Trace:** AA-NFR-007; AA-TRF-006; AC-22–24 as follow-on criteria; C12

## Problem

Usage and generated outputs do not establish that HoldSpeak improved the owner's work.

## Scope

Review the combined daily, supervised, and unattended evidence. Decide what to retain, repair, or expand.

Implementation seams: Local pilot data; ACCEPTANCE.md; earlier-roadmap disposition.

Out: Invented ROI, a general market-launch claim, or automatic expansion because a phase number is available.

## Acceptance criteria

- [ ] Report each recipe's usage, correctness, active effort, supervision cost, maintenance cost, and failures.
- [ ] Measure net time once per task and allocate shared setup costs once.
- [ ] Record at least two concrete examples of improved decision work or preserved follow-through, or report the outcome inconclusive.
- [ ] Expansion candidates identify a measured pain, proposed scope, owner, and decision trigger.
- [ ] Portfolio, native parity, extra connectors, and additional workers remain deferred unless evidence justifies a specific next commitment.

## Test plan

Owner evidence review with all attempts retained. Audit metric denominators and source support. No product suite is substituted for the usefulness decision.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G5](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
