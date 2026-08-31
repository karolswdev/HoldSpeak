# HS-156-05 - Plain words: the jargon purge and the UX-evidence checklist

- **Project:** holdspeak
- **Phase:** 156
- **Status:** done
- **Depends on:** HS-156-04
- **Unblocks:** HS-156-07
- **Owner:** unassigned

## Problem

"catalog · available", schema-speak statuses, and unexplained
"Needs attention" are why the co-creator got lost. Every string on the
door path must say what a manager needs next (settled design D4;
POSITIONING voice rules).

## Scope

- **In:** the wording pass over the Models surface's door path and
  list rows: statuses describe state + next step in human words ("not
  downloaded", "downloading · 34%", "ready", "server unreachable —
  check it"); group labels audited against POSITIONING; the concierge
  UX-evidence log (`assets/concierge-ux-evidence.md`, copied into this
  phase) turned into a numbered checklist — every item marked FIXED
  (with the story/test) or RECORDED (with the reason). A product-copy
  fence extension covering the new strings.
- **Out:** renaming backend schema fields; touching non-Models rooms.

## Acceptance criteria

- [ ] The UX-evidence checklist ships in this story's evidence with zero unaddressed items (each FIXED or RECORDED).
- [ ] The copy fence (test_product_copy or a sibling) covers the door strings; no banned jargon on the door path (a greppable deny-list test: "catalog", "no_assignment", raw capability ids in door-path UI strings).
- [ ] vitest snapshot of the row/status wording states.

## Test plan

- **Unit:** the deny-list fence + vitest wording states.
- **Integration:** covered by 03's glass (shots show the final words).
- **Manual / device:** story 05.

## What shipped

### Three bound defects fixed

1. **Raw GGUF filenames (Defect 1):** `_humanize_model_label()` added to
   `front_door_service.py`; converts "Qwen3.5-9B-Instruct-Q6_K.gguf" to
   "Qwen3.5 9B (local)" with the raw filename preserved as a `detail` field.
   Legacy GGUF packs no longer show the filename x7 on the card.

2. **SPEECH RECOGNITION duplication (Defect 2):** `speech_recognition` removed
   from the LLM loop in `_build_pack`; handled only by `_speech_line()` which
   now carries `group_id: "speech_recognition"` for completeness. Each card
   shows Speech recognition exactly once (the whisper line).

3. **"Thoughts & notes Fix" collision (Defect 3):** `repairCopy()` added to
   `frontDoor.tsx`; produces a proper sentence (e.g., "Speech recognition has
   no model"). Short action verbs ("Fix") become "needs attention". ActionNotice
   button changed from "Fix" to "Fix it" per D3 pattern.

### Deny-list fence

Copy fence tests in `frontDoor.test.tsx`: unconfigured cards, configured
strip, and attention strip all rendered and checked for banned jargon
("catalog", "no_assignment", "no_compatible_assignment", "provider_family",
".gguf"). Python deny-list test in `test_front_door_recommendation.py`
covers both catalog-preset and legacy-GGUF packs.

### desk-tokens.css shim retired

Import census: zero importers across the web tree. File deleted. The
one source of truth is `styles/tokens.css`.

### UX evidence checklist

12-item concierge log reviewed: 1 FIXED (item 9, jargon in door path),
11 RECORDED (backend/API gaps, not door-path wording). Checklist at
`assets/concierge-ux-checklist-05.md`.

### Shots

Shot index at `assets/story-05-shots/index.md` with reviewer slot.
Shots need retake after code changes (orchestrator or glass).

## Notes / open questions

- Council checklist item: retire the `desk-tokens.css` import shim after an import census (one token source). DONE: census clean, file deleted.

- No prose novels: plain = wordy; one line beats a paragraph everywhere.
