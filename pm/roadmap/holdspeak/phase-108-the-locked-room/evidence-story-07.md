# Evidence - HS-108-07

- **Story:** HS-108-07 - Closeout - open the locked room
- **Status:** done
- **Date:** 2026-07-30

## Corrected machine sitting

```text
$ uv run --extra test python scripts/phase108_closeout_beats.py
B1  PASS  warrant forgery/replay/payload/focus confinement (14 passed)
B2  PASS  real desktop act through the spawned executor
          operation op_b73ba81d0fdc41c98a0ed092d4c74681
          marker_landed=true; native=succeeded; kernel=succeeded
B3  PASS  terminal text and keys universally enter process.input (47 passed)
B4  PASS  CLI reads require an authenticated principal (71 passed)
B5  PASS  generic claim and execution liveness terminalize (10 passed)
B6  PASS  mandatory live browser bus (3 passed)
B7  PASS  empty register, confinement fence, CI and docs (32 passed)
B8  PASS  complete Python and web sweeps
          4382 passed, 37 skipped, 2 warnings
          64 web files / 373 tests; typecheck and production build passed

8/8 machine beats passed
```

The expected Python skips are opt-in hardware/model fixtures; no Phase 108
gate was deselected. The two warnings are the existing meeting-import
background-thread teardown race. The built-bundle browser proof ran with
Chromium and `HOLDSPEAK_REQUIRE_LIVE_BUS=1`, so it could not silently skip.

## The finding before the verdict

The adversarial closeout audit found that a timed-out desktop child left a
desynchronized pipe whose still-alive process could make `_start()` accept a
later operation. Broken state now closes that endpoint permanently. A
regression proves the first attempt is indeterminate and no second message is
written to the pipe. The full eight-beat session above was rerun after the fix.

## The owner's verdict

On 2026-07-30, after the corrected 8/8 machine sitting and delivered behavior
were presented, the owner gave this verdict verbatim:

> 's all's good, moyt.

No blocking defect was raised. The phase closes at 7/7 under Article IX.4.
