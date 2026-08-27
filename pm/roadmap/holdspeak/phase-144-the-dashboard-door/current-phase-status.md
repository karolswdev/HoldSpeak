# Phase 144 — The Dashboard Door

**Status:** in progress (1/6). HS-144-01 done; HS-144-02 next.

**Last updated:** 2026-08-27.

## Owner mandate

The Door has a history, and it is recorded honestly. Proposed at the
Phase 139 close as "TODO kanban, upcoming meetings, and scheduled
recording on a front door the owner would actually use on a Tuesday";
its scheduled-recording slice shipped standalone as Phase 136; then
**cancelled 2026-08-18** by owner order ("okay, cut it") because
dashboard furniture would have deepened complexity before the first
useful act was clear — Phase 140, The First Sentence, took its slot.

The world changed. First Sentence shipped (the one-job open + reveal),
the Thought spine shipped (141), and the Intelligence Router shipped
(143). The complexity the cancellation protected against is resolved.
On **2026-08-27 the owner ruled twice**: open the Dashboard Door, and
build it as the **original sketch** — TODO kanban + upcoming meetings
+ scheduled recordings on one front door — adapted only where things
already shipped. That ruling supersedes the 2026-08-18 cancellation.

The standing charter questions apply to every surface in this phase:
*will you use this on a tired Tuesday?* and *does this operate with
joy?*

## Evidence base

Two read-only opus audits (2026-08-27, main @ `ab79c702`), archived in
this phase's assets:

- [`assets/audit-a-pillars-census.md`](./assets/audit-a-pillars-census.md)
  — code-level census of the three pillars, file:line throughout.
- [`assets/audit-b-front-door-walk.md`](./assets/audit-b-front-door-walk.md)
  — live real-hub walk (isolated HOME, 1440+393 shots in
  `assets/audit-b-shots/`) + the routing census.

The load-bearing facts:

- **The Chair at `/` is already the front door** (`web/src/desk/chair/
  ChairHome.tsx:38-63`): hero (ThoughtEntry) + activeWork
  (FinishThoughtsLane) + four counsel-ruled lanes
  (`laneContract.ts:26-31`: brief → follow-through → meetings →
  agents). The First Sentence gate wraps it
  (`DeskApp.tsx:137-196`).
- **The kanban read model half-exists.** `GET /api/follow-through/
  board` (`holdspeak/services/follow_through_service.py:122`) already
  computes four lanes (now / waiting / unassigned / overdue) over
  action_items + cadence_loops + people-commitment projections.
  Unfinished thoughts (`refinement_thoughts`, `schema.py:859-883`) are
  excluded and lack owner/due/priority; workbench items are
  agent tasks, not owner TODOs (audit A §1.6).
- **No calendar-protocol code exists anywhere** (audit A §2.2: zero
  ICS/CalDAV/OWA imports). Phase 135 ruled "ICS first" and nothing was
  ever built. Today "upcoming" can only mean
  `scheduled_recordings.next_fire_at` plus untrustworthy
  browser-history candidates (`activity_meeting_candidates`,
  `schema.py:690-712`).
- **Scheduled recordings are complete machinery** (Phase 136:
  conductor, cron, routes, MCP, SCHEDULED-badged rows in
  `MeetingsLane.tsx:101-162`) — but there is **no Chair-level create
  affordance**; creating one takes the Cadence surface.
- **No unified count/badge** exists anywhere ("3 overdue, 2 waiting").
- Front-door defects found live: the Go menu is invisible at 393px,
  and the `/meetings` deep-link races `SurfaceWindows` registration
  (audit B, surprises).

## Settled design (orchestrator-ruled; the owner may overrule any row)

Per the ceremony budget, open choices are [ORCH-CALL]s decided here
with dispositions — no counsel round was spent:

1. **The Door reforges the Chair — replace, never sit beside.** No
   second front surface, no new SurfaceWindow. ChairHome's lane half
   becomes the Door: the kanban and the upcoming rail. The hero and
   the First Sentence gate are untouched — Phase 140's law stands.
   The counsel-ruled four-lane order (B.Q2 urgency gradient) is
   superseded by this charter for the Chair only; the ruling is named
   here, not silently dropped.
2. **Kanban lanes are server-computed projections; card moves are real
   verbs.** The Door extends the follow-through board read model. A
   card moved or completed calls the existing transition verbs
   (`follow_through/complete`, `cadence.set_status`,
   `people.commitment.transition`, thought verbs) and shows the
   receipt. No board-position table, no manual lane-override store —
   lanes derive from status truth. If a drag has no lawful verb
   behind it, the drag does not exist.
