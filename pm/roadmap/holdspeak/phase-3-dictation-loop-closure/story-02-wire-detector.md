# HS-3-02 — Wire `detect_project_for_cwd()` into `Utterance` + blocks loader

- **Project:** holdspeak
- **Phase:** 3
- **Status:** done
- **Depends on:** HS-3-01 (detector function exists + unit-tested)
- **Unblocks:** HS-3-03 (llama_cpp leg can verify project context flowing); kb-enricher (HS-1-06) becoming live in dogfood
- **Owner:** unassigned

## Problem

HS-3-01 ships the pure `detect_project_for_cwd()` function. This
story wires it through the two `Utterance` construction sites
(`holdspeak/controller.py:265`, `holdspeak/commands/dictation.py:89`)
and through the `holdspeak/plugins/dictation/blocks.py:150` loader's
unused `project_root` parameter, so the entire DIR-01 block-grounded
path runs for real on dogfood.

## Scope

- **In:**
  - `holdspeak/controller.py` and `holdspeak/commands/dictation.py` populate `Utterance.project` from `detect_project_for_cwd()` instead of hard-coding `None`.
  - The block-loader call site (`holdspeak/plugins/dictation/blocks.py` callers) passes the detected `project_root` so per-project `<root>/.holdspeak/blocks.yaml` is auto-discovered per spec §8.1.
  - Integration test exercising the controller path end-to-end: feed a synthetic transcript from a temp project tree, assert the pipeline's `Utterance.project` is non-None and the kb-enricher resolves a `{project.name}` placeholder against it.
  - Integration test for the CLI path (`holdspeak dictate ...`): same shape.
  - `holdspeak doctor` reports project-context detection status for the current cwd (detected | none | error). Either a new sub-check or an extension of an existing dictation/doctor surface — pick at implementation time.
- **Out:**
  - Narrowing `ProjectContext` from `dict[str, Any]` to a dataclass — DIR-01 §6.4 explicitly leaves the loose typing.
  - New project-detector heuristics. HS-3-01 owns the function; this story consumes it.
  - Web/UI surfacing of project context.
  - Caching across utterances — only add if profiling shows it matters.

## Acceptance criteria

- [x] `holdspeak/controller.py` and `holdspeak/commands/dictation.py` both populate `Utterance.project` from `detect_project_for_cwd()` (no more hard-coded `None`).
- [x] Block loader call sites pass the resolved `project_root` (`HoldSpeakController._build_dictation_pipeline` and `_cmd_dry_run` both pass it through to `assembly.build_pipeline`).
- [x] Integration test (controller path): `test_controller_pipeline_build_passes_project_root_and_utterance_carries_project` asserts `captured["project_root"] == root.resolve()` and `utt.project["name"] == "myproj"` from a temp project tree.
- [x] Integration test (CLI path): `test_cli_dry_run_populates_project_from_cwd` runs `_cmd_dry_run` from a temp project tree and asserts `"project: myproj"` + the project's blocks file is loaded.
- [x] `holdspeak doctor` ships `_check_dictation_project_context` (PASS when detected, WARN when no project, PASS-skip when pipeline disabled); 3 unit tests cover the cases.
- [x] Full regression: `uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py` → 988 passed, 12 skipped (delta +7 vs. HS-3-01 baseline 981).

## Test plan

- **Integration:** the two end-to-end tests above, using `tmp_path` + `monkeypatch` of cwd.
- **Doctor:** unit test asserting the detection-status surface.
- **Regression:** the documented full-suite command (metal excluded).

## Notes / open questions

- The two Utterance constructors run in different process contexts (controller is the long-running TUI/web process; CLI is short-lived). `detect_project_for_cwd()` is called with `Path.cwd()` at construction time in both — fine for the CLI; the long-running controller currently uses its launch cwd, which is the right thing for a hold-to-talk tool (the user usually launches `holdspeak` from the project they're working in). Document this in evidence.
- If profiling shows `detect_project_for_cwd()` running on every utterance is noticeable, add a one-line LRU cache keyed on `(cwd, mtime of nearest anchor)`. Don't pre-optimize.
