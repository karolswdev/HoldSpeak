# HS-115-06 - The rails window

- **Project:** holdspeak
- **Phase:** 115
- **Status:** backlog
- **Depends on:** HS-115-01
- **Unblocks:** HS-115-07
- **Owner:** unassigned

## The thesis (the bar)

The DeliveryBoard, DeliveryTerminalWindow, DeliveryDossierWindow,
and RoadmapWindow are rebuilt to fit the Desk OS window grammar.
The Rails view stops trying to show everything at once. The title
bar stays fixed. The window material uses the shared tokens. Raw
operational identifiers are hidden. When this ships, the delivery
surfaces feel like OS tools — dense but navigable, not an ops
dashboard pasted into a window.

**Articles served:** I (no feature-owned pages), VII (no prose,
quiet chrome), VIII (native-grade craft).

## Ground (from the audit)

| Rule | File | Violation |
|------|------|-----------|
| L3 | desk.css:3076 | DeliveryBoard scrolls entire shell, title bar disappears |
| C1 | DeliveryBoard.tsx:328 | Everything renders concurrently, overloading window |
| M1 | desk.css:3080 | Board uses `--surface-1` not `--desk-window-fill` |
| M3 | desk.css:3149 | Dossier story opener is bespoke button |
| M1 | RoadmapWindow.css:0 | No window-body material, transparent |
| M3 | RoadmapWindow.tsx:22 | Phase controls are custom flat buttons |
| L2 | RoadmapWindow.css:9 | Phase/story titles permanently hidden |
| L2 | RoadmapWindow.css:25 | Health paths permanently hidden |
| C1 | RoadmapWindow.css:1 | Body escapes frame in constrained windows |
| D3 | RoadmapWindow.css:12 | Separate visual grammar (pills, rounded cards) |
| C1 | DeliveryBoard.tsx:118 | Active-work rows expose node, branch, worktree, INEXACT |
| C1 | DeliveryBoard.tsx:425 | Unbound-session rows show raw pane/node IDs |
| C1 | DeliveryTerminalWindow.tsx:205 | Raw target, generation, worktree IDs |
| C1 | DeliveryDossierWindow.tsx:103 | Internal state/freshness enums, commit SHA |
| C1 | DeliveryDossierWindow.tsx:136 | Raw shell commands outside RAW fold |
| C3 | desk.css:3084 | Board labels use generic typography |

## Deliverables

1. **DeliveryBoard scroll fix.** The board body must scroll inside
   the window shell. Title bar stays fixed. Structure:
   `shell > fixed-head + scrollable-body`.

2. **DeliveryBoard information architecture.** The board currently
   renders sources, projects, stories, work, sessions, launches,
   and receipts all at once. Restructure into wings or tabs:
   - **Stories** wing: project + phase + story cards
   - **Work** wing: active sessions and launches
   - **Events** wing: event log (currently at the bottom)

3. **Board material.** Use `--desk-window-fill` instead of
   `--surface-1`. Labels use `--font-mono` and surface tokens.

4. **Board content sanitization.** Active-work rows: show session
   name and status, not raw node/branch/worktree IDs. Unbound
   sessions: show session name, not raw pane identifiers.

5. **RoadmapWindow body.** Add flex layout with bounded height.
   Use `--desk-window-fill` background. Replace rounded pills/cards
   with shared Desk chip/ledger grammar.

6. **RoadmapWindow overflow.** Phase/story titles and health paths
   get `title` attributes and either two-line treatment or
   expand-on-click.

7. **Dossier/terminal cleanup.** Dossier: state/freshness enums
   and commit SHA go behind RAW. Shell commands go behind RAW.
   Terminal: raw target/generation/worktree IDs → human-readable.
   Dossier story opener → `desk-chip quiet`. Phase controls →
   `desk-chip quiet`.

## Test plan

- `npx vitest run` — all frontend tests pass.
- Open Rails → resize window → title bar must stay fixed, body
  must scroll.
- Open Rails → only one wing's content visible at a time.
- Open a roadmap window → resize smaller → content must not escape
  the frame.
- Open a dossier → no raw enums or commit SHAs in primary view.
