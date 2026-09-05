# HS-171-04 — PROJECTS in the shade + the dock badge

- **Project:** holdspeak
- **Phase:** 171
- **Status:** in-progress
- **Depends on:** HS-171-01, HS-171-03
- **Unblocks:** HS-171-05, HS-171-08
- **Owner:** unassigned

## Problem

The SystemShade (web/src/desk/components/SystemShade.tsx) has three
sections: Needs you (approve-queue items from the gate and projections),
Finished (receipts), and Learned (dictation corrections). No Room or
Project data appears there. The owner must open each Room individually
to see what needs him. The dock badge (Dock.tsx:146) reads from
launcher.badge and carries coder-session counts, not project needs-you.

## Scope

- In:
  - A PROJECTS section in the SystemShade, positioned above the
    existing "Needs you" section, built to the HS-171-01 artboard.
  - Each row: project name, needs-you count, the first WHY from the
    aggregate (HS-171-03 cache), a severity chip, and an "Open" verb
    that opens the Room.
  - The section headline carries the aggregate count ("PROJECTS -- N
    need you across M projects"); omitted when zero (UX-CANON.md rule
    A.8: no counters of zero).
  - The dock badge on the attention launcher carries the aggregate
    needs-you count from the cached route.
  - The shade polls the cached aggregate when open (the existing
    polling pattern in SystemShade.tsx, useEffect at open).
- Out:
  - Real-time websocket push (the shade polls on open; push is a
    future enhancement).
  - People items in the shade (Phase 172).
  - Editing project settings from the shade.

## Acceptance criteria

- [ ] The PROJECTS section appears in the SystemShade when the
      aggregate count > 0; omitted when zero (Article VI.1; UX-CANON.md
      rule A.8).
- [ ] Each row shows project name, count, first WHY, severity chip,
      and an "Open" verb (Article VII.1: no prose; UX-CANON.md rule
      A.1: every verb is the library Button).
- [ ] Clicking "Open" on a row opens the Room (via openPrimitive or
      openSurfaceWhenReady, the existing shell helpers).
- [ ] The dock badge carries the aggregate count; zero = no badge
      (UX-CANON.md rule A.8).
- [ ] The shade polls the cached aggregate on open; closing stops the
      poll.
- [ ] The rig asserts the artboard (UX-CANON.md rule E.2): type steps,
      token positions, no intersecting row children.
- [ ] Zero egress (Article III).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k shade_projects`
  (vitest for the shade component, pytest for the API shape).
  - The PROJECTS section renders with the correct count and rows.
  - The section is omitted when the aggregate is empty.
  - The dock badge carries the count.
- Integration: the rig boots a hub with a project that has needs-you
  items, opens the shade, asserts the PROJECTS section.
- Manual: screenshot walk at 1440 + 393; the artboard beside the shot.

## Notes / open questions

- The shade currently uses `useProjections` for its data. The PROJECTS
  section reads from a separate fetch (`/api/desk/needs-you`), not the
  projections store.
