# Evidence - PHILO-5-01

- **Story:** PHILO-5-01 - One decision through one contract (and the Codex path proved)
- **Status:** done
- **Date:** 2026-09-24

## What was built

- The contract: `holdspeak/operations.py` — `OperationDescriptor` (:57), the four decision descriptors and `DESCRIPTORS` (:218), `bind` (:274), `OperationRegistry.invoke` (:252; authority refusal :258), `for_context` (:295) and `for_runtime` (:315). No decorator, no plugin framework. The model-tool descriptor (`services/tool_capability_service.py:216`) and kernel `OperationSpec` are untouched.
- Hub composition binds it once to the hub's own `PrimitiveService` and puts the one registry on the root and the context: `holdspeak/runtime/composition.py:479,482`; fields `runtime/composition.py:88`, `web/context.py:57`.
- HTTP over `invoke`: `web/routes/primitives/decisions.py:44,54,75,88` (list, create, read, update). In the hub, `GET /api/decisions` and `GET /api/decisions/{id}` are served FIRST by the project-decisions router (`web_server.py:1158` before `:1233`, verified on the real app); its desk branches now call the same contract: `web/routes/decisions.py:53,58`.
- MCP over `invoke`: `mcp/tools.py:563,569,575,581` (`kind="decisions"` of `desk.list/get/create/update`, and `desk.verb` desk.create/desk.update through the same helpers); `desk.delete` and every other kind keep the generic path.
- Standalone retired: `serve_standalone` deleted; `serve()` is proxy-only (`mcp/server.py:458`); `composition.STANDALONE_ENV`/`standalone_enabled` deleted; docs `docs/MCP_SIDECAR.md`, `docs/SECURITY.md`, `holdspeak/runtime_lock.py` docstring updated; the HS-165 walk harness composes in its own test process (`tests/integration/_mcp_walk_server.py`).
- The Codex seams: the rig publishes its port through `claim_database(..., port=port, host=host)` (`scripts/graph_walk.py:1517`) and persists its token to `meeting.web_auth_token` under the lane HOME, path-guarded (`scripts/graph_walk.py:1484`); `scripts/astra` gains a repeated `-c KEY=VALUE` passthrough (`scripts/astra:21,25,54`; documented `docs/internal/TWO-BRAINS.md` §6).
- The export: `docs/generated/operations.json` from `scripts/gen_operations_json.py`; drift-guarded in `tests/unit/test_philo5_one_decision.py`.
- The residual set: `docs/internal/philo/phase-5/residual-set.json`, computed by `scripts/residual_census.py`.

## Measurements (two, never one)

- **Public MCP tools:** 225 before, 225 after (`docs/MCP_SIDECAR.md` roster regenerated; unchanged).
- **Residual implementation identities** `(transport, entry point, discriminator)`: 334 at `4b4f8d94` (269 MCP, 65 HTTP; 67 route `*Service(...)` constructions, the charter's count) -> 327 after (263 MCP, 64 HTTP; 66 constructions). Paid: exactly 7 decision identities (listed in the set's `paid`).

## Reds (retained under `docs/internal/philo/phase-5/one-decision/`)

- `red-main-behaviour.txt` — the new fences run UNCHANGED on a `git archive origin/main` copy with main's own code on `PYTHONPATH`: 4 failed. The Codex seam: `AssertionError: the rig hub published no port: {... 'port': None ...}`; the retired hatch: main created `holdspeak.db` under the sidecar's HOME; `composition.current()` did not raise with the variable set; `serve()` started the refinement runtime.
- `red-main-residual.txt` — `scripts/residual_census.py --check --root <main copy>`: `RESIDUAL FENCE RED: 7 problem(s)`, each a NEW residual identity (the 7 decision entries this story pays).
- `red-mutations.txt` — six deliberate mutations, each turns its fence red: m1 a fresh `PrimitiveService` bound at composition (identity assertion fails); m2 the HTTP create route calls the service by hand (the invoke recording misses `decision.create`); m3 the MCP create branch calls the service by hand (`TypeError` instead of the named `invalid_arguments` refusal, and the recording misses it); m4 a new route `PrimitiveService(...)` construction (`NEW residual identity`); m5 the rig stops persisting its token (`'' == 'philo5-01-token'`); m6 `invoke` drops the authority check (the authority fields reach the service).
- `green-branch-residual.txt` — `RESIDUAL FENCE GREEN: 327 identities match` the branch.

## The Codex proof (`docs/internal/philo/phase-5/one-decision/codex/`)

