# Evidence - HS-125-04

- **Story:** HS-125-04 - Aftercare triage queue
- **Status:** done
- **Date:** 2026-08-07

## Proof

### Captured run — 2026-08-08T00:12:22Z

- **Command:** `uv run pytest -q tests/ -k aftercare -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4dd0fb80b4fd06d2ae00d58a5d891c330f008ac9

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 4712 items / 4666 deselected / 2 skipped / 46 selected

tests/integration/test_actuator_presence_broadcasts.py .                 [  2%]
tests/integration/test_decision_records.py .                             [  4%]
tests/integration/test_history_slack_surfaces.py ..                      [  8%]
tests/integration/test_presence_learning_aftercare_broadcasts.py ....... [ 23%]
.                                                                        [ 26%]
tests/integration/test_web_aftercare_file_issue.py .....                 [ 36%]
tests/integration/test_web_meeting_aftercare_api.py ......               [ 50%]
tests/integration/test_web_slack_export.py .                             [ 52%]
tests/unit/test_aftercare_triage.py .......                              [ 67%]
tests/unit/test_intel_process_aftercare_callback.py .                    [ 69%]
tests/unit/test_meeting_aftercare.py ..............                      [100%]

=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
=============== 46 passed, 2 skipped, 4666 deselected in 13.22s ================
```

### Captured run — 2026-08-08T00:14:04Z

- **Command:** `uv run pytest -q tests/ -k aftercare -v`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4dd0fb80b4fd06d2ae00d58a5d891c330f008ac9

```text
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
rootdir: /Users/karol/dev/tools/HoldSpeak
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
asyncio: mode=Mode.AUTO, debug=False, asyncio_default_fixture_loop_scope=function, asyncio_default_test_loop_scope=function
collected 4712 items / 4666 deselected / 2 skipped / 46 selected

tests/integration/test_actuator_presence_broadcasts.py .                 [  2%]
tests/integration/test_decision_records.py .                             [  4%]
tests/integration/test_history_slack_surfaces.py ..                      [  8%]
tests/integration/test_presence_learning_aftercare_broadcasts.py ....... [ 23%]
.                                                                        [ 26%]
tests/integration/test_web_aftercare_file_issue.py .....                 [ 36%]
tests/integration/test_web_meeting_aftercare_api.py ......               [ 50%]
tests/integration/test_web_slack_export.py .                             [ 52%]
tests/unit/test_aftercare_triage.py .......                              [ 67%]
tests/unit/test_intel_process_aftercare_callback.py .                    [ 69%]
tests/unit/test_meeting_aftercare.py ..............                      [100%]

=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
=============== 46 passed, 2 skipped, 4666 deselected in 15.37s ================
```
