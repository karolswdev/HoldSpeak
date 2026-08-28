# Evidence - HS-146-02

- **Story:** HS-146-02 - Settings service + wire
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T22:15:25Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/integration/test_calendar_settings.py tests/unit/test_door_read_model.py tests/unit/test_door_transport_parity.py tests/unit/test_phase143_routing_authority_census.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** cea4d3ce31b25169157f03ffd583943270a31f16

```text
.....................................                                    [100%]
37 passed in 12.32s
```

## Orchestrator triage note

The captured run (37 passed) covers the sources wire (14
integration tests: two-source persist, id preservation/minting,
per-entry named refusals by label or index, non-list/non-object
refusals, the `_calendar_sources` fact truth, MCP path), door
semantics + transport parity, and the routing census. The worker's
own round ran 68 focused (incl. the hs145 glass e2e proving the
old-wire bridge still green) + a clean import smoke.

Orchestrator verification: a wider sweep of every test file
referencing `redacted_settings`/`_calendar_subscription`/
`settings_service` ran 93 passed with ONE failure — the
phase-143 routing census, pure line drift again from the
settings_service insertions (2 pointer entries, 3 classification
keys, 2 resolver-reference entries remapped 1:1; suite 10/10
after). The census's exactness is doing its job on a hot file;
each drift is remapped with attributes and classifications
byte-unchanged.

**Ruled dual-fact reality** (worker's honest audit, 12 consumers
tabled in its report): `_calendar_subscription` ships ALONGSIDE
`_calendar_sources` because the UI, walk script, and both door
glass e2es still read it — HS-146-03 retires the UI consumer,
HS-146-04 flips the seeds/walk. Retirement comments mark both
sites.
