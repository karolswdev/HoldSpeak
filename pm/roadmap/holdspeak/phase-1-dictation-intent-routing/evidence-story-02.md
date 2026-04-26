# Evidence — HS-1-02 (Transducer contracts)

**Story:** [story-02-contracts.md](./story-02-contracts.md)
**Date:** 2026-04-25
**Status flipped:** ready → done

## What shipped

- `holdspeak/plugins/dictation/__init__.py` — new package marker.
- `holdspeak/plugins/dictation/contracts.py` — `Utterance`,
  `IntentTag`, `StageResult` (all `@dataclass(frozen=True)`),
  `Transducer` (`Protocol`, `@runtime_checkable`). Field names + types
  match DIR-01 §6.4 exactly. `ProjectContext` aliased to
  `dict[str, Any]` for now (see Notes).
- `tests/unit/test_dictation_contracts.py` — five cases.

## Test output

```
$ uv run pytest tests/unit/test_dictation_contracts.py -q
.....                                                                    [100%]
5 passed in 0.04s
```

The five cases exercised:

1. `test_utterance_construction_and_immutability` — field round-trip + `FrozenInstanceError` on mutation.
2. `test_intent_tag_defaults_and_immutability` — `extras` defaults to `{}`, immutable.
3. `test_stage_result_defaults_and_immutability` — `warnings`/`metadata` default to empty containers, immutable.
4. `test_transducer_protocol_conformance` — `isinstance(stub, Transducer)` true; `isinstance(missing_run, Transducer)` false.
5. `test_transducer_run_smoke` — minimal stub `run()` returns a `StageResult` with the expected fields.

## Regression sweep

```
$ uv run pytest tests/ -q --timeout=30
... (output trimmed) ...
2 failed, 783 passed, 10 skipped, 3 warnings in 61.72s (0:01:01)
FAILED tests/e2e/test_metal.py::TestMicrophoneRecording::test_can_record_short_audio
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

The two failures are in `tests/e2e/test_metal.py`, which is the
`metal` marker per `pyproject.toml`: "hardware tests requiring real
mic/model/keyboard (local only)." They exercise `AudioRecorder` mic
recording and Whisper model loading — both touch hardware/models, not
the plugin contracts. Pre-existing environmental failures, not
regressions from HS-1-02.

## Notes

- `Plugin.kind` extension: the existing system uses a free-form
  `kind: str` on `DeterministicPlugin` (`holdspeak/plugins/builtin.py`)
  rather than an enum, so accepting `"transducer"` required no code
  change. Existing kinds (`synthesizer`, `validator`,
  `artifact_generator`, `signals`) are unchanged. Spec §6.4
  ("`Transducer` is added as a new value of the existing `Plugin.kind`
  field") is satisfied by convention without a code-level extension.
- `ProjectContext` is a `dict[str, Any]` alias because
  `holdspeak/plugins/project_detector.py` does not currently expose a
  named `ProjectContext` dataclass — it produces context dicts. A
  stronger named alias can land later without breaking this contract;
  HS-1-06 (kb-enricher) will read keys off whatever shape the producer
  publishes.

## Files in this commit

- `holdspeak/plugins/dictation/__init__.py` (new)
- `holdspeak/plugins/dictation/contracts.py` (new)
- `tests/unit/test_dictation_contracts.py` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-02-contracts.md` (status flip + acceptance criteria checked)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-02.md` (this file)
- `pm/roadmap/holdspeak/README.md` (last-updated line)
