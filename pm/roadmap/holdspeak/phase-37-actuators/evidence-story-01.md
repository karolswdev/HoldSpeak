# Evidence — HS-37-01: Actuator contract + unblock the kind (gated, proposal-only)

**Date:** 2026-06-04. **Branch:** `phase-37/hs-37-01-actuator-contract`.

## What shipped

The plugin system's third kind is now *proposable* — and the safety model is established
at the contract level: **an actuator proposes; it never acts.**

### Files

- **`holdspeak/plugins/actuators.py` (new)** — the `ActuatorProposal` contract:
  `target` / `action` / `preview` / `payload` (the exact machine side-effect, the parity
  source of truth) / `reversible` / `required_capabilities`; `from_run_output()` validates
  an actuator's `run()` output (collecting every problem at once) and raises
  `ActuatorProposalError` on a malformed proposal; `to_payload()` serializes; the
  `ACTUATOR_PROPOSAL_STATUS = "proposed"` constant.
- **`holdspeak/plugin_sdk.py`** — `actuator` added to `KNOWN_PLUGIN_KINDS` and the
  `actuator` capability to `KNOWN_PLUGIN_CAPABILITIES`; the deferred
  "(actuators are deferred to a later phase)" `unknown_kind` rejection removed.
- **`holdspeak/plugins/host.py`** — the propose-blocking branch is gone; an actuator now
  runs to **build a proposal**, surfaced as a `PluginRunResult(status="proposed")` with
  the proposal on `output`. A malformed proposal becomes a plain `error` (no side effect).
  `proposed` added to the status doc + the metrics dict/getter. `allow_actuators` is
  **retained, reserved** for gating *execution* of an approved proposal (HS-37-04), with a
  comment to that effect — it no longer gates *proposing*.

### The safety posture (HS-37-01 slice)

- Proposing is safe (it performs no side effect), so it isn't gated — but an actuator
  **opts in** via the `actuator` capability, which is **off by default**: a registered
  actuator is capability-`blocked` until an operator enables it.
- A malformed `run()` output can't slip through as a side effect — it's an `error`.
- Execution doesn't exist yet; `allow_actuators` is the future gate for it (HS-37-04).

## Verification

### Targeted — contract + lockstep + metrics

```
$ uv run pytest -q tests/unit/test_actuator_contract.py tests/unit/test_intent_security.py \
    tests/unit/test_plugin_sdk.py tests/unit/test_plugin_pack_loader.py \
    tests/unit/test_intent_observability.py
52 passed
```

- `test_actuator_contract.py` (new) — `ActuatorProposal` happy paths (minimal, full
  round-trip, string-stripping, empty payload) + rejections (non-mapping, each missing/
  blank required string, non-object payload, non-list capabilities, all-problems-at-once).
- `test_intent_security.py` (rewritten in lockstep) — an actuator run → `proposed` + the
  proposal on output + **no side effect**; a malformed proposal → `error`; and the
  `actuator` capability is **off by default** (registered actuator `blocked` until the
  capability is enabled, then `proposed`).
- `test_plugin_sdk.py` (updated in lockstep) — `test_actuator_kind_is_accepted` (+ the
  `actuator` capability) replaces the old `..._is_rejected_this_phase`.

### Routing invariants — byte-identical default path

```
$ uv run pytest -q tests/unit/test_intent_router.py tests/unit/test_intent_dispatch.py \
    tests/unit/test_intent_pipeline.py
18 passed
```

No actuator is registered by default and the router chains are untouched, so the
routing/dispatch path is unchanged.

### Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2040 passed, 15 skipped in 57.82s        # +20 vs HS-36 close (new contract/security tests)
$ uv run ruff check holdspeak/plugins/actuators.py holdspeak/plugins/host.py \
    holdspeak/plugin_sdk.py tests/unit/test_actuator_contract.py tests/unit/test_intent_security.py
All checks passed!
$ uv run ruff check --select F821 holdspeak/plugins/host.py
All checks passed!
```

## Notes

- The proposal `payload` is stored verbatim and is the **source of truth** for the
  parity check the guarded executor makes in HS-37-04 — it is never recomputed downstream.
- No persistence/UI/execution here by design — HS-37-02 persists the proposal, HS-37-03
  surfaces it for approval, HS-37-04 executes an approved one under audit.
