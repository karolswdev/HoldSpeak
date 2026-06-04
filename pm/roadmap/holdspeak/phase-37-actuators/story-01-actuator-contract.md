# HS-37-01 — Actuator contract + unblock the kind (gated, proposal-only)

- **Project:** holdspeak
- **Phase:** 37
- **Status:** not-started
- **Depends on:** none (Phase 35 groundwork is in place)
- **Unblocks:** HS-37-02, HS-37-03, HS-37-04, HS-37-05
- **Owner:** unassigned

## Problem

The plugin system has three kinds in the RFC but only two are live. The `actuator` kind is
blocked in two places: `plugin_sdk.validate_manifest` rejects it as deferred, and
`PluginHost(allow_actuators=False)` returns `status="blocked"` for any actuator-kind
plugin. Before anything else can happen we need a **contract for what an actuator
returns** and a host that can *propose* (not execute) an actuator's side effect — while
keeping execution firmly behind the gate.

## Scope

- **In:**
  - An **`ActuatorProposal`** result shape (dataclass + validation), distinct from an
    artifact-generator's read-only output: `target` (system, e.g. `github`/`jira`/
    `webhook`), `action` (verb, e.g. `create_issue`), `preview` (human-readable string),
    `payload` (machine dict of exactly what would be sent), `reversible: bool`, and the
    `required_capabilities`.
  - Unblock `actuator`/`actuators` in `holdspeak/plugin_sdk.py` (`KNOWN_PLUGIN_KINDS` +
    the `validate_manifest` `unknown_kind` message), and add a unit asserting an actuator
    manifest now validates.
  - Host change in `holdspeak/plugins/host.py`: an actuator's `run()` is routed to
    **produce an `ActuatorProposal`** (a new non-`blocked` status, e.g. `proposed`),
    **never** an inline side effect. The `allow_actuators` gate and the `blocked` status
    are **retained for execution** (HS-37-04), not for proposing — i.e. proposing is
    allowed; executing is what's gated.
  - Keep actuators **unregistered by default** so the default routing/dispatch path is
    byte-identical.
- **Out:**
  - Persistence (HS-37-02), the approval UI (HS-37-03), and any actual execution /
    egress (HS-37-04). This story stops at "the host can produce a proposal object."
  - A concrete reference actuator (HS-37-05) — a test double/fixture actuator is enough
    here.

## Acceptance criteria

- [ ] `ActuatorProposal` exists with validation; `target`/`action`/`preview`/`payload`/
      `reversible` are populated and the `payload` is the exact machine representation of
      the proposed side effect.
- [ ] `plugin_sdk.validate_manifest` accepts a `kind: actuator` manifest; the deferred
      `unknown_kind` rejection for `actuator` is gone (a test that previously asserted the
      rejection is updated in lockstep, not silenced).
- [ ] The host runs a fixture actuator and returns a **proposal** (status `proposed`),
      with **no side effect performed**; the `allow_actuators=False` default still blocks
      *execution* (covered fully in HS-37-04).
- [ ] With no actuator registered, the routing/dispatch path is byte-identical:
      `test_intent_router` / `test_intent_dispatch` / `test_multi_intent_routing` unchanged
      and green.
- [ ] Suite green; new/changed modules ruff + F821 clean.

## Test plan

- Unit: `ActuatorProposal` validation (happy + missing/invalid fields).
- Unit: `plugin_sdk` accepts the actuator kind (and still rejects genuinely-unknown
  kinds).
- Unit: a fixture actuator through the host yields a `proposed` result and performs no
  side effect (assert via a spy that no executor/connector was called).
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green; the plugin-frontier
  tests (`test_plugin_sdk.py`) updated for the now-valid actuator kind.

## Notes / open questions

- Mirror the existing `PluginRunResult` shape so the proposal flows through the same host
  plumbing (idempotency key, metrics, logging) as a normal run.
- The `payload` is stored verbatim and is the **source of truth** for execution parity in
  HS-37-04 — do not recompute it downstream from mutable state.
- Decision (deferred to HS-37-02): whether the proposal carries its own id or borrows the
  plugin-run idempotency key.
