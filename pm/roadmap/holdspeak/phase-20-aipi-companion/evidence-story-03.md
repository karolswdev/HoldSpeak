# Evidence — HS-20-03 Companion Debug Surface

- **Date:** 2026-05-24
- **Status:** done
- **Story:** [HS-20-03](./story-03-companion-debug-surface.md)

## What changed

- Added `/api/companion/status` to `holdspeak/web_server.py`.
- The endpoint reports:
  - connected AIPI-compatible devices;
  - supported companion query names;
  - fresh waiting Claude/Codex session state;
  - dictation pipeline and target override settings;
  - runtime text insertion status;
  - `ready_for_agent_reply` and explicit blockers.
- Added integration tests for ready and blocked companion states.
- Documented companion readiness verification in
  [Claude/Codex Agent Hook Install](../../../../docs/AGENT_HOOK_INSTALL.md).

## Validation

```bash
.venv/bin/pytest -q tests/integration/test_web_server.py::TestCompanionStatusEndpoint
```

Result:

```text
2 passed in 0.62s
```

```bash
.venv/bin/pytest -q tests/integration/test_web_server.py::TestDeviceHealthEndpoint tests/integration/test_web_server.py::TestCompanionStatusEndpoint tests/integration/test_web_server.py::TestRuntimeControlEndpoints
```

Result:

```text
10 passed in 0.91s
```

```bash
git diff --check
```

Result: passed.

## Notes

- `ready_for_agent_reply` is intentionally strict: it requires a connected
  device, a fresh waiting agent question, enabled dictation pipeline, and
  available text insertion status.
- The endpoint is diagnostic; it does not add an autonomous reply path.
