# Evidence — HS-52-01: Carve the dictation-dispatch seam out of `web_runtime`

Write-once record of the scoped-E carve. The dictation orchestration is out of the
god-object and into a standalone, unit-testable module, byte-identical.

## What shipped

- **New module `holdspeak/dictation_runner.py`** (143 lines): `run_dictation_pipeline(text,
  *, config, server, audio_duration_s, transcribed_at, agent_reply_session=None) -> str`.
  The body is the old `_maybe_run_dictation_pipeline` verbatim, with the two `self`
  collaborators it touched (`self.config`, `self.server`) lifted to explicit parameters.
  Off (pipeline disabled) or on any error it returns the input text unchanged; journaling
  stays a best-effort side-channel.
- **`web_runtime.py`**: the ~90-line inline method is now a thin delegate that calls
  `run_dictation_pipeline(...)` with `self.config` / `self.server`. The file shrank from
  **2341 to 2255 lines**. One import added (`from .dictation_runner import
  run_dictation_pipeline`).

### Naming note
The module is `dictation_runner`, not `dictation_runtime`: the name `dictation_runtime`
is already taken by the DIR-01 LLM backend layer (`holdspeak/plugins/dictation/runtime.py`,
covered by `tests/unit/test_dictation_runtime.py`). `dictation_runner` keeps the
orchestration distinct from the LLM runtime. (The brief named it `dictation_runtime.py`
only as an example.)

## Why this is byte-identical

The extraction is mechanical: same inputs, same logic, same return. The call site
(`web_runtime.py:1607`) is unchanged; the only behavioural surface, the typed text, is
the function's return value, and the existing dictation integration + e2e tests exercise
it end to end and still pass with no edits. The phase's later dispatch branch (HS-52-04)
will sit at the top of this seam; this story added no new behaviour.

## Tests

New focused unit test `tests/unit/test_dictation_runner.py` (drives the extracted entry
directly, which was impossible while it lived inline on `WebRuntime`):
- `test_disabled_pipeline_returns_text_unchanged` — the off path (the common case).
- `test_missing_dictation_config_returns_text_unchanged` — defensive default.
- `test_build_pipeline_error_falls_back_to_text` — the except path returns the text.
- `test_pipeline_not_loaded_returns_text` — `runtime_status != "loaded"` returns the text.
- `test_enabled_pipeline_returns_final_text` — happy path returns `run.final_text`.
- `test_web_runtime_method_delegates` — the `WebRuntime` method passes `config`/`server`
  through to the carved function.

```
uv run pytest -q tests/unit/test_dictation_runner.py
-> 6 passed

uv run pytest -q -k "dictation and (pipeline or project_context or runtime)" --ignore=tests/e2e/test_metal.py
-> 113 passed, 3 skipped   (the byte-identical guard, unchanged)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2460 passed, 17 skipped   (was 2454 at Phase 51 close; +6 is the new unit tests)
```

0 `_built/` tracked; no UI bundle touched.

## Not done here (by design)

- No feature. The voice-command dispatch decision (match keyword -> fire action) lands at
  the top of this seam in HS-52-04.
- Only the dictation path was carved; the rest of `web_runtime` (hotkey/device/meeting/
  activity) is untouched. Full candidate E stays a backlog watch item.
