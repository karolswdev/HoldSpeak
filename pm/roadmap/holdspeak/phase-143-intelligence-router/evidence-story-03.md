# Evidence - HSEGHS001HS104-143-03

- **Story:** HSEGHS001HS104-143-03 - Reusable Model Profile Authority
- **Status:** done
- **Date:** 2026-08-21

## Outcome

Story 03 separates reusable model identity from private, mutable execution
configuration. Immutable v2 profile revisions contain only safe model and
capability facts. Hub-local binding heads point to an existing deployment head
and its exact content-addressed `DeploymentRevision`; every profile and
deployment identity is reconstructed and verified before projection, probe, or
binding.

The shared OWNER-only application service now backs HTTP and MCP list, detail,
create, revise, probe, bind, unbind, and delete surfaces. List and detail expose
the safe current binding and latest matching readiness observation, so an owner
can recover the narrow CAS revision after restart without learning a path,
endpoint, secret slot, or private observation identifier.

## Authority and compatibility truth

- OWNER enforcement is the first public service action; AGENT, MODEL_TURN, and
  missing-principal calls cannot discover records or trigger a probe.
- Readiness observations are minted server-side after bounded destination
  observation, then admitted only after the exact deployment head is rechecked
  under `BEGIN IMMEDIATE`.
- Profile deletion consults registered, fail-closed dependency providers for
  bindings, deployments, artifacts, acquisitions, assignments, and route plans.
- V2 profiles, bindings, tombstones, and readiness observations are hub-local;
  hostile sync buckets refuse and sync never creates them.
- The v1 adapter is read-only and resolves the same historical
  `DeploymentRevision` and placement receipt without rewriting legacy bytes or
  creating v2 state.
- Download and use-existing commands now stop at model availability. The Models
  surface says `Added` / `Available in Models`, suppresses repeat acquisition,
  and does not claim the model is assigned to Thoughts.

## Verification

### Integrated authority, acquisition, registry, transport, schema, and census

```text
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q \
  tests/unit/test_model_profile_authority.py \
  tests/unit/test_inference_model_acquisition.py \
  tests/unit/test_profile_key_live_resolution.py \
  tests/unit/test_inference_targets.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_inference_capability_registry.py \
  tests/unit/test_api_surface.py tests/unit/test_db.py \
  tests/unit/test_mcp_phase133_surface.py tests/unit/test_mcp_tools.py \
  tests/unit/test_mcp_phase133_auth.py

157 passed in 26.03s
```

### Web compatibility and production build

```text
vitest run InferenceCapabilityPanel.test.tsx settingsModels.test.tsx
34 passed

npm run build
vite build completed successfully (inherited chunk-size warnings only)
```

### Static hygiene

```text
ruff check <changed Story 03 Python files>
All checks passed!

git diff --check
# clean
```

## Known inherited baseline

Ten old model-run cases in `tests/unit/test_web_routes_primitives.py` return
`409 inference_target_unavailable` because their historical
`_this_machine_readiness` monkeypatch no longer controls the direct configured
model resolver. The same failures reproduce on merged `main`; Story 03 does not
hide or broaden into that fixture migration.

## Review result

Independent architecture/counsel review returned **RATIFY** after persisted
profile/deployment tamper checks, restart-discoverable binding/readiness truth,
registered dependency providers, executable v1 parity, and the exact 44-site
routing census were verified.

### Captured run — 2026-08-22T03:28:41Z

- **Command:** `/bin/zsh -lc PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q tests/unit/test_model_profile_authority.py tests/unit/test_inference_model_acquisition.py tests/unit/test_profile_key_live_resolution.py tests/unit/test_inference_targets.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_inference_capability_registry.py tests/unit/test_api_surface.py tests/unit/test_db.py tests/unit/test_mcp_phase133_surface.py tests/unit/test_mcp_tools.py tests/unit/test_mcp_phase133_auth.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** a7ec4d97d11e8ec92a387e5211b59b1ce576ea9c

```text
........................................................................ [ 45%]
........................................................................ [ 91%]
.............                                                            [100%]
157 passed in 17.96s
```
