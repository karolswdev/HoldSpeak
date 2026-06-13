# Evidence — HS-64-01: The README catches up

**Date:** 2026-06-13
**Verdict:** done. Every P59–P62 surface is now findable from the front
door, in canon names, and a missed Phase-62 sweep target got fixed.

## The four edits

1. **The two-modes dictation cell** gains the wake word ("listens
   hands-free, with the result previewed, never typed, until you
   confirm" — the honest preview-default framing), the spoken language
   setting ("any of Whisper's 99 languages"), and the spoken-symbol
   dictionary (with the `"double colon"` → `::` example).
2. **The meeting cell** gains Send to Slack as aftercare's outbound door,
   folded into the existing propose/approve/execute sentence so the
   never-acts-without-you truth covers it.
3. **The "Everything is local" pillar** notes the 99 languages in
   passing.
4. **A real find:** the "Meet Qlippy" paragraph still narrated the
   RETIRED Phase-56 "three questions in plain language" pattern — Phase
   62's sweep covered the UI and the image alts but missed this prose.
   Rewritten to the egress-badge posture per the POSITIONING voice rule.

The comparison table was checked and holds (no stale claims; the
trade-offs paragraph still true). Canonical names verified against
POSITIONING; no banned synonyms introduced.

## Proof

- `uv run pytest -q tests/unit/test_doc_drift_guard.py` → 13 passed
  (dashes, AI vocab, banned names, plugin counts, links, images).
