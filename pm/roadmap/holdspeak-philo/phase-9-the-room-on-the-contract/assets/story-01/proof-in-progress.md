# Evidence - PHILO-9-01

- **Story:** PHILO-9-01 - The Room's operations on the contract (and discovery)
- **Status:** in-progress
- **Date:** 2026-09-27
- **Branch:** `feat/philo-9-01-room-operations` from main `ffbeb04b`.

## F14 — the first commit

`jsonschema>=4.21` joins the base dependencies (`pyproject.toml`); the fence `tests/unit/test_philo9_base_install_imports_catalogue.py` builds a real venv from `[project].dependencies` only and imports `holdspeak.mcp.tools`. The first capture below runs that fence against an export of main `ffbeb04b` (an archive of the commit extracted into `.tmp/main-copy`, the fence copied in): RED, `ModuleNotFoundError: No module named 'jsonschema'`. The second runs it on the branch: green.

## What was built

- **The Room's rows** (`holdspeak/operations.py`, `ROOM_OPERATIONS`): 26 explicit descriptors — the 18 MCP identities of the charter's enumeration (`project.list`, `get`, `get_room`, `create`, `update`, `archive`, `restore`, `link`, `unlink`, `open_review`, `get_delta`, `decide_proposal`, `accept_review`, `list_updates`, `draft_update`, `update_draft`, `publish_update`, `desk.needs_you`), `project.door.create` beside `project.create` (HTTP only), and the seven new tools (`project.item.list/create/update/transition`, `project.resource.list/add/remove`). Each names its real method and closed argument names; each id argument says where the id comes from (F12).
- **Admission declared by effect, enforced by PHILO-9-02:** `Admission.enforced` (new field, default true) is false on every admitted Room row, so `invoke` runs them as today, with no kernel operation and no refusal receipt (`OperationRegistry._admits` / `consequential`). The rows match the admission table: archive, link, unlink, decide_proposal, accept_review, publish_update, resource.add/remove admitted; the Door's create admitted only with sources; the rest exempt or reads (`tests/unit/test_philo9_contract.py`).
- **Binding:** `runtime/composition._compose_room_services` puts the hub's four Room services on the root and the context (bare builds for a partial context only); `operations.bind` binds the rows to them (the identity fence). The MCP family (`holdspeak/mcp/families/project.py`, `ROOM_TOOL_OPERATIONS`, `_room_tool`) and the HTTP routes (`projects.py`, `project_reviews.py`, `project_updates.py`, `project_door.py`, `people.py`, `automations.py`) reach them through the one `invoke`; `desk.needs_you` in `mcp/tools.py` too. The route glue each transport copied moved into the services: `ProjectDeltaService.get_delta` and `decide_proposal(review_id=...)`.
- **The seven tools** follow the charter's table: closed input schemas with the vocabularies (`item_type`, `severity`, `lifecycle`, `relationship`, the patch fields, `minProperties: 1`), checked at the MCP edge; refusals carry the service's code (`validation`, `not_found`, `stale_revision`, `idempotency_conflict`); results equal the HTTP bodies. `kernel.receipt` joins PROJECT (and SWEEP) (`holdspeak/mcp/palettes.py`).
- **ProjectService** (every backend edit of the phase for story 01): F6 `_read_room_updates` / `_read_room_steward`; F13 `needs_you` (the mute rule moved from the route, `needs_you_aggregate.apply_mute`); F2 `_overdue_milestones` in health (`inputs.overdueMilestones`, reason `N OVERDUE`) and a NEEDS YOU row (`source: item`, `kind: milestone`, `OVERDUE · N DAYS`); F7 `ROOM_WRITE_METHODS`; F22 the singular.
- **A1:** `PUT`/`DELETE /api/projects/{id}/resources/{ref}` forward `expected_revision` and `command_id` (DELETE from an optional JSON body).
- **The delivery record:** `project_update_deliveries` (schema, additive reconcile), `UpdateDeliveriesRepository` (insert only; `project_id` from the stored update; a draft refused `UpdateNotPublishedError`), `attach_deliveries` on `list_updates`, `get_update` and the Room's updates section. `project.mark_update_delivered` and its route are PHILO-9-02's (R4-2).
- **Generated:** `docs/generated/operations.json` (68 operations), `docs/generated/api-reference.json`, `docs/MCP_SIDECAR.md` (236 tools), `tests/fixtures/db_schema_canonical.txt`, `docs/internal/philo/phase-5/residual-set.json`; the rig's `op` map (`scripts/graph_walk.py`); two atlas line anchors moved with the code (`atlas.json`, `atlas-phase7.json`, symbols unchanged).

