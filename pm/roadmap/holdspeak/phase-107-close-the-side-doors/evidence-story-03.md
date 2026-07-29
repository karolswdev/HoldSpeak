# Evidence - HS-107-03

- **Story:** HS-107-03 - The subprocess family — 5 sites
- **Status:** done
- **Date:** 2026-07-28

## Proof

### Captured run — 2026-07-29T05:22:34Z

- **Command:** `uv run pytest -q tests/unit/test_subprocess_exec_kernel.py tests/unit/test_gated_connector.py tests/unit/test_kernel_effect_fence.py tests/unit/test_dictation_commit_boundary.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2312cd8ddce8e3c8d2a039a0ae18584db27ce966

```text
.................................                                        [100%]
33 passed in 2.10s
```

### Captured run — 2026-07-29T05:23:03Z

- **Command:** `git diff --exit-code --stat -- holdspeak/kernel/broker.py holdspeak/kernel/admission.py holdspeak/kernel/journal.py holdspeak/kernel/model.py holdspeak/kernel/executor.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 2312cd8ddce8e3c8d2a039a0ae18584db27ce966

```text
(no output)
```

## Triage verdicts (the written arguments live in `holdspeak/kernel/subprocess_exec.py`'s module docstring)

- **C01** (`connector_runtime.py` `PermissionGate.run_subprocess`) —
  CONSEQUENTIAL: executes an arbitrary connector process under ambient
  machine authority. Migrated to `subprocess.exec@1`; the gate no
  longer performs its own permission decision for subprocess acts.
- **C02 / C03** (`gh` / `jira` enrichment) — READ: fixed metadata-view
  shapes. Receipt-free, but now require an authenticated owner
  principal and named `gh`/`jira` read authority.
- **C04** (`gated_connector.py` dispatch) — CONSEQUENTIAL: manifest
  permission and argv prefixes ride into kernel hard prerequisites;
  subprocess manifest checking is no longer a second policy decision.
- **C05** (`missioncontrol_bridge.py` `dw`) — READ: document views
  obtain information only; no admission ceremony on the conveyor;
  principal + named `dw`/`gh` read authority enforced.

## Live proofs (implementation session, this machine, 2026-07-29)

Recorded verbatim from the real-metal implementation session (temp
journals; full transcript in the story's assets is not required — the
closeout re-proves the beats). Highlights:

- **Real connector run with receipt read back:** op
  `op_676c8e1178f34d1287e549b0aa9a04ef` (`subprocess.exec`,
  principal `local-owner`), native receipt binds
  `argv=["/usr/bin/printf","connector-live-ok"]`,
  `process_outcome=exited_zero`, kernel receipt `rcpt_7ef589d7…`
  `succeeded`; stdout `connector-live-ok`.
- **Non-zero exit receipted as the distinction it is:** `/bin/sh -c
  "exit 7"` → operation outcome `succeeded`,
  `process_outcome=nonzero_exit`, `returncode=7`.
- **Indeterminate, not blindly retried:** `/bin/sleep 30` killed by
  timeout → operation state `indeterminate`, receipt
  `rcpt_dc36aad8…`, `INDETERMINATE_DISPATCH_COUNT=1`.
- **Argv immutability (Article XI clause 3):** the decision's argv
  source mutated to `"echo payload-swapped"` after approval; the
  journal and the actual execution retained the admitted
  `["/usr/bin/printf","immutable-ok"]`.
- **Agent-principal refusal by name:**
  `ReadSubprocessDenied: subprocess read 'gh' refused: principal
  'agent:untrusted' lacks read authority for 'gh'`.
- **Single decision proven:** exactly one `broker.decide` per migrated
  act; C01 has no `_require` call and one `run_subprocess_operation`
  dispatch; C04's `_route` has one `execute_subprocess` dispatch; the
  legacy `manifest.allows` branch is limited to `op.kind !=
  "subprocess"` (4-test census, all passing).

## Register reconciliation with HS-107-02 (merge-time, orchestrator)

HS-107-03 was implemented in parallel against the pre-02 register
(40/4/36) and landed after 02 (31/5/26). The composed truth, resolved
by hand and pinned exactly by the fence
(`test_effect_ledger_asserts_the_migrated_29_5_3_21_counts`):
**29 total / 5 covered (T01 T02 D09 N03 N04) / 3 reads (C02 C03 C05)
/ 21 debt**; families tmux 2, text_typer 1, subprocess 3, egress 13,
raw_desktop 10. C01/C04 removed with their migrations; nothing
loosened. Merged tree: unit 3397 passed, integration 749 passed.
