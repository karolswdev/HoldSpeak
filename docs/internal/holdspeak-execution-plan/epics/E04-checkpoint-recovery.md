# E04 Explain checkpoint recovery limits honestly

**Historical draft, not the current backlog.** Detailed planning has resumed in the [HS- hierarchy](../EXECUTION_INDEX.md); this earlier outline remains unapproved reference material and grants no implementation permission.
Status: pending user direction; no implementation, task expansion or product test execution.

## Why this epic exists

The owner must see that work continued even when an optional restart snapshot was not recorded, including handoff rows.

## Bounded context for a future assigned concern

Use [Agent start](../AGENT_START.md) for common safety. The eventual task should link the relevant section of the target/evidence, applicable invariant IDs, public contract, implementation entry point and proving tests—not require every package document. These precise task maps have not been authored. Current [user direction](../DECISIONS.md) remains pending, so this outline is not executable.

## Stories

- [S40 Show recoverability in both ledger branches](../stories/S40-recovery-ledger.md)

## Definition of done

Ordinary and handoff rows show truthful pin state/reason; intact-worktree pin failure remains nonblocking and leaves historical state unchanged.

## Scope boundary

Program-local projection only. No new schema, generic retry, auto pin repair or live Git probe on normal reads.

The package itself grants no repository mutation or shipping authority. Complete prerequisite reports before dependent implementation; current repository instructions and other lanes' ownership must be honored. Roll back only an authorized task-owned delta, never durable external effects or another lane's work. No tests have been run for this package.
