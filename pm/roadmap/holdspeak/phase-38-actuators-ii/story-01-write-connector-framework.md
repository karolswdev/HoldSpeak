# HS-38-01 — Gated write-connector framework + permission manifest

- **Project:** holdspeak
- **Phase:** 38
- **Status:** not-started
- **Depends on:** none (builds on the Phase-37 executor + the connector runtime)
- **Unblocks:** HS-38-02, HS-38-03, HS-38-04
- **Owner:** unassigned

## Problem

Phase 37's `ActuatorExecutor` calls an injected `connector(proposal) -> dict`, but the only
built-in connector pack (`github_cli`) is **read-only by Phase-25 policy**. To do real
writes safely we need a contract for *write* connectors: each declares exactly what it may
do (a per-connector **permission manifest**), and every outbound call routes through the
existing `PermissionGate`, so a connector can never egress beyond what it declared.

## Scope

- **In:**
  - A **write-connector permission manifest** — the narrow allow-list for one connector:
    the `PermissionGate` permission it needs (`shell:exec` / `network:outbound`) + the
    concrete operations it may perform (e.g. permitted `gh` argv prefixes; allow-listed
    webhook hosts). Mirror `connector_sdk.ConnectorManifest` (`permissions` /
    `requires_network`) + the `github_cli` `is_command_allowed` allow-check pattern.
  - A **`build_gated_connector(...)`** helper that wraps a side-effect builder in (1) the
    manifest allow-check (refuse anything not declared, **before** egress) and (2) the
    `PermissionGate` operation (`run_subprocess` / `open_outbound_socket`), and returns the
    `connector(ActuatorProposal) -> dict` the `ActuatorExecutor` expects. A refused op
    raises (the executor records it as `failed` + audit) and performs **no** egress.
  - Keep the `ActuatorExecutor` (status + policy + parity + audit) **unchanged** — this
    story only produces gated `connector` callables for it.
- **Out:**
  - The concrete GitHub / webhook connectors (HS-38-02 / HS-38-03) — a fake connector +
    fake gate are enough here.
  - Live proposals (HS-38-04).

## Acceptance criteria

- [ ] A connector declares a permission manifest (permission token + a concrete op
      allow-list); `build_gated_connector` produces an executor-shaped `connector`.
- [ ] An operation the manifest **does not** admit is refused **before** any egress (the
      `PermissionGate` op is never reached); asserted with a fake gate/runner spy.
- [ ] A permitted op routes through `PermissionGate` (`run_subprocess` /
      `open_outbound_socket`) and returns a result dict; the executor records `executed`.
- [ ] The default suite makes **no real outbound call** (fake gate/runner injected).
- [ ] Suite green; new module ruff + F821 clean.

## Test plan

- Unit: manifest allow-check (permitted vs refused op); `build_gated_connector` happy path
  (gate invoked, result returned) + refusal path (gate **not** invoked, raises).
- Unit (integration with Phase 37): the gated connector driven through
  `ActuatorExecutor.execute` → `executed` on permit, `failed` (no egress) on refuse.
- Suite: `uv run pytest -q --ignore=tests/e2e/test_metal.py` green.

## Notes / open questions

- The manifest is the *narrowest* gate — it layers under the existing approval + policy +
  parity gates, never replacing them. A connector with no permitted ops does nothing.
- Reuse `connector_runtime.PermissionGate`; do not add a second egress primitive.
- Decision (deferred to HS-38-03): webhook host allow-listing granularity (fixed config
  host vs per-proposal host vetted against an allow-list).
