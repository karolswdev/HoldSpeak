# Evidence — HS-52-04: Dispatch wiring (match -> fire, type nothing)

Write-once record of the wiring that turns the parts into a working feature: speak a
configured keyword, the action fires and nothing is typed; speak anything else, you
dictate as normal.

## What shipped

`holdspeak/dictation_runner.py`:
- `dispatch_voice_command(text, *, config, runner=None, type_writer=None, platform=None,
  on_activity=None) -> VoiceCommandResult | None`, the dispatch decision at the top of
  the carved seam. Off by default (macros disabled -> `None`), deterministic
  whole-utterance match (`VoiceMacro.matches`), and on a match it fires through the
  bounded connector (HS-52-03), surfaces "command: <keyword>" via `on_activity`, and
  returns a `VoiceCommandResult` (handled, ok/error). A configured macro is auto-fired:
  the config is the consent, so there is no per-fire prompt.

`holdspeak/web_runtime.py`:
- `_maybe_dispatch_voice_command(text, agent_reply_session)` is the thin delegate: it
  injects the runtime typer (so a `type_text` macro types via `typer.type_text`) and a
  runtime-activity callback, then calls `dispatch_voice_command`.
- In `_transcribe_and_type`, right after text processing and **before** the dictation
  pipeline, a match returns early: on success a "Command" complete activity + first-run
  mark, on failure an error activity, and in both cases **nothing is typed**. No match
  falls straight through to the unchanged pipeline.

## The non-meeting persistence resolution (the wrinkle the brief flagged)

The brief planned to record the fire through `record_proposal -> transition_proposal ->
ActuatorExecutor.execute`. The schema makes that impractical for a voice fire:
`actuator_proposals.meeting_id TEXT NOT NULL REFERENCES meetings(id)` (db/core.py:408).
A voice command has no meeting, so persisting there would need either a fake/synthetic
`meetings` row (pollutes `/history`, semantically wrong) or a schema change (a
`SCHEMA_VERSION` bump, which Phase 50 made a deliberate, guarded affair) — both out of
proportion for this story.

Resolution: **reuse the guarded execution, not the meeting-scoped persistence.** The
fire goes through the HS-52-03 connector, which is built on `build_gated_connector` +
`WriteConnectorManifest` + `PermissionGate` — so the security-relevant part (the bounded
per-macro manifest + the egress gate) is fully reused. The audit is the runtime-activity
broadcast + the log, not the meeting table. A persistent, non-meeting fire log can be a
later story if it earns its keep; it is recorded as deferred here, not hand-waved.

## Byte-identical when off

`dispatch_voice_command` returns `None` immediately when macros are disabled (the
default) or nothing matches, so `_transcribe_and_type` proceeds exactly as before. The
full suite's existing dictation transcription tests pass unchanged, which is the proof.

## Tests

```
uv run pytest -q tests/unit/test_voice_command_dispatch.py
-> 7 passed   (macros-off -> None; no-match -> None; shell fires the bounded argv;
   type_text types via the injected writer; "command: <keyword>" activity on match;
   a failed command is handled (not typed) with the error; the WebRuntime delegate
   injects the typer + activity and routes type_writer to the runtime typer)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2495 passed, 17 skipped   (was 2488; +7 is the new tests, no regressions — the
   existing transcription tests proving the off path is byte-identical)
```

0 `_built/` tracked; no UI bundle touched.

## Not done here (by design)

- The `/commands` board that creates and tests macros is HS-52-05 (the centerpiece).
- A persistent per-fire audit log (deferred; the actuator table is meeting-scoped).
