# HS-121-08 — The command center

- **Project:** holdspeak
- **Phase:** 121
- **Status:** backlog
- **Depends on:** HS-121-01 (LedgerFilter)
- **Unblocks:** HS-121-12 (the walk)
- **Owner:** unassigned

## The thesis (the bar)

Palette is substring-only. No object search. No settings jump. Four
independent search implementations with no persistence. LedgerFilter
(story 01) handles persistence. This story upgrades the palette and
adopts LedgerFilter across search surfaces.

Covers: F2 (palette), F11 (search fragmentation).

## Acceptance criteria

- [ ] Palette uses fuzzy token-based matching.
- [ ] Palette OBJECTS section searches desk store by name.
- [ ] Palette SETTINGS section searches Prefs module index.
- [ ] Meetings, attention, agent picker use LedgerFilter.
- [ ] Filter state persists across window close/reopen.

## Files in scope

- `web/src/desk/components/DeskToolShelf.tsx`
- `web/src/desk/tools.ts`
- `web/src/desk/surface/LedgerFilter.tsx` (from story 01)
- Meeting/attention/agent picker consumers
