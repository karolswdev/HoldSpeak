# HS-52-02 — Macro model + config (config-version-safe, `/api/settings`)

- **Project:** holdspeak
- **Phase:** 52
- **Status:** not started
- **Depends on:** HS-52-01
- **Unblocks:** HS-52-03, HS-52-04
- **Owner:** unassigned

## Problem
There is nowhere to store voice macros. The dictation config needs a macro section that
loads and saves safely (Phase 50 made config forward-compatible) and round-trips through
the settings API, so the matcher (HS-52-03) and the editor UI (HS-52-04) have a contract
to build on.

## Scope
- **In:**
  - A `VoiceMacro` model: a `phrase` (the exact spoken command to match) and a
    deterministic `action` (a typed/structured value the matcher resolves, e.g. an
    action kind plus payload). Keep it data, not code.
  - A `MacrosConfig` dataclass nested under `DictationConfig` in `holdspeak/config.py`
    (~`:323-399`): `enabled: bool = False`, `items: list[VoiceMacro] = []`. Unpack it in
    `Config.load()` (`:456-466`) through the existing `_coerce()` (`:24-42`) so unknown
    keys are dropped and a stale/newer config does not break (Phase 50
    `config_version`).
  - Read/write through `/api/settings` (`holdspeak/web/routes/system.py:442` GET, `:461`
    PUT): the macros section is returned and persisted with validation.
- **Out:** the matcher (HS-52-03); the editor UI (HS-52-04).

## Acceptance criteria
- [ ] `VoiceMacro` + `MacrosConfig` exist; `MacrosConfig.enabled` defaults `False`,
      `items` defaults empty.
- [ ] Config load/save round-trips a macros section; an older/unversioned config loads
      without dropping other fields (config-version-safe).
- [ ] `GET /api/settings` returns the macros section; `PUT /api/settings` validates and
      persists it; a malformed macro is rejected with a clear error, not silently
      dropped.
- [ ] A unit test pins the round-trip and the off-by-default shape.
- [ ] `npm run build` n/a; 0 `_built/` tracked.

## Test plan
- Unit: config round-trip + default shape; settings API read/write
  (`uv run pytest -q -k "config or settings"`).

## Notes / open questions
- Decide the `action` representation in this story (an action `kind` enum + optional
  payload reads cleanest). HS-52-03 consumes it; keep it minimal and deterministic.
- Validation lives with the API merge path (`system.py:461`), mirroring the other
  config sections.
