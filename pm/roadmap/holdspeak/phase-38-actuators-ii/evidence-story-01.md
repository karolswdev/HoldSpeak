# Evidence — HS-38-01: Gated write-connector framework + permission manifest

**Date:** 2026-06-04. **Branch:** `phase-38/hs-38-01-write-connector-framework`.

## What shipped

The safety seam every Phase-38 write connector depends on: a **per-connector
permission manifest** plus a `build_gated_connector(...)` helper that turns a side-effect
*plan* into the `connector(proposal) -> dict` the Phase-37 `ActuatorExecutor` injects. The
manifest is the **narrowest** gate — it layers *under* the executor's existing approval +
policy + payload-parity gates, never replacing them, and can only ever *narrow* what
reaches the wire.

### Files

- **`holdspeak/plugins/gated_connector.py` (new)** —
  - **`WriteConnectorManifest`** — declares exactly one egress permission (`shell:exec`
    **or** `network:outbound`; anything else is rejected in `__post_init__`) plus the
    concrete operations it admits: `allowed_argv_prefixes` for CLI, `allowed_hosts` for
    outbound. `allows(op)` is the allow-check (argv-prefix match — generalizing
    `github_cli.is_command_allowed` to arbitrary-length prefixes from `argv[0]`; or
    case-insensitive host membership). An **empty allow-list admits nothing** — the
    connector then does nothing, the safe default. `build_gate()` synthesizes a minimal
    `ConnectorManifest` carrying the one permission and wraps it in the existing
    `connector_runtime.PermissionGate` (no second egress primitive introduced).
  - **`GatedOperation`** — one concrete planned side effect: `.subprocess(argv, **kwargs)`
    or `.outbound(host, port, request=…)`; `summary()` for refusal/audit text.
  - **`build_gated_connector(manifest, *, plan, interpret, gate=…, runner=…, opener=…)`** —
    per proposal, in order: **plan → allow-check → gate → interpret**. The allow-check runs
    **before** the gate: a refused op raises `ConnectorOperationRefused` and reaches no
    egress. An admitted op routes through `PermissionGate.run_subprocess` /
    `open_outbound_socket` (the gate's opener closure carries the full op so the connector's
    HTTP opener can send `op.request`); the gate still enforces the permission token.
  - **`ConnectorOperationRefused`** — operator-readable; the executor catches it like any
    connector failure (→ `failed` + audit, no side effect).
- **`tests/unit/test_gated_connector.py` (new)** — 12 tests (below).

### The safety posture (HS-38-01 slice)

- The manifest **only narrows**: a connector can never perform an op it didn't declare.
  The allow-check is consulted *before* `PermissionGate`, so a refusal never touches egress.
- `PermissionGate` is reused, not replaced — the synthesized gate genuinely enforces the
  permission (a gate built without `shell:exec` raises `PermissionDenied` even for an op the
  manifest would admit; asserted).
- The `ActuatorExecutor` (status + policy + parity + audit) is **unchanged** — this story
  only produces gated `connector` callables for it. Nothing is registered, so routing /
  dispatch stay byte-identical and actuators stay off by default.
- The default suite makes **no real outbound call** — `runner` / `opener` / a spy gate are
  injected throughout; the concrete `gh` / webhook connectors are HS-38-02 / HS-38-03.

## Verification

### Targeted — framework + executor integration

```
$ uv run pytest -q tests/unit/test_gated_connector.py
12 passed in 0.40s
```

- **Manifest validation** — a non-write permission is rejected; `operation` maps the
  permission token to its gate op.
- **Allow-check** — CLI admits only the declared argv prefix (refuses sibling verbs, other
  binaries, kind-mismatched outbound ops); webhook admits only the listed host
  (case-insensitive, refuses off-list hosts + kind-mismatched subprocess ops); an empty
  allow-list admits nothing.
- **Permit path** — a permitted subprocess routes through a real gate to a fake runner and
  returns the interpreted dict; a permitted outbound routes through the gate to a fake
  opener that receives the full op (incl. `request`).
- **Refuse path** — a refused subprocess / outbound raises `ConnectorOperationRefused`
  with the gate (a spy) and runner/opener **never reached** (no egress).
- **Gate layer is real** — a gate built from a manifest *without* `shell:exec` raises
  `PermissionDenied` for an otherwise-permitted op.
- **`ActuatorExecutor` integration** — a permitted gated connector drives an approved
  proposal to `executed` (runner called once, audit ends `executed`); a refused op drives
  it to `failed` with **no egress** (spy/runner untouched, `error` names
  `ConnectorOperationRefused`, audit ends `failed`, and `failed → approved` retry is legal).

### Full suite + lint

```
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2092 passed, 15 skipped in 59.52s        # +12 vs HS-37 close (the new framework tests)
$ uv run ruff check holdspeak/plugins/gated_connector.py tests/unit/test_gated_connector.py
All checks passed!
$ uv run ruff check --select F821 holdspeak/plugins/gated_connector.py
All checks passed!
```

## Notes

- The deferred decision on **webhook host allow-listing granularity** (fixed config host vs
  per-proposal host vetted against an allow-list) is settled at the framework level in favor
  of an **allow-list of hosts** the proposal's target host must be a member of — `plan`
  derives the host from the payload, `allowed_hosts` vets it. HS-38-03 supplies the concrete
  webhook connector + the config wiring.
- `build_gated_connector` is **not registered anywhere** — like the Phase-37 reference, it
  is a host-side seam the executor injects, kept out of `register_builtin_plugins`, so the
  default plugin set + routing chains are byte-identical.
