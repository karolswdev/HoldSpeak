# Evidence - HS-94-10

- **Story:** HS-94-10 - Multi-node chaos/security/performance owner walk and close
- **Status:** done
- **Date:** 2026-07-16

## Proof

### Captured run — 2026-07-16T09:26:20Z

- **Command:** `.venv/bin/python scripts/phase94_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 08dcb1ea7c3a76879ad741a0663a05b79748bb9a

```text
HS-94-10 campaign — 2026-07-16T09:26:50Z
report: /Users/karol/dev/tools/HoldSpeak/pm/roadmap/holdspeak/phase-94-delivery-runtime/evidence/hs-94-10/campaign-report-20260716T092651Z.json

north-star journeys:
  observe: True
  evidence: True
  steer: True
  launch: True
fault matrix:
  node_kill_reconcile: True
  generation_mismatch: True
  expired: True
  out_of_order: True
  source_failure_lkg: True
  link_loss_cursor_resume: True
poll economy: True (1 client == 3 dw calls, 10 clients == 3)
posture invariance: True
zero duplicate/wrong-target: True
self attempt exactly-once: True
census accounted: True (13/13 commands)
census clean (no leaks): True (0 leaks)
compat consumers:
  /api/missioncontrol/: 11 consumer file(s) (7 authored, 4 generated build copies) still call /api/missioncontrol/ — keep the compat route until parity shows zero callers
  /api/coders/: 36 consumer file(s) (14 authored, 22 generated build copies) still call /api/coders/ — keep the compat route until parity shows zero callers
```

### Captured run — 2026-07-16T09:26:51Z

- **Command:** `.venv/bin/python scripts/phase94_audit_census.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 08dcb1ea7c3a76879ad741a0663a05b79748bb9a

```text
census over campaign-report-latest.json
  commands: 13/13 accounted, 0 unaccounted
  leak scan: 0 leaks across 33 wire bodies, 18 hub rows, 11 node receipts
  verdict: PASS
```

### Captured run — 2026-07-16T09:26:51Z

- **Command:** `uv run pytest -q tests/integration/test_delivery_campaign.py`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 08dcb1ea7c3a76879ad741a0663a05b79748bb9a

```text
........                                                                 [100%]
8 passed in 30.32s
```
