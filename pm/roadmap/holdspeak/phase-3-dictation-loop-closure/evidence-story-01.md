# Evidence — HS-3-01: `detect_project_for_cwd()` pure function

- **Phase:** 3 (Dictation Loop Closure)
- **Story:** HS-3-01
- **Captured at HEAD:** `c27e8f0` (pre-commit)
- **Date:** 2026-04-26

## What shipped

- New module `holdspeak/plugins/dictation/project_root.py` (~130 LOC) defining `detect_project_for_cwd(start: Path | None = None) -> ProjectContext | None`.
- Walks from `start` (default `Path.cwd()`) up toward `$HOME`/filesystem root; returns the first ancestor (inclusive) containing one of the recognized anchors. Anchor priority within a single directory: `.holdspeak/` > `.git/` > `pyproject.toml` > `package.json` > `Cargo.toml`.
- `$HOME` itself is never returned as a project root — the walk stops *before* including `$HOME`.
- Returned dict carries `{name, root, anchor}` plus an optional `kb` mapping loaded from `<root>/.holdspeak/project.yaml` if present.
- `name` derivation falls back: `pyproject.toml [project].name` → `Cargo.toml [package].name` → `package.json` `"name"` → directory basename.
- 8 unit tests in `tests/unit/test_project_detector_cwd.py`.

## Module location

Picked `holdspeak/plugins/dictation/project_root.py` rather than
adding a function to the existing `holdspeak/plugins/project_detector.py`.
Rationale: the existing module is the **MIR-side** transcript→KB
keyword scorer (a `HostPlugin` with `id="project_detector"`,
`run(context)` returning matched-projects scoring); the cwd-based
detector is a **dictation-side** pure function with a completely
different shape and consumer. Mixing them would make
`project_detector.py` two unrelated surfaces sharing only a name.
Documented in `current-phase-status.md` "Decisions made".

## Test output

### Targeted unit tests

```
$ uv run pytest tests/unit/test_project_detector_cwd.py -v --timeout=30
============================= test session starts ==============================
platform darwin -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
configfile: pyproject.toml
plugins: anyio-4.12.1, mock-3.15.1, timeout-2.4.0, asyncio-1.3.0, cov-7.0.0
timeout: 30.0s
collected 8 items

tests/unit/test_project_detector_cwd.py::test_holdspeak_anchor_beats_git_at_same_level PASSED [ 12%]
tests/unit/test_project_detector_cwd.py::test_git_anchor_beats_pyproject_at_same_level PASSED [ 25%]
tests/unit/test_project_detector_cwd.py::test_walks_up_from_nested_dir PASSED [ 37%]
tests/unit/test_project_detector_cwd.py::test_returns_none_outside_any_project PASSED [ 50%]
tests/unit/test_project_detector_cwd.py::test_name_derivation_pyproject_then_cargo_then_package_then_dirname PASSED [ 62%]
tests/unit/test_project_detector_cwd.py::test_kb_absent_when_no_project_yaml PASSED [ 75%]
tests/unit/test_project_detector_cwd.py::test_kb_loaded_when_project_yaml_present PASSED [ 87%]
tests/unit/test_project_detector_cwd.py::test_does_not_escape_home PASSED [100%]

============================== 8 passed in 0.07s ===============================
```

### Full regression

```
$ uv run pytest tests/ --timeout=30 -q --ignore=tests/e2e/test_metal.py
... (output snipped)
981 passed, 12 skipped in 19.18s
```

Pass delta vs. HS-3 scaffold baseline (973 passed): **+8** (the 8
new unit tests). 12 skipped is unchanged from the baseline (10
mock-meeting fixture-missing + 1 llama-cpp-python missing + 1
GGUF missing).

## Real-world smoke test (informal, not in evidence)

Ran `python -c "from pathlib import Path; from holdspeak.plugins.dictation.project_root import detect_project_for_cwd; print(detect_project_for_cwd(Path('/Users/karol/dev/tools/HoldSpeak')))"` from inside the repo to confirm self-detection. Output:

```
{'name': 'holdspeak', 'root': '/Users/karol/dev/tools/HoldSpeak', 'anchor': 'git'}
```

Anchor is `git` because there's no `.holdspeak/` at the repo root
(the global config lives at `~/.config/holdspeak/` per XDG); `name`
is `holdspeak` from `pyproject.toml`'s `[project].name`. Behavior
matches design.

## Deviations from story scope

- The story stub said 6 unit-test scenarios; shipped 8 because the
  positive-case `kb_loaded_when_project_yaml_present` is a useful
  inverse of the `kb_absent` scenario, and splitting the
  name-derivation cases into 4 standalone tests would have been
  overkill (kept as one test with 4 sub-cases). All 6 originally
  named scenarios are covered.
- Used `tomllib` (3.11+) with `tomli` ImportError fallback rather
  than declaring a hard `tomli` dependency. The fallback path is
  reachable on Python 3.10 (project minimum) where `tomli` is
  already in the lock file conditionally.

## Out-of-scope (intentionally deferred)

- Wiring the function into `Utterance.project` and `blocks.py`'s
  `project_root` parameter — that's HS-3-02.
- Caching across calls — the function is cheap (one stat per
  ancestor, at most one small file read for `name`, optional YAML
  read for `kb`); add an LRU cache only if profiling in HS-3-02
  shows it matters.
