# HS-116-14 — Voice-driven workbench

- **Project:** holdspeak
- **Phase:** 116
- **Status:** done
- **Depends on:** HS-116-10, HS-116-11
- **Unblocks:** HS-116-15
- **Owner:** unassigned

## The thesis (the bar)

The workbench is fully drivable by voice. Not just "mic button fills
a text field" — real voice commands that create items, set priorities,
trigger runs, and configure the workbench. The existing desk voice
command system (grammar + intent router + proposal strip) gains
workbench-scoped commands. When this ships, a user can hold the mic
and say "add review the auth timeout PR, priority one" and the item
appears on the workbench with P1 priority — no keyboard.

**Articles served:** IV (voice is first-class — every text input can
be spoken into; voice arms, it does not fire except where configured),
VII (no prose — the voice commands are the interface).

## Deliverables

1. **Workbench voice commands.** Register the following voice intents
   in the desk voice grammar when a workbench window is focused:

   | Voice command | Action |
   |---|---|
   | "add [title]" / "new item [title]" | Create item with spoken title |
   | "add [title] priority [1-5]" | Create item with priority |
   | "run" / "run this workbench" / "go" | Trigger manual run |
   | "dismiss [item reference]" | Dismiss the focused/named item |
   | "set agent to [name]" | Pick a recipe by name |
   | "set schedule [preset]" | Apply a schedule preset |
   | "clear done" | Remove all done/dismissed items |

2. **Mic button on every input.** The composer already has MicButton
   for the title input. Add mic affordances to:
   - The item body textarea (when expanded for editing)
   - The workbench name (EditInPlace — hold mic to rename by voice)
   - The constitutional context editor textarea

3. **Voice-created items proposal strip.** When a voice command
   creates an item, it follows Article IV.2: voice arms, it does
   not fire. The item appears in a proposal strip at the top of the
   item list, showing what was heard and what will be created. The
   user confirms (Enter/tap) or dismisses (Escape).

4. **Voice command discoverability.** The workbench window's
   configuration panel shows a "Voice commands" section with a
   compact list of available commands. No prose — just the command
   and what it does.

## Test plan

- Visual: open a workbench, hold the mic button, say "add review the
  auth timeout, priority one." Verify the proposal strip shows the
  item. Confirm it. Verify the item appears with P1 priority.
- Visual: say "run this workbench." Verify the run triggers.
