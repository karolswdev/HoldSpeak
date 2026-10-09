# Lane 16a-A3 — the interior kit: proof shots

Each shot is one window of the four the canvas draws
(`../01-canvas/compositor.html`), composed from the kit on a real hub.

| Shot | Canvas window it matches | Face |
|---|---|---|
| `needs-you-1440.png`, `needs-you-393.png` | "Needs you" (`#w-needs`) | `web/src/desk/needs/NeedsDrawer.tsx` (the Chair's Needs-you window) |
| `room-1440.png`, `room-393.png` | "Payments ledger cutover" (`#w-room`) | `web/src/desk/drawer/DrawerWindow.tsx` (the Project's window: Icons / List, Room, History) |
| `conductor-1440.png`, `conductor-393.png` | "Conductor" (`#w-cond`) | `web/src/desk/conductor/ConductorWindow.tsx` |
| `meeting-1440.png`, `meeting-393.png` | "Cutover sync" (`#w-mtg`) | `web/src/pages/cores/history/MeetingDetail.tsx` + `MeetingHeader.tsx` in the Meetings window (`HistoryCore.tsx`) |

1440: the window element alone. 393: the screen (one window fills the work
area).

## The rig

- A real `MeetingWebServer` on an isolated HOME and a fresh database
  (`tests/e2e/glass_infra._boot`), removed after the run. Nothing read the
  owner's DB, Keychain, `~/.codex`, `~/.claude` or `~/.pi`.
- The seed: the PHILO-14 C4 Conductor seed (`tests/e2e/test_philo14_c4_conductor_glass._seed`:
  the meeting "Ledger cutover sync" with three action items, Claude Code
  asking "The runbook needs a rollback owner. Jordan or Avery?", Codex at
  work, three launches, PR #412), plus the Project "Payments ledger cutover"
  with that meeting, its meeting Watch and one GitHub Watch (the two
  Sources), four speakers on the transcript, and two decision proposals
  (one confirmed for Jordan, one to decide).
- The script: the lane's scratchpad `a3_shots.py` (not committed).

## Lane A1's material is injected

Lane A1 (the slate ground, the paper wells, the interior token remap) is on
its own branch and not on `main`. So that the shots show the kit in the
material it was drawn for, the rig injects A1's `:root` tokens (from
`p16/a1-material` 86ed790cc, `tokens.css`) and A1's
`web/src/desk/components/window-interior.css` verbatim into the page. The
kit itself reads A1's tokens with fallbacks: without A1 the window ground
stays dark and the kit's ground words fall back to `--text`, so a face
stays readable; the paper wells are paper either way.

## What the 393 run measured

- Every library Button on the meeting window owns 44 px (height or the
  narrow-desk halo): none under 44 px.
- No horizontal scroll on the screen.
- No page errors at 1440 or 393.
