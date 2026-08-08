# HS-128-01 — Intelligence pullout shell

- **Project:** holdspeak
- **Phase:** 128
- **Status:** done
- **Depends on:** —
- **Unblocks:** HS-128-02 through HS-128-10
- **Owner:** unassigned

## The thesis (the bar)

Intelligence is one native Desk surface, not three feature panes. Its shell
establishes one quiet, persistent place for the operating picture.

### What changes

1. Register `IntelligencePullout` in `PULLOUT_CONTENT` and open it through the
   existing Pullout protocol.
2. Render DeskWindowFrame chrome and a segmented `BRIEF` / `FOLLOW-THROUGH` /
   `RECEIPTS` header using the established Signal Workbench grammar.
3. Default the first open to Brief; preserve the last selected view on later
   opens without changing unrelated pullout state.
4. Render an honest placeholder in each view until its data surface lands.

## Acceptance criteria

1. Intelligence opens and closes as a standard Desk pullout.
2. All three tabs switch the interior without creating a route or modal.
3. First open selects Brief; reopening restores the prior selected view.
4. Empty placeholders are compact, named, and usable by the later stories.

## Test plan

- Web: mount through `PULLOUT_CONTENT`; assert the three tabs and default.
- State: open, select Receipts, close, and reopen to prove view preservation.
- Walk: inspect the pullout inside existing DeskWindowFrame chrome.
