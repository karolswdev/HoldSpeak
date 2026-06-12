# Evidence — HS-63-04: WebRuntime mixins: the platform glue + thin core

**Date:** 2026-06-12
**Verdict:** done. `web_runtime.py` is **555 lines** (boot, config apply,
presence sync, onboarding nudges, signal handling, run, run_web_runtime) —
down from 2,635 at phase open. Five more mixins; zero body lines lost.

## What shipped

The composition is now `WebRuntime(TranscriberStateMixin,
RuntimeActivityMixin, MeetingGlueMixin, RoutingGlueMixin, PluginQueueMixin,
DictationCaptureMixin, WakeWordGlueMixin, DeviceGlueMixin)`:

- `runtime/meeting_glue.py` (552): start/stop, segment/intel/broadcast
  handlers, bookmarks, meeting updates, action-item passthroughs.
- `runtime/routing_glue.py` (450): intent controls, the route preview,
  preview-history + MIR-history persistence, artifact synthesis, project
  association.
- `runtime/activity.py` (264): activity broadcasts, the voice-state
  machine, idle/state/status payloads, the intel-egress summary.
- `runtime/plugin_queue.py` (171): the deferred-queue flush, drains,
  loop, on-demand processor.
- `runtime/transcriber_state.py` (144): status, lazy load, background
  warm.

Unused imports were auto-trimmed from every new module (37–41 each) so no
patchable-looking name exists where nothing calls it — the HS-63-03
lesson applied mechanically.

## The crash that proved the census right

The first post-carve suite run ABORTED (Fatal Python error) inside
`mlx_whisper detect_language`: the device-reply tests patch
`web_runtime.Transcriber` with a fake, the lookup had moved to
`transcriber_state`, the patch missed — and a REAL MLX Whisper model
loaded inside a unit test and died. Exactly the failure mode the scaffold
census predicted for this global, and exactly why the patch-target policy
exists. (A separate source-lock, the language-knob construction-site
grep, also followed the moved code.)

## The test edits (patch-target/source-lock paths ONLY)

| Test file | Old target | New target |
|---|---|---|
| test_web_runtime.py (×5) | `web_runtime.Transcriber` | `runtime.transcriber_state.Transcriber` |
| test_web_runtime.py (×1) | `web_runtime.MeetingSession` | `runtime.meeting_glue.MeetingSession` |
| test_web_runtime.py (×1) | `web_runtime.drain_plugin_run_queue` | `runtime.plugin_queue.drain_plugin_run_queue` |
| test_language_knob.py (×1) | source-lock path `web_runtime.py` | `runtime/transcriber_state.py` |

Assertions byte-identical throughout.

## The verbatim proof

The body-line diff between the pre-story core and (the new core + the
five mixins): **0 original lines lost** (the class statement had already
become the composition in HS-63-03; this story only extended the list).

## Proof

- Full suite: **2768 passed, 17 skipped**.
- Shape: core 555; largest runtime module 552; everything ≤600.
