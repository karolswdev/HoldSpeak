# HS-63-03 — WebRuntime mixins: the feature glue

- **Project:** holdspeak
- **Phase:** 63
- **Status:** done
- **Depends on:** none
- **Unblocks:** HS-63-04
- **Owner:** unassigned

## Problem
The wake-word glue, the device handlers, and the dictation capture path
(transcribe-and-type, hotkey, tmux agent reply, voice-command dispatch)
are ~900 lines of feature glue inside WebRuntime.

## Scope
- **In:** `holdspeak/runtime/` gains `wake_glue.py`, `device_glue.py`,
  and `dictation_capture.py` as mixins, bodies verbatim. The documented
  patch-target moves happen here: `run_dictation_pipeline` (wake +
  dictation tests), `dispatch_voice_command`, `Transcriber` if its
  loader moves — every moved monkeypatch site listed in evidence with
  before → after paths; assertions byte-identical.
- **Out:** the platform glue (HS-63-04); behavior changes.

## Acceptance criteria
- [x] The three mixins are single-concern and under budget.
- [x] Test edits are patch-target paths ONLY, enumerated in evidence.
- [x] Full suite green; the wake/dictation/device slices read.

      See `evidence-story-03.md`.

## Test plan
- Full suite + the wake_runtime / dictation / device test slices.
