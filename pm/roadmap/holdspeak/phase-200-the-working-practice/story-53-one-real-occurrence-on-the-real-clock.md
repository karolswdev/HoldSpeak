# HS-200-53: One real occurrence, on the real clock, with a receipt

- **Project:** holdspeak
- **Phase:** 200
- **Status:** backlog
- **Depends on:** HS-200-47, HS-200-48, HS-200-49, HS-200-50, HS-200-51
- **Unblocks:** HS-200-21, HS-200-33, HS-200-36
- **Owner:** unassigned
- **Gate:** G4
- **Trace:** the 2026-09-18 scheduled-clock measurement on `ba48baf3` (two independent lanes); AC P200-A18; C9's "at least three real scheduled occurrences"

## Problem

**This has never happened. Not once, on any machine.**

`kernel_schedule_ticks` (`holdspeak/db/schema.py:1830-1834`) is the durable
record of a consumed due minute — one row per `(workbench_id, due_minute)`, the
primary key that makes a second tick a `duplicate_tick`
(`holdspeak/kernel/schedule_delegated.py:84-86`). On the owner's desk that table is
reported **empty** — a figure carried from the 2026-09-18 clock measurement's read of his real database, not measured by this lane, which read his real database. What this lane
measured directly is the tree: nothing in it exercises the path end to end. The whole
delegated-schedule apparatus — the owner-only mint, the
frozen terms, the SCHEDULER principal, the refusal receipts — has been shipped
and never exercised by the wall clock it was built for.

Everything before this story in the cluster is argued from source and proven
with injected time. Injected time cannot establish that the conductor thread is
running in the real hub process, that it survives a sleep, that the minute it
believes in is the minute the owner's clock shows, or that the receipt is
readable afterwards. HS-200-36 asks for three consecutive real occurrences and
a restart drill; it cannot start from zero. **This story is the first one.**

## Scope

Stand up one practice recipe on one Workbench, bound to one Project, on a real
cron schedule, on a real hub, and let the clock fire it unattended — then read
the occurrence, its receipt, and the record it produced.

Implementation seams: none in the product, if 47–51 landed correctly. This is a
proof story. Its artifacts are the run transcript, the receipt, the produced
record, and the shots of the Project surface showing them.

Out: three occurrences and the restart drill — that is HS-200-36, and this
story is its prerequisite, not its substitute. Out: enabling anything unattended
on the owner's real desk; the rig is the orchestrator's hub, with an isolated
HOME, and nothing writes to `~/.local/share/holdspeak/holdspeak.db`.

## Acceptance criteria

- [ ] A Workbench bound to one practice recipe and one Project carries an
      enabled cron schedule with an explicit zone and a LIVE owner delegation.
- [ ] The occurrence fires **from the wall clock**, unattended — no `run now`,
      no injected time, no manual dispatch. The evidence names the planned local
      minute and the observed one.
- [ ] `kernel_schedule_ticks` gains exactly one row for that minute, and a
      second tick on the same minute is refused as `duplicate_tick`.
- [ ] The declared execution owner ran: its own durable record exists, linked to
      the occurrence.
- [ ] The Project surface shows the result with its scheduler identity, route
      and receipt, shot at 1440 and 393
      (`feedback_screenshot_walk_before_claiming_ui_done`).
- [ ] A second schedule bound to a recipe whose compile returns an `unavailable`
      gap fires and **refuses**, with the gap on the receipt — the honest path
      is proven beside the happy one.
- [ ] The evidence states, in one sentence, what was NOT proven: coverage across
      a sleep, a restart, a DST boundary, and repetition. Those are HS-200-36's.

## Test plan

Wall-clock proof, not a test suite. Run a real hub from the built tree against
an isolated HOME and a seeded temporary database; set a schedule a few minutes
out; wait; read `kernel_schedule_ticks`, `kernel_receipts` and the produced
record through the product's own read paths. Keep the wall-clock transcript
separate from any injected-clock output
(`reference_live_walk_not_beside_parallel_suite`: never run this beside a
parallel suite — CPU starvation looks like a missed minute).

Use the [execution brief](EXECUTION.md#verification-commands) for isolated commands and the planned-test naming rule.
Update the affected public procedure with implemented behavior in the same PR.
Retain actual output in this story's evidence file when it ships.

## Notes / open questions

This story targets [G4](DELIVERY.md#release-gates).
The [technical contracts](CONTRACTS.md) and [acceptance protocol](ACCEPTANCE.md) define the shared invariants.

**Registry candidate (HS-200-46).** After this ships, one sentence becomes
assertable and must stay true: the delegated-schedule path has an exercised
end-to-end proof. Its predicate is the evidence file's existence and the
suite that replays the occurrence with injected time — the wall-clock leg
itself cannot be a CI predicate, and saying so is part of the entry.

**A walk, not a demo.** The owner's standing rule is that a walk writes nothing
to his desk (`reference_walk_seeds_in_real_db`). His attended leg — the same
occurrence on his own hub, on his pilot Project — is a separate ask and stays
open until he takes it.
