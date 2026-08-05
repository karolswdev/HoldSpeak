# HS-116-17 — First-class app

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-10, HS-116-12
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

Workbenches is a first-class application of the DeskOS, sitting
alongside Speak, Meetings, Agents, and Settings. It has its own
dock entry, its own launch surface, and its own home view. The
home view is a dashboard of all workbenches — a quick-scan
surface that tells the owner: which agents are working, which need
attention, what ran overnight, and what's coming up next. This is
NOT a settings page. This is mission control for your agents.

**Articles served:** I (the Desk is the operating surface — the
workbenches app is a desk application, not a feature), VIII
(native-grade craft — the home view is a real surface, not a list).

**UI/UX direction:** Study DW Phase 36's board view: kanban lanes,
story cards, drag-to-move, segmented toggle. The workbenches home
doesn't need kanban lanes (workbenches aren't in "lanes"), but it
needs the FEEL of an operator dashboard: dense, glanceable, status
at a glance, one-click to open any workbench.

The four existing dock apps are Speak (⌁), Meetings (▣), Agents
(◉), Settings (⚙). Workbenches joins as the fifth: the glyph
should communicate "work surface" or "agent workspace." Candidate:
⚒ (hammers — work), ◫ (window with pane — workspace), or ⧉
(the existing workflow glyph, repurposed since the workflow
builder is secondary to workbenches now).

## Deliverables

1. **Workbenches home surface.** A new surface registered in
   `SurfaceWindows.tsx` with key `"open-workbenches"`. This
   replaces the existing `"build-workflow"` / `"surface-workbench"`
   entry (which was the old workflow builder). The home view:

   ```
   ┌──────────────────────────────────────────────────┐
   │ WORKBENCHES                        [＋ Create]   │
   ├──────────────────────────────────────────────────┤
   │                                                   │
   │  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
   │  │ ⚡ TODO Agent │  │ ☀ Morning    │  │ ◈ Bug  │ │
   │  │ 5 pending    │  │   Brief      │  │ Triage │ │
   │  │ 2 done today │  │ Last: 7 AM   │  │ 0 items│ │
   │  │ ● LOCAL      │  │ 3/3 done     │  │ Manual │ │
   │  │ Next: 2 AM   │  │ ● LAN        │  │ ● LOCAL│ │
   │  └──────────────┘  └──────────────┘  └────────┘ │
   │                                                   │
   │  RECENT RUNS                                      │
   │  ┌─────────────────────────────────────────────┐  │
   │  │ 2h ago  Morning Brief  3/3 done  LOCAL      │  │
   │  │ 8h ago  TODO Agent     4/5 done 1 fail  LAN │  │
   │  │ 1d ago  Morning Brief  3/3 done  LOCAL      │  │
   │  └─────────────────────────────────────────────┘  │
   │                                                   │
   └──────────────────────────────────────────────────┘
   ```

2. **Workbench summary cards.** Each workbench appears as a card
   showing: template icon + name, pending/done item counts, egress
   lamp, schedule (next run time or "Manual"), agent avatar (small).
   Cards use the Signal Workbench material (bevel, keyline).
   Click opens the individual workbench window.

3. **Needs-you indicator.** If a workbench has draft skills pending
   approval, failed items, or a refused run, the card shows a
   small attention dot (the same dot the Attention drawer uses).
   The home view header shows a total count: "2 need you."

4. **Recent runs ledger.** Below the cards, a `SurfaceLedger` of
   recent runs across ALL workbenches, most recent first. Each
   row: timestamp, workbench name, items done/failed, egress lamp.
   Click opens the specific workbench's run history wing.

5. **Dock entry.** The workbenches app gets a dock entry in
   `DeskChrome.tsx` alongside Speak, Meetings, Agents, Settings.
   Glyph and position determined by the owner's preference. The
   dock entry shows the "needs you" count as a badge.

6. **Create flow.** The "＋ Create" chip in the home view opens
   the template picker (from HS-116-05) in a new workbench window.
   The "New Workbench" verb in the Create menu also opens this
   flow.

7. **DESK_TOOLS entry.** Update `tools.ts` to register the
   workbenches app with its glyph, label, description, and action
   key so it appears in the command palette and Go menu.

## Test plan

- Visual at 1440: the workbenches home showing 3 workbench cards
  and a recent runs ledger. Verify material (bevels, keylines,
  egress lamps), needs-you dot on one card, dock entry.
- Visual at 393: cards stack vertically, ledger remains scrollable.
- Flow: click a card → workbench window opens. Click "Create" →
  template picker opens. Click a dock entry → home view opens.
