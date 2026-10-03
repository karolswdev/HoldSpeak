# PHILO-13-13 - C3 A live Dock (AppIcons)

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** in-progress
- **Depends on:** PHILO-13-03 (A2, the one needs-you projection); PHILO-13-04 (A3, Record reads `res.ok`); PHILO-13-11 (C1 canvas ratified: live state drawn on the AppIcons, criterion 7); PHILO-13-09 (B4, for the 1:1 time on People)
- **Unblocks:** C3-W (the faces lane's wiring step)
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks. Wiring step C3-W: Muad'Dib (Fedaykin, Opus 5.5) on `feat/philo-13-muaddib`; Astra checks
- **Lane:** Data + truth (`../wt-philo-13-13-astra`, `feat/philo-13-13-astra`)
- **Proposal:** C3 (PROPOSAL §3, Wave C)
- **Closure finding:** `grounding/structure.md` F4 (`:287`), move 3 (`:302`); `grounding/faces-jobs.md` move 5 (`:156`)
- **Canvas:** C1's (the AppIcon states, criterion 7)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

The Dock shows his day live, from the bus: REC only when the hub confirms, the 1:1 time on People, one AppIcon per active project with its count. No polling where a frame exists.

## Problem

The Dock has one live mark, the needs-you count or `•`, on a 60 s poll (`web/src/desk/components/window/Dock.tsx:55-70`, `:60`), though one authenticated WebSocket already dispatches frames (`web/src/runtime/RuntimeBus.tsx:41`; frame names `holdspeak/realtime_frames.py:42`, `web/src/runtime/frames.ts:14`). `desk_changed` triggers a debounced full refresh (`web/src/desk/useDeskChangedRefresh.ts:35`) but does not cover every meeting, Room, thought or sync write (`grounding/structure.md:178`). Polls: `grounding/structure.md:180-190`. The record orb says recording after a refused start (A3).

## Scope

- **In:**
  - Per-app AppIcon state from the projections already loaded (`useProjections`, `web/src/desk/DeskApp.tsx:186`), generalising the one badge path (`Dock.tsx` logic).
  - `REC <time>` on Meetings only when the hub confirms recording (after A3).
  - The next 1:1 time on People (after B4's link).
  - One AppIcon per active project with its needs-you count (A2's projection).
  - Scoped invalidation on the producers the bus does not yet cover for these states (a meeting becoming ready, a send settling), and recovery after a reconnect; the Dock's 60 s poll retired where a frame exists.
- **C3-W (the faces lane, a named wiring step):** the AppIcon states drawn in `dock.css` to the ratified C1 canvas. This lane edits no CSS.
- **Out:** a new event system or SSE (`grounding/structure.md:168`); a status window; retiring low-value operator polls (`grounding/structure.md:192`); the AppIcon art (C1, Muad'Dib).

## Acceptance criteria

- [ ] With every window closed, a meeting becoming ready or a send settling shows on the Dock within ~1 s of the server event, at 1440 and 393. A real producer, an emitted frame, a consumer read and a rendered change, in one fence (`grounding/structure.md:178`).
- [ ] REC shows only after the hub confirms; a refused start shows no REC.
- [ ] After a disconnect, changes made while disconnected show after reconnect; no freshness is claimed while disconnected.
- [ ] No zero badge (A.8); no new status window.
- [ ] The Dock reads no needs-you poll where a frame exists.
- [ ] **H-C3** merged (this lane: `Dock.tsx` logic, `web/src/runtime/**`, `useDeskChangedRefresh.ts`, backend producers). **C3-W** merged by the faces lane; **its merge record cites the owner's ratification record of the C1 canvas (path + his quote).** The story flips `done` only when both are merged; the merge record names both commits.

## Test plan

- **Atlas file:** `docs/internal/philo/graph/atlas-phase13-astra.json` (this lane's only atlas file; `--atlas` per run, `scripts/graph_walk.py:6507`); its count fence in `tests/unit/test_philo13_astra_atlas.py`. The C3-W wiring step's face cases go in `atlas-phase13-muaddib.json` (the faces lane's file).
- **Focused:** realtime frame tests for the producers touched; web unit on the Dock state reducer; `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** real hub, every window closed: finish a meeting's summary through the real producer; settle a send to the FILE destination in the HOME; time the Dock change.
- **Atlas:** one case per live state (meeting ready, send settled, REC confirmed/refused, reconnect), at 1440 and 393, one case per `scripts/graph_walk.py run` invocation.
- **Shots:** the Dock before and after each event, both widths.

## Worker-brief scars

- **Doubles that lie:** a fence that pushes a fake frame into the client proves the reducer, not the Desk; the proof is a real producer's frame.
- **The receipt under one branch:** the send AppIcon shows each outcome the send can reach (sent, failed, unknown), not only success.

## Effort (not a promise)

Grounding size: M (`grounding/structure.md:302`; `grounding/faces-jobs.md:156`). PROVISIONAL.

## Notes

- 2026-10-01 — r2: Astra charter check r1 (DO-NOT-RATIFY) paid; see the status file, "Round two".
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.

- 2026-10-03 — H-C3 and H-C3-origin candidate: [Astra lane report](lane-13-astra.md). UNCHECKED — awaiting Muad'Dib. C3-W remains a named handoff; no done flip.
