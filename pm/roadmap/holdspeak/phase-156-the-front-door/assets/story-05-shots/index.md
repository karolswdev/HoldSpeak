# HS-156-05 shot sheet — plain words: the jargon purge

Reviewer: ______________ Verdict: ______________ Date: ______________

## Cards (unconfigured desk) — after defect fixes

| Shot | Width | What to look for | Present |
|------|-------|-----------------|---------|
| door-cards-1440.png | 1440 | Human model names "Qwen3.5 9B (local)" (not raw .gguf filenames); SPEECH RECOGNITION appears ONCE per card (not duplicated); TEXT-TO-SPEECH line present; group labels match POSITIONING | YES |
| door-cards-393.png | 393 | Same content at mobile width; no horizontal overflow; cards stack cleanly | YES |

## Strip + repair (configured desk) — after defect fixes

| Shot | Width | What to look for | Present |
|------|-------|-----------------|---------|
| strip-repair-1440.png | 1440 | Attention notice reads "Thoughts & notes needs attention" (a sentence, not "Thoughts & notes Fix"); "FIX IT" button (not "Fix"); Advanced disclosure below | YES |
| strip-repair-393.png | 393 | Same content at mobile width; FIX IT button accessible | YES |

## Bound defects addressed (visually confirmed)

1. **Raw GGUF filenames (Defect 1):** Cards show "Qwen3.5 9B (local)" per group, not "Qwen3.5-9B-Instruct-Q6_K.gguf". Confirmed in door-cards-1440.png and door-cards-393.png.
2. **SPEECH RECOGNITION duplication (Defect 2):** Each card shows Speech recognition exactly once (the whisper line). No duplicate LLM line. Confirmed in door-cards-1440.png.
3. **"Thoughts & notes Fix" collision (Defect 3):** Strip reads "Thoughts & notes needs attention" with a "FIX IT" button. No label collision. Confirmed in strip-repair-1440.png and strip-repair-393.png.


## Gate verdict

**Reviewer:** the orchestrator (Fable), 2026-08-31. **Verdict: PASS.**
All three defects bound by the 04 gate are visibly gone: the cards say
"Qwen3.5 9B (local)" where filenames stood, speech appears once with
its size, and the strip reads "Thoughts & notes needs attention — FIX
IT" — a sentence with its one action. 393 stacks clean. The story-04
sheet keeps its historical frames; this sheet is the wording record.