## Measurements (two, never one)

- **Residual identities:** 284 -> **263** (MCP 223 -> 205: the 18; HTTP 61 -> 58: the three constructors `projects.py::_build_needs_you HeartbeatService`, `automations.py::_project_service ProjectService`, `people.py::projects ProjectService` — PAID, not moved: the bare build a partial route context needs is `operations._bare_projects`, not a route module). Route constructions 63 -> 59. The 21 are the set's `paid` under `PHILO-9-01`; on a copy of main the fence names each as a NEW residual identity (the capture below).
- **Public MCP tools:** 229 -> **236** (the seven, in `public_tools_added`).

## The three-state compatibility table (`tests/unit/test_philo9_compat.py`, imports nothing the story adds)

| Surface | Base: main `ffbeb04b` | Round one = built |
|---|---|---|
| The 18 MCP tools: names, envelope keys, `not_found` / `project_request_invalid` codes | green | green |
| HTTP routes: envelope keys and statuses (200; 404 `{error}`, `{success, error}`, `{code, message}`; 400 `{error}`) | green | green |
| Named difference 1 — HTTP bodies close their argument names (an unknown field of `POST /api/projects`, `POST`/`PATCH` items, a transition's extra fields: ignored before, refused 400 now; the fields HTTP read before, including `created_by_ref` and `provenance_kind`, are kept) | ignored | refused (`test_the_named_difference_http_bodies_close_their_argument_names`) |
| Named difference 2 — A1, the resource routes' `expected_revision` / `command_id` | dropped (red below) | honoured |
| `desk.needs_you` over MCP with a muted project (F13) | counts the muted | one count (a superset: `mutedCount`, `muted` per item) |

## Open, unpaid or unknown

- **"mark it delivered"** (a discovery phrase of this story's criteria): its tool `project.mark_update_delivered` lands in PHILO-9-02 (R4-2). Pinned by a strict expected failure in `tests/unit/test_philo9_discovery.py`; the story stays in progress.
- **RECEIPTS** lists pipeline events of the observed services only (ProjectService and WatchService are `@observe_service`; the delta, update and steward services are not), so a publication or a delivery is not yet a Room receipt. The kernel receipts of story 02 are the planned source; not changed here.
- **Pre-existing reds, not this story's:** `tests/unit/test_phase143_inference_capability_census.py` (4) and `test_phase143_routing_authority_census.py` (1) fail identically on the main export (line anchors in `kernel/executor.py` and `meeting_import.py`, files this story does not touch).
- The per-row lower-level admission decision (link's `watch.create` as a child) is declared in words only; PHILO-9-02 implements it.

## Proof

### Captured run — 2026-09-28T01:52:34Z

- **Command:** `bash .tmp/iso.sh uv run pytest -q -p no:cacheprovider .tmp/main-copy/tests/unit/test_philo9_base_install_imports_catalogue.py`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b015cbefe64265d30074542b85a1e3830174ad40

```text
FF                                                                       [100%]
=================================== FAILURES ===================================
__________________ test_base_dependencies_declare_jsonschema ___________________

    def test_base_dependencies_declare_jsonschema() -> None:
        names = [dep.split(">")[0].split("=")[0].split(";")[0].strip().lower() for dep in _base_dependencies()]
>       assert "jsonschema" in names
E       AssertionError: assert 'jsonschema' in ['mlx-whisper', 'sounddevice', 'numpy', 'pynput', 'pyperclip', 'fastapi', ...]

.tmp/main-copy/tests/unit/test_philo9_base_install_imports_catalogue.py:37: AssertionError
______________ test_clean_base_install_imports_the_mcp_catalogue _______________

tmp_path = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-1499/test_clean_base_install_import0')

    @pytest.mark.timeout(600)
    @pytest.mark.skipif(shutil.which("uv") is None, reason="the clean venv is built with uv")
    @pytest.mark.skipif(tomllib is None, reason="reads pyproject with tomllib")
    def test_clean_base_install_imports_the_mcp_catalogue(tmp_path: Path) -> None:
        venv = tmp_path / "venv"
        subprocess.run(["uv", "venv", "-q", str(venv), "--python", f"{sys.version_info.major}.{sys.version_info.minor}"],
                       check=True, capture_output=True, text=True)
        requirements = tmp_path / "base.txt"
        requirements.write_text("\n".join(_base_dependencies()) + "\n", encoding="utf-8")
        python = venv / "bin" / "python"
        subprocess.run(["uv", "pip", "install", "-q", "--python", str(python), "-r", str(requirements)],
                       check=True, capture_output=True, text=True)
        probe = subprocess.run(
            [str(python), "-c", "import holdspeak.mcp.tools, holdspeak.operations; print('IMPORT OK')"],
            cwd=str(tmp_path), env={"PYTHONPATH": str(REPO), "HOME": str(tmp_path), "PATH": "/usr/bin:/bin"},
            capture_output=True, text=True,
        )
>       assert probe.returncode == 0, probe.stderr[-2000:]
E       AssertionError: MCP family project failed to load: No module named 'jsonschema'
E         MCP family interview failed to load: No module named 'jsonschema'
E         Traceback (most recent call last):
E           File "<string>", line 1, in <module>
E             import holdspeak.mcp.tools, holdspeak.operations; print('IMPORT OK')
E             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
E           File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/mcp/__init__.py", line 3, in <module>
E             from .server import main
E           File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/mcp/server.py", line 52, in <module>
E             from .resources import ResourceError, list_resources, read_resource
E           File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/mcp/resources.py", line 26, in <module>
E             from holdspeak import operations as desk_operations
E           File "/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/operations.py", line 38, in <module>
E             from jsonschema import Draft202012Validator
E         ModuleNotFoundError: No module named 'jsonschema'
E         
E       assert 1 == 0
E        +  where 1 = CompletedProcess(args=['/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-1499/test_clea..., in <module>\n    from jsonschema import Draft202012Validator\nModuleNotFoundError: No module named \'jsonschema\'\n').returncode

.tmp/main-copy/tests/unit/test_philo9_base_install_imports_catalogue.py:57: AssertionError
=========================== short test summary info ============================
FAILED .tmp/main-copy/tests/unit/test_philo9_base_install_imports_catalogue.py::test_base_dependencies_declare_jsonschema
FAILED .tmp/main-copy/tests/unit/test_philo9_base_install_imports_catalogue.py::test_clean_base_install_imports_the_mcp_catalogue
2 failed in 5.57s
```

### Captured run — 2026-09-28T01:52:51Z

- **Command:** `bash .tmp/iso.sh uv run pytest -q -p no:cacheprovider tests/unit/test_philo9_base_install_imports_catalogue.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b015cbefe64265d30074542b85a1e3830174ad40

```text
..                                                                       [100%]
2 passed in 11.80s
```

### Captured run — 2026-09-28T02:44:33Z

- **Command:** `bash .tmp/iso.sh uv run python scripts/residual_census.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6197e2e3aaff3317c444a2fe2dcf6f9cc4a71517

```text
RESIDUAL FENCE GREEN: 263 identities match /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde
```

### Captured run — 2026-09-28T02:44:35Z

- **Command:** `bash .tmp/iso.sh uv run python scripts/residual_census.py --check --root .tmp/main-copy`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6197e2e3aaff3317c444a2fe2dcf6f9cc4a71517

```text
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/automations.py::build_automations_router._project_service', 'ProjectService')
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/people.py::build_people_router.projects', 'ProjectService')
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/projects.py::build_projects_router._build_needs_you', 'HeartbeatService')
NEW residual identity (not in the set): ('mcp', 'desk.needs_you', '')
NEW residual identity (not in the set): ('mcp', 'project.accept_review', '')
NEW residual identity (not in the set): ('mcp', 'project.archive', '')
NEW residual identity (not in the set): ('mcp', 'project.create', '')
NEW residual identity (not in the set): ('mcp', 'project.decide_proposal', '')
NEW residual identity (not in the set): ('mcp', 'project.draft_update', '')
NEW residual identity (not in the set): ('mcp', 'project.get', '')
NEW residual identity (not in the set): ('mcp', 'project.get_delta', '')
NEW residual identity (not in the set): ('mcp', 'project.get_room', '')
NEW residual identity (not in the set): ('mcp', 'project.link', '')
NEW residual identity (not in the set): ('mcp', 'project.list', '')
NEW residual identity (not in the set): ('mcp', 'project.list_updates', '')
NEW residual identity (not in the set): ('mcp', 'project.open_review', '')
NEW residual identity (not in the set): ('mcp', 'project.publish_update', '')
NEW residual identity (not in the set): ('mcp', 'project.restore', '')
NEW residual identity (not in the set): ('mcp', 'project.unlink', '')
NEW residual identity (not in the set): ('mcp', 'project.update', '')
NEW residual identity (not in the set): ('mcp', 'project.update_draft', '')
RESIDUAL FENCE RED: 21 problem(s) against /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy
```

### Captured run — 2026-09-28T02:44:44Z

- **Command:** `bash .tmp/run_main.sh tests/unit/test_philo9_room_contract.py -k a1 or f2 or f6 or f7 or f13 or f22 -rf --tb=line`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6197e2e3aaff3317c444a2fe2dcf6f9cc4a71517

```text
holdspeak from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/__init__.py
FFFF.FFFF                                                                [100%]
=================================== FAILURES ===================================
E   AssertionError: {"resource":{"id":"proj-4696837a8d06|note:note_63bc22d6f7bf","project_id":"proj-4696837a8d06","resource_ref":"note:note_63bc22d6f7bf","relationship":"member","source":"manual","confidence":1.0,"created_at":"2026-09-27T20:44:45.870820","last_modified":"2026-09-27T20:44:45.870820","deleted":false,"result_kind":"linked","project_revision":2,"changed_refs":["project:proj-4696837a8d06"]}}
    assert 200 == 409
     +  where 200 = <Response [200 OK]>.status_code
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:80: AssertionError: {"resource":{"id":"proj-4696837a8d06|note:note_63bc22d6f7bf","project_id":"proj-4696837a8d06","resource_ref":"note:note_63bc22d6f7bf","relationship":"member","source":"manual","confidence":1.0,"created_at":"2026-09-27T20:44:45.870820","last_modified":"2026-09-27T20:44:45.870820","deleted":false,"result_kind":"linked","project_revision":2,"changed_refs":["project:proj-4696837a8d06"]}}
E   assert 3 == 2
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:97: assert 3 == 2
E   AssertionError: {"success":true,"removed":true}
    assert 200 == 409
     +  where 200 = <Response [200 OK]>.status_code
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:115: AssertionError: {"success":true,"removed":true}
E   AssertionError: {'assessment': 'on_track', 'checked_at': None, 'inputs': {'ciFailing': False, 'overdue': 0, 'reviewWaitingDays': None, 'targetPassed': False}, 'merge_queue_depth': 0, ...}
    assert 'on_track' == 'at_risk'
      
      - at_risk
      + on_track
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:130: AssertionError: {'assessment': 'on_track', 'checked_at': None, 'inputs': {'ciFailing': False, 'overdue': 0, 'reviewWaitingDays': None, 'targetPassed': False}, 'merge_queue_depth': 0, ...}
E   AssertionError: {'reason': 'not_yet_built', 'state': 'absent'}
    assert 'absent' == 'ok'
      
      - ok
      + absent
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:190: AssertionError: {'reason': 'not_yet_built', 'state': 'absent'}
E   AssertionError: ['list_meetings', 'list_meetings', 'list_meetings', 'room', 'list_meetings', 'list_meetings', ...]
    assert 'create_item' in ['list_meetings', 'list_meetings', 'list_meetings', 'room', 'list_meetings', 'list_meetings', ...]
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:211: AssertionError: ['list_meetings', 'list_meetings', 'list_meetings', 'room', 'list_meetings', 'list_meetings', ...]
E   AssertionError: (2, 1)
    assert 2 == 1
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:231: AssertionError: (2, 1)
E   AssertionError: assert ['1 proposals waiting'] == ['1 proposal waiting']
      
      At index 0 diff: '1 proposals waiting' != '1 proposal waiting'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_room_contract.py:252: AssertionError: assert ['1 proposals waiting'] == ['1 proposal waiting']
=========================== short test summary info ============================
FAILED tests/unit/test_philo9_room_contract.py::test_a1_the_resource_put_refuses_a_stale_revision
FAILED tests/unit/test_philo9_room_contract.py::test_a1_the_resource_put_honours_the_command_id
FAILED tests/unit/test_philo9_room_contract.py::test_a1_the_resource_delete_refuses_a_stale_revision
FAILED tests/unit/test_philo9_room_contract.py::test_f2_a_past_due_milestone_turns_health_and_is_in_needs_you
FAILED tests/unit/test_philo9_room_contract.py::test_f6_the_room_reports_a_published_update_and_a_completed_steward_run
FAILED tests/unit/test_philo9_room_contract.py::test_f7_the_rooms_receipts_are_its_writes_not_its_reads
FAILED tests/unit/test_philo9_room_contract.py::test_f13_one_needs_you_count_with_a_muted_project
FAILED tests/unit/test_philo9_room_contract.py::test_f22_one_waiting_proposal_is_singular
8 failed, 1 passed, 7 deselected in 7.20s
```

### Captured run — 2026-09-28T02:44:52Z

- **Command:** `bash .tmp/run_main.sh tests/unit/test_philo9_compat.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 6197e2e3aaff3317c444a2fe2dcf6f9cc4a71517

```text
holdspeak from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/__init__.py
...                                                                      [100%]
3 passed in 2.83s
```

### Captured run — 2026-09-28T02:44:56Z

- **Command:** `bash .tmp/run_main.sh tests/unit/test_philo9_discovery.py -rf --tb=line`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 6197e2e3aaff3317c444a2fe2dcf6f9cc4a71517

```text
holdspeak from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/__init__.py
FFFFFFxFFFFFFFFFFFFFFFFFFFFFF.                                           [100%]
=================================== FAILURES ===================================
E   AssertionError: 'add a milestone or a risk to a project' is named by [], expected ['project.item.create']
    assert [] == ['project.item.create']
      
      Right contains one more item: 'project.item.create'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:97: AssertionError: 'add a milestone or a risk to a project' is named by [], expected ['project.item.create']
E   AssertionError: 'copy my update for delivery' is named by [], expected ['project.list_updates']
    assert [] == ['project.list_updates']
      
      Right contains one more item: 'project.list_updates'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:97: AssertionError: 'copy my update for delivery' is named by [], expected ['project.list_updates']
E   AssertionError: 'draft my update' is named by [], expected ['project.draft_update']
    assert [] == ['project.draft_update']
      
      Right contains one more item: 'project.draft_update'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:97: AssertionError: 'draft my update' is named by [], expected ['project.draft_update']
E   AssertionError: 'make a project' is named by [], expected ['project.create']
    assert [] == ['project.create']
      
      Right contains one more item: 'project.create'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:97: AssertionError: 'make a project' is named by [], expected ['project.create']
E   AssertionError: 'publish my update in the room' is named by [], expected ['project.publish_update']
    assert [] == ['project.publish_update']
      
      Right contains one more item: 'project.publish_update'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:97: AssertionError: 'publish my update in the room' is named by [], expected ['project.publish_update']
E   AssertionError: 'what needs me' is named by [], expected ['desk.needs_you']
    assert [] == ['desk.needs_you']
      
      Right contains one more item: 'desk.needs_you'
      Use -v to get more diff
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:97: AssertionError: 'what needs me' is named by [], expected ['desk.needs_you']
E   AssertionError: project.get.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.get.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.get_room.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.get_room.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.update.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.update.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.archive.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.archive.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.restore.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.restore.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.link.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.link.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.unlink.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.unlink.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.open_review.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.open_review.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.get_delta.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.get_delta.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.decide_proposal.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.decide_proposal.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.accept_review.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.accept_review.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.list_updates.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.list_updates.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.draft_update.project_id does not say where its value comes from: 'Project identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.draft_update.project_id does not say where its value comes from: 'Project identifier.'
E   AssertionError: project.update_draft.update_id does not say where its value comes from: 'Update identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.update_draft.update_id does not say where its value comes from: 'Update identifier.'
E   AssertionError: project.publish_update.update_id does not say where its value comes from: 'Update identifier.'
    assert []
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:124: AssertionError: project.publish_update.update_id does not say where its value comes from: 'Update identifier.'
E   KeyError: 'project.item.list'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.item.list'
E   KeyError: 'project.item.create'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.item.create'
E   KeyError: 'project.item.update'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.item.update'
E   KeyError: 'project.item.transition'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.item.transition'
E   KeyError: 'project.resource.list'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.resource.list'
E   KeyError: 'project.resource.add'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.resource.add'
E   KeyError: 'project.resource.remove'
/Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/tests/unit/test_philo9_discovery.py:118: KeyError: 'project.resource.remove'
=========================== short test summary info ============================
FAILED tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[add a milestone or a risk to a project]
FAILED tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[copy my update for delivery]
FAILED tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[draft my update]
FAILED tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a project]
FAILED tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[publish my update in the room]
FAILED tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[what needs me]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.get]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.get_room]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.update]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.archive]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.restore]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.link]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.unlink]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.open_review]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.get_delta]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.decide_proposal]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.accept_review]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.list_updates]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.draft_update]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.update_draft]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.publish_update]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.list]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.create]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.update]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.transition]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.resource.list]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.resource.add]
FAILED tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.resource.remove]
28 failed, 1 passed, 1 xfailed in 1.37s
```

### Captured run — 2026-09-28T02:47:27Z

- **Command:** `bash .tmp/iso.sh uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_philo9_base_install_imports_catalogue.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_contract.py tests/unit/test_philo9_delivery_record.py tests/unit/test_philo9_discovery.py tests/unit/test_philo9_compat.py -rxX`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4ea1dbc9c8f099ef38d0d44ade5ba0101901159

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 62%]
.....................................x.....                              [100%]
=========================== short test summary info ============================
XFAIL tests/unit/test_philo9_discovery.py::test_mark_it_delivered_maps_to_its_tool - PHILO-9-02 lands project.mark_update_delivered with its admission (R4-2)
114 passed, 1 xfailed in 17.26s
```

