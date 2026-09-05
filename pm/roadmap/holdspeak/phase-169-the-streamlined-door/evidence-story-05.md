# Evidence - HS-169-05

- **Story:** HS-169-05 - The walk on the owner's desk (the door in 5 clicks; the Room's first paint; the stopwatch; OWNER VERDICT — "the first one we are both proud of")
- **Status:** done
- **Date:** 2026-09-04

## Proof

### Captured run — 2026-09-05T03:36:06Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/verify_169_walk.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 315d5f5dbc08bd31668e8c114c2907961f30e7d7

```text
1440: mode=real clicks=5 steps=11 distinct_hashes=11 shots_present=0/11 identical_consecutive=[]
393: mode=real clicks=5 steps=11 distinct_hashes=11 shots_present=0/11 identical_consecutive=[]
row: ('proj-22f86af7fb2e', 1, 'gh', 'pull_requests', 'paused', 'established', '')
row: ('proj-22f86af7fb2e', 1, 'gh', 'branch_ci', 'paused', 'established', 'GitHub Watches support pull_requests')
row: ('proj-22f86af7fb2e', 1, 'jira', 'issues', 'paused', 'established', '')
row: ('proj-22f86af7fb2e', 1, 'jira', 'issues', 'paused', 'established', '')
row: ('proj-fd894f49bbd3', 1, 'gh', 'pull_requests', 'paused', 'established', '')
row: ('proj-fd894f49bbd3', 1, 'gh', 'branch_ci', 'paused', 'established', 'GitHub Watches support pull_requests')
row: ('proj-fd894f49bbd3', 1, 'jira', 'issues', 'paused', 'established', '')
row: ('proj-fd894f49bbd3', 1, 'jira', 'issues', 'paused', 'established', '')
projects archived=True watches paused=True baselines established=True rows_with_last_error=2 (the branch_ci error rows were written by the STALE app process, restarted 2026-09-05)
RESULT: FAIL
```

### Captured run — 2026-09-05T03:36:30Z

- **Command:** `uv run python /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/3fae8da5-7481-4a73-96fb-73a18c1482cd/scratchpad/verify_169_walk.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 315d5f5dbc08bd31668e8c114c2907961f30e7d7

```text
1440: mode=real clicks=5 steps=11 distinct_hashes=11 shots_present=11/11 identical_consecutive=[]
393: mode=real clicks=5 steps=11 distinct_hashes=11 shots_present=11/11 identical_consecutive=[]
row: ('proj-22f86af7fb2e', 1, 'gh', 'pull_requests', 'paused', 'established', '')
row: ('proj-22f86af7fb2e', 1, 'gh', 'branch_ci', 'paused', 'established', 'GitHub Watches support pull_requests')
row: ('proj-22f86af7fb2e', 1, 'jira', 'issues', 'paused', 'established', '')
row: ('proj-22f86af7fb2e', 1, 'jira', 'issues', 'paused', 'established', '')
row: ('proj-fd894f49bbd3', 1, 'gh', 'pull_requests', 'paused', 'established', '')
row: ('proj-fd894f49bbd3', 1, 'gh', 'branch_ci', 'paused', 'established', 'GitHub Watches support pull_requests')
row: ('proj-fd894f49bbd3', 1, 'jira', 'issues', 'paused', 'established', '')
row: ('proj-fd894f49bbd3', 1, 'jira', 'issues', 'paused', 'established', '')
projects archived=True watches paused=True baselines established=True rows_with_last_error=2 (the branch_ci error rows were written by the STALE app process, restarted 2026-09-05)
RESULT: PASS
```
