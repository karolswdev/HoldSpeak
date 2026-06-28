# Evidence — Cadence Phase 8 (hardening + dogfood, the finale)

**Date:** 2026-06-28. **Branch:** `holdspeak/cadence-phase8-hardening`.

## What shipped

| Story | Files | Proof |
|-------|-------|-------|
| CAD-8-01 | `cadence/audit.py` (`export_audit`) + `commands/cadence.py` (`audit`) + `web/routes/cadence.py` (`GET /audit`) + `main.py` | `test_cadence_e2e.py` + route + CLI checks |
| CAD-8-02 | `tests/integration/test_cadence_e2e.py` | the full flow test |
| CAD-8-03 | the off-switch test | `test_master_off_switch_*` |
| CAD-8-04 | `docs/CADENCE.md` + `docs/README.md` pointer | doc-drift guard green |
| CAD-8-05 | `dogfood/PROTOCOL.md` Tier C | committed |

## The full journey, in one test

`test_full_chief_of_staff_flow`: seed a meeting + an action + a proposal → `tick` projects + scores
(2 loops) → `build_brief` leads with the top move → `build_closeout` recommends a decision per loop →
`apply_decision` snoozes the top loop → `export_audit` reflects it with `egress.scope == "local"`.
The audit is JSON-serializable and never claims off-machine egress.

## The trust posture, closed out

- **Master off-switch** proven: `_cadence_enabled()` is False when `cadence.enabled` is False (no
  in-runtime thread); `run-now`/`audit` still work on demand (explicit user actions).
- **Telemetry-free audit:** `holdspeak cadence audit --out audit.json` writes a complete local
  snapshot; the `/api/cadence/audit` route returns the same with a `local` egress badge.
- **The doc** is product-tense and passes the doc-drift / dash / roadmap-vocab guards (and the now
  product-real word `closeout` was un-banned from that guard, since it ships as a CLI command).

## Proof

- `uv run pytest -q` over cadence + web-server + the doc-drift / density guards → **205 passed.**
- **Program complete (8/8).** The live `.43` LLM proof is recorded in
  `../phase-7-llm-nba/proof/real-metal-43.md`. The remaining buttons are the owner's: the master
  switch, the live dogfood walk, and an optional real Telegram pairing.
