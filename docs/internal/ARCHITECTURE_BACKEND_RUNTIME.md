# The backend runtime decomposition (Phase 63)

The backend twin of [ARCHITECTURE_WEB_FRONTEND.md](./ARCHITECTURE_WEB_FRONTEND.md).
Two god-objects paid down their debt the same way the dictation cockpit
did: verbatim moves into single-concern modules, a thin assembly core, and
a density guard so the shape cannot silently regrow.

## Why this exists

`web_runtime.py` proved that a carve regrows without a lock. Phase 52
sliced the dictation orchestration out of it at 2,341 lines; by Phase 63 it
had regrown to 2,635 (the wake word, devices, and routing glue all landed
in the god-object because it was the path of least resistance).
`meeting_session.py` had the same disease un-flagged: models, recording,
transcription, intel, persistence, and mutations in one 1,674-line file.

## The shape

**`holdspeak/web_runtime.py` (the core, ~555 lines)** keeps exactly what a
boot module owns: `__init__`, config apply + presence sync, the onboarding
nudges, signal handling, `run()`, and `run_web_runtime()`. Everything else
is a mixin in **`holdspeak/runtime/`**, composed by the class:

| Module | Concern |
|---|---|
| `transcriber_state.py` | transcription status, lazy load, background warm |
| `activity.py` | runtime activity broadcasts, the voice-state machine, state/status payloads |
| `meeting_glue.py` | meeting start/stop, segment/intel/broadcast handlers, bookmarks, action-item passthroughs |
| `routing_glue.py` | MIR intent controls, route preview, history + artifact persistence, project association |
| `plugin_queue.py` | the deferred plugin-run queue (flush, drains, loop) |
| `dictation_capture.py` | transcribe-and-type, the hotkey handlers, tmux agent reply, voice-command dispatch |
| `wake_glue.py` | the wake-word listener lifecycle, armed capture, the preview/type fork |
| `device_glue.py` | AIPI-Lite voice sessions, events, health, queries |

**`holdspeak/meeting_session/` (a package; the old module path is the
package, so every existing import works)**:

| Module | Concern |
|---|---|
| `models.py` | the pure data layer: Bookmark, TranscriptSegment, IntelSnapshot, MeetingSaveResult, MeetingState |
| `session.py` | the core: lifecycle (start/stop), bookmarks, device attach, broadcasts (~795 lines) |
| `transcribe_loop.py` | the background loop, the overlap window, chunk transcription |
| `intel_analysis.py` | the live intel cadence and bookmark-label refinement |
| `persistence.py` | `save()` |
| `mutations.py` | action-item status/review/edit, title, tags |

## The rules the pattern lives by

1. **Mixins receive everything via `self`.** A mixin module never imports
   `web_runtime` (the core imports the mixins; a cycle is a design error).
2. **Patch targets live where the lookup happens.** A test that fakes a
   module-level dependency (`Transcriber`, `run_dictation_pipeline`, …)
   patches the MIXIN module that calls it, not the core. Phase 63 learned
   this twice the hard way: a missed patch loaded a real MLX Whisper model
   inside a unit test (a process-fatal abort), and a wrong-module patch
   passed two tests coincidentally while the real pipeline ran silently.
3. **No unused imports in mixin modules.** An importable-but-uncalled name
   is a patching trap — someone will monkeypatch it and nothing will
   change. Phase 63 auto-trimmed every carved header.
4. **Relative imports gain a dot inside packages — at every indentation.**
   The carve scripts missed indented `try:`-block imports twice; the
   guarded `except ImportError` fallbacks then masked the mistake
   (intel silently became `None`). Check function-local imports too.
5. **The guard fires → carve, don't bump**
   (`tests/unit/test_backend_density_guard.py`: cores 650/850, modules
   ≤600). Raising a budget is a reviewed decision, not a reflex.

## Adding a concern (the walkthrough)

1. Create `holdspeak/runtime/<concern>.py` with a `<Concern>Mixin` class;
   import only what the methods call (parent-relative: `from ..x import`).
2. Add the mixin to `WebRuntime`'s base list in `web_runtime.py`.
3. State arrives via `self` (set up in the core's `__init__`); new
   attributes are initialized there, used in the mixin.
4. Tests that fake the mixin's module-level dependencies patch
   `holdspeak.runtime.<concern>.<name>`.
5. Stay under the module budget; if the concern wants more, it is two
   concerns.

## Named watch items

- `holdspeak/web/routes/meetings.py` (~1,525): a Phase-26 route module
  with a different shape; if it keeps growing it earns its own phase.
