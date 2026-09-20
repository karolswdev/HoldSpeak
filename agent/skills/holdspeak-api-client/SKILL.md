---
name: holdspeak-api-client
description: Use when changing a backend route or a web, companion or MCP client. Applies to the HoldSpeak repository, not to user-installed runtime Workbench skills.
---

# holdspeak-api-client

Read `AGENTS.md`, `CLAUDE.md` and the current charter first. Owner instructions
in the active session override standing workflows. Work in the assigned clone
or worktree. Paths below are repository-relative; verify them before editing.

## Inspect first

- `scripts/gen_api_surface.py`
- `docs/API_SURFACE.md`
- `web/src/lib/api.ts`
- `web/src/runtime/RuntimeBus.tsx`

## Vocabulary and invariants

HTTP route, runtime event, client projection and operation receipt are separate contracts.

## Change path

Use the typed HTTP boundary and shared runtime bus. Inspect server auth and error behavior. Regenerate the API roster and affected MCP reference; do not hand-edit generated output.

Update `docs/API_REFERENCE.md` and the corresponding Philo capability metadata when behavior
or evidence changes. Keep the source snapshot and test-execution status honest.

## Verification

Collect the relevant tests before running them:

```sh
HOME="$(mktemp -d)" uv run pytest --collect-only -q tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py
HOME="$(mktemp -d)" uv run pytest -q tests/unit/test_api_surface.py tests/unit/test_mcp_sidecar_doc_drift.py
```

These are starting checks, not a substitute for tests of the changed branch.
Workers run only their brief's scoped tests. The orchestrator owns the quiet
full suite. Never run `tests/e2e/test_metal.py`. Frontend changes also need
focused interaction tests and 1440/393 evidence under the current UI charter.

## Traps

Do not send provider keys to web state. Route presence and method alone do not prove authorization or idempotency.

## Prove completion

Report changed paths, the source-to-assertion trace, exact collected test names,
run outcomes, documentation changes and remaining unknowns. Separate mocked
proof from observed behavior. Workers hold for SHIP; they do not stage or commit.
