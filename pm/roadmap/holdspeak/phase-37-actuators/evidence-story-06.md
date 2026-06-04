# Evidence — HS-37-06: Actuator documentation (project docs update)

**Date:** 2026-06-04. **Branch:** `phase-37/hs-37-01-actuator-contract`.

## What shipped

All relevant project documentation now reflects what Phases 37-01→05 actually shipped —
actuators are documented for authors, surfaced in the public README, and no live doc still
calls them deferred. (Promoted to its own story per direct user ask.)

### `docs/PLUGIN_AUTHORING.md` — new **Actuators** section + reconciliation

- A full `## Actuators` section: the safety invariant; the propose → approve → execute
  flow diagram; the **`ActuatorProposal`** field table (target / action / preview / payload
  / reversible / required_capabilities); the lifecycle ladder (`proposed → approved →
  executed | rejected | failed`, retry from `failed`); the **three gates** (the `actuator`
  capability to propose, per-action **human approval**, the `MeetingConfig.allow_actuators`
  master switch + `allowed_actuators` allow-list); the **`ActuatorExecutor`** (payload
  parity / TOCTOU + audit + injected connector); and a **worked example** on
  `followup_ticket_actuator` (the `run()` shape + `build_outbox_connector` + the full
  wiring), with links to `actuators.py` / `actuator_executor.py` /
  `followup_ticket_actuator.py` / `test_actuator_reference.py`.
- Reconciled the four stale claims: the `kind` table row (`actuator` "_none shipped_" →
  `followup_ticket_actuator`, "Blocked by default" → "approval-gated"); the "gated off …
  deferred to a future phase" note → "actuators propose; they never act on their own" + a
  pointer; the manifest note "`actuator` is **not** a valid `kind` yet" → "**is** a valid
  kind"; and the **Out of scope** "Actuators … deferred to a later phase" bullet removed.
- Added `followup_ticket_actuator` to the built-in reference table.

### `README.md` (public surface)

- The "Meeting intelligence plugins" section gains an **actuators** paragraph: the third
  kind, an approval-gated external side effect (audited, executed == previewed), **off by
  default**, with `followup_ticket_actuator` as the shipped worked example — linked to the
  new `docs/PLUGIN_AUTHORING.md#actuators` section. The "write your own" line now also
  names the actuator approval flow.

### Doc-truth scope note

`docs/evidence/**` (frozen phase-MIR-01 evidence) is left verbatim. The MIR-01 plan's
`MIR-S-002` "Actuator plugins MUST remain disabled by default" is **not** stale — it's
still honored: the `allow_actuators` master switch is off by default, so the requirement
holds; Phase 37 added the propose/approve/execute flow *around* that default, it didn't
flip it.

## Verification

```
$ grep -niE "actuator" docs/PLUGIN_AUTHORING.md | grep -iE "defer|blocked by default|later phase|not.*valid|none shipped"
(none)

$ uv run pytest -q tests/unit/test_doc_drift_guard.py
3 passed                # no live doc claims a stub; the scanner sees the docs; no dangling relative links

$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2080 passed, 15 skipped in 60.38s     # unchanged — docs-only
```

All the new relative links resolve (`holdspeak/plugins/actuators.py`,
`actuator_executor.py`, `builtin/followup_ticket_actuator.py`,
`tests/unit/test_actuator_reference.py`).

## Notes

- The authoring section mirrors `docs/CONNECTOR_DEVELOPMENT.md`'s shape (protocol →
  contract → gates → worked example → testing) so the two ecosystems read the same.
- The worked example is real, runnable code (it matches the shipped
  `followup_ticket_actuator` + `ActuatorExecutor`), not pseudocode — the HS-37-07 closeout
  verifies it stays accurate.
