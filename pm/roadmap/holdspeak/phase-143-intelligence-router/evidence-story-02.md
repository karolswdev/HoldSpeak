# Evidence - HSEGHS001HS104-143-02

- **Story:** HSEGHS001HS104-143-02 - Canonical Capability Registry
- **Status:** done
- **Date:** 2026-08-21

## Outcome

Story 02 adds one process-composed, deterministic authority for HoldSpeak's
typed inference jobs and retry policies. It owns no profile, assignment,
deployment, credential, or execution state and creates no second inference
gateway.

The sealed registry contains 51 capability definitions, including all 15
plugins installed by the production meeting host, and 7 immutable retry-policy
definitions. Every definition binds a closed result schema, requirements,
canonical egress boundaries, permitted retry policies, and safe owner copy.

Both the web server and standalone MCP sidecar compose the registry before
serving. Unknown, duplicate, confusable, schema-drifted, group-conflicting, or
unversioned plugin definitions therefore stop composition before profile or
runner access.

## Transport and privacy truth

- HTTP list/detail and MCP list/detail resources delegate the same owner-only
  application service and return the same safe projection.
- AGENT, MODEL_TURN/SERVICE, and unauthenticated callers cannot discover the
  owner inventory. MCP missing-principal refusal occurs before database access.
- The projection contains no source-module path, model locator, endpoint,
  credential, profile binding, or assignment state.
- API and MCP inventories and the model architecture documentation name the new
  surfaces explicitly.

## Verification

### Integrated registry, census, transport, and setup gate

```text
PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q \
  tests/unit/test_phase143_inference_capability_registry.py \
  tests/unit/test_phase143_inference_capability_census.py \
  tests/unit/test_phase143_routing_authority_census.py \
  tests/unit/test_phase143_surface_fallback_census.py \
  tests/unit/test_mcp_phase133_auth.py \
  tests/unit/test_mcp_phase133_surface.py \
  tests/unit/test_inference_setup_capability_truth.py \
  tests/unit/test_inference_model_acquisition.py \
  tests/unit/test_api_surface.py

80 passed in 19.92s
```

The combined run encountered the existing timing-sensitive setup-envelope
comparison once because its HTTP and MCP reads independently mint volatile
observation timestamps. The exact failed case passed immediately in isolation;
the remaining 63 registry/census/MCP/acquisition/API cases also passed together.

### Static hygiene

```text
/Users/karol/dev/tools/HoldSpeak/.venv/bin/ruff check \
  holdspeak/inference_capabilities.py \
  holdspeak/services/inference_capability_service.py \
  holdspeak/kernel/runtime.py \
  holdspeak/mcp/resources.py \
  holdspeak/mcp/server.py \
  holdspeak/web/routes/setup.py \
  tests/unit/test_phase143_inference_capability_registry.py
All checks passed!

git diff --check
# clean
```

## Known inherited baseline

The repository-wide one-path census currently reports the pre-existing,
main-reproducible `MeshServeWorker._mutation_direct_dispatch run_prompt` site.
Story 02 does not touch that source or its execution census and does not hide or
reclassify the inherited failure.

## Review result

Independent architecture/counsel review returned **RATIFY** after startup MCP
composition, per-capability parity, installed-plugin revision binding, recursive
closed result schemas, canonical egress vocabulary, and group-confusable
validation were added. A final audit also verified that the registered Ask,
Rails-grounding, meeting-plugin, and canonical prompt-adapter schemas accept
their real runtime results and reject unknown-field drift.

### Captured run — 2026-08-22T03:01:18Z

- **Command:** `/bin/zsh -lc PYTHONPATH=. /Users/karol/dev/tools/HoldSpeak/.venv/bin/pytest -q tests/unit/test_phase143_inference_capability_registry.py tests/unit/test_phase143_inference_capability_census.py tests/unit/test_phase143_routing_authority_census.py tests/unit/test_phase143_surface_fallback_census.py tests/unit/test_mcp_phase133_auth.py tests/unit/test_mcp_phase133_surface.py tests/unit/test_inference_setup_capability_truth.py tests/unit/test_inference_model_acquisition.py tests/unit/test_api_surface.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 273063bf3440e999ce51936dd00017c86e4aa554

```text
........................................................................ [ 90%]
........                                                                 [100%]
80 passed in 20.18s
```
