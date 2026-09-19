# HS-200-21: Run a configured brief through an existing cadence

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-15, HS-200-17, HS-200-19, HS-200-20, HS-200-53
- **Unblocks:** HS-200-22, HS-200-23, HS-200-31, HS-200-33, HS-200-40
- **Owner:** unassigned
- **Gate:** G2
- **Trace:** AA-IVW-009–011; AA-AUT-001; AC-18, AC-35–36; C5, C9

## Problem

An installed recipe is useful when its trigger actually runs and its result returns to the Project.

## Scope

Bind one preparation or update recipe to the existing appropriate scheduler and result projection.

Implementation seams: the Workbench cron clock — `workbenches.schedule` (`holdspeak/db/schema.py:1714-1716`) ticked at `holdspeak/workbench_conductor.py:544` into `WorkbenchRunner.run_scheduled` (`holdspeak/services/workbench_runner.py:342`) under an owner-minted schedule delegation (`holdspeak/services/schedule_delegation.py:50-58`); the connector-watch interval swept by `HeartbeatService.run_sweep` for change-driven firings; the Steward as an effect drainer; recipe binding; Project result projection.

Out: General autonomous workers or an uninterrupted overnight guarantee before G4.

## Acceptance criteria

- [ ] The configuration names its actual scheduler, trigger, time zone, execution owner, and output.
- [ ] Run now and one actual scheduled occurrence produce linked results and receipts.
- [ ] Last run, next trigger, failure, and paused states reflect persisted owner records.
- [ ] Missing sources or models produce bounded recovery and partial-result semantics.
- [ ] Duplicate ticks cannot create unexplained duplicate local outputs under the existing scheduler's supported contract.

## Test plan

Planned suite: phase200_recurring_brief. Integration: actual scheduler with injected time, duplicate tick, failed source, disabled task. Live: one scheduled occurrence on the available hub.

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

**Amended 2026-09-18 (HS-200-47..53 cluster).** The seam line named "Heartbeat, Cadence, Steward" as the scheduler seams. Cadence is not a scheduler: it is a projection of open loops, and the product says so in its own tick — *"Cadence projections (attention only, never schedule)"*, `holdspeak/workbench_conductor.py:630`. The Steward drains effects and keeps no clock. The seams are corrected to the measured owners. The acceptance criteria are unchanged. **Ruled 2026-09-18 by the orchestrator.** This story's AC P200-A18 leg — one actual scheduled occurrence — is exactly what HS-200-53 proves, so a G2 story depends on G4 work. **21 is not re-gated:** the gates are the owner's charter and are not re-cut on the orchestrator's authority. Instead the consequence is stated where a reader meets the gate — G2's exit-criteria line in [current status](current-phase-status.md#exit-criteria-evidence-required) and its row in the [release gates](DELIVERY.md#release-gates) both now say that G2 cannot close before HS-200-53 lands.

This story targets [G2](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.
Inspect the selected integration revision before adding a new service or field.
Existing behavior can satisfy this story through fresh integrated proof.
