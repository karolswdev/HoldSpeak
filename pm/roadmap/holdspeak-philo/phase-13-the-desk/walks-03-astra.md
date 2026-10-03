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

## R3 ruling on the Room milestone

The r2 observations above remain historical records of the then-current title-match projection. Muad'Dib's r3 condition rules that a meeting-action title does not identify a project milestone. The suppression has been removed. The main oracle fixture keeps a distinct, future-dated Room milestone; a separate real-producer regression proves a same-title overdue milestone remains counted by project health at 1→1 after the meeting action is completed. The current code and tests supersede the r2 projection conclusion while preserving its captured observations.

## R3 actual Dock walk

After removing the title-match suppression and keeping the seeded Room milestone distinct, I reran the actual `case.p13.dock.needs_you_week` once at each width with `scripts/graph_walk.py`. Both runs used engine `none`, a fresh isolated HOME and DB, revision `4725aaee` with the r3 worktree dirty, and the current built frontend. The case setup mints the real week and marks the real A1 action done; the reload then settles at five.

| Viewport | Result | Observation | Before | After | Touch mode | Elapsed |
|---|---|---|---|---|---|---|
| 1440 | pass | [record](assets/story-03-needs-you/r3/dock-1440/20261002T203914Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [6](assets/story-03-needs-you/r3/dock-1440/20261002T203914Z-case.p13.dock.needs_you_week-astra-1440/before.png) | [5](assets/story-03-needs-you/r3/dock-1440/20261002T203914Z-case.p13.dock.needs_you_week-astra-1440/after.png) | pointer | 3.875 s |
| 393 | pass | [record](assets/story-03-needs-you/r3/dock-393/20261002T204111Z-case.p13.dock.needs_you_week-astra-393/observation.json) | [6](assets/story-03-needs-you/r3/dock-393/20261002T204111Z-case.p13.dock.needs_you_week-astra-393/before.png) | [5](assets/story-03-needs-you/r3/dock-393/20261002T204111Z-case.p13.dock.needs_you_week-astra-393/after.png) | native `ui-touch` | 2.853 s |

For both observations, the hub and SQLite path were under the run's temporary HOME; the recorded source revision is dirty as expected. I read the initial feedback and settled result separately and viewed both before/after shots. The trigger is the reload after the setup's real A1 status change; it fires no extra non-GET request. Command logs are [1440](assets/story-03-needs-you/r3/dock-1440-command.txt) and [393](assets/story-03-needs-you/r3/dock-393-command.txt). The isolated walk scratch under `.tmp/graph-walk/phase13-astra-r3/` was removed after each result was copied to the story assets.

## R4 Dock walk from the #730 candidate

After rebasing onto current `main` at #730, I ran the real `case.p13.dock.needs_you_week` one time per viewport, engine `none`, with a fresh short-path HOME and DB each time. Both observations report revision `50addf2e46e86e24a1cb0ee51f775c6b098e24ae`, pass, six before the real A1 status route, and five after reload within the 30-second bound. The 393 run uses native touch. I read each observation and viewed all four before/after images before accepting the result.

| Viewport | Result | Observation | Before | After | Touch mode | Worktree |
|---|---|---|---|---|---|---|
| 1440 | pass, 2.855 s | [record](assets/story-03-needs-you/r4-dock-1440/20261003T020119Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [6](assets/story-03-needs-you/r4-dock-1440/20261003T020119Z-case.p13.dock.needs_you_week-astra-1440/before.png) | [5](assets/story-03-needs-you/r4-dock-1440/20261003T020119Z-case.p13.dock.needs_you_week-astra-1440/after.png) | pointer | clean |
| 393 | pass, 2.369 s | [record](assets/story-03-needs-you/r4-dock-393/20261003T020226Z-case.p13.dock.needs_you_week-astra-393/observation.json) | [6](assets/story-03-needs-you/r4-dock-393/20261003T020226Z-case.p13.dock.needs_you_week-astra-393/before.png) | [5](assets/story-03-needs-you/r4-dock-393/20261003T020226Z-case.p13.dock.needs_you_week-astra-393/after.png) | native `ui-touch` | dirty from the already-copied 1440 evidence files only |

Both DB paths are under the per-run temporary HOME and both runs use engine `none`. The first 1440 attempt used a long system temp path and its tmux cleanup reported a socket-path error; no run-owned tmux process remained. I removed that scratch and reran 1440 with `/tmp/p13.*`, then used the same short path for 393. The final observations report no server at their run-owned tmux sockets, and the run output under `.tmp/graph-walk/phase13-astra-r4-short/` was removed after the results were copied here. These Dock results do not close A2-W's Chair, bell, Room or Meetings work.

## R4 actual Dock walk on the #731 head

After rebasing onto #731 (`origin/main` `8485874f6`), I ran the actual `case.p13.dock.needs_you_week` once per viewport at candidate source revision `0f32ddb87613638725ec80c471a6ced7b0b3e070`. Each invocation used engine `none`, a fresh isolated HOME and DB, and its own output directory. The produced Desk reads six before the real A1 status route and five after reload, within the 30-second bound. I read each observation and viewed every before/after shot.

| Viewport | Result | Observation | Before | After | Input mode |
|---|---|---|---|---|---|
| 1440 | pass, 2.378 s to predicate | [record](assets/story-03-needs-you/r4-dock-on-731-1440/20261003T023129Z-case.p13.dock.needs_you_week-astra-1440/observation.json) | [6](assets/story-03-needs-you/r4-dock-on-731-1440/20261003T023129Z-case.p13.dock.needs_you_week-astra-1440/before.png) | [5](assets/story-03-needs-you/r4-dock-on-731-1440/20261003T023129Z-case.p13.dock.needs_you_week-astra-1440/after.png) | pointer |
| 393 | pass, 2.379 s to predicate | [record](assets/story-03-needs-you/r4-dock-on-731-393/20261003T023147Z-case.p13.dock.needs_you_week-astra-393/observation.json) | [6](assets/story-03-needs-you/r4-dock-on-731-393/20261003T023147Z-case.p13.dock.needs_you_week-astra-393/before.png) | [5](assets/story-03-needs-you/r4-dock-on-731-393/20261003T023147Z-case.p13.dock.needs_you_week-astra-393/after.png) | native touch |

Command records: [1440](assets/story-03-needs-you/r4-on-731-walk-1440-command.txt), [393](assets/story-03-needs-you/r4-on-731-walk-393-command.txt). Both observations name the same candidate revision and isolated per-run DB paths. They report `dirty=true` because the untracked `r4-on-731-*` verification receipts were already present; there were no tracked A2 source edits, and the A2 source paths are byte-identical to the #730 candidate `50addf2e`. The 393 `touch_mode` resolves to `ui-touch` / `native-touch`. These Dock observations do not close A2-W's Chair, bell, Room or Meetings work.
