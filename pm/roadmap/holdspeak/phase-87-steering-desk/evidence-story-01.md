# Evidence - HS-87-01

- **Story:** HS-87-01 - Attach: the session pull-out with the live pane view
- **Status:** done
- **Date:** 2026-07-07

## Proof

### Captured run — 2026-07-08T03:22:26Z

- **Command:** `uv run pytest -q tests/unit/test_coder_steering.py tests/unit/test_web_routes_coders_peek.py tests/integration/test_coder_steering_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6b68087fee592f4ae67670a8f98f7c20e44d5022

```text
...........................                                              [100%]
27 passed in 1.38s
```

### Captured run — 2026-07-08T03:22:40Z

- **Command:** `bash -c cd web && npm run test:desk`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6b68087fee592f4ae67670a8f98f7c20e44d5022

```text

> holdspeak-web@0.0.1 test:desk
> vitest run src/desk


 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  7 passed (7)
      Tests  70 passed (70)
   Start at  21:22:40
   Duration  184ms (transform 479ms, setup 0ms, import 561ms, tests 57ms, environment 0ms)
```

### Captured run — 2026-07-08T03:22:48Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6b68087fee592f4ae67670a8f98f7c20e44d5022

```text
ssssssssssssssssssssss...ssssssssss..................................... [  2%]
...............................................................s........ [  4%]
........................................................................ [  6%]
.......................ss............................................... [  8%]
........................................................................ [ 10%]
........................................................................ [ 12%]
........................................................................ [ 14%]
........................................................................ [ 17%]
........................................................................ [ 19%]
........................................................................ [ 21%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 36%]
........................................................................ [ 38%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 55%]
........................................................................ [ 57%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 96%]
........................................................................ [ 98%]
..............................................................           [100%]
=========================== short test summary info ============================
SKIPPED [1] tests/e2e/test_dictation_learning_digest_spoken_e2e.py:33: opt-in: set HOLDSPEAK_SPOKEN_DICTATION_E2E=1 to run the spoken-dictation learning-digest e2e (uses macOS `say` + the Whisper base model)
SKIPPED [1] tests/e2e/test_spoken_meeting_e2e.py:41: opt-in: set HOLDSPEAK_SPOKEN_E2E=1 to run the spoken-meeting e2e
SKIPPED [1] tests/e2e/test_dictation_enrichment_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation enrichment e2e
SKIPPED [1] tests/e2e/test_dictation_journal_e2e.py:57: set HOLDSPEAK_DICTATION_E2E_BASE_URL + HOLDSPEAK_DICTATION_E2E_MODEL to a reachable OpenAI-compatible endpoint to run the real dictation journal e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:44: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:52: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [12] tests/e2e/test_dogfood_plumbing_e2e.py:66: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_dogfood_plumbing_e2e.py:85: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [3] tests/e2e/test_dogfood_plumbing_e2e.py:95: set HOLDSPEAK_DOGFOOD=1 to run the dogfood plumbing e2e
SKIPPED [1] tests/e2e/test_meeting_transcription.py:86: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:120: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:147: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:190: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:210: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:340: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:372: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:389: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:410: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/e2e/test_meeting_transcription.py:438: Mock meeting fixture not found: /Users/karol/dev/tools/HoldSpeak/tests/fixtures/mock_meeting.wav
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
3339 passed, 37 skipped in 261.63s (0:04:21)
```
