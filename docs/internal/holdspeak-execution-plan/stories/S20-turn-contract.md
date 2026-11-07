# S20 Own completion in ThreadService

**Historical draft, not the current backlog.** Detailed planning has resumed in the [HS- hierarchy](../EXECUTION_INDEX.md); this earlier outline remains unapproved reference material and grants no implementation permission.
Parent epic: [E02 Make interactive turn lifetime explicit](../epics/E02-thread-turns.md)

## User outcome

As an interactive caller, I can observe and await my turn through one public boundary without knowing how executors and persistence are managed.

## Bounded context for a future assigned concern

Use [Agent start](../AGENT_START.md) for common safety and the linked parent epic for this story's intended outcome. A future task must name only the relevant invariant IDs, contract/implementation anchors, source sections and proving tests. Do not impose whole-package reading on an agent doing one local change. Task briefs are not yet authored; [user direction](../DECISIONS.md) is pending.

## Reserved task outline not authorized for execution

- `T20` — reserved only; task not authored
- `T21` — reserved only; task not authored

Keep characterization and implementation in the same isolated lane when a target regression test is intentionally red before the fix. Do not merge an intentionally red intermediate test-only change. The current fast-cycle workflow governs authorized shipping, not a new per-task process ceremony.

## Acceptance

The public contract settles only after terminal persistence, has explicit detach/cancel semantics, and preserves existing route/start behavior.

The task reports must identify the tested SHA/diff, exact commands, collection output/run tails and unknowns. Source inspection is not a test pass. [Completion report](../COMPLETION_REPORT_TEMPLATE.md).

## Scope and rollback

No universal job runtime, automation-loop merge, new durable job schema or changed route policy. Preserve unrelated edits. If a prerequisite or invariant cannot be met, stop dependent work and report the smallest necessary decision. Do not widen the story into generic framework work.
