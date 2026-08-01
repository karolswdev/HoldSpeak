# Evidence - HS-111-02

- **Story:** HS-111-02 - Speak
- **Status:** done
- **Date:** 2026-08-01

## Proof

### Captured run — 2026-08-01T19:59:15Z

- **Command:** `uv run pytest -q tests/unit tests/integration`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** bad8e813150fbad845f4d4bb7ce180d672dfb1bb

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
tests/integration/test_web_transcript_import_api.py::test_garbage_transcript_marks_the_row_honestly_and_is_removable
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-b9a5be72
  
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
4207 passed, 3 skipped, 1 warning in 424.26s (0:07:04)
```

(The captured run is the FULL python proof: tests/unit 3443 +
tests/integration 764, 3 pre-existing model-dependency skips. The web
suite ran separately, output read: `cd web && npm run check` exit 0 —
tokens/token-gate clean, architecture guard, typecheck, **66 test
files / 387 tests passed**, build green.)

## What shipped

The Speak program rethought as the OS's dictation deck (Workbench 2.0
transport/meter/ledger structure, Signal Workbench render), per the
verified audit (.tmp/hs-111-02-audit.md):

- **The cockpit is an instrument**: full-width sunken strip — 48×48
  TALK momentary key (held = inverted video; the banned mic glow at
  desk.css:4394 is DELETED), 12-segment LedMeter fed by a real RMS
  tap on the capture stream, named STATE register
  IDLE/LISTENING/TRANSCRIBING, etched readout cells (PIPELINE lamp,
  → TARGET, BUDGET) from the readiness wire. The 70%-void web form is
  gone.
- **Every toast died into the footer**: the readiness line is now the
  program-wide receipt/refusal bar (DRAFT RESTORED, MARKED OK,
  TAUGHT, SAVING…/WRITTEN, ⚠ refusals) via a ReceiptContext.
- **The correction ritual is a gadget sheet in place**: WRONG extends
  the receipt with FIELD cycle gadget / VALUE string gadget with mic /
  TEACH — the "What should change?" form stack is dead.
- **The journal is a machine ledger**: new SurfaceLedger/Row species —
  26px one-line mono rows (time | transcript | → dest | ms | taught),
  click-to-expand in place with the sunken cursor-line fill, token
  head `TODAY n · TAUGHT n`, search with mic. SurfaceStream untouched
  (LiveCore safe).
- **The gear door is one gadget sheet**: six prose sections recomposed
  onto GadgetGroups; the Hooks raw-JSON dump replaced with designed
  rows (raw object behind Raw trace); correction memory a GadgetTable
  with KIND|GIST|VALUE|REACH + arming FORGET?; digest a token row.
- **Four new kit species for stories 03-08**: LedMeter, LampGadget,
  TransportKey/TransportRow, GadgetTable verbs slot.
- Five python guard/integration tests re-pointed honestly per the
  audit's §4 (trust-signals now asserts the banner species STAYS
  dead); the dead StatusPill import is deleted.

## Live proof (real hub, :8765)

Before/after in [assets/hs-111-02/](./assets/hs-111-02/):
`before-desktop-cockpit.png` (the void: textarea + button + prose) /
`before-desktop-journal.png` (the 2-line feed) vs
`desktop-00-speak-resting.png` (the deck), `desktop-03` (WRONG sheet
in place), `desktop-04` (the ledger), `desktop-08` (door sheet,
designed Hooks), `mobile-00` (the deck at 393px, DRAFT RESTORED as a
footer receipt token). Full 19-shot set reviewed
(.tmp/hs-111-02-after/).

## Honest notes (deviations, canon-driven)

- Empty digest reads `WEEK · TAUGHT 0` (the vocabulary guard bans the
  em-dash token the audit sketched).
- "Delivery target" not bare "Target" (product-language guard).
- TEACH renders "Teach" with the pinned aria-labels so the
  moment-of-truth/ritual guards' accessible names survive.
- Hooks SET/— chips key off `latest_session` presence — the only
  honest signal the wire offers.
- Dry-run walks (audit + build) wrote a few real journal entries on
  the hub (source dry-run); deletable in-app.
