VERDICT: RATIFY-WITH-CONDITIONS

FINDINGS:

1. **R4 is paid at charter level.** Child authority, policy bounds, revoke/expiry cutoff and run ownership are explicit pre-brief requirements; delivery exposure and admission land together in story 02; real-grant refusal belongs to story 07; return/orphan states require rendered fences; the close uses three sessions and includes story 07’s atlas cases. The checked design beats and canvases remain prerequisites to build. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:415`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-05-the-atlas-cases-for-the-room.md:18`.

2. **The delivery table is proportionate and lawful in shape — Tenet 1 satisfied.** Several confirmations require separate records. One additive table preserves published-update immutability, records confirmation time honestly and retains owner-only admission. I would not reopen the rulings or require another lifecycle engine. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:182`.

3. **A new delivery and a repeated confirmation remain insufficiently distinguished — Tenets 3/7.** The tool lists `command_id` and `idempotency_conflict`, but the acceptance criterion only proves “two marks give two rows.” It does not settle replay, concurrent duplicates, double-clicks or a lost response. Removing `already_delivered` makes that distinction necessary. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:129`, `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/story-02-the-steward-and-the-connectors-under-article-xi.md:47`. The kernel already identifies replay by principal and idempotency key: `holdspeak/kernel/journal.py:123`.

4. **The operation link needs enforceable semantics — Tenet 7; Articles V/XI.** `operation_id TEXT = …` does not specify a foreign key, non-nullness, uniqueness or transactional coupling. A reference alone also cannot guarantee that a delivery has its terminal receipt. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:182`. Existing machinery can commit the local insert, terminal state and receipt together: `holdspeak/kernel/journal_atomic.py:7`.

5. **The mistaken-mark behavior is explicit, with a real limitation.** It remains an ordinary delivery entry with time and To; adding the correct entry does not retract or identify the wrong one. DELIVERED ×N would count both confirmations. Undo is expressly parked, so I do not make building it a charter-merge condition. The canvas must show this limitation faithfully. Evidence: `pm/roadmap/holdspeak-philo/phase-9-the-room-on-the-contract/current-phase-status.md:183`, `pm/roadmap/holdspeak/BACKLOG.md:1331`.

CONDITIONS:

Before merging, add these contract clauses and their planned acceptance fences:

- One logical confirmation retains its `command_id` through double-clicks and retries. Same principal/key/payload returns the original delivery, timestamp, operation and receipt; changed payload refuses `idempotency_conflict`; a deliberate additional delivery uses a new key, including to the same recipient. Define omitted-key behavior. Fence concurrent replay, restart replay and the rendered pending/success transition.
- Require `operation_id NOT NULL UNIQUE REFERENCES kernel_operations(operation_id)`, supplied by execution context; derive `project_id` from the stored update. Preserve references without cascade deletion. Insert the delivery with terminal state and receipt in one transaction using the existing machinery. Fence rollback and replay.

These are charter amendments and build criteria, not demands to implement before charter merge.

MISSED:

1. Highest owner cost: an uncertain response or double-click can become an irreversible duplicate.
2. Next: a delivery row can outlive or lack the receipt promised as its provenance unless persistence is coupled.
3. Known limitation: adding a correct confirmation does not correct a mistaken one.

TUESDAY: Yes, conditionally—he can copy, return and record several deliveries; retries must preserve one confirmation, and mistaken marks remain visible.

UNKNOWN: Reviewed `0066bebc..5c3538ac` in fresh worktree `/Users/karol/dev/tools/wt-philo-p9-check-r5-5c3538ac`. `dw check holdspeak-philo` and `git diff --check` passed; worktree clean. No files changed. No runtime, browser, atlas or full-suite verification; the delivery implementation and canvases are not built.