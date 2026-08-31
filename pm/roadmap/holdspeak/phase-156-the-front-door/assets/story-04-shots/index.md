# HS-156-04 shot sheet — the door surface

Reviewer: ______________ Verdict: ______________ Date: ______________

## Cards (unconfigured desk)

| Shot | Width | What to look for |
|------|-------|-----------------|
| door-cards-1440.png | 1440 | Three pack cards (Light, Balanced, Full); each shows all 7 group lines + speech + TTS; download sizes; Balanced has RECOMMENDED badge; "Set up my own" below |
| door-cards-393.png | 393 | Same content at mobile width; no horizontal overflow; cards stack cleanly |
| door-cards-focus-1440.png | 1440 | Keyboard focus visible after Tab presses; all three packs fully visible with scrolling; "SET UP" confirm button at bottom |
| door-cards-focus-393.png | 393 | Keyboard focus at mobile width |

## Strip + fold (configured desk)

| Shot | Width | What to look for |
|------|-------|-----------------|
| door-strip-1440.png | 1440 | ActionNotice strip with attention state naming ONE action (FIX button); "Advanced" disclosure trigger below |
| door-strip-393.png | 393 | Strip renders at mobile width; FIX button accessible |
| door-fold-open-1440.png | 1440 | Advanced fold open: full Model Library (12 models, tabs, detail panel) + Assignments visible; zero features removed |
| door-fold-open-393.png | 393 | Advanced fold at mobile width; Library stacks correctly |

## Strip configured (separate test leg)

| Shot | Width | What to look for |
|------|-------|-----------------|
| strip-initial-1440.png | 1440 | Health strip with attention notice and FIX button |
| strip-initial-393.png | 393 | Strip at mobile width |
| strip-fold-open-1440.png | 1440 | Advanced fold fully open showing Library + Assignments |
| strip-fold-open-393.png | 393 | Fold at mobile width |

## Notes

- The attention state (e.g. "Thoughts & notes Fix") comes from the real assignment
  summary: the seeded profile has limited claims, so some groups show attention.
  Story 05 (the jargon purge) will refine wording.
- "Needs attention" inside the Library is the Library's own summary (untouched
  advanced layer); the door's ActionNotice replaces it at the surface level.
- Zero horizontal overflow at both widths (asserted in the glass tests).


## Gate verdict

**Reviewer:** the orchestrator (Fable), 2026-08-31. **Verdict: PASS on
structure** — the cards are ChoiceCardGroup with honest tier blurbs,
sizes, and the RECOMMENDED badge; 393 stacks with zero overflow; the
strip is an ActionNotice with exactly ONE action; the fold keeps the
advanced layer whole. **Three wording defects BOUND TO STORY 05:**
(1) raw GGUF filenames repeated per job line; (2) SPEECH RECOGNITION
listed twice per card (the recommender's display lines duplicate the
speech row); (3) the strip/repair copy reads "Thoughts & notes Fix" —
label collision, not a sentence. 05 does not close while any of the
three stand.
