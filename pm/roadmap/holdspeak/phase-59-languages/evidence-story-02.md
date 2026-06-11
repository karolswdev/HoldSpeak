# Evidence — HS-59-02: The spoken-symbol dictionary

**Date:** 2026-06-11
**Branch:** `phase-59-languages`

## 1. What shipped

- **Config** (`holdspeak/config.py`): `DictationConfig.spoken_symbols`
  (default empty) validated in `__post_init__` via
  `validate_spoken_symbols` — entries `{spoken, symbol, attach}` with
  attach ∈ none/left/right/both (default none), non-empty fields,
  case-insensitive duplicate refusal, every refusal actionable
  (`DictationConfigError`, the route's existing 400 handler). Threaded
  through `Config.load` and the settings route's `DictationConfig`
  construction; `asdict` carries it to `/api/settings` automatically.
- **`TextProcessor(spoken_symbols=…)`**: instance tables copied from the
  pristine class built-ins; user entries merge user-wins (the phrase is
  dropped from every table first, then inserted into its mode's table —
  a user can even move a built-in to another attach mode); the user's
  symbol is replaced via a lambda so it is literal text, never a regex
  template.
- **`web_runtime`** threads `config.dictation.spoken_symbols` into its
  `TextProcessor`.
- **The settings editor** (Voice typing section): add/remove rows
  (spoken phrase, symbol, attach select), the honest hint, an empty-state
  line crediting the built-ins. Screenshot reviewed with three seeded
  entries rendering.
- **POSITIONING.md** gains two canonical-name rows ("the spoken-symbol
  dictionary", "the spoken language setting").

## 2. A real find: per-table ordering broke cross-table phrases

The first cut kept the original five sequential passes and only sorted
longest-first **within** each table. The matrix caught it immediately:
`"std double colon vector"` → `"std double: vector"` — the built-in
`colon` (attach-left table, processed earlier) ate the inside of the
user's `double colon` (attach-both table). `_process_punctuation` is now
**one combined pass sorted longest-first across every table**. The
built-ins never overlapped across tables, so their behavior is unchanged
— proven the strong way: the golden built-in lock AND the entire
pre-existing `test_text_processor.py` (55 tests) pass unmodified against
the restructured pass.

## 3. Tests

`tests/unit/test_spoken_symbols.py` — 17 tests: the byte-identical golden
lock (bare vs. empty-dict instances), the attach-mode matrix (incl. the
literal-symbol guarantee with a `\\g<>` payload), user-overrides-builtin
(class tables un-mutated), mode moves, the cross-table longest-first
cases, and the validation matrix. `tests/integration/
test_settings_spoken_symbols.py` — 3 tests: normalized round-trip, the
clean 400 (and the bad write changing nothing), the editor page locks.

```
$ uv run pytest -q tests/unit/test_spoken_symbols.py tests/unit/test_text_processor.py
72 passed        # 17 new + the 55 existing processor tests, unmodified
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2683 passed, 17 skipped
```

(2663 → 2683.) `npm run build` clean.
