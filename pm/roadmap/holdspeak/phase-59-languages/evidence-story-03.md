# Evidence — HS-59-03: Docs: languages + the dictionary

**Date:** 2026-06-11
**Branch:** `phase-59-languages`

## 1. What shipped

**`docs/USER_GUIDE.md`** (the home decision: the story draft said "the
typing guide", but punctuation commands have always lived in the User
Guide's voice-typing section, and the canon's rule is extend, don't
fragment — so both features landed there, beside the table they extend):

- **"Speak your language"** (a new subsection before Punctuation): what
  the spoken language setting does, what Auto-detect means, the honest
  short-utterance note ("a few words in one language can be detected as a
  neighboring one; pin your language and transcription stops guessing"),
  and the one-setting-covers-everything statement (dictation, live
  meetings, and imported recordings share the engine).
- **The spoken-symbol dictionary** woven into the Punctuation section
  right after the built-in table: where to add entries, three real
  examples (tilde, arrow, double colon), the user-wins rule, and all four
  attach modes explained with the `std::vector` example.

**`docs/GETTING_STARTED.md`** gains a two-line pointer after its
punctuation table (the minimal-path guide stays minimal).

## 2. The guards

Zero em/en dashes in the new prose (audited per section); canonical names
used ("the spoken-symbol dictionary", "the spoken language setting" — the
rows added to the canon in HS-59-02); the live voice guard (dashes +
AI-vocab + names), the vocab guard, and the link/image locks all green in
the 81-test doc slice.

## 3. Tests

```
$ uv run pytest -q tests/ -k "doc"
81 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2683 passed, 17 skipped
```

(Docs-only; suite unchanged.)
