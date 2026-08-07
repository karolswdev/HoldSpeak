# HS-117-11 — The backend errors

- **Project:** holdspeak
- **Phase:** 117
- **Status:** done
- **Depends on:** ---
- **Unblocks:** HS-117-12
- **Owner:** unassigned

## The thesis (the bar)

The Python backend defines 30+ custom exception classes scattered
across 15 modules with no shared base, no error codes, and no
consistent hierarchy. Most inherit directly from `RuntimeError` or
`ValueError`. Two `DiscoveryError` classes (in
`connector_pack_loader.py` and `plugin_pack_loader.py`) are not even
`Exception` subclasses -- they are plain objects used as error
envelopes. The web API layer has no uniform way to translate domain
errors into HTTP responses.

When this story ships, a `holdspeak/errors.py` module defines a
`HoldSpeakError` base class with an error code. Every existing
exception inherits from it (or a domain-specific subclass). The
two `DiscoveryError` plain classes become proper exceptions. The API
layer maps `HoldSpeakError` subclasses to structured JSON responses.

**Articles served:** VI (honest construction -- exceptions that are
not `Exception` subclasses are lies), X (sustainability -- a unified
hierarchy means one `except HoldSpeakError` catches everything
domain-specific).

## Deliverables

### 1. Create `holdspeak/errors.py` with the base hierarchy

Define `HoldSpeakError(Exception)` with a `code: str` class
attribute and an optional `code` keyword in `__init__`. Six domain
subclasses: `ConfigError` (`CONFIG_ERROR`), `AudioError`
(`AUDIO_ERROR`), `TranscriptionError` (`TRANSCRIPTION_ERROR`),
`DatabaseError` (`DATABASE_ERROR`), `PluginError` (`PLUGIN_ERROR`),
`AgentError` (`AGENT_ERROR`).

### 2. Migrate existing exceptions (30+ classes)

Re-parent each existing exception to the appropriate base:

- `DictationConfigError`, `VoiceMacroError` (config.py) ->
  inherit `ConfigError`.
- `AudioRecorderError` (audio.py), `RemoteAudioRecorderError`,
  `DeviceRegistryError`, `DuplicateLabelError`, `HandshakeError`,
  `InvalidHandshakeError` (device_audio.py) -> inherit `AudioError`.
- `TranscriberError`, `TranscriberTimeoutError` (transcribe.py),
  `TranscriptParseError` (transcript_parse.py) ->
  inherit `TranscriptionError`.
- `SchemaVersionError` (db/core.py),
  `DecisionTransitionRefused` (db/decisions.py) ->
  inherit `DatabaseError`.
- `DiscoveryError` in `connector_pack_loader.py` and
  `plugin_pack_loader.py` -> make proper `Exception` subclasses
  inheriting `PluginError`. Preserve their data fields.
- `CapabilityError`, `UnknownAdapterError`,
  `CapabilityUnavailableError` (agent_capabilities.py) ->
  inherit `AgentError`.
- `ProductLanguageError`, `ProductLanguageException`
  (product_language.py) -> consolidate into one class inheriting
  `HoldSpeakError`. Alias the old name for backwards compatibility.
- `MeetingRecorderError` (meeting_recorder.py),
  `MeetingImportError` (meeting_import.py) -> inherit
  `HoldSpeakError` directly.
- `TmuxTransportError` (tmux_transport.py),
  `DesktopEffectWarrantRequired` (typer.py) -> inherit
  `HoldSpeakError` directly.
- `FaultInjected` (faults.py) -> inherit `HoldSpeakError`
  (it is a testing concern but should still be catchable).
- `FloorHeldError` (audio floor) -> inherit `AudioError`.

Keep each exception defined in its original module. Change only
the base class and add a `code` class attribute.

### 3. Add error-to-response mapping

Add to `holdspeak/errors.py`:

```python
def error_response(e: HoldSpeakError) -> dict:
    return {"error": e.code, "message": str(e)}
```

Wire into the web API error handler so `HoldSpeakError` subclasses
produce `{"error": "AUDIO_ERROR", "message": "..."}` responses
instead of raw 500s.

## What NOT to do

- Do NOT change error-handling logic at call sites. Only the
  exception base class and `code` attribute change.
- Do NOT remove any existing exception class. Every `except
  FooError` in the codebase must keep working.
- Do NOT add error codes to non-HoldSpeak exceptions (stdlib,
  third-party). Only domain errors get the hierarchy.
- Do NOT touch the database schema or models. That is HS-117-10.

## Test plan

1. `uv run pytest -q` -- all backend tests pass.
2. Verify every custom exception inherits `HoldSpeakError`:
   `grep -rn "class.*Error.*Exception\|class.*Error.*RuntimeError\|class.*Error.*ValueError" holdspeak/ | grep -v HoldSpeakError`
   returns zero hits (excluding stdlib re-raises).
3. Verify the `DiscoveryError` classes are proper exceptions:
   `uv run python -c "from holdspeak.connector_pack_loader import
   DiscoveryError; assert issubclass(DiscoveryError, Exception)"`.
4. Verify error codes exist:
   `uv run python -c "from holdspeak.errors import AudioError;
   assert AudioError.code == 'AUDIO_ERROR'"`.
5. `npx tsc --noEmit` -- frontend unaffected.

## Estimated scope

~80 lines added (`holdspeak/errors.py`). ~30 lines changed across
~15 modules (base class swaps). Net: ~110 lines added. 1 new file,
~15 files touched.
