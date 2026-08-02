# Evidence - HS-111-05

- **Story:** HS-111-05 - Ask and conversation
- **Status:** done
- **Date:** 2026-08-01

## Proof

### Captured run — 2026-08-02T00:56:03Z

- **Command:** `uv run pytest -q tests/unit tests/integration`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 8b822668ff22aadec19a730d62a2a72609b8513c

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
........................................................................ [ 29%]
........................................................................ [ 30%]
........................................................................ [ 32%]
........................................................................ [ 34%]
........................................................................ [ 35%]
........................................................................ [ 37%]
........................................................................ [ 39%]
........................................................................ [ 41%]
........................................................................ [ 42%]
........................................................................ [ 44%]
........................................................................ [ 46%]
........................................................................ [ 47%]
........................................................................ [ 49%]
........................................................................ [ 51%]
........................................................................ [ 53%]
........................................................................ [ 54%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 59%]
........................................................................ [ 61%]
........................................................................ [ 63%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 68%]
........................................................................ [ 70%]
........................................................................ [ 71%]
........................................................................ [ 73%]
........................................................................ [ 75%]
........................................................................ [ 76%]
........................................................................ [ 78%]
........................................................................ [ 80%]
........................................................................ [ 82%]
........................................................................ [ 83%]
..........................s............................................. [ 85%]
........................................................................ [ 87%]
...................ss................................................... [ 88%]
........................................................................ [ 90%]
........................................................................ [ 92%]
........................................................................ [ 94%]
........................................................................ [ 95%]
........................................................................ [ 97%]
........................................................................ [ 99%]
..................................                                       [100%]
=============================== warnings summary ===============================
tests/integration/test_web_transcript_import_api.py::test_txt_upload_uses_the_transcript_fallback_speaker
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-5e6e724b
  
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
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-7f4aade7
  
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
4207 passed, 3 skipped, 2 warnings in 426.48s (0:07:06)
```

(Captured run = the full python proof: unit 3443 + integration 764,
3 pre-existing model-dependency skips. Web ran separately, output
read: `cd web && npm run check` exit 0 — **68 test files / 392
tests**, token gate clean (46 exceptions, all in use), typecheck,
build green.)

## What shipped

Ask rethought as the query console (SurfaceTraffic transmission
grammar — ONE conversation language with the persona chat), per the
verified audit (.tmp/hs-111-05-audit.md) plus the owner's live bug
report folded in mid-build:

- **The thread is SurfaceTraffic**: `YOU>` turn with lens/CTX
  tokens; routing = `HUB>` turn with a scanning LedMeter RX (the
  pulse and print-bounce animations are deleted); the answer turn =
  Material body + per-run EgressChip + placement tokens + KEEP/BIN.
  The hand-rolled egress-badge in AskPanel is dead.
- **THE HONESTY FIX**: the grounding receipt — parsed off the wire
  since HS-109-04 and rendered NOWHERE — now reaches the glass:
  `GROUNDED ON N OF M` (ProjectMemoryCore's exact match math) + one
  OPENABLE citation token per source ref. CitationChips promoted
  into the kit (desk/surface/citations.tsx); ProjectMemoryCore
  imports from the kit — the two surfaces can never disagree.
- **The owner's error-overlap report, structurally dead**: every
  fault lands in the footer receiptbar (danger tone) or as an
  in-flow error turn; nothing floats or absolutely positions over
  the deck; no critical text in tooltips. Machine-verified in the
  refusal state: every control visible and inside the viewport at
  both sizes.
- **Zero naked HTML**: RunsOnPicker's raw <select> became a
  CycleGadget (lands on all four mounts), row-title buttons became
  CheckGadget bands, disclosure heads carry aria-expanded + focus
  dress.
- **The rack**: one GadgetGroup GROUNDING — full-width CheckGadget
  hover-band rows, indented sub-picks with real token figures, the
  shared LedMeter CTX gauge; the audit's live overflow defect
  (missing minmax(0,1fr)) is dead by construction, proven with the
  57-char offender title at both viewports (scrollWidth ==
  clientWidth).
- Wire byte-untouched (ask.ts/grounding.ts/chat.ts + python);
  glass-drop hooks preserved (glassDrop.test.tsx unedited);
  steering tests pass with zero edits.

## Live proof (real hub, :8765)

Before/after in [assets/hs-111-05/](./assets/hs-111-05/):
`before-desktop-overflow.png` (the long-title blowout pushing the
gauge off-panel) vs `desktop-01-console-resting.png`,
`desktop-03-rack-picked.png` (the rack holding the same offender),
`desktop-05-refusal.png` + `mobile-05-refusal.png` (the owner's
error path: in-flow `× HUB>` turn + receiptbar fault line, every
control operable). Full 12-shot set reviewed
(.tmp/hs-111-05-after/).

## Honest notes

- **No printed turn captured**: no language model was reachable
  tonight (hub-local none, .43 down, mesh offline) — the refusal
  path was captured instead of faking a print; the receipt block is
  covered by the CitationChips kit test + unchanged python receipt
  suites. A live printed-turn walk should ride the next story's
  proof once .43 is back.
- Steer-composer leg: ARM refused honestly (no tmux-backed session
  existed); the shared rack is the same component proven in the Ask
  and PersonaChat legs; steering tests byte-unedited.
- The two grounding disclosure heads remain house-grammar buttons
  with aria-expanded (no kit disclosure species carries a budget
  token yet) — story 08 kit territory if it wants one species.
- This commit also carries the day's roadmap riders authored between
  stories: HS-111-11 (the terminal pane — owner's xterm.js ruling),
  the HS-111-07 owner riders (desktop right-click NEW>/LAUNCH>,
  debug-behind-RAW, the command-deck palette + menubar z-order from
  the usability doctrine), the HS-111-08 doctrine riders (roving
  focus, arming deletes), and the usability doctrine PROPOSAL filed
  at proposals/usability-doctrine.md awaiting the owner's sitting.
  No story flips with them; they are master-doc updates.
