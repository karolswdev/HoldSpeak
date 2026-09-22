# PHILO-2-04 - The live pass, Muad'Dib

- **Project:** holdspeak-philo
- **Phase:** 2
- **Status:** backlog
- **Depends on:** PHILO-2-01
- **Unblocks:** see the phase status doc
- **Owner:** Muad'Dib (Opus workers); Astra checks

## Problem

A graph read from the tree cannot see an Open that fails with zero diff. The live pass presses every edge in every atlas state and records what changed: DOM, URL, open windows, requests fired, DB rows, receipt line. Zero diff is a finding.

## Scope

- **In:** what the acceptance criteria name, and only that; the one brief (`docs/internal/philo/briefs/graph-audit-brief.md`) is the contract.
- **Out:** fixing the product (Phase 3), correcting docs before the council (story 07), anything on the owner's desk.

## Acceptance criteria

- [ ] `scripts/graph_walk.py` (the one press-and-diff rig; parametrised by state and width; it replaces the phase walks, which are parked, never deleted) runs against a real hub in an isolated HOME with states minted through the real API (never a double), at 1440 and 393, with the clock advanced per the atlas.
- [ ] The first-use twenty are walked first with the real LAN engine; every other edge with a recorded engine reply.
- [ ] Per edge per state: the consequence record (diff classes) and a shot; zero-diff edges and un-renderable states are findings with their shot.
- [ ] The pass never touches the owner's desk (`~/.local/share/holdspeak`), never the microphone (fixture WAV), never his keychain.
- [ ] Output: `docs/internal/philo/graph/live-muaddib.json` + `live-muaddib.md` + shots; Astra's check recorded beside it.

## Test plan

- **Unit:** the rig's diff classifier has negative controls (a known dead verb reads zero-diff; a known live verb reads its class).
- **Integration:** the rig itself, one state, both widths, in CI.
- **Manual / device:** none; the owner's own sitting is HS-202-06.

## Notes / open questions

The roots lens applies to every criterion: the owner works ninety percent of his day on the desk; the interfaces guide him; Workbench 2.0+ on steroids (Tenet 6). A finding that does not cost him on a Tuesday ranks last.
