# Evidence — HS-69-05: Premium sheets / modals uplift

**Date:** 2026-06-29
**Verdict:** done. The shared confirm dialog now wears the iPad sheet craft,
contextual to danger vs affirmative, proven by screenshots in both states.

## What shipped (`web/src/components/ConfirmDialog.astro`)

- **Grab handle** — a quiet centered pill bar at the top edge, echoing the iPad
  sheet's pull affordance.
- **Glyph-chip header** — the header is now a flex row with a `.glyph-chip`
  beside the title. The icon swaps with context: a check for an affirmative
  prompt, an alert triangle for a destructive one, driven by an `is-danger`
  class the dispatcher toggles (alongside the existing primary/danger button
  toggle). In the danger state the chip itself tints red.
- **Top-lit gradient hairline** — the same masked 1px gradient border as
  `.signal-card`, added as the dialog's `::before` (the dialog's surface/elev
  stay the more-elevated modal values; only the hairline is borrowed).
- **Tinted-glow backdrop** — the `::backdrop` gains a soft accent (or danger)
  radial wash over the dim overlay.
- **Accent "Done" pill** — the action buttons are now `--radius-pill`, and the
  affirmative (primary/danger) carries a soft glow.
- Removed the stale `HS-12-02 Workbench window` comment (hard border / VT323 /
  no rounded corners) that no longer described the code.

One uplift covers every modal: `ConfirmDialog` is mounted once by AppLayout and
called via `window.holdspeakConfirm` from history, dashboard, activity, and the
dictation blocks/knowledge flows.

## Proof

- **Screenshots** (`scripts/screenshot_phase69_sheet.py`, real seeded server,
  `holdspeakConfirm` triggered on `/settings`):
  - `screenshots/sheet-danger.png` — "Delete this meeting?" with the red glyph
    chip + alert icon, the red-tinted backdrop glow, the local-only scope pill,
    and "Keep" / "Delete" pills (Delete carries the danger glow).
  - `screenshots/sheet-confirm.png` — "Apply these settings?" with the accent
    check chip, the accent backdrop glow, and "Cancel" / "Apply" pills.
- **Behaviour preserved:** the dispatcher's focus/Esc/backdrop/label logic is
  untouched; the route pre-flight (every page loads with zero page errors, so
  the inline dialog script parses) = 2 passed; frontend density guard = passed
  (ConfirmDialog still under the component budget).
