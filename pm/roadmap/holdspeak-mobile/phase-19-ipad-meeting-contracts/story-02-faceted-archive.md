# HSM-19-02 — The faceted archive: search + facet chips over the shipped clients

- **Project:** holdspeak-mobile
- **Phase:** 19
- **Status:** done — see [`evidence-story-02.md`](./evidence-story-02.md). Search + facet
  chips on the desktop card, server-side narrowing, honest empties; live-hub proven (real
  facets from real segments/tags; a real narrowed render via the same code path the chips
  call). The `date_*`/`has_open_actions` params stay a named follow-up. The tap rides the
  19-07 walk (W2).
- **Depends on:** `HTTPDesktopClient+Facets.swift` (`listFacets()`, `searchMeetings(query:speaker:type:)`);
  hub routes `GET /api/meetings` (`search/speaker/tag` params) + `GET /api/meetings/facets`
  (`holdspeak/web/routes/meetings/crud.py:24,90`).
- **Unblocks:** archive parity on the iPad (desktop /history has had facets since HS-55).
- **Owner:** unassigned

## Problem

The desktop's archive is searchable and faceted; the iPad's is a flat list. The clients
shipped in Wave 3 (`listFacets` → `{speakers, tags}` chips; `searchMeetings` narrows
server-side) have **zero UI callers** — the shell's live list is still
`CompanionMeetings.load()` → `listMeetings()` with no query params.

## The design

1. **A filter row on the DESKTOP card** (`CompanionShellApp.swift`): a compact search field
   plus facet chips (speakers, tags) fed by `listFacets()` on connect. Tapping a chip or
   submitting a search re-lists via `searchMeetings` — narrowing is server-side, never a
   client-side filter of a stale page.
2. **Chips are honest at N=0:** an archive with no speakers/tags shows no chip row (empty
   arrays are a normal state, not an error).
3. **Active filters are visible and clearable** — a selected chip is lit; one tap clears it;
   clearing everything returns to the plain list.
4. **Compact-aware** (Phase-20 law): the filter row wraps on the lane via the existing
   `FlowLayout`.

## Scope

- **In:** the filter row (search + speaker/tag chips), server-side narrowing, selected/clear
  states, honest empties, sim proof.
- **Out:** the hub's `date_from/date_to/has_open_actions` params (available, unwired in the
  Swift client — a named follow-up, not this story); the desk app's local list (on-device
  meetings are not the hub archive).

## Test plan

- `swift test` green (client already covered by `*ClientTests`).
- Sim proof: seeded facets demo → screenshots of the chip row, a lit chip narrowing the
  list, and the cleared state.
