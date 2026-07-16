# HS-94-07 progress record — Remote factory and Story-bound agent launch

**Captured:** 2026-07-16<br>
**Acceptance status:** done at the owner-rescoped scope (the cross-machine
launch over a second physical node is BACKLOG candidate Y; atomicity,
guards, and rollback are machine-verified with real git worktrees).

## What shipped

- Agent Profiles (`~/.holdspeak/agent_profiles.json`,
  `agent_profiles_schema:1`): node-configured argv templates with a fixed
  executable from a known allow-list (claude, codex) and allow-listed
  option slots. A client references profile_id + options only; an
  executable, argv, shell, env, or worktree path from the client is refused
  by name.
- `worktree.create` as a distinct typed command (additive to the HS-94-06
  envelope) with its own receipt and rollback; out-of-root/duplicate/dirty/
  injection refuse pre-execution.
- `agent.launch` atomicity: worktree.create → factory.spawn → immutable
  target → exactly one WorkAttempt (kind=launch, exact) → launch receipt.
  On failure the created worktree/session are retained and named (never a
  silent orphan, never a surprise kill). The rider binds the real session
  onto the same attempt (reusing the HS-94-04 claim path, guarded by the
  exact-session unique index); no rider → starting→unknown
  (failed_to_register) with the terminal still openable and a late rider
  still able to recover.
- Remote discover/rename/kill by discovered generation, idempotent through
  the HS-94-06 envelope with joined node+hub receipts.
- Routes wired into the app sharing the terminal command service and target
  registry.

## Verification

16 new tests over real git worktrees (launcher exec stubbed through the
injectable runner): one-attempt-one-target-one-receipt, every client-smuggle
refusal, worktree-create rollback + recovery, all pre-execution guards,
launch-without-rider retention + late recovery, remote rename/kill
idempotency. Combined factory/launch/delivery/attempt lane 270 passed;
steering/coder 163 passed; full unit suite 3,195 passed; API surface
regenerated (332 routes).
Captured at close in [evidence-story-07](./evidence-story-07.md).
