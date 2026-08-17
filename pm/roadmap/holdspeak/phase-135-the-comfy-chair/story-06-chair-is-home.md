# HS-135-06 — The Chair is home

- **Project:** holdspeak
- **Phase:** 135
- **Status:** done
- **Depends on:** HS-135-05
- **Unblocks:** HS-135-13
- **Owner:** unassigned

## Problem

HoldSpeak opens on the spatial floor — the ontology as the front door.
The owner ruled: the Chair is HOME at every width; the floor stays
fully intact one gesture away; counsel settled the gesture as a dock
button.

## Scope

### In

- `/` (desktop grammar, ≥960px) renders the Chair as the landing
  surface. The floor remains complete and unchanged behind a dock
  button (floor glyph, L3 chrome species) that swaps Chair↔Floor
  in place; the swap is instant and stateful (window layer unaffected
  — windows float over both).
- The Cmd+K shelf, menubar, dock, and all existing routes unchanged —
  the shelf remains canonical discovery (law-book addition 3).
- Deep links and existing routes keep working (the route table gains
  the Chair as `/`; the floor gets its own route/state).
- Tests: landing renders Chair; dock button swaps both ways; windows
  persist across the swap; existing route tests untouched-green.

### Out

- Narrow width behavior (Phase 136); any floor redesign; lane content.

## Acceptance criteria

- [ ] Fresh load lands on the Chair; one click reaches the floor; one
  click returns (screenshots).
- [ ] An open DeskWindow survives the swap (test).
- [ ] Full web route suite green.

## Test plan

- `cd web && npx vitest run` — routing/shell suites + new tests;
  both-surface screenshots in evidence.
