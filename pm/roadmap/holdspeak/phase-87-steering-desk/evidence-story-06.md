# Evidence - HS-87-06

- **Story:** HS-87-06 - The robustness rig, the walk, the docs
- **Status:** done
- **Date:** 2026-07-07

## Proof

### Captured run — 2026-07-08T04:51:21Z

- **Command:** `uv run python scripts/steer_walk_hs87.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2ebbfafa41a5cc922f3f0b3842b85ec5e2bb60d

```text

======================================================================
BEAT 1: Attach — watch the pane (zero grants)
======================================================================
watched; grants: {}

======================================================================
BEAT 2: Refuse — unarmed steer refused, nothing typed
======================================================================
refused: unarmed audit_id: 7

======================================================================
BEAT 3: Arm — pin %N, countdown begins
======================================================================
armed pane: %0 ttl: 900

======================================================================
BEAT 4: Steer — a reply lands in the real pane
======================================================================
delivered and visible: walk-steer-d45b3c

======================================================================
BEAT 5: Ground — control vs treatment (.43)
======================================================================
control: I don't have access to your organization's deployment schedule or code names, so
treatment: The deploy is scheduled for Friday the 13th at 3:47pm with the code name BLUEBIR
grounded steer delivered; refs: ['artifact:a1']

======================================================================
BEAT 6: Classify — keep as note
======================================================================
note kept and openable: note_7e3069b68a7b

======================================================================
BEAT 7: Crown cases — recycled pane, expiry, cross-surface disarm
======================================================================
(a) recycled/dead pane refused + revoked: pane_gone
(b) TTL expiry refused + revoked: expired
(c) cross-surface disarm → next send unarmed: unarmed

======================================================================
BEAT 8: Audit — the trail for beats 2-7, read back
======================================================================
audit outcomes (newest first): ['unarmed', 'expired', 'pane_gone', 'delivered', 'delivered', 'unarmed', 'unarmed', 'expired', 'pane_gone', 'delivered', 'delivered', 'unarmed']

======================================================================
WALK: PASS — 12 audit rows, all beats live
======================================================================
```

### Captured run — 2026-07-08T04:51:24Z

- **Command:** `uv run pytest -q tests/unit/test_steering_chokepoint.py tests/unit/test_steering_audit_completeness.py tests/unit/test_desk_locks.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2ebbfafa41a5cc922f3f0b3842b85ec5e2bb60d

```text
.........                                                                [100%]
9 passed in 0.07s
```

### Captured run — 2026-07-08T04:51:39Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a2ebbfafa41a5cc922f3f0b3842b85ec5e2bb60d

```text
ssssssssssssssssssssss...ssssssssss..................................... [  2%]
..................................................................s..... [  4%]
........................................................................ [  6%]
..........................ss............................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 12%]
........................................................................ [ 14%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 43%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 62%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 83%]
........................................................................ [ 85%]
........................................................................ [ 87%]
........................................................................ [ 89%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 96%]
........................................................................ [ 98%]
...........................................................              [100%]
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-64142389
  
  Traceback (most recent call last):
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/meeting_import.py", line 95, in _run_import_job
      import_transcript(
      ~~~~~~~~~~~~~~~~~^
          tmp_path,
          ^^^^^^^^^
      ...<6 lines>...
          started_at=started_at,
          ^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_import.py", line 395, in import_transcript
      return _persist_import(
          db=db,
      ...<8 lines>...
          speakers_found=parsed.speakers_found,
      )
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/meeting_import.py", line 325, in _persist_import
      db.intel.enqueue_intel_job(
      ~~~~~~~~~~~~~~~~~~~~~~~~~~^
          state.id,
          ^^^^^^^^^
          transcript_hash=state.transcript_hash(),
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
          reason=state.intel_status_detail,
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py", line 31, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/core.py", line 1029, in _connection
      conn.commit()
      ~~~~~~~~~~~^^
  sqlite3.OperationalError: disk I/O error
  
  During handling of the above exception, another exception occurred:
  
  Traceback (most recent call last):
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 1044, in _bootstrap_inner
      self.run()
      ~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/threading.py", line 995, in run
      self._target(*self._args, **self._kwargs)
      ~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/meeting_import.py", line 136, in _run_import_job
      _set_import_status(
      ~~~~~~~~~~~~~~~~~~^
          db, meeting_id, "import_failed", f"{type(exc).__name__}: {exc}"
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      )
      ^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/web/routes/meeting_import.py", line 72, in _set_import_status
      state = db.meetings.get_meeting(meeting_id)
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/meetings.py", line 256, in get_meeting
      row = conn.execute(
            ~~~~~~~~~~~~^
          "SELECT * FROM meetings WHERE id = ?", (meeting_id,)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
      ).fetchone()
      ^
  sqlite3.OperationalError: no such table: meetings
  
  Enable tracemalloc to get traceback where the object was allocated.
  See https://docs.pytest.org/en/stable/how-to/capture-warnings.html#resource-warnings for more info.
    warnings.warn(pytest.PytestUnhandledThreadExceptionWarning(msg))

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
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
3408 passed, 37 skipped, 1 warning in 266.41s (0:04:26)
```
