# Evidence - HS-87-03

- **Story:** HS-87-03 - Steer: the voice-first composer, delivered and audited
- **Status:** done
- **Date:** 2026-07-07

## Proof

### Captured run — 2026-07-08T04:00:39Z

- **Command:** `uv run pytest -q tests/unit/test_coder_steering_deliver.py tests/unit/test_db_steering_audit.py tests/unit/test_steering_chokepoint.py tests/unit/test_web_routes_coders_steer.py tests/integration/test_coder_steering_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f3b311dcf137e7979e932cc181e04b768135de07

```text
.......................                                                  [100%]
23 passed in 3.69s
```

### Captured run — 2026-07-08T04:00:44Z

- **Command:** `bash -c cd web && npx vitest run src/desk`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f3b311dcf137e7979e932cc181e04b768135de07

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  7 passed (7)
      Tests  79 passed (79)
   Start at  22:00:44
   Duration  193ms (transform 470ms, setup 0ms, import 569ms, tests 59ms, environment 0ms)
```

### Captured run — 2026-07-08T04:00:52Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** f3b311dcf137e7979e932cc181e04b768135de07

```text
ssssssssssssssssssssss...ssssssssss..................................... [  2%]
.................................................................s...... [  4%]
........................................................................ [  6%]
.........................ss............................................. [  8%]
........................................................................ [ 10%]
........................................................................ [ 12%]
........................................................................ [ 14%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 21%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 31%]
........F............................................................... [ 33%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 42%]
.................................F...................................... [ 44%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 96%]
........................................................................ [ 98%]
........................................                                 [100%]
=================================== FAILURES ===================================
_______________ test_phase79_package_modules_stay_single_concern _______________

    def test_phase79_package_modules_stay_single_concern() -> None:
        offenders = []
        for pkg in _P79_PACKAGES:
            for path in sorted(pkg.glob("*.py")):
                if path.name == "__init__.py":
                    continue
                budget = (
                    _SETTINGS_ROUTER_BUDGET
                    if path == _HS / "web" / "routes" / "system" / "settings.py"
                    else _MODULE_BUDGET
                )
                n = _lines(path)
                if n > budget:
                    offenders.append(f"{path.relative_to(_REPO)}: {n} lines (budget {budget})")
>       assert not offenders, (
            "Phase-79 package modules over budget — carve a new concern module, "
            "don't grow one:\n  " + "\n  ".join(offenders)
        )
E       AssertionError: Phase-79 package modules over budget — carve a new concern module, don't grow one:
E           holdspeak/web/routes/system/coders.py: 619 lines (budget 600)
E       assert not ['holdspeak/web/routes/system/coders.py: 619 lines (budget 600)']

tests/unit/test_backend_density_guard.py:144: AssertionError
________ TestDatabaseShape.test_fresh_schema_matches_canonical_snapshot ________

self = <tests.unit.test_db.TestDatabaseShape object at 0x12023bc50>
tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-550/test_fresh_schema_matches_cano0')
project_root = PosixPath('/Users/karol/dev/tools/HoldSpeak')

    def test_fresh_schema_matches_canonical_snapshot(self, tmp_path, project_root: Path):
        """HS-31-04: the migration ladder was squashed to one canonical schema.
        A fresh build must match the committed snapshot exactly — any intended
        schema change must update tests/fixtures/db_schema_canonical.txt in the
        same commit, keeping the schema honest without a version ladder."""
        import re
        import sqlite3
        from holdspeak.db import Database
    
        Database(tmp_path / "schema_check.db")
        conn = sqlite3.connect(str(tmp_path / "schema_check.db"))
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT type, name, sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type, name"
        ).fetchall()
        actual = "\n".join(
            f"{r['type']} {r['name']}: {re.sub(r'\\s+', ' ', (r['sql'] or '').strip())}"
            for r in rows
        ) + "\n"
        conn.close()
    
        snapshot = project_root / "tests" / "fixtures" / "db_schema_canonical.txt"
        expected = snapshot.read_text()
>       assert actual == expected, (
            "Fresh DB schema diverged from the canonical snapshot. If this change is "
            f"intended, regenerate {snapshot.relative_to(project_root)}."
        )
E       AssertionError: Fresh DB schema diverged from the canonical snapshot. If this change is intended, regenerate tests/fixtures/db_schema_canonical.txt.
E       assert 'index idx_ac...aker);\nEND\n' == 'index idx_ac...aker);\nEND\n'
E         
E         Skipping 6995 identical leading characters in diff, use -v to show
E         + index idx_steering_audit_key: CREATE INDEX idx_steering_audit_key ON steering_audit(session_key)
E         + index idx_steering_audit_ts: CREATE INDEX idx_steering_audit_ts ON steering_audit(ts)
E           index idx_topics_meeting: CREATE INDEX idx_topics_meeting ON topics(meeting_id)
E           index idx_workflows_modified: CREATE INDEX idx_workflows_modified ON workflows(last_modified DESC)
E           table action_items: CREATE TABLE action_items (...
E         
E         ...Full output truncated (589 lines hidden), use '-vv' to show

tests/unit/test_db.py:1643: AssertionError
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-ff554cda
  
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
FAILED tests/unit/test_backend_density_guard.py::test_phase79_package_modules_stay_single_concern
FAILED tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot
2 failed, 3387 passed, 37 skipped, 1 warning in 266.42s (0:04:26)
```

### Captured run — 2026-07-08T04:14:03Z

- **Command:** `uv run pytest -q tests/unit/test_coder_steering_deliver.py tests/unit/test_db_steering_audit.py tests/unit/test_steering_chokepoint.py tests/unit/test_web_routes_coders_steer.py tests/integration/test_coder_steering_live.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f3b311dcf137e7979e932cc181e04b768135de07

```text
.......................                                                  [100%]
23 passed in 3.73s
```

### Captured run — 2026-07-08T04:14:15Z

- **Command:** `bash -c cd web && npx vitest run src/desk`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f3b311dcf137e7979e932cc181e04b768135de07

```text

 RUN  v4.1.9 /Users/karol/dev/tools/HoldSpeak/web


 Test Files  7 passed (7)
      Tests  79 passed (79)
   Start at  22:14:15
   Duration  193ms (transform 495ms, setup 0ms, import 585ms, tests 60ms, environment 0ms)
```

### Captured run — 2026-07-08T04:14:16Z

- **Command:** `uv run pytest -q --ignore=tests/e2e/test_metal.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f3b311dcf137e7979e932cc181e04b768135de07

```text
ssssssssssssssssssssss...ssssssssss..................................... [  2%]
.................................................................s...... [  4%]
........................................................................ [  6%]
.........................ss............................................. [  8%]
........................................................................ [ 10%]
........................................................................ [ 12%]
........................................................................ [ 14%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 21%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 29%]
........................................................................ [ 31%]
........................................................................ [ 33%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 60%]
........................................................................ [ 63%]
........................................................................ [ 65%]
........................................................................ [ 67%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 77%]
........................................................................ [ 79%]
........................................................................ [ 82%]
........................................................................ [ 84%]
........................................................................ [ 86%]
........................................................................ [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 96%]
........................................................................ [ 98%]
........................................                                 [100%]
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-3abc1c98
  
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
3389 passed, 37 skipped, 1 warning in 267.36s (0:04:27)
```
