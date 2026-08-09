# HS-131-05 — Workbench work and memory cannot outrun cancellation

- **Project:** holdspeak
- **Phase:** 131
- **Status:** backlog
- **Depends on:** HS-131-02, HS-131-03
- **Unblocks:** HS-131-06, HS-131-10
- **Owner:** unassigned

## Problem

A manual Workbench run creates a native run record but calls the model directly.
After a successful item call it may invoke a second model for memory writeback,
which is invisible as a separate consequence. Cancellation updates durable
state after the fact and can still allow late model output to mint work or
memory.

## Scope

### In

- Admit one parent Workbench attempt for manual execution through
  `holdspeak/services/workbench_service.py:155-165` and
  `holdspeak/workbench_conductor.py:421-679`.
- Route the item-generation call at `workbench_conductor.py:563-568` through the
  runner as one child and the memory-writeback call at `:603-623` as a distinct
  child. Never hide the second invocation inside the first receipt.
- Preserve Workbench item, attempt, memory, and history records as native domain
  projections that reference their operation and receipt IDs.
- Thread cancellation and deadline through active provider work. A cancelled
  parent stops queued children, cancels the active child, and atomically blocks
  item output and memory writeback from late completion.
- Keep manual owner gestures as the existing approval source. The kernel derives
  principal and authority; the Workbench service does not self-approve as the
  owner.
- Keep target precedence from Phase 130 and execute the admitted deployment
  revision exactly.

### Out

- Scheduled Workbench authority. HS-131-06 owns delegation.
- Workbench UI redesign, Agent/skill ownership, or general capability hosting.
- Memory model or prompt redesign.

## Acceptance criteria

- [ ] One manual Workbench attempt has one authenticated parent operation.
- [ ] Each item-generation provider call has one admitted child and one terminal
  receipt.
- [ ] Each memory-writeback provider call has its own admitted child and terminal
  receipt, causally linked to the parent and source item child.
- [ ] A Workbench with memory disabled creates no memory child.
- [ ] Cancelling before item completion leaves no item output and no memory;
  cancelling after item completion but before memory completion preserves the
  item and refuses or cancels the memory child without a late write.
- [ ] Repeated cancellation is idempotent; it cannot cancel another Workbench or
  change an immutable terminal receipt.
- [ ] Native Workbench attempt/history reads can resolve their kernel operation,
  child invocations, and terminal receipts.
- [ ] Manual execution contains no direct model call outside the runner.

## Test plan

- Unit: focused Workbench service/conductor tests plus
  `uv run pytest -q tests/unit/test_workbench_triage_kernel.py tests/unit/test_inference_kernel.py`.
- Integration: focused cases from `tests/e2e/test_workbench_walk.py` for one item,
  memory writeback, cancellation timing, and receipt linkage.
- Manual / device: run a manual Workbench item against the LAN model, inspect the
  item and memory children, then cancel during each stage.

## Notes / open questions

The Workbench parent is a domain attempt, not a substitute for invocation
children. The memory call is a real model invocation even when the user never
sees it as a separate card.
