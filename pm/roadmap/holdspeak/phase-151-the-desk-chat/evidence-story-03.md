# Evidence - HS-151-03

- **Story:** HS-151-03 - The streaming seam (invoke_stream + typed deltas + frames)
- **Status:** done
- **Date:** 2026-08-29

## Proof

### Captured run — 2026-08-29T21:34:59Z

- **Command:** `env HOME=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/1d7c5de7-eeec-4b6e-927e-186a731078fc/scratchpad/home03 uv run pytest -q tests/unit/test_inference_runner_stream.py tests/unit/test_stream_cadence.py tests/unit/test_realtime_frame_registry.py tests/unit/test_chat_completion_deltas.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 02d9b34a6dd312764506d3cf384bc437094725de

```text
..................................                                       [100%]
=============================== warnings summary ===============================
../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_default_fixture_loop_scope
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: asyncio_mode
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

../../../../../../../../opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434
  /opt/homebrew/lib/python3.14/site-packages/_pytest/config/__init__.py:1434: PytestConfigWarning: Unknown config option: timeout_method
  
    self._warn_or_fail_if_strict(f"Unknown config option: {key}\n")

tests/unit/test_inference_runner_stream.py:27
  /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/tests/unit/test_inference_runner_stream.py:27: PytestUnknownMarkWarning: Unknown pytest.mark.timeout - is this a typo?  You can register custom marks to avoid this warning - for details, see https://docs.pytest.org/en/stable/how-to/mark.html
    pytestmark = pytest.mark.timeout(30, method="signal")

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
34 passed, 5 warnings in 6.70s
```

## Orchestrator triage (2026-08-29)

Read: 34 passed (6 runner-stream + 9 cadence + 8 engine-deltas/adapter
+ the frame drift test + the rest of that registry file). The first
builder pass stopped short of D3's provider half; sent back and closed
in-round (`_chat_completion_deltas`, `run_prompt_stream`,
`StreamingPromptAdapter`). The builder's "10 pre-existing failures" in
`test_one_path_spine.py` / `test_one_path_cardinality.py` are
verified-by-builder against clean code; the close sweep re-verifies
against the 143 baseline names. Frames sit in `EMITTED_WITHOUT_CONSUMER`
until 05 wires the pullout — honest, and the registry test enforces it.