### Captured run — 2026-09-28T02:47:45Z

- **Command:** `bash .tmp/iso.sh uv run pytest --collect-only -q -p no:cacheprovider tests/unit/test_philo9_base_install_imports_catalogue.py tests/unit/test_philo9_room_contract.py tests/unit/test_philo9_contract.py tests/unit/test_philo9_delivery_record.py tests/unit/test_philo9_discovery.py tests/unit/test_philo9_compat.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4ea1dbc9c8f099ef38d0d44ade5ba0101901159

```text
tests/unit/test_philo9_base_install_imports_catalogue.py::test_base_dependencies_declare_jsonschema
tests/unit/test_philo9_base_install_imports_catalogue.py::test_clean_base_install_imports_the_mcp_catalogue
tests/unit/test_philo9_room_contract.py::test_a1_the_resource_put_refuses_a_stale_revision
tests/unit/test_philo9_room_contract.py::test_a1_the_resource_put_honours_the_command_id
tests/unit/test_philo9_room_contract.py::test_a1_the_resource_delete_refuses_a_stale_revision
tests/unit/test_philo9_room_contract.py::test_f2_a_past_due_milestone_turns_health_and_is_in_needs_you
tests/unit/test_philo9_room_contract.py::test_f2_preservation_a_milestone_not_yet_due_or_reached_keeps_the_room_on_track
tests/unit/test_philo9_room_contract.py::test_f6_the_room_reports_a_published_update_and_a_completed_steward_run
tests/unit/test_philo9_room_contract.py::test_f7_the_rooms_receipts_are_its_writes_not_its_reads
tests/unit/test_philo9_room_contract.py::test_f13_one_needs_you_count_with_a_muted_project
tests/unit/test_philo9_room_contract.py::test_f22_one_waiting_proposal_is_singular
tests/unit/test_philo9_room_contract.py::test_the_seven_tools_are_listed_with_the_charters_schemas
tests/unit/test_philo9_room_contract.py::test_the_seven_tools_equal_the_http_routes_in_one_hub_and_across_a_restart
tests/unit/test_philo9_room_contract.py::test_the_seven_tools_refuse_as_the_routes_do
tests/unit/test_philo9_room_contract.py::test_a_reused_command_id_with_a_different_body_is_idempotency_conflict_on_both
tests/unit/test_philo9_room_contract.py::test_the_rigs_op_step_reaches_the_new_operations
tests/unit/test_philo9_room_contract.py::test_kernel_receipt_on_the_palette_reads_its_own_and_refuses_a_foreign_operation[PROJECT]
tests/unit/test_philo9_room_contract.py::test_kernel_receipt_on_the_palette_reads_its_own_and_refuses_a_foreign_operation[SWEEP]
tests/unit/test_philo9_contract.py::test_the_room_rows_are_the_charters_rows
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[desk.needs_you]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.accept_review]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.archive]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.create]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.decide_proposal]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.door.create]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.draft_update]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.get]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.get_delta]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.get_room]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.item.create]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.item.list]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.item.transition]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.item.update]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.link]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.list]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.list_updates]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.open_review]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.publish_update]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.resource.add]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.resource.list]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.resource.remove]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.restore]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.unlink]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.update]
tests/unit/test_philo9_contract.py::test_each_row_declares_its_admission_by_effect_and_story_02_enforces_it[project.update_draft]
tests/unit/test_philo9_contract.py::test_the_door_create_is_admitted_only_with_sources
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[desk.needs_you]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.accept_review]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.archive]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.create]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.decide_proposal]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.door.create]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.draft_update]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.get]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.get_delta]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.get_room]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.item.create]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.item.list]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.item.transition]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.item.update]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.link]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.list]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.list_updates]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.open_review]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.publish_update]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.resource.add]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.resource.list]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.resource.remove]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.restore]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.unlink]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.update]
tests/unit/test_philo9_contract.py::test_each_row_is_bound_to_the_hubs_one_instance[project.update_draft]
tests/unit/test_philo9_contract.py::test_an_admitted_row_makes_no_kernel_operation_until_story_02
tests/unit/test_philo9_contract.py::test_every_mcp_tool_and_http_route_of_the_slice_reaches_the_one_registry
tests/unit/test_philo9_contract.py::test_the_project_palette_refuses_outside_and_admits_the_new_tools_through_dispatch
tests/unit/test_philo9_contract.py::test_the_named_difference_http_bodies_close_their_argument_names
tests/unit/test_philo9_delivery_record.py::test_the_reconcile_creates_the_table_on_an_existing_database
tests/unit/test_philo9_delivery_record.py::test_the_repository_has_no_update_or_delete_path
tests/unit/test_philo9_delivery_record.py::test_a_delivery_never_writes_the_published_update
tests/unit/test_philo9_delivery_record.py::test_the_untouched_fence_turns_red_on_a_delivery_that_writes_the_update
tests/unit/test_philo9_delivery_record.py::test_a_draft_is_refused_and_an_operation_is_used_once
tests/unit/test_philo9_delivery_record.py::test_two_deliveries_read_back_in_order_on_every_read
tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[add a milestone or a risk to a project]
tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[copy my update for delivery]
tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[draft my update]
tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[make a project]
tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[publish my update in the room]
tests/unit/test_philo9_discovery.py::test_each_job_phrase_maps_to_one_tool_and_its_argument_path[what needs me]
tests/unit/test_philo9_discovery.py::test_mark_it_delivered_maps_to_its_tool
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.get]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.get_room]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.update]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.archive]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.restore]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.link]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.unlink]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.open_review]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.get_delta]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.decide_proposal]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.accept_review]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.list_updates]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.draft_update]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.update_draft]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.publish_update]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.list]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.create]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.update]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.item.transition]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.resource.list]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.resource.add]
tests/unit/test_philo9_discovery.py::test_every_id_argument_names_where_its_value_comes_from[project.resource.remove]
tests/unit/test_philo9_discovery.py::test_no_project_tool_says_the_product_sends_the_update
tests/unit/test_philo9_compat.py::test_the_eighteen_mcp_answers_keep_their_envelopes
tests/unit/test_philo9_compat.py::test_the_eighteen_mcp_refusals_keep_their_codes
tests/unit/test_philo9_compat.py::test_the_http_routes_keep_their_envelopes_and_statuses

