# HS-52-03 — Local action connectors on the actuator framework

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
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
- [ ] A connector per action kind, built on `build_gated_connector`, each carrying a
      per-macro manifest derived from the configured action.
- [ ] The allowed action runs; an operation that does not match the macro's manifest is
      refused before any side effect (`ConnectorOperationRefused`).
- [ ] With the capability off, no connector executes.
- [ ] Each connector unit-tested with an injected runner/opener (no real side effects in
      CI): allowed-runs, off-manifest-refused, capability-off-blocks.
- [ ] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit with injected `runner` / `opener` (the framework supports test doubles): per-kind
  allowed/refused/blocked (`uv run pytest -q -k "actuator or connector or macro"`).

## Notes / open questions
- `type_text` reusing `typer.py` must not collide with the normal dictation typing; the
  dispatcher (HS-52-04) returns early so only one path types.
- Keep `open_url` / `launch_app` bounded (a single open/launch with the configured target),
  not a general shell. `shell` is the explicit "run my command" kind.
