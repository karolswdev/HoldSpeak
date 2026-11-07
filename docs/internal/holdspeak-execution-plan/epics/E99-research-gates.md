# E99 Resolve evidence gaps before proposing more code

**Historical draft, not the current backlog.** Detailed planning has resumed in the [HS- hierarchy](../EXECUTION_INDEX.md); this earlier outline remains unapproved reference material and grants no implementation permission.
Status: pending user direction; no implementation, task expansion or product test execution.

## Why this epic exists

Research hypotheses deserve bounded inspection, not implementation by assertion.

## Bounded context for a future assigned concern

Use [Agent start](../AGENT_START.md) for common safety. The eventual task should link the relevant section of the target/evidence, applicable invariant IDs, public contract, implementation entry point and proving tests—not require every package document. These precise task maps have not been authored. Current [user direction](../DECISIONS.md) remains pending, so this outline is not executable.

## Stories

- [S99 Keep uncertain findings separate from implementation](../stories/S99-discovery.md)

## Definition of done

Each question has source-backed findings, a testable reproduction plan and a recommendation or useful negative answer.

## Scope boundary

Discovery only; core delivery does not wait on these questions.

The package itself grants no repository mutation or shipping authority. Complete prerequisite reports before dependent implementation; current repository instructions and other lanes' ownership must be honored. Roll back only an authorized task-owned delta, never durable external effects or another lane's work. No tests have been run for this package.
