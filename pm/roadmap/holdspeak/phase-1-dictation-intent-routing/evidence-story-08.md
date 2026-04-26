# Evidence — HS-1-08 (CLI)

**Story:** [story-08-cli.md](./story-08-cli.md)
**Date:** 2026-04-25
**Status flipped:** backlog → done

## What shipped

- `holdspeak/plugins/dictation/assembly.py` — `build_pipeline(cfg,
  ...)` returns a `BuildResult(pipeline, blocks, runtime_status,
  runtime_detail)`. Single source of truth for "build the DIR-01
  pipeline from `Config.dictation`". When the runtime factory
  raises (`RuntimeUnavailableError` or anything else), the pipeline
  still ships, but with `llm_enabled=False` so the `intent-router`
  is skipped per the HS-1-03 contract. `runtime_factory` is a test
  seam — production callers leave it `None`.
- `holdspeak/controller.py` — `_build_dictation_pipeline` now
  delegates to `assembly.build_pipeline`. External behavior
  unchanged; the existing 5 controller cases stay green. When the
  runtime is unavailable the controller emits a one-line warning
  (instead of failing) so the live path keeps typing the original
  text via the no-LLM pipeline.
- `holdspeak/commands/dictation.py` — `run_dictation_command(args,
  *, stream=None)` dispatches five subcommands:
  - `dry-run "<text>"` — DIR-F-010. Builds a synthetic
    `Utterance(audio_duration_s=0.0, project=None)`, runs the
    pipeline, prints per-stage `elapsed_ms` / intent / metadata /
    text + the final text + total elapsed.
  - `blocks ls [--project PATH]` — DIR-A-001. Lists block ids.
  - `blocks show <id> [--project PATH]` — DIR-A-001. Prints the
    block spec; exit 2 when the id isn't loaded.
  - `blocks validate [--project PATH]` — DIR-A-001. Loads the YAML
    via `load_blocks_yaml`; exit 2 + clear message on
    `BlockConfigError`; "nothing to validate" no-op when the file
    is absent.
  - `runtime status` — DIR-A-001. Prints requested + resolved
    backend, resolution reason, configured model paths, and
    "available | missing" against the configured paths. Never
    exits non-zero — it's a discovery surface; doctor (HS-1-09)
    owns the verdict.
  - `_build_argparse_subparsers` + `normalize_args` keep the CLI
    surface in one file; `main.py` calls them.
- `holdspeak/main.py` — `dictation` subparser registered between
  `intel` and `doctor`. Dispatches to `run_dictation_command` after
  `normalize_args` collapses nested action strings.
- `tests/unit/test_dictation_cli.py` — 13 cases covering each
  subcommand happy + sad path, including the no-LLM `dry-run`
  fallback (the load-bearing assertion that block authors can
  exercise the CLI without `mlx-lm` / `llama-cpp-python`).

## DIR requirements verified in this story

| Requirement | Verified by |
|---|---|
| `DIR-A-001` CLI exposes dry-run / blocks ls / blocks show / blocks validate / runtime status | One test per subcommand in `test_dictation_cli.py` |
| `DIR-F-010` `dictation dry-run` prints each stage's `StageResult` without invoking the typer | `test_dry_run_prints_each_stage_when_runtime_loaded` (asserts `[intent-router]`, `[kb-enricher]`, matched intent, applied template all appear in the output) |
| HS-1-08 acceptance — model-less dry-run usable for block authors | `test_dry_run_falls_back_to_no_llm_when_runtime_unavailable` (asserts the warning prints and `intent-router` stage is skipped) |
| HS-1-08 acceptance — controller + CLI share one assembly | `_build_dictation_pipeline` is a one-liner over `assembly.build_pipeline`; controller suite stays at 10/10 green after the refactor |

## Test output

### Targeted (CLI)

```
$ uv run pytest -q tests/unit/test_dictation_cli.py
.............                                                            [100%]
13 passed in 0.06s
```

### Controller still green after refactor

```
$ uv run pytest -q tests/unit/test_controller.py
..........                                                               [100%]
10 passed in 0.43s
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q
... [progress dots elided]
1 failed, 895 passed, 13 skipped, 3 warnings in 17.01s
FAILED tests/e2e/test_metal.py::TestWhisperTranscription::test_model_loads
```

Pre-existing hardware-only Whisper-loader failure (recorded as the
known baseline since HS-1-03). Pass delta: 882 → 895 (+13 new CLI
cases).

## Files in this commit

- `holdspeak/plugins/dictation/assembly.py` (new)
- `holdspeak/commands/dictation.py` (new)
- `holdspeak/controller.py` (modified — `_build_dictation_pipeline` delegates)
- `holdspeak/main.py` (modified — register dictation subcommand)
- `tests/unit/test_dictation_cli.py` (new)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/story-08-cli.md` (new — story authored, status flipped to done in same commit)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/evidence-story-08.md` (this file)
- `pm/roadmap/holdspeak/phase-1-dictation-intent-routing/current-phase-status.md` (story table + "Where we are" + last-updated)
- `pm/roadmap/holdspeak/README.md` (last-updated line)

## Notes

- `runtime status` does **not** load the model. It checks
  `Path(...).exists()` against the configured `mlx_model` /
  `llama_cpp_model_path` so users can scan availability without
  paying the cold-load cost. Doctor (HS-1-09) gets the "actually
  load it" check.
- The CLI lives in `tests/unit/` rather than `tests/integration/`
  because every case mocks at the assembly seam (`build_runtime`
  factory) and writes a temporary `blocks.yaml` — there's no real
  network or disk dependency. `tests/integration/test_runtime_*.py`
  already cover the model-loaded paths.
- `dry-run`'s synthetic `Utterance(project=None)` matches what the
  controller currently passes (DIR-01 default). Block authors that
  want to test `{project.*}` placeholders will get DIR-02 project
  plumbing; for now `kb-enricher`'s DIR-F-007 skip prints a clear
  warning naming the unresolved key.
- The shared assembly helper is the natural home for HS-1-09's
  doctor checks: `build_pipeline` already returns enough to render
  the `LLM runtime` and `Structured-output compilation` lines.
