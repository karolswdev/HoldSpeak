# HS-102-03 — Ask AI: the composer refit

- **Project:** holdspeak
- **Phase:** 102
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-102-07

## The owner's words (the bar)

> "'Ask AI' — needs an overhaul"

## Problem

The Ask panel (`web/src/desk/components/AskPanel.tsx`, opened from
the selection bar the click grammar now makes prominent) predates the
interior canon: it still composes as sections and controls around a
question box rather than ONE composer well (the grammar the agent
chat and the capability cards already converged on in rounds 2 and
8: mic · material · the verb inline, route and grounding folded into
the well's foot as captions). Round 7 also flagged its
`desk-pullout-md` pre-box answers — answers should render as
MATERIAL (`Material.tsx`), with the run receipt as a quiet caption
and the grounding gauge honest at the point of send. Since round 9
made single-click-select the desk's primary gesture, this surface
is now the FIRST composed thing most selections meet — it must read
native.

## Scope

- In: `AskPanel.tsx` recomposed to the one-well grammar: composed
  hello only where it earns its place, ONE composer well (MicButton,
  question material, Ask verb), Runs on + grounding
  (GroundingSection / RailsPicker) folded into the well's foot;
  answers render through `Material` (no pre boxes), receipts as
  quiet captions, "keep on the desk" as the one material verb on the
  answer; the AskBar → panel handoff stays one gesture.
- Out: the ask wire route and grounding composition
  (`buildGrounding`, byte-identical); the selection grammar
  (HS-102-05); RailsPicker internals.

## Acceptance criteria

- [ ] Hands-first ledger recorded (headed, 1440 + 393; empty,
      grounded-selection, answered, and failed states) before code.
- [ ] One composer well; no label+control stacks; route + grounding
      read as captions in the well foot.
- [ ] Answers are material (Material render), receipt a caption,
      keep-on-desk the verb on the material; failure states honest
      by name.
- [ ] Driven live on a staged hub against the real model (.43 or
      staged endpoint): select an object → Ask → grounded answer →
      keep → the artifact materializes; both viewports, screenshots
      read.
- [ ] A named guard: the interior-canon guard (or vitest) refuses
      `desk-pullout-md` pre-boxes in AskPanel and pins the one-well
      composition.

## Test plan

- Web vitest (ask tests updated); token gate; vocabulary +
  interior-canon guards; the live grounded-ask drive (control vs
  treatment where a model is available); both viewports, headed.

## Evidence required

- The ledger; before/after; the live grounded-ask record; guard
  output.
