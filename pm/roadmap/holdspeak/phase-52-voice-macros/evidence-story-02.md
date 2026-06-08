# Evidence — HS-52-02: Macro model + config

Write-once record of the macro store. Designing the `/commands` board first
(`design-voice-commands-board.md` §10) pinned exactly this schema, no more fields than
the editor shows.

## What shipped

**The model** (`holdspeak/config.py`):
- `VoiceMacroAction`: `kind` in `("open_url", "launch_app", "shell", "type_text")` +
  a single `payload` (the URL / app / command / snippet). `__post_init__` normalizes the
  kind and rejects an unknown kind or an empty payload with `VoiceMacroError`. A
  `preview()` method is the single source of the plain-language "what fires" string
  ("opens ...", "launches ...", "runs: ...", "types: ...") so the card, the editor, and
  any audit read identically (design §10).
- `VoiceMacro`: a `keyword` + a `VoiceMacroAction`. `__post_init__` coerces an action
  dict (from JSON) into a `VoiceMacroAction`, trims the keyword, and rejects an empty one.
  A `matches(transcript)` method does the deterministic whole-utterance match the
  dispatcher (HS-52-04) will use: normalize both sides (case-fold, trim, strip trailing
  `.!?,`) and compare for equality. It selects which macro fires; it never composes one.
- `MacrosConfig`: `enabled: bool = False`, `items: list[VoiceMacro] = []`. Nested on
  `DictationConfig.macros`. `__post_init__` coerces item dicts into `VoiceMacro`s. OFF by
  default.

**Persistence** (`config.py` `Config.load`): a `_coerce(MacrosConfig, macros_data,
section="dictation.macros")` call, so the section loads forward-safe (Phase 50
`config_version`): an older/unversioned config with macros upgrades in place without
dropping other fields. `save()` is unchanged (`asdict` already recurses the new
dataclasses).

**API** (`holdspeak/web/routes/system.py` `PUT /api/settings`): validates the macros
section, returning a clean **400** with a clear message on a malformed macro (bad kind,
empty keyword, non-list items) rather than a 500 or a silently-dropped command. `merged`
carries `current`'s macros as the base, so omitting the section preserves it. `GET`
already returns it via `config.to_dict()`.

## Design decisions

- **Strict `__post_init__` validation** (raises `VoiceMacroError`), matching the existing
  `DictationConfigError` precedent for bad pipeline stages. The realistic path to a bad
  macro is the API, which validates and rejects before persisting, so a corrupt macro
  never reaches disk; a hand-edited corrupt config falls back to defaults on load (logged),
  exactly as a bad pipeline stage does today.
- **One `payload` field**, not a per-kind union, because the board's adaptive editor shows
  exactly one field per kind. Minimal schema, as design §10 demanded.
- `preview()` lives on the model so the "what you see is what fires" string has one home.

## Tests

```
uv run pytest -q tests/unit/test_voice_macros_config.py
-> 15 passed   (off-by-default, each kind + preview, kind normalization, unknown-kind and
   empty-payload rejection, empty-keyword rejection, action-dict coercion, normalized
   whole-utterance match, MacrosConfig item coercion + rejection, save/load round-trip,
   config-version-safe load)

uv run pytest -q tests/integration/test_web_dictation_settings_api.py -k macros
-> 5 passed   (GET off-by-default shape, PUT persists all four kinds, PUT rejects unknown
   kind (400), PUT rejects empty keyword (400), omitting macros preserves them)

uv run pytest -q --ignore=tests/e2e/test_metal.py
-> 2480 passed, 17 skipped   (was 2460; +20 is the new tests, no regressions)
```

0 `_built/` tracked; no UI bundle touched.

## Not done here (by design)

- The connectors that execute an action are HS-52-03; the dispatch that fires on a match
  is HS-52-04; the `/commands` editor is HS-52-05. This story is the data contract they
  build on.
