# Evidence - HS-104-01

- **Story:** HS-104-01 - The capability ledger — what each adapter actually knows
- **Status:** done
- **Date:** 2026-07-26

## What shipped

- `holdspeak/agent_capabilities.py` — the frozen declaration table
  (4 adapters × 5 capabilities, every cell a reviewed claim),
  `require_capability()` (typed refusal naming adapter + standing),
  `LEDGER_CONSUMERS` + `consumer_violations()` for the census.
- `GET /api/agents/capabilities`
  (`holdspeak/web/routes/system/agent_capabilities.py`, wired in the
  system router); API-surface manifest regenerated (334 routes).
- Contract schema (spec artifact):
  `pm/roadmap/holdspeak-mobile/contracts/schemas/agent-capabilities.schema.json`
  — the unit suite validates the LIVE route payload against it and
  proves a lying payload rejects.
- Doctor: "Agent capabilities" check — red when a registered consumer
  requests a capability the ledger declares `unavailable`, proven by
  a monkeypatched bad consumer in-test.
- `claude-code-hooks` declared all-`unavailable` per the recipe: the
  ledger never promises ahead of the code; HS-104-02 flips exactly
  the cells it implements.

## Proof

### Captured run — 2026-07-26T17:58:22Z

- **Command:** `uv run pytest -q tests/unit/test_agent_capabilities.py tests/unit/test_api_surface.py tests/unit/test_db.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** de3549638b27e0de0229f30453e6f3ee6eba0bb8

```text
........................................................................ [ 72%]
...........................                                              [100%]
99 passed in 6.75s
```
