# Phase 63 — Agent Brief (read this first)

**Phase 63 — Backend Decomposition** for HoldSpeak. Backlog row **E**,
picked by the owner ("E, puh-lease") right after Phase 62. The backend twin
of [Phase 54](../phase-54-dictation-frontend-decomposition/): the same
disease, the same cure, the same proof standard.

## 0. Mission

Two god-objects pay down their debt: `web_runtime.py` (**2,635 lines** —
it has regrown PAST its pre-Phase-52 size of 2,341; the wake word, devices,
and routing glue all landed there) and `meeting_session.py` (**1,674
lines** — models + recording + transcription + intel + persistence +
mutations in one file). Carve both into single-concern modules,
**behavior-preserving** (code moved verbatim; assertions byte-identical),
locked by a backend density guard so they cannot regrow.

## 1. The one thing you must not get wrong

**This is a refactor, not a rewrite.** Method bodies move verbatim. The
only permitted test edits are monkeypatch TARGET module paths where a
module-level global moved with its method (each one listed in evidence);
every assertion stays byte-identical. If a move makes you want to "improve"
a body, stop — improvements are out of scope.

## 2. Rules (the standing set)

PMO gate (7 boxes; evidence with done-flips; final-summary at exit); no
`Co-Authored-By`; cadence per shipping commit; one PR, branch
`phase-63-backend-decomposition`, merged on green; tests via
`uv run pytest -q --ignore=tests/e2e/test_metal.py`. Docs get their own
story (the standing rule). The voice guard is live for doc prose.

## 3. Ground truth (verified at scaffold)

- **Sizes:** web_runtime.py 2,635 / meeting_session.py 1,674 /
  web_server.py 563 (already thin — Phase 26/34 carved the routes;
  web_server is NOT in scope) / dictation_runner.py 248 (the Phase-52
  slice of E, the precedent).
- **The monkeypatch census** (the carve's hard constraint): tests patch
  11 distinct globals on `holdspeak.web_runtime`. Six are used only by
  `__init__`/`run` which STAY in the core module (TextTyper,
  MeetingWebServer, HotkeyListener, AudioRecorder,
  build_desktop_presence_host, ProjectDetectorPlugin). Five ride with
  moved methods and their patch sites move with them: `Transcriber`
  (_ensure_transcriber_loaded), `run_dictation_pipeline`
  (_transcribe_and_type, _transcribe_wake), `dispatch_voice_command`,
  `drain_plugin_run_queue`, `MeetingSession` (_start_meeting).
- **meeting_session has NO monkeypatched globals**; 38 test files import
  names from it (`MeetingState`, `TranscriptSegment`, `IntelSnapshot`,
  `Bookmark`, `MeetingSession`). Re-exports from `meeting_session.py`
  keep every one unmodified — the module stays the canonical public
  import point (that is API, not a compat shim).
- **The mechanic:** mixin classes in new packages, composed by the
  original class — the Python equivalent of Phase 54's partials. Verbatim
  method moves, zero call-site changes, `self` keeps working.
  - `holdspeak/runtime/` — WebRuntime's concern modules.
  - `holdspeak/meeting/` — MeetingSession's concern modules + the pure
    models.
- **WebRuntime concern map** (line ranges at scaffold): transcriber
  state/load/warm (~266–337); activity+state+status payloads (~345–512,
  1035–1090); meeting glue incl. start/stop + broadcasts + action items
  (~338, 407–427, 521–634, 692–954, 1138–1204, 1570–1587); MIR/routing
  glue (~428–439, 1205–1569); deferred plugin queue (~955–1034); dictation
  capture + hotkey + tmux + voice commands (~1588–1857, 2151–2221); wake
  glue (~1858–2150); device glue (~2222–2468); core keeps __init__,
  config-apply/presence-sync, onboarding nudges, signal/run,
  run_web_runtime.
- **MeetingSession concern map:** pure models (~54–273: Bookmark,
  TranscriptSegment, IntelSnapshot, MeetingSaveResult, MeetingState +
  helpers); transcribe loop + overlap + chunks (~1228–1439); intel
  (~1527–1674); persistence (save ~1440–1526); mutations (action items /
  title / tags ~979–1227); core keeps __init__, lifecycle
  (start/stop/bookmarks), device attach, broadcasts.
- **The Phase-54 proof standard:** density guard with carve-don't-bump
  messages; the full suite as the behavior-preservation proof; a live
  closeout (the runtime boots and serves; a meeting start/stop and a
  dictation dry-run work end to end on the real server).

## 4. Stories

- **HS-63-01 — the meeting models.** `holdspeak/meeting/models.py`: the
  five dataclasses + module helpers move verbatim; `meeting_session.py`
  re-exports. Zero test changes.
- **HS-63-02 — MeetingSession mixins.** `holdspeak/meeting/`:
  `transcribe_loop.py`, `intel.py`, `mutations.py`, `persistence.py` as
  mixins; `meeting_session.py` keeps lifecycle + assembly, lands under
  the budget. Zero test changes expected (no patched globals).
- **HS-63-03 — WebRuntime mixins, the feature glue.** `holdspeak/
  runtime/`: `wake_glue.py`, `device_glue.py`, `dictation_capture.py`
  (transcribe-and-type, hotkey, tmux, voice-command dispatch). The
  patch-target moves happen here (run_dictation_pipeline,
  dispatch_voice_command, Transcriber if touched) — documented per site.
- **HS-63-04 — WebRuntime mixins, the platform glue.** `meeting_glue.py`,
  `routing_glue.py`, `plugin_queue.py`, `activity.py`,
  `transcriber_state.py`; the core `web_runtime.py` lands under the
  budget (boot/run/config only).
- **HS-63-05 — the backend density guard + docs.** `tests/unit/
  test_backend_density_guard.py` (scoped budgets: the two cores + every
  new module ≤650, carve-don't-bump messages, proven both ways);
  `docs/internal/ARCHITECTURE_WEB_FRONTEND.md` gains the backend twin
  section or a sibling doc records the pattern + the concern map;
  CONTRIBUTING pointer.
- **HS-63-06 — closeout.** Live: the real runtime boots (`run_web_runtime`
  path), serves /api/status, a meeting starts and stops through the real
  routes, a dictation dry-run runs through the real pipeline route; zero
  page errors on the cockpit. Full suite; final-summary; BACKLOG E
  flipped; README; PR merged on green; memory.

## 5. Gotchas

- **Patch-target moves are the ONLY test edits.** Track every one in the
  story evidence with before → after module paths.
- **Module-global lookups travel with the method.** When a moved body
  references a name, import that name in the mixin's module; check
  whether any test patches it (the census above) before assuming.
- **Import cycles:** mixin modules must not import `web_runtime` (the
  core imports THEM). Anything the mixin needs from the core arrives via
  `self`.
- **`web_server.py` and the route modules are OUT of scope** (already
  carved; routes/meetings.py at 1,525 is a watch item, note it in the
  guard's comments, do not carve it now).
- **GGML_NO_BACKTRACE + the MLX thread pinning are LOAD-BEARING** (Phase
  60): do not touch `holdspeak/__init__.py` or `_MlxTranscriber`'s
  executor while moving transcriber-adjacent code.
- The deferred-intel queue and voice-session floor logic are
  concurrency-sensitive — verbatim moves only, locks travel with their
  methods.
