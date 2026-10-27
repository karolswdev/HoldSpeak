# The Window Program — 2026-10-27

**Owner's charge (2026-10-27 02:30):** "I'm employing you to do a thorough analysis of all windows
in our system. Mapping workflows, use cases, and making sure that: A) documentation of the project
and the UI design and everything is up to date; B) the windows are absolutely delightful, offer
minimal friction; C) you truly look at all windows, e.g. the 'Ask AI' still, honestly, looks like
total shit. … This is a multi-step orchestration plan that I want you to treat super seriously."

This program is LIVE judgement and fixes, not more research. It stands on what exists and does
not rewrite it: the 2026-10-23 packet (47 families, [workflow map](design-proposal/WORKFLOW-MAP.md),
[seven journeys](design-proposal/JOURNEYS.md), [use-case inventory](USE-CASE-INVENTORY.json)),
the [window grammar](WINDOW-GRAMMAR-2026-10-24.md), the [window audit](WINDOW-AUDIT-2026-10-25.md),
the [egress ruling](EGRESS-LABELS-2026-10-25.md), and the canvases of this week
(icons D, dock, note workspace). Canon: `docs/internal/UX-CANON.md`, the Seven Tenets.

## Phases

| # | Phase | Output | Done when |
| --- | --- | --- | --- |
| P0 | **The atlas.** Every window and door, shot in realistic states (seeded dense desk, a wallpaper on, 1440 and 393), judged with one rubric, mapped to its jobs and doors. | `WINDOW-ATLAS-2026-10-27.md` + `atlas-2026-10-27/*.png` | every manifest window, every pullout kind, every door has a row with shots, a score and its top defects |
| P1 | **Ask.** Named by the owner. Audit, a direction canvas at real size (two directions, recommended first), his pick, then the build. | `canvases/ask-direction-2026-10-27.html`, then PRs | the owner judges Ask live and does not bounce it |
| P2 | **Fix waves.** Worst-scored windows first, three or four lanes per wave; a canvas wherever the direction is open; each lane runs quick_check, merges, redeploys; the atlas row is re-shot after the merge. | PRs; atlas rows updated | no window scores under 2 on any axis; the owner's live catches trend to zero |
| P3 | **Docs currency.** A drift audit of README, `docs/*.md` user docs, the canon docs (`UX-CANON`, `DESIGN_SYSTEM`, `DESK_GRAMMAR`, `WINDOW-GRAMMAR`), and the native-experience packet (what shipped vs what is still proposed); names and verbs in docs match the live product; stale docs parked, not deleted. | `DOC-DRIFT-2026-10-27.md` + docs PRs | every drift row is fixed or parked with a reason |
| P4 | **Proof.** After each wave: the whole browser suite on main; a fresh atlas pass; `pm/STATUS.md`. | green main; the atlas | the owner says so, live |

## The rubric (0–3 on each axis; the atlas records the score and the evidence)

1. **Grammar** — title bar → toolbar → content edge to edge → status bar; no page H1, no card-in-card, no dead bands.
2. **Text** — ASD-STE100, sentence case, no caps tokens, mono only for ids/code, no counters of zero, no egress chips on working faces.
3. **Honest states** — empty, loading, error and stale each say what is true and what to do next; nothing fakes freshness.
4. **Friction** — presses from the door to the useful outcome; the number is written down; the primary verb is one press away.
5. **Delight** — colour, objects, depth and motion with restraint (the 2026-10-24 ruling: not sterile, not clip art).
6. **Density and legibility** — 32 px rows, 13/12 px type, nothing under 12 px, no clipping, no overlap, contrast.
7. **Consistency** — the same thing looks the same in every window (lamps, badges, verbs, lists, dates).
8. **Phone** — the window works at 393: sheet, pager, status bar clear of the dock.

A window's **top defects** are named in the owner's terms (what he would say when he sees it), with the file that owns each.

## Lanes

- **ATLAS-A** (`wt-ng-dock`): the application windows of `applications.ts` (Today, Capture, Speak + wings, Ask, Meetings, Agents, every Settings pane, Live, Rhythm, Setup, Context, Workbenches, Components, Activity, Room + wings, Project setup, Processes, Commands, People, Projects, Decisions, New decision, Calendar snapshot, Engines).
- **ATLAS-B** (`wt-ng-atlas`): the object windows of the pullout registry (note, thread, decision, meeting, person, room, artifact, coder, directory/drawers, Archive, brief, report, intelligence …) and the doors (⌘K palette, the menu bar and its menus, the bell, Needs you, the Send preview, the feedback sheet, the shortcut sheet, the window switcher, Mission control), and the whole desk at 393.
- **ASK** (`wt-ng-dockcanvas`): P1.
- **DOCS** (`wt-ng-note`): P3's drift audit, fixing as it goes.

## Tracker

Filled by the atlas lanes; one row per window; re-shot after every fix wave.

| Window | Jobs (J1–J7 / USE_CASES row) | Doors in → out | Score (8 axes) | Top defects | Lane / PR |
| --- | --- | --- | --- | --- | --- |
