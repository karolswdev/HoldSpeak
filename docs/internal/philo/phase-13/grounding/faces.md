# PHILO Phase 13 grounding — the faces half (index)

**Status:** UNCHECKED — awaiting Astra. **Owner:** Muad'Dib (Fedaykin W1 + W2, Opus 5.5), 2026-10-01. **Base:** main `4c49651e`.
**Plan:** [PLAN.md](PLAN.md) (r2, Astra-checked). **Other half:** [structure.md](structure.md) + [inventory.md](inventory.md) (Astra; Muad'Dib RATIFY, merged #722 `13e3040b`).

| Part | File | What it holds |
|---|---|---|
| Every surface | [faces-surfaces.md](faces-surfaces.md) | 21/23 registry rows (20 distinct faces), the frame, 3/7 object windows + the Delivery door, 7/13 pullouts, the Room; 1440 + 393, cold + populated; the carried ledger; the canon audit; 18 findings; reconciliation with S0. 187 shots in `shots/surfaces/`. |
| The Tuesday spine, the fold, the ambition | [faces-jobs.md](faces-jobs.md) | J1–J5 end to end at both widths with return and recovery (gestures, dead taps, rig seconds); the Phase 12 fold map; 10 ambition moves on the four-part test; 15 findings; 5 forks. 85 shots in `shots/jobs/`. |

## Muad'Dib's own verification (orchestrator, before relaying)

- **Read on glass:** `shots/surfaces/01-chair-pop-1440.png` — "8 need you", "NEEDS YOU 5 OF 7", bell 7, Dock 7 on one screen; `41-frame-meetings-open-pop-393.png` — Meetings "Nothing needs you" while the Dock shows 5; the frame (menu bar + capture bar + two Dock rows) takes ~250 of 852 px.
- **Recording that lies (jobs F2), verified in source:** `recordingSlice.ts:47-56` awaits `apiRequest` and sets `recording` with no `res.ok` check; `lib/api.ts:27-32` is a bare `fetch`. Confirmed.
- **The invisible closed window (jobs F1):** `openPullout` stores the id as given (`compositorSlice.ts:137-152`), `Pullout.tsx:68` closes with `o.id`, `closePullout` filters by equality (`:177-189`). The mismatch is plausible from source; **not yet proven by a failing unit test** — the charter story owes that test first.
- **The look.** Beyond the defects: the Chair at 1440 reads as a black web dashboard — lists of rows and chips — not as a Workbench desk of windows, gadgets and icons. Neither half measured this, because it is not a defect; it is the gap the owner named ("lean on the steroids"). The proposal leads with it.

## Combined top findings (both faces files + structure, by owner cost)

1. **Work is destroyed or lost.** Meetings and Workbench items hard-delete (structure F1, surfaces #3); windows, places and drafts are lost on reload or close (structure F2, jobs F5: the J3 note typed 4 times).
2. **The Desk does not tell one truth.** Needs-you counts disagree across Chair, bell, Dock and Meetings (surfaces #1); status faces contradict (summary ON/OFF, destinations None, Agents empty) (surfaces #2); Record claims a refused recording (jobs F2).
3. **What he reads does not open.** Brief, calendar and commitment rows are inert; Brief→People dispatches nowhere (jobs F3, structure F3).
4. **A closed window keeps catching taps** until reload (jobs F1).
5. **The phone is a third chrome** (surfaces #4, jobs F12).
6. **Failure faces dead-end or print raw server text** (surfaces #5, jobs F4/F11).
7. **The 12 px floor broken on 25 faces; 102 raw-button candidates** (surfaces #9, structure §3).
