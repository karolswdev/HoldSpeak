# Evidence — HS-3-02: wire `detect_project_for_cwd()` into Utterance + blocks loader

- **Phase:** 3 (Dictation Loop Closure)
- **Story:** HS-3-02
- **Captured at HEAD:** `6659662` (pre-commit)
- **Date:** 2026-04-26

## What shipped

### Controller wiring (`holdspeak/controller.py`)

- New attribute `self._dictation_project: Optional[dict[str, Any]]` initialised to `None`.
- `_build_dictation_pipeline()` now calls `detect_project_for_cwd()` once at build time, stores the result on `self._dictation_project`, and passes `project_root=Path(self._dictation_project["root"])` (or `None`) through to `assembly.build_pipeline`.
- `_maybe_run_dictation_pipeline()` populates `Utterance.project=self._dictation_project` instead of hard-coded `None`.
- `apply_runtime_config()` clears `self._dictation_project` so a config edit (e.g. flipping `dictation.pipeline.enabled`) triggers re-detection on the next pipeline build.

### CLI wiring (`holdspeak/commands/dictation.py`)

- `_cmd_dry_run` calls `detect_project_for_cwd()` at the top, passes `project_root` to `build_pipeline`, populates `Utterance.project`, and prints a `project: <name> (<anchor> @ <root>)` line (or `project: (none detected)`) so the surface is visible in dogfood.

### Doctor surface (`holdspeak/commands/doctor.py`)

- New `_check_dictation_project_context(config)` returning a `DoctorCheck`:
  - `PASS` with `"disabled"` detail when `dictation.pipeline.enabled is False`.
  - `PASS` with `"detected <name> (anchor=<a>) at <path>"` when a project is detected (suffix `+ KB` when `<root>/.holdspeak/project.yaml` is present).
  - `WARN` with `"no project root detected from cwd=..."` and a fix hint pointing at `mkdir <project>/.holdspeak` otherwise.
- Inserted ahead of `_check_dictation_runtime` in `collect_doctor_checks()` so the dictation block reads top-down: project context → runtime → constraint compile.

## Test output

### Targeted (HS-3-02 surfaces)

```
$ uv run pytest tests/unit/test_doctor_command.py tests/integration/test_dictation_project_context.py --timeout=30 -q
............................                                             [100%]
28 passed in 2.06s
```

The 4 new integration tests:

```
tests/integration/test_dictation_project_context.py::test_cli_dry_run_populates_project_from_cwd PASSED
tests/integration/test_dictation_project_context.py::test_cli_dry_run_reports_no_project_outside_tree PASSED
tests/integration/test_dictation_project_context.py::test_controller_pipeline_build_passes_project_root_and_utterance_carries_project PASSED
tests/integration/test_dictation_project_context.py::test_controller_apply_runtime_config_clears_project PASSED
```

The 3 new doctor unit tests:

```
test_project_context_check_pass_when_pipeline_disabled
test_project_context_check_pass_when_project_detected
test_project_context_check_warn_when_no_project_detected
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
988 passed, 12 skipped in 16.90s
```

Pass delta vs. HS-3-01 baseline (981 passed): **+7** (4 integration
+ 3 doctor unit). 12 skipped is unchanged.

## Practical effect

Prior to this commit, `Utterance.project` was hard-coded to `None`
at both construction sites — the kb-enricher stage had nothing to
substitute for `{project.name}` / `{project.kb.*}` placeholders, so
the entire DIR-01 block-grounded path was inert in dogfood. Per-project
`<root>/.holdspeak/blocks.yaml` files were also unreachable because
no caller passed a non-`None` `project_root` to `assembly.build_pipeline`.

After this commit:
- Launching `holdspeak` from inside a project directory means every
  utterance carries `{name, root, anchor, kb?}` to every stage.
- A `<root>/.holdspeak/blocks.yaml` is auto-loaded over the global
  one (DIR-01 §8.1 replacement semantics).
- `holdspeak doctor` confirms project detection at a glance.

## Deviations from story scope

- The two `Utterance` constructors run in different process
  contexts; the long-running controller detects once at pipeline
  build (cwd is fixed for the process), the short-lived CLI detects
  on every `_cmd_dry_run` invocation. This matches the story's
  "Notes" section and is documented in evidence rather than as
  test-side coverage (testing the controller's "detect once, reuse"
  invariant is implicit in `test_controller_pipeline_build_passes_project_root_and_utterance_carries_project`).
- No caching layer added — function is cheap enough; story Notes
  explicitly authorised deferring this.

## Out-of-scope (deferred per story)

- Narrowing `ProjectContext` from `dict[str, Any]` to a dataclass.
- New project-detector heuristics (HS-3-01 territory).
- Web/UI surfacing of project context.
- LRU cache across utterances — only add if profiling later shows it matters.
