# Evidence - HS-166-07

- **Story:** HS-166-07 - The close (gates, riders, debts, final summary)
- **Status:** done
- **Date:** 2026-09-03

## Proof

### Captured run — 2026-09-03T08:33:28Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-07-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8f5b05688032da8468c6802dafcb570556a4d5e5

```text
=== FULL SUITE TOTALS (CI-style isolated HOME, -n auto) ===
13 failed, 7879 passed, 6 skipped in 773.10s (0:12:53)
6 failed, 1322 passed, 55 skipped in 483.27s (0:08:03)
=== MAIN BASELINE (run 33697563134 @ 493253d8):       24 names ===
=== BRANCH-NEW CANDIDATES ===
tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[1440]
tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]
tests/e2e/test_hs166_jira_walk.py::test_jira_live_walk[1440]
tests/e2e/test_hs166_jira_walk.py::test_jira_live_walk[393]
tests/integration/test_web_activity_api.py::test_connector_list_includes_calendar_with_capabilities
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest
tests/unit/test_inference_runner.py::test_deadline_unknown_provider_closes_indeterminate_before_dispatch_returns
tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current
tests/unit/test_project_mcp_commands.py::test_all_command_tools_discoverable
tests/unit/test_thread_tool_gate.py::TestClassificationCensus::test_every_mcp_tool_is_classified
=== CANDIDATES RE-RUN ON THE SETTLED TREE (isolated HOME; the live walk must SKIP here) ===
SKIPPED [1] tests/e2e/test_hs166_jira_walk.py:51: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
1 skipped in 1.33s
=== THE LIVE WALK ON THE SETTLED TREE (real HOME) ===
2 passed in 174.26s (0:02:54)
=== WEB ===
VERDICT: baseline-subset, zero branch-new
=== FLAKE PROOF: inference_runner deadline x2 ===
1 passed in 0.73s
1 passed in 0.71s
```

### Captured run — 2026-09-03T08:37:17Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-07-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8f5b05688032da8468c6802dafcb570556a4d5e5

```text
=== FULL SUITE TOTALS (CI-style isolated HOME, -n auto) ===
13 failed, 7879 passed, 6 skipped in 773.10s (0:12:53)
6 failed, 1322 passed, 55 skipped in 483.27s (0:08:03)
=== MAIN BASELINE (run 33697563134 @ 493253d8):       24 names ===
=== BRANCH-NEW CANDIDATES ===
tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[1440]
tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]
tests/e2e/test_hs166_jira_walk.py::test_jira_live_walk[1440]
tests/e2e/test_hs166_jira_walk.py::test_jira_live_walk[393]
tests/integration/test_web_activity_api.py::test_connector_list_includes_calendar_with_capabilities
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest
tests/unit/test_inference_runner.py::test_deadline_unknown_provider_closes_indeterminate_before_dispatch_returns
tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current
tests/unit/test_project_mcp_commands.py::test_all_command_tools_discoverable
tests/unit/test_thread_tool_gate.py::TestClassificationCensus::test_every_mcp_tool_is_classified
=== CANDIDATES RE-RUN ON THE SETTLED TREE (isolated HOME; the live walk must SKIP here) ===
SKIPPED [1] tests/e2e/test_hs166_jira_walk.py:51: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
1 skipped in 1.05s
=== THE LIVE WALK ON THE SETTLED TREE (real HOME) ===
1 failed, 1 passed in 164.15s (0:02:44)
=== WEB ===
VERDICT: BRANCH-NEW FAILURES: 1
=== FLAKE PROOF: inference_runner deadline x2 ===
1 passed in 0.72s
1 passed in 0.70s
```

### Captured run — 2026-09-03T08:44:57Z

- **Command:** `bash /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/6cc7cc4f-4f46-45dd-9e21-e76a98eaf6b9/scratchpad/story166-07-verify.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8f5b05688032da8468c6802dafcb570556a4d5e5

```text
=== FULL SUITE TOTALS (CI-style isolated HOME, -n auto) ===
13 failed, 7879 passed, 6 skipped in 773.10s (0:12:53)
6 failed, 1322 passed, 55 skipped in 483.27s (0:08:03)
=== MAIN BASELINE (run 33697563134 @ 493253d8):       24 names ===
=== BRANCH-NEW CANDIDATES ===
tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[1440]
tests/e2e/test_hs163_steward_glass.py::test_dogfood_run_and_dedup[393]
tests/e2e/test_hs166_jira_walk.py::test_jira_live_walk[1440]
tests/e2e/test_hs166_jira_walk.py::test_jira_live_walk[393]
tests/integration/test_web_activity_api.py::test_connector_list_includes_calendar_with_capabilities
tests/unit/test_api_surface.py::test_committed_manifest_matches_the_live_app
tests/unit/test_api_surface.py::test_committed_markdown_matches_the_manifest
tests/unit/test_inference_runner.py::test_deadline_unknown_provider_closes_indeterminate_before_dispatch_returns
tests/unit/test_kernel_effect_fence.py::test_effect_ledger_is_complete_and_current
tests/unit/test_project_mcp_commands.py::test_all_command_tools_discoverable
tests/unit/test_thread_tool_gate.py::TestClassificationCensus::test_every_mcp_tool_is_classified
=== CANDIDATES RE-RUN ON THE SETTLED TREE (isolated HOME; the live walk must SKIP here) ===
SKIPPED [2] tests/e2e/test_hs166_jira_walk.py:1636: acli jira auth status failed (exit 1): ✗ Error: unauthorized: use 'acli jira auth login' to authenticate
9 passed, 2 skipped in 22.31s
=== THE LIVE WALK ON THE SETTLED TREE (real HOME) ===
2 passed in 172.23s (0:02:52)
=== WEB ===
VERDICT: baseline-subset, zero branch-new
=== FLAKE PROOF: inference_runner deadline x2 ===
1 passed in 0.72s
1 passed in 0.70s
```
