# Evidence — HS-58-05: The guard

**Date:** 2026-06-11
**Branch:** `phase-58-front-door`

## 1. What shipped

`tests/unit/test_doc_drift_guard.py` extended with the voice guard (+4
tests, same corpus as the Phase-51 vocabulary guard: root README +
non-recursive `docs/*.md`; fenced code blocks exempt via a shared
`_prose_lines` walker):

- **`test_no_user_facing_doc_uses_dashes_in_prose`** — zero em/en dashes,
  with an explicit `_VERBATIM_UI_QUOTES` allowlist carrying the one
  legitimate survivor (the journal replay note quoted verbatim from
  `journal.js`). The failure message names file:line and points at the
  canon.
- **`test_no_user_facing_doc_uses_ai_vocabulary`** — the humanizer's
  high-frequency tells (delve, seamless, the VERB leverage, supercharge,
  effortless, game-changing, cutting-edge, "is a testament", and the
  negative-parallelism TIC only: "it's not just / isn't just / not
  merely"). Tuned live against the finished corpus: the first cut flagged
  two legitimate logical uses of "not just" ("revocation, not just
  rotation"; "every meeting, not just the visible page") and was narrowed
  to the tic forms — plain logic stays legal.
- **`test_no_user_facing_doc_uses_banned_feature_names`** — the
  POSITIONING.md canonical-name table's drift-prone synonyms ("voice
  macros", "intelligent dictation").
- **`test_voice_guard_patterns_catch_seeded_violations`** — proven both
  ways in one test: each pattern flags seeded violations and spares the
  legal forms ("highest-leverage", "elevated artifact cards", plain
  "not just").

**The Phase-51 pattern widened**: `HS-\\d{2}` → `HS-\\d{1,2}`, closing the
single-digit-phase hole HS-58-03 found live (`HS-9-03` in the Firefox
guide); the narrowness test gains `HS-9-03` in its must-flag list and the
spec-name keeps (`MIR-01`/`DIR-01`/`WFS-01`) still pass.

**`docs/internal/DOCS_STYLE.md`** documents the three rules and the
allowlist procedure (the Phase-51 home for doc-guard rules).

## 2. Tests

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
13 passed
$ uv run pytest -q --ignore=tests/e2e/test_metal.py
2645 passed, 17 skipped
```

(2641 → 2645: the four voice-guard tests.)
