# Evidence - HS-152-05

- **Story:** HS-152-05 - The renderers and the status line
- **Status:** done
- **Date:** 2026-08-30

## Proof

### Captured run — 2026-08-30T06:36:11Z

- **Command:** `uv run pytest -q -n 4 tests/unit/test_thread_family.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_tool_loop.py tests/unit/test_thread_decide_always.py tests/unit/test_thread_people_fence.py tests/unit/test_thread_service.py tests/unit/test_doc_drift_guard.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_one_path_census.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** eda449c23c7515c26bcca730cfc3266712b3bdaf

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 46%]
........................................................................ [ 92%]
......F....                                                              [100%]
=================================== FAILURES ===================================
____________ test_the_mesh_receiver_names_no_model_execution_at_all ____________
[gw2] darwin -- Python 3.14.2 /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/warpdrv-chat-port/.venv/bin/python3

    def test_the_mesh_receiver_names_no_model_execution_at_all() -> None:
        """The positive half of closing `mesh-receiver`: zero sites, not a waiver.

        A family can leave :data:`NAMED_FINDINGS` by being deleted or admitted. This
        one was ADMITTED, and the shape of that admission is visible right here: the
        worker constructs nothing, so the census finds no factory and no completion
        verb in its module. If a future edit reintroduces either, the mutation proof
        below is what fails.
        """
        sites = [site for site in census() if site.path == "holdspeak/commands/mesh_serve.py"]
>       assert sites == [], f"the mesh receiver named model execution again: {sites}"
E       AssertionError: the mesh receiver named model execution again: [Site(path='holdspeak/commands/mesh_serve.py', line=243, scope='MeshServeWorker._mutation_direct_dispatch', target='run_prompt', kind='call')]
E       assert [Site(path='h... kind='call')] == []
E
E         Left contains one more item: Site(path='holdspeak/commands/mesh_serve.py', line=243, scope='MeshServeWorker._mutation_direct_dispatch', target='run_prompt', kind='call')
E         Use -v to get more diff

tests/unit/test_one_path_census.py:1648: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_one_path_census.py::test_the_mesh_receiver_names_no_model_execution_at_all
1 failed, 154 passed in 43.99s
```

### Captured run — 2026-08-30T06:37:37Z

- **Command:** `uv run pytest -q -n 4 tests/unit/test_thread_family.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_tool_loop.py tests/unit/test_thread_decide_always.py tests/unit/test_thread_people_fence.py tests/unit/test_thread_service.py tests/unit/test_doc_drift_guard.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eda449c23c7515c26bcca730cfc3266712b3bdaf

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 63%]
.........................................                                [100%]
113 passed in 14.39s
```

### Captured run — 2026-08-30T06:37:52Z

- **Command:** `uv run pytest -q -n 0 tests/unit/test_phase143_inference_capability_census.py tests/unit/test_one_path_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eda449c23c7515c26bcca730cfc3266712b3bdaf

```text
..........................................                               [100%]
42 passed in 82.62s (0:01:22)
```

### Captured run — 2026-08-30T06:39:16Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/vitest05.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eda449c23c7515c26bcca730cfc3266712b3bdaf

```text

 Test Files  2 passed (2)
      Tests  47 passed (47)
   Start at  00:39:16
   Duration  836ms (transform 506ms, setup 93ms, import 725ms, tests 211ms, environment 404ms)
```

### Captured run — 2026-08-30T06:39:17Z

- **Command:** `zsh /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak--claude-worktrees-warpdrv-chat-port/7e7cb543-4e07-4e50-aa94-6c15c1b4a114/scratchpad/glass05.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** eda449c23c7515c26bcca730cfc3266712b3bdaf

```text
......                                                                   [100%]
6 passed in 142.43s (0:02:22)
```
