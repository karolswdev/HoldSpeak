# PHILO-13-07 - B2 The Desk remembers

- **Project:** holdspeak-philo
- **Phase:** 13
- **Status:** backlog
- **Depends on:** **PHILO-13-01 (B0): its cases exist and pass on main before this story merges (the gate)**; PHILO-13-05 (close means gone)
- **Unblocks:** D1 (out of this phase; the owner's "Later" waits on this story's return in real use)
- **Owner:** Muad'Dib (Fedaykin, Opus 5.5); Astra checks
- **Lane:** Faces + frame (`../wt-philo-13-muaddib`, `feat/philo-13-muaddib`)
- **Proposal:** B2 (PROPOSAL §3, Wave B); fork 3, "Everything"
- **Closure finding:** `grounding/structure.md` F2 (`:285`), move 1 (`:300`); `grounding/faces-jobs.md` F5 (`:171`), move 2 (`:153`); `grounding/faces-surfaces.md` F13 (`:200`)
- **Canvas:** none (no new face; the return is the existing windows in their places)

`grounding/` = `docs/internal/philo/phase-13/grounding/`.

## Goal

Every open window, its place and any unsent draft survive a reload and a close, automatically (Workbench *Snapshot*; the owner's fork 3, "Everything").

## Problem

The workspace document `hs.desk.workspace.v1` keeps surface windows, rects, order, maximize and zones only (`web/src/desk/store/workspaceStorage.ts:8`, `:15-25`, `:132`). Pullouts and the Info, Roadmap, Repository and Workbench windows live in separate in-memory arrays (`web/src/desk/store/compositorSlice.ts:126`; `web/src/desk/store/windowFactory.ts:30`): after a reload they are gone (`grounding/structure.md:143`). Surface windows come back on their first screen. Drafts are lost: the J3 1:1 note was typed four times; the J4 update lost 111 typed characters (`grounding/faces-jobs.md:85-88`, `:101`). Minimized windows come back open and in front; one window's position was lost (`grounding/faces-surfaces.md:81`). Shots: `grounding/shots/jobs/J1-07-after-reload-1440.png`, `J2-05-came-back-1440.png`, `J2-06-after-reload-1440.png`, `J3-04-came-back-1440.png`, `J3-05-after-reload-1440.png`, `J4-05-came-back-1440.png`, `J5-04-after-reload-1440.png` (and `-393`).

## Scope

- **In:**
  - Extend the existing workspace contract (not a second store) to the dynamic window families: pullouts, Info, Roadmap, Repository, Workbench (`web/src/desk/store/types.ts:26`; `workspaceStorage.ts:15`; `windowFactory.ts:30`), restored through `openPullout` (`compositorSlice.ts:137-152`).
  - A per-window **place**: the selected meeting, the person + tab, the send pick, scroll where it carries the job.
  - **Unsent drafts** in the same document: the People 1:1 note, the Room update draft, the Thought body before save, a meeting form field. A draft clears when its write lands.
  - Minimized windows come back minimized; every saved position comes back.
  - Close keeps the place for the next open of the same object (fork 3).
- **Out:** saved window sets (D1, "Later"); a virtual-screen model; first-value recovery clearing the workspace (intentional, `grounding/structure.md:145`; unverified, not changed here).

## Acceptance criteria

- [ ] **Gate:** PHILO-13-01's cases exist and pass on main before this story merges; they pass again on this story's head.
- [ ] Reload mid-job at 1440 and 393 (touch), for J1–J5 on the grounding week: 0 re-navigation gestures (from 2 in J2, 2 + retype in J3, 3 in J5); every window that was open comes back with its object and place.
- [ ] 0 lost drafts: a 1:1 note, a Room update draft and a Thought body typed and not saved survive a reload and a close; each clears after its save. Red on main.
- [ ] A minimized window comes back minimized; a moved window comes back where it was. Red on main (`grounding/faces-surfaces.md:81`).
- [ ] Closing one window closes only that one (`grounding/structure.md:300`).

## Test plan

- **Focused:** web unit on the workspace document (round trip per family; the place; drafts); `uv run python scripts/check_web_baseline.py --run`.
- **Glass:** the J1–J5 return legs of `grounding/faces-jobs.md` re-run at both widths (touch at 393), counting gestures.
- **Atlas:** one case per family (open → reload → same object and place) and one draft case, at 1440 and 393, one case per `scripts/graph_walk.py run` invocation; B0's cases re-run on the head.
- **Shots:** each reload shot above, re-taken.

## Worker-brief scars

- **Doubles that lie:** a fence reads the real `localStorage` document the app writes, after a real reload; never a hand-built document the app never writes.
- **Never rewrite a guard to match a removal:** existing workspace fences gain families; none is loosened.
- **Drafts are not records:** a draft is never sent or saved by restore; restore fills the field, he presses Save or Send.

## Effort (not a promise)

Grounding size: M (`grounding/faces-jobs.md:153`; `grounding/structure.md:300`). PROVISIONAL.

## Notes

- 2026-10-01 — drafts in `PeopleCore.tsx` (Astra's, B4) and the Room land through a brief exchange, merged serially (status file, map gaps).
- 2026-10-01 — drafted by the Fedaykin docs lane for Muad'Dib; unratified.
