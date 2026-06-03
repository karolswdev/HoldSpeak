# Evidence — HS-32-01 (Class-ify `web_runtime.py` → `WebRuntime`)

**Shipped:** 2026-06-02. The 1,702-line procedural `run_web_runtime()` — which
threaded runtime state through 10 `nonlocal` variables across ~55 inline closures
— is now a `WebRuntime` class. State is instance attributes; the closures are
methods; `run_web_runtime()` is a thin shim. Behavior-preserving.

## What changed

- `holdspeak/web_runtime.py`:
  - **New `WebRuntime` class.** `__init__` builds all runtime state (config,
    plugin host + context provider + project detector, typer, device registry /
    status emitter, recording ticker, voice session, locks, `runtime_status`,
    the MIR/pending-history buffers, `device_stats_cycle`) — the setup the old
    function did before defining its closures.
  - **`run()`** holds the lifecycle: server construction + `WebRuntimeCallbacks`
    wiring, `runtime_url`, the deferred-plugin-queue thread, transcriber warmup,
    recorder + hotkey start, the startup prints, signal-handler registration, the
    `runtime_stop_event` keep-alive loop, and the `finally` shutdown (flush queue,
    stop hotkey, finalize active meeting, stop server, join the queue thread).
    Call order is preserved exactly.
  - Every closure → a method; every `nonlocal` → `self.*`. The 10 reassigned vars
    (`config`, `transcriber`, `meeting_session`, `pending_title`, `pending_tags`,
    `preview_window_seq`, `last_meeting_snapshot`, `mir_profile`,
    `mir_override_intents`, `last_route_preview`) are now plain attribute writes —
    no `nonlocal` declarations remain.
  - The nested `_signal_handler` is a bound method; `_warm()` and
    `_device_transcript_complete` stay as small local closures inside their
    methods (they close over thread-local args, not runtime state).
  - `run_web_runtime(*, no_open, stop_event, register_signal_handlers)` is now a
    4-line shim: `WebRuntime(...).run()`. Signature unchanged — `main.py:412` and
    the entire test suite call it exactly as before.
  - `import sys` moved from inside the function to module scope (was a local
    import used only by the server-start failure branch).

## Why the monkeypatch contract still holds

`tests/unit/test_web_runtime.py` patches module-level names
(`Config`, `MeetingWebServer`, `AudioRecorder`, `HotkeyListener`, `Transcriber`,
`TextTyper`, `MeetingSession`, `drain_plugin_run_queue`, `webbrowser`) and then
calls `run_web_runtime(...)`. The methods reference those names **unqualified**
(module globals resolved at call time), so `monkeypatch.setattr(web_runtime, ...)`
still intercepts them through the class. No test changed.

## Tests ran

- `uv run pytest -q tests/unit/test_web_runtime.py` → **9 passed** (the runtime's
  own regression gate: start/stop services, no-open, env port, warm-on-start,
  actionable-exit, full meeting-control callback round-trip, and the three
  device-voice reply paths).
- `uv run pytest -q --ignore=tests/e2e/test_metal.py` → **2063 passed, 14 skipped**
  — identical to the pre-refactor baseline. Behavior-preserving.
- `uv run ruff check holdspeak/web_runtime.py` → **All checks passed!** (incl. an
  explicit `--select F821` undefined-name sweep — the decomposition lesson from
  Phase 31).

## Decisions / deviations

- **Pure helpers kept as instance methods.** `_normalize_tags`,
  `_meeting_summary_from_state`, `_infer_intent_scores`,
  `_derive_preview_transcript_hash` don't read `self`, but stayed methods (not
  `@staticmethod`) to keep the move verbatim and the call sites `self._x(...)`.
- **Out of scope / left as-is:** the 22 pre-existing `ruff` findings elsewhere in
  `holdspeak/` (confirmed present on the clean merged tree, none in
  `web_runtime.py`) — not this story's surface.
- The done-when "no module-level `nonlocal`-threaded god-function remains" holds:
  `grep nonlocal holdspeak/web_runtime.py` is empty.
