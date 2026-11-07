# HS-T00 · Establish the assigned execution baseline

**Status:** task specification complete; execution requires a named environment/role and authorized actions. Parent: HS-E00 / HS-S00 in the [ordered plan](../EXECUTION_INDEX.md). Unlocks only the specifically assigned contract/characterization task in the active hierarchy, not implementation. No code edits belong to this task.

## Mandatory context

Read [Agent start: authority and checkout safety](../AGENT_START.md#authority-and-checkout-safety), the assigned story's contract, [validation: setup and isolation](../VALIDATION.md#setup-and-isolation), and invariants [I16/I18](../INVARIANTS.md). Follow the actual current root/scoped repository instructions named by Agent start. Do not read the entire research library.

## Why

Research was pinned to `80b641fa41c7352280cfa52e933acf6dbe8d3857`; GitHub main matched it at 19:34 UTC on 3 November 2026. That is not evidence that today's assigned checkout, dependencies or test fixtures match. This task prevents applying a historical plan over new work or treating planning permission as execution permission.

## Procedure

1. Record assignment: task/story ID, role, permitted checkout/worktree, code/test/setup actions and shipping status. If absent, report the missing assignment and stop before repository mutation or test execution.
2. In the assigned checkout, use read-only inspection commands below. Record actual HEAD and comparison base. Inspect any dirty paths; preserve unrelated work and stop on overlapping or unexplained changes. Do not fetch/create/switch a worktree merely because the plan mentions one.
3. Read current `AGENTS.md`, `docs/internal/TWO-BRAINS.md`, `CLAUDE.md` current fast-cycle section, `pm/STATUS.md`, Constitution and the applicable scoped guides. Recheck for newly added guides/skills. Preserve current implementation/review roles; documentation planning is not a product-code lane.
4. Compare the assigned story's symbols, callers and tests with its pin. If only line numbers moved, update the task report. If behavior, authority or path ownership changed, reconcile the plan before dependent work. If the desired behavior is already implemented, prove that instead of redoing it.
5. Use the assigned task's exact V section as the single source of its tool, fixture, test-target and capture budget. Check only that slice's Python/uv, Node/npm, browser/local-server, Git/DW, encrypted-store or CLI prerequisites; do not install unrelated capabilities. Distinguish existing targets from proposed files correctly absent before implementation. Declared Python is >=3.10; pinned CI uses 3.12. Where browser proof is assigned, resolve this environment's installed cache and the repository wrapper's actual platform behavior, not an assumed macOS path. Setup requires its own authorized scope. HS-S24 is contract-only; optional characterization needs explicit test authority and cannot establish a runtime spending cap.
6. Inspect the assigned V section's real-local versus fake-effect boundary and actual fixtures before collection. Keep owner HOME/DB/Keychain, credentials, live providers/devices and remote repositories out of the run. Temporary local Git/DW or encrypted-store execution is still execution, not source reading; verify local remotes, injected keys/principals, disabled background effects and fail-closed provider seams as relevant. A fake GitHub-looking URL or isolated HOME alone is not network isolation. Preserve the slice's specific intercepted-versus-real browser mutations and allowed bookkeeping; do not replace them with a blanket claim that every operation is fake. Keep evidence outside temporary HOME and use separate directories for jointly assigned command unions.

**Read-only inspection commands, proposed execution checklist, not run during planning:**

```sh
git rev-parse --show-toplevel
git status --short
git rev-parse HEAD
git rev-parse origin/main
git diff --name-only
git diff --stat
```

A missing/stale `origin/main` is a reported baseline issue, not a reason to invent a comparison or silently fetch. Record a valid comparison commit under the assignment before integrated checks.

## Acceptance and handoff

Return a baseline report with assignment/role, actual root/worktree/HEAD/base, dirty-path ownership, current instruction differences, source drift, installed tooling/cache status, test-fixture isolation and exact allowed file/test/capture budget copied from the **assigned V section**, with existing versus proposed status intact. Record its section and task IDs so a successor can inspect the exact contract rather than a duplicated all-slice checklist. Name every missing prerequisite; source inspection is not successful collection or proof.

Include this report in the [portable handoff](../AGENT_START.md#one-portable-handoff-bounded-reading). This report unlocks the assigned contract/characterization task, not implementation or shipping; later tasks still need their own resolved local gate and assignment. Do not let an absent unrelated slice or historical analysis artifact block the selected outcome.

## Rollback and stops

No source or durable state change is intended. If an authorized setup step is needed, report it separately; do not modify package versions or machine settings to make the plan pass. Stop for missing authority, wrong checkout, overlapping dirty work, material drift, unavailable safe fixtures or required tooling. Report action, target, reason, completed work and pending/denied/uncertain status. Never clean or reset another lane.
