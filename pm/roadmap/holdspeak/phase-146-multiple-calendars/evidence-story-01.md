# Evidence - HS-146-01

- **Story:** HS-146-01 - Multi-source plumbing (config + DB + conductor)
- **Status:** done
- **Date:** 2026-08-28

## Proof

### Captured run — 2026-08-28T22:06:22Z

- **Command:** `zsh -c H=$(mktemp -d); HOME=$H uv run --python 3.13.11 pytest -q tests/unit/test_phase143_routing_authority_census.py "tests/unit/test_db.py::TestDatabaseShape::test_fresh_schema_matches_canonical_snapshot" tests/unit/test_calendar_ingest_conductor.py tests/unit/test_calendar_events_repository.py tests/unit/test_calendar_ingest.py tests/unit/test_door_read_model.py tests/unit/test_door_transport_parity.py tests/integration/test_calendar_settings.py tests/unit/test_reconcile.py 2>&1 | tail -3`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** f316f047fb10283e47f0db0d26d066a0ed7c8ae5

```text
..................................................................       [100%]
66 passed in 24.60s
```

## Orchestrator triage note

The captured run (66 passed) is the final-tree focused set: calendar
repository (scoped replace, two-source coexistence, failure
isolation, orphan cleanup), conductor (multi-source iteration,
per-source failure isolation, empty-list no-fetch), ingest, reconcile
(column adds on an existing table), door read model + transport
parity (the bridge holds), calendar settings integration, the
routing-authority census, and the canonical schema snapshot. The
worker separately proved the wire bridge on the real-hub hs145 glass
e2e (2 passed) and a clean `import holdspeak.web_server` smoke.

**Full-sweep triage (readable log `sweep_hs146_s01.log`, run on the
worker tree): 13 failed / 6745 passed.** Eleven names baseline-exact.
Two branch-new, both lawful consequences with in-commit remedies:

| Name | Class | Disposition |
|---|---|---|
| `test_db…fresh_schema_matches_canonical_snapshot` | branch-caused, expected | the additive `source_id`/`source_label` columns + rescoped unique index; `tests/fixtures/db_schema_canonical.txt` regenerated per the documented recipe (isolated HOME), 2-line diff |
| `test_phase143_routing_authority_census…exact` | branch-caused, pure line drift | insertions in `config/core.py`, `config/integrations.py`, `settings_service.py` shifted pinned `file:line` anchors — 6 pointer entries + 5 `PROFILE_ID_CLASSIFICATIONS` keys remapped 1:1 per file with attributes AND classification values unchanged (verified by the census's own AST inventory before patching); suite 10/10 after |

**Two orchestrator surgical deltas after the sweep** (both verified
by the 66-test focused rerun; the sweep interpretation stands for the
worker tree): (1) restored five load-bearing comments the worker had
deleted out-of-scope (the no-credential-headers wire posture note,
join-outlasts-timeout, boot-is-a-refresh, the redirect-refusal
rationale, the repository transaction rationale); (2) hardened the
story-02 bridge: a `calendar.sources` wire write now validates every
URL instead of accepting raw dicts (story 02 replaces this with the
full named-refusal treatment + `_calendar_sources` fact). Nothing
in-tree posts the sources wire yet, so the sweep's coverage of the
guard is not weakened.
