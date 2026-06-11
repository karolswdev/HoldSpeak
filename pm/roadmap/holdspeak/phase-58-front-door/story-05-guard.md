# HS-58-05 — The guard

- **Project:** holdspeak
- **Phase:** 58
- **Status:** done
- **Depends on:** HS-58-02, HS-58-03, HS-58-04
- **Unblocks:** HS-58-06
- **Owner:** unassigned

## Problem
Phase 51 guards vocabulary; nothing guards voice. Without a lock, the next
doc commit reintroduces dashes and AI-isms and the phase decays.

## Scope
- **In:** extend `test_doc_drift_guard.py` over the user-facing corpus
  (README + non-recursive docs/*.md, prose only — fenced code blocks
  exempt): zero em/en dashes; an AI-vocab blocklist (the humanizer's
  high-frequency tells, tuned to zero false positives on the finished
  corpus); canonical-name consistency for names the canon declares
  drift-prone. Proven both ways (seeded violations fail).
- **Out:** guarding internal docs; style rules beyond the canon.

## Acceptance criteria
- [x] The corpus passes; seeded dashes, AI-vocab, and non-canonical names
      are flagged (proven in `test_voice_guard_patterns_catch_seeded_violations`)
      with file:line messages pointing at the canon.
- [x] Code blocks exempt via `_prose_lines`; the verbatim UI quote
      allowlisted; the "not just" pattern narrowed live to the tic forms
      after flagging two legitimate logical uses (no false positives on
      the corpus).
- [x] The rule documented in DOCS_STYLE.md — and the Phase-51 vocab
      pattern widened to catch single-digit phases (the live `HS-9-03`
      find). See `evidence-story-05.md`.

## Test plan
- The new guards both ways + the full doc slice + full suite.
