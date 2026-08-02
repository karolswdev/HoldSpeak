# Evidence - HS-111-11

- **Story:** HS-111-11 - The terminal pane
- **Status:** done
- **Date:** 2026-08-02

## Proof

### Captured run — 2026-08-02T09:25:00Z

- **Command:** `uv run pytest -q tests/unit tests/integration --deselect tests/integration/test_web_aftercare_file_issue.py::test_filed_proposal_never_executes_until_approved_and_enabled`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** ccf1774ba2bbef220bbd6beaac7d54d58763df48

```text
........................................................................ [  1%]
........................................................................ [  3%]
........................................................................ [  5%]
........................................................................ [  6%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 11%]
........................................................................ [ 13%]
........................................................................ [ 15%]
........................................................................ [ 17%]
........................................................................ [ 18%]
........................................................................ [ 20%]
........................................................................ [ 22%]
........................................................................ [ 23%]
........................................................................ [ 25%]
........................................................................ [ 27%]
........................................................................ [ 28%]
........................................................................ [ 30%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 45%]
........................................................................ [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 52%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 57%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 62%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 69%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 74%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 79%]
........................................................................ [ 81%]
........................................................................ [ 83%]
................................................s....................... [ 85%]
........................................................................ [ 86%]
.........................................ss............................. [ 88%]
........................................................................ [ 90%]
........................................................................ [ 91%]
........................................................................ [ 93%]
........................................................................ [ 95%]
........................................................................ [ 96%]
........................................................................ [ 98%]
.......................................................                  [100%]
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-c521d60f
  
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
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/core.py", line 1570, in _connection
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
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/meetings.py", line 440, in get_meeting
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

tests/integration/test_web_transcript_import_api.py::test_garbage_transcript_marks_the_row_honestly_and_is_removable
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-8dec20fb
  
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
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/intel.py", line 35, in enqueue_intel_job
      with self._connection() as conn:
           ~~~~~~~~~~~~~~~~^^
    File "/Users/karol/.local/share/uv/python/cpython-3.13.11-macos-aarch64-none/lib/python3.13/contextlib.py", line 148, in __exit__
      next(self.gen)
      ~~~~^^^^^^^^^^
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/core.py", line 1570, in _connection
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
    File "/Users/karol/dev/tools/HoldSpeak/holdspeak/db/meetings.py", line 440, in get_meeting
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
SKIPPED [1] tests/integration/test_dictation_llama_cpp_e2e.py:72: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_llama_cpp.py:38: llama-cpp-python and /Users/karol/Models/gguf/Qwen3.5-4B-Instruct-Q4_K_M.gguf are required for this integration test
SKIPPED [1] tests/integration/test_runtime_mlx.py:38: mlx-lm + outlines + /Users/karol/Models/mlx/Qwen3.5-8B-MLX-4bit are required for this integration test
4228 passed, 3 skipped, 1 deselected, 2 warnings in 450.72s (0:07:30)
```

(Captured run = the full python proof: unit 3465 — up 15 with the
new raw-peek tests — + integration 763; 3 pre-existing model skips;
1 deselection = the environmental aftercare flap documented in
evidence-story-08 (the live hub posture leaks into an unhermetic
test; the builder re-proved it fails identically with this story's
python diff stashed). Web ran separately, output read: exit 0 —
**77 test files / 444 tests**, gates/typecheck/build green.)

## What shipped

The owner's ruling made real — "those panes need to be runnin' on
xterm.js... and be a lot more utility-oriented":

- **The raw peek mode (python)**: `peek_pane(raw=True)` — opt-in
  ANSI passthrough on the same capture/hash-gate path, plus pane
  geometry (width/height/cursor) as garnish. Raised raw byte cap
  (256 KB, argued: SGR runs inflate a colored screen 2-4x and a
  64 KB tail drops the lines a faithful repaint needs); same
  200-line cap; stripped stays the byte-identical default. The
  route edit landed surgically in the PRE-EXISTING-DIRTY
  coder_steering_routes.py at net-zero lines (the density budget
  was already consumed to the byte).
- **THE CONSENT SPINE, proven untouched**: zero edits to any
  steering wire test; the steering.ts diff is pure read-path
  (PaneGeom parsing) — verified by grep, no touch on
  arm/disarm/steer/sendKeys/grants; the new route test's fake has
  no `raw` kwarg, so any leak of the flag into the legacy call is a
  hard error by construction.
- **xterm.js as the PaneWell interior**: one lazy chunk (364 KB
  min / 94 KB gzip, loads ONLY with the pullout/terminal — eager
  desk untouched), `disableStdin: true` with no onData anywhere —
  the terminal is a VIEWER; typing remains the armed composer's
  monopoly. Themed from tokens before open() (no white flash),
  steady block cursor, selection in accent tint, ANSI palette
  mapped to the token tones. Both terminal surfaces inherited via
  the HS-111-06 seam — one interior swap, as designed.
- **Full-repaint on poll**: one write per changed hash, single
  frame; with geometry the terminal sizes to the pane's cols×rows
  and parks the cursor at tmux's position.
- **The utility pass**: `RAW / STRIPPED · RAW UNAVAILABLE` honesty
  token, `LINES n`, live `Δ age`, the FIND StringGadget (mic by kit
  construction) driving the search addon with visible highlights,
  copy-on-select. The fallback face is the old stripped rendering
  with the honest token — never blank (proven against an emulated
  older hub).

## Live proof (staged golden-local hub, real tmux)

A real throwaway tmux session filled with ANSI (killed after; the
owner's sessions untouched; nothing armed or steered). All 10
walk beats PASS. Assets in [assets/hs-111-11/](./assets/hs-111-11/):
`01` true colors/inverse/underline/powerline-prompt at 1440, `02`
THE READ-ONLY PROOF (typing into the focused terminal leaves the
pane byte-identical by capture-pane comparison), `03` the search
highlight, `04` the stripped fallback face, `06` 393×852. Full
set in .tmp/hs-111-11-after/.

## Honest notes

- The delivery-terminal leg fit-wraps to the well width (its stream
  wire carries no pane geometry) — a named stream-wire limitation.
- Cursor parking can drift a row on trailing-blank-trimmed edge
  cases; full-screen apps align exactly.
- Route-level docs are one sentence (the density budget); full
  semantics documented on peek_pane.
