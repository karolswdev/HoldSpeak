VERDICT: DO-NOT-RATIFY

FINDINGS:

1. **P1 — A late worker resurrects a terminal run.** After expiry, the reaper sets the run to `interrupted` and its operation to `indeterminate`. Releasing the queued worker changes the run back to `running`; it reaches RECORD, while the receipt stays terminal. The next start refuses `active_run_exists`. The unconditional writes at `holdspeak/services/project_steward_service.py:573` and `:604` bypass the terminal winner. **Tenets 3/7; L4.** [Failing reproduction](/tmp/holdspeak-counsel-684-late.py), [result](/tmp/holdspeak-counsel-684-late.out).

2. **P1 — The parent closes before its child settles.** My probe produced a child deadline ten seconds later than its parent’s. Reaping then left the parent `indeterminate` and the child `claimed`; releasing the child subsequently created an update and recorded success. `holdspeak/kernel/broker.py:254` assigns an independent deadline; `holdspeak/kernel/liveness.py:18` reaps without descendant ordering. This violates the explicit beat at `docs/internal/philo/phase-9/steward-beat/README.md:181`. **Tenets 3/7; Articles VI/XI.** [Failing reproduction](/tmp/holdspeak-counsel-684-deadline.py), [result](/tmp/holdspeak-counsel-684-deadline.out).

3. **P1 — Triggered watch evaluation has no child admission.** `holdspeak/services/steward_contract.py:528` calls `evaluate_due` directly. A real Door-created watch reached the `gh pr list` runner, but the database gained only `project.steward.trigger`: no evaluation child or leaf receipt. The beat explicitly preserves watch evaluation’s admission. **Tenet 3; Article XI.2.** [Failing reproduction](/tmp/holdspeak-counsel-684-trigger.py), [result](/tmp/holdspeak-counsel-684-trigger.out).

4. **P2 — Concurrent start replay can expose an undurable handle.** Holding the first request between kernel claim and run insertion lets the identical retry return HTTP 200 with `success:true, run_id:null`, while the database contains zero runs. The original later returns a non-null run ID. `holdspeak/services/project_kernel.py:336` treats `claimed` as sufficient; `holdspeak/services/steward_contract.py:215` returns the missing row. **Tenets 3/7; L1.** [Failing reproduction](/tmp/holdspeak-counsel-684-run-replay.py), [result](/tmp/holdspeak-counsel-684-run-replay.out).

5. **P2 — Publication retries lose the original success and receipt.** Publish with a command key, then repeat the identical HTTP or MCP request: both retries return `published_update`, without the original operation or receipt. `_answer` calls the service again (`holdspeak/services/project_kernel.py:348`); `publish_update` attempts publication again (`holdspeak/services/project_update_service.py:2008`). The database operation remains succeeded. Thus the admitted replay contract is not closed as a class. **Tenets 3/7; Article VI.** [Failing reproduction](/tmp/holdspeak-counsel-684-publish.py), [result](/tmp/holdspeak-counsel-684-publish.out).

6. **P2 — Source addition creates false watch evidence.** Acceptance does persist the resource and watch together. However, the new path inherits `test_state="passed"` and `baseline_state="established"` from the setup helper (`holdspeak/services/project_service.py:2838`). My scanner-produced suggestion was accepted with zero provider calls, an empty snapshot, and null test time/result. **Tenet 3; Article VI.** Record the untested state honestly, or perform the corresponding admitted probe. [Failing reproduction](/tmp/holdspeak-counsel-684-source-state.py), [result](/tmp/holdspeak-counsel-684-source-state.out).

7. **P2 — B1 is incomplete in two branches.** The empty Jira card hardcodes “Not set up” (`web/src/pages/cores/connections/ConnectionsPane.tsx:319`), observed at [1440](/tmp/holdspeak-counsel-684-jira-empty-1440.png) and [393](/tmp/holdspeak-counsel-684-jira-empty-393.png). Also, removing `gh` from PATH changes a cached `connected` result to `unavailable` while retaining the old check timestamp (`holdspeak/services/github_provider.py:191`). That is not the last probe’s stored state. **Tenets 3/4; Article VI.** [Probe and rendered observations](/tmp/holdspeak-counsel-684-b1.out).

8. **P2 — A rewritten double weakens the account fence.** `tests/web/test_hs168_connections_routes.py:50` claims the cached producer stores no login; the real producer does. At `:230`, the former non-null account assertion becomes merely `"account" in conn`, accepting `None`. **Tenet 3; Article IX; scar 2.** Use the real probe producer and assert the returned account.

9. **The claimed closure exceeds the ratified implementation and evidence.** `evidence-story-02.md:38` explicitly parks model parentage, deadline clamping and `run_once` admission; these remain beat requirements. The atlas diff only moves two line anchors—no story-02 cases or actual atlas observations ship. `tests/unit/test_philo9_02_rig_op.py:26` exercises real operations, but is not an atlas-case run. **Tenets 3/7; Article IX.** Backlog entries alone do not amend the ratified beat.

Independent verification: **135 story tests passed**, including delivery rollback/FK/concurrent/restart checks, B2 with issued PROJECT credentials, F9, F20, source persistence and both supplied Connections viewports. **457 kernel/Phase 7 regression tests passed**; I found no reproduced desk deadlock from `BEGIN IMMEDIATE`. Seven selected fences fail meaningfully on `d05e0eb5`, including F20, B2, source addition and the journal race. [Story results](/tmp/holdspeak-counsel-684-focused.log), [kernel results](/tmp/holdspeak-counsel-684-kernel.log), [base failures](/tmp/holdspeak-counsel-684-main-red.log).

CONDITIONS:

- Fix findings 1–8 and add fences for the demonstrated interleavings, retries and rendered branches.
- Complete the remaining beat obligations, or obtain and record a checked scope amendment before claiming them closed.
- Supply actual story atlas cases and observations, then classify final-head CI.

MISSED:

Ranked by owner cost: a permanently occupied run slot; children acting after their parent’s terminal receipt; unreceipted watch effects; broken retry answers; manufactured watch health; incomplete connection states and weakened proof.

TUESDAY: No—the owner can be told a run ended yet be unable to start another, or see a successful publication reported as a failed retry.

UNKNOWN:

Grant-enabled agent children and revoke/expiry behavior belong to story 07 and remain unverified. No live external nudge send or model invocation was performed. I verified seven base failures, not every claimed red or all 28 mutations.

Reviewed **24576f25** in a fresh worktree; tracked files remain unchanged. The PR advanced to **aeae7bd8** during review. That newer head is not certified; the pinned head’s Unit, Integration and E2E CI jobs were still running at the last check.