# HS-1-08 — Step 7: CLI (`holdspeak dictation …`)

- **Project:** holdspeak
- **Phase:** 1
- **Status:** done
- **Depends on:** HS-1-04 (runtime + grammars), HS-1-05 (blocks loader), HS-1-06 (built-in stages), HS-1-07 (controller wiring + assembly seam)
- **Unblocks:** HS-1-09 (doctor reuses `runtime.resolve_backend` + `grammars` compile checks), HS-1-11 (DoD smoke uses the dry-run CLI)
- **Owner:** unassigned

## Problem

Spec §6.2 #8 + §9.3 (`DIR-A-001`) + §9.1 (`DIR-F-010`) require a
`holdspeak dictation` CLI surface so users can:

- `dry-run "<text>"` — execute the full pipeline against a synthetic
  `Utterance` without touching the keyboard typer; print each
  stage's `StageResult`. (DIR-F-010.)
- `blocks ls` — list every block id loaded from the resolved
  `blocks.yaml`.
- `blocks show <id>` — print one block's full spec.
- `blocks validate [--project PATH]` — load + validate the global
  (or project-scoped) `blocks.yaml` and exit non-zero on schema
  failure.
- `runtime status` — report the resolved backend, resolution path,
  configured model, and load status; never fails — `INFO`/`WARN`
  only.

The controller-side builder shipped in HS-1-07 already knows how to
assemble a `DictationPipeline` from `Config.dictation`; HS-1-08
lifts that into a dedicated `assembly.py` so the CLI and controller
share the same code path (one builder, one place to keep correct).

A model-less `dry-run` is a first-class use case (block authors
should be able to validate their YAML and see the prompt-feeding
shape without installing an MLX/GGUF model), so the CLI MUST be
runnable without either backend installed: when the runtime build
fails, the pipeline runs with `llm_enabled=False`, the
`intent-router` stage is skipped (HS-1-03 contract), and the dry-run
prints a clear "no LLM runtime available" warning before the stage
table.

## Scope

- **In:**
  - `holdspeak/plugins/dictation/assembly.py`:
    - `build_pipeline(cfg, *, on_run=None, project_root=None,
      global_blocks_path=None) -> DictationPipeline`. Resolves
      blocks, builds the runtime (or returns `llm_enabled=False`
      pipeline if the runtime can't load), wires `IntentRouter` +
      `KbEnricher`, returns a `DictationPipeline`. Single source of
      truth for "build the DIR-01 pipeline from config".
    - `BuildResult` named-tuple-ish (`pipeline`, `runtime_status:
      Literal["loaded", "unavailable", "disabled"]`,
      `runtime_detail: str`, `blocks: LoadedBlocks`) so callers can
      report what happened without re-running resolution.
  - `holdspeak/controller.py` — `_build_dictation_pipeline` thins to
    a one-liner over `assembly.build_pipeline`. Same external
    behavior; the controller test suite stays green.
  - `holdspeak/commands/dictation.py` — argparse-style
    `run_dictation_command(args)` dispatch with subcommands:
    `dry-run`, `blocks-ls`, `blocks-show`, `blocks-validate`,
    `runtime-status`. (Argparse subparsers in `main.py` pass a
    `dictation_command` arg.)
  - `holdspeak/main.py` — register the `dictation` subcommand and
    nested actions; route to `run_dictation_command`.
  - `tests/unit/test_dictation_cli.py` — table-driven unit tests:
    - `dry-run` happy-path (mock assembly, assert the printed
      output names every stage and the final text).
    - `dry-run` with no-LLM fallback (mock runtime build to fail;
      assert the warning prints and `intent-router` is skipped).
    - `blocks ls` empty + populated.
    - `blocks show <id>` happy + missing-id (exit 2).
    - `blocks validate` valid + invalid YAML (exit 0 / exit 2).
    - `runtime status` reports the resolved backend + path.
- **Out:**
  - Doctor checks (HS-1-09) — `runtime status` here is the CLI
    surface; doctor will share `assembly.build_pipeline` for its
    own check format in HS-1-09.
  - Web-side dry-run (DIR-02 candidate; spec §6.3 #4 calls for a
    read-only API but it's not a phase-exit requirement).
  - Integration tests against a real model — the existing
    `tests/integration/test_runtime_*.py` cover the model-loaded
    paths; the CLI tests run without model dependencies.
  - Mutating subcommands (block edit / create / delete) — DIR-02.

## Acceptance criteria

- [x] `holdspeak/plugins/dictation/assembly.py` ships
      `build_pipeline()` returning a `BuildResult` with the
      pipeline + runtime status + loaded blocks.
- [x] `controller._build_dictation_pipeline` delegates to
      `assembly.build_pipeline` and the existing controller tests
      stay green (no behavior change).
- [x] `holdspeak dictation dry-run "<text>"` prints a stage-by-stage
      report including the final typed text and exits 0 on success.
- [x] `holdspeak dictation dry-run` with no LLM runtime available
      prints a warning, runs with `llm_enabled=False`, and the
      `intent-router` stage is reported as skipped — non-zero exit
      is reserved for hard CLI errors only.
- [x] `holdspeak dictation blocks ls` lists block ids one per line
      (or "no blocks loaded" + exit 0 when empty).
- [x] `holdspeak dictation blocks show <id>` prints the block spec
      and exits 2 when the id is missing.
- [x] `holdspeak dictation blocks validate [--project PATH]` exits 0
      on a valid YAML, exits 2 on a `BlockConfigError` with a clear
      message including the offending file + path.
- [x] `holdspeak dictation runtime status` prints the resolved
      backend, resolution reason, model id/path, and a "loaded |
      available | missing" availability tag — never exits non-zero.
- [x] `uv run pytest -q tests/unit/test_dictation_cli.py
      tests/unit/test_controller.py` → all green.
- [x] Full regression: 882+N passed, 13 skipped, 1 pre-existing
      hardware-only Whisper-loader fail.

## Test plan

- **Unit:** `tests/unit/test_dictation_cli.py` — at least one case
  per subcommand, plus the no-LLM fallback for `dry-run`.
- **Regression:** `uv run pytest -q tests/`.
- **Manual:** None for the model-loaded path (HS-1-11 covers
  end-to-end); the no-LLM dry-run is exercised by the unit tests.

## Notes / open questions

- The CLI uses argparse subparsers (consistent with `intel`,
  `history`, `actions`), not a hand-rolled positional dispatcher.
  Each subcommand gets its own help text.
- `dry-run`'s `Utterance` carries a synthetic `audio_duration_s=0.0`
  and `transcribed_at=datetime.now()`; `project=None` matches the
  controller's DIR-01 default. Block authors that want to test
  `{project.*}` placeholders can wait for DIR-02 project plumbing,
  or provide a project root via `--project` (out-of-scope for this
  story; tracked as a DIR-02 follow-up).
- `blocks validate` accepts an explicit `--project PATH` so authors
  can validate a project-scope `<project_root>/.holdspeak/blocks.yaml`
  before committing it. With no `--project`, validates the global
  `~/.config/holdspeak/blocks.yaml` (or reports "no blocks file
  configured" + exit 0).
- `runtime status` is intentionally an `INFO`/`WARN`-only surface:
  exit 0 even when no backend is available, because the CLI is also
  a discovery tool ("what would I get if I enabled the pipeline?").
  The doctor command (HS-1-09) is where the verdict goes.