115 tests collected in 0.30s
```

### Captured run — 2026-09-28T02:47:59Z

- **Command:** `bash .tmp/run_scoped.sh -rxX`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4ea1dbc9c8f099ef38d0d44ade5ba0101901159

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  2%]
........................................................................ [  5%]
........................................................................ [  8%]
........................................................................ [ 10%]
........................................................................ [ 13%]
........................................................................ [ 16%]
........................................................................ [ 18%]
........................................................................ [ 21%]
........................................................................ [ 24%]
........................................................................ [ 26%]
........................................................................ [ 29%]
........................................................................ [ 32%]
................................s....................................... [ 34%]
........................................................................ [ 37%]
........................................................................ [ 40%]
........................................................................ [ 42%]
........................................................................ [ 45%]
.......x................................................................ [ 48%]
........................................................................ [ 50%]
........................................................................ [ 53%]
........................................................................ [ 56%]
........................................................................ [ 58%]
........................................................................ [ 61%]
........................................................................ [ 64%]
........................................................................ [ 66%]
........................................................................ [ 69%]
........................................................................ [ 72%]
........................................................................ [ 74%]
........................................................................ [ 77%]
........................................................................ [ 80%]
........................................................................ [ 82%]
......................................s................................. [ 85%]
........................................................................ [ 88%]
...........................................................s............ [ 90%]
........................................................................ [ 93%]
........................................................................ [ 96%]
........................................................................ [ 98%]
..............................                                           [100%]
=========================== short test summary info ============================
XFAIL tests/unit/test_philo9_discovery.py::test_mark_it_delivered_maps_to_its_tool - PHILO-9-02 lands project.mark_update_delivered with its admission (R4-2)
2690 passed, 3 skipped, 1 xfailed in 182.55s (0:03:02)
```

