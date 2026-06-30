# HS-69-05 — Premium sheets / modals uplift

- **Status:** done
- **Priority:** MED (touches every modal)
- **Depends on:** HS-69-02
- **Catalog pattern(s):** §5 sheets
- **Evidence:** [evidence-story-05.md](./evidence-story-05.md)

## Goal

Bring the iPad sheet craft (grab handle + glyph-chip header + accent "Done"
pill + tinted glow background) to the web's modal surface, so every confirm
prompt reads as a premium Signal sheet rather than a flat box.

## Scope

- `ConfirmDialog.astro` — the one `<dialog>` mounted by AppLayout and used by
  every page's destructive/affirmative prompt (history, dashboard, activity,
  dictation blocks/knowledge). One uplift touches them all.
- Contextual: a danger prompt tints the glyph + glow + pill red; an affirmative
  prompt is accent.

## Proof required

Grab handle + glyph-chip header + accent "Done" + tinted glow applied;
screenshots of ≥2 dialogs uplifted.

## Done

Shipped and screenshot-proven in both states (`sheet-danger.png`,
`sheet-confirm.png`): grab handle, contextual glyph chip (accent check ↔ danger
alert), top-lit gradient hairline, tinted-glow backdrop, and the accent/danger
"Done" pill with a soft glow. The stale "Workbench window" comment was removed.
Behaviour unchanged (focus/Esc/labels); density guard + route pre-flight green.
