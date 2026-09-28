VERDICT: **DO-NOT-RATIFY** — PR #684 at `7119cfd9`.

FINDINGS:

1. **P1 — Publication replay still fails after terminal-storage rollback.** Publication commits before the new replay result and receipt. Injecting a failure in that terminal transaction leaves the update published, the operation claimed, and no `project_operation_results` row. The identical retry returns `409 published_update` and closes the operation refused. F5 is only partly paid. **Tenets 3/7.** Evidence: `holdspeak/services/project_kernel.py:299`, `holdspeak/services/project_update_service.py:2020`; [reproduction](/tmp/holdspeak-counsel-684-r2-publish-rollback.py), [result](/tmp/holdspeak-counsel-684-r2-publish-rollback.out).

2. **P2 — Self-closing operations bypass original-answer storage.** Through MCP, save policy A, save different policy B, then retry A: the response contains B’s terms with A’s original receipt. `_call` stores results only when the handle remains open; policy closes its own handle and reconstructs replays from current state. The HTTP policy route also discards `command_id`, creating another operation on retry. **Tenets 3/7.** Evidence: `holdspeak/services/project_kernel.py:297`, `holdspeak/services/steward_contract.py:150`, `holdspeak/web/routes/steward.py:169`; [MCP reproduction](/tmp/holdspeak-counsel-684-r2-policy.py), [result](/tmp/holdspeak-counsel-684-r2-policy.out).

3. **P2 — Deepest-first sorting does not settle every child before its parent.** Hold a real child after approval but before claim, then expire the parent. The reaper closes the parent while the child remains `awaiting_execution`, without a receipt: that branch checks the unclamped claim deadline. Releasing the child correctly refuses dispatch, so this probe demonstrates receipt-order failure, not an escaped effect. F2 remains partly unpaid. **Tenets 3/7; beat §3.** Evidence: `holdspeak/kernel/broker.py:253`, `holdspeak/kernel/liveness.py:26`; [reproduction](/tmp/holdspeak-counsel-684-r2-unclaimed-child.py), [result](/tmp/holdspeak-counsel-684-r2-unclaimed-child.out).

4. **P2 — The scheduler model-child obligation is not paid.** With a producer-minted deployment and the real inference runner, forcing the scheduled draft to request the model produces `declared_capability_required` before reaching the provider boundary. `_PROJECT_PATH` has ended before the service executes, while scheduler admission requires it. The captured-runner test cannot detect this. This is a latent obligation: today’s steward defaults to deterministic drafting. **Tenets 3/7; Article IX.** Evidence: `holdspeak/services/project_kernel.py:254`, `holdspeak/kernel/project.py:127`, `tests/unit/test_philo9_02_round_two.py:356`; [reproduction](/tmp/holdspeak-counsel-684-r2-scheduler-model.py), [result](/tmp/holdspeak-counsel-684-r2-scheduler-model.out).

**Two replay stores: yes.** A real `project.resource.add` stores identical response bodies in `project_commands.result_json` and `project_operation_results.result_json`, through separate transactions and replay paths. The duplication fails **Tenet 1** unless its distinct responsibility is justified; finding 1 demonstrates the unresolved transaction gap. [DB proof](/tmp/holdspeak-counsel-684-r2-two-stores.out).

**Paid:** r1 F1, F3, F4, F6, F7 and F8; ordinary publication retries; claimed-child deadline clamping; `run_once` admission; actual atlas observations. No new terminal-guard race reproduced.

Independent verification: [154 focused tests](/tmp/holdspeak-counsel-684-r2-focused.log), [141 regression tests](/tmp/holdspeak-counsel-684-r2-kernel.log), and [six glass tests](/tmp/holdspeak-counsel-684-r2-glass.log) passed. All four actual atlas cases passed on clean `7119cfd9`. All six committed shots were inspected. The old export reproduced **11 failures, four passes**. [Red log](/tmp/holdspeak-counsel-684-r2-red.log).

All seven original scripts were rerun. Six passed; the original start-replay script times out because its release depends on the retry returning. The corrected independent-release fence passes.

CONDITIONS:

- Close the replay gaps, including terminal rollback and self-closing operations; establish one authoritative answer per command.
- Settle approved descendants before their expired parent.
- Prove scheduler model admission through the real runner, or record a checked scope amendment.
- Fence these reproductions before merge. CI is not a condition.

MISSED:

Ranked by owner cost: committed publication reported refused; changed policy paired with an old receipt; premature parent closure; unproven scheduler model authority.

TUESDAY: **Not yet**—a retry can still misreport completed work or return policy terms that its receipt did not record.

UNKNOWN:

I did not rerun the full suite or all 39 mutations, send an external nudge, or exercise story 07 grants. Atlas cases were not run red.

The review worktree remains clean. The lane was clean at entry; subsequent non-shot edits are now staged there. Phase 168/169 shots are unchanged. I changed no reviewed source or evidence files.