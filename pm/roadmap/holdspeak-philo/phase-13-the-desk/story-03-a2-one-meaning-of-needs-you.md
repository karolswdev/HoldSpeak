# PHILO-13-03 - A2 One meaning of "needs you"

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** the owner's ratification of this charter
- **Unblocks:** PHILO-13-06 (B1 wires the Chair to the projection), PHILO-13-13 (C3's counts)
- **Owner:** Astra (Luna, xhigh); Muad'Dib checks
- **Lane:** Data + truth (`../wt-philo-13-astra`, `feat/philo-13-astra`)
- **Proposal:** A2 (PROPOSAL §3, Wave A)
- **Closure finding:** `grounding/faces.md:20` (qualified, Astra faces r1 finding 3); `grounding/faces-surfaces.md` F1 (`:188`)
- **Canvas:** none (words and one number; the Chair face is wired in B1)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

"Needs you" means one thing, from one projection, everywhere it shows. A window that counts something narrower says what it counts.

## Problem

One label, several meanings. On one screen he reads `8 need you` beside `NEEDS YOU 5 OF 7`; the bell reads 7; Meetings says "Nothing needs you" while the Dock shows 5 (`grounding/shots/surfaces/01-chair-pop-1440.png`, `41-frame-meetings-open-pop-393.png`, `13-meetings-pop-1440.png`, `131-frame2-bell-pop-1440.png`, `64-room-pop-1440.png`). The surfaces count different things: the Chair combines ranked rows and blockers (`web/src/desk/chair/ChairHome.tsx:800`, `:839`); Meetings counts summary-needed or failed only (`web/src/pages/cores/history/helpers.ts:216-233`); the Dock polls its own read every 60 s (`web/src/desk/components/window/Dock.tsx:60`); the shade reads needs-you on its own 5 s poll (`web/src/desk/components/SystemShade.tsx:149`). The defect is one label with several meanings, not five readings of one total (`grounding/faces.md:20`).

## Scope

- **In:**
  - One projection that defines "needs you" (built on `web/src/desk/projections.ts:101` and its service, `holdspeak/web/routes/projections.py:20`), and one hook the Chair, the bell/shade and the Dock read.
  - The Dock badge logic (`Dock.tsx`, logic) on that hook.
  - Narrower counts renamed to what they count: Meetings (`helpers.ts:216-233`) → e.g. `2 need a summary`; the Room headline → its own fact. Never "needs you" for a narrower count; no counter of zero (A.8).
  - The hook handed to Muad'Dib for the Chair (B1 wires it; `ChairHome.tsx` is his).
- **Out:** the Chair's face (B1); live push of the count (C3); new attention kinds.

## Acceptance criteria

- [ ] One function defines needs-you; a unit fence over a seeded week (real producers) gives one number; the Chair hook, the shade and the Dock read it.
- [ ] Every "needs you" on a populated-week shot agrees, at 1440 and 393 (Chair after B1; bell, shade and Dock here).
- [ ] Meetings and the Room never say "needs you" for a narrower count; each says what it counts; zero is omitted or said true (`Nothing needs a summary`).
- [ ] Red on main: the shots above disagree; green here on the same seed.

## Test plan

- **Focused:** the projection's service tests; web unit on the hook and the Dock badge; `uv run python scripts/check_web_baseline.py --run` (zero branch-new).
- **Atlas:** one case reading the count on the Chair, bell and Dock in one run, at 1440 and 393 (touch), `scripts/graph_walk.py run`, one case per invocation.
- **Shots:** the six shots above, re-taken on the same seed.

## Worker-brief scars

- **Fences that name old words:** fences that assert `Nothing needs you` on Meetings or the Room change with the word, in the same commit.
- **Doubles that lie:** seed the week through the real producers (`scripts/philo11_send_job.py` `mint` pattern, `grounding/faces-surfaces.md:11`); never a stub that returns the count.
- **Never rewrite a guard to match a removal:** if a per-surface count goes, its guard rehomes onto the shared projection.

## Effort (not a promise)

Grounding size: not sized as a move. PROVISIONAL.

## Notes

- 2026-10-01 — `web/src/pages/cores/history/helpers.ts` and the Room headline are not in PROPOSAL §4's map; this charter assigns them to this lane (see the status file's map gaps). For Astra's check.
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