A FRESH `codex exec` session (codex-cli 0.155.1, `gpt-6-astra`, session `01a0d4cc-8b58-78a1-b823-8976291fae32`) launched by `scripts/astra ask ... -c mcp_servers.holdspeak.command=<lane>/.venv/bin/holdspeak-mcp -c mcp_servers.holdspeak.cwd=<lane> -c mcp_servers.holdspeak.env.HOME=<the rig hub's HOME>`, against the rig's hub (`graph_walk.Hub`) in a `mktemp -d` HOME:

- `effective-config.txt` — `codex mcp get holdspeak --json` with the same overrides (stdio, the lane's executable and cwd, `env.HOME` = the hub HOME), and what that HOME resolves to in the lane's own code: DB, lock and config under the hub HOME; `discover_hub()` finds port 59823; token present.
- `transcript.events.jsonl` — every MCP call on the `holdspeak` server: `desk.create kind=decisions` -> `decision_32e0c6ba0eea`; `desk.get` -> "PHILO-5-01 Codex proof decision", accepted; the shell restart request; `desk.get` again after the restart -> the same; `desk.list` -> `[decision_32e0c6ba0eea]`. `mcp_errors: []` (`codex-final.md`).
- `restart.done` — the rig restart: pid 57030 -> 57993, same port 59823, `same_db_path: true`, the new lock body names the new pid and the port.
- `db-proof.txt` — the row, read with `sqlite3 -readonly` from `<hub HOME>/.local/share/holdspeak/holdspeak.db` after the rig stopped.
- `hub.json` (the first hub: pid, port, DB and config paths, lock body), `hub.log` (the restarted hub's lines; the first process's lines are replaced by `Hub.start` on restart — its facts are in `hub.json`).

The desk was never touched: every hub in this story ran in a `mktemp -d` HOME, and the Codex MCP server's `HOME` was that HOME.

## Proof

### Captured run — 2026-09-24T19:05:54Z

- **Command:** `bash -c set -o pipefail; HOME_REAL=$HOME; HOME=$(mktemp -d) PLAYWRIGHT_BROWSERS_PATH=$HOME_REAL/Library/Caches/ms-playwright npm_config_cache=$HOME_REAL/.npm uv run pytest -q -p no:cacheprovider -n 8 tests/unit/test_philo5_one_decision.py tests/unit/test_philo5_codex_seams.py tests/unit/test_mcp_*.py tests/unit/test_philo_graph_atlas.py tests/unit/test_philo3_01_decision_route.py tests/unit/test_philo3_03_brief_clock.py tests/unit/test_philo4_02_decision_rows.py tests/unit/test_philo4_04_atlas_contracts.py tests/unit/test_philo4_02_readable_rows.py tests/unit/test_philo3_summary_rig.py tests/unit/test_web_routes_primitives.py tests/unit/test_web_routes_sync_primitives.py tests/unit/test_primitive_contract.py tests/unit/test_phase200_one_composition_root.py tests/unit/test_phase143_inference_capability_registry.py tests/unit/test_graph_walk_producer_clock.py tests/unit/test_graph_walk_http_fault.py tests/unit/test_graph_walk_calibration.py tests/unit/test_phase200_runtime_identity.py tests/unit/test_hs201_startup_identity.py tests/unit/test_phase200_intel_drain.py tests/unit/test_doc_drift_guard.py tests/unit/test_api_surface.py tests/unit/test_phase200_doc_claims.py tests/unit/test_phase200_canon_guard.py tests/unit/test_philo_graph_schema.py tests/unit/test_philo_architecture.py tests/unit/test_one_path_spine.py tests/integration/test_phase200_one_composition_root_processes.py tests/integration/test_hs165_mcp_walk.py tests/integration/test_decision_records.py tests/integration/test_phase200_runtime_identity.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1bc2bdb7452df4865b3c4ef3cb0e56fcbf02abf0

```text
bringing up nodes...
bringing up nodes...

........................................................................ [ 11%]
........................................................................ [ 22%]
........................................................................ [ 33%]
........................................................................ [ 44%]
........................................................................ [ 56%]
........................................................................ [ 67%]
........................................................................ [ 78%]
........................................................................ [ 89%]
..................................................................       [100%]
642 passed in 71.67s (0:01:11)
```

### Captured run — 2026-09-24T19:07:12Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run python scripts/gen_operations_json.py --check && HOME=$(mktemp -d) uv run python scripts/residual_census.py --check && HOME=$(mktemp -d) uv run python scripts/gen_mcp_sidecar_doc.py && git diff --exit-code docs/MCP_SIDECAR.md && HOME=$(mktemp -d) uv run python scripts/philo_api_reference.py --check && HOME=$(mktemp -d) uv run python scripts/philo_boundary_census.py --check`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 1bc2bdb7452df4865b3c4ef3cb0e56fcbf02abf0

```text
OK docs/generated/operations.json
RESIDUAL FENCE GREEN: 327 identities match /Users/karol/dev/tools/wt-philo-5-01
wrote docs/MCP_SIDECAR.md
  225 tools across 41 families
API reference checked
Boundary candidate census checked
```

### Captured run — 2026-09-24T19:07:20Z

- **Command:** `bash -c set -o pipefail; HOME=$(mktemp -d) uv run python scripts/residual_census.py --check --root /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/mainco`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1bc2bdb7452df4865b3c4ef3cb0e56fcbf02abf0

```text
NEW residual identity (not in the set): ('http', 'holdspeak/web/routes/primitives/decisions.py::build_desk_decisions_router._svc', 'PrimitiveService')
NEW residual identity (not in the set): ('mcp', 'desk.create', 'kind=decisions')
NEW residual identity (not in the set): ('mcp', 'desk.get', 'kind=decisions')
NEW residual identity (not in the set): ('mcp', 'desk.list', 'kind=decisions')
NEW residual identity (not in the set): ('mcp', 'desk.update', 'kind=decisions')
NEW residual identity (not in the set): ('mcp', 'desk.verb', 'verb_id=desk.create,kind=decisions')
NEW residual identity (not in the set): ('mcp', 'desk.verb', 'verb_id=desk.update,kind=decisions')
RESIDUAL FENCE RED: 7 problem(s) against /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/mainco
```

### Captured run — 2026-09-24T19:07:29Z

- **Command:** `bash -c set -o pipefail; cd /private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/mainco && HOME=$(mktemp -d) PYTHONPATH=/private/tmp/claude-501/-Users-karol-dev-tools-HoldSpeak/fd5ad72b-2ed6-4ad6-b127-8b5e72ca6caa/scratchpad/mainco /Users/karol/dev/tools/wt-philo-5-01/.venv/bin/python -m pytest -q -p no:cacheprovider -rf tests/unit/test_philo5_codex_seams.py tests/integration/test_phase200_one_composition_root_processes.py::test_the_retired_standalone_hatch_still_refuses_and_opens_nothing tests/unit/test_phase200_one_composition_root.py::TestNoRuntimeRefusal::test_the_retired_standalone_env_improvises_no_root tests/unit/test_mcp_thoughts.py::test_proxy_serve_owns_no_runtime_and_opens_nothing 2>&1 | grep -E '^(FAILED|E  )|passed|failed' | head -30`
- **Cwd:** .
- **Exit code:** 1
- **Index-tree:** 1bc2bdb7452df4865b3c4ef3cb0e56fcbf02abf0

```text
E           AssertionError: the rig hub published no port: {'pid': 60597, 'process_start': '2026-09-24T13:07:30.613962', 'port': None, 'host': None, 'label': 'holdspeak web', 'alive': True}
E           assert None == 60147
E            +  where None = <built-in method get of dict object at 0x10f122ec0>('port')
E            +    where <built-in method get of dict object at 0x10f122ec0> = {'alive': True, 'host': None, 'label': 'holdspeak web', 'pid': 60597, ...}.get
E            +  and   60147 = <graph_walk.Hub object at 0x10f069e80>.port
E       AssertionError: 
E       assert not [PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-540/test_the_retired_standalone_ha0/home/.local/share/holdspeak/holdspeak.db')]
E        +  where [PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-540/test_the_retired_standalone_ha0/home/.local/share/holdspeak/holdspeak.db')] = list(<map object at 0x10f1b09c0>)
E        +    where <map object at 0x10f1b09c0> = rglob('holdspeak.db')
E        +      where rglob = PosixPath('/private/var/folders/q7/5dzz5g2116b3lq8rhg7hwjrr0000gn/T/pytest-of-karol/pytest-540/test_the_retired_standalone_ha0/home').rglob
E           Failed: DID NOT RAISE <class 'holdspeak.runtime.composition.NoRuntimeError'>
E       AssertionError: assert ['start', 'bi...ind', 'close'] == []
E         
E         Left contains 4 more items, first extra item: 'start'
E         Use -v to get more diff
FAILED tests/unit/test_philo5_codex_seams.py::test_a_rig_hub_is_found_and_accepted_by_the_real_proxy_across_a_restart
FAILED tests/integration/test_phase200_one_composition_root_processes.py::test_the_retired_standalone_hatch_still_refuses_and_opens_nothing
FAILED tests/unit/test_phase200_one_composition_root.py::TestNoRuntimeRefusal::test_the_retired_standalone_env_improvises_no_root
FAILED tests/unit/test_mcp_thoughts.py::test_proxy_serve_owns_no_runtime_and_opens_nothing
4 failed in 3.06s
```