### Captured run — 2026-09-28T02:51:02Z

- **Command:** `bash .tmp/run_scoped.sh -rxX`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4ea1dbc9c8f099ef38d0d44ade5ba0101901159

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  4%]
........................................................................ [  8%]
........................................................................ [ 13%]
........................................................................ [ 17%]
........................................................................ [ 22%]
........................................................................ [ 26%]
........................................................................ [ 31%]
.......................s................................................ [ 35%]
........................................................................ [ 39%]
........................................................................ [ 44%]
........................................................................ [ 48%]
........................................................................ [ 53%]
........................................................................ [ 57%]
........................................................................ [ 62%]
........................................................................ [ 66%]
........................................................................ [ 70%]
........................................................................ [ 75%]
........................................................................ [ 79%]
........x....................................s.......................... [ 84%]
...........................................s............................ [ 88%]
........................................................................ [ 93%]
............................................................s........... [ 97%]
........................................                                 [100%]
=========================== short test summary info ============================
XFAIL tests/unit/test_philo9_discovery.py::test_mark_it_delivered_maps_to_its_tool - PHILO-9-02 lands project.mark_update_delivered with its admission (R4-2)
1619 passed, 4 skipped, 1 xfailed in 134.69s (0:02:14)
```

### Captured run — 2026-09-28T02:53:18Z

- **Command:** `bash .tmp/run_main.sh tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py -rf --tb=no`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** d4ea1dbc9c8f099ef38d0d44ade5ba0101901159

```text
holdspeak from /Users/karol/dev/tools/HoldSpeak/.claude/worktrees/agent-a9cee30c09ab6adde/.tmp/main-copy/holdspeak/__init__.py
FFF...F...F.......                                                       [100%]
=========================== short test summary info ============================
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_call_site_fixture_is_complete_and_fail_closed
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_product_runner_entrance_has_one_owner
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_shared_helpers_have_semantic_callers
FAILED tests/unit/test_phase143_inference_capability_census.py::test_phase143_every_censused_site_has_one_capability_and_source_owner
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
5 failed, 13 passed in 27.49s
```

### Captured run — 2026-09-28T02:53:48Z

- **Command:** `bash .tmp/docs_checks.sh`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** d4ea1dbc9c8f099ef38d0d44ade5ba0101901159

```text
== python3 -m unittest discover -s tests/unit -p test_docs_navigation.py
----------------------------------------------------------------------
Ran 9 tests in 0.004s

