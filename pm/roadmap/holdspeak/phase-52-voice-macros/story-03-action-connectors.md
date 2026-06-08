# HS-52-03 — Local action connectors on the actuator framework

- **Project:** holdspeak
- **Phase:** 52
- **Status:** done
- **Depends on:** HS-52-02
- **Unblocks:** HS-52-04
- **Owner:** unassigned

## Problem
A macro's action has to actually run, safely. HoldSpeak already has a guarded executor and
a gated-connector framework (Phase 37/38) built for "a pre-approved action that leaves the
safe zone." Build the local action connectors on it instead of reinventing execution.

## Scope
- **In:**
  - New connectors via `build_gated_connector` (`plugins/gated_connector.py:237-290`) for
    the action kinds from HS-52-02:
    - `shell` — `permission: "shell:exec"`, a `GatedOperation.subprocess(argv)`; the
      manifest's `allowed_argv_prefixes` is derived from THIS macro's configured command,
      so the connector permits exactly that command and nothing else.
    - `open_url` / `launch_app` — a local open/launch (macOS `open`, Linux `xdg-open`), a
      bounded subprocess with the URL/app as the argument; manifest derived per macro.
    - `type_text` — types the snippet via `typer.py` (no subprocess); the simplest
      connector, mirror `followup_ticket_actuator.py:118-147` for shape.
  - Reuse `ActuatorProposal` (`plugins/actuators.py:41-133`) and the `plan` / `interpret`
    connector shape unchanged. A `plan(proposal)` turns the macro payload into the
    `GatedOperation`; `interpret(result)` returns a small success/output dict.
  - Nothing executes unless the capability is enabled (the dictation-side enable from
    HS-52-02 plus the executor's `allow_actuators`-style gate). Off, the connectors are
    inert.
- **Out:** the dispatch wiring + auto-approval (HS-52-04); the UI (HS-52-05).

## Acceptance criteria
- [x] A connector per action kind: `open_url` / `launch_app` / `shell` on
      `build_gated_connector` (each with a per-macro manifest derived from the configured
      action), `type_text` as a plain local connector. (`plugins/voice_macro_connector.py`
      `build_voice_macro_connector`)
- [x] The allowed action runs (injected runner); an op that does not match the macro's
      manifest is refused before any side effect.
      (`test_connector_refuses_a_different_command_than_configured` raises
      `ConnectorOperationRefused`, the runner is never reached — the bounded-blast-radius
      property)
- [x] With the capability off, no connector executes.
      (`test_capability_off_blocks_execution_before_the_connector`: real `ActuatorExecutor`
      with `allow_actuators=False` raises `ActuatorPolicyError`, the connector never runs)
- [x] Each connector unit-tested with an injected runner / type_writer (no real side
      effects): allowed-runs per kind, off-manifest-refused, non-zero-exit-raises,
      type_text-types, capability-off-blocks. (`tests/unit/test_voice_macro_connector.py`,
      8 tests)
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit with injected `runner` / `opener` (the framework supports test doubles): per-kind
  allowed/refused/blocked (`uv run pytest -q -k "actuator or connector or macro"`).

## Notes / open questions
- `type_text` reusing `typer.py` must not collide with the normal dictation typing; the
  dispatcher (HS-52-04) returns early so only one path types.
- Keep `open_url` / `launch_app` bounded (a single open/launch with the configured target),
  not a general shell. `shell` is the explicit "run my command" kind.
