# HS-52-02 — Macro model + config (keyword -> action; `/api/settings`)

- **Project:** holdspeak
- **Phase:** 52
- **Status:** done
- **Depends on:** HS-52-01
- **Unblocks:** HS-52-03, HS-52-04, HS-52-05
- **Owner:** unassigned

## Problem
There is nowhere to store voice command macros. The config needs a macro section that
loads/saves safely (Phase 50 made config forward-compatible) and round-trips through the
settings API, so the connectors (HS-52-03), the dispatcher (HS-52-04), and the editor UI
(HS-52-05) have a contract to build on.

## Scope
- **In:**
  - A `VoiceMacro` model: a `keyword` (the exact spoken phrase to match) and an `action`
    with a `kind` in {`open_url`, `launch_app`, `shell`, `type_text`} plus the kind's
    payload (a URL, an app/path, an argv/command string, the snippet text). Keep it data.
  - A `MacrosConfig` dataclass nested under `DictationConfig` in `holdspeak/config.py`
    (~`:323-399`): `enabled: bool = False`, `items: list[VoiceMacro] = []`. Unpack in
    `Config.load()` (`:456-466`) through `_coerce()` (`:24-42`) so unknown keys drop and
    a stale/newer config does not break (Phase 50 `config_version`).
  - Read/write through `/api/settings` (`web/routes/system.py:442` GET, `:461` PUT) with
    validation: a macro with an unknown kind or an empty keyword is rejected with a clear
    error, not silently dropped.
- **Out:** the connectors (HS-52-03); the dispatcher (HS-52-04); the editor UI (HS-52-05).

## Acceptance criteria
- [x] `VoiceMacro` + `MacrosConfig` exist; `enabled` defaults `False`, `items` empty.
      (`config.py`: `VoiceMacroAction` / `VoiceMacro` / `MacrosConfig` on
      `DictationConfig.macros`)
- [x] Config load/save round-trips a macros section; an older/unversioned config loads
      without dropping other fields. (`_coerce(MacrosConfig, ...)` in `Config.load`;
      round-trip + version-safe unit tests)
- [x] `GET /api/settings` returns the macros section; `PUT` validates + persists it; a
      malformed macro is rejected with a clear error (400). (`system.py`;
      `TestVoiceMacrosSettingsApi`)
- [x] A unit test pins round-trip, the action-kind validation, the normalized
      whole-utterance match, the preview strings, and off-by-default.
      (`tests/unit/test_voice_macros_config.py`, 15 tests)
- [x] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit: config round-trip + default shape + kind validation; settings API read/write
  (`uv run pytest -q -k "config or settings"`).

## Notes / open questions
- The `action` shape is the contract HS-52-03 turns into a connector operation and
  HS-52-04 turns into an `ActuatorProposal` payload. Keep it minimal and explicit.
- Keyword normalization (case, trailing punctuation) is defined in HS-52-04's matcher;
  here just store the keyword as the user typed it.
