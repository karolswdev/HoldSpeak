# HS-115-01 - The shared material

- **Project:** holdspeak
- **Phase:** 115
- **Status:** backlog
- **Depends on:** —
- **Unblocks:** HS-115-03, HS-115-04, HS-115-05, HS-115-06
- **Owner:** unassigned

## The thesis (the bar)

Every shared CSS primitive must consume the Signal Workbench tokens
that Phase 110 defined. Chips get the bevel. Windows get the keyline.
Sections get hairline separation. The specificity wars between the
unified material rule and per-component overrides are resolved — one
cascade, one material. When this ships, fixing a token value changes
every surface simultaneously.

**Articles served:** VII (consistent quality), VIII (native-grade
craft).

## Ground (from the audit)

| Rule | File | Violation |
|------|------|-----------|
| M3 | desk.css:274 | `.desk-chip` lacks bevel box-shadow |
| M1 | desk.css:812 | Pullout border overrides unified material rule |
| M1 | desk.css:981 | Front-window keyline excludes `.is-sheet` |
| M4 | desk.css:1156 | Pullout sections — `border: 0`, no separation |
| M1 | desk.css:812 | Delivery terminal/dossier lack `--desk-window-fill` |
| M1 | desk.css:4125 | Command palette uses wrong shadow/border |
| M2 | desk.css:4578 | SystemShade head lacks `--desk-window-head-fill` |
| M1 | tokens.css:258 | `--desk-window-shadow-rest` has no consumer |
| M2 | tokens.css:275 | `--desk-window-head-front` never consumed |

## Deliverables

1. **Chip bevel.** `.desk-chip` gets `box-shadow: var(--desk-window-bevel)`.
   Every button on every surface gets depth in one line.

2. **Pullout specificity fix.** The `.desk-next .desk-pullout` border
   at line 812 must yield to the shell's material. Either lower its
   specificity or remove the per-pullout border in favor of the shell's
   keyline.

3. **Sheet keyline.** `.is-sheet` front windows get the keyline too.

4. **Section separation.** Pullout body sections get a hairline
   `border-top: 1px solid var(--border-rule)` between siblings
   (`:not(:first-child)`), not `border: 0`.

5. **Delivery shell fill.** Ensure terminal and dossier pullouts
   inherit `--desk-window-fill` from the unified rule.

6. **Command palette material.** The tool shelf gets the bevel and
   keyline treatment instead of its bespoke shadow.

7. **SystemShade head.** Apply `--desk-window-head-fill` to the shade
   header.

8. **Dead token cleanup.** Remove `--desk-window-shadow-rest`,
   `--desk-window-margin`, `--desk-window-grab`,
   `--desk-window-cascade` if truly unused. Wire
   `--desk-window-head-front` to `.is-front` title bars.

## Test plan

- `uv run pytest -q` — no backend regressions.
- `npx vitest run` — all frontend tests pass.
- Visual: open a note pullout, a zone window, an agent chat, and the
  command palette. Every one must show the bevel, the keyline, and
  section hairlines.
