# Evidence — HS-52-03: Local action connectors on the actuator framework

Write-once record of the connectors. Reuse, not reinvention: the egress kinds run
through the existing Phase-38 gated-connector framework unchanged; only the local
connectors + the per-macro manifest derivation are new.

## What shipped

`holdspeak/plugins/voice_macro_connector.py`:
- `build_voice_macro_connector(action, *, runner=None, type_writer=None, platform=None)`
  returns the `connector(proposal) -> dict` the `ActuatorExecutor` injects.
- **Egress kinds** (`open_url`, `launch_app`, `shell`) are built with
  `build_gated_connector` + a per-macro `WriteConnectorManifest` (`shell:exec`):
  - `open_url`   -> `open <url>` (macOS) / `xdg-open <url>` (Linux)
  - `launch_app` -> `open -a <app>` (macOS) / `<app>` (Linux)
  - `shell`      -> `sh -c <command>`
  - The manifest's `allowed_argv_prefixes` is `(argv,)` for that macro's own command, so
    the executor admits exactly that op and refuses anything else before egress.
- **`type_text`** is a plain local connector (typing is not egress) that types via an
  injected `type_writer` (the dispatcher passes the runtime typer in HS-52-04; the default
  lazily builds a `TextTyper`).
- Helpers `voice_macro_argv()` / `voice_macro_manifest()` are the single source of the
  per-kind argv + manifest. `_plan` rebuilds the op from the proposal's stored payload
  (`{"kind", "payload"}`); `_interpret` returns `{argv, returncode, stdout, stderr}` and
  raises on a non-zero exit (-> the proposal becomes `failed`, audited), mirroring the
  `github_issue` reference connector.

Nothing was changed in the actuator framework: `ActuatorProposal`, `ActuatorExecutor`,
`build_gated_connector`, `WriteConnectorManifest`, and `PermissionGate` are reused as-is.

## The safety property, tested

- **Bounded blast radius.** `test_connector_refuses_a_different_command_than_configured`:
  a connector built for `echo hi` is handed a proposal carrying `rm -rf /`; it raises
  `ConnectorOperationRefused` and the injected runner is never reached. A mishearing fires
  the wrong configured macro; it can never compose a new command, and even a tampered
  payload cannot run anything off the macro's manifest.
- **Off by default.** `test_capability_off_blocks_execution_before_the_connector`: a real
  `ActuatorExecutor` with `allow_actuators=False` raises `ActuatorPolicyError` before the
  connector runs. The capability is the informed opt-in.

## Tests

```
uv run pytest -q tests/unit/test_voice_macro_connector.py
-> 8 passed   (argv per kind macOS/Linux; each egress kind runs its bounded argv via an
   injected runner; off-manifest refused before the runner; non-zero exit raises;
   type_text types via the injected writer; capability-off blocks before the connector)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2488 passed, 17 skipped   (was 2480; +8 is the new tests, no regressions)
```

0 `_built/` tracked; no UI bundle touched.

## Not done here (by design)

- The dispatch (match keyword -> build proposal -> record + auto-approve + execute) is
  HS-52-04, which injects the runtime typer for `type_text` and resolves the non-meeting
  actuator persistence context. This story delivers the connectors it will fire.
