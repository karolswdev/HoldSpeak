# HS-37-04 — Guarded executor + audit + governance gate

- **Project:** holdspeak
- **Phase:** 37
- **Status:** done
- **Depends on:** HS-37-03
- **Unblocks:** HS-37-05
- **Owner:** unassigned

## Problem

An approved proposal still must not execute carelessly. This is where the side effect
actually happens — so it's where the invariant is enforced in code: what runs must equal
what was approved, only approved proposals run, every run is audited, and egress goes
through the Phase-25-gated connector surface (no new outbound primitive).

## Scope

- **In:**
  - A **guarded executor** that acts on an `approved` proposal and, before any outbound
    call:
    1. **Payload parity** — re-derive the preview from the stored `payload` and assert it
       equals the approved preview (TOCTOU guard); abort → `failed` on mismatch.
    2. **Policy gate** (RFC open question #5) — an external actuator requires an explicit
       approval (always); a per-project allow-list (`MeetingConfig`) controls *which
       actuator ids* may be proposed/executed at all; `allow_actuators` must be on.
    3. **Egress via the existing surface** — route the side effect through
       `connector_runtime` / `activity_connectors` so it honors the **Phase-25 provider
       gate**; do not add a new egress path.
    4. **Audit** — write an audit-log entry (actor / action / target / payload-hash /
       result / timestamp) for the terminal state (`executed` or `failed`).
  - Transition `approved → executed` on success, `approved → failed` (retryable) on error;
    surface the result/error on the proposal.
- **Out:**
  - The concrete reference actuator + its real connector call (HS-37-05) — here the
    executor is exercised with a **stub/dry-run** connector so the default suite makes no
    real outbound call.
  - Auto-retry/backoff policy (manual retry is enough this phase).

## Acceptance criteria

- [x] Only an `approved` proposal executes; a `proposed`/`rejected`/`executed` proposal
      raises `ActuatorExecutionError` and makes no outbound call.
- [x] **Payload parity** is enforced: a wrong `approved_payload_hash` aborts to `failed`
      (+ audit), no connector call (`payload_hash` = sha256 of canonical payload).
- [x] The **policy gate** holds: `allow_actuators=False` or an actuator id not on the
      allow-list raises `ActuatorPolicyError` with **no state change** (enable + retry);
      the not-approved guard already covers "no approval ⇒ no execution". The gate's home
      is the new `MeetingConfig.allow_actuators` + `allowed_actuators` (default-safe).
- [x] Every terminal transition (`executed`/`failed`) writes an **audit entry** (via
      `transition_proposal`, carrying the payload hash in `detail`); tests assert each.
- [x] Egress routes through an **injected connector** (HS-37-05 supplies the
      Phase-25-gated one; this module never opens a socket); the default suite uses a spy
      connector and makes **no real outbound call**.
- [x] Suite green (2073/15); `actuator_executor.py` + `config.py` ruff + F821 clean.

## Test plan

- Unit: execute an approved proposal (stub connector) → `executed` + audit entry.
- Unit: parity mismatch → `failed`, no connector call (spy).
- Unit: policy gate — gate off / not-allow-listed / unapproved ⇒ no execution.
- Unit: connector error → `failed` (retryable) + audit entry.
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- The audit entry must be written even on the failure path — a terminal proposal with no
  audit row is a stop signal (see the phase risk table).
- Reuse the Phase-25 provider-gate decision point rather than re-checking egress policy
  here; the executor *delegates* the "is this endpoint allowed" question to the connector
  runtime.
- Keep the executor connector-agnostic (it takes a connector handle); HS-37-05 supplies a
  concrete one.
