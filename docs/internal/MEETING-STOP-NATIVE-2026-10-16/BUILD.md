# Meeting Stop — bounded native cleanup

DRAFT — UNCHECKED — awaiting Muad'Dib. HOLD FOR SHIP.

Worktree: `/Users/karol/dev/tools/wt-meeting-stop-20261016`.
Branch: `fix/meeting-stop-native-20261016`; base `798338072`.
Tuesday: Stop ends capture and saves the meeting even if an audio device fails
to close. Other API requests continue to work.

## Diagnosed seam

The supplied process sample showed the web uvloop thread inside PortAudio
`FinishStoppingStream` → `AudioOutputUnitStop`, waiting for a CoreAudio mutex.
A CoreAudio IO thread was also waiting inside `startStopCallback` →
`AudioUnitGetProperty`. The sample proves native teardown is stuck; it does not
establish the ownership of those native mutexes. The application defect is
definite: async Stop routes called that synchronous native teardown directly
on the event loop, making the whole API unavailable.

The recorder already journaled mic/system PCM continuously. Root owns the
incident recovery and its separate record. This lane has made no owner-state
changes. No transcript, token or audio content was read or printed.

## Change

- `meeting_recorder.py`: each buffer/journal commit rechecks capture admission
  under the same recorder lock used to seal and snapshot Stop. An accepted
  commit finishes before the snapshot; a callback still copying/resampling at
  the cutoff is refused when it reaches commit. Native stop/close calls occur
  outside that lock, on separate daemon workers per stream, with one shared
  one-second wait budget. Stop returns accepted chunks even after that budget.
  Cleanup errors are separate from audio-save errors. A recorder with failed
  cleanup refuses reuse until restart.
- `meeting_session/session.py`: the existing stop event supplies a concurrent
  Stop guard under the session lock. Capture seals before background-thread
  joins, and the accepted PCM journal finalizes before slower transcript or
  intelligence work. The same meeting still receives its final DB checkpoint
  and compatibility save. Native cleanup failure does not mark saved audio as
  lost or replace its identity.
- `runtime/meeting_glue.py`: confirmed cleanup releases the audio floor as
  before. Failed or pending cleanup retains the floor until restart. The saved
  meeting result and existing runtime error surface report the device problem
  separately from save failure.
- `web/routes/meetings/live.py`: both Stop aliases offload the synchronous
  service call. Their final broadcast stays on the event loop. Concurrent Stop
  answers 409; a completed save with a device cleanup problem returns success
  with a warning.

No shared audio manager, UI change or provider work was added. Existing
transcription/intelligence join deadlines and final processing remain; this
change bounds native teardown, not every possible downstream service delay.

## Focused proof

Root gave TEST GO for exactly these five files:

```text
tests/unit/test_meeting_native_stop.py
tests/unit/test_meeting_session.py
tests/unit/test_meeting_capture_durability.py
tests/integration/test_meeting_stop_and_conflicts.py
tests/integration/test_device_meeting_session.py
```

New focused cases exercise native stop and close wedges, shared cleanup
deadline/daemon ownership, close failure, late callbacks, accepted journal
commit ordering, same-ID journal/DB/JSON finalization, audio-floor behavior,
concurrent Stop, responsive ASGI requests and event-loop broadcasts.

Commands, from the worktree root, in order:

```sh
.venv/bin/python .tmp/meeting-stop/locked.py stop-collect .venv/bin/python -m pytest --collect-only -q tests/unit/test_meeting_native_stop.py tests/unit/test_meeting_session.py tests/unit/test_meeting_capture_durability.py tests/integration/test_meeting_stop_and_conflicts.py tests/integration/test_device_meeting_session.py
.venv/bin/python .tmp/meeting-stop/locked.py stop-run .venv/bin/python -m pytest -q -n 8 --dist worksteal tests/unit/test_meeting_native_stop.py tests/unit/test_meeting_session.py tests/unit/test_meeting_capture_durability.py tests/integration/test_meeting_stop_and_conflicts.py tests/integration/test_device_meeting_session.py
```

Both exited 0. The wrapper held the machine test lock and supplied an isolated
HOME with native-state switches off. The new recorder tests replace device
discovery and native streams; ASGI tests run in memory, without a live hub or
socket. Read the complete logs at `.tmp/meeting-stop/stop-collect.log` and
`.tmp/meeting-stop/stop-run.log`; neither contains warnings or failures.

Actual collection tail:

```text
51 tests collected in 4.12s
```

Actual complete run output:

```text
bringing up nodes...
bringing up nodes...

...................................................                      [100%]
51 passed in 3.95s
```

The collection includes 15 new parametrized cases in
`tests/unit/test_meeting_native_stop.py`, plus 36 standing cases in the four
existing files. The new cases prove:

- Native mic/system cleanup share one deadline and run on independent daemons.
- Either `stop()` or `close()` can hang without withholding accepted chunks;
  a returned close error is also reported.
- Both mic and system callbacks already resampling at the cutoff cannot write
  after Stop. An accepted journal write completes before the snapshot and is
  present in the finalized durable manifest.
- A native wedge still permits same-ID PCM finalization and SQLite/JSON save.
- Concurrent Stop is refused before a second finalization.
- Successful cleanup releases the floor; failed cleanup preserves the saved
  result while retaining the floor and exposing its separate error.
- Both HTTP aliases keep another ASGI request responsive, broadcast on the
  event-loop thread, return a cleanup warning, and report duplicate Stop as 409.

Own-path `git diff --check` exited 0. No build, browser, stage or commit command
was run. These checks simulate native hangs; they do not demonstrate that
CoreAudio itself can recover. The deliberate timeout posture requires restart
before another capture, even if a daemon eventually returns. Existing final
transcription and intelligence work can still take their normal time; the fix
does not impose a new global Stop deadline. Root owns quick check, source
review, delivery and the live close. HOLD FOR SHIP.

## Root check

Root read the focused collection and run output and the four-file source change.
Independent read-only counsel found no material blocker in cutoff/finalization,
native deadlines, audio-floor retention or event-loop/broadcast placement. This
is implementation counsel, not a formal Muad'Dib or postmerge Astra review.

The quick check passed: production web build, 125 affected Python checks, 109
Desk sweep checks at the required widths, and 17 canon guards. Logs are under
`.tmp/meeting-stop/quick/`; the root runner ended GREEN. Native hangs are
simulated in regression checks; the existing live incident was captured before
recovery, not reproduced on the owner's audio hardware.
