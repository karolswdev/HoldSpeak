# Evidence - PHILO-5-02

- **Story:** PHILO-5-02 - The loop shares the contract
- **Status:** done
- **Date:** 2026-09-24

## What was built

- The catalogue grew by 13 explicit descriptors, no framework: `holdspeak/operations.py:247` (`meeting.list`), `:275` (`meeting.read` — also the summary's planning/completion/terminal read and the import's read-back; no second summary read), `:298` (`meeting.import`, with `held=("tmp_path", "config", "transcriber_factory")`), `:326` (`meeting.summary.run`), `:351` / `:366` (`brief.generate` / `brief.latest`), `:381` / `:406` (`brief.shelf.write` / `.read`), `:427` / `:446` (`thought.create` / `thought.save` = `update_working`, A4's KEPT), `:474` / `:494` / `:514` (`thought.read` / `thought.workbench.read` / `thought.list`). Fields are only as strict as both transports already were; each transport keeps its own published schema and each service its own named refusals.
- `invoke` takes `held` — the transport-held inputs a descriptor names, exactly those, never arguments (`operations.py:577-614`). `bind_available`, `for_context(ctx, *bare, **fallbacks)` and `for_runtime(**builders)` serve the two lawful partial compositions (`:654,:680,:704`).
- One composition: `runtime/composition.py:496-525` puts the meeting, summary, clock-bearing brief (gap A — composed HERE, once, with `WebContext.brief_clock`, `:503`) and Thought application services on the root and the context, and binds the whole catalogue to them. `web_server.py:933` removes the summary factory (gap C); `web/routes/meetings/intel.py:17` prefers the composed instance.
- HTTP over `invoke`: `web/routes/meetings/crud.py:72,104`; `meetings/intel.py:99`; `meeting_import.py:94` (multipart custody, config and transcriber unchanged, gap E); `monday_brief.py:115,126,134,146` (the router builds no service in the hub); `primitives/thoughts.py:65,83,141,157,203`.
- MCP over `invoke`: `mcp/tools.py:878,880` (meeting.list/get), `:993` (meeting.run_intelligence — the hub's wired instance, gap B), `:1075,:1081` (monday_brief.get keeps `generate=true` and its default read; monday_brief.generate), `:1084,:1086` (the NEW `monday_brief.shelf` / `monday_brief.shelf_read`), `:686-731` (the NEW `meeting.import` intake: absolute path, readable, supported type, not empty; the hub copies the file into its own custody); `mcp/families/thought.py:244,334`. The hand-written branches (clockless `MondayBriefService`, unwired `MeetingIntelService`) are deleted.
- Resources over `invoke` (gap D): `mcp/resources.py:433` (`_ops`), `:529` briefs/latest, `:542` thoughts/unfinished, `:548` thoughts/{id}/workbench (the hub's application service and coordinator, not the standalone family runtime), `:565` thoughts/{id}, `:586` meetings/{id}.
- The service side: `MeetingService.import_held_file` (`services/meeting_service.py:228`), `RefinementApplicationService.get_thought` / `list_unfinished` (`services/refinement_application_service.py:270,274`). The three new tools are classified (`services/thread_tools.py:94-97,121`), outside CHAT_PALETTE.

## Measurements (two, never one)

- **Public MCP tools:** 225 -> 228 (`meeting.import`, `monday_brief.shelf`, `monday_brief.shelf_read`; `docs/MCP_SIDECAR.md` roster regenerated; `residual-set.json` `public_tools_added`).
- **Residual implementation identities:** 327 -> 320 (MCP 263 -> 256; HTTP 64 -> 64; route constructions 66 -> 66). Paid, exactly: `mcp meeting.list`, `meeting.get`, `meeting.run_intelligence`, `monday_brief.generate`, `monday_brief.get`, `thought.create`, `thought.update_working`. Moved, NOT paid: `http monday_brief.py::build_monday_brief_router` -> `::build_monday_brief_router.ops` (`MondayBriefService`) — in the hub the router builds nothing now; the construction survives only as the partially wired context's fallback, kept in the route so the Phase 4 route tests' `get_database`/`get_observer` seams hold unchanged. Still residual, on purpose: `meetings/crud.py::_service`, `meetings/intel.py::_svc`, `primitives/thoughts.py::service` / `::application` — each also serves routes outside the pilot inventory.

## Reds and greens (retained under `docs/internal/philo/phase-5/the-loop/`)

- `red-base-loop-fences.txt` — the unchanged `tests/unit/test_philo5_the_loop.py` on a `git archive 6e707ff3` copy: 19 failed, 4 passed. The behavioural reds through the real producers: gap A `AssertionError: 2026-09-24T14:...` (MCP dated the brief by the wall clock, not the hub clock 2026-10-13); gap B `assert 'runtime_queue' in []`; gap C `assert <function MeetingWebServer._create_app.<locals>.<lambda> ...> is None` (the hub's summary factory); the invoke recording `assert [] == ['meeting.lis...` (no transport called the contract). The import/shelf tools' base answer is `Unknown tool` — NOT claimed as the required red; M2/M3 prove those invariants.
- `red-mutations.txt` — M1 a fresh `MeetingService` bound at composition (identity red); M2 the intake bypasses `invoke` (recording red); M3 the intake hands the caller's own file to the worker (the caller's file is deleted: `FileNotFoundError`); M4/M5 a resource builds its own service (recording red); M6 `_svc` returns a second instance (identity red); M7 `thought.update_working` calls the service by hand (recording red); M8 a clockless brief service in MCP (wall-clock date); M9 an unwired summary service in MCP (`runtime_queue` absent); M10/M11 the runner census still fails closed on a `.invoke` whose name is not a declared operation.
- `compat-base.txt` / `compat-built.txt` — `tests/unit/test_philo5_loop_compat.py` (imports nothing new): 58 passed on base, 58 passed built, identical row outcomes.
- `red-base-residual.txt` — the built set against the base tree: `RESIDUAL FENCE RED: 9 problem(s)` (the 7 paid MCP identities + the moved HTTP pair). `green-built-residual.txt` — `RESIDUAL FENCE GREEN: 320 identities`.
- `scoped-tests.txt` — the scoped file list the captured run below executes.

## Found on the way (inherited, paid)

`tests/unit/test_phase143_inference_capability_census.py` (two tests) and `test_phase143_routing_authority_census.py` were ALREADY red on `6e707ff3` (verified on the base copy: 3 failed): PHILO-5-01's registry `.invoke` calls read as unregistered `InferenceRunner.invoke` entrances, and its line shifts left stale pins. Paid: the census tells a contract call apart by its second argument being a declared operation name (no runner call takes one), mutation-proved (M10, M11); the pins are re-anchored with a note. `refinement_application_service.py`'s new methods sit at the class end so no routing pin moved there.

## Not claimed

- No full suite (the orchestrator's job). No browser walk: no face changed; the rendered Phase 4 fences are the vitest chair suite. No real ASR: the audio import uses a stub transcriber through the same monkeypatch seam the HTTP import tests use. The Codex rehearsal is story 04.
- The decision admission is NOT resolved and NOT exempted (round two): INHERITED DEBT under Article XI, unruled, assigned to the owner's ruling (phase status "Decisions deferred"; `pm/roadmap/holdspeak/BACKLOG.md` "PHILO-5-02 follow-ups"). The `test_philo5_the_loop.py:618` test is characterization only.

## Round two (Astra's check on built, BOUNCE — `checks/story-02-built-astra.md`)

Retained under `docs/internal/philo/phase-5/the-loop/round-2/`.

- **1. The owner boundary on `meeting.import` (P1).** The contract: `OperationDescriptor.owner_only` and `OperationRegistry.authorize` (`holdspeak/operations.py:355,609`), called first by `invoke`; the refusal is `OperationOwnerRequired` — a `ServiceError`, code `owner_required`, status 403 (the owner-only service idiom). The MCP intake calls `authorize` before it looks at the path (`holdspeak/mcp/tools.py:706`); the HTTP upload before it stores the body (`holdspeak/web/routes/meeting_import.py:66`). Fence `tests/unit/test_philo5_the_loop_r2.py:131`: remote MCP enabled through `PUT /api/settings/remote`, a DESK credential issued through `POST /api/settings/remote/credentials`, the call from client host `192.0.2.123` with ONLY the agent token -> `owner_required`, zero touches of the target (`Path.open`, `Path.is_file`, `Path.exists`, `os.access`, `open` all observed), no meeting; the same credential from loopback -> `owner_required`; the local owner then imports the same file and the observer sees its open (the zero is not vacuous). The HTTP route alone behind an agent principal -> 403 `owner_required`, no temp file (`:165`). RED on round one (`red-round-one.txt`): the remote DESK import succeeded (`{"meeting_id": "0e3f8bcb", "transcription_status": "importing"}` — Astra's `48a3fa11` reproduced) and the HTTP route stored the agent's upload (202). M14 (the intake checks the owner only inside `invoke`) -> red with `['Path.is_file', 'os.access', 'Path.open']`; M15 (`owner_only=False`) -> red, the agent import succeeds; the round-one local-owner fence stays green under both (`red-mutations.txt`).
- **Filesystem audit of the registry.** Of the 17 descriptors, only `meeting.import` takes a transport-held file (`held`), and its only name-like argument is `filename` (the extension picks the format; the hub never opens by it). No other descriptor has a path argument or a held input; none spawns a process. The model call behind `meeting.summary.run` is queued work, not a caller-named path.
- **2. `thought.list`'s declared shape (P2).** `result="{items, next_cursor}"` (`holdspeak/operations.py:560`); `docs/generated/operations.json` regenerated. Fence for the CLASS: every descriptor whose `result` declares a braced shape (8 of 17) runs its real producer through the hub's registry and must return the declared top-level keys (`test_philo5_the_loop_r2.py:333`; `brief.shelf.read` is a data-keyed map and is checked as one); a second test fails if a braced declaration has no producer in the fence (`:327`). RED on round one: `thought.list declares ['thoughts', 'next_cursor']; the producer returned ['items', 'next_cursor']`.
- **3. Shelf writes traverse the registry (P2).** `test_philo5_the_loop_r2.py:348` records the hub's ONE `invoke` for the HTTP shelf write + read and the MCP `monday_brief.shelf` + `monday_brief.shelf_read`. M12 (MCP shelf write calls the composed service directly) -> `MCP shelf left the registry: ['brief.shelf.read']`; M13 (the same for HTTP) -> `HTTP shelf left the registry: ['brief.shelf.read']`; the round-one state fence `test_phase4_mcp_shelf_writes_are_the_hubs_shelf` stays GREEN under both — Astra's finding reproduced, now fenced. The implementation was already correct, so there is no round-one red for this fence; the mutations are its red.
- **4. The admission wording.** Phase status "Decisions made" / "Decisions deferred" / "Discovered missing admissions" rewritten as INHERITED DEBT (Article XI), UNRULED on "acts under Article V" (filing), assigned (BACKLOG "PHILO-5-02 follow-ups"); the exemption claim is withdrawn; the test docstring at `test_philo5_the_loop.py:618` says CHARACTERIZATION ONLY.
- **Line pin paid.** The four lines added to the MCP intake moved the `recipe.run` call `holdspeak/mcp/tools.py:848` -> `:852`; its pin in `tests/unit/test_phase143_inference_capability_census.py:395` is re-anchored; so are the three routing pins `holdspeak/mcp/tools.py:980/981/983` -> `:984/985/987` in `tests/unit/test_phase143_routing_authority_census.py:109,172,205` (the first round-two capture below is red on exactly that pin; the second is after the re-anchor).
- **Not claimed.** The contract-level unit test (`test_the_contract_refuses_a_non_owner_before_anything_else`) is red on round one by an unavailable symbol — not claimed as a behavioural red. No full suite, no browser walk, no real Codex rehearsal in this round.

## Proof

### Captured run — 2026-09-24T20:09:59Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider -n 8 $(cat /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/scoped-list.txt)`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 833d28b1805b267a8535211ea43b0501fa3cac67

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 40%]
..................................F.....F............................... [ 48%]
........................................................................ [ 56%]
........................................................................ [ 65%]
........................................................................ [ 73%]
........................................................................ [ 81%]
........................................................................ [ 89%]
........................................................................ [ 97%]
.....................                                                    [100%]
=================================== FAILURES ===================================
___________ test_the_loop_keeps_its_base_outcome[http thought list] ____________
[gw3] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-5-02/.venv/bin/python

hub = <tests.unit.test_philo5_loop_compat.Hub object at 0x114d13230>
label = 'http thought list', call = <function <lambda> at 0x10d8112d0>
base = (200, True)

    @pytest.mark.parametrize(("label", "call", "base"), ROWS, ids=[row[0] for row in ROWS])
    def test_the_loop_keeps_its_base_outcome(hub: Hub, label: str, call: Callable[[Hub], Any], base: Any) -> None:
>       assert call(hub) == base
E       assert (200, False) == (200, True)
E         
E         At index 1 diff: False != True
E         Use -v to get more diff

tests/unit/test_philo5_loop_compat.py:168: AssertionError
______ test_the_loop_keeps_its_base_outcome[resource thoughts unfinished] ______
[gw3] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-5-02/.venv/bin/python

hub = <tests.unit.test_philo5_loop_compat.Hub object at 0x114d13230>
label = 'resource thoughts unfinished'
call = <function <lambda> at 0x10d811590>, base = ('ok', True)

    @pytest.mark.parametrize(("label", "call", "base"), ROWS, ids=[row[0] for row in ROWS])
    def test_the_loop_keeps_its_base_outcome(hub: Hub, label: str, call: Callable[[Hub], Any], base: Any) -> None:
>       assert call(hub) == base
E       AssertionError: assert ('ok', False) == ('ok', True)
E         
E         At index 1 diff: False != True
E         Use -v to get more diff

tests/unit/test_philo5_loop_compat.py:168: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_philo5_loop_compat.py::test_the_loop_keeps_its_base_outcome[http thought list]
FAILED tests/unit/test_philo5_loop_compat.py::test_the_loop_keeps_its_base_outcome[resource thoughts unfinished]
2 failed, 883 passed in 73.16s (0:01:13)
```

### Captured run — 2026-09-24T20:13:33Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider -n 8 $(cat /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/scoped-list.txt)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 833d28b1805b267a8535211ea43b0501fa3cac67

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 40%]
........................................................................ [ 48%]
........................................................................ [ 56%]
........................................................................ [ 65%]
........................................................................ [ 73%]
........................................................................ [ 81%]
........................................................................ [ 89%]
........................................................................ [ 97%]
.....................                                                    [100%]
885 passed in 73.09s (0:01:13)
```

### Captured run — 2026-09-24T20:14:52Z

- **Command:** `bash -c set -o pipefail; cd web && npx vitest run src/desk/chair 2>&1 | tail -6`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 833d28b1805b267a8535211ea43b0501fa3cac67

```text

 Test Files  15 passed (15)
      Tests  89 passed (89)
   Start at  14:14:52
   Duration  3.29s (transform 2.89s, setup 1.56s, import 6.98s, tests 5.14s, environment 5.35s)
```

### Captured run — 2026-09-24T20:14:56Z

- **Command:** `bash -c set -e; uv run python scripts/gen_operations_json.py --check; uv run python scripts/residual_census.py --check; uv run python scripts/philo_api_reference.py --check; uv run python scripts/philo_boundary_census.py --check; uv run python scripts/philo_graph_reference.py --check; uv run python scripts/gen_mcp_sidecar_doc.py --check 2>/dev/null || HOME=$(mktemp -d) uv run pytest -q -p no:cacheprovider tests/unit/test_mcp_sidecar_doc_drift.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 833d28b1805b267a8535211ea43b0501fa3cac67

```text
OK docs/generated/operations.json
RESIDUAL FENCE GREEN: 320 identities match /Users/karol/dev/tools/wt-philo-5-02
API reference checked
Boundary candidate census checked
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
wrote docs/MCP_SIDECAR.md
  228 tools across 41 families
```

### Captured run — 2026-09-24T20:17:24Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider -n 8 $(cat docs/internal/philo/phase-5/the-loop/scoped-tests.txt)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 833d28b1805b267a8535211ea43b0501fa3cac67

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  8%]
........................................................................ [ 16%]
........................................................................ [ 24%]
........................................................................ [ 32%]
........................................................................ [ 40%]
........................................................................ [ 48%]
........................................................................ [ 56%]
........................................................................ [ 65%]
........................................................................ [ 73%]
........................................................................ [ 81%]
........................................................................ [ 89%]
........................................................................ [ 97%]
.....................                                                    [100%]
885 passed in 73.40s (0:01:13)
```

### Captured run — 2026-09-24T20:43:48Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider -n 8 $(cat docs/internal/philo/phase-5/the-loop/round-2/scoped-tests.txt)`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** b418e149876c382609fb2165d6c229b40a4aca7a

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  7%]
........................................................................ [ 14%]
........................................................................ [ 22%]
........................................................................ [ 29%]
........................................................................ [ 36%]
........................................................................ [ 44%]
.................................................................F...... [ 51%]
........................................................................ [ 58%]
........................................................................ [ 66%]
........................................................................ [ 73%]
........................................................................ [ 80%]
........................................................................ [ 88%]
........................................................................ [ 95%]
...........................................                              [100%]
=================================== FAILURES ===================================
__ test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer ___
[gw4] darwin -- Python 3.14.2 /Users/karol/dev/tools/wt-philo-5-02/.venv/bin/python

    def test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer() -> None:
        definitions, references, pointers, profile_ids = _routing_ast_inventory(REPO)
        assert definitions == ROUTING_RESOLVER_DEFINITIONS
>       assert references == ROUTING_RESOLVER_REFERENCES
E       AssertionError: assert {'holdspeak/d...acement', ...} == {'holdspeak/d...acement', ...}
E
E         Extra items in the left set:
E         'holdspeak/mcp/tools.py:985:import:resolve_meeting_placement'
E         Extra items in the right set:
E         'holdspeak/mcp/tools.py:981:import:resolve_meeting_placement'
E         Use -v to get more diff

tests/unit/test_phase143_routing_authority_census.py:363: AssertionError
=========================== short test summary info ============================
FAILED tests/unit/test_phase143_routing_authority_census.py::test_ast_census_is_exact_for_every_routing_resolver_reference_and_pointer
1 failed, 978 passed in 72.55s (0:01:12)
```

### Captured run — 2026-09-24T20:45:20Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); HOME=$H PLAYWRIGHT_BROWSERS_PATH=/Users/karol/Library/Caches/ms-playwright npm_config_cache=/Users/karol/.npm uv run pytest -q -p no:cacheprovider -n 8 $(cat docs/internal/philo/phase-5/the-loop/round-2/scoped-tests.txt)`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b418e149876c382609fb2165d6c229b40a4aca7a

```text
bringing up nodes...
bringing up nodes...

........................................................................ [  7%]
........................................................................ [ 14%]
........................................................................ [ 22%]
........................................................................ [ 29%]
........................................................................ [ 36%]
........................................................................ [ 44%]
........................................................................ [ 51%]
........................................................................ [ 58%]
........................................................................ [ 66%]
........................................................................ [ 73%]
........................................................................ [ 80%]
........................................................................ [ 88%]
........................................................................ [ 95%]
...........................................                              [100%]
979 passed in 75.61s (0:01:15)
```

### Captured run — 2026-09-24T20:46:40Z

- **Command:** `bash -c set -o pipefail; H=$(mktemp -d); export HOME=$H; uv run python scripts/philo_api_reference.py --check && uv run python scripts/philo_boundary_census.py --check && uv run python scripts/gen_operations_json.py --check && uv run python scripts/philo_openapi_reference.py --check && uv run python scripts/philo_graph_reference.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b418e149876c382609fb2165d6c229b40a4aca7a

```text
API reference checked
Boundary candidate census checked
OK docs/generated/operations.json
OpenAPI: 569 paths
note: subtype conflict edge.cli.hub_restart: astra=process.restart; muaddib=cli
note: subtype conflict edge.face.arrival_load: astra=lifecycle.mount; muaddib=navigation.load
note: subtype conflict edge.face.thought_keep: astra=pointer.blur; muaddib=pointer.click
note: subtype conflict edge.route.brief_item_shelf: astra=ui; muaddib=http
note: subtype conflict edge.route.brief_latest: astra=ui; muaddib=http
note: subtype conflict edge.route.heartbeat_run_now: astra=ui; muaddib=http
note: subtype conflict edge.route.inference_assignments_set: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_delete: astra=ui; muaddib=http
note: subtype conflict edge.route.model_profile_unbind: astra=ui; muaddib=http
note: subtype conflict edge.route.projection_presentation: astra=ui; muaddib=http
note: subtype conflict edge.route.projections_list: astra=ui; muaddib=http
note: subtype conflict edge.timer.heartbeat_sweep: astra=ui; muaddib=timer
note: subtype conflict iface.face.arrival: astra=face.section; muaddib=face.window
note: subtype conflict iface.face.first_words: astra=face.card; muaddib=face.panel
graph join checked: docs/generated/graph.json; 14 subtype conflict note(s)
```

### Captured run — 2026-09-24T20:46:48Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) .githooks/dw check holdspeak-philo`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** b418e149876c382609fb2165d6c229b40a4aca7a

```text
dw check: ok
```
