# S00 Start from the current repository safely

**Historical draft, not the current backlog.** Detailed planning has resumed in the [HS- hierarchy](../EXECUTION_INDEX.md); this earlier outline remains unapproved reference material and grants no implementation permission.
Parent epic: [E00 Establish a safe current baseline](../epics/E00-baseline.md)

## User outcome

As an executing agent, I need a known checkout, authority and instruction set so my work does not overwrite another lane or revive stale design.

## Bounded context for a future assigned concern

Use [Agent start](../AGENT_START.md) for common safety and the linked parent epic for this story's intended outcome. A future task must name only the relevant invariant IDs, contract/implementation anchors, source sections and proving tests. Do not impose whole-package reading on an agent doing one local change. Task briefs are not yet authored; [user direction](../DECISIONS.md) is pending.

## Reserved task outline not authorized for execution

- `T00` — reserved only; task not authored

Keep characterization and implementation in the same isolated lane when a target regression test is intentionally red before the fix. Do not merge an intentionally red intermediate test-only change. The current fast-cycle workflow governs authorized shipping, not a new per-task process ceremony.

## Acceptance

A baseline report names current SHA, drift, ownership and safe test environment; no missing permission is treated as granted.

The task reports must identify the tested SHA/diff, exact commands, collection output/run tails and unknowns. Source inspection is not a test pass. [Completion report](../COMPLETION_REPORT_TEMPLATE.md).

## Scope and rollback

No product mutation; inspection only until an implementation assignment exists. Preserve unrelated edits. If a prerequisite or invariant cannot be met, stop dependent work and report the smallest necessary decision. Do not widen the story into generic framework work.
