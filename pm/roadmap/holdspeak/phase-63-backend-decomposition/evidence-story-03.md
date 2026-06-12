# Evidence — HS-63-03: WebRuntime mixins: the feature glue

**Date:** 2026-06-12
**Verdict:** done. The wake glue, the device glue, and the dictation
capture path live in `holdspeak/runtime/`; `web_runtime.py` dropped from
2,635 to **1,763 lines**; the verbatim proof is again one line.

## What shipped

`WebRuntime(DictationCaptureMixin, WakeWordGlueMixin, DeviceGlueMixin)`:

- `runtime/dictation_capture.py` (413): `_transcribe_and_type`,
  `_kick_off_transcribe`, voice-command dispatch, the pipeline runner,
  the tmux agent-reply path, and the hotkey press/release handlers.
- `runtime/wake_glue.py` (~360): the HS-60 section verbatim — listener
  lifecycle, the armed capture handoff, the preview/type fork, the
  one-shot token store.
- `runtime/device_glue.py` (~315): the AIPI-Lite voice sessions, events,
  health, and queries.

## The verbatim proof

The body-line diff (imports/blanks excluded) between the pre-story
`web_runtime.py` and (the new core + the three mixins): **exactly one
original line lost — `class WebRuntime:`**, rewritten as the composition.

## The test edits (the policy: patch-target paths ONLY)

Three files, six patch lines, assertions byte-identical:

| Test file | Old target | New target |
|---|---|---|
| test_wake_runtime.py (×3) | `web_runtime.run_dictation_pipeline` | `runtime.dictation_capture.run_dictation_pipeline` |
| test_dictation_runner.py (×1) | `web_runtime.run_dictation_pipeline` | `runtime.dictation_capture.run_dictation_pipeline` |
| test_voice_command_dispatch.py (×1) | `web_runtime.dispatch_voice_command` | `runtime.dictation_capture.dispatch_voice_command` |

An honest wrinkle worth recording: the first retarget pointed the wake
tests at `wake_glue` — and two of them PASSED anyway, because
`_transcribe_wake` reaches the pipeline through
`self._maybe_run_dictation_pipeline` (a dictation_capture method), so the
real global lives in dictation_capture's namespace and the unpatched real
pipeline ran silently. The third test failed loudly (KeyError) and
exposed it. Fix: all five sites point at dictation_capture, AND the
misleading unused `run_dictation_pipeline`/`dispatch_voice_command`
imports were trimmed from wake_glue/device_glue so nobody patches a name
that nothing calls.

Two function-local relative imports also needed the package depth fix
(`from .wake_word` → `from ..wake_word` etc., 8 sites) — loud
ModuleNotFoundErrors this time, the HS-63-01 lesson paying out.

## Proof

- AST free-name check on all three modules: clean.
- MRO smoke: the composed class resolves every moved method.
- Full suite: **2768 passed, 17 skipped**.
