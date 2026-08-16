# HS-120-01 — Workbench agents reforged

- **Project:** holdspeak
- **Phase:** 120
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-120-11 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

The workbench agent surfaces — dashboard cards, config strip, item
cards, inlet composer, template picker — shipped functional in Phase
116-118 but visually unfinished. The owner triggered this entire phase
because these surfaces are ugly.

When this ships, the workbench surfaces feel deliberate and crafted:

1. The inlet composer has real CSS. The `wb-inlet-*` classes that exist
   in JSX but not in any stylesheet get proper rules in
   `workbench-config.css`. The inline `style={{ position: "relative" }}`
   moves to CSS. The dead `wb-composer-*` rules are removed if the
   composer is fully replaced by the inlet.

2. Status is visible at a glance. Pending items get a
   `border-left-color: var(--text-faint)` (not transparent). P1/P2
   priority chips get `data-tone="fail"`/`"warn"`. The dashboard's
   "needs attention" state promotes to a card-level left-border
   treatment (kill the 8px dot). Status card backgrounds get a subtle
   tint matching their status color.

3. Toggle chips show their state. `[aria-pressed="true"]` on
   `.desk-chip` gets `border-color: var(--accent); background:
   var(--accent-tint)`. This is a one-rule CSS fix that ripples across
   schedule presets, priority chips, and every other toggle chip in the
   desk.

4. The config strip signals expandability. A trailing `▾` chevron.
   Agent name at normal weight (identity leads), metadata at faint
   weight. On narrow windows, collapse to avatar + name + chevron.

5. Template picker icons match the sprite system. Use `AgentAvatar`
   for templates with a recipe, workbench cartridge sprite for others.
   No raw platform emoji at 18px.

6. Dashboard agentless cards use the workbench cartridge sprite, not a
   raw `⚙` at 14px with 0.6 opacity.

7. Dead agent-rail.css (97 lines, `position: fixed; z-index: 29`, no
   component references it) is deleted and its import removed from
   `desk.css`.

8. Inline `style={{fontSize:"9px"...}}` on memory/run badge chips
   moves to a CSS class (`.desk-chip.is-compact` or equivalent).

## Acceptance criteria

- [ ] `wb-inlet`, `wb-inlet-row`, `wb-inlet-input`, `wb-inlet-tray`,
      `wb-inlet-egress`, `wb-inlet-resolving`, `wb-inlet-chip-remove`
      are defined in `workbench-config.css`. No inline `position:
      relative` on the inlet container.
- [ ] `.desk-chip[aria-pressed="true"]` is styled in the chip base CSS.
- [ ] Pending items have a visible left border color.
- [ ] P1/P2 chips render with danger/warn tones.
- [ ] Dashboard cards with `needsYou` show a left-border status signal;
      no 8px dot.
- [ ] Config strip has a trailing expand chevron.
- [ ] Template picker renders sprites, not emoji.
- [ ] Dashboard agentless cards render the workbench sprite, not `⚙`.
- [ ] `agent-rail.css` is deleted and its import removed.
- [ ] No inline `style={{}}` on chip badges in WorkbenchWindow.
- [ ] Dead `wb-composer-*` CSS rules removed (if inlet fully replaced
      the composer).

## Test plan

- Visual: open a workbench with pending/running/done/failed items at
  1440px and 393px widths. Verify status hierarchy reads at a glance.
- Visual: open config strip, verify chevron, verify narrow-window
  collapse.
- Visual: open template picker with and without recipes, verify
  sprites render.
- Visual: open workbench dashboard with needs-attention and idle
  cards, verify the distinction.
- Grep: `agent-rail` returns zero hits outside git history.
- Grep: `style={{` in WorkbenchWindow.tsx — zero inline style objects
  on chip/badge elements.

## Files in scope

- `web/src/desk/components/workbench-config.css`
- `web/src/desk/components/WorkbenchWindow.tsx`
- `web/src/desk/components/WorkbenchTemplatePicker.tsx`
- `web/src/pages/cores/WorkbenchesHomeCore.tsx`
- `web/src/desk/components/agent-rail.css` (delete)
- `web/src/desk/desk.css` (remove agent-rail import)
- Chip base CSS (wherever `.desk-chip` is defined)
