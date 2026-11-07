# S90 Verify and hand off the completed vision

**Historical draft, not the current backlog.** Detailed planning has resumed in the [HS- hierarchy](../EXECUTION_INDEX.md); this earlier outline remains unapproved reference material and grants no implementation permission.
Parent epic: [E90 Establish the integrated result](../epics/E90-validation.md)

## User outcome

As the receiving owner or agent, I can understand exactly what is built, what was tested and what remains without reading the development conversation.

## Bounded context for a future assigned concern

Use [Agent start](../AGENT_START.md) for common safety and the linked parent epic for this story's intended outcome. A future task must name only the relevant invariant IDs, contract/implementation anchors, source sections and proving tests. Do not impose whole-package reading on an agent doing one local change. Task briefs are not yet authored; [user direction](../DECISIONS.md) is pending.

## Reserved task outline not authorized for execution

- `T90` — reserved only; task not authored

Keep characterization and implementation in the same isolated lane when a target regression test is intentionally red before the fix. Do not merge an intentionally red intermediate test-only change. The current fast-cycle workflow governs authorized shipping, not a new per-task process ceremony.

## Acceptance

Integration evidence must establish only the outcomes eventually accepted and revised by the user; open gates must be closed or explicitly blocked, and no unperformed ship/deploy/live action may be claimed.

The task reports must identify the tested SHA/diff, exact commands, collection output/run tails and unknowns. Source inspection is not a test pass. [Completion report](../COMPLETION_REPORT_TEMPLATE.md).

## Scope and rollback

No shipping by implication and no full-suite or live-provider expansion. Preserve unrelated edits. If a prerequisite or invariant cannot be met, stop dependent work and report the smallest necessary decision. Do not widen the story into generic framework work.