OK
== python3 scripts/check_docs.py
Documentation navigation: 70 files checked; local targets and Markdown headings resolve.
== python3 scripts/check_docs.py docs/internal/philo/DELIVERY_ROADMAP.md docs/internal/philo/DESIGN_SPECIFICATION.md docs/internal/philo/EXTERNAL_RESEARCH.md docs/internal/philo/INITIAL_PLAN.md docs/internal/philo/initial-findings.md docs/internal/philo/README.md docs/internal/philo/SOURCE_HIERARCHY.md docs/internal/philo/source-checklist.md docs/internal/philo/SRS.md docs/internal/philo/adr/capability-evidence-ownership.md docs/internal/philo/adr/desktop-host.md docs/internal/philo/checks/accuracy-luna.md docs/internal/philo/checks/baseline-failures.md docs/internal/philo/checks/luna-audits.md docs/internal/philo/checks/plan-astra-response.md docs/internal/philo/checks/plan-muaddib-round2.md docs/internal/philo/checks/plan-muaddib.md docs/internal/philo/visuals/README.md docs/internal/philo/desktop-prototypes/README.md agent/skills/holdspeak-api-client/SKILL.md agent/skills/holdspeak-capability-verifier/SKILL.md agent/skills/holdspeak-connector-author/SKILL.md agent/skills/holdspeak-desk/SKILL.md agent/skills/holdspeak-dictation/SKILL.md agent/skills/holdspeak-doc-maintainer/SKILL.md agent/skills/holdspeak-kernel/SKILL.md agent/skills/holdspeak-meetings/SKILL.md agent/skills/holdspeak-model-routing/SKILL.md agent/skills/holdspeak-plugin-author/SKILL.md agent/skills/holdspeak-release-auditor/SKILL.md agent/skills/holdspeak-repo-navigator/SKILL.md agent/skills/holdspeak-security-review/SKILL.md agent/skills/holdspeak-troubleshooter/SKILL.md
Documentation navigation: 33 files checked; local targets and Markdown headings resolve.
== python3 scripts/philo_repository_census.py --check
Repository census: 5 outputs verified.
== python3 scripts/philo_api_reference.py --check
API reference checked
== python3 scripts/philo_boundary_census.py --check
Boundary candidate census checked
== python3 scripts/philo_doctor_reference.py --check
Doctor reference: 41 check functions
== python3 scripts/philo_config_reference.py --check
Configuration declaration reference is current
== python3 scripts/philo_graph_reference.py --check
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
== python3 scripts/validate_architecture.py
Architecture metadata: 4 shard(s), 147 record(s)
Architecture metadata validation passed.
== python3 scripts/generate_capability_docs.py --check
Architecture documentation checked (10 outputs).
== python3 scripts/check_doc_coverage.py --check
Documentation coverage checked.
DOCS RC=0
```
