# Phase 171 - The Heartbeat

**Last updated:** 2026-09-05.

## Goal

The desk reaches him. The sweep runs unattended, needs-you aggregates
across Rooms in the shade and the dock, macOS notifications fire on the
edge of the count with quiet hours, the Monday brief recurs on its own
loop, and every active Room is reachable from the command deck. Nothing
leaves the machine (Article III); watching is free (Article V); every
tick receipted (Article XI).

## Status

**PLANNED 0/10.**

**Depends on:** Phase 170 merged.

## Charter

The value-era question (Phase 139): "will you use this on a Tuesday?"

Tuesday, 08:05. His Mac shows one notification: "HoldSpeak -- 3 need you
across 2 projects." He clicks; the system shade opens with PROJECTS
across every Room, the overnight deltas since he last looked, and the
Monday brief already regenerated. He never opened a Room to learn it.

Census facts from THE-TUESDAY-ARC.md section 0 that this phase pays:
cadence_loops 0, cadence_nudges 0 (nothing runs unattended); the Monday
brief ran ONCE (1839 items on 2026-08-24) and never again.

## Scope

- In:
  - The scheduler stamps `next_evaluation_at` and the unattended sweep
    runs on it; one cadence setting in Settings.
  - `GET /api/desk/needs-you` aggregate gets cadence-driven refresh and
    a server-side cache (pays 170's N+1 per-Room query).
  - PROJECTS section in the SystemShade with Room rows, needs-you counts,
    and the first WHY; the dock badge carries the total.
  - macOS notifications on the EDGE of the needs-you count via
    UNUserNotificationCenter from the Cocoa child process; quiet hours
    (existing config); per-project mute; the notification names no
    content beyond the count unless the owner opts in (Article III).
  - The Monday brief recurs on its own cadence loop and lands in the
    shade.
  - PROJECTS section in the command deck (every active Room reachable).
  - The five conductor loops become parallel with their own failure
    boundaries (the hygiene lane item this phase's tree touches).
  - The design on the library before build (canvas at 1440 + 393).
  - His walk on his desk: a notification he actually receives.
- Out:
  - New conductor loop types beyond the existing five.
  - Push notifications to iOS/iPad (Phase 174 Reach).
  - Notification content beyond the aggregate count (unless the owner
    opts in at the settings level).
  - People items in the shade (Phase 172).
  - External writes or sends (no egress in this phase).

## Exit criteria (evidence required)

- [ ] The scheduler stamps `next_evaluation_at` on watches and the
      sweep runs unattended on the cadence setting; the cadence_loops
      count on his desk is > 0.
- [ ] `GET /api/desk/needs-you` returns a cached aggregate that
      refreshes on the cadence tick, not per-request; response time
      < 50 ms from cache.
- [ ] The SystemShade shows a PROJECTS section with Room rows, count,
      and the first WHY; the dock badge carries the aggregate count.
- [ ] A macOS notification fires within 10 s of the needs-you count
      crossing its edge (0 to > 0, or delta since last notification);
      quiet hours suppress it; per-project mute suppresses it; the
      notification body names no Room content beyond the count (Article
      III) unless the owner opts in.
- [ ] The Monday brief regenerates on its own cadence loop without the
      owner opening the desk; the shade shows the most recent brief.
- [ ] Every active Room appears in the command deck; selecting one opens
      the Room.
- [ ] The five conductor loops run in parallel threads with independent
      failure boundaries; a crash in one does not halt the others.
- [ ] The design on the canvas at 1440 + 393 is ratified by the owner
      before the build.
- [ ] His walk on his desk: a notification he receives, the shade with
      PROJECTS, the brief regenerated; his word.
- [ ] Zero egress (Article III); every tick receipted (Article XI).

## Story status

| ID | Story | Status | Story file | Evidence |
| --- | --- | --- | --- | --- |
| HS-171-01 | The design (the Heartbeat's faces on the canvas before build) | backlog | [story-01-the-design](./story-01-the-design.md) | -- |
| HS-171-02 | The cadence row (the scheduler, the unattended sweep, parallel conductor loops) | backlog | [story-02-the-cadence-row](./story-02-the-cadence-row.md) | -- |
| HS-171-03 | The needs-you aggregate (cache + cadence-driven refresh; 170's N+1 paid) | backlog | [story-03-the-needs-you-aggregate](./story-03-the-needs-you-aggregate.md) | -- |
| HS-171-04 | PROJECTS in the shade + the dock badge | backlog | [story-04-projects-in-the-shade](./story-04-projects-in-the-shade.md) | -- |
| HS-171-05 | macOS notifications on the edge (quiet hours, per-project mute, Article III) | backlog | [story-05-macos-notifications](./story-05-macos-notifications.md) | -- |
| HS-171-06 | The Monday brief recurring (its own cadence loop, lands in the shade) | backlog | [story-06-monday-brief-recurring](./story-06-monday-brief-recurring.md) | -- |
| HS-171-07 | PROJECTS in command-K (every active Room reachable from the deck) | backlog | [story-07-projects-in-command-k](./story-07-projects-in-command-k.md) | -- |
| HS-171-08 | The walk (his desk: a notification he actually receives) | backlog | [story-08-the-walk](./story-08-the-walk.md) | -- |
| HS-171-09 | The docs (guide re-shot for every new face; the heartbeat in the architecture) | backlog | [story-09-the-docs](./story-09-the-docs.md) | -- |
| HS-171-10 | The close (gates, sweep, counsel, the ledger, final summary; PR; merge on his word) | backlog | [story-10-the-close](./story-10-the-close.md) | -- |

## Where we are

PLANNED. Waiting for Phase 170 to merge. The recon is complete: the
scheduler has `next_evaluation_at` in the schema (schema.py:2324) but
null on his watches; the cadence engine exists (cadence/ package) but
0 loops, 0 nudges on his desk; the conductor runs two daemon threads
(plugin queue + cadence) serially; `GET /api/desk/needs-you` exists
(projects.py:380) but queries every Room per request (the N+1); the
SystemShade has three sections (Needs you, Finished, Learned) with zero
Room/Project items; the Cocoa presence host (desktop_presence_cocoa.py)
has AppKit/WebKit but zero notification calls; the command deck
(verbRegistry.ts) registers desk.new-project but no "open Room" verb;
quiet hours exist in config (integrations.py:209-210) and the cadence
scheduler respects them (cadence/scheduler.py:30); the dock badge reads
from launcher.badge (Dock.tsx:146) and could carry the aggregate count.

## Active risks

| Risk | Likelihood | Mitigation | Stop signal |
| --- | --- | --- | --- |
| Notification fatigue | Medium | The edge rule (fire only on delta, not every tick) + quiet hours + per-project mute are the design, not an afterthought | The owner mutes all notifications within 48 h of his walk |
| Cocoa child process stability | Low | The presence host already runs as a child; notifications use the same runloop; test with a long-running session | The child crashes on notification dispatch |
| N+1 cache invalidation | Low | The cadence tick is the invalidation signal; stale-for-one-tick is acceptable (reads are free, Article V) | Cache staleness > 2 ticks observed |

## Decisions made (this phase)

- (none yet -- PLANNED)

## Decisions deferred

- The exact cadence interval default (15 min while active, 60 min
  otherwise) -- confirmed at design time from the arc's proposal.
- Whether the notification body includes Room names (Article III says
  count only by default; the owner can opt in) -- settled at design.
