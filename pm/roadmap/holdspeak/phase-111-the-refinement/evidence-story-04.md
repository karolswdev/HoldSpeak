# Evidence - HS-111-04

- **Story:** HS-111-04 - Agents
- **Status:** done
- **Date:** 2026-08-01

## Proof

### Captured run — 2026-08-01T22:46:53Z

- **Command:** `uv run pytest -q tests/unit tests/integration`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 3c0df929c294bd93e2050e5a8ccbacde4e55712f

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
  /Users/karol/dev/tools/HoldSpeak/.venv/lib/python3.13/site-packages/_pytest/threadexception.py:58: PytestUnhandledThreadExceptionWarning: Exception in thread meeting-import-8e6f22f0
  
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
4207 passed, 3 skipped, 1 warning in 427.27s (0:07:07)
```

(The captured run is the full python proof: tests/unit 3443 +
tests/integration 764, 3 pre-existing model-dependency skips. An
earlier local run had a 4th transient skip — rails-observer live
proof when the .43 LLM was momentarily unreachable — gone on the
captured rerun. Web suite ran separately, output read:
`cd web && npm run check` exit 0 — **67 test files / 389 tests**,
token gate, architecture guard, typecheck, build all green.)

## What shipped

The Agents/Companion program rethought as the crew console
(process-monitor / operator-console structure, Signal Workbench
render), per the verified audit (.tmp/hs-111-04-audit.md):

- **The crew board**: Sessions + Chat collapsed into ONE
  SurfaceLedger — head `CREW n · SESSIONS n · BLOCKED n`, SESSIONS
  band blocked-first with LampGadget cells and open-in-place ANSWER,
  CREW band below; wings Roster | Delivery; the SaaS empty-state
  page, profile cards, StatusPills, and the "How it connects" prose
  accordion are dead (facts live behind the door as tokens).
- **The personnel record**: persona detail is a record head (beveled
  glyph tile · name · role token · EgressChip) over a transmission
  log — new **SurfaceTraffic** kit species: prefixed mono `YOU>` /
  `<NAME>>` turns in the sunken well, per-reply egress chips + KEEP,
  thinking = scanning `LedMeter RX`. Bubbles, hello card, slide-in,
  and the hand-rolled second egress-badge species are dead
  (DeskChrome's system badge untouched — story 07 territory).
- **Steering re-rendered, consent spine BYTE-UNTOUCHED**: ARM is a
  TransportKey whose armed state is inverted video (both accent-glow
  rings deleted), the TTL countdown a draining `LedMeter GRANT` +
  mono m:ss, context budget `LedMeter CTX` + `CAP 8 KB` token,
  policy prose → axis-named fact tokens, NodeChip → CycleGadget,
  PanePicker → mini-ledger rows (the smuggled `inset 2px 0 0 0`
  accent rail is dead), spawn/rename inputs gained mics, kill keeps
  the two-step (confirm = inverted danger).
- **The proof of the constraint**: `desk/steering.ts` zero diff
  (verified by git); `steering.test.ts` passed with ZERO edits; all
  python steering wire tests passed unedited (111 passed on the
  targeted run).

## Live proof (real hub, :8765)

Before/after in [assets/hs-111-04/](./assets/hs-111-04/):
`before-desktop-sessions.png` (the SaaS empty state) and
`before-desktop-persona.png` (the messenger bubbles) vs
`desktop-01-crew-board.png`, `desktop-04-persona-record.png`,
`desktop-06-session-unarmed.png` (LIVE lamp, sunken script well,
unarmed ARM key — attached read-only to a live pane; nothing
spawned, armed, steered, or killed during the walk), `mobile-01`.
Full 12-shot set reviewed (.tmp/hs-111-04-after/).

## Honest notes

- `KEPT n` fact omitted from the record head — the harvest count has
  no honest client-side source; `TURNS n` rendered instead (omission
  over invention).
- ARM lives in an always-present footer transport strip, not the
  window head (a 48px key can't ride the title bar); arming
  affordance visibility unchanged.
- Two stale token-allowlist entries pruned (their raw values died
  with the bubbles/shadow) — the token gate requires exact liveness.
- One integration source-marker test re-pointed honestly
  (test_companion_page_is_the_agent_desk: markers named the deleted
  prose; now pinned to the new source with the guarantee intact).
