# Evidence - HS-122-10

- **Story:** HS-122-10 - Desk doctor
- **Status:** done
- **Date:** 2026-08-06

## Proof

### Captured run — 2026-08-07T00:04:50Z

- **Command:** `uv run pytest -q tests/ -k doctor`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cb953bb05078736a6b942ad57d9f7c6729af8131

```text
...................................................................      [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
67 passed, 2 skipped, 4584 deselected in 5.09s
```

### Captured run — 2026-08-07T00:05:43Z

- **Command:** `uv run python -c from holdspeak.doctor import run_doctor`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cb953bb05078736a6b942ad57d9f7c6729af8131

```text
(no output)
```
