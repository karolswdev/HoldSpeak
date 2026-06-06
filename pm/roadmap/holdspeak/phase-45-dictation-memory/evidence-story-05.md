# Evidence — HS-45-05: Docs (the dictation journal & its privacy posture)

**Date:** 2026-06-06. **Author:** Claude (Opus 4.8 session).
**Branch:** `phase-45-dictation-memory`.

## What shipped

User-facing documentation for the whole Phase-45 arc, with the privacy posture
first-class (per the standing per-phase docs-story rule).

### `docs/INTELLIGENT_TYPING_GUIDE.md` §12 — "Dictation journal, corrections & replay"

A new section (before "Good First Configuration") covering:

- **Your dictation stays local** — a first-class privacy callout: local-only,
  never uploaded/synced/shared; secret-filtered on write; retention-capped
  (`dictation.journal_retention`, default 500); per-entry delete + Clear journal;
  the `dictation.journal_enabled` toggle (on by default, local) with the
  side-channel guarantee (off ⇒ byte-identical typed output).
- **What is recorded** — a table (transcript · final text · route · target ·
  latency · source · corrected), plus search/filter.
- **The moment of truth** — the in-flow *"Was that right? → Fix it → Taught ✓"*
  loop: it teaches (writes a correction the Memory tab manages) and marks the
  entry corrected; gist-only, secret-filtered, focus-safe.
- **Replay** — ↻ Replay re-runs the stored transcript through the current
  pipeline (dry-run, nothing typed, no new row); the correct → replay → "routing
  changed" payoff; re-insert is preview + copy (never types into the active app).

Three real screenshots from the phase evidence, copied to `docs/assets/journal/`:
`journal-timeline.png`, `moment-of-truth.png`, `replay-before-after.png`.

### Cross-links

- **Root `README.md`** — the "Intelligent dictation" blurb now ends with the
  journal/correct/replay capability + a link to §12; a new quick-link table row
  ("Review, correct, and replay past dictations").
- **`docs/README.md`** (the docs index) — a new bullet under the Intelligent
  Typing Guide linking §12.

## Tests

```
$ uv run pytest -q tests/unit/test_doc_drift_guard.py
3 passed in 0.02s
```

- `test_no_live_doc_claims_a_deterministicplugin_stub` — clean (no stub claims).
- `test_no_live_doc_has_a_dangling_relative_link` — **clean**: the three new
  `assets/journal/*.png` image refs and the cross-link paths all resolve on disk.
- `test_drift_guard_actually_scans_docs` — the guard covers the live docs set.

## Invariants honored (in the prose)

- **Local-first & private** stated explicitly and up front — local-only, never
  uploaded/synced; secret-filter + retention + wipe + toggle; no overstatement
  (no cloud-sync claim; the on-by-default toggle is named alongside its off
  behavior).
- **Side-channel** — the doc states journaling-off ⇒ byte-identical typed output.
- **Focus-safe** — the in-moment fix and replay re-insert are documented as
  never typing into / stealing focus from the active app.
- **Docs only** — no code changed; features shipped in HS-45-01…04.
