# Luna proof — graph rig r3, DRAFT

The Luna worker changed only `scripts/graph_walk.py` and `tests/unit/test_philo13_graph_walk.py`. Its test selections included all three standing shared files: `tests/unit/test_philo_graph_atlas.py`, `tests/unit/test_api_surface.py`, and `tests/unit/test_philo_graph_reference.py`. The worker used isolated HOME/TMPDIR and deleted every temporary directory it created. No staging, evidence capture, story flip, or commit was done by the worker.

## R4 / C4 — rounded-sheet hit points

Target: `tests/unit/test_philo13_graph_walk.py::test_hit_test_probes_use_interior_points_for_rounded_sheet`. It uses Playwright and a 393 × 393 rounded sheet to exercise both `_SNAPSHOT_JS` and `_PLACEMENT_ARM_JS`.

The pre-fix selection was:

```sh
uv run pytest --collect-only -q tests/unit/test_philo_graph_atlas.py tests/unit/test_api_surface.py tests/unit/test_philo_graph_reference.py tests/unit/test_philo13_graph_walk.py::test_hit_test_probes_use_interior_points_for_rounded_sheet
```

It collected 126 tests. The same selection without `--collect-only` failed before the code change: `assert hit["all_owned"] is True`; **1 failed, 125 passed in 5.97s**. The pre-fix 2 px inset sampled the rounded corners.

After the fix, both probes sample the 3 × 3 grid at fractions `[0.125, 0.5, 0.875]`. The target collected 126 tests and passed **126 passed in 5.64s**. The final graph-walk scoped selection collected 137 and passed **137 passed in 7.93s**. All nine samples and ownership checks remain.

## R5 / C5 — trigger lifecycle errors

Target: `tests/unit/test_philo13_graph_walk.py::test_trigger_lifecycle_error_is_recorded_as_fail`. The case uses the real calibration HTTP trigger against a missing route, expects status 200, and checks the actual recorder row.

The pre-fix selection used the three standing files plus the target test, collected 126 tests, and failed before the code change: **1 failed, 125 passed in 8.41s** because the observed trigger lifecycle verdict was `blocked`, not `fail`.

After the fix, the target plus the three unresolved-placeholder/negative-control tests and standing files collected 129 and passed **129 passed in 44.53s**. The final graph-walk scoped selection collected 137 and passed **137 passed in 7.93s**. The failure record now carries `trigger_error.lifecycle = "fail"` and verdict `fail`; unresolved pre-fire placeholders remain blocked.

The lane's final selection after the Atlas, lifecycle and probe changes collected 166 tests and passed **166 passed in 8.64s**; see [focused collection](focused-collect.txt) and [focused run](focused-green.txt).
