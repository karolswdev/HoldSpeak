# H-A2 — One needs-you membership

**DRAFT — UNCHECKED — awaiting Muad'Dib.** Story 03 remains in-progress until H-A2 and A2-W are both merged. This record is an interface handoff, not the story's done call.

`web/src/desk/needsYou.ts` exports `computeNeedsYou(inputs)` and `useNeedsYou()`. The Dock badge reads the hook. The Chair, bell/shade and Room remain A2-W's work.

## Pure function

Pass the actual Door response as `door`, the Room aggregate's `items` as `roomItems`, heartbeat `muted_projects` as `mutedProjectIds`, the assignment response as `assignments`, its read state as `assignmentRead`, and mapped `Meeting[]` as `meetings`. Tests can supply one `now` clock. `fromWireMeeting` in `api.ts` maps the meeting wire rows.

The result holds `members`, `count`, ranked `unmutedItems` and `mutedItems`, `blockers`, and `failedMeetings`. Each member has `kind` and `ref`. Attention refs keep the source's ref; blocker refs are `blocker:engines`, `blocker:speech`, `blocker:summary`, or `blocker:unknown`; meeting refs are their stored IDs.

- R1 uses Door `overdue`, `now`, `waiting`, and `unassigned` plus Room rows. A Room commitment's `actionItemId` covers its Door card before mute handling. The combined rows pass through the existing dedup and rank helpers, then split by mute state. The pure function adds no terminal-status rule. Room milestones are projected and counted by their own stored lifecycle and due date. A matching title does not link a project milestone to a meeting action and cannot suppress it.
- R2 imports `meetingPathBlockers` read-only. Pending reads add no blocker. A failed read adds `unknown`. Missing roster rows do not prove that an engine is absent. Only an exact summary-capability assignment clears the summary path.
- R3 counts `FAILED` and `RETRYING` summaries. A queued or retrying job with attempts and a last error stays `RETRYING` after its retry time. A stored successful summary adds no member.

Door output rows retain `_doorCard`, `_isDoor`, and `_isUnassigned` for the existing open grammar. `open_ref` remains a Desk route token; it is not an egress URL. Room rows retain commitment, proposal, rank and source metadata.

## Shared read

`useNeedsYou()` adds `loading`, `complete`, `errors`, the Room envelope as `room`, and `refresh()` to the pure result. Consumers share one snapshot, an in-flight read and one 60-second poll while mounted. `refreshNeedsYou()` is also exported for an existing mutation's completion path and C3's later refresh wiring.

The hook reads `/api/door`, the cached `/api/desk/needs-you`, `/api/inference/assignments`, offset pages from `/api/meetings?summary_attention=true`, and `/api/settings/heartbeat`. The summary-attention filter runs before pagination and the route reports the exact total of unparked FAILED/RETRYING Meetings; the hook pages only that filtered set and never pages the whole archive. `?fresh=1` is sent only by an explicit `refresh()` call. Source failures keep known rows and leave `complete` false. A roster failure is shown as the R2 unknown blocker. Room completeness uses the existing `readCoverage` rule and retains the wire's coverage, freshness and next-item metadata.

## A2-W still required

Replace the Chair's local membership merge and headline total with this result. Wire the bell/shade and Room's shared headline to the same hook. Keep each face's open grammar and coverage treatment. Label any narrower Room or Meetings count with what it counts. Keep zero counters off the face. Rehome the relevant Chair guards with the implementation; do not remove or weaken them.

Run A2-W's actual atlas cases at 1440 and 393 with native touch. On the oracle, read six in the Chair, bell and Dock, then verify the real A1-done mutation. The merge record must name both halves. H-A2's Dock case alone does not prove those other faces.

The H-A2 shots expose a remaining Chair caption: the shared total is 6 (then 5), while its ranked-only section says `NEEDS YOU 4` (then `NEEDS YOU 3`). That narrower caption also needs a name for what it counts in A2-W. The existing Chair headline agrees on this fixture but still uses its local code; that agreement is not evidence of shared wiring.

## Verification status

The real-producer oracle yields these six refs: `philo13-a2-A1`, `A2 confirm the room commitment`, `philo13-a2-A3`, `philo13-a2-A4`, `blocker:engines`, and `philo13-a2-failed-meeting`. The real A1 PATCH removes only A1, leaving five. The seeded A1 Room milestone has a distinct title and future due date, so it is not a second attention member. A separate real-route regression fence creates an overdue milestone with the same title as A1 and proves the project health count remains 1 before and after the action is marked done. A2's action ID is `action-0005000000000000`; the Room ref is its actual title, not an invented ID alias. M1 is muted through heartbeat settings; the real Door omits D1.

Both the r2 and r3 Dock atlas runs pass at 1440 and native touch at 393. The r3 run uses the current distinct-title seed after the R2 ruling. See [walks](walks-03-astra.md) and the [lane proof](lane-03-astra.md). The shared module preserves the existing Chair guards; A2-W must rehome them with its wiring. No owner desk sitting or real send is claimed.

## Counsel r2 conditions

| Condition | Settled requirement |
|---|---|
| C1 | R3 counts every FAILED/RETRYING Meeting, including old rows, through the bounded status-filtered server read. The hook pages only that filtered result, never all Meetings. A2-W uses the same hook. |
| C2 | The 60-second poll reads cached `/api/desk/needs-you`; only explicit `refresh()` sends `?fresh=1`. Keep the minute interval and do not refresh the Room aggregate on every poll. A successful meeting action-item status mutation marks the cached needs-you aggregate dirty so its next ordinary read rebuilds. |
| C3 | `scripts/graph_walk.py` and `docs/internal/philo/graph/atlas.schema.json` are Astra-owned shared paths. The faces lane requests changes by named handoff. |
| C4 | Keep the existing ref-level Room-covers-Door mutant and add a code-level `dedupAttention`-skipped mutant. The code mutant must be rejected by the fixed six-ref oracle minted through real producers. |

## Counsel r3 conditions

| Condition | Paid ruling |
|---|---|
| R1 | The five atlas source-reference fences point to current symbols. Generated references were regenerated, and every Documentation Navigation command passed; see [generation](assets/story-03-needs-you/r3/doc-generation.txt) and [navigation](assets/story-03-needs-you/r3/documentation-navigation.txt). |
| R2 | `_overdue_milestones` no longer matches Room milestone titles to meeting action text. The seeded oracle uses a distinct, future-dated Room milestone. A separate real-producer test fails against the old rule at 1→0 and passes with the project-health overdue count preserved at 1→1; see the [r3 focused run](assets/story-03-needs-you/r3/r3-focused-green.txt). |
