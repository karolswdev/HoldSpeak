# Meeting Stop: bounded postmerge follow-up

Two source-derived review findings require deterministic reproduction before
they are called product defects. First, failure to start a native cleanup
thread can bypass the cleanup error and release an unconfirmed audio floor.
Second, a delayed duplicate Stop can write Saving after the winning Stop saved.
Both affect truthful completion and custody (Tenets 3 and 7).

Settled behavior: thread startup failure is a cleanup failure, preserves the
snapshotted audio and save, and retains the unavailable floor. Attempt the other
device independently; do not fall back to blocking native cleanup on the caller.
One runtime caller owns Stop and its Saving/Saved side effects. A duplicate
returns the existing refusal without changing the winning result or activity.
Keep the existing session guard, public API and final result composition.

Worker scope is `holdspeak/meeting_recorder.py`,
`holdspeak/runtime/meeting_glue.py` and `tests/unit/test_meeting_native_stop.py`.
If a small initialization seam is necessary, report its exact path to root
before editing. Current anchors are recorder 613–650 and meeting_glue 380–413;
verify them because lines drift. All UI, unrelated runtime and docs are root
or sibling owned. Do not broaden the lane.

Use deterministic thread/event control, no native devices, owner state or
providers. First collect and run the two new regressions against current code;
then make only the observed corrections. Focused budget is the owned unit file,
under `scripts/test_lock.py` with isolated HOME and native effects disabled.
No full suite, `test_metal.py`, stage, commit or deploy. Report collection,
red/green tails and exact remaining limits; HOLD FOR SHIP. Root integrates,
runs ordinary quick and carries the subsequent main suite through its result.

## Reproduced and repaired

The three deterministic regressions fail before product edits (3 failed in
2.35 seconds): failure to launch either mic or system cleanup reports no
cleanup error, and the controlled duplicate produces Saving → Saved → Saving.
These are now observed software defects, not reports of a new native incident.

The recorder records each failed cleanup launch, attempts the other stream,
and returns the captured chunks. Runtime Stop claims its existing meeting lock
before visible side effects, preserves the session's own finalization guard,
and releases its runtime claim in `finally`. One save and the exact meeting ID
remain. The new checks verify real isolated DB and journal results, complete
audio chunks, the unavailable audio floor, final Saved activity, and refusal
of the delayed duplicate without a second side effect.

Collection: 18 tests. Owned file: **18 passed in 2.50 seconds**. Red/green logs
are `.tmp/meeting-stop-review/{red-run,green-run,green-collect}.log` in the
follow-up worktree. Native streams are controlled doubles; OS driver recovery
is unverified. No UI composition changes. Root inspected the exact failures,
product diff and proof. Independent source counsel found no blocker, including
the actual callback lock ordering. Ordinary quick GREEN: **120 affected tests,
109 Desk sweep cases and 17 canon guards**. The 28 documentation guards pass.
The unchanged frontend source/build agree at `2759d0c6c13d4b6b`; backend
revision identity remains separate from this frontend digest.
Two additional saved-meeting cases pass at 1440/393; root inspected
`.tmp/evidence-shots/desk-sweep/meeting-{1440,393}.png`. They verify retained
layout and controls, not physical recording or the simulated failure paths.

## Delivery and full-run follow-through

Merged #1237 at `add3c231c`; the verified idle hub was delivered normally from
`wt-meeting-stop-review-fixes-20261017`, PID25584, port8765. Health, Desk,
Conductor and Models return200. Frontend `2759d0c6c13d4b6b` matches source;
the backend revision is the merged head above. Formal Astra bounded review
[RATIFY](https://github.com/karolswdev/HoldSpeak/pull/1237#issuecomment-6230298016)
also closes the original #1233 review's two executed findings.

The subsequent full run completed with3 failed/16,571 passed, plus3 mandatory
live-bus passes. It reopened the runtime size guard and found the audio-journal
completion/discovery ordering and transient PR receipt read. These are fixed
forward in [the full-main follow-up](MODULE-FOLLOWUP.md); the earlier focused
review is not presented as a full-suite pass.
