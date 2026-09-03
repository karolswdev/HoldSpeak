# Evidence - HS-166-03

- **Story:** HS-166-03 - The JiraWatchSource + templates + candidates (the gate graduates; the fetcher-seam rider)
- **Status:** done
- **Date:** 2026-09-02

## Proof

### Captured run — 2026-09-03T03:17:44Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-03-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c6f2990db84826ae66e4cec955139eb1c1a87d4a

```text
=== SCOPED (isolated HOME) ===
........................................................................ [ 97%]
..............                                                           [100%]
518 passed in 91.34s (0:01:31)
=== LIVE (real acli, real site; one harness transition, reverted) ===
connection: connected
rules set: 1
TEST: passed | provider: jira | connection: {'site': 'karolsaneapple.atlassian.net', 'email': 'karolsane+apple@gmail.com', 'connection_ref': 'karolsaneapple.atlassian.net|karolsane+apple@gmail.com'} | projects: ['KAN'] | n: 3 | calls: None
  jql: project in ("KAN") ORDER BY updated DESC
  rep: [(None, 'in progress', '2026-09-10'), (None, 'in progress', '2026-09-17'), (None, 'done', '')]
  transitions: ['jira.issue.discovered', 'jira.issue.assigned', 'jira.issue.status_changed', 'jira.issue.category_changed', 'jira.issue.priority_changed', 'jira.issue.due_changed', 'jira.issue.resolved']
BASELINE: established
EVAL-1 (no change): [('evaluated', 0, None, None)]
HARNESS: acli transition KAN-2: In Progress -> Done
   0 ✓ Work item KAN-2 has been successfully transitioned to Done
EVAL-2 (after transition): [('evaluated', 3, [{'id': 'weff_e1be146afd4a', 'evaluation_id': 'weval_13a873d7e2a4', 'rule_id': 'wrule_b7a1ac2047e6', 'action_kind': 'project.observe', 'target_ref': '', 'idempotency_key': '893ef822c47b6d182e0dafb01e4a4d2d', 'arguments_sha256': '', 'state': 'pending', 'operation_id': None, 'receipt_id': None, 'result_ref': None, 'verification_state': '', 'error_code': None, 'error_detail': None, 'created_at': '2026-09-03 03:19:43', 'completed_at': None}], None)]
   effects : ['project.observe']
EVAL-3 (unchanged): [('evaluated', 0, None, None)]
HARNESS REVERT: KAN-2: Done -> In Progress
   0 ✓ Work item KAN-2 has been successfully transitioned to In Progress
Traceback (most recent call last):
  File "/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/live166-03.py", line 47, in <module>
    assert o1[0]["transition_count"] == 0 and o2[0]["transition_count"] >= 1 and len(o2[0]["effects"]) == 1 and o3[0]["transition_count"] == 0, "LIVE PROOF FAILED"
           ~~~~~^^^^^^^^^^^^^^^^^^^^
KeyError: 'transition_count'
```

### Captured run — 2026-09-03T03:20:29Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-03-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** c6f2990db84826ae66e4cec955139eb1c1a87d4a

```text
=== SCOPED (isolated HOME) ===
........................................................................ [ 97%]
..............                                                           [100%]
518 passed in 93.41s (0:01:33)
=== LIVE (real acli, real site; one harness transition, reverted) ===
connection: connected
rules set: 1
TEST: passed | provider: jira | connection: {'site': 'karolsaneapple.atlassian.net', 'email': 'karolsane+apple@gmail.com', 'connection_ref': 'karolsaneapple.atlassian.net|karolsane+apple@gmail.com'} | projects: ['KAN'] | n: 3 | calls: None
  jql: project in ("KAN") ORDER BY updated DESC
  rep: [(None, 'in progress', '2026-09-10'), (None, 'in progress', '2026-09-17'), (None, 'done', '')]
  transitions: ['jira.issue.discovered', 'jira.issue.assigned', 'jira.issue.status_changed', 'jira.issue.category_changed', 'jira.issue.priority_changed', 'jira.issue.due_changed', 'jira.issue.resolved']
BASELINE: established
EVAL-1 (no change): [('evaluated', 0, None, None)]
HARNESS: acli transition KAN-2: In Progress -> Done
   0 ✓ Work item KAN-2 has been successfully transitioned to Done
EVAL-2 (after transition): [('evaluated', 3, [{'id': 'weff_542b20dcfa4c', 'evaluation_id': 'weval_75f3fe69c025', 'rule_id': 'wrule_35ceae93e033', 'action_kind': 'project.observe', 'target_ref': '', 'idempotency_key': '9507dd099f4e6d67a1b03c54136b13d4', 'arguments_sha256': '', 'state': 'pending', 'operation_id': None, 'receipt_id': None, 'result_ref': None, 'verification_state': '', 'error_code': None, 'error_detail': None, 'created_at': '2026-09-03 03:22:35', 'completed_at': None}], None)]
   effects : ['project.observe']
EVAL-3 (unchanged): [('evaluated', 0, None, None)]
HARNESS REVERT: KAN-2: Done -> In Progress
   0 ✓ Work item KAN-2 has been successfully transitioned to In Progress
LIVE PROOF DONE
```
