# Evidence - HS-105-02

- **Story:** HS-105-02 - Drop-onto — composition by direct manipulation
- **Status:** done
- **Date:** 2026-07-26

## Proof

### Captured run — 2026-07-26T16:28:19Z

- **Command:** `sh -c cd web && npx tsc --noEmit -p . && npx vitest run 2>&1 | grep -E 'Tests|Files' && npm run tokens:gate 2>&1 | tail -1`
- **Cwd:** .
- **Exit code:** 0
- **Index-tree:** 4a1467bd280d2b38ec8a6d301d91d16a31f4f960

```text
 Test Files  54 passed (54)
      Tests  336 passed (336)
token gate: clean (61 allow-listed exceptions, all in use)
```

## What shipped (the narrative)

The AppIcon rule lands: objects compose by direct manipulation, and
the matrix is CONTRACT DATA (`dropMatrix.ts`) — what a kind accepts
and the NAMED verb release performs; unlisted pairs refuse by
omission; components never hardcode kind pairs (guard-pinned).

- **The physics of intent** (engine): during an object drag, the
  object under the cursor is matrix-consulted; a viable target lights
  via its REAL `_sel` state image (the dual-image rule reused as the
  drop affordance) and the verb tag rides the cursor — the consent
  surface: the tag states exactly what release does. Inert pairs stay
  inert; the tag and lighting clear on leave/release.
- **The verbs, v1 (consent-honest)**: groundable → recipe/chain/
  workflow = "Hold as source" — the target's card opens with the
  dropped object's CONTENT as the held run material and the Ask/Run
  verb beside it (the human presses it; a drop never fires a model);
  filable → kb = "Add to Knowledge" — the SAME membership PUT the
  card's Filed strip toggles, reversible there. Zone filing (drop on
  a drawer) predates this story and joins the matrix conceptually.
- **A drop is an entrance, not a move**: the dragged object returns
  home after the verb.

## The live walk (staged hub :8788)

1. Dragged the Project glossary note over "Summarize like a PM": the
   verb tag read "Hold as source" (assets/hs105-drop-verb.png);
   release opened the recipe's card with the note's REAL content
   (the BLUEBIRD glossary text) prefilled as run material and the
   Ask verb armed beside it (assets/hs105-drop-grounded.png).
2. Dragged a note over a KB: tag read "Add to Knowledge"; release
   landed the membership ON THE WIRE — GET /api/kbs shows the
   note's qualified ref in member_ids (printed in the walk output).
3. Honest note: the "Selected source" strip is the coder-session
   affordance; for capability kinds the grounding rides the material
   input — verified by value, not by strip presence.

## Guards

`dropMatrix.test.ts` (4 pins: named verbs per family, refusal by
omission, no verb-less rules). Captured above: tsc clean, vitest
336/336 (54 files), tokens gate clean. Remainder recorded: multi-
object drops, drop-into-zone-windows (cross-window re-filing), the
orb as a drop target (Speak-with-context) — sitting-loop material.
