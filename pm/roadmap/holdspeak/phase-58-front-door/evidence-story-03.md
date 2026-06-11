# Evidence — HS-58-03: The core guides

**Date:** 2026-06-11
**Branch:** `phase-58-front-door`

## 1. What shipped

The eight user-flow guides, revised against the canon:

- **Why-ledes.** GETTING_STARTED now opens with the five-minutes-to-first-
  dictation promise and why voice typing is the foundation; the typing
  guide opens with the say-vs-meant gap the dictation pipeline crosses;
  MEETING_MODE_GUIDE opens with "a meeting should end with decisions,
  owners, and follow-ups, not a recording"; DICTATION_COPILOT reframes
  transcription-vs-intent; FIREFOX_EXTENSION_GUIDE explains why the
  companion exists (pre-briefing is only as good as the activity it can
  see); USER_GUIDE's lede now carries the two-modes frame with canonical
  names (Dictate / Meet, "the dictation pipeline", "the dictation
  journal", "meeting aftercare"). VOICE_COMMANDS and ACTIVITY_PREBRIEFING
  already opened to standard (recent docs) and were left alone.
- **The dash cleanup.** Per-file em/en dashes, before → after:
  GETTING_STARTED 8→0, INTELLIGENT_TYPING_GUIDE 28→1, MEETING_MODE_GUIDE
  13→0, DICTATION_COPILOT 15→0, FIREFOX_EXTENSION_GUIDE 6→0 (USER_GUIDE,
  VOICE_COMMANDS, ACTIVITY_PREBRIEFING were already 0). Every replacement
  hand-chosen (period / comma / colon / parentheses / restructure), never
  mechanical. Numeric ranges normalized (4-9B, ① through ④).
- **The one surviving dash is deliberate**: the typing guide quotes the
  journal replay UI verbatim ("Preview only — nothing was typed", the
  string `journal.js` really renders) and quoted UI strings are exempt
  per the canon. One was caught the other way: my first pass edited that
  quote, the grep against `web/src` caught the desync, and the verbatim
  quote was restored. The HS-58-05 guard will allowlist it explicitly.
- **Canonical names**: "intelligent typing"-as-feature-name replaced by
  "the dictation pipeline" in prose (doc titles kept; they are document
  names, not feature names).

## 2. A real find: a vocab leak the Phase-51 guard misses

`FIREFOX_EXTENSION_GUIDE.md` opened with "HS-9-03." — roadmap vocabulary
in a user-facing doc. It survived Phase 51 because the guard's pattern
expects two-digit story numbers and `HS-9-03` has a single-digit phase.
The leak is fixed here (the lede now explains the extension's why
instead); widening the guard pattern lands with HS-58-05.

## 3. Tests

```
$ uv run pytest -q tests/ -k "doc"
77 passed, 2 skipped
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2641 passed, 17 skipped
```

(Docs-only; suite unchanged. Vocab, link, image, and Qlippy locks green
over all eight revisions; no pinned phrase was altered.)
