# HS-115-04 - System surfaces

- **Project:** holdspeak
- **Phase:** 115
- **Status:** done
- **Depends on:** HS-115-01
- **Unblocks:** HS-115-07
- **Owner:** unassigned

## The thesis (the bar)

AttentionDrawer (Desk memory), TrustWindow, SystemShade,
DeskToolInspector, and DeskToolShelf all pass the audit checklist.
Bespoke buttons become shared chips. Prose becomes state labels.
Internal data stays behind RAW disclosure. When this ships, the
system surfaces feel like OS chrome — dense, actionable, quiet.

**Articles served:** VII (no prose, labels state what), VIII
(native-grade craft), XI (every operation has an audit trace —
but the trace is for the system, not the user).

## Ground (from the audit)

| Rule | File | Violation |
|------|------|-----------|
| L4 | desk.css:4102 | AttentionDrawer filter select intrinsic-width |
| M3 | AttentionDrawer.tsx:125 | Filter button is bespoke |
| M3 | AttentionDrawer.tsx:256 | "Load older" is bespoke |
| M3 | TrustWindow.tsx:141 | Navigation uses `btn-link` not chip |
| M3 | DeskToolInspector.tsx:269 | Related-material controls bespoke |
| M3 | SystemShade.tsx:148 | Decision controls are bespoke |
| L2 | desk.css:2396 | Steering refusal details clipped at 220px |
| L2 | desk.css:4703 | Held-call argument previews ellipsized |
| C2 | TrustWindow.tsx:78 | Opens with explanatory prose |
| C2 | TrustWindow.tsx:83 | External-destination alert is paragraph |

## Deliverables

1. **Chip migration.** Replace every bespoke button in AttentionDrawer,
   TrustWindow, DeskToolInspector, and SystemShade with
   `className="desk-chip quiet"`. Six controls total.

2. **AttentionDrawer filter width.** Set the select to fill its column
   (`width: 100%`).

3. **Overflow fixes.** Steering refusal details: remove `max-width:
   220px` or add title attribute + expand-on-click. Held-call
   arguments: same treatment.

4. **Trust window prose → labels.** Replace the opening explanatory
   paragraphs with terse boundary state: "All data stays on this
   device" / "External destinations configured". One line, not two
   paragraphs.

5. **Shade head fill.** Apply `--desk-window-head-fill` to the shade
   header bar.

## Test plan

- `npx vitest run` — all frontend tests pass.
- Open Desk memory → Filter button must be a chip. Select must fill
  its column.
- Open Trust → no prose paragraphs. One-line state labels.
- Open notification shade → decision buttons must be chips. Head bar
  must have the correct fill.
