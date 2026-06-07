# HS-49-05 — Docs: meeting aftercare, end to end

- **Project:** holdspeak
- **Phase:** 49
- **Status:** backlog
- **Depends on:** HS-49-01, HS-49-02, HS-49-03, HS-49-04
- **Owner:** unassigned

## Problem
Meeting aftercare (what's open / decided / changed -> jump to the moment -> accept
-> file an issue / draft the follow-up) is the new follow-through story, but the
docs describe meeting capture + artifacts without telling the loop-closing flow.
Per the standing rule, every phase gets its own dedicated docs story; this is it.

## Scope
- **In:**
  - Document the **aftercare flow** end to end in the Meeting Mode guide: review a
    meeting -> see what's still open / what was decided / what changed since last
    time -> jump to the transcript moment -> accept an action -> file it as an
    issue (human-approved, off by default) or draft the follow-up (preview + copy).
    One narrative, accurate to the shipped UI.
  - Update the **README / docs index** hook so meeting aftercare reads as
    "close the loop" follow-through, complementing the dictation learning loop.
  - Honesty: actuators are off by default + human-approved + audited; drafts are
    preview-only; diffs/provenance are real. Say so; ground every claim in code.
- **Out:** new feature work (HS-49-01..04). Documentation + framing only.

## Acceptance criteria
- [ ] The Meeting Mode guide documents aftercare as one coherent flow matching the
      shipped UI (open/decided/changed, the moment jump, accept -> issue, follow-up
      draft); no over-claim (off-by-default actuators, preview-only drafts).
- [ ] README/index hooks present aftercare as the meeting-side "close the loop"
      follow-through; terms consistent with `DOCS_STYLE.md`.
- [ ] Doc-drift + dangling-link/image-ref guards green; claims grounded in
      `meetings.py` / `actuators.py` / the aftercare endpoint; a real screenshot
      added (mirror `scripts/screenshot_*.py`).

## Test plan
- `uv run pytest -q -k "doc_drift or link or doc_guard or doc"`.
- Manual: read the aftercare section top to bottom; a newcomer understands how a
  meeting result becomes their next action, and what stays human-approved/local.

## Notes / open questions
- Voice: no em or en dashes, no rule-of-three padding, no "not X but Y" (the
  humanizer rule); plain and direct.
- Reuse the Phase-48 docs pattern (a numbered end-to-end flow + screenshots + an
  honest limits note).
