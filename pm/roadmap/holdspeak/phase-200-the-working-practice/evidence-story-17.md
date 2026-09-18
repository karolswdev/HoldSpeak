# Evidence - HS-200-17

- **Story:** HS-200-17 - Define three executable recipe contracts
- **Status:** done
- **Date:** 2026-09-18

## Proof

### Captured run — 2026-09-18T22:57:29Z

- **Command:** `uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 79%]
...................                                                      [100%]
91 passed in 4.13s
```

### Captured run — 2026-09-18T22:57:39Z

- **Command:** `uv run pytest -q tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_modes.py tests/unit/test_doc_drift_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_phase200_one_composition_root.py -rf`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 44%]
........................F............................................... [ 88%]
..................                                                       [100%]
=================================== FAILURES ===================================
_________________ test_no_user_facing_doc_uses_dashes_in_prose _________________

    def test_no_user_facing_doc_uses_dashes_in_prose() -> None:
        offenders = []
        for doc in _user_facing_docs():
            for lineno, line in _prose_lines(doc):
                if "—" not in line and "–" not in line:
                    continue
                if any(marker in line for marker in _VERBATIM_UI_QUOTES):
                    continue
                offenders.append(f"{doc.relative_to(_REPO)}:{lineno}: {line.strip()[:80]}")
>       assert not offenders, (
            "Em/en dashes in user-facing prose (use a period, comma, colon, or "
            "parentheses — see docs/internal/POSITIONING.md voice rules; verbatim "
            "UI quotes belong in _VERBATIM_UI_QUOTES):\n  " + "\n  ".join(offenders)
        )
E       AssertionError: Em/en dashes in user-facing prose (use a period, comma, colon, or parentheses — see docs/internal/POSITIONING.md voice rules; verbatim UI quotes belong in _VERBATIM_UI_QUOTES):
E           docs/USER_GUIDE.md:986: does the work — the preparation brief, the follow-through board and decision
E           docs/USER_GUIDE.md:1009: plan is a read — it writes nothing and runs nothing.
E           docs/USER_GUIDE.md:1012: owner that would supply an unattended firing — the heartbeat for preparation,
E           docs/USER_GUIDE.md:1013: cadence for the review, the steward for the update — and reports that trigger
E           docs/USER_GUIDE.md:1023: meant *Agents* — your own saved prompts — since long before the catalog
E       assert not ['docs/USER_GUIDE.md:986: does the work — the preparation brief, the follow-through board and decision', 'docs/USER_GU...orts that trigger', 'docs/USER_GUIDE.md:1023: meant *Agents* — your own saved prompts — since long before the catalog']

tests/unit/test_doc_drift_guard.py:574: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_doc_drift_guard.py::test_no_user_facing_doc_uses_dashes_in_prose
1 failed, 161 passed in 21.01s
```

### Captured run — 2026-09-18T22:58:53Z

- **Command:** `uv run pytest -q tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_modes.py tests/unit/test_doc_drift_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_phase200_one_composition_root.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
162 passed in 20.99s
```

### Captured run — 2026-09-18T23:01:56Z

- **Command:** `uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 74%]
.........................                                                [100%]
97 passed in 4.75s
```

### Captured run — 2026-09-18T23:02:02Z

- **Command:** `uv run pytest -q tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_modes.py tests/unit/test_doc_drift_guard.py tests/unit/test_phase200_doc_claims.py tests/unit/test_phase200_one_composition_root.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 44%]
........................................................................ [ 88%]
..................                                                       [100%]
162 passed in 20.21s
```

### Captured run — 2026-09-18T23:02:28Z

- **Command:** `uv run python -c 
from holdspeak.services import recipe_catalog as rc
for d in rc.list_descriptors():
    sched = d.trigger(rc.TRIGGER_SCHEDULED)
    print(f'{d.recipe_id}@v{d.version}  manual={d.trigger(rc.TRIGGER_MANUAL).available}  scheduled_owner={sched.owner} available={sched.available}')
    for s in d.steps:
        print('   ', s.name, '->', rc.resolve_step(s).__qualname__)
    print('    limits', rc.resolve_limits(d))
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
preparation_brief@v1  manual=True  scheduled_owner=HeartbeatService available=False
    prepare -> PreparationBriefService.prepare
    limits {'max_priorities': 3, 'max_questions': 3, 'max_obligations': 3}
