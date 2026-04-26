# Evidence — HS-1-07 (Controller wiring)

**Story:** [story-07-controller.md](./story-07-controller.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/controller.py` — DIR-01 dictation pipeline plumbed into
  the live voice-typing path:
  - `_maybe_run_dictation_pipeline(text, audio_duration_s,
    transcribed_at)` is invoked in
    `_on_hotkey_release.transcribe_and_type` between
    `text_processor.process` and `typer.type_text`. Returns the
    (possibly enriched) text. Any unexpected exception falls back to
    the input text — defense in depth on top of the executor's
    per-stage error isolation (DIR-F-003).
  - `_get_dictation_pipeline()` lazy-builds and caches a
    `DictationPipeline` instance per controller. A build failure is
    sticky for the controller lifetime (`_dictation_pipeline_failed`)
    so a missing model file or unavailable backend never rebuilds on
    every keystroke; recovery seam is `apply_runtime_config()`, which
    drops the cache + failure flag.
  - `_build_dictation_pipeline()` is the **only** place
    `holdspeak.plugins.dictation.*` is imported, all imports inside
    the function body. Disabled-state never touches them.
  - `_emit_pipeline_run(run)` is the controller-side `on_run`
    callback that emits the DIR-O-001 structured log line — stage
    IDs, per-stage `elapsed_ms` map, intent matched + block_id,
    warnings, total_elapsed_ms, short_circuited. Keeping this
    controller-side preserves the HS-1-03 invariant that the
    executor is I/O-free.
  - `apply_runtime_config()` invalidates the cached pipeline + clears
    the failure flag so config edits to `dictation.*` take effect on
    the next utterance.
  - Module-level `_GLOBAL_BLOCKS_PATH = ~/.config/holdspeak/blocks.yaml`
    matches spec §8.1; per-project root is `None` for DIR-01 (project
    plumbing is a DIR-02 concern; `kb-enricher`'s DIR-F-007 skip
    handles missing `{project.*}` context cleanly).
- `tests/unit/test_controller.py` — 5 new cases covering the
  byte-identical disabled path, the enabled happy path + log
  emission, build-failure fallback (sticky), run-time exception
  fallback, and cache invalidation by `apply_runtime_config`.

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-C-001` Defaults keep DIR-01 fully off | `test_dictation_disabled_path_is_byte_identical_and_does_not_build_pipeline` (asserts builder not called, output == input, no cached pipeline) |
| `DIR-F-003` Stage exception → original text typed | `test_dictation_pipeline_run_exception_falls_back_to_processed_text` (controller-level fallback above the executor's own per-stage isolation) |
| `DIR-O-001` Structured per-run log line | `test_dictation_enabled_runs_pipeline_and_types_final_text` (asserts `dictation_pipeline_run` log line with stage_ids / elapsed_ms / intent / total_elapsed_ms keys) |
| Phase exit #4 — disabled byte-identical | Same disabled-path test: typer receives `text_processor.process` output verbatim; no dictation modules touched |

## Test output

### Targeted (controller)

```
$ uv run pytest -q tests/unit/test_controller.py
..........                                                               [100%]
10 passed in 0.55s
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q
... [progress dots elided]
=================================== FAILURES ===================================
__________________ TestWhisperTranscription.test_model_loads ___________________
...
E       AttributeError: 'Transcriber' object has no attribute '_path_or_hf_repo'
1 failed, 882 passed, 13 skipped, 3 warnings in 17.53s
```

Pre-existing hardware-only Whisper-loader failure (recorded in
HS-1-03..06 evidence as the known baseline). Pass delta: 877 → 882
(+5 new controller cases).

## Files in this commit

- `holdspeak/controller.py` (modified)
- `tests/unit/test_controller.py` (extended)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-07-controller.md` (new — story authored, status flipped to done in same commit)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-07.md` (this file)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- The disabled-byte-identical guarantee is enforced by **lazy-import
  discipline**, not by a sentinel flag. `_maybe_run_dictation_pipeline`
  early-returns when `cfg.pipeline.enabled is False` before reaching
  the builder; the builder is the only place dictation modules are
  imported. The unit test confirms the builder is never called on
  the disabled path. (A `'holdspeak.plugins.dictation.pipeline' not in
  sys.modules` check would be unreliable in a test process where
  other tests have already imported the dictation modules; the
  builder-not-called assertion is the load-bearing one.)
- Build failures are sticky on purpose: a missing model file or
  uninstalled extra is the kind of error that won't fix itself
  utterance-to-utterance, and re-trying on every release would
  hammer the user with the same warning. Recovery is explicit via
  `apply_runtime_config()` (called from the settings-screen apply
  flow).
- `Utterance.audio_duration_s = len(audio) / 16000` uses the project's
  fixed mic sample rate (set in `holdspeak/audio.py`); the constant
  `_AUDIO_SAMPLE_RATE_HZ` is named at module scope to keep the
  controller from reaching into the audio module's internals.
- `max_total_latency_ms` enforcement (DIR-R-003) is still deferred
  per HS-1-03's note. The executor records `total_elapsed_ms`, the
  controller logs it, and a future story can add a hard kill once
  there's real latency data — no measurement gate per the
  2026-04-25 amendment.
