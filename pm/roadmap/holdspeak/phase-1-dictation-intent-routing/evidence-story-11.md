# Evidence — HS-1-11 (DoD sweep)

**Story:** [story-11-dod.md](./story-11-dod.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done
**Phase verdict:** DIR-01 complete.

## What shipped

- `holdspeak/config.py` — DIR-C-002 enforced. New module-level
  `_KNOWN_DICTATION_STAGES = ("intent-router", "kb-enricher")` +
  `DictationConfigError`; `DictationPipelineConfig.__post_init__`
  rejects unknown stage IDs at construction with a message that
  surfaces both the offending IDs and the canonical list.
- `tests/unit/test_config.py::TestDictationPipelineValidation` —
  default + accept-known + reject-unknown (3 cases).
- `holdspeak/plugins/dictation/runtime_mlx.py` — two real bugs fixed
  during the live-model exercise:
  1. `~` not expanded → `mlx_lm.load` interpreted the path as an
     HF repo id and failed. Fixed by passing the expanded path
     when the configured value looks like a filesystem path
     (`/`, `~`, `.`); bare `namespace/repo_name` still go through
     unmodified.
  2. `outlines.processors.JSONLogitsProcessor` no longer exists in
     `outlines>=1.0`. Refactored `MlxRuntime.classify` to use the
     current `outlines.from_mlxlm(model, tokenizer)` +
     `Generator(omodel, output_type=JsonSchema(schema_dict))`
     shape. Test seam moved from `processor_factory + generate_fn`
     to `generator_factory(model, tokenizer, schema_dict) ->
     callable(prompt, max_tokens) -> str`. The 4 mlx-runtime unit
     cases were updated to the new seam.
- `tests/integration/test_runtime_mlx.py` — gate updated to detect
  the new `outlines` API; previously this integration test always
  skipped (no `JSONLogitsProcessor` to import). It is now active
  on the reference Mac and passes against the real
  `Qwen3-8B-MLX-4bit`.
- `~/.config/holdspeak/blocks.yaml` — sample block-config authored
  for the e2e (kept in the user scope; not committed). Two blocks
  (`ai_prompt_buildout`, `documentation_exercise`) using
  `mode: replace` so the rendered template is the final typed
  text.
- Evidence bundle at
  `docs/evidence/phase-dir-01/20260425-2027/` per spec §11.2 with
  the DIR-* traceability matrix, per-area UT logs (one per area:
  pipeline / router / enricher / blocks / runtime / config /
  security), CLI + doctor logs, structured-output compile log,
  DIR-O-001 sample log line, real-model trace, and phase summary.

## DIR requirements verified in this story

The full DIR-* matrix is in
[`docs/evidence/phase-dir-01/20260425-2027/03_traceability.md`](../../../docs/evidence/phase-dir-01/20260425-2027/03_traceability.md).
Highlights specific to HS-1-11:

| Requirement | Method | Verified by |
|---|---|---|
| `DIR-C-002` Unknown stage IDs rejected at config load time | UT | `tests/unit/test_config.py::TestDictationPipelineValidation::test_unknown_stage_id_rejected` (raises `DictationConfigError` naming the bad ID + the canonical list) |
| `DIR-R-001` Pipeline runs end-to-end on the reference Mac with `mlx` Qwen3-8B-MLX-4bit | MT | `61_runtime_trace.txt` — three utterances classify correctly (intents `ai_prompt_buildout` / `documentation_exercise` / no-match), warm timings ≈ 2.7 s |
| Phase exit #4 — disabled-state byte-identical | UT | `test_dictation_disabled_path_is_byte_identical_and_does_not_build_pipeline` stays green; the controller test suite reports 10/10 after the assembly refactor |
| Phase exit #5 — doctor reports the new checks cleanly in both states | AT | `61_runtime_trace.txt` final section (both `pipeline.enabled=false` and `=true` produce `[PASS]` lines) |

## Test output

### Targeted (DIR-C-002)

```
$ uv run pytest -q tests/unit/test_config.py -k Dictation
...                                                                      [100%]
3 passed, 58 deselected in 0.06s
```

### Mlx integration (now active)

```
$ uv run --extra dictation-mlx pytest tests/integration/test_runtime_mlx.py -v
tests/integration/test_runtime_mlx.py::test_mlx_runtime_classify_returns_valid_json PASSED [100%]
1 passed in 3.75s
```

### Real-model dry-run (excerpt — full output in `61_runtime_trace.txt`)

```
--- input: Claude, please write a Python function that parses a CSV file and returns a list of dicts.
[intent-router] elapsed_ms=2696.05
  intent: matched=True block_id=ai_prompt_buildout confidence=1.00
[kb-enricher] elapsed_ms=0.02
  metadata: {'applied_block': 'ai_prompt_buildout', 'mode': 'replace'}
final_text: 'Claude, please write a Python function ... \n\n---\n(HoldSpeak: prompt-buildout block matched — context appended)\n'
total_elapsed_ms: 2696.09
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q
1 failed, 907 passed, 12 skipped, 3 warnings in 25.95s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

Pre-existing hardware-only Whisper-loader failure (recorded as the
known baseline since HS-1-03; unrelated). Pass delta vs. HS-1-09:
+4 (3 new config-validation cases + 1 mlx integration test now
active instead of skipped).

## Files in this commit

- `holdspeak/config.py` (modified — DIR-C-002 validation +
  `DictationConfigError`)
- `holdspeak/plugins/dictation/runtime_mlx.py` (modified — `~`
  expansion + outlines 1.x API binding)
- `tests/unit/test_config.py` (extended)
- `tests/unit/test_dictation_runtime.py` (test seam updated for
  the new `generator_factory`)
- `tests/integration/test_runtime_mlx.py` (gate updated for
  `outlines>=1.0`)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-11-dod.md` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-11.md` (this file)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/README.md` (last-updated line — phase complete)
- `docs/evidence/phase-dir-01/20260425-2027/` (full evidence bundle —
  `00_manifest.md`, `01_env.txt`, `02_git_status.txt`,
  `03_traceability.md`, `10_ut_*.log` × 7, `12_*`, `40_*`, `41_*`,
  `60_logs_sample.txt`, `61_runtime_trace.txt`, `99_phase_summary.md`)

## Notes

- The DIR-O-001 sample log in `60_logs_sample.txt` was generated
  programmatically via the controller's `_emit_pipeline_run`
  callback fed a representative `PipelineRun`, rather than
  scraped from a live `holdspeak` session log. The shape (keys,
  types, values) is identical to what the live controller writes;
  the runtime test (`tests/unit/test_controller.py::test_dictation_enabled_runs_pipeline_and_types_final_text`)
  is the active assertion that this is what the controller emits.
- The HF model snapshot is **not** committed (it's a 4.35 GB
  binary in `~/Models/`, not in the repo). The `61_runtime_trace.txt`
  captures `ls -la` of the snapshot dir as proof of presence at
  capture time.
- Sample `~/.config/holdspeak/blocks.yaml` is also not committed
  (user-scope file). The structure is documented in spec §8.2;
  the e2e trace shows it loaded with 2 blocks.
- DIR-S-003 (no network calls in the runtime modules) verified by
  `grep -nE 'urllib|socket|requests|httpx|http\.client'` against
  `runtime*.py` returning no matches — captured at the bottom of
  `61_runtime_trace.txt`. The runtime touches only `mlx_lm.load`
  + the `outlines` JSON-schema generator; both operate on local
  files.
