# HS-172-07 — People in the Room and the shade

- **Project:** holdspeak
- **Phase:** 172
- **Status:** in-progress
- **Depends on:** HS-172-03, HS-172-05, HS-172-06
- **Unblocks:** HS-172-08
- **Owner:** unassigned

## Problem

People are not reachable from the Room or the shade at 393. The arc
names this "the 393 gap paid." The Room has NEEDS YOU, SOURCES, SINCE
YOU LOOKED, and DECISIONS sections but no People section. The People
card (from the 1:1 brief) has no entry point from the Room's context.
The shade has no People items.

## Scope

- In:
  - A PEOPLE section in the Room (or under NEEDS YOU as a subsection)
    showing the resolved team members who appear in Watch entities,
    each with their brief summary (PRs waiting, commitments overdue).
  - The People card opens from the Room (tapping a person row) and
    from the shade at 393.
  - The face at both widths follows the HS-172-01 artboard.
  - The People card shows the enriched 1:1 brief data (HS-172-05).
- Out:
  - Creating new People relationships from the Room (the People
    setup flow is separate).
  - The full People management surface (list, archive, etc.).
  - People items in the shade beyond the Room-reachable card (the
    shade shows the People card from Room context only).

## Acceptance criteria

- [ ] The Room shows resolved People for the project's Watch entities
      at both widths (1440 + 393); verified by a rig with a seeded
      Watch snapshot and linked People aliases.
- [ ] Tapping a person row in the Room opens the People card with the
      enriched 1:1 brief.
- [ ] The shade at 393 allows reaching the People card from a Room
      context.
- [ ] When no People aliases are linked to Watch entities, the section
      is absent (UX-CANON.md rule A.8: no counters of zero).

## Test plan

- Unit: `HOME=$(mktemp -d) uv run pytest -q tests/ -k people_in_room`
  - Room returns People section with resolved team members.
  - No aliases linked = no People section.
- Integration: n/a.
- Manual: the owner's Room shows People for his team; the card opens
  at both widths.

## Notes / open questions

- The 393 layout: at narrow width the People section may collapse to
  a summary row with a chevron, expanding into the People card. The
  artboard decides.
