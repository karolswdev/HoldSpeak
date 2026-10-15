# Next surface findings

2026-10-15, base c910 plus this pass. These are open refinements, not repaired
claims. Root read the production shots cited below; no new provider behavior
is inferred. Keep the existing Workbench kit and writers.

1. **Duplicate speech control in Decisions search — small, clear cost.**
   `web/src/desk/pullouts/views/DecisionsView.tsx:348` composes StringGadget
   with a separate MicButton. StringGadget already includes its own mic
   (`web/src/desk/surface/gadgets.tsx:336`). Actual desktop shot:
   `.tmp/decision-delight/after-desk-1440/front-window-covers-divider.png`.
   Two adjacent mic buttons compete for one search value. Next direction:
   use the field's existing speech control once; preserve its search writer,
   focus and draft scope. Audit similar StringGadget callers for the same
   composition before making a shared default change. Tenets 3/5/6.

2. **Repeated Send heading — polish introduced by this fold.**
   `web/src/desk/surface/send/SendWell.tsx:875` paints a Send label beside
   the Send verb; expansion adds the existing well's SEND heading. Actual
   reader/record shots: `after-desk-1440/reader-send-folded.png`,
   `record-send-opened.png`, and `after-final-393/reader-send-folded.png`
   under `.tmp/decision-delight/`. The duplicate full preview is repaired,
   but the compact row can be clearer. Next direction: one worded fold
   control with prepared/running/history facts beside it; keep one inner
   destination heading, exact held Retry and egress where dispatch occurs.
   No new disclosure/controller framework. Tenets 3/5/6.

3. **Record context facts have weak hierarchy.** Actual
   `after-final-393/record-send-folded.png` shows Rationale and Source as
   plain text within the Context inset. Source control is worded and works
   through its current handler, but the two facts read like body text.
   Source: `web/src/desk/pullouts/views/DecisionsView.tsx`, ReceiptDetail's
   Context GadgetGroup. Next direction: existing fact-row primitives for
   source identity/action; keep rationale as Material. First audit longer
   titles and multiple source/work links at both widths. Tenets 3/5/6.

The higher-cost behavior findings from the preceding pass are covered by
this pass's runtime observations: seam pointer interception, eager duplicate
preview, refusal closing the editor, and stale ordinary status preview.
This list is a bounded continuation queue, not a claim that the remaining
product has been fully audited or that the owner accepted these faces.
