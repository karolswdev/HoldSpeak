# HS-48-04 — Docs: the learning loop, end to end

- **Project:** holdspeak
- **Phase:** 48
- **Status:** backlog
- **Depends on:** HS-48-01, HS-48-02, HS-48-03
- **Owner:** unassigned

## Problem
The learning loop (record → correct → learn → see what it learned → replay) is the
product's headline open-source story, but the docs describe its pieces separately
(the journal, corrections, replay) without telling it as one loop, and the new
digest + trust signals + ritual are undocumented. Per the standing rule, every
phase gets its own dedicated docs story; this is it.

## Scope
- **In:**
  - Document the **full loop** in the Intelligent Typing guide (and/or the Dictation
    Copilot doc): dictate → "that was wrong" in one tap → HoldSpeak learns → "What
    HoldSpeak learned" digest shows it (with the honest "N similar" count) → replay
    proves it. One narrative, accurate to the shipped UI.
  - Update the **README / docs index** hook so the learning loop reads as a
    first-class, demoable, local-first differentiator (the open-source pitch:
    "it gets better at your voice, on your machine, and shows you the proof").
  - Keep the `DOCS_STYLE.md` terms consistent; ground every claim in live code.
- **Out:** new feature work (HS-48-01..03). Documentation + framing only.

## Acceptance criteria
- [ ] The guide documents the learning loop as one coherent flow, matching the
      shipped UI (digest, inline counts, one-tap correction, replay); no over-claim.
- [ ] README/index hooks present the loop as a headline local-first differentiator;
      terms consistent with `DOCS_STYLE.md`.
- [ ] Doc-drift + dangling-link/image-ref guards green; claims grounded in
      `journal.py` / `corrections.py` / the digest endpoint.

## Test plan
- `uv run pytest -q -k "doc_drift or link or doc_guard"`.
- Manual: read the loop section top to bottom; a newcomer understands that
  correcting teaches the tool and where to see the proof.

## Notes / open questions
- Honesty bar: the learning is real but bounded (Jaccard token overlap, local,
  off-by-default until `corrections_enabled`). Say so; do not imply a model that
  silently retrains.
- Add a real screenshot of the digest (mirror `scripts/screenshot_*.py`).