decision_review@v1  manual=True  scheduled_owner=HeartbeatService available=False
    obligations -> FollowThroughService.board
    decisions -> DecisionRecordService.list_records
    coverage -> PreparationBriefService.preview_manifest
    limits {'limit': 200}
weekly_update@v1  manual=True  scheduled_owner=HeartbeatService available=False
    draft -> ProjectUpdateService.draft_update
    limits {'max_claims': 40}
```

### Captured run — 2026-09-18T23:30:02Z

- **Command:** `uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 63%]
..........................................                               [100%]
114 passed in 5.98s
```

### Captured run — 2026-09-18T23:30:09Z

- **Command:** `uv run pytest -q tests/unit/test_phase200_attention_coverage.py tests/unit/test_phase200_attention.py tests/unit/test_phase200_doc_claims.py tests/unit/test_doc_drift_guard.py tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_modes.py tests/unit/test_thread_tool_loop.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_phase200_preparation_brief.py tests/unit/test_update_drafter.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 21%]
........................................................................ [ 43%]
........................................................................ [ 65%]
........................................................................ [ 86%]
............................................                             [100%]
332 passed in 41.72s
```

### Captured run — 2026-09-18T23:30:53Z

- **Command:** `uv run python -c 
from holdspeak.services import recipe_catalog as rc
print('scheduled owner chain:'); print(' ', rc.SCHEDULED_TRIGGER_OWNER); print()
for d in rc.list_descriptors():
    print(f'{d.recipe_id}@v{d.version}')
    print('   inputs      ', [i.name for i in d.inputs])
    print('   limits      ', rc.resolve_limits(d))
    print('   unreachable ', rc.unreachable_declarations(d))
    for s in d.steps:
        print('   step', s.name, '->', rc.resolve_step(s).__qualname__)
`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
scheduled owner chain:
  connector_watches interval -> HeartbeatService.run_sweep -> WatchService.evaluate_due -> watch_effects (action_kind='project.steward.run_once') -> ProjectStewardService.run_due

preparation_brief@v1
   inputs       ['project_id', 'purpose', 'generator']
   limits       {'max_priorities': 3, 'max_questions': 3, 'max_obligations': 3}
   unreachable  []
   step prepare -> PreparationBriefService.prepare
decision_review@v1
   inputs       ['project_id']
   limits       {'limit': 200}
   unreachable  []
   step obligations -> FollowThroughService.board
   step decisions -> DecisionRecordService.list_records
   step coverage -> PreparationBriefService.preview_manifest
weekly_update@v1
   inputs       ['project_id', 'generator']
   limits       {}
   unreachable  []
   step draft -> ProjectUpdateService.draft_update
```

### Captured run — 2026-09-18T23:54:37Z

- **Command:** `uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py tests/unit/test_phase200_attention_coverage.py tests/unit/test_phase200_attention.py tests/unit/test_phase200_doc_claims.py tests/unit/test_doc_drift_guard.py tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py tests/unit/test_thread_tool_gate.py tests/unit/test_thread_modes.py tests/unit/test_thread_family.py tests/unit/test_thread_tool_loop.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_hs172_people_sources.py tests/unit/test_hs171_heartbeat_wire.py tests/unit/test_hs171_aggregate_notify.py tests/unit/test_phase200_preparation_brief.py tests/unit/test_update_drafter.py tests/unit/test_phase200_continuity.py tests/unit/test_watch_service.py -rf`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 10%]
........................................................................ [ 20%]
........................................................................ [ 30%]
........................................................................ [ 41%]
........................................................................ [ 51%]
........................................................................ [ 61%]
........................................................................ [ 72%]
........................................................................ [ 82%]
........................................................................ [ 92%]
...................................................                      [100%]
699 passed in 71.35s (0:01:11)
```

### Captured run — 2026-09-18T23:55:51Z

- **Command:** `env TZ=UTC uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 6.62s
```

### Captured run — 2026-09-18T23:55:59Z

- **Command:** `env TZ=Pacific/Kiritimati uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 6.97s
```

### Captured run — 2026-09-18T23:56:07Z

- **Command:** `env TZ=Pacific/Midway uv run pytest -q tests/unit/test_phase200_recipe_catalog.py tests/integration/test_phase200_recipe_catalog.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a4ab6c0a52043ebea5199482e48e57981e02d80e

```text
........................................................................ [ 62%]
............................................                             [100%]
116 passed in 6.62s
```
