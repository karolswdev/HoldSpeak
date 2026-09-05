# HS-171-07 — PROJECTS in command-K

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** HS-171-01
- **Unblocks:** HS-171-08
- **Owner:** unassigned

## Problem

The command deck (verbRegistry.ts) registers `desk.new-project` (line
231) but has no verb to open an existing Room. The owner cannot type
a project name into the command palette and jump to its Room. The arc
says: "a PROJECTS section in the command deck."

## Scope

- In:
  - A PROJECTS section in the command deck listing every active Room.
  - Each entry: project name, needs-you count badge (omitted when
    zero), and the "Open" verb.
  - Selecting an entry opens the Room (via the existing
    `openSurfaceWhenReady` or `openPrimitive` shell helpers).
  - The entries are searchable by project name (the existing keyword
    matching in the verb registry).
  - The entries refresh when the desk's project list changes.
- Out:
  - Project creation from the command deck (already exists as
    `desk.new-project`).
  - Archived projects in the command deck.
  - Room subsections (sources, decisions) in the command deck.

## Acceptance criteria

- [ ] Every active Room appears in the command deck's PROJECTS section;
      verified by the rig asserting the entry count matches the project
      count (Article IX.1).
- [ ] Selecting a Room entry opens the Room.
- [ ] The needs-you count badge appears on entries with count > 0;
      omitted when zero (UX-CANON.md rule A.8).
- [ ] The entries are searchable by project name.
- [ ] Archived projects do not appear.
- [ ] Zero egress (Article III).

## Test plan

- Unit: vitest for the verb registry entries.
  - The PROJECTS section renders with the correct entries.
  - An archived project does not appear.
  - The needs-you badge appears for count > 0.
- Integration: n/a (the verb registry is a client-side concern).
- Manual: type a project name in the command palette; the Room opens.

## Notes / open questions

- The verb registry uses a static registration pattern
  (verbRegistry.ts). The PROJECTS entries need to be dynamic (they
  depend on the project list from the API). The existing pattern for
  dynamic entries (e.g., coder sessions in the panes launcher) can be
  followed.
- The entry's `keywords` should include "project", "room", and the
  project name for broad matching.
