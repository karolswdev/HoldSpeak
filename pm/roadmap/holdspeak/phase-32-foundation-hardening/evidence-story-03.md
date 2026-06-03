# Evidence — HS-32-03 (Converge audio ownership)

**Shipped:** 2026-06-02. The three audio-capture paths — hotkey, device, meeting
— now arbitrate through **one** owner model: the shared `VoiceTypingSession`
audio floor. Previously hotkey/device went through its single-owner lock but the
meeting built its own recorder and bypassed it, so "two things grabbed the mic"
was possible and only prevented by scattered ad-hoc `_active_meeting_session()`
checks. With the TUI/menubar gone (HS-32-07), all three live only in
`WebRuntime`, so the arbiter has a single home.

## What changed

### `holdspeak/voice_typing.py`
- Added `acquire(owner) -> bool` and `release(owner)` — a **source-less** floor
  claim sharing the same one-at-a-time lock as `begin`/`end`. The meeting drives
  its own multi-stream `MeetingRecorder` (mic + system + devices concurrently),
  which doesn't fit the single-`AudioSource` `begin`/`end` model — so it holds
  the floor via `acquire`/`release` instead. `release` is a no-op on owner
  mismatch (safe to call on any meeting-end path) and never stops a source.
- Class docstring updated: it is now "the single owner model for all capture in
  the web runtime," not just hotkey/device.

### `holdspeak/web_runtime.py`
- `_start_meeting` **acquires** the floor (`owner="meeting"`) before building the
  session/opening any recorder. If the floor is held (a hotkey/device session is
  recording) the start is **rejected** with a clear `RuntimeError`. The
  build→start→register block is wrapped so a start-up failure **releases** the
  floor (rollback) before the meeting is registered.
- `_stop_active_meeting` **releases** the floor immediately after `session.stop()`
  (the recorder is closed; the slower save/intel/artifact work touches no mic),
  so hotkey/device voice typing can resume during persistence.
- `run()`'s shutdown-finalize path releases the floor after `active.stop()`.
- **Removed the redundant `_active_meeting_session()` guards** from
  `_on_hotkey_press` / `_on_hotkey_release`: with the meeting now holding the
  floor, `voice_session.begin("hotkey")` returns `False` and `end("hotkey")`
  returns `None` on its own. The arbiter is the single decision point — no
  scattered ownership checks. (The device path keeps its meeting-attached
  routing: "device attached to the active meeting → return True so the WS pumps
  frames into the meeting's drain" is *frame routing*, not floor ownership.)

## Defined precedence

First to hold the floor keeps it until release. So:
- meeting active → hotkey/device `begin()` rejected;
- hotkey/device recording → `_start_meeting` rejected ("audio floor held by …").

## Tests

- New `TestAudioFloorArbitration` in `tests/unit/test_voice_typing_session.py`
  (7 tests): `acquire` blocks `begin` and vice-versa; `release` frees the floor;
  `release` is a no-op on owner mismatch; `acquire` is source-less and rejects a
  blank owner; and a **concurrency test** hammering 10 racing `begin()`s while a
  meeting holds the floor — none win, no source starts, the meeting keeps the
  floor (mutual exclusion).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **1946 passed, 14
  skipped** (+7). `voice_typing.py` / `web_runtime.py` ruff-clean.
- **Real-audio paths** (a meeting actually opening `MeetingRecorder`, hotkey
  opening `AudioRecorder`) remain covered only by the `metal` marker, which needs
  a physical mic and is **not runnable in this remote session** — exercised
  logically here via the fake-source arbiter tests + the existing
  `test_web_runtime` start/stop flow (which now drives acquire/release through
  the real `VoiceTypingSession`).

## Decisions / deviations

- **`WebRuntime` acquires on the meeting's behalf** — `MeetingSession` stays
  ignorant of the arbiter (we just decoupled it from the web server in HS-32-02;
  re-coupling it to an audio arbiter would undo that). The runtime orchestrates.
- The meeting capture mechanism is **unchanged** (still `MeetingRecorder`); this
  story adds a logical ownership gate around it, it doesn't rewrite capture — so
  no real capture path regresses.
- Floor released **right after `session.stop()`**, not at the end of the save
  path — the mic is free the moment capture ends.