3. **Thoughts join the board as-is; no schema extension.** Unfinished
   thoughts appear in an active-work column via their existing
   state/continuity fields. No owner/due/priority columns are added to
   `refinement_thoughts` this phase (single-user reality; migrations
   stay minimal). Workbench items stay OUT of the owner kanban.
4. **Upcoming meetings = ICS first, executing the Phase 135 ruling.**
   One calendar subscription (file path or URL) parsed into a
   `calendar_events` projection, refreshed on a bounded cadence, with
   the egress badge on any URL fetch. OWA/Playwright scraping stays
   out (unruled scope). Merged with `scheduled_recordings.next_fire_at`
   into ONE upcoming timeline. If the owner does not want ICS this
   phase, HS-144-02 drops and the upcoming rail ships
   scheduled-recordings-only — the stories are cut to make that a
   clean amputation.
5. **The two front-door defects are this phase's to fix** (393px Go
   menu, `/meetings` deep-link race) — a Door phase does not ship a
   broken doorframe. They ride in HS-144-04.

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-144-01 | The Door read model | done | [story-01](./story-01-door-read-model.md) | [evidence-story-01](./evidence-story-01.md) |
| HS-144-02 | Calendar ingest (ICS first) | in-progress | [story-02](./story-02-calendar-ingest-ics.md) | — |
| HS-144-03 | The kanban on glass | backlog | [story-03](./story-03-kanban-on-glass.md) | — |
| HS-144-04 | The upcoming rail + doorframe repairs | backlog | [story-04](./story-04-upcoming-rail-and-repairs.md) | — |
| HS-144-05 | Docs | backlog | [story-05](./story-05-docs.md) | — |
| HS-144-06 | The walk and the close | backlog | [story-06](./story-06-walk-and-close.md) | — |

## Risk register

| Risk | Guard | Stop signal |
|---|---|---|
| Reforging ChairHome breaks neighbor surfaces (the shared-file law) | every story touching ChairHome/DeskApp names the neighboring e2e files IN its slices; sweeps triaged vs the 11-inherited baseline | any non-baseline failure in a Chair/First-Sentence/lane e2e |
| The kanban becomes a second junk drawer | lanes derive from status truth only; no override store; counts honest | a card state with no verb behind it |
| ICS parsing meets a hostile/weird feed | bounded parser, malformed events skipped with a named receipt, never a crash | hub boot or Door render fails on a bad feed |
| Calendar URL fetch leaks quietly | egress badge law; fetch is subscription-scoped, no auth secrets stored this phase | any fetch without a badge |
| The Door regresses First Sentence | the gate (`DeskApp.tsx:137-196`) is out of scope for edits; walk re-runs the cold-open leg | fresh-HOME open shows anything before the one job |
| Beauty debt | beauty pass after the functional pass; shots to the owner before merge | owner flinch |

## Decision log

- 2026-08-27 — Owner picked the Dashboard Door from the next-arc menu,
  with the 2026-08-18 cancellation history explicitly presented.
- 2026-08-27 — Owner ruled the shape: the **original sketch**, adapted
  only where things already shipped. Cancellation superseded.
- 2026-08-27 — Orchestrator ruled the five settled-design calls above
  ([ORCH-CALL] dispositions; ceremony budget — no counsel round).
  The ICS call (design §4) is the one the owner is most likely to
  want to re-cut; it is flagged in the charter report.
- 2026-08-27 — CI remains dead (out of GH minutes; owner order).
  Verification is local-only; push/merge only on the owner's word.

## Where we are

Chartered. Two audits archived, six stories cut, HS-144-01 ready.

HS-144-01 closed 2026-08-27: DoorService + GET /api/door + door.get
MCP twin with reciprocal parity; inventories 135 tools / 537 routes;
two zero-product-bug opus audits; close sweep baseline-exact, zero
branch-new (evidence-story-01.md carries the capture chain + triage).
One ledger note carried: the theoretical pagination spin (outside the
YOLO bar).

- 2026-08-27 — HS-144-03 scope amendment (visible): the glass plan
  found `people.commitment.transition` is MCP-only — the Door
  aggregate advertises a verb the browser cannot reach. Story 03
  slice 0 adds the one thin HTTP route over the same application
  service, parity-proven. Recorded here per the amendment duty; the
  owner may overrule at the sitting.
