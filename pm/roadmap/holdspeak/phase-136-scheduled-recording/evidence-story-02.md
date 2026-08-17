# Evidence - HS-136-02

- **Story:** HS-136-02 - The schedule verb (API + MCP)
- **Status:** done
- **Date:** 2026-08-16

## Proof

### Captured run — 2026-08-17T05:44:22Z

- **Command:** `uv run pytest -q tests/unit/test_scheduled_recording_routes.py tests/unit/test_scheduled_recording_mcp.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 45c473bc93035eab3f5101fe7cd5a6236f9d473f

```text
........................................                                 [100%]
40 passed in 7.96s
```

## Orchestrator verification (the done call)

- **Full suite** (isolated HOME, `-n auto`): 5917 passed, 47 skipped, 2
  failed — both resolved, neither a logic regression:
  - `test_api_surface::test_committed_manifest_matches_the_live_app` —
    the new `/api/scheduled-recordings` routes drifted the committed
    manifest. Regenerated via `scripts/gen_api_surface.py` (run under an
    isolated HOME — the script boots the live app and the owner's real
    DB is ahead at v63, so a bare run crashes on SchemaVersionError);
    `docs/api-surface.json` (451 routes) + `docs/API_SURFACE.md`
    updated, all 5 api-surface tests green.
  - `test_inference_runner::test_deadline_unknown_provider_closes_indeterminate_before_dispatch_returns`
    — untouched by this story; 3/3 green run serially → the known
    xdist concurrency flake (BACKLOG Candidate Z), not a regression.
- Focused route + MCP suites: 40 passed (see captured run above).
