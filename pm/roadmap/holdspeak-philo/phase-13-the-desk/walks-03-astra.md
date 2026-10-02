# PHILO-13-03 — H-A2 actual atlas walks

**DRAFT — UNCHECKED — awaiting Muad'Dib.** These records prove H-A2's Dock behavior. They do not close A2-W or story 03.

Case: `case.p13.dock.needs_you_week` in `docs/internal/philo/graph/atlas-phase13-astra.json`. One `graph_walk.py run` per invocation, engine `none`, isolated HOME and DB. Each case seeds real stored-state, proposal/project, heartbeat and assignment producers, restarts the hub, reads the Dock's six, PATCHes A1 done through the real route, reloads, then reads five. The source revision is `65d55047` with the uncommitted H-A2 changes; the frontend build fingerprints distinguish old and final builds.

| Run | Verdict | Observation | Before | After |
|---|---|---|---|---|
| 1440, final | pass | [record](assets/story-03-needs-you/final/dock-1440-final/20261002T043501Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [6](assets/story-03-needs-you/final/dock-1440-final/20261002T043501Z-case.p13.dock.needs_you_week-astra-1440/before.png) | [5](assets/story-03-needs-you/final/dock-1440-final/20261002T043501Z-case.p13.dock.needs_you_week-astra-1440/after.png) |
| 393, final, native touch | pass | [record](assets/story-03-needs-you/final/dock-393-final/20261002T043623Z-case.p13.dock.needs_you_week-astra-393/observation.json) | [6](assets/story-03-needs-you/final/dock-393-final/20261002T043623Z-case.p13.dock.needs_you_week-astra-393/before.png) | [5](assets/story-03-needs-you/final/dock-393-final/20261002T043623Z-case.p13.dock.needs_you_week-astra-393/after.png) |
| 1440, prior frontend build | blocked at the initial 6 check | [record](assets/story-03-needs-you/old-build/dock-1440-old-build/20261002T043233Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [Chair 6, Dock 1](assets/story-03-needs-you/old-build/dock-1440-old-build/20261002T043233Z-case.p13.dock.needs_you_week-astra-1440/blocked.png) | mutation not reached |

The two final runs observe five after reload in 2.852 seconds, within the 30-second bound. The badge is inside the viewport and owns its hit-test points. The phone's setup click uses native touch; the A1 mutation is an HTTP-route step, not a claim that a phone Done Button was exercised. Each live PATCH returns `status: done` for the original `philo13-a2-A1` ID.

The Room wins A2 by its real `actionItemId`, `action-0005000000000000`, and keeps the real ref `A2 confirm the room commitment`. M1's muted row and D1's omission are recorded in the seed's real route payloads. The fixture provenance includes DB readback, assignment clear/reopen evidence, script SHA-256, exact command, and run-owned paths. No owner DB, engine, send or inherited tmux socket was used.

Astra read every observation and all screenshots, including each final `setup-05.png`, before the next invocation. Raw observation JSON, PNG and command-log bytes are retained. [Manifest](assets/story-03-needs-you/manifest.json), [selected runs](assets/story-03-needs-you/selected-runs.json), [captured commands](assets/story-03-needs-you/captured-runs.md).

The Chair headline happens to agree at 6 then 5, but its local code is not yet replaced. Its narrower caption still says `NEEDS YOU 4` then `NEEDS YOU 3`; A2-W must relabel it and prove the Chair, bell, Room and Meetings against the same oracle. This is the Tenet 3 finding that remains open.

## R2 actual atlas rerun — cache invalidation and Room duplicate

The first r2 1440 run was red: the real A1 PATCH returned 200, but the Dock stayed at 6 after reload. A second run after cache invalidation was also red at 6 because the real Room route still emitted the same-project A1 milestone after its linked meeting action became done. The route fence against the cache-only change was red too (`after["count"]` remained 2). The corrected fence now performs only the real A1 PATCH, verifies that the ordinary cached read has a new `computedAt`, confirms the duplicate Room project row remains stored as `planned`, and asserts the exact six refs become five.

| Run | Verdict | Observation | Before | After | Duration |
|---|---|---|---|---|---|
| 1440, before both fixes | fail | [record](assets/story-03-needs-you/r2-live/dock-1440/20261002T080013Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | 6 | 6 | 49.022 s |
| 1440, cache invalidation only | fail | [record](assets/story-03-needs-you/r2-live/dock-1440-fixed/20261002T082020Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | 6 | 6 | see record |
| 1440, final | pass | [record](assets/story-03-needs-you/r2-live/dock-1440-final-r2/20261002T084352Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [6](assets/story-03-needs-you/r2-live/dock-1440-final-r2/20261002T084352Z-case.p13.dock.needs_you_week-astra-1440/before.png) | [5](assets/story-03-needs-you/r2-live/dock-1440-final-r2/20261002T084352Z-case.p13.dock.needs_you_week-astra-1440/after.png) | 2.373 s |
| 393, final, native touch | pass | [record](assets/story-03-needs-you/r2-live/dock-393-final-r2/20261002T084433Z-case.p13.dock.needs_you_week-astra-393/observation.json) | [6](assets/story-03-needs-you/r2-live/dock-393-final-r2/20261002T084433Z-case.p13.dock.needs_you_week-astra-393/before.png) | [5](assets/story-03-needs-you/r2-live/dock-393-final-r2/20261002T084433Z-case.p13.dock.needs_you_week-astra-393/after.png) | 2.371 s |

The two final invocations each used a fresh isolated HOME/DB, one actual atlas case per run, engine `none`, and the shared hub rig. I inspected the before and after screenshots for both viewports before starting the next invocation. The 393 run used the native `ui-touch` adapter. The complete `setup-05.png`, before/after images, observations and logs are retained under `assets/story-03-needs-you/r2-live/`.
