# HS-58-05 — The guard

- **Project:** holdspeak
- **Phase:** 58
- **Status:** backlog
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
- [ ] The corpus passes; a seeded dash, a seeded "delve", and a seeded
      non-canonical name each fail with actionable messages.
- [ ] Code blocks and legitimate literals are exempt (no false positives).
- [ ] The rule documented in DOCS_STYLE.md (the Phase-51 home).

## Test plan
- The new guards both ways + the full doc slice + full suite.
