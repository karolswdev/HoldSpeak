# Evidence - HS-166-02

- **Story:** HS-166-02 - Discovery + search (projects, issue types, statuses, JQL; routes + MCP)
- **Status:** done
- **Date:** 2026-09-02

## Proof

### Captured run — 2026-09-03T02:47:43Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-02-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 14a329aa5bbfa254847093eaddc01e687f538175

```text
=== SCOPED (isolated HOME) ===
=========================== short test summary info ============================
SKIPPED [1] tests/unit/test_github_provider.py:526: gh CLI not authenticated or not installed
SKIPPED [1] tests/unit/test_github_provider.py:537: gh CLI not authenticated or not installed
274 passed, 2 skipped in 47.57s
=== LIVE (real acli, real HOME) ===
status: connected
projects: ready None [('KAN', 'WRONG', 'software'), ('SAM1', '(Example) Bi-annual Benefits & Wellness Updates', 'software')]
issue_types: enumerated [('Epic', False), ('Subtask', True), ('Task', False)]
statuses: observed [('Done', 'done'), ('In Progress', 'indeterminate')] categories: ['new', 'indeterminate', 'done']
search: ready None calls: 4 n: 3
   KAN-1 | In Progress / indeterminate | due: 2026-09-10 | res: None | upd: 2026-09-02T20:02:24 | assg: None
   KAN-2 | In Progress / indeterminate | due: 2026-09-17 | res: None | upd: 2026-09-02T20:02:25 | assg: None
   KAN-3 | Done / done | due: None | res: None | upd: 2026-09-02T20:02:26 | assg: None
count not-done: {'state': 'ready', 'error_code': None, 'error_detail': None, 'connection_ref': 'karolsaneapple.atlassian.net|karolsane+apple@gmail.com', 'count': 2}
bad jql: failed query_invalid | failed to parse JQL query: the value 'nope' does not exist for the field 'projec
validate: True WRONG ['Epic', 'Subtask', 'Task']
validate NOPE: False query_invalid
LIVE PROOF OK
```
