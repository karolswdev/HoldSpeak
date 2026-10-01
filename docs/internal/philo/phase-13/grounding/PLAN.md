# PHILO Phase 13 grounding — the plan (THE DESK)

**Status:** Muad'Dib 2026-10-01. Astra check r1 RATIFY-WITH-CONDITIONS (session `01a0f928-dd63-7192-ac64-58ba872e33ae`, `checks/plan-astra.md`); all four conditions and both MISSED items paid in r2 below.
**Base:** main `4c49651e` (#721, handover XXXII).

## The owner's words (2026-10-01, verbatim)

> "I do want us to restructure and refine our Desk experiences. We've been
> soooo heavily investing into the floor, and totally ignoring the desk..."

> "Make sure we want an incredible exeprience. The whoe Workbench 2.0+ on
> steroids needs to really lean on steroids. Get it?"

His answers to Muad'Dib's three questions:
1. **"The Desk" = both, the whole thing:** the windows he works in
   (Intelligence/Brief, Meetings, the Room, Speak, Ask, People, Calendar, …)
   AND the OS frame around them (menu bar, Dock, the application registry,
   window management, pullouts, the Chair dock, palette). Everything except
   the Floor.
2. **Phase 12 is folded in.** Story 01 is done (merged #717). Story 02's
   canvases F–J are merged (#718) but **never ratified** by him; story 02
   stays in-progress. The canvases are preserved as artifacts, not as a
   ratified design. Their `Send to ▸` names Floor, list and menu-bar origins
   only (`phase-12-…/design/floor-send.md:57`); an **in-window origin was
   never designed and must be re-grounded** here. Of 03–06 only the
   window-side intent carries (Send to ▸ from inside a window, the artifact
   window, the reads); the Floor destination icons and the drop are parked
   (not deleted). The proposal must map each retained behaviour **and its
   atlas / closing-use proof** (old stories 05, 06) against the parked Floor
   work (Astra r1, F4).
3. **Audit, then propose.** Both brains audit now; Muad'Dib brings a ranked
   proposal; nothing is built before he ratifies canvases.

## The bar (read this first — it changes what an audit looks for)

Tenet 6 is "Amiga Workbench 2.0+ **on steroids**", and he just said to lean
on the steroids. A defect list is necessary and not sufficient. Each half
must also answer: **what would the incredible version of this Desk be?**
Not today's windows with fewer bugs: the Desk he would open first thing on a
Tuesday and keep open all day, because it is fast, spatial, alive, and
obviously his. Measure every surface against three lenses:

- **Job:** which job of a Senior Architect with three reports (Tenet 7) does
  it serve? Would he open it on a Tuesday? If not, merge or park it
  (Tenet 3: help and accelerate, never a million interfaces).
- **Workbench 2.0+:** does it behave like a real Workbench/Intuition desk:
  windows with honest gadgets, depth/zoom, right-button menus, screens,
  AppIcons, keyboard first, a consistent component grammar (Tenet 5)?
- **Steroids:** what does the modern, live layer add that 1990 could not:
  instant feedback, live state (meetings, intelligence, sends) visible
  without opening anything, motion with meaning, a command palette that
  does verbs, windows that remember, the desk arranged by his day?

Every half ends with an **ambition section**: at most 10 moves (a ceiling,
not a quota) that would make this Desk incredible. Each move names: (a) the
owner's job it serves; (b) the **observable improvement** (what he sees or
saves, measurable: clicks, seconds, a window he no longer opens); (c) the
smallest change that delivers it on existing components (path:line);
(d) a rough cost S/M/L. Bold is wanted; a feature list without (b) is
rejected. Screens, automatic arrangement and similar are candidates, not
requirements.

**The Tuesday spine (Astra r1, TUESDAY).** Windows are not scored alone.
Both halves follow the same **owner jobs end to end, across windows,
including return and recovery** (leave, come back, reload, a failure
mid-job):
- J1 the morning: arrive → read the brief → open what needs him today;
- J2 a meeting: start → live → summary → decision → send the update;
- J3 a 1:1 with one of his three reports: prep → notes → follow-ups;
- J4 a project: open the Room → what changed → publish an update;
- J5 capture a thought by voice and find it again later.

## Two halves, two brains, disjoint files

| Half | Owner | Writes only | Worktree / branch |
|---|---|---|---|
| **Faces** (live walk) | Muad'Dib → Fedaykin (Opus 5.5) | `docs/internal/philo/phase-13/grounding/faces.md`, `shots/`, `probes/faces-*` | `../wt-philo-13-ground` · `docs/philo-13-ground` |
| **Structure** (census + wiring) | Astra → Luna xhigh | `docs/internal/philo/phase-13/grounding/structure.md`, `probes/structure-*` | `../wt-philo-13-ground-astra` · `docs/philo-13-ground-astra` |

Each brain checks the other's half (recorded in `grounding/checks/`).

### One surface inventory for both halves (Astra r1, F1)

The census is NOT only `applications.ts`. Both halves work from one
complete list, which Astra's half produces first (§S0) and Muad'Dib's half
walks: the 23 registry applications; the object windows mounted outside the
registry (`web/src/desk/DeskApp.tsx:264-301`: DeliveryDossier,
DeliveryTerminal, Roadmap, Repo, Workbench, ScheduleCreate, Trust); every
pullout in `web/src/desk/pullouts/registry.ts` by name (Artifact, Chain,
Coder, Decision, Directory, Intelligence, Kb, Meeting, Note, People,
Recipe, Thread, Workflow, Fallback); the frame (menu bar, Dock, Expose,
Switcher, SnapGhost, palette, Get Info, the Chair dock, the arrival); and
the **handoffs** between them (what opens what).

### Faces half (Muad'Dib)

Method (Astra r1, F3): the walk procedure is
`agent/skills/holdspeak-capability-verifier/SKILL.md` "Walk a case", through
`scripts/graph_walk.py`, one case per invocation, real hub on a throwaway
HOME (`mktemp -d`, removed after; `tests/e2e/glass_infra.py` `_boot` for
seeded shots). **Two states:** (i) **cold arrival** on an empty HOME
(the first screen he would see), and (ii) **a populated week** for a Senior
Architect with three reports: projects, people, meetings with summaries,
decisions, a published update, a brief, notes, artifacts, a saved folder
destination. At **393, real touch-driven transitions** with their effect
(law 29), never a narrow screenshot alone. Walk, at **1440 and 393**:

1. **The frame:** menu bar (Desk/Object/Go/Window), Dock, palette, window
   open/close/move/resize/depth/zoom, window memory across reload, the
   pullouts, the Chair dock, Get Info, the arrival (first screen).
2. **Every Dock and menu application** in `web/src/desk/applications.ts`
   (23 entries; note two `Models` entries at `applications.ts:327` and
   `:435`). For each: the shot; the job it serves; would he open it on a
   Tuesday; dead ends, ghosts, overlaps, noun count; time-to-first-useful
   pixel; what is live vs stale.
3. **The carried ledger** (handover XXXII §Open 3): the Chair dock over the
   meeting preview at 393; "No meetings yet" beside an open record; G1 the
   dead Room Open; G5 the Meetings footer at 393; the lone THIS DEVICE chip;
   **and the highest-cost one: meetings and Workbench items still
   hard-delete** (`phase-10-…/final-summary.md:139`; Astra r1 MISSED).
3b. **The face canon audit** (Astra r1 MISSED; `docs/internal/UX-CANON.md`):
   plain language (ASD-STE100, no prose), every verb the library Button,
   the voice mic on every input, real 393 hit ownership by hit test, the
   12 px floor, no counters of zero, no modals.
3c. **The Tuesday spine** J1–J5 walked end to end, with return and recovery.
4. **The Phase 12 fold:** read canvases F–J (`pm/roadmap/holdspeak-philo/
   phase-12-send-from-the-floor/design/floor-send.md` and the ratification page in handover XXXII) and say which window-side parts
   carry.
5. **Ambition section** per the bar above, with reference to real
   Workbench 2.0 behaviour.

Intelligence and dictation cleanup are OFF (Qwythos `.43` down by the
owner). "Engine off" excuses **only the unavailable operation itself**.
Navigation to it, stored results, recovery, and how the face presents the
failure are all still audited, and a dishonest or dead-end failure face
is a finding (Astra r1, F3).

### Structure half (Astra)

0. **S0, the surface inventory** (above), committed first so the faces
   lane walks the same list.
1. **The registry census:** each surface in the inventory → the
   component it mounts → its data path (routes, services) → where it is
   reachable (Dock, menu, palette, deep link). Duplicates, orphans, dead
   entries, apps with no live data.
2. **The window manager:** `DeskWindow.tsx`, `chromeState.ts`, layout
   persistence: what is remembered, what is lost, what a Workbench-grade
   window manager would need (depth, zoom, snap, screens) and what already
   exists to build on.
3. **The frame's components:** which species the windows share vs.
   hand-roll (Tenet 5); size and complexity hotspots in `web/src/desk/`.
4. **Live state:** what the Desk can learn without polling (bus,
   `/api/...` events) to make windows and the Dock alive; what exists today.
5. **The Phase 12 fold, backend side:** what in story 01 (`floorSendBinding`,
   `GET /api/brief/{id}`, the artifact source) serves Send to ▸ in windows,
   and the hard-delete paths for meetings and Workbench items (where a
   park would replace the delete).
6. **The consolidation map:** merge / park / keep for every application,
   with the reason, ordered so nothing breaks.
7. **Ambition section** per the bar, from the structure's side.

## Both halves end the same way

- Findings ranked by **owner cost**, each tagged with the J1–J5 job it breaks.
- The ambition section (5–10 grounded, costed moves).
- **Open forks for the owner:** at most 5, each with a recommended default.

## Laws for both lanes

Docs only — no product code. Isolated HOME for every hub and probe; never
the owner's real DB; no sends. Scoped probes only — no full suite (law 26;
93 GB free). Never `git stash/reset/clean/checkout --`; stage by explicit
path. Commit through the gate (no story flips). Draft PR each, marked
UNCHECKED — awaiting the other brain.

## After grounding

Muad'Dib synthesizes the proposal (the Phase 13 charter draft, Phase 12's
03–06 re-scoped visibly) → Astra checks → the owner rules the forks →
canvases on the library before build → his ratification → build waves.
