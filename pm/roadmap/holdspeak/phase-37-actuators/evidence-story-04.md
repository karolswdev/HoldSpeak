# Evidence — HS-37-04: Guarded executor + audit + governance gate

**Date:** 2026-06-04. **Branch:** `phase-37/hs-37-01-actuator-contract`.

## What shipped

The one place an actuator's side effect happens — so the one place the invariant is
enforced in code. **No external side effect without an approved proposal, the gate on,
payload parity, and an audit entry; egress only through an injected (Phase-25-gated)
connector.**

### Files

- **`holdspeak/plugins/actuator_executor.py` (new)** — `ActuatorExecutor.execute(
  proposal_id, approved_payload_hash=None)`. The guard stack, in order:
  1. **status** — refuses anything not `approved` (`ActuatorExecutionError`); no call.
  2. **policy gate** — `allow_actuators` must be on; if a per-project allow-list is
     supplied, the actuator id must be on it. A refusal raises `ActuatorPolicyError` and
     **changes no state** (operator can enable + retry).
  3. **payload parity (TOCTOU)** — the side effect is built from the proposal's stored
     `payload` (the source of truth); when the approval layer passes the hash it approved
     and it doesn't match `payload_hash(proposal.payload)`, the executor aborts to
     `failed` **with no outbound call**.
  4. **egress** — calls the injected `connector(proposal) -> result`; this module never
     opens a socket (HS-37-05 supplies a connector backed by the connector runtime).
  5. **audit** — `executed` (with the result) or `failed` (with the error) is recorded via
     `ActuatorRepository.transition_proposal`, which writes an audit row carrying the
     payload hash in `detail`.
  A connector exception → `failed` (retryable via `failed → approved`).
- **`holdspeak/config.py`** — the policy gate's home: `MeetingConfig.allow_actuators`
  (master switch, default `False`) + `allowed_actuators` (per-project allow-list, default
  `[]`, validated + normalized like `disabled_plugins`). **Default-safe:** off + empty ⇒
  no external side effect ever runs.

## Verification

### Executor + config — 14 cases

```
$ uv run pytest -q tests/unit/test_actuator_executor.py
14 passed
```

- **Happy path** — approved → `executed`, the connector saw the *stored* payload, result
  recorded, the `executed` transition on the audit trail.
- **Status gate** — `proposed`/`rejected`/`executed` all raise, **no connector call**.
- **Policy gate** — master gate off raises + no call + state stays `approved`; an
  unlisted actuator raises + no call + stays `approved`; a listed actuator executes.
- **Payload parity** — a wrong approved-hash → `failed` (+ audit), **no connector call**;
  the matching hash executes.
- **Connector failure** — a raising connector → `failed` (+ audit), and the proposal is
  retryable (`failed → approved → executed`).
- **Config** — `allow_actuators`/`allowed_actuators` default-safe; allow-list normalized;
  a non-list `allowed_actuators` rejected.

### Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2073 passed, 15 skipped in 57.54s        # +14 (executor + config tests)
$ uv run ruff check holdspeak/plugins/actuator_executor.py holdspeak/config.py
All checks passed!
```

## Notes

- The executor is **connector-agnostic** by design (takes a `connector` callable) — the
  default suite never makes a real outbound call (spy connector). HS-37-05 supplies a
  concrete connector routed through `connector_runtime` (the Phase-25 provider gate).
- Policy/status refusals **raise without changing state** so the proposal can be retried
  once the gate is enabled; parity/connector failures **transition to `failed`** (audited)
  because an execution attempt was made.
- Decision taken (was deferred): **governance granularity** = per-action approval *always*
  (the `approved` status), and the per-project allow-list (`allowed_actuators`) + the
  master switch are *additional* gates — none removes the approval+audit step.
