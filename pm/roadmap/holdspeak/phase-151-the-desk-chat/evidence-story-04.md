# Evidence - HS-151-04

- **Story:** HS-151-04 - The turn route (threads API, refs frozen, abort, branch, keep)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T22:18:21Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/1d7c5de7-eeec-4b6e-927e-186a731078fc/scratchpad/home04 uv run pytest -q tests/unit/test_thread_service.py tests/integration/test_threads_api.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_one_path_census.py tests/unit/test_recipe_runner_migration.py tests/integration/test_phase143_agent_turn_adoption.py tests/integration/test_phase143_closeout_chaos.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ac821c50368a51d9ef06de0172b24e9c7df257a2

```text
........................................................................ [ 84%]
.............                                                            [100%]
=============================== warnings summary ===============================
.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: asyncio_mode

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: timeout

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/.venv/lib/python3.14/site-packages/_pytest/config/__init__.py:1464: PytestConfigWarning: Unknown config option: timeout_method

    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
85 passed, 4 warnings in 113.94s (0:01:53)
```

## Orchestrator triage (2026-08-29)

Read: 85 passed (17 unit `test_thread_service.py` incl. the ≥3-delta
monotonic-seq and DB==concatenation pins and the two M1 pins; 8
integration `test_threads_api.py` with the bus captured; the three
143 census tests; one_path census; the three files whose retired
`RecipeService.chat` tests were deleted). The builder's first pass
used the non-streaming `execute` and wrote one part — sent back;
`execute_stream` now lives on `RoutedInferenceCoordinator` beside
`execute` with identical bookkeeping. The two
`test_placement_provenance` reds the builder called pre-existing ARE
lines 33–34 of `phase-143-intelligence-router/assets/story-08-inherited-failure-baseline.txt`.
Compaction-cut seam exists without a cut (DC-03).
